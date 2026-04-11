"""Executable RuntimeKernel for owlmlx Runtime-0."""

from __future__ import annotations

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
    GenerateResult,
    LoadResult,
    RuntimeErrorCode,
    RuntimeStatus,
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

        requested_gb = self.backend.status().detail.get("default_memory_gb", memory_gb)
        if memory_gb is not None:
            requested_gb = memory_gb
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

    async def generate(
        self,
        prompt: str,
        *,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> GenerateResult:
        """Generate text through the backend under GenerationGate discipline."""

        target_model = model_id or self._active_model_id
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

        def call_backend() -> GenerateResult:
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
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            wait_time_s=gated.wait_time_s,
            execution_time_s=gated.execution_time_s,
            was_queued=gated.was_queued,
        )

    def unload_model(self, model_id: str) -> UnloadResult:
        """Unload a model through the backend and clear active model if needed."""

        result = self.backend.unload(model_id)
        if result.ok and self._active_model_id == model_id:
            remaining = self.backend.status().loaded_models
            self._active_model_id = remaining[-1].model_id if remaining else None
        return result

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
