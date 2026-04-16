"""Executable RuntimeKernel for owlmlx Runtime-0."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Any

from owlmlx.abort_recovery import AbortRecoveryTracker
from owlmlx.memory_budget import (
    BudgetVerdict,
    MachineMemoryProfile,
    budget_snapshot,
    default_machine_profile,
)
from owlmlx.model_inventory import (
    LoadedModelEntry,
    ModelInventorySnapshot,
    inventory_budget_check,
    inventory_health_snapshot,
    inventory_to_dict,
)
from owlmlx.runtime_health import InferenceHealth, LoadState, TruthLevel
from owlmlx.serving import GenerationGate, PreGateAdmissionMetadata

from .backends import RuntimeBackend
from .types import (
    ChatTurn,
    GenerateResult,
    LoadResult,
    RestartResult,
    RuntimeErrorCode,
    RuntimeStatus,
    StreamEvent,
    UnloadResult,
)


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
    ) -> None:
        self.backend = backend
        self.profile = profile if profile is not None else default_machine_profile()
        self.generation_gate = generation_gate if generation_gate is not None else GenerationGate()
        self.abort_recovery = abort_recovery if abort_recovery is not None else AbortRecoveryTracker()
        self._active_model_id: str | None = None
        self._governance_transition_count = 0
        self._governance_recent_window_runs = 0
        self._governance_active_reassignment_visible = False
        self._governance_restart_restore_visible = False
        self._governance_explicit_targeting_evidence_visible = False

    @property
    def active_model_id(self) -> str | None:
        """Current default model used when generate() omits model_id."""

        return self._active_model_id

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

    def load_model(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        """Load a model after owlmlx memory-budget preflight."""

        requested_gb = (
            memory_gb
            if memory_gb is not None
            else self.backend.status().detail.get("default_memory_gb")
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
            self._record_governance_transition(
                previous_active=previous_active,
                new_active=self._active_model_id,
            )
        return result

    def _resolve_target_model(self, model_id: str | None) -> str | None:
        return model_id or self._active_model_id

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

        def call_backend() -> GenerateResult:
            assert target_model is not None
            return self.backend.generate(target_model, prompt, **kwargs)

        gated = await self.generation_gate.execute_async_with_admission(
            self._build_pre_gate_admission_metadata(
                request_kind="generate",
                model_id=target_model,
                stream=False,
                prompt=prompt,
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

        async with self.generation_gate.stream_session_with_admission(
            self._build_pre_gate_admission_metadata(
                request_kind="generate_stream",
                model_id=target_model,
                stream=True,
                prompt=prompt,
            )
        ) as gate_start:
            saw_non_error_event = False
            for event in self.backend.stream_generate(target_model, prompt, **kwargs):
                if event.event != "error":
                    saw_non_error_event = True
                yield StreamEvent(
                    event=event.event,
                    model_id=event.model_id,
                    text=event.text,
                    error_code=event.error_code,
                    finish_reason=event.finish_reason,
                    sequence=event.sequence,
                    prompt_tokens=event.prompt_tokens,
                    completion_tokens=event.completion_tokens,
                    wait_time_s=gate_start.wait_time_s,
                    execution_time_s=event.execution_time_s,
                    was_queued=gate_start.was_queued,
                    detail=event.detail,
                )
            if saw_non_error_event:
                self._record_governance_explicit_targeting(model_id)

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

        async with self.generation_gate.stream_session_with_admission(
            self._build_pre_gate_admission_metadata(
                request_kind="generate_stream_messages",
                model_id=target_model,
                stream=True,
                messages=messages,
            )
        ) as gate_start:
            saw_non_error_event = False
            for event in self.backend.stream_generate_messages(target_model, messages, **kwargs):
                if event.event != "error":
                    saw_non_error_event = True
                yield StreamEvent(
                    event=event.event,
                    model_id=event.model_id,
                    text=event.text,
                    error_code=event.error_code,
                    finish_reason=event.finish_reason,
                    sequence=event.sequence,
                    prompt_tokens=event.prompt_tokens,
                    completion_tokens=event.completion_tokens,
                    wait_time_s=gate_start.wait_time_s,
                    execution_time_s=event.execution_time_s,
                    was_queued=gate_start.was_queued,
                    detail=event.detail,
                )
            if saw_non_error_event:
                self._record_governance_explicit_targeting(model_id)

    def unload_model(self, model_id: str) -> UnloadResult:
        """Unload a model through the backend and clear active model if needed."""

        previous_active = self._active_model_id
        result = self.backend.unload(model_id)
        if result.ok and self._active_model_id == model_id:
            remaining = self.backend.status().loaded_models
            self._active_model_id = remaining[-1].model_id if remaining else None
        if result.ok:
            self._record_governance_transition(
                previous_active=previous_active,
                new_active=self._active_model_id,
            )
        return result

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
        self._record_governance_transition(
            previous_active=previous_active,
            new_active=self._active_model_id,
        )
        self._record_governance_restart_restore(
            restored_active=was_active and self._active_model_id == model_id
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
        }
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
                    "generation_gate",
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
            "generation_gate": status.generation_gate,
            "active_model_id": status.active_model_id,
        }
