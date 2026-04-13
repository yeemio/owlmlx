from __future__ import annotations

import asyncio

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeErrorCode, RuntimeKernel


def _small_profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def test_kernel_load_model_updates_inventory() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=2.0), profile=_small_profile())

    result = kernel.load_model("fake-a")

    assert result.ok is True
    assert kernel.active_model_id == "fake-a"
    status = kernel.status_dict()
    assert status["inventory"]["model_count"] == 1
    assert status["inventory"]["total_loaded_gb"] == 2.0
    assert status["health"]["readiness"] == "ready"
    assert status["health"]["is_ready"] is True


def test_kernel_rejects_model_that_exceeds_budget() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=7.0), profile=_small_profile())

    result = kernel.load_model("too-large")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.memory_budget_exceeded
    assert "exceed serving budget" in result.message
    assert kernel.status_dict()["inventory"]["model_count"] == 0


def test_kernel_budget_counts_already_loaded_models() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=4.0), profile=_small_profile())

    first = kernel.load_model("fake-a", memory_gb=4.0)
    second = kernel.load_model("fake-b", memory_gb=3.0)

    assert first.ok is True
    assert second.ok is False
    assert second.error_code is RuntimeErrorCode.memory_budget_exceeded
    assert kernel.status_dict()["inventory"]["total_loaded_gb"] == 4.0


def test_generate_before_load_fails() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())

    result = asyncio.run(kernel.generate("hello"))

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded


def test_generate_after_load_uses_active_model() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_small_profile())
    kernel.load_model("fake-a")

    result = asyncio.run(kernel.generate("hello", max_tokens=8))

    assert result.ok is True
    assert result.model_id == "fake-a"
    assert result.text.startswith("hello :: fake completion")
    assert result.wait_time_s is not None
    assert result.execution_time_s is not None
    assert kernel.status_dict()["generation_gate"]["total_served"] == 1


def test_generate_specific_unloaded_model_fails() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())
    kernel.load_model("fake-a")

    result = asyncio.run(kernel.generate("hello", model_id="fake-b"))

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded
    assert result.model_id == "fake-b"


def test_generate_stream_after_load_uses_active_model() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_small_profile())
    kernel.load_model("fake-a")

    async def collect():
        events = []
        async for event in kernel.generate_stream("hello", max_tokens=8):
            events.append(event)
        return events

    events = asyncio.run(collect())

    assert [event.event for event in events][-1] == "done"
    assert events[0].model_id == "fake-a"
    assert events[0].wait_time_s is not None
    assert kernel.status_dict()["generation_gate"]["total_served"] == 1


def test_unload_model_clears_active_model() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())
    kernel.load_model("fake-a")

    result = kernel.unload_model("fake-a")

    assert result.ok is True
    assert result.freed_gb == 1.0
    assert kernel.active_model_id is None
    assert kernel.status_dict()["inventory"]["model_count"] == 0


def test_unload_missing_model_fails() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())

    result = kernel.unload_model("missing")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded


def test_restart_model_roundtrip_keeps_model_loaded() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())
    kernel.load_model("fake-a")

    result = kernel.restart_model("fake-a")

    assert result.ok is True
    assert result.model_id == "fake-a"
    assert result.restarted_model is not None
    assert result.stage == "completed"
    assert result.retryable is False
    status = kernel.status_dict()
    assert status["active_model_id"] == "fake-a"
    assert status["inventory"]["model_count"] == 1


def test_restart_missing_model_fails() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())

    result = kernel.restart_model("missing")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded
    assert result.stage == "preflight"
    assert result.retryable is False


class _UnloadFailBackend(FakeBackend):
    def unload(self, model_id: str):
        loaded = self._loaded.get(model_id)
        return type(super().unload("missing"))(
            ok=False,
            message="forced unload failure",
            error_code=RuntimeErrorCode.backend_error,
            model_id=model_id,
            freed_gb=loaded.memory_gb if loaded is not None else 0.0,
        )


class _LoadFailBackend(FakeBackend):
    def __init__(self) -> None:
        super().__init__()
        self._load_calls = 0

    def load(self, model_id: str, *, memory_gb: float | None = None):
        self._load_calls += 1
        if self._load_calls == 1:
            return super().load(model_id, memory_gb=memory_gb)
        return type(super().load("missing", memory_gb=memory_gb))(
            ok=False,
            message="forced reload failure",
            error_code=RuntimeErrorCode.backend_error,
            model=None,
        )


def test_restart_model_exposes_unload_failure_stage() -> None:
    kernel = RuntimeKernel(_UnloadFailBackend(), profile=_small_profile())
    kernel.load_model("fake-a")

    result = kernel.restart_model("fake-a")

    assert result.ok is False
    assert result.stage == "unload"
    assert result.retryable is True


def test_restart_model_exposes_load_failure_stage() -> None:
    kernel = RuntimeKernel(_LoadFailBackend(), profile=_small_profile())
    kernel.load_model("fake-a")

    result = kernel.restart_model("fake-a")

    assert result.ok is False
    assert result.stage == "load"
    assert result.retryable is True


def test_backend_unhealthy_status_blocks_readiness() -> None:
    kernel = RuntimeKernel(FakeBackend(healthy=False), profile=_small_profile())

    status = kernel.status_dict()

    assert status["backend"]["healthy"] is False
    assert status["health"]["readiness"] == "blocked"
    assert status["health"]["block_reason"] == "backend is down"


def test_concurrent_generations_are_serialized_by_gate() -> None:
    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0, generate_delay_s=0.05),
        profile=_small_profile(),
    )
    kernel.load_model("fake-a")

    async def run_pair():
        return await asyncio.gather(
            kernel.generate("one"),
            kernel.generate("two"),
        )

    first, second = asyncio.run(run_pair())

    assert first.ok is True
    assert second.ok is True
    gate = kernel.status_dict()["generation_gate"]
    assert gate["total_served"] == 2
    assert gate["total_queued"] == 2
    assert first.was_queued is False or second.was_queued is False
    assert first.was_queued is True or second.was_queued is True


def test_status_dict_exposes_governance_observations() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_small_profile())

    kernel.load_model("model-a")
    kernel.load_model("model-b")
    explicit = asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    unload = kernel.unload_model("model-b")
    restart = kernel.restart_model("model-a")

    assert explicit.ok is True
    assert unload.ok is True
    assert restart.ok is True

    status = kernel.status_dict()

    assert "governance_observations" in status
    assert status["contract"]["diagnostic_sections"] == [
        "backend.detail",
        "governance_observations",
        "generation_gate",
    ]
    assert status["governance_observations"] == {
        "transition_count": 4,
        "recent_window_runs": 2,
        "active_reassignment_visible": True,
        "restart_restore_visible": True,
        "explicit_targeting_evidence_visible": True,
    }
