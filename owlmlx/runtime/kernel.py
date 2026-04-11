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
from owlmlx.serving import GenerationGate

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
            self._active_model_id = model_id
        return result

    def _resolve_target_model(self, model_id: str | None) -> str | None:
        return model_id or self._active_model_id

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

        gated = await self.generation_gate.execute_async(call_backend)
        result = gated.value
        if not isinstance(result, GenerateResult):
            return GenerateResult(
                ok=False,
                message="backend returned invalid generation result",
                error_code=RuntimeErrorCode.backend_error,
                model_id=target_model,
                detail={"raw_result": repr(result)},
            )
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

        gated = await self.generation_gate.execute_async(call_backend)
        result = gated.value
        if not isinstance(result, GenerateResult):
            return GenerateResult(
                ok=False,
                message="backend returned invalid generation result",
                error_code=RuntimeErrorCode.backend_error,
                model_id=target_model,
                detail={"raw_result": repr(result)},
            )
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

        async with self.generation_gate.stream_session() as gate_start:
            for event in self.backend.stream_generate(target_model, prompt, **kwargs):
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

        async with self.generation_gate.stream_session() as gate_start:
            for event in self.backend.stream_generate_messages(target_model, messages, **kwargs):
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

    def unload_model(self, model_id: str) -> UnloadResult:
        """Unload a model through the backend and clear active model if needed."""

        result = self.backend.unload(model_id)
        if result.ok and self._active_model_id == model_id:
            remaining = self.backend.status().loaded_models
            self._active_model_id = remaining[-1].model_id if remaining else None
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
            )

        was_active = self._active_model_id == model_id
        unloaded = self.backend.unload(model_id)
        if not unloaded.ok:
            return RestartResult(
                ok=False,
                message=f"restart unload failed: {unloaded.message}",
                error_code=unloaded.error_code or RuntimeErrorCode.backend_error,
                model_id=model_id,
                detail={"unload": asdict(unloaded)},
            )

        reloaded = self.backend.load(model_id, memory_gb=current.memory_gb)
        if not reloaded.ok:
            return RestartResult(
                ok=False,
                message=f"restart load failed: {reloaded.message}",
                error_code=reloaded.error_code or RuntimeErrorCode.backend_error,
                model_id=model_id,
                detail={
                    "unload": asdict(unloaded),
                    "load": asdict(reloaded),
                },
            )
        if was_active:
            self._active_model_id = model_id
        return RestartResult(
            ok=True,
            message=f"restarted {model_id}",
            model_id=model_id,
            restarted_model=reloaded.model,
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
        return {
            "backend": {
                "backend_name": status.backend.backend_name,
                "healthy": status.backend.healthy,
                "loaded_models": [asdict(m) for m in status.backend.loaded_models],
                "detail": status.backend.detail,
            },
            "inventory": status.inventory,
            "budget": status.budget,
            "health": status.health,
            "generation_gate": status.generation_gate,
            "active_model_id": status.active_model_id,
        }
