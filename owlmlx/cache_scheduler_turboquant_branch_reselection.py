"""Runtime-owned branch reselection after the carrier-local cache chain is complete."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_branch_reselection import (
    CachePreClaimAdmissionCarrierBranchReselection,
    build_cache_pre_claim_admission_carrier_branch_reselection,
)
from .cache_scheduler_branch_selection import (
    CacheSchedulerBranchSelection,
    build_cache_scheduler_branch_selection,
)
from .cache_turboquant_preconditions_gap import (
    CacheTurboQuantPreconditionsGap,
    build_cache_turboquant_preconditions_gap,
)


@dataclass(frozen=True, slots=True)
class CacheSchedulerTurboQuantBranchReselection:
    """Exact truth for the next non-carrier cache branch."""

    carrier_branch_reselection: CachePreClaimAdmissionCarrierBranchReselection
    scheduler_branch_selection: CacheSchedulerBranchSelection
    turboquant_preconditions_gap: CacheTurboQuantPreconditionsGap
    status: str
    reselection_rung: str
    selected_branch: str
    selected_branch_status: str
    secondary_branch: str
    secondary_branch_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_scheduler_turboquant_branch_reselection(
    *,
    carrier_branch_reselection: CachePreClaimAdmissionCarrierBranchReselection | None = None,
    scheduler_branch_selection: CacheSchedulerBranchSelection | None = None,
    turboquant_preconditions_gap: CacheTurboQuantPreconditionsGap | None = None,
) -> CacheSchedulerTurboQuantBranchReselection:
    """Build exact scheduler-vs-TurboQuant branch reselection truth."""

    carrier = (
        carrier_branch_reselection
        if isinstance(
            carrier_branch_reselection, CachePreClaimAdmissionCarrierBranchReselection
        )
        else build_cache_pre_claim_admission_carrier_branch_reselection()
    )
    scheduler = (
        scheduler_branch_selection
        if isinstance(scheduler_branch_selection, CacheSchedulerBranchSelection)
        else build_cache_scheduler_branch_selection()
    )
    turboquant = (
        turboquant_preconditions_gap
        if isinstance(turboquant_preconditions_gap, CacheTurboQuantPreconditionsGap)
        else build_cache_turboquant_preconditions_gap()
    )

    reselection_rung = "scheduler_turboquant_branch_unresolved"
    selected_branch = "carrier_branch_not_yet_complete"
    selected_branch_status = "not_reselectable"
    secondary_branch = "carrier_branch_not_yet_complete"
    secondary_branch_status = "not_reselectable"
    residual_blocker = (
        "scheduler-vs-TurboQuant branch reselection is not yet exact because the carrier-local exactness chain is not complete"
    )
    recommended_next_step = (
        "finish the carrier-local exactness chain before reselecting the next non-carrier cache branch"
    )

    if carrier.reselection_rung == "carrier_branch_reselection_exact":
        reselection_rung = "scheduler_turboquant_branch_exact"
        selected_branch = "scheduler_depth"
        selected_branch_status = scheduler.selected_branch
        secondary_branch = "turboquant_preconditions"
        secondary_branch_status = turboquant.preconditions_rung
        residual_blocker = (
            "the carrier-local exactness chain is complete; remaining cache closure reselects to scheduler depth first, while TurboQuant stays exact-but-secondary on the current path"
        )
        recommended_next_step = (
            "treat cache as scheduler-depth work on this path; keep TurboQuant exact-but-secondary and continue with the selected scheduler branch without reopening the carrier-local ingress chain"
        )

    return CacheSchedulerTurboQuantBranchReselection(
        carrier_branch_reselection=carrier,
        scheduler_branch_selection=scheduler,
        turboquant_preconditions_gap=turboquant,
        status="partial",
        reselection_rung=reselection_rung,
        selected_branch=selected_branch,
        selected_branch_status=selected_branch_status,
        secondary_branch=secondary_branch,
        secondary_branch_status=secondary_branch_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_scheduler_turboquant_branch_reselection_to_dict(
    reselection: CacheSchedulerTurboQuantBranchReselection,
) -> dict[str, object]:
    """Serialize scheduler-vs-TurboQuant branch reselection truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_scheduler_turboquant_branch_reselection",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "selected_branch",
                "secondary_branch",
            ],
        },
        "summary": {
            "status": reselection.status,
            "reselection_rung": reselection.reselection_rung,
            "residual_blocker": reselection.residual_blocker,
            "recommended_next_step": reselection.recommended_next_step,
        },
        "selected_branch": {
            "branch": reselection.selected_branch,
            "status": reselection.selected_branch_status,
        },
        "secondary_branch": {
            "branch": reselection.secondary_branch,
            "status": reselection.secondary_branch_status,
        },
    }
