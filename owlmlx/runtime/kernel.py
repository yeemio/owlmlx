"""Executable RuntimeKernel for owlmlx Runtime-0."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Iterable
from dataclasses import asdict
from time import monotonic
from typing import Any, Mapping

from owlmlx.abort_recovery import AbortRecoveryTracker
from owlmlx.cache_residency_tracker import CacheResidencyTracker
from owlmlx.memory_budget import (
    BudgetVerdict,
    MachineMemoryProfile,
    budget_snapshot,
    default_machine_profile,
)
from owlmlx.host_pressure import (
    HostPressureSnapshot,
    host_pressure_not_sampled_snapshot,
    host_pressure_snapshot_to_dict,
    sample_host_pressure,
)
from owlmlx.model_inventory import (
    LoadedModelEntry,
    ModelInventorySnapshot,
    inventory_budget_check,
    inventory_health_snapshot,
    inventory_to_dict,
)
from owlmlx.runtime_health import InferenceHealth, LoadState, TruthLevel
from owlmlx.serving import (
    GenerationGate,
    GenerationResult as GateResult,
    PreGateAdmissionMetadata,
)

from .backends import RuntimeBackend
from .types import (
    ChatTurn,
    GenerateResult,
    LoadResult,
    PinResult,
    RestartResult,
    RuntimeErrorCode,
    RuntimeStatus,
    StreamEvent,
    TTLPolicyResult,
    TTLSweepResult,
    UnloadResult,
)


_METAL_OOM_COOLDOWN_S = 120.0


class RuntimeKernel:
    """Self-owned runtime control object.

    RuntimeKernel is the first executable owlmlx runtime boundary. It owns
    model load/generate/unload/status coordination and consumes the existing
    truth substrate directly instead of waiting for the platform to pass in
    derived state.
    """

    def __init__(
        self,
        backend: RuntimeBackend,
        *,
        profile: MachineMemoryProfile | None = None,
        generation_gate: GenerationGate | None = None,
        abort_recovery: AbortRecoveryTracker | None = None,
        clock: Callable[[], float] | None = None,
        host_pressure_sampler: Callable[[], HostPressureSnapshot | Mapping[str, Any]] | None = None,
    ) -> None:
        self.backend = backend
        self.profile = profile if profile is not None else default_machine_profile()
        self.generation_gate = generation_gate if generation_gate is not None else GenerationGate()
        self.abort_recovery = abort_recovery if abort_recovery is not None else AbortRecoveryTracker()
        self._clock = clock if clock is not None else monotonic
        self._host_pressure_sampler = (
            host_pressure_sampler if host_pressure_sampler is not None else sample_host_pressure
        )
        self._last_host_pressure_snapshot = host_pressure_snapshot_to_dict(
            host_pressure_not_sampled_snapshot()
        )
        self._active_model_id: str | None = None
        self._pinned_model_ids: set[str] = set()
        self._ttl_seconds_by_model_id: dict[str, float] = {}
        self._ttl_last_touch_s: dict[str, float] = {}
        self._eviction_history: list[dict[str, Any]] = []
        self._governance_transition_count = 0
        self._governance_recent_window_runs = 0
        self._governance_active_reassignment_visible = False
        self._governance_restart_restore_visible = False
        self._governance_explicit_targeting_evidence_visible = False
        self._governance_pinning_events_visible = False
        self._governance_ttl_events_visible = False
        self._governance_ttl_expiry_visible = False
        self._governance_eviction_history_visible = False
        self._reclaim_barrier_events: list[dict[str, Any]] = []
        self._reclaim_barrier_event_seq: int = 0
        self._load_failure_events: list[dict[str, Any]] = []
        self._load_failure_event_seq: int = 0
        self._memory_pressure_cooldown_until_s: float | None = None
        self._memory_pressure_cooldown_reason_code: str | None = None
        self._memory_pressure_cooldown_reason_message: str | None = None
        self._memory_pressure_cooldown_failure_fingerprint: tuple[object, ...] | None = None
        self._cache_residency_tracker = CacheResidencyTracker()
        self._post_load_warmup_log: list[dict[str, Any]] = []

    @property
    def active_model_id(self) -> str | None:
        """Current default model used when generate() omits model_id."""

        return self._active_model_id

    def _memory_pressure_cooldown_snapshot(self) -> dict[str, Any]:
        now_s = self._now_s()
        until_s = self._memory_pressure_cooldown_until_s
        remaining_s = max(float(until_s) - now_s, 0.0) if until_s is not None else 0.0
        active = remaining_s > 0.0
        return {
            "active": active,
            "reason_code": self._memory_pressure_cooldown_reason_code,
            "reason_message": self._memory_pressure_cooldown_reason_message,
            "remaining_s": round(remaining_s, 6),
            "cooldown_until_s": round(until_s, 6) if until_s is not None else None,
            "policy": "metal_oom_child_loss_cooldown",
        }

    def _sync_memory_pressure_cooldown_from_backend(
        self,
        backend_status: Any,
    ) -> None:
        detail = getattr(backend_status, "detail", {})
        if not isinstance(detail, Mapping):
            return
        if detail.get("last_failure_class") != "metal_oom":
            return
        last_subprocess = detail.get("last_subprocess")
        if isinstance(last_subprocess, Mapping):
            fingerprint: tuple[object, ...] = (
                "metal_oom",
                last_subprocess.get("returncode"),
                str(last_subprocess.get("stderr") or "")[-512:],
                str(last_subprocess.get("payload") or "")[-512:],
            )
        else:
            fingerprint = ("metal_oom", str(detail.get("last_error") or "")[-512:])
        if fingerprint == self._memory_pressure_cooldown_failure_fingerprint:
            return
        self._memory_pressure_cooldown_failure_fingerprint = fingerprint
        self._memory_pressure_cooldown_until_s = self._now_s() + _METAL_OOM_COOLDOWN_S
        self._memory_pressure_cooldown_reason_code = "metal_oom_child_loss_cooldown"
        self._memory_pressure_cooldown_reason_message = (
            "A subprocess-backed generation failed with Metal insufficient-memory "
            "signals; new model loads are blocked until the runtime-owned "
            "cooldown window expires."
        )

    def _sample_host_pressure_for_load(self) -> dict[str, Any]:
        try:
            snapshot = self._host_pressure_sampler()
        except Exception as exc:  # pragma: no cover - defensive boundary
            snapshot_dict = {
                "available": False,
                "source": "host_pressure_sampler",
                "classification": "unknown",
                "reason_code": "host_pressure_sampler_failed",
                "reason_message": f"Host pressure sampler failed: {exc}",
            }
        else:
            snapshot_dict = host_pressure_snapshot_to_dict(snapshot)
        self._last_host_pressure_snapshot = snapshot_dict
        return snapshot_dict

    def sample_host_pressure(self) -> dict[str, Any]:
        """Explicitly refresh the cached host-pressure load-admission sample."""

        return self._sample_host_pressure_for_load()

    def inventory_snapshot(self) -> ModelInventorySnapshot:
        """Build model inventory from backend-owned loaded model state."""

        backend_status = self.backend.status()
        load_state = LoadState.true_loaded if backend_status.healthy else LoadState.unavailable
        truth_level = TruthLevel.true if backend_status.healthy else TruthLevel.unavailable
        entries = tuple(
            LoadedModelEntry(
                model_id=model.model_id,
                memory_gb=model.memory_gb,
                load_state=load_state,
                truth_level=truth_level,
                backend=model.backend,
                loaded_at=model.loaded_at,
            )
            for model in backend_status.loaded_models
        )
        return ModelInventorySnapshot(entries=entries)

    def load_model(
        self,
        model_id: str,
        *,
        memory_gb: float | None = None,
        post_load_warmup: bool = False,
    ) -> LoadResult:
        """Load a model after owlmlx memory-budget preflight."""

        backend_status = self.backend.status()
        self._sync_memory_pressure_cooldown_from_backend(backend_status)
        dead_registered_models = tuple(
            str(item)
            for item in backend_status.detail.get("dead_registered_models", [])
            if isinstance(item, str) and item
        )
        if dead_registered_models:
            return LoadResult(
                ok=False,
                message=(
                    "recovery barrier: stale subprocess registration requires "
                    f"cleanup before loading {model_id}"
                ),
                error_code=RuntimeErrorCode.backend_error,
                detail={
                    "recovery_barrier": {
                        "reason_code": "dead_registered_models_require_unload",
                        "dead_registered_models": list(dead_registered_models),
                    }
                },
            )
        cooldown = self._memory_pressure_cooldown_snapshot()
        if cooldown["active"]:
            return LoadResult(
                ok=False,
                message=(
                    "memory pressure cooldown active after Metal OOM; "
                    f"refusing to load {model_id}"
                ),
                error_code=RuntimeErrorCode.backend_error,
                detail={"memory_pressure_cooldown": cooldown},
            )

        host_pressure = self._sample_host_pressure_for_load()
        if host_pressure.get("classification") == "host_pressure_block":
            return LoadResult(
                ok=False,
                message=(
                    "host pressure admission barrier active; "
                    f"refusing to load {model_id}"
                ),
                error_code=RuntimeErrorCode.backend_error,
                detail={"host_pressure": dict(host_pressure)},
            )

        requested_gb = (
            memory_gb
            if memory_gb is not None
            else backend_status.detail.get("default_memory_gb")
        )
        if requested_gb is None:
            return LoadResult(
                ok=False,
                message="memory_gb is required when backend has no default memory estimate",
                error_code=RuntimeErrorCode.invalid_request,
            )

        budget = inventory_budget_check(
            self.inventory_snapshot(),
            requested_model_gb=float(requested_gb),
            profile=self.profile,
        )
        if budget.verdict == BudgetVerdict.exceeds:
            self._record_load_failure_event(
                model_id=model_id,
                cause_class="oom_class_failure",
                error_code=RuntimeErrorCode.memory_budget_exceeded.value,
                message=budget.message,
            )
            return LoadResult(
                ok=False,
                message=budget.message,
                error_code=RuntimeErrorCode.memory_budget_exceeded,
                detail={"budget": asdict(budget)},
            )

        result = self.backend.load(model_id, memory_gb=memory_gb)
        if result.ok:
            previous_active = self._active_model_id
            self._active_model_id = model_id
            self._touch_model_activity(model_id)
            self._cache_residency_tracker.record_load(model_id)
            if post_load_warmup:
                self._run_post_load_warmup(model_id)
            self._record_governance_transition(
                previous_active=previous_active,
                new_active=self._active_model_id,
            )
            # Successful same-model load resolves any prior unresolved load
            # failure event for that model id (auto-resolution rule).
            self._resolve_matching_load_failure_events(model_id=model_id)
        elif result.error_code not in {
            RuntimeErrorCode.model_already_loaded,
            RuntimeErrorCode.unsupported_model_family,
        }:
            cause_class = (
                "oom_class_failure"
                if result.error_code is RuntimeErrorCode.memory_budget_exceeded
                else "load_failure"
            )
            self._record_load_failure_event(
                model_id=model_id,
                cause_class=cause_class,
                error_code=(
                    result.error_code.value
                    if result.error_code is not None
                    else None
                ),
                message=result.message,
            )
        return result

    def _run_post_load_warmup(self, model_id: str) -> None:
        """Fire one minimal generate to compile Metal JIT shaders after load.

        Runs synchronously inside load_model (which is already off the event
        loop in the FastAPI thread-pool). Bypasses GenerationGate because
        nothing else is running at load time. Failure is logged but never
        propagates — warmup must not undo a successful load.
        """
        t0 = self._clock()
        ok = True
        error_msg: str | None = None
        try:
            for _ in self.backend.stream_generate(model_id, "", max_tokens=1):
                pass
        except Exception as exc:
            ok = False
            error_msg = str(exc)
        elapsed_ms = round((self._clock() - t0) * 1000, 1)
        if ok:
            self._cache_residency_tracker.record_use(model_id)
        entry: dict[str, Any] = {
            "model_id": model_id,
            "warmup_ms": elapsed_ms,
            "ok": ok,
        }
        if error_msg is not None:
            entry["error"] = error_msg
        self._post_load_warmup_log.append(entry)

    def _resolve_target_model(self, model_id: str | None) -> str | None:
        return model_id or self._active_model_id

    def _now_s(self) -> float:
        return float(self._clock())

    def _loaded_model_ids(self) -> set[str]:
        return {model.model_id for model in self.backend.status().loaded_models}

    def _touch_model_activity(self, model_id: str | None) -> None:
        if model_id is None:
            return
        if model_id in self._loaded_model_ids():
            self._ttl_last_touch_s[model_id] = self._now_s()

    def _ttl_expired_model_ids(self, *, now_s: float | None = None) -> tuple[str, ...]:
        current = self._now_s() if now_s is None else float(now_s)
        expired: list[str] = []
        for model_id, ttl_seconds in self._ttl_seconds_by_model_id.items():
            if model_id not in self._loaded_model_ids():
                continue
            last_touch = self._ttl_last_touch_s.get(model_id)
            if last_touch is None:
                continue
            if current - last_touch >= ttl_seconds:
                expired.append(model_id)
        return tuple(sorted(expired))

    def _record_load_failure_event(
        self,
        *,
        model_id: str,
        cause_class: str,
        error_code: str | None,
        message: str,
    ) -> dict[str, Any]:
        """Record a runtime-owned load operation boundary failure.

        ``cause_class`` is one of ``oom_class_failure`` / ``load_failure`` /
        ``unknown``; the termination recovery policy reads this section to
        classify load-side termination causes without re-deriving them.
        """

        self._load_failure_event_seq += 1
        event = {
            "event_id": self._load_failure_event_seq,
            "model_id": model_id,
            "cause_class": cause_class,
            "stage": "backend_load",
            "error_code": error_code,
            "message": message,
            "recorded_at_s": round(self._now_s(), 6),
            "resolved": False,
        }
        self._load_failure_events.append(event)
        return event

    def _resolve_matching_load_failure_events(self, *, model_id: str) -> int:
        resolved = 0
        for event in self._load_failure_events:
            if (
                not event.get("resolved", False)
                and event.get("model_id") == model_id
            ):
                event["resolved"] = True
                resolved += 1
        return resolved

    def _resolve_matching_reclaim_barrier_events(
        self,
        *,
        model_id: str,
        operations: set[str],
    ) -> int:
        resolved = 0
        for event in self._reclaim_barrier_events:
            if (
                not event.get("resolved", False)
                and event.get("model_id") == model_id
                and event.get("operation") in operations
            ):
                event["resolved"] = True
                resolved += 1
        return resolved

    def resolve_reclaim_barrier_event(self, event_id: int) -> dict[str, Any]:
        """Mark a specific reclaim-barrier event resolved.

        This is the explicit operator override path. It records that the
        barrier is no longer active; it does **not** retry, remediate, or
        re-execute the underlying operation. Auto-resolution on a successful
        same-model follow-up operation remains the primary resolution path.
        """

        for event in self._reclaim_barrier_events:
            if int(event.get("event_id") or 0) == int(event_id):
                if event.get("resolved", False):
                    return {
                        "ok": True,
                        "already_resolved": True,
                        "event": dict(event),
                    }
                event["resolved"] = True
                return {
                    "ok": True,
                    "already_resolved": False,
                    "event": dict(event),
                }
        return {
            "ok": False,
            "error_code": "reclaim_barrier_event_not_found",
            "event_id": int(event_id),
        }

    def _record_reclaim_barrier_event(
        self,
        *,
        model_id: str,
        operation: str,
        stage: str,
        error_code: str | None,
        message: str,
        source: str = "runtime_kernel",
    ) -> dict[str, Any]:
        """Record a failed-unload / failed-reclaim / restart-unload-stage event.

        Events are recorded at the operation boundary; resolution policy is
        deferred to a later release-floor 3.4 round. See
        ``owlmlx.settle_barrier_event`` for the contract that consumes the
        snapshot.
        """

        self._reclaim_barrier_event_seq += 1
        event = {
            "event_id": self._reclaim_barrier_event_seq,
            "model_id": model_id,
            "operation": operation,
            "source": source,
            "stage": stage,
            "error_code": error_code,
            "message": message,
            "recorded_at_s": round(self._now_s(), 6),
            "requires_recovery_barrier": True,
            "resolved": False,
        }
        self._reclaim_barrier_events.append(event)
        return event

    def _record_eviction_history(
        self,
        *,
        model_id: str,
        event: str,
        source: str = "ttl_policy",
    ) -> None:
        self._eviction_history.append(
            {
                "sequence": len(self._eviction_history) + 1,
                "model_id": model_id,
                "event": event,
                "source": source,
                "recorded_at_s": round(self._now_s(), 6),
            }
        )
        self._governance_eviction_history_visible = True

    def _record_governance_transition(
        self,
        *,
        previous_active: str | None,
        new_active: str | None,
    ) -> None:
        self._governance_transition_count += 1
        if (
            previous_active is not None
            and new_active is not None
            and previous_active != new_active
        ):
            self._governance_active_reassignment_visible = True

    def _record_governance_explicit_targeting(self, requested_model_id: str | None) -> None:
        if requested_model_id is None:
            return
        self._governance_explicit_targeting_evidence_visible = True
        self._governance_recent_window_runs += 1

    def _record_governance_restart_restore(self, *, restored_active: bool) -> None:
        if not restored_active:
            return
        self._governance_restart_restore_visible = True
        self._governance_recent_window_runs += 1

    def _build_pre_gate_admission_metadata(
        self,
        *,
        request_kind: str,
        model_id: str | None,
        stream: bool,
        prompt: str | None = None,
        messages: list[ChatTurn] | None = None,
    ) -> PreGateAdmissionMetadata:
        return PreGateAdmissionMetadata(
            request_kind=request_kind,
            model_id=model_id,
            stream=stream,
            prompt_chars=len(prompt or ""),
            message_count=len(messages or []),
        )

    def _assert_loaded_model(self, target_model: str | None) -> GenerateResult | None:
        if not target_model:
            return GenerateResult(
                ok=False,
                message="no active model loaded",
                error_code=RuntimeErrorCode.model_not_loaded,
            )
        if target_model not in {m.model_id for m in self.backend.status().loaded_models}:
            return GenerateResult(
                ok=False,
                message=f"model not loaded: {target_model}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=target_model,
            )
        return None

    async def generate(
        self,
        prompt: str,
        *,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> GenerateResult:
        """Generate text through the backend under GenerationGate discipline."""

        target_model = self._resolve_target_model(model_id)
        invalid = self._assert_loaded_model(target_model)
        if invalid is not None:
            return invalid

        cohort_generate = getattr(self.backend, "generate_cohort", None)

        def call_backend() -> GenerateResult:
            assert target_model is not None
            return self.backend.generate(target_model, prompt, **kwargs)

        metadata = self._build_pre_gate_admission_metadata(
            request_kind="generate",
            model_id=target_model,
            stream=False,
            prompt=prompt,
        )
        if callable(cohort_generate):
            def call_single(payload: object) -> GenerateResult:
                assert target_model is not None
                return self.backend.generate(target_model, str(payload), **kwargs)

            def call_cohort(payloads: tuple[object, ...]) -> tuple[GenerateResult, ...]:
                assert target_model is not None
                batch = cohort_generate(
                    target_model,
                    [str(item) for item in payloads],
                    **kwargs,
                )
                if batch.ok:
                    return tuple(batch.results)
                shared_error = GenerateResult(
                    ok=False,
                    message=batch.message,
                    error_code=batch.error_code or RuntimeErrorCode.backend_error,
                    model_id=target_model,
                    detail=dict(batch.detail),
                )
                return tuple(shared_error for _ in payloads)

            gated = await self.generation_gate.execute_async_cohort_with_admission(
                metadata,
                prompt,
                call_single,
                call_cohort,
            )
        else:
            gated = await self.generation_gate.execute_async_with_admission(
                metadata,
                call_backend,
            )
        result = gated.value
        if not isinstance(result, GenerateResult):
            return GenerateResult(
                ok=False,
                message="backend returned invalid generation result",
                error_code=RuntimeErrorCode.backend_error,
                model_id=target_model,
                detail={"raw_result": repr(result)},
            )
        if result.ok:
            self._record_governance_explicit_targeting(model_id)
            self._touch_model_activity(target_model)
            self._cache_residency_tracker.record_use(target_model)
        return GenerateResult(
            ok=result.ok,
            message=result.message,
            error_code=result.error_code,
            detail=result.detail,
            model_id=result.model_id,
            text=result.text,
            finish_reason=result.finish_reason,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            wait_time_s=gated.wait_time_s,
            execution_time_s=gated.execution_time_s,
            was_queued=gated.was_queued,
        )

    async def generate_messages(
        self,
        messages: list[ChatTurn],
        *,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> GenerateResult:
        """Generate text from structured chat messages."""

        target_model = self._resolve_target_model(model_id)
        invalid = self._assert_loaded_model(target_model)
        if invalid is not None:
            return invalid

        def call_backend() -> GenerateResult:
            assert target_model is not None
            return self.backend.generate_messages(target_model, messages, **kwargs)

        gated = await self.generation_gate.execute_async_with_admission(
            self._build_pre_gate_admission_metadata(
                request_kind="generate_messages",
                model_id=target_model,
                stream=False,
                messages=messages,
            ),
            call_backend,
        )
        result = gated.value
        if not isinstance(result, GenerateResult):
            return GenerateResult(
                ok=False,
                message="backend returned invalid generation result",
                error_code=RuntimeErrorCode.backend_error,
                model_id=target_model,
                detail={"raw_result": repr(result)},
            )
        if result.ok:
            self._record_governance_explicit_targeting(model_id)
            self._touch_model_activity(target_model)
            self._cache_residency_tracker.record_use(target_model)
        return GenerateResult(
            ok=result.ok,
            message=result.message,
            error_code=result.error_code,
            detail=result.detail,
            model_id=result.model_id,
            text=result.text,
            finish_reason=result.finish_reason,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            wait_time_s=gated.wait_time_s,
            execution_time_s=gated.execution_time_s,
            was_queued=gated.was_queued,
        )

    async def _stream_with_background_producer(
        self,
        *,
        metadata: PreGateAdmissionMetadata,
        producer: Callable[[], Iterable[StreamEvent]],
        on_success: Callable[[], None],
    ) -> AsyncIterator[StreamEvent]:
        """Run a stream producer under gate claim while draining to the consumer outside it."""

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[tuple[str, object | None]] = asyncio.Queue()

        def emit(kind: str, payload: object | None = None) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, (kind, payload))

        def run_producer() -> None:
            with self.generation_gate.stream_session_with_admission_sync(metadata) as gate_start:
                emit("start", gate_start)
                try:
                    for event in producer():
                        emit("event", event)
                except BaseException as exc:  # pragma: no cover - defensive runtime bridge
                    emit("error", exc)
            emit("done")

        producer_future = loop.run_in_executor(None, run_producer)
        gate_start: GateResult | None = None
        saw_non_error_event = False

        try:
            while True:
                kind, payload = await queue.get()
                if kind == "start":
                    if not isinstance(payload, GateResult):
                        raise RuntimeError("stream gate start payload is invalid")
                    gate_start = payload
                    continue
                if kind == "event":
                    if gate_start is None:
                        raise RuntimeError("stream gate start missing before first event")
                    if not isinstance(payload, StreamEvent):
                        raise RuntimeError("stream event payload is invalid")
                    if payload.event != "error":
                        saw_non_error_event = True
                    yield StreamEvent(
                        event=payload.event,
                        model_id=payload.model_id,
                        text=payload.text,
                        error_code=payload.error_code,
                        finish_reason=payload.finish_reason,
                        sequence=payload.sequence,
                        prompt_tokens=payload.prompt_tokens,
                        completion_tokens=payload.completion_tokens,
                        wait_time_s=gate_start.wait_time_s,
                        execution_time_s=payload.execution_time_s,
                        was_queued=gate_start.was_queued,
                        detail=payload.detail,
                    )
                    continue
                if kind == "error":
                    if isinstance(payload, BaseException):
                        raise payload
                    raise RuntimeError("stream producer failed with an invalid exception payload")
                if kind == "done":
                    break
                raise RuntimeError(f"unexpected stream queue item: {kind}")
        finally:
            await producer_future

        if saw_non_error_event:
            on_success()

    async def generate_stream(
        self,
        prompt: str,
        *,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """Generate a streamed response through the backend under GenerationGate discipline."""

        target_model = self._resolve_target_model(model_id)
        if not target_model:
            yield StreamEvent(
                event="error",
                error_code=RuntimeErrorCode.model_not_loaded,
                detail={"message": "no active model loaded"},
            )
            return
        if target_model not in {m.model_id for m in self.backend.status().loaded_models}:
            yield StreamEvent(
                event="error",
                model_id=target_model,
                error_code=RuntimeErrorCode.model_not_loaded,
                detail={"message": f"model not loaded: {target_model}"},
            )
            return

        metadata = self._build_pre_gate_admission_metadata(
            request_kind="generate_stream",
            model_id=target_model,
            stream=True,
            prompt=prompt,
        )

        def mark_success() -> None:
            self._record_governance_explicit_targeting(model_id)
            self._touch_model_activity(target_model)
            self._cache_residency_tracker.record_use(target_model)

        async for event in self._stream_with_background_producer(
            metadata=metadata,
            producer=lambda: self.backend.stream_generate(target_model, prompt, **kwargs),
            on_success=mark_success,
        ):
            yield event

    async def generate_stream_messages(
        self,
        messages: list[ChatTurn],
        *,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a response from structured chat messages."""

        target_model = self._resolve_target_model(model_id)
        if not target_model:
            yield StreamEvent(
                event="error",
                error_code=RuntimeErrorCode.model_not_loaded,
                detail={"message": "no active model loaded"},
            )
            return
        if target_model not in {m.model_id for m in self.backend.status().loaded_models}:
            yield StreamEvent(
                event="error",
                model_id=target_model,
                error_code=RuntimeErrorCode.model_not_loaded,
                detail={"message": f"model not loaded: {target_model}"},
            )
            return

        metadata = self._build_pre_gate_admission_metadata(
            request_kind="generate_stream_messages",
            model_id=target_model,
            stream=True,
            messages=messages,
        )

        def mark_success() -> None:
            self._record_governance_explicit_targeting(model_id)
            self._touch_model_activity(target_model)
            self._cache_residency_tracker.record_use(target_model)

        async for event in self._stream_with_background_producer(
            metadata=metadata,
            producer=lambda: self.backend.stream_generate_messages(
                target_model,
                messages,
                **kwargs,
            ),
            on_success=mark_success,
        ):
            yield event

    def unload_model(
        self,
        model_id: str,
        *,
        _operation: str = "explicit_unload",
    ) -> UnloadResult:
        """Unload a model through the backend and clear active model if needed.

        ``_operation`` is an internal hint used to classify a runtime-owned
        reclaim-barrier event when the backend unload boundary returns a
        failure result. Public callers should not pass it; ``sweep_expired_models``
        passes ``"ttl_sweep_reclaim"`` so a TTL sweep cleanup failure is
        recorded as ``failed_reclaim`` rather than ``failed_unload``.
        """

        if model_id in self._pinned_model_ids:
            return UnloadResult(
                ok=False,
                message=f"model is pinned and cannot be unloaded: {model_id}",
                error_code=RuntimeErrorCode.model_pinned,
                model_id=model_id,
                freed_gb=0.0,
            )

        previous_active = self._active_model_id
        result = self.backend.unload(model_id)
        if (
            not result.ok
            and result.error_code is not RuntimeErrorCode.model_not_loaded
        ):
            self._record_reclaim_barrier_event(
                model_id=model_id,
                operation=_operation,
                stage="backend_unload",
                error_code=(
                    result.error_code.value
                    if result.error_code is not None
                    else None
                ),
                message=result.message,
            )
        if result.ok and self._active_model_id == model_id:
            remaining = self.backend.status().loaded_models
            self._active_model_id = remaining[-1].model_id if remaining else None
        if result.ok:
            self._pinned_model_ids.discard(model_id)
            self._ttl_seconds_by_model_id.pop(model_id, None)
            self._ttl_last_touch_s.pop(model_id, None)
            _reason_map = {
                "ttl_sweep_reclaim": "ttl_expiry",
                "pressure_eviction": "pressure_eviction",
            }
            self._cache_residency_tracker.record_unload(
                model_id, reason=_reason_map.get(_operation, "manual_unload")
            )
        if result.ok:
            self._record_governance_transition(
                previous_active=previous_active,
                new_active=self._active_model_id,
            )
            # Successful follow-up unload resolves any prior unresolved
            # explicit_unload / ttl_sweep_reclaim event for the same model id
            # (auto-resolution rule).
            self._resolve_matching_reclaim_barrier_events(
                model_id=model_id,
                operations={"explicit_unload", "ttl_sweep_reclaim"},
            )
        return result

    def execute_memory_pressure_eviction(
        self,
        *,
        abort_recovery_snapshot: Mapping[str, Any] | None = None,
        protect_active: bool = True,
    ) -> dict[str, Any]:
        """Build the memory-pressure eviction policy and execute it if `evict`.

        Refuses to execute unless the policy decision is `evict`. On execution,
        unloads the selected victim through `unload_model`, records a
        runtime-owned eviction-history event with source
        `memory_pressure_policy`, and returns a structured result with the
        decision snapshot, victim, unload result, residency after-state, and
        the recorded eviction-history event.
        """

        from owlmlx.memory_pressure_eviction_policy import (
            build_memory_pressure_eviction_policy,
            memory_pressure_eviction_policy_to_dict,
        )

        snapshot = abort_recovery_snapshot
        if snapshot is None:
            snapshot = self.abort_recovery.snapshot()

        policy = build_memory_pressure_eviction_policy(
            runtime_status=self.status_dict(),
            abort_recovery_snapshot=snapshot,
            protect_active=protect_active,
        )
        policy_payload = memory_pressure_eviction_policy_to_dict(policy)

        if policy.decision != "evict":
            return {
                "ok": False,
                "executed": False,
                "decision": policy.decision,
                "reason_code": "execution_refused_unless_decision_is_evict",
                "reason_message": (
                    "Memory-pressure eviction execution refused because the "
                    f"policy decision is {policy.decision!r}, not 'evict'."
                ),
                "decision_snapshot": policy_payload,
                "selected_victim": None,
                "unload_result": None,
                "residency_after": None,
                "eviction_history_event": None,
            }

        assert policy.selected_victim is not None
        victim = dict(policy.selected_victim)
        victim_id = str(victim["model_id"])
        unload_result = self.unload_model(victim_id, _operation="pressure_eviction")
        unload_payload: dict[str, Any] = {
            "ok": unload_result.ok,
            "message": unload_result.message,
            "model_id": unload_result.model_id,
            "freed_gb": unload_result.freed_gb,
            "error_code": (
                unload_result.error_code.value
                if unload_result.error_code is not None
                else None
            ),
        }

        if not unload_result.ok:
            return {
                "ok": False,
                "executed": False,
                "decision": policy.decision,
                "reason_code": "unload_failed_during_eviction",
                "reason_message": (
                    "Memory-pressure eviction selected a victim but the "
                    "underlying unload failed; eviction did not occur."
                ),
                "decision_snapshot": policy_payload,
                "selected_victim": victim,
                "unload_result": unload_payload,
                "residency_after": None,
                "eviction_history_event": None,
            }

        self._record_eviction_history(
            model_id=victim_id,
            event="memory_pressure_evicted",
            source="memory_pressure_policy",
        )
        recorded_event = dict(self._eviction_history[-1])

        new_status = self.status_dict()
        residency_after = {
            "active_model_id": new_status.get("active_model_id"),
            "loaded_model_ids": [
                str(model.get("model_id"))
                for model in (new_status.get("backend") or {}).get(
                    "detail", {}
                ).get("loaded_models_summary", [])
                if isinstance(model, Mapping) and model.get("model_id")
            ]
            or [
                str(entry.model_id)
                for entry in self.backend.status().loaded_models
            ],
            "evicted_model_id": victim_id,
            "victim_still_resident": victim_id
            in {
                str(entry.model_id)
                for entry in self.backend.status().loaded_models
            },
        }

        return {
            "ok": True,
            "executed": True,
            "decision": policy.decision,
            "reason_code": policy.reason_code,
            "reason_message": policy.reason_message,
            "decision_snapshot": policy_payload,
            "selected_victim": victim,
            "unload_result": unload_payload,
            "residency_after": residency_after,
            "eviction_history_event": recorded_event,
        }

    def pin_model(self, model_id: str) -> PinResult:
        """Pin a loaded model against unload on the runtime-owned path."""

        if model_id not in {m.model_id for m in self.backend.status().loaded_models}:
            return PinResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
                pinned=False,
            )
        already_pinned = model_id in self._pinned_model_ids
        self._pinned_model_ids.add(model_id)
        self._governance_pinning_events_visible = True
        return PinResult(
            ok=True,
            message=(
                f"model already pinned: {model_id}"
                if already_pinned
                else f"pinned {model_id}"
            ),
            model_id=model_id,
            pinned=True,
            detail={
                "already_pinned": already_pinned,
                "pinned_model_ids": sorted(self._pinned_model_ids),
            },
        )

    def unpin_model(self, model_id: str) -> PinResult:
        """Remove runtime-owned pin protection from a loaded model."""

        if model_id not in self._pinned_model_ids:
            return PinResult(
                ok=False,
                message=f"model is not pinned: {model_id}",
                error_code=RuntimeErrorCode.invalid_request,
                model_id=model_id,
                pinned=False,
                detail={"pinned_model_ids": sorted(self._pinned_model_ids)},
            )
        self._pinned_model_ids.remove(model_id)
        self._governance_pinning_events_visible = True
        return PinResult(
            ok=True,
            message=f"unpinned {model_id}",
            model_id=model_id,
            pinned=False,
            detail={"pinned_model_ids": sorted(self._pinned_model_ids)},
        )

    def restart_model(self, model_id: str) -> RestartResult:
        """Restart a loaded model using the existing runtime registration."""

        loaded = {
            model.model_id: model
            for model in self.backend.status().loaded_models
        }
        current = loaded.get(model_id)
        if current is None:
            return RestartResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
                stage="preflight",
                retryable=False,
            )

        previous_active = self._active_model_id
        was_active = self._active_model_id == model_id
        unloaded = self.backend.unload(model_id)
        if not unloaded.ok:
            if unloaded.error_code is not RuntimeErrorCode.model_not_loaded:
                self._record_reclaim_barrier_event(
                    model_id=model_id,
                    operation="restart_unload_stage",
                    stage="backend_unload",
                    error_code=(
                        unloaded.error_code.value
                        if unloaded.error_code is not None
                        else None
                    ),
                    message=unloaded.message,
                )
            return RestartResult(
                ok=False,
                message=f"restart unload failed: {unloaded.message}",
                error_code=unloaded.error_code or RuntimeErrorCode.backend_error,
                model_id=model_id,
                stage="unload",
                retryable=True,
                detail={"unload": asdict(unloaded)},
            )

        reloaded = self.backend.load(model_id, memory_gb=current.memory_gb)
        if not reloaded.ok:
            return RestartResult(
                ok=False,
                message=f"restart load failed: {reloaded.message}",
                error_code=reloaded.error_code or RuntimeErrorCode.backend_error,
                model_id=model_id,
                stage="load",
                retryable=True,
                detail={
                    "unload": asdict(unloaded),
                    "load": asdict(reloaded),
                },
            )
        if was_active:
            self._active_model_id = model_id
        self._touch_model_activity(model_id)
        self._record_governance_transition(
            previous_active=previous_active,
            new_active=self._active_model_id,
        )
        self._record_governance_restart_restore(
            restored_active=was_active and self._active_model_id == model_id
        )
        # Successful restart resolves any prior unresolved
        # restart_unload_stage event for the same model id (auto-resolution
        # rule).
        self._resolve_matching_reclaim_barrier_events(
            model_id=model_id,
            operations={"restart_unload_stage"},
        )
        return RestartResult(
            ok=True,
            message=f"restarted {model_id}",
            model_id=model_id,
            restarted_model=reloaded.model,
            stage="completed",
            retryable=False,
            detail={
                "unload": asdict(unloaded),
                "load": asdict(reloaded),
            },
        )

    def set_model_ttl(self, model_id: str, ttl_seconds: float) -> TTLPolicyResult:
        """Attach a runtime-owned TTL policy to a loaded model."""

        if model_id not in self._loaded_model_ids():
            return TTLPolicyResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
                ttl_enabled=False,
            )
        normalized_ttl = float(ttl_seconds)
        if normalized_ttl <= 0:
            return TTLPolicyResult(
                ok=False,
                message=f"ttl_seconds must be > 0: {ttl_seconds}",
                error_code=RuntimeErrorCode.invalid_request,
                model_id=model_id,
                ttl_enabled=False,
            )
        self._ttl_seconds_by_model_id[model_id] = normalized_ttl
        self._touch_model_activity(model_id)
        self._governance_ttl_events_visible = True
        return TTLPolicyResult(
            ok=True,
            message=f"ttl policy set for {model_id}",
            model_id=model_id,
            ttl_enabled=True,
            ttl_seconds=normalized_ttl,
            detail={
                "ttl_model_ids": sorted(self._ttl_seconds_by_model_id),
                "ttl_policy_mode": "kernel_explicit_sweep",
            },
        )

    def clear_model_ttl(self, model_id: str) -> TTLPolicyResult:
        """Clear a runtime-owned TTL policy from a loaded model."""

        previous_ttl = self._ttl_seconds_by_model_id.pop(model_id, None)
        if previous_ttl is None:
            return TTLPolicyResult(
                ok=False,
                message=f"ttl policy not set: {model_id}",
                error_code=RuntimeErrorCode.invalid_request,
                model_id=model_id,
                ttl_enabled=False,
                detail={"ttl_model_ids": sorted(self._ttl_seconds_by_model_id)},
            )
        self._governance_ttl_events_visible = True
        return TTLPolicyResult(
            ok=True,
            message=f"ttl policy cleared for {model_id}",
            model_id=model_id,
            ttl_enabled=False,
            ttl_seconds=previous_ttl,
            detail={
                "ttl_model_ids": sorted(self._ttl_seconds_by_model_id),
                "ttl_policy_mode": "kernel_explicit_sweep",
            },
        )

    def sweep_expired_models(self, *, now_s: float | None = None) -> TTLSweepResult:
        """Unload expired, unpinned models under the runtime-owned TTL policy."""

        expired_model_ids = list(self._ttl_expired_model_ids(now_s=now_s))
        unloaded_model_ids: list[str] = []
        skipped_pinned_model_ids: list[str] = []
        for model_id in expired_model_ids:
            if model_id in self._pinned_model_ids:
                skipped_pinned_model_ids.append(model_id)
                self._record_eviction_history(
                    model_id=model_id,
                    event="ttl_expiry_blocked_by_pinning",
                )
                continue
            result = self.unload_model(model_id, _operation="ttl_sweep_reclaim")
            if result.ok:
                unloaded_model_ids.append(model_id)
                self._record_eviction_history(
                    model_id=model_id,
                    event="ttl_expired_unloaded",
                )
        if expired_model_ids:
            self._governance_ttl_expiry_visible = True
        return TTLSweepResult(
            ok=True,
            message="ttl sweep completed",
            scanned_model_count=len(self._loaded_model_ids()),
            expired_model_ids=tuple(expired_model_ids),
            unloaded_model_ids=tuple(unloaded_model_ids),
            skipped_pinned_model_ids=tuple(skipped_pinned_model_ids),
            detail={"ttl_policy_mode": "kernel_explicit_sweep"},
        )

    def status(self) -> RuntimeStatus:
        """Return a self-derived runtime status snapshot."""

        backend_status = self.backend.status()
        inventory = self.inventory_snapshot()
        loaded_memory = inventory_to_dict(inventory)["total_loaded_gb"]
        active = self._active_model_id
        inference_health = (
            InferenceHealth.serving
            if backend_status.healthy and backend_status.loaded_models
            else InferenceHealth.reachable_not_serving
            if backend_status.healthy
            else InferenceHealth.down
        )
        health = (
            inventory_health_snapshot(
                inventory,
                active,
                inference_health=inference_health,
                substrate_state=self.abort_recovery.state,
                budget_feasible=True,
            )
            if active is not None
            else {
                "load_state": LoadState.cold.value,
                "inference_health": inference_health.value,
                "truth_level": TruthLevel.unavailable.value,
                "readiness": "degraded" if backend_status.healthy else "blocked",
                "wait_tier": "short_wait" if backend_status.healthy else "currently_unavailable",
                "is_ready": False,
                "block_reason": None if backend_status.healthy else "backend is down",
            }
        )
        return RuntimeStatus(
            backend=backend_status,
            inventory=inventory_to_dict(inventory),
            budget=budget_snapshot(
                currently_loaded_gb=loaded_memory,
                profile=self.profile,
            ),
            health=health,
            generation_gate=self.generation_gate.status,
            active_model_id=active,
        )

    def status_dict(self) -> dict[str, Any]:
        """Return RuntimeStatus as a JSON-ready dict."""

        status = self.status()
        backend_detail = status.backend.detail
        recoverability = backend_detail.get("recoverability", {})
        summary = {
            "runtime": "owlmlx",
            "backend_name": status.backend.backend_name,
            "backend_healthy": status.backend.healthy,
            "readiness": status.health.get("readiness"),
            "block_reason": status.health.get("block_reason"),
            "active_model_id": status.active_model_id,
            "model_count": status.inventory.get("model_count", 0),
            "persistent_child": backend_detail.get("persistent_child", False),
        }
        governance_observations = {
            "transition_count": self._governance_transition_count,
            "recent_window_runs": self._governance_recent_window_runs,
            "active_reassignment_visible": self._governance_active_reassignment_visible,
            "restart_restore_visible": self._governance_restart_restore_visible,
            "explicit_targeting_evidence_visible": (
                self._governance_explicit_targeting_evidence_visible
            ),
            "pinning_events_visible": self._governance_pinning_events_visible,
            "ttl_events_visible": self._governance_ttl_events_visible,
            "ttl_expiry_visible": self._governance_ttl_expiry_visible,
            "eviction_history_events_visible": self._governance_eviction_history_visible,
        }
        expired_model_ids = list(self._ttl_expired_model_ids())
        expired_pinned_model_ids = [
            model_id for model_id in expired_model_ids if model_id in self._pinned_model_ids
        ]
        governance_policy = {
            "pinning_supported": True,
            "ttl_supported": True,
            "eviction_history_visible": bool(self._eviction_history),
            "backend_ttl_visible": False,
            "ttl_policy_mode": "kernel_explicit_sweep",
            "pinned_model_ids": sorted(self._pinned_model_ids),
            "pinned_model_count": len(self._pinned_model_ids),
            "ttl_model_ids": sorted(self._ttl_seconds_by_model_id),
            "ttl_policy_count": len(self._ttl_seconds_by_model_id),
            "ttl_expired_model_ids": expired_model_ids,
            "ttl_expired_pinned_model_ids": expired_pinned_model_ids,
            "eviction_history_count": len(self._eviction_history),
            "recent_eviction_history": list(self._eviction_history[-8:]),
        }
        unresolved_event_count = sum(
            1
            for event in self._reclaim_barrier_events
            if not event.get("resolved", False)
        )
        reclaim_barrier_section = {
            "events": [dict(event) for event in self._reclaim_barrier_events[-32:]],
            "total_event_count": len(self._reclaim_barrier_events),
            "unresolved_event_count": unresolved_event_count,
        }
        load_failure_unresolved = sum(
            1
            for event in self._load_failure_events
            if not event.get("resolved", False)
        )
        load_failure_section = {
            "events": [dict(event) for event in self._load_failure_events[-32:]],
            "total_event_count": len(self._load_failure_events),
            "unresolved_event_count": load_failure_unresolved,
        }
        memory_pressure_cooldown = self._memory_pressure_cooldown_snapshot()
        return {
            "contract": {
                "surface": "owlmlx.runtime.status",
                "version": "stabilization1",
                "stable_sections": [
                    "summary",
                    "health",
                    "inventory",
                    "budget",
                    "restart",
                ],
                "diagnostic_sections": [
                    "backend.detail",
                    "governance_observations",
                    "governance_policy",
                    "generation_gate",
                    "reclaim_barrier",
                    "load_failure",
                    "memory_pressure_cooldown",
                    "host_pressure",
                ],
            },
            "summary": summary,
            "backend": {
                "backend_name": status.backend.backend_name,
                "healthy": status.backend.healthy,
                "loaded_models": [asdict(m) for m in status.backend.loaded_models],
                "detail": status.backend.detail,
            },
            "inventory": status.inventory,
            "budget": status.budget,
            "health": status.health,
            "restart": {
                "active_model_id": status.active_model_id,
                "restartable_models": list(recoverability.get("restartable_models", [])),
                "restart_exhausted_models": list(
                    recoverability.get("restart_exhausted_models", [])
                ),
                "auto_restart_dead_session": backend_detail.get(
                    "auto_restart_dead_session",
                    False,
                ),
            },
            "governance_observations": governance_observations,
            "governance_policy": governance_policy,
            "generation_gate": status.generation_gate,
            "reclaim_barrier": reclaim_barrier_section,
            "load_failure": load_failure_section,
            "memory_pressure_cooldown": memory_pressure_cooldown,
            "host_pressure": dict(self._last_host_pressure_snapshot),
            "active_model_id": status.active_model_id,
            "cache_residency": self._cache_residency_tracker.status_dict(),
            "post_load_warmup": {
                "total_warmup_count": len(self._post_load_warmup_log),
                "log": list(self._post_load_warmup_log[-8:]),
            },
        }
