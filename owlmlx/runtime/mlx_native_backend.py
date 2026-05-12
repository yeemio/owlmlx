"""Experimental native MLX backend adapter.

This adapter runs `mlx_lm` in-process instead of as a subprocess. It exists in
parallel with `MlxLmSubprocessBackend` and is **not** wired into any published
serving path. Its purpose is to establish whether owlmlx can hold the
backend-adapter lifecycle contract on a native MLX path and to expose the
process-internal capability entry points (KV cache handle, decode step hook,
sampler injection, etc.) that the subprocess wrap paradigm cannot reach.

Hard scope (per owlmlx-native-mlx-backend-feasibility-scaffold round):

- does not replace `MlxLmSubprocessBackend`
- does not change phase45 active seam
- does not claim continuous batching, cache parity, implicit prefix matching,
  speculative decoding, or stream interleaving — even where the underlying
  mlx_lm API would support them
- does not relax post-claim ``max_concurrent = 1``, ticketed FIFO, or
  serial-safety invariants
- defers `mlx_lm` import to first call site and reports a graceful runtime
  error if `mlx_lm` is not installed (the optional ``runtime`` extra)

The adapter mirrors the public surface of `MlxLmSubprocessBackend` so that
both backends can be swapped behind the same runtime kernel contract.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from owlmlx.cache_manager import CacheManager, CachedRequestHandle
from owlmlx.memory_actuator import (
    AllocatorFloorConfig,
    MemoryActuator,
    ReclaimReceipt,
)
from owlmlx.session_kv_cache import SessionKVCacheStore

from .types import (
    BackendStatus,
    ChatTurn,
    GenerateCohortResult,
    GenerateResult,
    LoadedModelInfo,
    LoadResult,
    RuntimeErrorCode,
    StreamEvent,
    UnloadResult,
)


_BACKEND_NAME = "mlx-native"


@dataclass(slots=True)
class _NativeSession:
    """In-process state for one loaded model on the native path.

    ``last_prompt_cache`` records the **most recent single-request** KV cache
    handle (the result of ``mlx_lm.models.cache.make_prompt_cache(model)``)
    so that tests and future rounds can observe the binding. owlmlx makes
    **no** cross-request prefix-cache reuse claim; this attribute is
    explicitly per-request and is overwritten on every ``generate`` /
    ``stream_generate`` call.
    """

    model_id: str
    model: Any
    tokenizer: Any
    info: LoadedModelInfo
    lock: threading.Lock = field(default_factory=threading.Lock)
    last_error: str | None = None
    last_prompt_cache: Any = None
    last_prompt_cache_id: int | None = None
    prompt_cache_call_count: int = 0
    # C-1.2 release wiring: the active cache_manager handle for the
    # in-flight request. Set by ``_make_fresh_prompt_cache``, cleared by
    # ``_release_active_cache`` on generate/stream completion or unload.
    # ``None`` means no active acquire is pending release.
    active_cache_handle: CachedRequestHandle | None = None


class _TicketedAdmission:
    """Adapter-local ticketed FIFO admission.

    Preserves post-claim invariants on the native path:
    - ``max_concurrent = 1`` after admission: at most one generate / stream
      critical section is active at any moment
    - ticketed FIFO: requests are served strictly in arrival order; later
      arrivals cannot overtake earlier waiters even if scheduling is
      otherwise fair

    This is **adapter-local** — it preserves the contract owlmlx already
    proves on the subprocess backend without claiming any new capability
    (no batching, no parity, no interleaving).
    """

    __slots__ = (
        "_cond",
        "_next_ticket",
        "_serving",
        "_in_critical_section",
        "_max_observed_concurrency",
    )

    def __init__(self) -> None:
        self._cond = threading.Condition(threading.Lock())
        self._next_ticket = 0
        self._serving = 0
        self._in_critical_section = 0
        self._max_observed_concurrency = 0

    def acquire(self) -> tuple[int, bool]:
        """Block until it is this caller's turn.

        Returns ``(ticket, was_queued)``. ``was_queued`` is true only when
        this caller had to wait behind an active or earlier-admitted request;
        monotonic ticket values alone do not imply queueing.
        """

        with self._cond:
            ticket = self._next_ticket
            self._next_ticket += 1
            was_queued = self._in_critical_section > 0 or self._serving != ticket
            while self._serving != ticket:
                self._cond.wait()
            self._in_critical_section += 1
            if self._in_critical_section > self._max_observed_concurrency:
                self._max_observed_concurrency = self._in_critical_section
            return ticket, was_queued

    def release(self) -> None:
        with self._cond:
            self._in_critical_section -= 1
            self._serving += 1
            self._cond.notify_all()

    def snapshot(self) -> dict[str, int]:
        with self._cond:
            return {
                "next_ticket": self._next_ticket,
                "serving": self._serving,
                "in_critical_section": self._in_critical_section,
                "max_observed_concurrency": self._max_observed_concurrency,
            }


def _import_mlx_lm() -> tuple[Any, str | None]:
    """Return (mlx_lm_module, error). Defers import so missing extra fails gracefully."""

    try:
        import mlx_lm  # type: ignore[import-not-found]
    except ImportError as exc:
        return None, (
            f"mlx_lm is not installed in this Python environment "
            f"(install owlmlx[runtime]): {exc}"
        )
    except Exception as exc:  # pragma: no cover - defensive
        return None, f"mlx_lm import failed: {exc}"
    return mlx_lm, None


def _resolve_make_prompt_cache(mlx_lm_module: Any) -> Any | None:
    """Return ``make_prompt_cache`` reachable through the given mlx_lm module.

    Resolved by attribute walk on the passed-in module
    (``mlx_lm_module.models.cache.make_prompt_cache``) rather than via a
    top-level ``import mlx_lm.models.cache`` so that fake-injected
    ``mlx_lm`` stubs in tests can honestly report "no cache surface" even
    when the real ``mlx_lm.models.cache`` is cached in ``sys.modules`` from
    a prior import.

    Returns ``None`` when the upstream cache surface is missing on this
    particular module reference, or when the resolved attribute is not
    callable. Callers must treat ``None`` as "skip cache binding silently"
    — consistent with the scaffold-grade rating in the capability matrix.
    """

    try:
        models_attr = getattr(mlx_lm_module, "models", None)
        if models_attr is None:
            return None
        cache_attr = getattr(models_attr, "cache", None)
        if cache_attr is None:
            return None
        candidate = getattr(cache_attr, "make_prompt_cache", None)
    except Exception:
        return None
    if candidate is None or not callable(candidate):
        return None
    return candidate


def _non_empty_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


class MlxNativeBackend:
    """Experimental in-process MLX backend.

    Surface mirrors `MlxLmSubprocessBackend` for: ``load``, ``unload``,
    ``generate``, ``generate_messages``, ``stream_generate``,
    ``stream_generate_messages``, ``status``.

    All process-internal capability entry points (KV cache handle, decode
    step iterator, sampler injection, etc.) are reachable through the
    ``model`` and ``tokenizer`` attributes on the per-model session, but
    this adapter does not yet expose them as a public contract — that
    deliberately remains scope for a follow-up round.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, _NativeSession] = {}
        self._registry_lock = threading.Lock()
        self._last_error: str | None = None
        self._admission = _TicketedAdmission()
        # C-1.1 wiring: the cache_manager owns the in-process per-request KV
        # cache lifetime. ``_make_fresh_prompt_cache`` delegates to this
        # manager. ``_NativeSession`` cache fields remain populated as a
        # backward-compatible mirror so existing callers that read them
        # continue to work; the manager's counters are the canonical ledger.
        self._cache_manager = CacheManager()
        # Experimental, default-off session-scoped KV reuse. This is kept
        # separate from CacheManager because it deliberately holds a strong
        # cache-object reference across requests for the same explicit
        # session_id/model_id pair.
        self._session_kv_cache = SessionKVCacheStore.from_env()
        # C-3.1 wiring: the memory_actuator is the only sanctioned call site
        # for ``mlx_module.clear_cache()`` in owlmlx. ``unload`` constructs
        # a fresh actuator per call (with the lazily-imported mlx.core, or
        # ``None`` when the optional ``runtime`` extra is missing — in which
        # case the actuator returns a shaped no-op receipt). The most
        # recent receipt is observable on ``_last_unload_receipt`` so tests
        # and future telemetry can verify the actuator was invoked.
        self._last_unload_receipt: ReclaimReceipt | None = None
        # C-3.3 wiring: allocator floor configuration is operator-opt-in via
        # env vars OWLMLX_NATIVE_CACHE_LIMIT_BYTES + OWLMLX_NATIVE_WIRED_LIMIT_BYTES.
        # Configured exactly once on the first successful load (idempotent
        # via the flag below). When neither env var is set, configuration
        # is skipped entirely — preserving the prior unbounded-cache-pool
        # behavior for operators who have not opted in. The most recent
        # config (or ``None``) is observable on ``_last_allocator_floor_config``.
        self._allocator_floor_configured = False
        self._last_allocator_floor_config: AllocatorFloorConfig | None = None

    # ------------------------------------------------------------------ #
    # KV cache binding (single-request only — no cross-request reuse claim)
    # ------------------------------------------------------------------ #
    def _make_fresh_prompt_cache(
        self,
        mlx_lm_module: Any,
        session: _NativeSession,
    ) -> Any | None:
        """Create a fresh per-request KV cache handle, if upstream supports it.

        Returns the cache object on success and records it on
        ``session.last_prompt_cache`` for introspection. Returns ``None``
        when the upstream cache surface is not reachable (fake-injected
        ``mlx_lm`` stubs in tests, or older mlx-lm versions); callers must
        treat ``None`` as "skip cache binding silently".

        Each call produces a fresh cache. owlmlx makes **no** cross-request
        prefix-cache reuse claim; ``last_prompt_cache`` is observable for
        tests but is overwritten on every call.

        C-1.1 wiring: when upstream is reachable, delegates to
        ``self._cache_manager.acquire_for_request(...)``; the manager's
        counters become the canonical ledger and ``_NativeSession`` cache
        fields are mirrored for backward compatibility. When upstream is
        not reachable (fake stubs), the manager is bypassed because
        ``CacheManager.acquire_for_request`` raises ``RuntimeError`` on
        missing surface, while this method must silently return ``None``
        to preserve the adapter's defensive contract.
        """

        if _resolve_make_prompt_cache(mlx_lm_module) is None:
            session.last_prompt_cache = None
            session.last_prompt_cache_id = None
            return None
        try:
            handle, cache = self._cache_manager.acquire_for_request(
                model_id=session.info.model_id,
                mlx_lm_module=mlx_lm_module,
                model=session.model,
            )
        except Exception as exc:  # pragma: no cover - defensive
            session.last_error = f"make_prompt_cache failed: {exc}"
            session.last_prompt_cache = None
            session.last_prompt_cache_id = None
            session.active_cache_handle = None
            return None
        session.last_prompt_cache = cache
        session.last_prompt_cache_id = id(cache)
        session.prompt_cache_call_count += 1
        # The handle's monotonic ``cache_object_id`` is owned by the manager;
        # the session's ``last_prompt_cache_id`` continues to use ``id(cache)``
        # for backward compat with tests written before the manager existed.
        # The handle reference is retained on the session so
        # ``_release_active_cache`` can hand it back to the manager when the
        # request lifecycle completes (generate return, stream finally,
        # unload).
        session.active_cache_handle = handle
        return cache

    def _make_prompt_cache_for_request(
        self,
        mlx_lm_module: Any,
        session: _NativeSession,
        *,
        session_id: str | None,
        memory_watermark: str | None,
    ) -> Any | None:
        """Create or reuse a prompt cache for one request.

        Default-off behavior delegates to ``_make_fresh_prompt_cache`` exactly
        as before. When session cache is enabled and a session_id is present,
        the experimental store owns the strong cache reference across requests.
        Pressure watermark refusal falls back to the single-request path, which
        avoids persistent cache growth while preserving current generation
        behavior.
        """

        if not self._session_kv_cache.enabled or not _non_empty_string(session_id):
            return self._make_fresh_prompt_cache(mlx_lm_module, session)

        make_cache = _resolve_make_prompt_cache(mlx_lm_module)
        if make_cache is None:
            session.last_prompt_cache = None
            session.last_prompt_cache_id = None
            return None

        try:
            decision = self._session_kv_cache.acquire_for_request(
                session_id=session_id,
                model_id=session.info.model_id,
                make_cache=lambda: make_cache(session.model),
                watermark=memory_watermark,
            )
        except Exception as exc:  # pragma: no cover - defensive
            session.last_error = f"session KV cache failed: {exc}"
            session.last_prompt_cache = None
            session.last_prompt_cache_id = None
            return self._make_fresh_prompt_cache(mlx_lm_module, session)

        if decision.cache_object is None:
            return self._make_fresh_prompt_cache(mlx_lm_module, session)

        cache = decision.cache_object
        session.last_prompt_cache = cache
        session.last_prompt_cache_id = id(cache)
        if decision.created:
            session.prompt_cache_call_count += 1
        session.active_cache_handle = None
        return cache

    def _release_active_cache(self, session: _NativeSession) -> None:
        """Hand the active cache handle back to the manager. Idempotent.

        Called from generate's outer finally, stream_generate's outer
        finally (which fires on terminal yield, on exception, AND on
        early generator close per Python semantics), and from unload
        before the session is dropped.
        """

        handle = session.active_cache_handle
        if handle is None:
            return
        try:
            self._cache_manager.release_for_request(handle)
        finally:
            session.active_cache_handle = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def load(
        self,
        model_id: str,
        *,
        memory_gb: float | None = None,
    ) -> LoadResult:
        if not model_id:
            return LoadResult(
                ok=False,
                message="model_id must be non-empty",
                error_code=RuntimeErrorCode.invalid_request,
            )
        with self._registry_lock:
            if model_id in self._sessions:
                return LoadResult(
                    ok=False,
                    message=f"model already loaded: {model_id}",
                    error_code=RuntimeErrorCode.model_already_loaded,
                )

        mlx_lm, import_error = _import_mlx_lm()
        if mlx_lm is None:
            self._last_error = import_error
            return LoadResult(
                ok=False,
                message=import_error or "mlx_lm unavailable",
                error_code=RuntimeErrorCode.backend_error,
                detail={"reason": "mlx_lm_not_installed"},
            )

        try:
            model, tokenizer = mlx_lm.load(model_id)
        except FileNotFoundError as exc:
            return LoadResult(
                ok=False,
                message=f"model not found: {model_id} ({exc})",
                error_code=RuntimeErrorCode.model_not_found,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._last_error = str(exc)
            return LoadResult(
                ok=False,
                message=f"native load failed: {exc}",
                error_code=RuntimeErrorCode.backend_error,
            )

        info = LoadedModelInfo(
            model_id=model_id,
            memory_gb=float(memory_gb or 0.0),
            backend=_BACKEND_NAME,
            loaded_at=time.time(),
        )
        with self._registry_lock:
            if model_id in self._sessions:
                # Lost a race; drop the just-loaded duplicate.
                del model
                return LoadResult(
                    ok=False,
                    message=f"model already loaded: {model_id}",
                    error_code=RuntimeErrorCode.model_already_loaded,
                )
            self._sessions[model_id] = _NativeSession(
                model_id=model_id,
                model=model,
                tokenizer=tokenizer,
                info=info,
            )
        # C-3.3: configure the allocator floor on the first successful load
        # (idempotent — subsequent loads see the flag already set). Reads
        # operator-supplied env vars; skips silently if neither is set.
        self._maybe_configure_allocator_floor()
        return LoadResult(ok=True, message="loaded", model=info)

    def unload(self, model_id: str) -> UnloadResult:
        with self._registry_lock:
            session = self._sessions.pop(model_id, None)
        if session is None:
            return UnloadResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        # Drop strong references; let MLX/Python free in-process state.
        # C-1.2: hand any active cache handle back to the manager BEFORE
        # the session is dropped — otherwise the manager's per-model
        # registry would carry orphaned handles for an unloaded model.
        self._release_active_cache(session)
        self._session_kv_cache.drop_for_model(model_id)
        freed = float(session.info.memory_gb)
        session.model = None
        session.tokenizer = None
        session.last_prompt_cache = None
        session.last_prompt_cache_id = None
        # C-3.1: invoke the memory_actuator to actually return GPU/unified
        # memory pages back to the OS. This is the first owlmlx code path
        # to call ``mx.clear_cache()`` on the production unload path. When
        # mlx.core is not importable (no optional ``runtime`` extra), the
        # actuator returns a shaped no-op receipt and the existing
        # "drop refs and hope" behavior is preserved exactly.
        mlx_core_module = self._try_import_mlx_core()
        actuator = MemoryActuator(mlx_module=mlx_core_module)
        self._last_unload_receipt = actuator.release_single_model(
            model_id=model_id,
            declared_freed_gb=freed,
        )
        # C-3.2: surface measured allocator deltas onto UnloadResult when
        # the actuator had a real mlx_module (no-op receipt → both deltas
        # remain None). The declared ``freed_gb`` is unchanged.
        active_freed = self._compute_freed_bytes(
            self._last_unload_receipt.active_memory_before_bytes,
            self._last_unload_receipt.active_memory_after_bytes,
        )
        cache_freed = self._compute_freed_bytes(
            self._last_unload_receipt.cache_memory_before_bytes,
            self._last_unload_receipt.cache_memory_after_bytes,
        )
        return UnloadResult(
            ok=True,
            message="unloaded",
            model_id=model_id,
            freed_gb=freed,
            active_memory_freed_bytes=active_freed,
            cache_memory_freed_bytes=cache_freed,
        )

    @staticmethod
    def _compute_freed_bytes(
        before: int | None,
        after: int | None,
    ) -> int | None:
        """Compute ``before - after`` byte delta, or ``None`` if either
        reading is missing (no-mlx no-op receipt). Negative deltas are
        clamped to ``0`` because allocator growth during the measurement
        window is not a release; reporting it as negative would mislead
        callers that sum across unloads.
        """

        if before is None or after is None:
            return None
        return max(0, before - after)

    def _maybe_configure_allocator_floor(self) -> None:
        """Operator-opt-in allocator floor configuration. Idempotent.

        Reads ``OWLMLX_NATIVE_CACHE_LIMIT_BYTES`` and
        ``OWLMLX_NATIVE_WIRED_LIMIT_BYTES`` from the environment. When
        both are unset, returns silently — the prior unbounded-cache-pool
        behavior is preserved for operators who have not opted in.
        Otherwise, lazily imports ``mlx.core``, constructs a fresh
        actuator, and calls ``configure_allocator_floor`` once. The
        idempotent flag prevents repeat configuration across multiple
        loads on the same backend instance.
        """

        if self._allocator_floor_configured:
            return
        # Set the flag BEFORE doing work so concurrent loads do not
        # double-configure (the registry lock serializes load() entry but
        # this is belt-and-suspenders for any future reentrancy).
        self._allocator_floor_configured = True

        cache_limit = self._read_env_int("OWLMLX_NATIVE_CACHE_LIMIT_BYTES")
        wired_limit = self._read_env_int("OWLMLX_NATIVE_WIRED_LIMIT_BYTES")
        if cache_limit is None and wired_limit is None:
            return  # operator opted out — no actuator call

        mlx_core_module = self._try_import_mlx_core()
        actuator = MemoryActuator(mlx_module=mlx_core_module)
        self._last_allocator_floor_config = actuator.configure_allocator_floor(
            cache_limit_bytes=cache_limit,
            wired_limit_bytes=wired_limit,
        )

    @staticmethod
    def _read_env_int(env_var: str) -> int | None:
        """Read an env var as int; return ``None`` for unset or unparseable.

        Silently swallowing parse errors here is intentional — operator
        misconfiguration of an opt-in tuning knob should not block a
        model load. The fallthrough to ``None`` skips the configure
        call entirely if it's the only signal.
        """

        raw = os.environ.get(env_var)
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    @staticmethod
    def _try_import_mlx_core() -> object | None:
        """Lazily import ``mlx.core`` for the memory actuator.

        Returns the module on success, ``None`` when the optional
        ``runtime`` extra is not installed. The actuator's no-op branch
        (``mlx_module=None``) preserves the prior unload semantics
        exactly when mlx is unavailable.
        """

        try:
            import mlx.core as mx_core
        except ImportError:
            return None
        return mx_core

    # ------------------------------------------------------------------ #
    # Generation
    # ------------------------------------------------------------------ #
    def generate(
        self,
        model_id: str,
        prompt: str,
        **kwargs: object,
    ) -> GenerateResult:
        session = self._sessions.get(model_id)
        if session is None:
            return GenerateResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        mlx_lm, import_error = _import_mlx_lm()
        if mlx_lm is None:
            return GenerateResult(
                ok=False,
                message=import_error or "mlx_lm unavailable",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
            )
        max_tokens = int(kwargs.get("max_tokens") or 64)  # type: ignore[arg-type]
        session_id = _non_empty_string(kwargs.pop("session_id", None))
        memory_watermark = _non_empty_string(
            kwargs.pop("session_kv_cache_watermark", None)
        ) or _non_empty_string(kwargs.pop("memory_watermark", None))
        started = time.time()
        wait_started = started
        _ticket, was_queued = self._admission.acquire()
        wait_time_s = time.time() - wait_started
        try:
            try:
                with session.lock:
                    prompt_cache = self._make_prompt_cache_for_request(
                        mlx_lm,
                        session,
                        session_id=session_id,
                        memory_watermark=memory_watermark,
                    )
                    call_kwargs: dict[str, Any] = {
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                    }
                    if prompt_cache is not None:
                        call_kwargs["prompt_cache"] = prompt_cache
                    text = mlx_lm.generate(
                        session.model,
                        session.tokenizer,
                        **call_kwargs,
                    )
            except Exception as exc:  # pragma: no cover - defensive
                session.last_error = str(exc)
                return GenerateResult(
                    ok=False,
                    message=f"native generate failed: {exc}",
                    error_code=RuntimeErrorCode.backend_error,
                    model_id=model_id,
                )
        finally:
            # C-1.2: release the active cache handle before releasing the
            # admission ticket so the manager observes the request as fully
            # closed before the next acquire fires under the gate.
            self._release_active_cache(session)
            self._admission.release()
        return GenerateResult(
            ok=True,
            message="generated",
            model_id=model_id,
            text=str(text),
            execution_time_s=time.time() - started,
            wait_time_s=wait_time_s,
            was_queued=was_queued,
        )

    def generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> GenerateResult:
        prompt = "\n".join(f"{turn.role}: {turn.content}" for turn in messages)
        return self.generate(model_id, prompt, **kwargs)

    def generate_cohort(
        self,
        model_id: str,
        prompts: list[str],
        **kwargs: object,
    ) -> GenerateCohortResult:
        # Honest serial cohort — the native path does not yet claim batching.
        results: list[GenerateResult] = []
        for prompt in prompts:
            results.append(self.generate(model_id, prompt, **kwargs))
        return GenerateCohortResult(
            ok=all(r.ok for r in results),
            message="cohort_serial",
            model_id=model_id,
            results=tuple(results),
        )

    def stream_generate(
        self,
        model_id: str,
        prompt: str,
        **kwargs: object,
    ) -> Iterator[StreamEvent]:
        session = self._sessions.get(model_id)
        if session is None:
            yield StreamEvent(
                event="error",
                model_id=model_id,
                error_code=RuntimeErrorCode.model_not_loaded,
                detail={"message": f"model not loaded: {model_id}"},
            )
            return
        mlx_lm, import_error = _import_mlx_lm()
        if mlx_lm is None:
            yield StreamEvent(
                event="error",
                model_id=model_id,
                error_code=RuntimeErrorCode.backend_error,
                detail={"message": import_error or "mlx_lm unavailable"},
            )
            return
        max_tokens = int(kwargs.get("max_tokens") or 64)  # type: ignore[arg-type]
        session_id = _non_empty_string(kwargs.pop("session_id", None))
        memory_watermark = _non_empty_string(
            kwargs.pop("session_kv_cache_watermark", None)
        ) or _non_empty_string(kwargs.pop("memory_watermark", None))
        sequence = 0
        completion_tokens = 0
        finish_reason: str | None = None
        wait_started = time.time()
        _ticket, was_queued = self._admission.acquire()
        wait_time_s = time.time() - wait_started
        try:
            try:
                with session.lock:
                    prompt_cache = self._make_prompt_cache_for_request(
                        mlx_lm,
                        session,
                        session_id=session_id,
                        memory_watermark=memory_watermark,
                    )
                    stream_kwargs: dict[str, Any] = {
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                    }
                    if prompt_cache is not None:
                        stream_kwargs["prompt_cache"] = prompt_cache
                    generate_start = time.time()
                    first_token_prefill_ms: float | None = None
                    for token_payload in mlx_lm.stream_generate(
                        session.model,
                        session.tokenizer,
                        **stream_kwargs,
                    ):
                        sequence += 1
                        completion_tokens += 1
                        if sequence == 1:
                            first_token_prefill_ms = (
                                time.time() - generate_start
                            ) * 1000.0
                        text = (
                            token_payload.text
                            if hasattr(token_payload, "text")
                            else str(token_payload)
                        )
                        finish_reason = getattr(token_payload, "finish_reason", None)
                        yield StreamEvent(
                            event="token",
                            model_id=model_id,
                            text=text,
                            sequence=sequence,
                            completion_tokens=completion_tokens,
                            finish_reason=finish_reason,
                            wait_time_s=wait_time_s,
                            was_queued=was_queued,
                            prefill_ms=first_token_prefill_ms if sequence == 1 else None,
                        )
                        if finish_reason is not None:
                            break
            except Exception as exc:  # pragma: no cover - defensive
                session.last_error = str(exc)
                yield StreamEvent(
                    event="error",
                    model_id=model_id,
                    error_code=RuntimeErrorCode.backend_error,
                    detail={"message": f"native stream_generate failed: {exc}"},
                )
                return
            yield StreamEvent(
                event="done",
                model_id=model_id,
                sequence=sequence,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason or "stop",
                wait_time_s=wait_time_s,
                was_queued=was_queued,
            )
        finally:
            # C-1.2: release the active cache handle on terminal yield, on
            # exception path, AND on early generator close (Python guarantees
            # the generator's ``finally`` runs in all three cases). Pair
            # with admission release so the gate remains the outermost lock.
            self._release_active_cache(session)
            self._admission.release()

    def stream_generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> Iterator[StreamEvent]:
        prompt = "\n".join(f"{turn.role}: {turn.content}" for turn in messages)
        return self.stream_generate(model_id, prompt, **kwargs)

    # ------------------------------------------------------------------ #
    # Status
    # ------------------------------------------------------------------ #
    def status(self) -> BackendStatus:
        with self._registry_lock:
            loaded = tuple(s.info for s in self._sessions.values())
        mlx_lm, import_error = _import_mlx_lm()
        healthy = mlx_lm is not None
        detail: dict[str, Any] = {
            "backend_kind": "experimental_native_mlx",
            "raw_handle_access": "model_and_tokenizer_after_load",
            "future_entry_point_assumptions": (
                "mlx_lm.stream_generate",
                "mlx_lm.models.cache.make_prompt_cache",
                "mlx_lm.sample_utils.make_sampler",
            ),
            "entry_points_owned_by_owlmlx": False,
        }
        if not healthy:
            detail["import_error"] = import_error
        detail["admission"] = self._admission.snapshot()
        detail["session_kv_cache"] = self._session_kv_cache.status_dict()
        if mlx_lm is not None:
            detail["upstream_make_prompt_cache_reachable"] = (
                _resolve_make_prompt_cache(mlx_lm) is not None
            )
        else:
            detail["upstream_make_prompt_cache_reachable"] = False
        return BackendStatus(
            backend_name=_BACKEND_NAME,
            healthy=healthy,
            loaded_models=loaded,
            detail=detail,
        )

    # ------------------------------------------------------------------ #
    # Capability entry-point introspection (read-only, scaffold-grade)
    # ------------------------------------------------------------------ #
    def capability_entry_points(self, model_id: str) -> dict[str, Any]:
        """Report which in-process handles are available on a loaded model.

        This does not claim any of the upstream mlx_lm features as supported
        owlmlx capabilities; it only reports whether the *raw handle* is
        reachable in process so a future round can build on it.
        """

        session = self._sessions.get(model_id)
        if session is None:
            return {"available": False, "reason": "model_not_loaded"}
        mlx_lm, _ = _import_mlx_lm()
        upstream_cache_reachable = (
            mlx_lm is not None
            and _resolve_make_prompt_cache(mlx_lm) is not None
        )
        return {
            "available": True,
            "model_handle_present": session.model is not None,
            "tokenizer_handle_present": session.tokenizer is not None,
            "decode_step_iterator": {
                "symbol": "mlx_lm.stream_generate",
                "status": "used_by_stream_generate",
            },
            "kv_cache_factory": {
                "symbol": "mlx_lm.models.cache.make_prompt_cache",
                "status": (
                    "upstream_not_reachable"
                    if not upstream_cache_reachable
                    else "bound_session_scoped_experimental"
                    if self._session_kv_cache.enabled
                    else "bound_per_request_single_request_only"
                ),
                "last_prompt_cache_id": session.last_prompt_cache_id,
                "prompt_cache_call_count": session.prompt_cache_call_count,
                "cross_request_reuse_claimed": self._session_kv_cache.enabled,
                "session_kv_cache": self._session_kv_cache.status_dict(),
            },
            "sampler_factory": {
                "symbol": "mlx_lm.sample_utils.make_sampler",
                "status": "not_verified_this_round",
            },
        }
