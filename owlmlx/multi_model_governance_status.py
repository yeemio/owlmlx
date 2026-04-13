"""Runtime-owned multi-model governance status for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MultiModelGovernanceStatus:
    """Stable runtime-owned governance status for multi-model lifecycle behavior."""

    inventory: dict[str, Any]
    budget: dict[str, Any]
    active_model_id: str | None
    resident_model_count: int
    loaded_model_ids: tuple[str, ...]
    restartable_models: tuple[str, ...]
    restart_exhausted_models: tuple[str, ...]
    status: str
    governance_rung: str
    blocked_reason: str | None
    recommended_next_step: str


def build_multi_model_governance_status(
    runtime_status: Mapping[str, Any] | None = None,
) -> MultiModelGovernanceStatus:
    """Build runtime-owned multi-model governance status."""

    raw = dict(runtime_status or {})
    inventory = dict(raw.get("inventory", {}))
    budget = dict(raw.get("budget", {}))
    entries = inventory.get("entries", [])
    loaded_model_ids = tuple(
        str(entry.get("model_id"))
        for entry in entries
        if isinstance(entry, Mapping)
        and str(entry.get("load_state")) in {"true_loaded", "inferred_loaded"}
    )
    resident_model_count = len(loaded_model_ids)
    active_model_id = raw.get("active_model_id")
    restart = raw.get("restart", {})
    restartable_models = tuple(str(model_id) for model_id in restart.get("restartable_models", []))
    restart_exhausted_models = tuple(
        str(model_id) for model_id in restart.get("restart_exhausted_models", [])
    )

    governance_rung = "inventory_visible"
    blocked_reason = (
        "owlmlx still lacks runtime-owned pinning, TTL policy, and eviction history for deeper multi-model governance closure"
    )
    recommended_next_step = (
        "promote explicit multi-model active/default semantics and repeatable governance behavior before claiming stronger lifecycle parity"
    )

    active_model_loaded = bool(active_model_id) and str(active_model_id) in loaded_model_ids
    recoverability_visible = (
        "restartable_models" in restart and "restart_exhausted_models" in restart
    )

    if active_model_loaded or resident_model_count > 0:
        governance_rung = "active_default_visible"
        blocked_reason = (
            "owlmlx exposes active/default semantics, but multi-model residency and governance controls remain partial"
        )
        recommended_next_step = (
            "verify repeated multi-model switching and restart/unload semantics before claiming stronger governance closure"
        )

    if recoverability_visible:
        governance_rung = "restart_visibility_visible"
        blocked_reason = (
            "owlmlx exposes restart/unload recoverability, but pinning, TTL, and eviction-history governance still remain absent"
        )
        recommended_next_step = (
            "run repeated multi-model load/switch/unload/restart validation and keep absent governance controls explicit"
        )

    if resident_model_count >= 2 and active_model_loaded and recoverability_visible:
        governance_rung = "partial_closure"
        blocked_reason = (
            "owlmlx now exposes live multi-model residency, active/default semantics, and restart visibility, but pinning, TTL, and eviction-history governance remain below reference-grade parity"
        )
        recommended_next_step = (
            "freeze the remaining absent controls and move the dominant gap to heavy-weight runtime repeatability"
        )

    return MultiModelGovernanceStatus(
        inventory=inventory,
        budget=budget,
        active_model_id=str(active_model_id) if active_model_id is not None else None,
        resident_model_count=resident_model_count,
        loaded_model_ids=loaded_model_ids,
        restartable_models=restartable_models,
        restart_exhausted_models=restart_exhausted_models,
        status="partial",
        governance_rung=governance_rung,
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
    )


def multi_model_governance_status_to_dict(
    status: MultiModelGovernanceStatus,
) -> dict[str, Any]:
    """Serialize runtime-owned multi-model governance status."""

    return {
        "contract": {
            "surface": "owlmlx.multi_model_governance_status",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "inventory",
                "budget",
                "active_model",
                "governance_controls",
                "recoverability",
            ],
        },
        "summary": {
            "status": status.status,
            "governance_rung": status.governance_rung,
            "blocked_reason": status.blocked_reason,
            "recommended_next_step": status.recommended_next_step,
        },
        "inventory": {
            "resident_model_count": status.resident_model_count,
            "loaded_model_ids": list(status.loaded_model_ids),
            "total_loaded_gb": status.inventory.get("total_loaded_gb"),
            "loaded_count": status.inventory.get("loaded_count"),
        },
        "budget": {
            "serving_budget_gb": status.budget.get("serving_budget_gb"),
            "currently_loaded_gb": status.budget.get("currently_loaded_gb"),
            "available_gb": status.budget.get("available_gb"),
            "utilization": status.budget.get("utilization"),
        },
        "active_model": {
            "active_model_id": status.active_model_id,
            "active_model_loaded": (
                status.active_model_id in status.loaded_model_ids
                if status.active_model_id is not None
                else False
            ),
            "default_generation_supported": True,
            "default_selection_policy": "last_loaded_becomes_active",
            "explicit_model_targeting_supported": True,
            "explicit_unload_required": True,
        },
        "governance_controls": {
            "pinning_supported": False,
            "ttl_supported": False,
            "eviction_history_visible": False,
            "backend_ttl_visible": False,
            "model_runtime_supports_visible": True,
        },
        "recoverability": {
            "restartable_models": list(status.restartable_models),
            "restart_exhausted_models": list(status.restart_exhausted_models),
            "restart_surface_visible": True,
            "unload_surface_visible": True,
        },
    }
