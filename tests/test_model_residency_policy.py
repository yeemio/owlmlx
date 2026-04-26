from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.model_residency_policy import (
    build_model_residency_policy,
    model_residency_policy_to_dict,
)
from owlmlx.runtime.server import create_app


def _runtime_status_payload() -> dict[str, object]:
    return {
        "summary": {
            "runtime": "owlmlx",
            "backend_name": "fake",
            "backend_healthy": True,
            "readiness": "ready",
            "active_model_id": "fake-a",
            "model_count": 2,
        },
        "backend": {
            "backend_name": "fake",
            "healthy": True,
            "loaded_models": [
                {"model_id": "fake-a", "memory_gb": 2.0, "backend": "fake"},
                {"model_id": "fake-b", "memory_gb": 3.0, "backend": "fake"},
            ],
        },
        "inventory": {
            "model_count": 2,
            "total_loaded_gb": 5.0,
        },
        "budget": {
            "serving_budget_gb": 64.0,
            "currently_loaded_gb": 5.0,
            "available_gb": 59.0,
            "utilization": 0.078,
        },
        "governance_observations": {
            "pinning_events_visible": True,
            "ttl_events_visible": True,
            "ttl_expiry_visible": True,
            "eviction_history_events_visible": True,
        },
        "governance_policy": {
            "pinning_supported": True,
            "ttl_supported": True,
            "eviction_history_visible": True,
            "ttl_policy_mode": "kernel_explicit_sweep",
            "pinned_model_ids": ["fake-a"],
            "pinned_model_count": 1,
            "ttl_model_ids": ["fake-a", "fake-b"],
            "ttl_policy_count": 2,
            "ttl_expired_model_ids": ["fake-a", "fake-b"],
            "ttl_expired_pinned_model_ids": ["fake-a"],
            "eviction_history_count": 2,
            "recent_eviction_history": [
                {
                    "sequence": 1,
                    "model_id": "fake-a",
                    "event": "ttl_expiry_blocked_by_pinning",
                    "source": "ttl_policy",
                },
                {
                    "sequence": 2,
                    "model_id": "fake-b",
                    "event": "ttl_expired_unloaded",
                    "source": "ttl_policy",
                },
            ],
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


def test_model_residency_policy_classifies_active_pinned_ttl_model() -> None:
    payload = model_residency_policy_to_dict(
        build_model_residency_policy(runtime_status=_runtime_status_payload())
    )

    assert payload["contract"]["surface"] == "owlmlx.model_residency_policy"
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["status"] == "partial"
    assert payload["summary"]["resident_model_count"] == 2
    first = payload["models"][0]
    assert first["model_id"] == "fake-a"
    assert first["states"] == ["resident", "default_active", "pinned", "ttl_managed"]
    assert first["ttl_expired_but_pinned"] is True
    assert first["evictable"] is False
    assert first["evictability_scope"] == "blocked_by_pin"


def test_model_residency_policy_marks_unpinned_ttl_expired_model_evictable() -> None:
    payload = model_residency_policy_to_dict(
        build_model_residency_policy(
            runtime_status=_runtime_status_payload(),
            model_id="fake-b",
        )
    )

    second = payload["models"][1]
    assert second["model_id"] == "fake-b"
    assert second["states"] == ["resident", "ttl_managed", "evictable"]
    assert second["evictable"] is True
    assert second["manual_unload_eligible"] is True
    assert payload["target_model"]["model_id"] == "fake-b"
    assert payload["target_model"]["classification_status"] == "supported"
    assert payload["target_model"]["evictable"] is True


def test_model_residency_policy_keeps_non_resident_target_unknown() -> None:
    payload = model_residency_policy_to_dict(
        build_model_residency_policy(
            runtime_status=_runtime_status_payload(),
            model_id="fake-c",
        )
    )

    assert payload["target_model"]["model_id"] == "fake-c"
    assert payload["target_model"]["classification_status"] == "unknown"
    assert payload["target_model"]["states"] == ["unknown"]
    assert payload["target_model"]["reason_code"] == (
        "target_model_not_resident_and_load_on_demand_policy_not_frozen"
    )


def test_model_residency_policy_keeps_pressure_eviction_partial() -> None:
    payload = model_residency_policy_to_dict(
        build_model_residency_policy(runtime_status=_runtime_status_payload())
    )

    assert payload["residency_state_support"]["evictable"]["classification_status"] == "partial"
    assert payload["signals"]["budget"]["classification_status"] == "informational"
    assert "pressure_ranked_eviction" in payload["policy_boundaries"]["out_of_scope"]
    assert any(item["layer"] == "memory_pressure" for item in payload["missing_signals"])


def test_runtime_model_residency_policy_route_returns_surface() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get(
        "/v1/runtime/model-residency-policy",
        params={"model_id": "fake-a"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.model_residency_policy"
    assert payload["summary"]["resident_model_count"] == 1
    assert payload["target_model"]["classification_status"] == "supported"
    assert payload["target_model"]["states"] == ["resident", "default_active"]


def test_model_residency_policy_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "model_residency_policy.py")
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
