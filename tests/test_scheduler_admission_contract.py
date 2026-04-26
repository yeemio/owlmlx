from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.abort_recovery import AbortRecoveryTracker
from owlmlx.context_concurrency import HIGH_CONTEXT_THRESHOLD_TOKENS
from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.scheduler_admission_contract import (
    build_scheduler_admission_contract,
    scheduler_admission_contract_to_dict,
)


def _runtime_status_payload() -> dict[str, object]:
    return {
        "summary": {
            "runtime": "owlmlx",
            "backend_name": "fake",
            "backend_healthy": True,
            "readiness": "ready",
            "active_model_id": "fake-a",
            "model_count": 1,
        },
        "backend": {
            "backend_name": "fake",
            "healthy": True,
            "loaded_models": [{"model_id": "fake-a", "memory_gb": 2.0}],
        },
        "health": {
            "readiness": "ready",
        },
        "budget": {
            "serving_budget_gb": 64.0,
            "currently_loaded_gb": 2.0,
            "available_gb": 62.0,
            "utilization": 0.031,
        },
        "restart": {
            "restartable_models": [],
            "restart_exhausted_models": [],
            "auto_restart_dead_session": False,
        },
        "abort_recovery": {
            "state": "clean",
            "recovery_required": False,
            "contamination_reason": "",
            "last_probe_ok": None,
            "last_probe_at": None,
            "last_recovery_at": None,
            "total_high_context_aborts": 0,
        },
        "generation_gate": {
            "generation_gate": "idle",
            "queue_policy": "ticketed_fifo",
            "queue_discipline": "serial",
            "max_concurrent": 1,
            "waiters": 0,
            "pre_gate_admission": {
                "hook_status": "present",
                "hook_boundary": "before_whole_request_gate_claim",
                "hook_mode": "bounded_runtime_owned_cohort_window",
                "cohort_window_status": "idle",
                "cohort_count": 0,
                "open_cohort_size": 0,
                "staged_count": 0,
                "preserved_post_claim_invariants": [
                    "max_concurrent_1_after_gate_claim",
                    "ticketed_fifo_after_gate_claim",
                    "serial_safety_validated_only_after_gate_claim",
                ],
                "forbidden_expansions": [
                    "no_bypass_of_whole_request_gate_claim",
                ],
            },
        },
        "active_model_id": "fake-a",
    }


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def test_scheduler_admission_contract_accepts_interactive_request_when_idle() -> None:
    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="interactive",
        )
    )

    assert payload["contract"]["surface"] == "owlmlx.scheduler_admission_contract"
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["status"] == "partial"
    assert payload["summary"]["admission_decision"] == "accepted"
    assert payload["summary"]["request_class"] == "interactive"
    assert payload["summary"]["resolved_model_id"] == "fake-a"
    assert payload["reason"]["code"] == "runtime_owned_signals_allow_admission"
    assert payload["signals"]["residency"]["target_model_resident"] is True
    assert "no_hidden_bypass_of_whole_request_gate_claim" in payload["preserved_invariants"]


def test_scheduler_admission_contract_defers_when_waiters_are_visible() -> None:
    runtime_status = _runtime_status_payload()
    generation_gate = dict(runtime_status["generation_gate"])
    generation_gate["waiters"] = 2
    generation_gate["generation_gate"] = "active"
    runtime_status["generation_gate"] = generation_gate

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=runtime_status,
            request_class="stream",
        )
    )

    assert payload["summary"]["admission_decision"] == "deferred"
    assert payload["summary"]["confidence"] == "high"
    assert payload["reason"]["code"] == "visible_generation_gate_waiters"


def test_scheduler_admission_contract_defers_when_pre_gate_window_is_staged() -> None:
    runtime_status = _runtime_status_payload()
    generation_gate = dict(runtime_status["generation_gate"])
    pre_gate = dict(generation_gate["pre_gate_admission"])
    pre_gate["cohort_window_status"] = "open_for_join"
    pre_gate["staged_count"] = 2
    generation_gate["pre_gate_admission"] = pre_gate
    runtime_status["generation_gate"] = generation_gate

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=runtime_status,
            request_class="benchmark",
        )
    )

    assert payload["summary"]["admission_decision"] == "deferred"
    assert payload["reason"]["code"] == "pre_claim_window_already_staged"


def test_scheduler_admission_contract_rejects_when_no_target_model_is_available() -> None:
    runtime_status = _runtime_status_payload()
    runtime_status["active_model_id"] = None
    runtime_status["summary"] = {**runtime_status["summary"], "active_model_id": None}
    runtime_status["backend"] = {
        "backend_name": "fake",
        "healthy": True,
        "loaded_models": [],
    }

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=runtime_status,
            request_class="interactive",
        )
    )

    assert payload["summary"]["admission_decision"] == "rejected"
    assert payload["reason"]["code"] == "no_target_model_resolved"


def test_scheduler_admission_contract_rejects_non_resident_target_model() -> None:
    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="interactive",
            model_id="fake-b",
        )
    )

    assert payload["summary"]["admission_decision"] == "rejected"
    assert payload["reason"]["code"] == "target_model_not_resident"
    assert payload["signals"]["residency"]["target_model_resident"] is False


def test_scheduler_admission_contract_rejects_when_recovery_barrier_is_hard() -> None:
    tracker = AbortRecoveryTracker()
    tracker.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    tracker.apply_probe_result(passed=False, reason="scheduler loop", now=1005.0)

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="interactive",
            abort_recovery_snapshot=tracker.snapshot(),
        )
    )

    assert payload["summary"]["admission_decision"] == "rejected"
    assert payload["reason"]["code"] == "recovery_supervisor_hard_barrier"
    assert payload["signals"]["recovery"]["recovery_state"] == "contaminated"
    assert payload["signals"]["recovery"]["hard_recovery_barrier"] is True


def test_scheduler_admission_contract_surfaces_probing_without_global_reject() -> None:
    tracker = AbortRecoveryTracker()
    tracker.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="interactive",
            abort_recovery_snapshot=tracker.snapshot(),
        )
    )

    assert payload["summary"]["admission_decision"] == "accepted"
    assert payload["signals"]["recovery"]["recovery_state"] == "probing"
    assert payload["signals"]["recovery"]["high_context_barrier"] is True
    assert payload["signals"]["request_context_length"]["classification"] == "unknown"
    assert (
        payload["signals"]["recovery"]["decision_impact"]
        == "high_context_barrier_visible_without_request_context_length"
    )
    assert any(
        item["signal"] == "runtime_visible_context_tokens"
        for item in payload["missing_signals"]
    )


def test_scheduler_admission_contract_defers_known_high_context_during_recovery_probe() -> None:
    tracker = AbortRecoveryTracker()
    tracker.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="interactive",
            abort_recovery_snapshot=tracker.snapshot(),
            context_tokens=HIGH_CONTEXT_THRESHOLD_TOKENS + 1,
        )
    )

    assert payload["summary"]["admission_decision"] == "deferred"
    assert payload["reason"]["code"] == "recovery_probing_high_context_deferred"
    assert payload["signals"]["request_context_length"]["classification"] == "high_context"
    assert (
        payload["signals"]["request_context_length"]["decision_impact"]
        == "recovery_probing_defers_this_high_context_request"
    )


def test_scheduler_admission_contract_allows_known_non_high_context_during_recovery_probe() -> None:
    tracker = AbortRecoveryTracker()
    tracker.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="interactive",
            abort_recovery_snapshot=tracker.snapshot(),
            context_tokens=HIGH_CONTEXT_THRESHOLD_TOKENS,
        )
    )

    assert payload["summary"]["admission_decision"] == "accepted"
    assert payload["reason"]["code"] == "runtime_owned_signals_allow_admission"
    assert payload["signals"]["request_context_length"]["classification"] == "non_high_context"
    assert (
        payload["signals"]["recovery"]["decision_impact"]
        == "high_context_barrier_not_decisive_for_known_non_high_context"
    )


def test_scheduler_admission_contract_hard_recovery_barrier_rejects_regardless_of_context() -> None:
    tracker = AbortRecoveryTracker()
    tracker.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    tracker.apply_probe_result(passed=False, reason="scheduler loop", now=1005.0)

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="interactive",
            abort_recovery_snapshot=tracker.snapshot(),
            context_tokens=1,
        )
    )

    assert payload["summary"]["admission_decision"] == "rejected"
    assert payload["reason"]["code"] == "recovery_supervisor_hard_barrier"
    assert payload["signals"]["request_context_length"]["classification"] == "non_high_context"


def test_scheduler_admission_contract_keeps_generic_maintenance_unknown() -> None:
    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="maintenance",
        )
    )

    assert payload["summary"]["admission_decision"] == "unknown"
    assert payload["reason"]["code"] == "maintenance_admission_semantics_not_frozen"
    assert payload["request_class_support"]["maintenance"]["classification_status"] == "partial"


def test_scheduler_admission_contract_normalizes_unknown_request_class() -> None:
    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=_runtime_status_payload(),
            request_class="background-bulk",
        )
    )

    assert payload["summary"]["request_class"] == "unknown"
    assert payload["summary"]["admission_decision"] == "unknown"
    assert payload["reason"]["code"] == "request_class_unknown"


def test_runtime_scheduler_admission_contract_route_returns_surface() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get(
        "/v1/runtime/scheduler-admission-contract",
        params={"request_class": "interactive"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.scheduler_admission_contract"
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["admission_decision"] == "accepted"
    assert payload["signals"]["generation_gate"]["queue_policy"] == "ticketed_fifo"


def test_runtime_scheduler_admission_contract_route_rejects_contaminated_recovery() -> None:
    runtime = RuntimeKernel(FakeBackend(), profile=_profile())
    runtime.abort_recovery.record_abort(
        context_tokens=60000,
        error_type="stream_error",
        now=1000.0,
    )
    runtime.abort_recovery.apply_probe_result(
        passed=False,
        reason="scheduler loop",
        now=1005.0,
    )
    client = TestClient(create_app(runtime))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get(
        "/v1/runtime/scheduler-admission-contract",
        params={"request_class": "interactive"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["admission_decision"] == "rejected"
    assert payload["reason"]["code"] == "recovery_supervisor_hard_barrier"


def test_runtime_scheduler_admission_contract_route_defers_probing_high_context() -> None:
    runtime = RuntimeKernel(FakeBackend(), profile=_profile())
    runtime.abort_recovery.record_abort(
        context_tokens=60000,
        error_type="stream_error",
        now=1000.0,
    )
    client = TestClient(create_app(runtime))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get(
        "/v1/runtime/scheduler-admission-contract",
        params={
            "request_class": "interactive",
            "context_tokens": HIGH_CONTEXT_THRESHOLD_TOKENS + 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["admission_decision"] == "deferred"
    assert payload["reason"]["code"] == "recovery_probing_high_context_deferred"
    assert payload["signals"]["request_context_length"]["classification"] == "high_context"


def test_scheduler_admission_contract_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "scheduler_admission_contract.py")
        .read_text()
    )
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
