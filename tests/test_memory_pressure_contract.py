from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.memory_pressure_contract import (
    build_memory_pressure_contract,
    memory_pressure_contract_to_dict,
)
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app


def _runtime_status_payload(
    *,
    currently_loaded_gb: float,
    available_gb: float,
    utilization: float,
) -> dict[str, object]:
    return {
        "inventory": {
            "model_count": 2,
            "total_loaded_gb": currently_loaded_gb,
        },
        "budget": {
            "system_memory_gb": 128.0,
            "system_reserve_gb": 12.0,
            "serving_budget_gb": 116.0,
            "warning_threshold_gb": 100.0,
            "currently_loaded_gb": currently_loaded_gb,
            "available_gb": available_gb,
            "utilization": utilization,
        },
        "restart": {
            "restartable_models": [],
            "restart_exhausted_models": [],
            "auto_restart_dead_session": False,
        },
        "governance_policy": {
            "ttl_expired_model_ids": ["fake-a", "fake-b"],
            "ttl_expired_pinned_model_ids": ["fake-a"],
        },
    }


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def test_memory_pressure_contract_classifies_within_budget() -> None:
    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
            )
        )
    )

    assert payload["contract"]["surface"] == "owlmlx.memory_pressure_contract"
    assert payload["summary"]["pressure_classification"] == "within_budget"
    assert payload["reason"]["code"] == "budget_headroom_available"
    assert payload["policy_boundaries"]["runtime_owned_pressure_victim_selection"] is False


def test_memory_pressure_contract_classifies_near_budget() -> None:
    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=101.0,
                available_gb=15.0,
                utilization=0.871,
            )
        )
    )

    assert payload["summary"]["pressure_classification"] == "near_budget"
    assert payload["reason"]["code"] == "budget_warning_threshold_reached"


def test_memory_pressure_contract_classifies_over_budget() -> None:
    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=120.0,
                available_gb=-4.0,
                utilization=1.034,
            )
        )
    )

    assert payload["summary"]["pressure_classification"] == "over_budget"
    assert payload["summary"]["confidence"] == "high"
    assert payload["reason"]["code"] == "budget_headroom_negative"


def test_memory_pressure_contract_classifies_metal_oom_cooldown_barrier() -> None:
    status = _runtime_status_payload(
        currently_loaded_gb=0.0,
        available_gb=116.0,
        utilization=0.0,
    )
    status["memory_pressure_cooldown"] = {
        "active": True,
        "reason_code": "metal_oom_child_loss_cooldown",
        "remaining_s": 92.0,
    }

    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(runtime_status=status)
    )

    assert payload["summary"]["pressure_classification"] == "cooldown_barrier"
    assert payload["summary"]["confidence"] == "high"
    assert payload["reason"]["code"] == "metal_oom_cooldown_active"
    assert payload["recovery_context"]["memory_pressure_cooldown"]["active"] is True
    assert payload["policy_boundaries"]["runtime_owned_pressure_event_visible"] is True
    assert payload["policy_boundaries"]["runtime_owned_metal_oom_cooldown"] is True


def test_memory_pressure_contract_classifies_host_pressure_barrier() -> None:
    status = _runtime_status_payload(
        currently_loaded_gb=0.0,
        available_gb=116.0,
        utilization=0.0,
    )
    status["host_pressure"] = {
        "available": True,
        "source": "memory_pressure",
        "classification": "host_pressure_block",
        "reason_code": "free_percent_at_or_below_block_threshold",
        "free_percent": 8.0,
    }

    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(runtime_status=status)
    )

    assert payload["summary"]["pressure_classification"] == "host_pressure_barrier"
    assert payload["summary"]["confidence"] == "high"
    assert payload["reason"]["code"] == "host_pressure_admission_barrier_active"
    assert payload["recovery_context"]["host_pressure"]["free_percent"] == 8.0
    assert payload["policy_boundaries"]["runtime_owned_pressure_event_visible"] is True
    assert payload["policy_boundaries"]["runtime_owned_host_pressure_sample"] is True


def test_memory_pressure_contract_marks_missing_budget_unknown() -> None:
    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(runtime_status={"budget": {}})
    )

    assert payload["summary"]["pressure_classification"] == "unknown"
    assert payload["budget"]["classification_status"] == "unknown"
    assert payload["reason"]["code"] == "budget_snapshot_incomplete"


def test_memory_pressure_contract_keeps_reclaim_and_eviction_insufficient_signal() -> None:
    payload = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=101.0,
                available_gb=15.0,
                utilization=0.871,
            )
        )
    )

    assert payload["classification_support"]["insufficient_signal"]["classification_status"] == (
        "supported"
    )
    assert payload["residency_context"]["ttl_sweep_evictable_model_ids"] == ["fake-b"]
    assert "pressure_ranked_eviction" in payload["policy_boundaries"]["out_of_scope"]
    # reclaim attempt-result visibility now lives in owlmlx.settle_barrier_event;
    # the pressure contract still does not own a reclaim engine, but it should
    # no longer claim reclaim-attempt visibility is entirely missing.
    assert (
        "settle_barrier_event"
        in payload["policy_boundaries"]["runtime_owned_reclaim_attempt_result_visibility"]
    )
    assert payload["policy_boundaries"]["runtime_owned_reclaim_barrier"] is False
    assert any(item["layer"] == "eviction" for item in payload["missing_signals"])


def test_runtime_memory_pressure_contract_route_returns_surface() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/runtime/memory-pressure-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.memory_pressure_contract"
    assert payload["summary"]["pressure_classification"] == "within_budget"
    assert payload["budget"]["serving_budget_gb"] == 6.0
    # 2.1: PR #649 watermark fields land in the contract summary.
    assert payload["summary"]["watermark"] == "green"
    assert payload["summary"]["watermark_action"] == "proceed"


def test_runtime_memory_watermark_route_returns_headline_payload() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/runtime/memory-watermark")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.memory_watermark"
    assert payload["watermark"] in {"green", "yellow", "red", "fatal", "unknown"}
    assert payload["action"] in {
        "proceed", "evict_lru", "aggressive_evict", "refuse_load", "defer"
    }
    assert payload["thresholds"]["green_ceiling"] == 0.65
    assert payload["thresholds"]["yellow_ceiling"] == 0.80
    assert payload["thresholds"]["red_ceiling"] == 0.90
    assert payload["pressure_classification"] == "within_budget"


def test_runtime_memory_watermark_route_under_pressure() -> None:
    """When fake backend is loaded beyond the warning threshold, the watermark
    must reflect the elevated pressure level — verifies that the route is
    actually reading runtime state, not a static value."""
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 5.5})

    response = client.get("/v1/runtime/memory-watermark")
    payload = response.json()

    # within_budget (warning_threshold_gb=5.0) → near_budget once loaded > 5GB
    assert payload["pressure_classification"] in {"near_budget", "over_budget"}
    assert payload["watermark"] in {"yellow", "red"}
    assert payload["action"] in {"evict_lru", "aggressive_evict"}


def test_memory_pressure_contract_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "memory_pressure_contract.py")
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
