"""Runtime-owned multi-model governance controls for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MultiModelGovernanceControls:
    """Stable runtime-owned control/evidence surface for multi-model governance."""

    resident_model_count: int
    active_model_id: str | None
    controls_rung: str
    status: str
    blocked_reason: str | None
    recommended_next_step: str
    transition_count: int
    default_selection_policy_visible: bool
    explicit_model_targeting_supported: bool
    explicit_unload_required: bool
    restart_surface_visible: bool
    unload_surface_visible: bool
    pinning_supported: bool
    ttl_supported: bool
    eviction_history_visible: bool
    backend_ttl_visible: bool
    transition_history_visible: bool
    active_reassignment_visible: bool
    restart_restore_visible: bool
    explicit_targeting_evidence_visible: bool


def build_multi_model_governance_controls(
    runtime_status: Mapping[str, Any] | None = None,
    *,
    transition_evidence: Mapping[str, Any] | None = None,
) -> MultiModelGovernanceControls:
    """Build runtime-owned multi-model governance controls."""

    raw = dict(runtime_status or {})
    inventory = raw.get("inventory", {})
    active_model_id = raw.get("active_model_id")
    governance_policy = raw.get("governance_policy", {})
    resident_model_count = int(inventory.get("model_count", 0))
    restart = raw.get("restart", {})
    observations = raw.get("governance_observations", {})
    if isinstance(transition_evidence, Mapping):
        evidence = dict(transition_evidence)
    elif isinstance(observations, Mapping):
        evidence = dict(observations)
    else:
        evidence = {}

    transition_count = int(evidence.get("transition_count", 0))
    transition_history_visible = transition_count > 0
    active_reassignment_visible = bool(evidence.get("active_reassignment_visible", False))
    restart_restore_visible = bool(evidence.get("restart_restore_visible", False))
    explicit_targeting_evidence_visible = bool(
        evidence.get("explicit_targeting_evidence_visible", False)
    )

    controls_rung = "controls_visible"
    blocked_reason = (
        "owlmlx still lacks runtime-owned pinning, TTL policy, and eviction-history governance for deeper multi-model closure"
    )
    recommended_next_step = (
        "add repeated transition evidence or stronger governance controls before claiming broader lifecycle parity"
    )

    if transition_history_visible:
        controls_rung = "transition_evidence_visible"
        blocked_reason = (
            "owlmlx now has runtime-owned transition evidence, but pinning, TTL, and eviction-history governance remain absent"
        )
        recommended_next_step = (
            "keep absent controls exact and extend repeated governance transitions before moving the dominant gap"
        )

    if (
        resident_model_count >= 1
        and transition_history_visible
        and active_reassignment_visible
        and restart_restore_visible
        and explicit_targeting_evidence_visible
    ):
        controls_rung = "partial_closure"
        blocked_reason = (
            "owlmlx now exposes transition evidence for active reassignment, explicit targeting, and restart restore, but pinning, TTL, and eviction-history governance remain below reference-grade parity"
        )
        recommended_next_step = (
            "freeze remaining absent controls and shift the next locally reducible gap away from governance surface work"
        )

    pinning_supported = bool(governance_policy.get("pinning_supported", False))
    ttl_supported = bool(governance_policy.get("ttl_supported", False))
    eviction_history_visible = bool(
        governance_policy.get("eviction_history_visible", False)
    )
    backend_ttl_visible = bool(governance_policy.get("backend_ttl_visible", False))

    if pinning_supported and not ttl_supported and not eviction_history_visible:
        blocked_reason = (
            "owlmlx now owns runtime pinning, but TTL policy and eviction-history governance remain absent"
        )
        recommended_next_step = (
            "continue governance policy controls with TTL policy or eviction-history governance instead of widening cache work"
        )
    elif pinning_supported and ttl_supported and not eviction_history_visible:
        blocked_reason = (
            "owlmlx now owns runtime pinning and TTL policy, but eviction-history governance remains absent"
        )
        recommended_next_step = (
            "continue the governance fallback branch with eviction-history governance instead of reopening cache widening"
        )
    elif pinning_supported and ttl_supported and eviction_history_visible:
        blocked_reason = (
            "governance policy controls now exist locally; remaining closure is no longer policy-grade on this host"
        )
        recommended_next_step = (
            "return attention to supported-host baseline establishment instead of widening cache or inventing more local governance policy debt"
        )

    return MultiModelGovernanceControls(
        resident_model_count=resident_model_count,
        active_model_id=str(active_model_id) if active_model_id is not None else None,
        controls_rung=controls_rung,
        status="partial",
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
        transition_count=transition_count,
        default_selection_policy_visible=True,
        explicit_model_targeting_supported=True,
        explicit_unload_required=True,
        restart_surface_visible=bool(
            "restartable_models" in restart and "restart_exhausted_models" in restart
        ),
        unload_surface_visible=True,
        pinning_supported=pinning_supported,
        ttl_supported=ttl_supported,
        eviction_history_visible=eviction_history_visible,
        backend_ttl_visible=backend_ttl_visible,
        transition_history_visible=transition_history_visible,
        active_reassignment_visible=active_reassignment_visible,
        restart_restore_visible=restart_restore_visible,
        explicit_targeting_evidence_visible=explicit_targeting_evidence_visible,
    )


def multi_model_governance_controls_to_dict(
    controls: MultiModelGovernanceControls,
) -> dict[str, Any]:
    """Serialize runtime-owned multi-model governance controls."""

    return {
        "contract": {
            "surface": "owlmlx.multi_model_governance_controls",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "control_presence",
                "transition_evidence",
            ],
        },
        "summary": {
            "status": controls.status,
            "controls_rung": controls.controls_rung,
            "blocked_reason": controls.blocked_reason,
            "recommended_next_step": controls.recommended_next_step,
        },
        "control_presence": {
            "resident_model_count": controls.resident_model_count,
            "active_model_id": controls.active_model_id,
            "default_selection_policy_visible": controls.default_selection_policy_visible,
            "explicit_model_targeting_supported": (
                controls.explicit_model_targeting_supported
            ),
            "explicit_unload_required": controls.explicit_unload_required,
            "restart_surface_visible": controls.restart_surface_visible,
            "unload_surface_visible": controls.unload_surface_visible,
            "pinning_supported": controls.pinning_supported,
            "ttl_supported": controls.ttl_supported,
            "eviction_history_visible": controls.eviction_history_visible,
            "backend_ttl_visible": controls.backend_ttl_visible,
        },
        "transition_evidence": {
            "transition_history_visible": controls.transition_history_visible,
            "transition_count": controls.transition_count,
            "active_reassignment_visible": controls.active_reassignment_visible,
            "restart_restore_visible": controls.restart_restore_visible,
            "explicit_targeting_evidence_visible": (
                controls.explicit_targeting_evidence_visible
            ),
        },
    }
