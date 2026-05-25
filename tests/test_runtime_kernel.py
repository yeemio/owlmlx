from __future__ import annotations

import asyncio
import importlib
import sys
import threading
import types

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeErrorCode, RuntimeKernel
from owlmlx.serving import GenerationGate


def _small_profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def _clock_box(start: float = 100.0):
    state = {"now": float(start)}

    def clock() -> float:
        return float(state["now"])

    return state, clock


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


def test_kernel_blocks_load_when_host_pressure_sample_crosses_threshold() -> None:
    backend = FakeBackend(default_memory_gb=1.0)
    kernel = RuntimeKernel(
        backend,
        profile=_small_profile(),
        host_pressure_sampler=lambda: {
            "available": True,
            "source": "memory_pressure",
            "classification": "host_pressure_block",
            "reason_code": "free_percent_at_or_below_block_threshold",
            "reason_message": "Host free memory is below threshold.",
            "free_percent": 8.0,
        },
    )

    result = kernel.load_model("blocked-model")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error
    assert result.detail["host_pressure"]["classification"] == "host_pressure_block"
    assert backend.status().loaded_models == ()
    status = kernel.status_dict()
    assert status["host_pressure"]["free_percent"] == 8.0
    assert status["inventory"]["model_count"] == 0


def test_kernel_allows_load_when_host_pressure_sample_is_normal() -> None:
    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0),
        profile=_small_profile(),
        host_pressure_sampler=lambda: {
            "available": True,
            "source": "memory_pressure",
            "classification": "normal",
            "reason_code": "free_percent_above_warning_threshold",
            "reason_message": "Host free memory is above threshold.",
            "free_percent": 95.0,
        },
    )

    result = kernel.load_model("safe-model")

    assert result.ok is True
    assert kernel.status_dict()["host_pressure"]["classification"] == "normal"


def test_kernel_explicit_host_pressure_sample_updates_status_without_loading() -> None:
    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0),
        profile=_small_profile(),
        host_pressure_sampler=lambda: {
            "available": True,
            "source": "memory_pressure",
            "classification": "normal",
            "reason_code": "free_percent_above_warning_threshold",
            "reason_message": "Host free memory is above threshold.",
            "free_percent": 91.0,
        },
    )

    sample = kernel.sample_host_pressure()

    assert sample["classification"] == "normal"
    status = kernel.status_dict()
    assert status["host_pressure"]["free_percent"] == 91.0
    assert status["inventory"]["model_count"] == 0


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


def test_kernel_native_backend_lifecycle_stays_on_backend_worker(
    monkeypatch,
) -> None:
    fake = types.ModuleType("mlx_lm")
    observed: list[tuple[str, int]] = []
    observed_lock = threading.Lock()

    def record(operation: str) -> None:
        with observed_lock:
            observed.append((operation, threading.get_ident()))

    def fake_load(model_id: str) -> tuple[object, object]:
        record("load")
        return (object(), object())

    def fake_generate(model, tokenizer, *, prompt, max_tokens, **kwargs):
        record("generate")
        return f"generated:{prompt}:{max_tokens}"

    class _FakeToken:
        def __init__(self, text: str, finish_reason: str | None = None) -> None:
            self.text = text
            self.finish_reason = finish_reason

    def fake_stream_generate(model, tokenizer, *, prompt, max_tokens, **kwargs):
        record("stream_generate")
        yield _FakeToken("tok", finish_reason="stop")

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)

    import owlmlx.runtime.mlx_native_backend as mod

    mod = importlib.reload(mod)
    try:
        backend = mod.MlxNativeBackend()
        fake_core = types.SimpleNamespace(
            get_active_memory=lambda: 0,
            get_cache_memory=lambda: 0,
            clear_cache=lambda: record("unload"),
        )
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_core)
        caller_thread_id = threading.get_ident()
        kernel = RuntimeKernel(
            backend,
            profile=_small_profile(),
            host_pressure_sampler=lambda: {
                "available": True,
                "source": "test",
                "classification": "normal",
                "reason_code": "test_normal",
                "reason_message": "test normal",
            },
        )

        load = kernel.load_model("fake-native", memory_gb=1.0)

        async def collect_stream():
            return [
                event
                async for event in kernel.generate_stream("hello", max_tokens=2)
            ]

        stream_events = asyncio.run(collect_stream())
        generated = asyncio.run(kernel.generate("hi", max_tokens=3))
        unload = kernel.unload_model("fake-native")

        assert load.ok is True
        assert [event.event for event in stream_events] == ["token", "done"]
        assert generated.ok is True
        assert unload.ok is True

        operation_threads = {
            operation: thread_id for operation, thread_id in observed
        }
        assert set(operation_threads) == {
            "load",
            "stream_generate",
            "generate",
            "unload",
        }
        worker_thread_ids = set(operation_threads.values())
        assert len(worker_thread_ids) == 1
        assert caller_thread_id not in worker_thread_ids
        assert (
            backend.status().detail["thread_affinity"]["worker_thread_id"]
            in worker_thread_ids
        )
    finally:
        sys.modules.pop("mlx_lm", None)
        importlib.reload(mod)


def test_generate_stream_releases_gate_before_first_consumer_completes() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_small_profile())
    kernel.load_model("fake-a")

    async def observe():
        first_has_started = asyncio.Event()
        first_may_finish = asyncio.Event()
        first_consumer_completed = asyncio.Event()
        second_has_started = asyncio.Event()
        first_events: list[str] = []
        second_events: list[str] = []

        async def consume_first() -> None:
            stream = kernel.generate_stream("alpha beta", max_tokens=8)
            first_event = await anext(stream)
            first_events.append(first_event.event)
            first_has_started.set()
            await first_may_finish.wait()
            async for event in stream:
                first_events.append(event.event)
            first_consumer_completed.set()

        async def consume_second() -> None:
            async for event in kernel.generate_stream("gamma delta", max_tokens=8):
                second_events.append(event.event)
                if not second_has_started.is_set():
                    second_has_started.set()

        first_task = asyncio.create_task(consume_first())
        await first_has_started.wait()
        await asyncio.sleep(0.05)
        second_task = asyncio.create_task(consume_second())
        await asyncio.wait_for(second_has_started.wait(), timeout=0.2)
        mid = kernel.status_dict()
        second_started_early = not first_consumer_completed.is_set()
        first_may_finish.set()
        await asyncio.gather(first_task, second_task)
        return second_started_early, mid, first_events, second_events

    second_started_early, mid, first_events, second_events = asyncio.run(observe())

    assert second_started_early is True
    assert mid["generation_gate"]["max_concurrent"] == 1
    assert mid["generation_gate"]["queue_policy"] == "ticketed_fifo"
    assert first_events[0] == "token"
    assert first_events[-1] == "done"
    assert second_events[0] == "token"
    assert second_events[-1] == "done"
    assert kernel.status_dict()["generation_gate"]["total_served"] == 2


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


def test_pinning_blocks_unload_until_unpinned() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())
    kernel.load_model("fake-a")

    pinned = kernel.pin_model("fake-a")
    blocked = kernel.unload_model("fake-a")
    unpinned = kernel.unpin_model("fake-a")
    unloaded = kernel.unload_model("fake-a")

    assert pinned.ok is True
    assert blocked.ok is False
    assert blocked.error_code is RuntimeErrorCode.model_pinned
    assert unpinned.ok is True
    assert unloaded.ok is True


def test_restart_retains_pin_state() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile())
    kernel.load_model("fake-a")
    kernel.pin_model("fake-a")

    restarted = kernel.restart_model("fake-a")

    assert restarted.ok is True
    assert kernel.status_dict()["governance_policy"]["pinned_model_ids"] == ["fake-a"]


def test_ttl_policy_sweep_unloads_expired_unpinned_model() -> None:
    state, clock = _clock_box()
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile(), clock=clock)
    kernel.load_model("fake-a")
    configured = kernel.set_model_ttl("fake-a", 30.0)

    state["now"] = 140.0
    swept = kernel.sweep_expired_models()

    assert configured.ok is True
    assert swept.ok is True
    assert swept.unloaded_model_ids == ("fake-a",)
    assert kernel.status_dict()["inventory"]["model_count"] == 0


def test_ttl_policy_sweep_keeps_expired_pinned_model_loaded() -> None:
    state, clock = _clock_box()
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile(), clock=clock)
    kernel.load_model("fake-a")
    kernel.pin_model("fake-a")
    kernel.set_model_ttl("fake-a", 30.0)

    state["now"] = 140.0
    swept = kernel.sweep_expired_models()

    assert swept.ok is True
    assert swept.unloaded_model_ids == ()
    assert swept.skipped_pinned_model_ids == ("fake-a",)
    status = kernel.status_dict()
    assert status["inventory"]["model_count"] == 1
    assert status["governance_policy"]["ttl_expired_pinned_model_ids"] == ["fake-a"]


def test_ttl_sweep_records_eviction_history_events() -> None:
    state, clock = _clock_box()
    kernel = RuntimeKernel(FakeBackend(), profile=_small_profile(), clock=clock)
    kernel.load_model("fake-a")
    kernel.load_model("fake-b")
    kernel.pin_model("fake-a")
    kernel.set_model_ttl("fake-a", 30.0)
    kernel.set_model_ttl("fake-b", 30.0)

    state["now"] = 140.0
    swept = kernel.sweep_expired_models()
    status = kernel.status_dict()

    assert swept.ok is True
    assert status["governance_policy"]["eviction_history_visible"] is True
    assert status["governance_policy"]["eviction_history_count"] == 2
    assert [
        event["event"] for event in status["governance_policy"]["recent_eviction_history"]
    ] == [
        "ttl_expiry_blocked_by_pinning",
        "ttl_expired_unloaded",
    ]


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


def test_concurrent_generations_handoff_cohort_into_aggregated_child_exchange() -> None:
    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0, generate_delay_s=0.05),
        profile=_small_profile(),
        generation_gate=GenerationGate(pre_gate_window_s=0.02),
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
    status = kernel.status_dict()
    observations = status["backend"]["detail"]["cache_runtime_observations"]
    assert observations["child_exchange_mode"] == "aggregated_non_stream_child_exchange_visible"
    assert observations["aggregated_child_exchange_visible"] is True
    assert observations["aggregated_child_exchange_batch_count"] == 1
    assert observations["aggregated_child_exchange_request_count"] == 2
    assert observations["max_aggregated_child_batch_size"] == 2
    assert status["generation_gate"]["max_concurrent"] == 1
    assert status["generation_gate"]["queue_discipline"] == "serial"
    assert status["generation_gate"]["total_served"] == 2


def test_default_runtime_generation_keeps_single_worker_cohort_window_disabled() -> None:
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
    status = kernel.status_dict()
    observations = status["backend"]["detail"]["cache_runtime_observations"]
    assert observations["aggregated_child_exchange_batch_count"] == 0
    assert observations["aggregated_child_exchange_request_count"] == 0
    hook = status["generation_gate"]["pre_gate_admission"]
    assert hook["window_ms"] == 0
    assert hook["cohort_window_enabled"] is False
    assert hook["peak_cohort_size"] == 1
    assert hook["total_handoffs"] == 0
    assert hook["total_window_wait_s"] == 0.0


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
        "governance_policy",
        "generation_gate",
        "reclaim_barrier",
        "load_failure",
        "memory_pressure_cooldown",
        "host_pressure",
        "speculative_execution_status",
    ]
    assert status["governance_observations"] == {
        "transition_count": 4,
        "recent_window_runs": 2,
        "active_reassignment_visible": True,
        "restart_restore_visible": True,
        "explicit_targeting_evidence_visible": True,
        "pinning_events_visible": False,
        "ttl_events_visible": False,
        "ttl_expiry_visible": False,
        "eviction_history_events_visible": False,
    }


def test_status_dict_exposes_runtime_owned_pre_gate_admission_hook() -> None:
    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0, generate_delay_s=0.05),
        profile=_small_profile(),
        generation_gate=GenerationGate(pre_gate_window_s=0.02),
    )
    kernel.load_model("model-a")

    async def observe():
        first = asyncio.create_task(kernel.generate("one"))
        await asyncio.sleep(0.01)
        second = asyncio.create_task(kernel.generate("two"))
        await asyncio.sleep(0.01)
        mid = kernel.status_dict()
        results = await asyncio.gather(first, second)
        return mid, results

    mid, results = asyncio.run(observe())

    assert all(result.ok for result in results)
    hook = mid["generation_gate"]["pre_gate_admission"]
    assert hook["hook_status"] == "present"
    assert hook["hook_boundary"] == "before_whole_request_gate_claim"
    assert hook["hook_mode"] == "bounded_runtime_owned_cohort_window"
    assert hook["peak_cohort_size"] >= 2
    assert hook["total_staged"] >= 2
    assert (
        hook["cohort_count"] >= 1
        or hook["cohort_handoff_status"] in {
            "active_to_aggregated_child_exchange",
            "visible",
        }
    )
    if hook["cohort_count"] == 0:
        assert hook["last_handoff_request_count"] >= 2
        assert hook["total_handoffs"] >= 1
    assert hook["preserved_post_claim_invariants"] == [
        "max_concurrent_1_after_gate_claim",
        "ticketed_fifo_after_gate_claim",
        "serial_safety_validated_only_after_gate_claim",
    ]


def test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load() -> None:
    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0, generate_delay_s=0.05),
        profile=_small_profile(),
        generation_gate=GenerationGate(pre_gate_window_s=0.02),
    )
    kernel.load_model("fake-a")

    iterations = 3

    async def run_pair(round_id: int):
        return await asyncio.gather(
            kernel.generate(f"round-{round_id}-one"),
            kernel.generate(f"round-{round_id}-two"),
        )

    for round_id in range(iterations):
        first, second = asyncio.run(run_pair(round_id))
        assert first.ok is True
        assert second.ok is True

        status = kernel.status_dict()
        observations = status["backend"]["detail"]["cache_runtime_observations"]
        assert (
            observations["child_exchange_mode"]
            == "aggregated_non_stream_child_exchange_visible"
        )
        assert observations["aggregated_child_exchange_visible"] is True
        assert observations["aggregated_child_exchange_batch_count"] == round_id + 1
        assert observations["aggregated_child_exchange_request_count"] == (round_id + 1) * 2
        assert observations["max_aggregated_child_batch_size"] == 2

        gate = status["generation_gate"]
        assert gate["max_concurrent"] == 1
        assert gate["queue_discipline"] == "serial"
        assert gate["total_served"] == (round_id + 1) * 2

        hook = gate["pre_gate_admission"]
        assert hook["hook_status"] == "present"
        assert hook["hook_boundary"] == "before_whole_request_gate_claim"
        assert hook["hook_mode"] == "bounded_runtime_owned_cohort_window"
        assert hook["total_handoffs"] >= round_id + 1
        assert hook["last_handoff_request_count"] >= 2
        assert hook["preserved_post_claim_invariants"] == [
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ]

    final_status = kernel.status_dict()
    final_observations = final_status["backend"]["detail"]["cache_runtime_observations"]
    assert final_observations["aggregated_child_exchange_batch_count"] == iterations
    assert final_observations["aggregated_child_exchange_request_count"] == iterations * 2
    assert final_observations["max_aggregated_child_batch_size"] == 2

    final_gate = final_status["generation_gate"]
    assert final_gate["total_served"] == iterations * 2
    final_hook = final_gate["pre_gate_admission"]
    assert final_hook["total_handoffs"] >= iterations
    assert final_hook["total_staged"] >= iterations * 2
    assert final_hook["total_claimed"] >= iterations * 2
    assert final_hook["total_discarded"] == 0
