"""Tests for residency-aware eviction ordering — Campaign 2 eviction policy.

Verifies that the memory-pressure eviction policy uses the CacheResidencyTracker
state when selecting an eviction victim: evictable < resident < hot.
"""

from __future__ import annotations

from owlmlx.memory_pressure_eviction_policy import (
    build_memory_pressure_eviction_policy,
    memory_pressure_eviction_policy_to_dict,
)


# ---------------------------------------------------------------------------
# Helpers — build a minimal over_budget runtime_status payload
# ---------------------------------------------------------------------------

def _model_entry(model_id: str, memory_gb: float = 10.0) -> dict:
    return {"model_id": model_id, "memory_gb": memory_gb}


def _cache_residency(entries: dict[str, str]) -> dict:
    return {
        "surface": "owlmlx.cache_residency_tracker",
        "entry_count": len(entries),
        "entries": {
            model_id: {"model_id": model_id, "state": state}
            for model_id, state in entries.items()
        },
        "release_ledger_total": 0,
        "release_ledger": [],
    }


def _over_budget_status(
    loaded_models: list[dict],
    *,
    active_model_id: str | None = None,
    pinned_model_ids: list[str] | None = None,
    residency_states: dict[str, str] | None = None,
) -> dict:
    return {
        "summary": {
            "backend_healthy": True,
            "active_model_id": active_model_id,
        },
        "active_model_id": active_model_id,
        "inventory": {
            "model_count": len(loaded_models),
            "total_loaded_gb": sum(float(m["memory_gb"]) for m in loaded_models),
        },
        "backend": {"loaded_models": loaded_models},
        "budget": {
            "system_memory_gb": 8.0,
            "system_reserve_gb": 2.0,
            "serving_budget_gb": 6.0,
            "warning_threshold_gb": 5.0,
            "currently_loaded_gb": sum(float(m["memory_gb"]) for m in loaded_models),
            "available_gb": -4.0,
            "utilization": 1.5,
        },
        "restart": {
            "restartable_models": [],
            "restart_exhausted_models": [],
            "auto_restart_dead_session": False,
        },
        "governance_policy": {
            "pinned_model_ids": pinned_model_ids or [],
            "ttl_expired_model_ids": [],
            "ttl_expired_pinned_model_ids": [],
        },
        "governance_observations": {},
        "health": {"readiness": "ready"},
        **({"cache_residency": _cache_residency(residency_states)} if residency_states else {}),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_eviction_prefers_evictable_over_hot():
    """When one model is hot and another is evictable, evict the evictable one."""
    status = _over_budget_status(
        loaded_models=[
            _model_entry("model-hot", memory_gb=10.0),
            _model_entry("model-evictable", memory_gb=10.0),
        ],
        residency_states={
            "model-hot": "hot",
            "model-evictable": "evictable",
        },
    )
    policy = build_memory_pressure_eviction_policy(runtime_status=status)
    assert policy.decision == "evict"
    assert policy.selected_victim is not None
    assert policy.selected_victim["model_id"] == "model-evictable"


def test_eviction_prefers_evictable_over_resident():
    """When one model is resident and another is evictable, evict the evictable one."""
    status = _over_budget_status(
        loaded_models=[
            _model_entry("model-resident", memory_gb=10.0),
            _model_entry("model-evictable", memory_gb=10.0),
        ],
        residency_states={
            "model-resident": "resident",
            "model-evictable": "evictable",
        },
    )
    policy = build_memory_pressure_eviction_policy(runtime_status=status)
    assert policy.decision == "evict"
    assert policy.selected_victim["model_id"] == "model-evictable"


def test_eviction_prefers_resident_over_hot():
    """When one model is hot and another is resident, evict the resident one."""
    status = _over_budget_status(
        loaded_models=[
            _model_entry("model-hot", memory_gb=10.0),
            _model_entry("model-resident", memory_gb=10.0),
        ],
        residency_states={
            "model-hot": "hot",
            "model-resident": "resident",
        },
    )
    policy = build_memory_pressure_eviction_policy(runtime_status=status)
    assert policy.decision == "evict"
    assert policy.selected_victim["model_id"] == "model-resident"


def test_eviction_victim_includes_residency_state():
    """selected_victim dict contains residency_state field."""
    status = _over_budget_status(
        loaded_models=[_model_entry("model-a", memory_gb=10.0)],
        residency_states={"model-a": "evictable"},
    )
    policy = build_memory_pressure_eviction_policy(runtime_status=status)
    assert policy.decision == "evict"
    assert policy.selected_victim["residency_state"] == "evictable"


def test_eviction_residency_state_none_when_tracker_absent():
    """When no cache_residency in status, residency_state is None (backwards compat)."""
    status = _over_budget_status(
        loaded_models=[_model_entry("model-a", memory_gb=10.0)],
        residency_states=None,  # no cache_residency key
    )
    policy = build_memory_pressure_eviction_policy(runtime_status=status)
    assert policy.decision == "evict"
    assert policy.selected_victim["residency_state"] is None


def test_eviction_residency_falls_back_to_memory_size_as_tiebreaker():
    """Two models with same residency state → larger memory_gb evicted first."""
    status = _over_budget_status(
        loaded_models=[
            _model_entry("small-model", memory_gb=5.0),
            _model_entry("large-model", memory_gb=15.0),
        ],
        residency_states={
            "small-model": "evictable",
            "large-model": "evictable",
        },
    )
    policy = build_memory_pressure_eviction_policy(runtime_status=status)
    assert policy.decision == "evict"
    assert policy.selected_victim["model_id"] == "large-model"


def test_eviction_candidate_order_in_serialized_payload():
    """candidate_order in the serialized payload reflects residency priority."""
    status = _over_budget_status(
        loaded_models=[
            _model_entry("model-hot", memory_gb=10.0),
            _model_entry("model-evictable", memory_gb=10.0),
            _model_entry("model-resident", memory_gb=10.0),
        ],
        residency_states={
            "model-hot": "hot",
            "model-evictable": "evictable",
            "model-resident": "resident",
        },
    )
    policy = build_memory_pressure_eviction_policy(runtime_status=status)
    payload = memory_pressure_eviction_policy_to_dict(policy)
    order = [c["model_id"] for c in payload["candidate_order"]]
    # evictable → resident → hot
    assert order.index("model-evictable") < order.index("model-resident")
    assert order.index("model-resident") < order.index("model-hot")
