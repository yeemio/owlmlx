"""Runtime-owned residual policy-gap truth for multi-model governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .multi_model_governance_controls import (
    MultiModelGovernanceControls,
    build_multi_model_governance_controls,
)
from .multi_model_governance_transition_ledger import (
    MultiModelGovernanceTransitionLedger,
    build_multi_model_governance_transition_ledger,
)


@dataclass(frozen=True, slots=True)
class MultiModelGovernancePolicyGap:
    """Exact residual policy gap after governance observations are frozen."""

    controls: MultiModelGovernanceControls
    transition_ledger: MultiModelGovernanceTransitionLedger
    status: str
    policy_gap_rung: str
    residual_blocker: str | None
    recommended_next_step: str
    observed_runtime_behavior_frozen: bool
    absent_policy_controls: tuple[str, ...]
    present_policy_controls: tuple[str, ...]


def build_multi_model_governance_policy_gap(
    *,
    controls: MultiModelGovernanceControls | None = None,
    transition_ledger: MultiModelGovernanceTransitionLedger | None = None,
) -> MultiModelGovernancePolicyGap:
    """Build the exact residual policy-grade governance gap."""

    governance_controls = (
        controls
        if isinstance(controls, MultiModelGovernanceControls)
        else build_multi_model_governance_controls()
    )
    governance_transition_ledger = (
        transition_ledger
        if isinstance(transition_ledger, MultiModelGovernanceTransitionLedger)
        else build_multi_model_governance_transition_ledger()
    )

    absent_policy_controls: list[str] = []
    present_policy_controls: list[str] = []

    if governance_controls.pinning_supported:
        present_policy_controls.append("pinning")
    else:
        absent_policy_controls.append("pinning")

    if governance_controls.ttl_supported:
        present_policy_controls.append("ttl_policy")
    else:
        absent_policy_controls.append("ttl_policy")

    if governance_controls.eviction_history_visible:
        present_policy_controls.append("eviction_history_governance")
    else:
        absent_policy_controls.append("eviction_history_governance")

    observed_runtime_behavior_frozen = (
        governance_controls.controls_rung == "partial_closure"
        and governance_transition_ledger.ledger_rung == "partial_closure"
    )

    policy_gap_rung = "observation_gap_open"
    residual_blocker = (
        "governance runtime observations are still too weak to freeze the remaining policy-grade controls gap"
    )
    recommended_next_step = (
        "finish freezing runtime-owned governance observations before reducing the residual policy gap"
    )

    if observed_runtime_behavior_frozen:
        policy_gap_rung = "policy_gap_exact"
        residual_blocker = (
            "remaining governance gap is now policy-grade only: pinning, TTL policy, and eviction-history governance remain absent"
        )
        recommended_next_step = (
            "either implement one of the absent lifecycle controls or move the dominant gap to the next locally reducible stability gap"
        )

    return MultiModelGovernancePolicyGap(
        controls=governance_controls,
        transition_ledger=governance_transition_ledger,
        status="partial",
        policy_gap_rung=policy_gap_rung,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
        observed_runtime_behavior_frozen=observed_runtime_behavior_frozen,
        absent_policy_controls=tuple(absent_policy_controls),
        present_policy_controls=tuple(present_policy_controls),
    )


def multi_model_governance_policy_gap_to_dict(
    policy_gap: MultiModelGovernancePolicyGap,
) -> dict[str, Any]:
    """Serialize the residual governance policy gap."""

    return {
        "contract": {
            "surface": "owlmlx.multi_model_governance_policy_gap",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "observed_runtime_behavior",
                "policy_controls",
            ],
        },
        "summary": {
            "status": policy_gap.status,
            "policy_gap_rung": policy_gap.policy_gap_rung,
            "residual_blocker": policy_gap.residual_blocker,
            "recommended_next_step": policy_gap.recommended_next_step,
        },
        "observed_runtime_behavior": {
            "observed_runtime_behavior_frozen": (
                policy_gap.observed_runtime_behavior_frozen
            ),
            "controls_rung": policy_gap.controls.controls_rung,
            "transition_ledger_rung": policy_gap.transition_ledger.ledger_rung,
        },
        "policy_controls": {
            "present_policy_controls": list(policy_gap.present_policy_controls),
            "absent_policy_controls": list(policy_gap.absent_policy_controls),
        },
    }
