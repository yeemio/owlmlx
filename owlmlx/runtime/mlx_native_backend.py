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
- does not claim continuous batching, cache parity, prefix cache reuse,
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

import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

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
    """In-process state for one loaded model on the native path."""

    model_id: str
    model: Any
    tokenizer: Any
    info: LoadedModelInfo
    lock: threading.Lock = field(default_factory=threading.Lock)
    last_error: str | None = None


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
        freed = float(session.info.memory_gb)
        session.model = None
        session.tokenizer = None
        return UnloadResult(
            ok=True,
            message="unloaded",
            model_id=model_id,
            freed_gb=freed,
        )

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
        started = time.time()
        wait_started = started
        _ticket, was_queued = self._admission.acquire()
        wait_time_s = time.time() - wait_started
        try:
            try:
                with session.lock:
                    text = mlx_lm.generate(
                        session.model,
                        session.tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
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
        sequence = 0
        completion_tokens = 0
        finish_reason: str | None = None
        wait_started = time.time()
        _ticket, was_queued = self._admission.acquire()
        wait_time_s = time.time() - wait_started
        try:
            try:
                with session.lock:
                    for token_payload in mlx_lm.stream_generate(
                        session.model,
                        session.tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                    ):
                        sequence += 1
                        completion_tokens += 1
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
                "status": "not_verified_this_round",
            },
            "sampler_factory": {
                "symbol": "mlx_lm.sample_utils.make_sampler",
                "status": "not_verified_this_round",
            },
        }
