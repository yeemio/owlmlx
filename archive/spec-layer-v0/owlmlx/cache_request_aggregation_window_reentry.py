"""Runtime-owned request-aggregation-window reentry after branch reduction is exact."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_continuous_batching_branch_reduction import (
    CacheContinuousBatchingBranchReduction,
    build_cache_continuous_batching_branch_reduction,
)
from .cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
    build_cache_request_aggregation_window_exactness,
)


@dataclass(frozen=True, slots=True)
class CacheRequestAggregationWindowReentry:
    """Exact reentry point into the request-aggregation chain."""

    continuous_batching_branch_reduction: CacheContinuousBatchingBranchReduction
    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness
    status: str
    reentry_rung: str
    selected_reentry_target: str
    selected_reentry_target_status: str
    preserved_secondary_scheduler_reduction: tuple[str, ...]
    preserved_secondary_runtime_branch: str
    preserved_secondary_runtime_branch_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_request_aggregation_window_reentry(
    *,
    continuous_batching_branch_reduction: CacheContinuousBatchingBranchReduction | None = None,
    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness | None = None,
) -> CacheRequestAggregationWindowReentry:
    """Build exact request-aggregation reentry truth."""

    branch_reduction = (
        continuous_batching_branch_reduction
        if isinstance(
            continuous_batching_branch_reduction,
            CacheContinuousBatchingBranchReduction,
        )
        else build_cache_continuous_batching_branch_reduction()
    )
    aggregation_exactness = (
        request_aggregation_window_exactness
        if isinstance(
            request_aggregation_window_exactness,
            CacheRequestAggregationWindowExactness,
        )
        else build_cache_request_aggregation_window_exactness()
    )

    reentry_rung = "aggregation_reentry_unresolved"
    selected_reentry_target = "continuous_batching_branch_not_yet_exact"
    selected_reentry_target_status = "not_reentered"
    preserved_secondary_scheduler_reduction = ("continuous_batching_branch_not_yet_exact",)
    preserved_secondary_runtime_branch = "continuous_batching_branch_not_yet_exact"
    preserved_secondary_runtime_branch_status = "not_reentered"
    residual_blocker = (
        "request-aggregation reentry is not yet exact because continuous-batching branch reduction is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze continuous-batching branch reduction before re-entering the request-aggregation-window chain"
    )

    if (
        branch_reduction.reduction_rung == "continuous_batching_branch_exact"
        and branch_reduction.selected_reduction_target == "request_aggregation_window"
        and aggregation_exactness.exactness_rung == "aggregation_window_blocker_exact"
    ):
        reentry_rung = "aggregation_reentry_exact"
        selected_reentry_target = "request_aggregation_window"
        selected_reentry_target_status = "reentered_as_active_cache_subchain"
        preserved_secondary_scheduler_reduction = (
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        )
        preserved_secondary_runtime_branch = "turboquant_preconditions"
        preserved_secondary_runtime_branch_status = (
            branch_reduction.turboquant_branch_status
        )
        residual_blocker = (
            "continuous-batching reduction now re-enters the request-aggregation-window chain on the active path, while shared-prefill and interleaved-decode remain secondary and TurboQuant stays exact-but-secondary"
        )
        recommended_next_step = (
            "continue down the request-aggregation-window chain without reopening carrier-local or generic continuous-batching branch selection truth"
        )

    return CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=branch_reduction,
        request_aggregation_window_exactness=aggregation_exactness,
        status="partial",
        reentry_rung=reentry_rung,
        selected_reentry_target=selected_reentry_target,
        selected_reentry_target_status=selected_reentry_target_status,
        preserved_secondary_scheduler_reduction=preserved_secondary_scheduler_reduction,
        preserved_secondary_runtime_branch=preserved_secondary_runtime_branch,
        preserved_secondary_runtime_branch_status=preserved_secondary_runtime_branch_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_request_aggregation_window_reentry_to_dict(
    reentry: CacheRequestAggregationWindowReentry,
) -> dict[str, object]:
    """Serialize request-aggregation reentry truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_request_aggregation_window_reentry",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "selected_reentry_target",
                "preserved_secondary_scheduler_reduction",
                "preserved_secondary_runtime_branch",
            ],
        },
        "summary": {
            "status": reentry.status,
            "reentry_rung": reentry.reentry_rung,
            "residual_blocker": reentry.residual_blocker,
            "recommended_next_step": reentry.recommended_next_step,
        },
        "selected_reentry_target": {
            "target": reentry.selected_reentry_target,
            "status": reentry.selected_reentry_target_status,
        },
        "preserved_secondary_scheduler_reduction": list(
            reentry.preserved_secondary_scheduler_reduction
        ),
        "preserved_secondary_runtime_branch": {
            "branch": reentry.preserved_secondary_runtime_branch,
            "status": reentry.preserved_secondary_runtime_branch_status,
        },
    }
