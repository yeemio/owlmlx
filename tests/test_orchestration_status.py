from __future__ import annotations

from pathlib import Path

from owlmlx.orchestration_status import (
    build_orchestration_status,
    orchestration_status_to_dict,
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
            "loaded_models": [{"model_id": "fake-a", "memory_gb": 2.0, "backend": "fake"}],
        },
        "inventory": {"model_count": 1},
        "budget": {
            "system_memory_gb": 64.0,
            "system_reserve_gb": 0.0,
            "serving_budget_gb": 64.0,
            "warning_threshold_gb": 56.0,
            "currently_loaded_gb": 2.0,
            "available_gb": 62.0,
            "utilization": 0.031,
        },
        "restart": {
            "restartable_models": [],
            "restart_exhausted_models": [],
            "auto_restart_dead_session": False,
        },
        "generation_gate": {
            "generation_gate": "idle",
            "queue_policy": "ticketed_fifo",
            "queue_discipline": "serial",
            "max_concurrent": 1,
            "waiters": 0,
            "pre_gate_admission": {
                "hook_status": "present",
                "hook_mode": "bounded_runtime_owned_cohort_window",
                "cohort_window_status": "idle",
                "cohort_count": 0,
                "staged_count": 0,
                "cohort_handoff_status": "visible",
            },
        },
        "governance_observations": {
            "recent_window_runs": 1,
            "restart_restore_visible": False,
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
        "governance_policy": {
            "pinning_supported": True,
            "ttl_supported": True,
            "eviction_history_visible": False,
            "pinned_model_ids": [],
            "pinned_model_count": 0,
            "ttl_model_ids": [],
            "ttl_policy_count": 0,
            "ttl_expired_model_ids": [],
            "ttl_expired_pinned_model_ids": [],
            "eviction_history_count": 0,
            "recent_eviction_history": [],
        },
        "active_model_id": "fake-a",
    }


def test_orchestration_status_defaults_to_partial_unknown_when_idle() -> None:
    status = build_orchestration_status(runtime_status=_runtime_status_payload())
    payload = orchestration_status_to_dict(status)

    assert payload["contract"]["surface"] == "owlmlx.orchestration_status"
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["status"] == "partial"
    assert payload["summary"]["bottleneck_layer"] == "unknown"
    assert payload["summary"]["confidence"] == "low"
    assert payload["layer_assessment"]["admission"]["classification_status"] == "supported"
    assert payload["layer_assessment"]["generation_gate"]["classification_status"] == "supported"
    assert payload["layer_assessment"]["memory_pressure"]["classification_status"] == "partial"
    assert payload["child_surfaces"]["admission"]["surface"] == "owlmlx.scheduler_admission_contract"
    assert payload["child_surfaces"]["model_residency"]["surface"] == "owlmlx.model_residency_policy"
    assert payload["child_surfaces"]["memory_pressure"]["surface"] == "owlmlx.memory_pressure_contract"
    assert payload["child_surfaces"]["recovery_supervisor"]["surface"] == "owlmlx.recovery_supervisor_contract"
    assert "owlmlx.scheduler_admission_contract" in payload["upstream_truth_sources"]
    assert "owlmlx.request_context_length_truth" in payload["upstream_truth_sources"]
    assert "owlmlx.recovery_supervisor_contract" in payload["upstream_truth_sources"]
    assert "max_concurrent_1_after_gate_claim" in payload["preserved_invariants"]
    assert payload["scheduler"]["request_context_length"]["classification"] == "unknown"
    assert payload["stream"]["hold_scope"] == "backend_producer_turn"
    assert payload["residency"]["resident_model_count"] == 1
    assert payload["pressure"]["pressure_classification"] == "within_budget"


def test_orchestration_status_marks_generation_gate_when_waiters_visible() -> None:
    runtime_status = _runtime_status_payload()
    generation_gate = dict(runtime_status["generation_gate"])
    generation_gate["waiters"] = 2
    runtime_status["generation_gate"] = generation_gate

    status = build_orchestration_status(runtime_status=runtime_status)
    payload = orchestration_status_to_dict(status)

    assert payload["summary"]["bottleneck_layer"] == "generation_gate"
    assert payload["summary"]["confidence"] == "high"
    assert payload["scheduler"]["reason_code"] == "scheduler_admission_deferred_generation_gate"


def test_orchestration_status_marks_admission_when_pre_gate_staging_visible() -> None:
    runtime_status = _runtime_status_payload()
    generation_gate = dict(runtime_status["generation_gate"])
    pre_gate = dict(generation_gate["pre_gate_admission"])
    pre_gate["staged_count"] = 3
    generation_gate["pre_gate_admission"] = pre_gate
    runtime_status["generation_gate"] = generation_gate

    status = build_orchestration_status(runtime_status=runtime_status)
    payload = orchestration_status_to_dict(status)

    assert payload["summary"]["bottleneck_layer"] == "admission"
    assert payload["summary"]["confidence"] == "high"
    assert payload["scheduler"]["reason_code"] == "scheduler_admission_deferred_pre_claim"


def test_orchestration_status_marks_memory_pressure_when_pressure_contract_over_budget() -> None:
    runtime_status = _runtime_status_payload()
    runtime_status["budget"] = {
        "system_memory_gb": 64.0,
        "system_reserve_gb": 0.0,
        "serving_budget_gb": 64.0,
        "warning_threshold_gb": 56.0,
        "currently_loaded_gb": 66.0,
        "available_gb": -2.0,
        "utilization": 1.031,
    }

    status = build_orchestration_status(runtime_status=runtime_status)
    payload = orchestration_status_to_dict(status)

    assert payload["summary"]["bottleneck_layer"] == "memory_pressure"
    assert payload["summary"]["confidence"] == "high"
    assert payload["pressure"]["pressure_classification"] == "over_budget"
    assert payload["pressure"]["runtime_owned_pressure_victim_selection"] is False


def test_orchestration_status_marks_recovery_when_supervisor_barrier_visible() -> None:
    runtime_status = _runtime_status_payload()
    runtime_status["restart"] = {
        "restartable_models": [],
        "restart_exhausted_models": ["fake-a"],
        "auto_restart_dead_session": True,
    }

    status = build_orchestration_status(runtime_status=runtime_status)
    payload = orchestration_status_to_dict(status)

    assert payload["summary"]["bottleneck_layer"] == "recovery"
    assert payload["summary"]["confidence"] == "high"
    assert payload["scheduler"]["reason_code"] == "restart_attempts_exhausted"
    assert payload["recovery"]["recovery_state"] == "restart_exhausted"
    assert payload["recovery"]["hard_recovery_barrier"] is True


def test_orchestration_status_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__).parents[1].joinpath("owlmlx", "orchestration_status.py").read_text()
    )
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
