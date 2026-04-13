"""Runtime-owned reselection of the next locally reducible dominant gap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cache_scheduler_implementation_backlog import (
    CacheSchedulerImplementationBacklog,
    build_cache_scheduler_implementation_backlog,
)
from .cache_turboquant_preconditions_gap import (
    CacheTurboQuantPreconditionsGap,
    build_cache_turboquant_preconditions_gap,
)
from .heavy_weight_repeatability_status import (
    HeavyWeightRuntimeRepeatabilityStatus,
)
from .multi_model_governance_policy_gap import (
    MultiModelGovernancePolicyGap,
    build_multi_model_governance_policy_gap,
)


@dataclass(frozen=True, slots=True)
class DominantGapReselection:
    """Exact re-evaluation of the next dominant locally reducible gap."""

    cache_scheduler_backlog: CacheSchedulerImplementationBacklog
    cache_turboquant_preconditions: CacheTurboQuantPreconditionsGap
    governance_policy_gap: MultiModelGovernancePolicyGap
    heavy_weight_repeatability: HeavyWeightRuntimeRepeatabilityStatus
    status: str
    decision_rung: str
    selected_gap: str
    rationale: str


def build_dominant_gap_reselection(
    *,
    cache_scheduler_backlog: CacheSchedulerImplementationBacklog | None = None,
    cache_turboquant_preconditions: CacheTurboQuantPreconditionsGap | None = None,
    governance_policy_gap: MultiModelGovernancePolicyGap | None = None,
    heavy_weight_repeatability: HeavyWeightRuntimeRepeatabilityStatus | None = None,
) -> DominantGapReselection:
    """Build the runtime-owned dominant-gap reselection decision."""

    cache_backlog = (
        cache_scheduler_backlog
        if isinstance(cache_scheduler_backlog, CacheSchedulerImplementationBacklog)
        else build_cache_scheduler_implementation_backlog()
    )
    turboquant_gap = (
        cache_turboquant_preconditions
        if isinstance(cache_turboquant_preconditions, CacheTurboQuantPreconditionsGap)
        else build_cache_turboquant_preconditions_gap()
    )
    governance_gap = (
        governance_policy_gap
        if isinstance(governance_policy_gap, MultiModelGovernancePolicyGap)
        else (
            MultiModelGovernancePolicyGap(
                controls=getattr(governance_policy_gap, "controls", object()),
                transition_ledger=getattr(
                    governance_policy_gap, "transition_ledger", object()
                ),
                status=str(getattr(governance_policy_gap, "status", "partial")),
                policy_gap_rung=str(
                    getattr(governance_policy_gap, "policy_gap_rung", "observation_gap_open")
                ),
                residual_blocker=getattr(governance_policy_gap, "residual_blocker", None),
                recommended_next_step=str(
                    getattr(
                        governance_policy_gap,
                        "recommended_next_step",
                        "finish freezing runtime-owned governance observations before reducing the residual policy gap",
                    )
                ),
                observed_runtime_behavior_frozen=bool(
                    getattr(governance_policy_gap, "observed_runtime_behavior_frozen", False)
                ),
                absent_policy_controls=tuple(
                    getattr(
                        governance_policy_gap,
                        "absent_policy_controls",
                        getattr(governance_policy_gap, "policy_controls_absent", ()),
                    )
                ),
                present_policy_controls=tuple(
                    getattr(governance_policy_gap, "present_policy_controls", ())
                ),
            )
            if hasattr(governance_policy_gap, "policy_gap_rung")
            else build_multi_model_governance_policy_gap()
        )
    )
    heavy_weight = (
        heavy_weight_repeatability
        if isinstance(heavy_weight_repeatability, HeavyWeightRuntimeRepeatabilityStatus)
        else HeavyWeightRuntimeRepeatabilityStatus(
            host_stability=object(),
            first_smoke_decision=object(),
            supported_host_proof_visible=False,
            supported_host_repeat_runs=0,
            status="partial",
            repeatability_rung="local_blocked",
            blocked_reason="supported host/system image is still required",
            recommended_next_step="move repeated heavy-weight validation to a supported host before raising heavier runtime claims",
        )
    )

    selected_gap = "cache_scheduler_depth"
    decision_rung = "reselection_exact"
    rationale = (
        "cache_scheduler_depth remains the next locally reducible dominant gap because scheduler implementation backlog is exact, TurboQuant is exact-but-secondary, governance is already narrowed to a policy-grade gap, and heavy-weight repeatability is still externally blocked"
    )

    if governance_gap.policy_gap_rung != "policy_gap_exact":
        selected_gap = "multi_model_lifecycle_governance"
        rationale = (
            "multi_model_lifecycle_governance remains dominant because governance has not yet narrowed to a policy-grade exact gap"
        )
    elif cache_backlog.backlog_rung != "implementation_gap_exact":
        rationale = (
            "cache_scheduler_depth remains dominant because governance is already narrowed to a policy-grade exact gap while cache has not yet narrowed to an exact scheduler implementation backlog"
        )
    elif (
        cache_backlog.backlog_rung == "implementation_gap_exact"
        and turboquant_gap.preconditions_rung != "preconditions_exact"
    ):
        rationale = (
            "cache_scheduler_depth remains dominant because scheduler backlog is exact while TurboQuant preconditions have not yet frozen strongly enough to make the branch fully exact"
        )

    return DominantGapReselection(
        cache_scheduler_backlog=cache_backlog,
        cache_turboquant_preconditions=turboquant_gap,
        governance_policy_gap=governance_gap,
        heavy_weight_repeatability=heavy_weight,
        status="partial",
        decision_rung=decision_rung,
        selected_gap=selected_gap,
        rationale=rationale,
    )


def dominant_gap_reselection_to_dict(
    decision: DominantGapReselection,
) -> dict[str, object]:
    """Serialize dominant-gap reselection."""

    return {
        "contract": {
            "surface": "owlmlx.dominant_gap_reselection",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "candidate_gap_truth",
            ],
        },
        "summary": {
            "status": decision.status,
            "decision_rung": decision.decision_rung,
            "selected_gap": decision.selected_gap,
            "rationale": decision.rationale,
        },
        "candidate_gap_truth": {
            "cache_scheduler_depth": {
                "scheduler_backlog_rung": decision.cache_scheduler_backlog.backlog_rung,
                "turboquant_preconditions_rung": decision.cache_turboquant_preconditions.preconditions_rung,
            },
            "multi_model_lifecycle_governance": {
                "policy_gap_rung": decision.governance_policy_gap.policy_gap_rung,
            },
            "heavy_weight_runtime_repeatability": {
                "repeatability_rung": decision.heavy_weight_repeatability.repeatability_rung,
            },
        },
    }
