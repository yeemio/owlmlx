from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.settle_barrier_event import (
    BARRIER_STATE_VOCABULARY,
    OPERATION_VOCABULARY,
    SETTLE_BARRIER_EVENT_SURFACE,
    REQUIRED_EVENT_FIELDS,
    build_settle_barrier_event,
    settle_barrier_event_to_dict,
)
from owlmlx.recovery_supervisor import (
    build_recovery_supervisor_contract,
    recovery_supervisor_contract_to_dict,
)
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.backends import RuntimeBackend
from owlmlx.runtime.server import create_app
from owlmlx.runtime.types import (
    LoadResult,
    RuntimeErrorCode,
    UnloadResult,
)


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


class _FailingUnloadFakeBackend(FakeBackend):
    """Fake backend whose unload reaches the cleanup boundary and fails.

    Used to simulate a real cleanup-boundary failure (RuntimeErrorCode
    backend_error) rather than a missing-model preflight failure.
    """

    def __init__(
        self,
        *,
        fail_unload_for: set[str] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._fail_unload_for = set(fail_unload_for or set())

    def unload(self, model_id: str) -> UnloadResult:
        if model_id in self._fail_unload_for:
            # The model is still resident; we simulate a backend cleanup
            # boundary error rather than evicting it from the dict.
            return UnloadResult(
                ok=False,
                message=f"injected backend cleanup failure for {model_id}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
                freed_gb=0.0,
            )
        return super().unload(model_id)


def test_clean_runtime_reports_no_failed_unload_or_settle_barrier_event() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_profile())
    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )

    assert payload["contract"]["surface"] == SETTLE_BARRIER_EVENT_SURFACE
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["barrier_state"] == "clean"
    assert payload["barrier"]["hard_recovery_barrier"] is False
    assert payload["barrier"]["unresolved_event_count"] == 0
    assert payload["events"] == []


def test_explicit_unload_failure_records_failed_unload() -> None:
    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)

    result = kernel.unload_model("fake-a")
    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error

    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )
    assert payload["summary"]["barrier_state"] == "failed_unload"
    assert payload["barrier"]["hard_recovery_barrier"] is True
    assert payload["barrier"]["unresolved_event_count"] == 1
    assert len(payload["events"]) == 1
    event = payload["events"][0]
    for field in REQUIRED_EVENT_FIELDS:
        assert field in event, f"missing field: {field}"
    assert event["model_id"] == "fake-a"
    assert event["operation"] == "explicit_unload"
    assert event["stage"] == "backend_unload"
    assert event["resolved"] is False


def test_pinned_unload_block_does_not_record_failed_unload_event() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_profile())
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.pin_model("fake-a")

    result = kernel.unload_model("fake-a")
    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_pinned

    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )
    assert payload["summary"]["barrier_state"] == "clean"
    assert payload["events"] == []


def test_missing_model_unload_does_not_record_failed_unload_event() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_profile())

    result = kernel.unload_model("never-loaded")
    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded

    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )
    assert payload["summary"]["barrier_state"] == "clean"
    assert payload["events"] == []


def test_ttl_sweep_failure_records_failed_reclaim() -> None:
    state = {"now": 100.0}

    def clock() -> float:
        return float(state["now"])

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
        clock=clock,
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.set_model_ttl("fake-a", 30.0)
    state["now"] = 200.0

    sweep = kernel.sweep_expired_models()
    assert sweep.expired_model_ids == ("fake-a",)
    assert sweep.unloaded_model_ids == ()  # unload failed

    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )
    assert payload["summary"]["barrier_state"] == "failed_reclaim"
    assert payload["barrier"]["unresolved_event_count"] == 1
    event = payload["events"][0]
    assert event["operation"] == "ttl_sweep_reclaim"
    assert event["model_id"] == "fake-a"


def test_ttl_pinned_skip_does_not_record_reclaim_failure_barrier() -> None:
    state = {"now": 100.0}

    def clock() -> float:
        return float(state["now"])

    kernel = RuntimeKernel(FakeBackend(), profile=_profile(), clock=clock)
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.pin_model("fake-a")
    kernel.set_model_ttl("fake-a", 30.0)
    state["now"] = 200.0

    sweep = kernel.sweep_expired_models()
    assert sweep.skipped_pinned_model_ids == ("fake-a",)

    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )
    assert payload["summary"]["barrier_state"] == "clean"
    assert payload["events"] == []


def test_restart_unload_stage_failure_records_restart_unload_failed() -> None:
    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)

    restart = kernel.restart_model("fake-a")
    assert restart.ok is False
    assert restart.stage == "unload"

    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )
    assert payload["summary"]["barrier_state"] == "restart_unload_failed"
    assert payload["barrier"]["unresolved_event_count"] == 1
    event = payload["events"][0]
    assert event["operation"] == "restart_unload_stage"
    assert event["stage"] == "backend_unload"


def test_recovery_supervisor_reports_hard_barrier_when_event_unresolved() -> None:
    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")  # records failed_unload event

    payload = recovery_supervisor_contract_to_dict(
        build_recovery_supervisor_contract(
            runtime_status=kernel.status_dict(),
            abort_recovery_snapshot=kernel.abort_recovery.snapshot(),
        )
    )
    assert payload["summary"]["recovery_state"] == "failed_reclaim_barrier"
    assert payload["barrier"]["hard_recovery_barrier"] is True
    assert payload["lifecycle"]["reclaim_barrier_state"] == "failed_unload"
    assert payload["lifecycle"]["reclaim_barrier_unresolved_event_count"] == 1


def test_scheduler_admission_rejects_when_reclaim_barrier_active() -> None:
    from owlmlx.scheduler_admission import (
        build_scheduler_admission_contract,
        scheduler_admission_contract_to_dict,
    )

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=kernel.status_dict(),
            request_class="interactive",
            abort_recovery_snapshot=kernel.abort_recovery.snapshot(),
        )
    )
    assert payload["summary"]["admission_decision"] == "rejected"


def test_orchestration_status_reports_recovery_bottleneck_when_event_unresolved() -> None:
    from owlmlx.orchestration_status import (
        build_orchestration_status,
        orchestration_status_to_dict,
    )

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")

    payload = orchestration_status_to_dict(
        build_orchestration_status(
            runtime_status=kernel.status_dict(),
            abort_recovery_snapshot=kernel.abort_recovery.snapshot(),
        )
    )
    assert payload["summary"]["bottleneck_layer"] == "recovery"
    assert payload["recovery"]["hard_recovery_barrier"] is True


def test_memory_pressure_contract_does_not_claim_reclaim_engine_or_pressure_eviction() -> None:
    from owlmlx.memory_pressure_classifier import (
        build_memory_pressure_contract,
        memory_pressure_contract_to_dict,
    )

    kernel = RuntimeKernel(FakeBackend(), profile=_profile())
    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(runtime_status=kernel.status_dict())
    )
    boundaries = payload["policy_boundaries"]
    assert boundaries["runtime_owned_pressure_victim_selection"] is False
    assert boundaries["runtime_owned_reclaim_barrier"] is False
    assert "pressure_ranked_eviction" in boundaries["out_of_scope"]
    assert "reclaim_engine" in boundaries["out_of_scope"]


def test_settle_barrier_event_route_returns_payload() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.get("/v1/runtime/reclaim-barrier-event")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == SETTLE_BARRIER_EVENT_SURFACE
    assert payload["summary"]["barrier_state"] == "clean"
    assert payload["summary"]["supported_barrier_states"] == list(BARRIER_STATE_VOCABULARY)
    assert payload["summary"]["supported_operations"] == list(OPERATION_VOCABULARY)


def test_settle_barrier_event_route_after_failed_unload_reports_hard_barrier() -> None:
    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    client = TestClient(create_app(kernel))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 1.0})
    unload_response = client.post("/v1/unload", json={"model_id": "fake-a"})
    assert unload_response.status_code == 500
    unload_payload = unload_response.json()
    assert unload_payload["object"] == "error"
    assert unload_payload["error_code"] == "backend_error"
    assert unload_payload["http_status"] == 500

    response = client.get("/v1/runtime/reclaim-barrier-event")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["barrier_state"] == "failed_unload"
    assert payload["barrier"]["hard_recovery_barrier"] is True


def test_settle_barrier_event_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__).parents[1]
        / "owlmlx"
        / "settle_barrier_event.py"
    ).read_text()
    forbidden = ["llm_router", "ops_dashboard", "AI/Agent", "owlops", "owlcoda"]
    for pattern in forbidden:
        assert pattern not in source


def test_decision_vocabulary_is_stable() -> None:
    assert set(OPERATION_VOCABULARY) == {
        "explicit_unload",
        "ttl_sweep_reclaim",
        "restart_unload_stage",
        "unknown",
    }
    assert set(BARRIER_STATE_VOCABULARY) == {
        "clean",
        "failed_unload",
        "failed_reclaim",
        "restart_unload_failed",
        "unknown",
    }


def test_unknown_state_when_runtime_status_has_no_section() -> None:
    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status={})
    )
    assert payload["summary"]["barrier_state"] == "unknown"
    assert payload["barrier"]["hard_recovery_barrier"] is False
    assert payload["barrier"]["classification_status"] == "insufficient_signal"


def test_resolved_event_does_not_create_barrier() -> None:
    payload = settle_barrier_event_to_dict(
        build_settle_barrier_event(
            runtime_status={
                "reclaim_barrier": {
                    "events": [
                        {
                            "event_id": 1,
                            "model_id": "fake-a",
                            "operation": "explicit_unload",
                            "source": "runtime_kernel",
                            "stage": "backend_unload",
                            "error_code": "backend_error",
                            "message": "old failure",
                            "recorded_at_s": 1.0,
                            "requires_recovery_barrier": True,
                            "resolved": True,
                        },
                    ],
                    "total_event_count": 1,
                    "unresolved_event_count": 0,
                },
            }
        )
    )
    assert payload["summary"]["barrier_state"] == "clean"
