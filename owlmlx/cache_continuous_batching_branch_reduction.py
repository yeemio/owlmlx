"""Runtime-owned continuous-batching branch reduction after scheduler branch reselection."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_batching_mechanism_subgap import (
    CacheBatchingMechanismSubgap,
    build_cache_batching_mechanism_subgap,
)
from .cache_scheduler_turboquant_branch_reselection import (
    CacheSchedulerTurboQuantBranchReselection,
    build_cache_scheduler_turboquant_branch_reselection,
)


@dataclass(frozen=True, slots=True)
class CacheContinuousBatchingBranchReduction:
    """Exact reduction target inside the selected continuous-batching branch."""

    scheduler_turboquant_branch_reselection: CacheSchedulerTurboQuantBranchReselection
    batching_mechanism_subgap: CacheBatchingMechanismSubgap
    status: str
    reduction_rung: str
    selected_scheduler_branch: str
    selected_scheduler_branch_status: str
    selected_reduction_target: str
    selected_reduction_target_status: str
    secondary_scheduler_reduction: tuple[str, ...]
    secondary_scheduler_reduction_statuses: tuple[str, ...]
    turboquant_branch_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_continuous_batching_branch_reduction(
    *,
    scheduler_turboquant_branch_reselection: CacheSchedulerTurboQuantBranchReselection | None = None,
    batching_mechanism_subgap: CacheBatchingMechanismSubgap | None = None,
) -> CacheContinuousBatchingBranchReduction:
    """Build the next exact continuous-batching reduction target."""

    branch_reselection = (
        scheduler_turboquant_branch_reselection
        if isinstance(
            scheduler_turboquant_branch_reselection,
            CacheSchedulerTurboQuantBranchReselection,
        )
        else build_cache_scheduler_turboquant_branch_reselection()
    )
    mechanism_subgap = (
        batching_mechanism_subgap
        if isinstance(batching_mechanism_subgap, CacheBatchingMechanismSubgap)
        else build_cache_batching_mechanism_subgap()
    )

    reduction_rung = "continuous_batching_branch_unresolved"
    selected_scheduler_branch = "scheduler_depth_not_yet_reselected"
    selected_scheduler_branch_status = "not_reduced"
    selected_reduction_target = "scheduler_depth_not_yet_reselected"
    selected_reduction_target_status = "not_reduced"
    secondary_scheduler_reduction = ("scheduler_depth_not_yet_reselected",)
    secondary_scheduler_reduction_statuses = ("not_reduced",)
    turboquant_branch_status = branch_reselection.secondary_branch_status
    residual_blocker = (
        "continuous-batching branch reduction is not yet exact because scheduler-vs-TurboQuant branch reselection is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze scheduler-vs-TurboQuant branch reselection before reducing the selected scheduler branch further"
    )

    if (
        branch_reselection.reselection_rung == "scheduler_turboquant_branch_exact"
        and branch_reselection.selected_branch_status == "continuous_batching"
        and mechanism_subgap.subgap_rung == "mechanism_subgap_exact"
    ):
        reduction_rung = "continuous_batching_branch_exact"
        selected_scheduler_branch = "continuous_batching"
        selected_scheduler_branch_status = "selected_on_current_path"
        selected_reduction_target = mechanism_subgap.selected_mechanism
        selected_reduction_target_status = mechanism_subgap.selected_mechanism_status
        secondary_scheduler_reduction = (
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        )
        secondary_scheduler_reduction_statuses = (
            mechanism_subgap.shared_prefill_batch_step_status,
            mechanism_subgap.interleaved_decode_scheduler_status,
        )
        turboquant_branch_status = branch_reselection.secondary_branch_status
        residual_blocker = (
            "scheduler depth remains the active cache branch on this path, and inside that branch the next honest reduction target is request aggregation; TurboQuant stays exact-but-secondary and the other batching mechanisms remain downstream of aggregated admission"
        )
        recommended_next_step = (
            "re-enter the request-aggregation-window chain as the selected continuous-batching reduction target; keep shared_prefill_batch_step and interleaved_decode_scheduler secondary, and keep TurboQuant exact-but-secondary"
        )

    return CacheContinuousBatchingBranchReduction(
        scheduler_turboquant_branch_reselection=branch_reselection,
        batching_mechanism_subgap=mechanism_subgap,
        status="partial",
        reduction_rung=reduction_rung,
        selected_scheduler_branch=selected_scheduler_branch,
        selected_scheduler_branch_status=selected_scheduler_branch_status,
        selected_reduction_target=selected_reduction_target,
        selected_reduction_target_status=selected_reduction_target_status,
        secondary_scheduler_reduction=secondary_scheduler_reduction,
        secondary_scheduler_reduction_statuses=secondary_scheduler_reduction_statuses,
        turboquant_branch_status=turboquant_branch_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_continuous_batching_branch_reduction_to_dict(
    reduction: CacheContinuousBatchingBranchReduction,
) -> dict[str, object]:
    """Serialize continuous-batching branch reduction truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_continuous_batching_branch_reduction",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "selected_scheduler_branch",
                "selected_reduction_target",
                "secondary_scheduler_reduction",
            ],
        },
        "summary": {
            "status": reduction.status,
            "reduction_rung": reduction.reduction_rung,
            "residual_blocker": reduction.residual_blocker,
            "recommended_next_step": reduction.recommended_next_step,
        },
        "selected_scheduler_branch": {
            "branch": reduction.selected_scheduler_branch,
            "status": reduction.selected_scheduler_branch_status,
        },
        "selected_reduction_target": {
            "target": reduction.selected_reduction_target,
            "status": reduction.selected_reduction_target_status,
        },
        "secondary_scheduler_reduction": [
            {
                "target": target,
                "status": status,
            }
            for target, status in zip(
                reduction.secondary_scheduler_reduction,
                reduction.secondary_scheduler_reduction_statuses,
                strict=True,
            )
        ],
        "secondary_runtime_branch": {
            "branch": "turboquant_preconditions",
            "status": reduction.turboquant_branch_status,
        },
    }
