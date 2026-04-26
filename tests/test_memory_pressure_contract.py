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
    assert any(item["layer"] == "reclaim" for item in payload["missing_signals"])


def test_runtime_memory_pressure_contract_route_returns_surface() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/runtime/memory-pressure-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.memory_pressure_contract"
    assert payload["summary"]["pressure_classification"] == "within_budget"
    assert payload["budget"]["serving_budget_gb"] == 6.0


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
