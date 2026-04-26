"""Runtime-owned single-host model residency policy contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


MODEL_RESIDENCY_POLICY_SURFACE = "owlmlx.model_residency_policy"
MODEL_RESIDENCY_POLICY_VERSION = "v1"
RESIDENCY_STATES = (
    "resident",
    "default_active",
    "pinned",
    "ttl_managed",
    "evictable",
    "unknown",
)


@dataclass(frozen=True, slots=True)
class ModelResidencyPolicy:
    """Stable runtime-owned residency policy snapshot for current model state."""

    target_model_id: str | None
    target_status: dict[str, Any]
    models: tuple[dict[str, Any], ...]
    residency_state_support: dict[str, dict[str, Any]]
    policy_boundaries: dict[str, Any]
    signals: dict[str, Any]
    missing_signals: tuple[dict[str, str], ...]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _list_of_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _loaded_models(raw_status: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    backend = _mapping(raw_status.get("backend"))
    loaded_models = backend.get("loaded_models")
    if not isinstance(loaded_models, list):
        return ()
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in loaded_models:
        loaded = _mapping(entry)
        model_id = loaded.get("model_id")
        if not isinstance(model_id, str) or not model_id or model_id in seen:
            continue
        seen.add(model_id)
        normalized.append(
            {
                "model_id": model_id,
                "memory_gb": loaded.get("memory_gb"),
                "backend": loaded.get("backend"),
                "loaded_at": loaded.get("loaded_at"),
            }
        )
    return tuple(normalized)


def _residency_state_support() -> dict[str, dict[str, Any]]:
    return {
        "resident": {
            "classification_status": "supported",
            "reason_code": "loaded_model_inventory_is_runtime_owned",
        },
        "default_active": {
            "classification_status": "supported",
            "reason_code": "active_model_id_is_runtime_owned",
        },
        "pinned": {
            "classification_status": "supported",
            "reason_code": "kernel_pin_set_and_unload_block_are_runtime_owned",
        },
        "ttl_managed": {
            "classification_status": "supported",
            "reason_code": "kernel_ttl_policy_and_explicit_sweep_are_runtime_owned",
        },
        "evictable": {
            "classification_status": "partial",
            "reason_code": "ttl_expired_unpinned_evictability_is_owned_but_pressure_eviction_policy_is_not",
        },
        "unknown": {
            "classification_status": "supported",
            "reason_code": "fallback_state_retained_for_non_resident_or_weak_signal_targets",
        },
    }


def _model_policy_entry(
    *,
    model: Mapping[str, Any],
    active_model_id: str | None,
    pinned_model_ids: tuple[str, ...],
    ttl_model_ids: tuple[str, ...],
    ttl_expired_model_ids: tuple[str, ...],
    ttl_expired_pinned_model_ids: tuple[str, ...],
) -> dict[str, Any]:
    model_id = str(model["model_id"])
    resident = True
    default_active = model_id == active_model_id
    pinned = model_id in pinned_model_ids
    ttl_managed = model_id in ttl_model_ids
    ttl_expired = model_id in ttl_expired_model_ids
    expired_but_pinned = model_id in ttl_expired_pinned_model_ids
    ttl_evictable = ttl_expired and not pinned
    manual_unload_eligible = not pinned

    states = ["resident"]
    if default_active:
        states.append("default_active")
    if pinned:
        states.append("pinned")
    if ttl_managed:
        states.append("ttl_managed")
    if ttl_evictable:
        states.append("evictable")

    return {
        "model_id": model_id,
        "states": states,
        "resident": resident,
        "default_active": default_active,
        "pinned": pinned,
        "ttl_managed": ttl_managed,
        "ttl_expired": ttl_expired,
        "ttl_expired_but_pinned": expired_but_pinned,
        "evictable": ttl_evictable,
        "manual_unload_eligible": manual_unload_eligible,
        "memory_gb": model.get("memory_gb"),
        "backend": model.get("backend"),
        "loaded_at": model.get("loaded_at"),
        "evictability_scope": (
            "ttl_expired_unpinned_explicit_sweep"
            if ttl_evictable
            else "blocked_by_pin"
            if pinned
            else "manual_unload_only_no_pressure_policy"
        ),
    }


def _target_status(
    *,
    target_model_id: str | None,
    model_entries: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    if not target_model_id:
        return {
            "model_id": None,
            "classification_status": "unknown",
            "states": ["unknown"],
            "reason_code": "no_target_model_requested",
        }
    for entry in model_entries:
        if entry["model_id"] == target_model_id:
            return {
                "model_id": target_model_id,
                "classification_status": "supported",
                "states": list(entry["states"]),
                "resident": entry["resident"],
                "default_active": entry["default_active"],
                "pinned": entry["pinned"],
                "ttl_managed": entry["ttl_managed"],
                "evictable": entry["evictable"],
                "reason_code": "target_model_residency_classified_from_runtime_truth",
            }
    return {
        "model_id": target_model_id,
        "classification_status": "unknown",
        "states": ["unknown"],
        "resident": False,
        "reason_code": "target_model_not_resident_and_load_on_demand_policy_not_frozen",
    }


def build_model_residency_policy(
    *,
    runtime_status: Mapping[str, Any] | None = None,
    model_id: str | None = None,
) -> ModelResidencyPolicy:
    """Build the current runtime-owned model residency policy contract."""

    raw_status = _mapping(runtime_status)
    summary = _mapping(raw_status.get("summary"))
    inventory = _mapping(raw_status.get("inventory"))
    governance_policy = _mapping(raw_status.get("governance_policy"))
    governance_observations = _mapping(raw_status.get("governance_observations"))
    budget = _mapping(raw_status.get("budget"))

    active_model_id = raw_status.get("active_model_id") or summary.get("active_model_id")
    loaded = _loaded_models(raw_status)
    pinned_model_ids = _list_of_strings(governance_policy.get("pinned_model_ids"))
    ttl_model_ids = _list_of_strings(governance_policy.get("ttl_model_ids"))
    ttl_expired_model_ids = _list_of_strings(governance_policy.get("ttl_expired_model_ids"))
    ttl_expired_pinned_model_ids = _list_of_strings(
        governance_policy.get("ttl_expired_pinned_model_ids")
    )
    model_entries = tuple(
        _model_policy_entry(
            model=model,
            active_model_id=active_model_id if isinstance(active_model_id, str) else None,
            pinned_model_ids=pinned_model_ids,
            ttl_model_ids=ttl_model_ids,
            ttl_expired_model_ids=ttl_expired_model_ids,
            ttl_expired_pinned_model_ids=ttl_expired_pinned_model_ids,
        )
        for model in loaded
    )

    target_model_id = model_id or active_model_id if isinstance(active_model_id, str) else model_id
    missing_signals = (
        {
            "layer": "load_on_demand",
            "signal": "runtime_owned_defer_to_load_or_auto_load_policy",
            "reason": "non-resident targets remain unknown because residency policy does not yet own load scheduling",
        },
        {
            "layer": "memory_pressure",
            "signal": "runtime_owned_pressure_ranked_eviction_policy",
            "reason": "TTL sweep evictability is visible, but pressure-driven victim selection is not frozen",
        },
        {
            "layer": "recovery",
            "signal": "runtime_owned_recovery_barrier_after_failed_unload_or_reclaim",
            "reason": "restart visibility exists outside this residency contract",
        },
    )

    return ModelResidencyPolicy(
        target_model_id=target_model_id,
        target_status=_target_status(
            target_model_id=target_model_id,
            model_entries=model_entries,
        ),
        models=model_entries,
        residency_state_support=_residency_state_support(),
        policy_boundaries={
            "policy_scope": "current_residency_state_classification",
            "owned_actions_visible": [
                "load_sets_active_model",
                "unload_clears_or_reassigns_active_model",
                "pin_blocks_unload",
                "ttl_policy_explicit_sweep",
                "eviction_history_events",
            ],
            "out_of_scope": [
                "automatic_load_on_demand",
                "pressure_ranked_eviction",
                "recovery_supervisor",
                "continuous_batching",
                "multi_worker_scheduler_depth",
            ],
        },
        signals={
            "active_model_id": active_model_id,
            "inventory": {
                "model_count": inventory.get("model_count", len(model_entries)),
                "total_loaded_gb": inventory.get("total_loaded_gb"),
                "loaded_model_ids": [entry["model_id"] for entry in model_entries],
                "classification_status": "supported",
            },
            "pinning": {
                "pinning_supported": bool(governance_policy.get("pinning_supported", False)),
                "pinned_model_ids": list(pinned_model_ids),
                "pinned_model_count": governance_policy.get(
                    "pinned_model_count", len(pinned_model_ids)
                ),
                "pinning_events_visible": bool(
                    governance_observations.get("pinning_events_visible", False)
                ),
                "classification_status": "supported",
            },
            "ttl": {
                "ttl_supported": bool(governance_policy.get("ttl_supported", False)),
                "ttl_policy_mode": governance_policy.get("ttl_policy_mode"),
                "ttl_model_ids": list(ttl_model_ids),
                "ttl_policy_count": governance_policy.get("ttl_policy_count", len(ttl_model_ids)),
                "ttl_expired_model_ids": list(ttl_expired_model_ids),
                "ttl_expired_pinned_model_ids": list(ttl_expired_pinned_model_ids),
                "ttl_events_visible": bool(
                    governance_observations.get("ttl_events_visible", False)
                ),
                "ttl_expiry_visible": bool(
                    governance_observations.get("ttl_expiry_visible", False)
                ),
                "classification_status": "supported",
            },
            "eviction_history": {
                "eviction_history_visible": bool(
                    governance_policy.get("eviction_history_visible", False)
                ),
                "eviction_history_count": governance_policy.get("eviction_history_count", 0),
                "recent_eviction_history": list(
                    governance_policy.get("recent_eviction_history", [])
                ),
                "classification_status": "supported",
            },
            "budget": {
                "serving_budget_gb": budget.get("serving_budget_gb"),
                "currently_loaded_gb": budget.get("currently_loaded_gb"),
                "available_gb": budget.get("available_gb"),
                "utilization": budget.get("utilization"),
                "classification_status": "informational",
                "policy_impact": "does_not_select_eviction_victim_in_this_contract",
            },
        },
        missing_signals=missing_signals,
    )


def model_residency_policy_to_dict(policy: ModelResidencyPolicy) -> dict[str, Any]:
    """Serialize the runtime-owned model residency policy contract."""

    return {
        "contract": {
            "surface": MODEL_RESIDENCY_POLICY_SURFACE,
            "version": MODEL_RESIDENCY_POLICY_VERSION,
            "stable_sections": [
                "summary",
                "target_model",
                "models",
                "residency_state_support",
                "policy_boundaries",
                "signals",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "resident_model_count": len(policy.models),
            "target_model_id": policy.target_model_id,
            "supported_states": list(RESIDENCY_STATES),
            "policy_depth": "current_state_classification",
        },
        "target_model": policy.target_status,
        "models": list(policy.models),
        "residency_state_support": policy.residency_state_support,
        "policy_boundaries": policy.policy_boundaries,
        "signals": policy.signals,
        "missing_signals": list(policy.missing_signals),
    }
