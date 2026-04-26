from __future__ import annotations

from pathlib import Path

from owlmlx.abort_recovery import AbortRecoveryTracker
from owlmlx.recovery_supervisor_contract import (
    build_recovery_supervisor_contract,
    recovery_supervisor_contract_to_dict,
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
        "health": {"readiness": "ready", "block_reason": None},
        "restart": {
            "restartable_models": [],
            "restart_exhausted_models": [],
            "auto_restart_dead_session": False,
        },
        "governance_observations": {
            "recent_window_runs": 1,
            "restart_restore_visible": False,
            "eviction_history_events_visible": False,
        },
    }


def _payload(
    runtime_status: dict[str, object] | None = None,
    tracker: AbortRecoveryTracker | None = None,
) -> dict[str, object]:
    contract = build_recovery_supervisor_contract(
        runtime_status=runtime_status or _runtime_status_payload(),
        abort_recovery_snapshot=(tracker or AbortRecoveryTracker()).snapshot(),
    )
    return recovery_supervisor_contract_to_dict(contract)


def test_recovery_supervisor_contract_clean_runtime_has_no_barrier() -> None:
    payload = _payload()

    assert payload["contract"]["surface"] == "owlmlx.recovery_supervisor_contract"
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["recovery_state"] == "clean"
    assert payload["summary"]["barrier_decision"] == "no_recovery_barrier"
    assert payload["barrier"]["hard_recovery_barrier"] is False
    assert payload["request_impact"]["generation_admissible"] is True
    assert payload["request_impact"]["high_context_generation_admissible"] is True


def test_recovery_supervisor_contract_probing_defers_high_context_only() -> None:
    tracker = AbortRecoveryTracker()
    tracker.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)

    payload = _payload(tracker=tracker)

    assert payload["summary"]["recovery_state"] == "probing"
    assert payload["summary"]["barrier_decision"] == "defer_high_context_until_probe"
    assert payload["barrier"]["hard_recovery_barrier"] is False
    assert payload["barrier"]["high_context_barrier"] is True
    assert payload["request_impact"]["generation_admissible"] is True
    assert payload["request_impact"]["high_context_generation_admissible"] is False


def test_recovery_supervisor_contract_contaminated_requires_barrier() -> None:
    tracker = AbortRecoveryTracker()
    tracker.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    tracker.apply_probe_result(passed=False, reason="scheduler loop", now=1005.0)

    payload = _payload(tracker=tracker)

    assert payload["summary"]["recovery_state"] == "contaminated"
    assert payload["summary"]["barrier_decision"] == "recovery_barrier_required"
    assert payload["barrier"]["hard_recovery_barrier"] is True
    assert payload["request_impact"]["generation_admissible"] is False
    assert payload["substrate"]["contamination_reason"] == "scheduler loop"


def test_recovery_supervisor_contract_restart_exhausted_requires_operator_recovery() -> None:
    runtime_status = _runtime_status_payload()
    runtime_status["restart"] = {
        "restartable_models": [],
        "restart_exhausted_models": ["fake-a"],
        "auto_restart_dead_session": True,
    }

    payload = _payload(runtime_status=runtime_status)

    assert payload["summary"]["recovery_state"] == "restart_exhausted"
    assert payload["summary"]["barrier_decision"] == "operator_recovery_required"
    assert payload["barrier"]["hard_recovery_barrier"] is True
    assert payload["restart"]["restart_exhausted_models"] == ["fake-a"]


def test_recovery_supervisor_contract_backend_unhealthy_fails_closed() -> None:
    runtime_status = _runtime_status_payload()
    summary = dict(runtime_status["summary"])
    summary["backend_healthy"] = False
    runtime_status["summary"] = summary
    runtime_status["health"] = {"readiness": "blocked", "block_reason": "backend is down"}

    payload = _payload(runtime_status=runtime_status)

    assert payload["summary"]["recovery_state"] == "backend_unhealthy"
    assert payload["summary"]["barrier_decision"] == "block_runtime_generation"
    assert payload["barrier"]["general_admission_block_required"] is True


def test_recovery_supervisor_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "recovery_supervisor_contract.py")
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
