"""Runtime-owned multi-model governance transition ledger for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MultiModelGovernanceTransitionLedger:
    """Stable runtime-owned transition ledger for multi-model governance."""

    resident_model_count: int
    active_model_id: str | None
    transition_count: int
    recent_window_runs: int
    status: str
    ledger_rung: str
    blocked_reason: str | None
    recommended_next_step: str
    active_reassignment_visible: bool
    explicit_targeting_evidence_visible: bool
    restart_restore_visible: bool


def build_multi_model_governance_transition_ledger(
    runtime_status: Mapping[str, Any] | None = None,
    *,
    transition_evidence: Mapping[str, Any] | None = None,
) -> MultiModelGovernanceTransitionLedger:
    """Build runtime-owned multi-model governance transition ledger."""

    raw = dict(runtime_status or {})
    inventory = raw.get("inventory", {})
    active_model_id = raw.get("active_model_id")
    resident_model_count = int(inventory.get("model_count", 0))

    observations = raw.get("governance_observations", {})
    if isinstance(transition_evidence, Mapping):
        evidence = dict(transition_evidence)
    elif isinstance(observations, Mapping):
        evidence = dict(observations)
    else:
        evidence = {}
    transition_count = max(int(evidence.get("transition_count", 0)), 0)
    recent_window_runs = max(int(evidence.get("recent_window_runs", 0)), 0)
    active_reassignment_visible = bool(evidence.get("active_reassignment_visible", False))
    explicit_targeting_evidence_visible = bool(
        evidence.get("explicit_targeting_evidence_visible", False)
    )
    restart_restore_visible = bool(evidence.get("restart_restore_visible", False))

    ledger_rung = "no_transition_runs"
    blocked_reason = (
        "owlmlx still lacks repeated governance-transition evidence strong enough to reduce the remaining lifecycle gap"
    )
    recommended_next_step = (
        "run repeated governance transitions and keep absent lifecycle controls exact"
    )

    if transition_count > 0:
        ledger_rung = "transition_visibility"
        blocked_reason = (
            "owlmlx now has one governance-transition evidence window, but repeated transition proof remains limited"
        )
        recommended_next_step = (
            "promote repeated governance transitions before claiming stronger lifecycle closure"
        )

    if transition_count >= 2 and recent_window_runs >= 2:
        ledger_rung = "repeated_transition_visibility"
        blocked_reason = (
            "owlmlx now has repeated governance-transition evidence, but pinning, TTL, and eviction-history governance remain absent"
        )
        recommended_next_step = (
            "keep absent lifecycle controls exact and freeze transition evidence before moving the dominant gap"
        )

    if (
        transition_count >= 4
        and recent_window_runs >= 2
        and active_reassignment_visible
        and explicit_targeting_evidence_visible
        and restart_restore_visible
    ):
        ledger_rung = "partial_closure"
        blocked_reason = (
            "owlmlx now has repeated governance-transition evidence for active reassignment, explicit targeting, and restart restore, but lifecycle controls such as pinning, TTL, and eviction history remain below reference-grade parity"
        )
        recommended_next_step = (
            "freeze the remaining absent lifecycle controls and refresh the customer-runtime evidence ledger"
        )

    return MultiModelGovernanceTransitionLedger(
        resident_model_count=resident_model_count,
        active_model_id=str(active_model_id) if active_model_id is not None else None,
        transition_count=transition_count,
        recent_window_runs=recent_window_runs,
        status="partial",
        ledger_rung=ledger_rung,
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
        active_reassignment_visible=active_reassignment_visible,
        explicit_targeting_evidence_visible=explicit_targeting_evidence_visible,
        restart_restore_visible=restart_restore_visible,
    )


def multi_model_governance_transition_ledger_to_dict(
    ledger: MultiModelGovernanceTransitionLedger,
) -> dict[str, Any]:
    """Serialize runtime-owned multi-model governance transition ledger."""

    return {
        "contract": {
            "surface": "owlmlx.multi_model_governance_transition_ledger",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "recent_window",
                "transition_signals",
            ],
        },
        "summary": {
            "status": ledger.status,
            "ledger_rung": ledger.ledger_rung,
            "blocked_reason": ledger.blocked_reason,
            "recommended_next_step": ledger.recommended_next_step,
        },
        "recent_window": {
            "resident_model_count": ledger.resident_model_count,
            "active_model_id": ledger.active_model_id,
            "transition_count": ledger.transition_count,
            "recent_window_runs": ledger.recent_window_runs,
        },
        "transition_signals": {
            "active_reassignment_visible": ledger.active_reassignment_visible,
            "explicit_targeting_evidence_visible": (
                ledger.explicit_targeting_evidence_visible
            ),
            "restart_restore_visible": ledger.restart_restore_visible,
        },
    }
