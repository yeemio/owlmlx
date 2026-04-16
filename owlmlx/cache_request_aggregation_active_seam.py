"""Runtime-owned active seam selection inside the request-aggregation chain."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
    build_cache_request_aggregation_window_exactness,
)
from .cache_request_aggregation_window_reentry import (
    CacheRequestAggregationWindowReentry,
    build_cache_request_aggregation_window_reentry,
)


@dataclass(frozen=True, slots=True)
class CacheRequestAggregationActiveSeam:
    """Exact active seam selection after request aggregation has re-entered."""

    request_aggregation_window_reentry: CacheRequestAggregationWindowReentry
    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness
    status: str
    seam_rung: str
    selected_seam: str
    selected_seam_status: str
    preserved_secondary_dependencies: tuple[str, ...]
    preserved_secondary_runtime_branch: str
    preserved_secondary_runtime_branch_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_request_aggregation_active_seam(
    *,
    request_aggregation_window_reentry: CacheRequestAggregationWindowReentry | None = None,
    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness | None = None,
) -> CacheRequestAggregationActiveSeam:
    """Build the exact active seam inside the request-aggregation chain."""

    reentry = (
        request_aggregation_window_reentry
        if isinstance(request_aggregation_window_reentry, CacheRequestAggregationWindowReentry)
        else build_cache_request_aggregation_window_reentry()
    )
    exactness = (
        request_aggregation_window_exactness
        if isinstance(request_aggregation_window_exactness, CacheRequestAggregationWindowExactness)
        else build_cache_request_aggregation_window_exactness()
    )

    seam_rung = "aggregation_active_seam_unresolved"
    selected_seam = "request_aggregation_not_yet_reentered"
    selected_seam_status = "not_selected"
    preserved_secondary_dependencies = ("request_aggregation_not_yet_reentered",)
    preserved_secondary_runtime_branch = "request_aggregation_not_yet_reentered"
    preserved_secondary_runtime_branch_status = "not_selected"
    residual_blocker = (
        "request-aggregation active seam is not yet exact because request-aggregation reentry is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze request-aggregation reentry before selecting the active seam inside the request-aggregation chain"
    )

    if (
        reentry.reentry_rung == "aggregation_reentry_exact"
        and reentry.selected_reentry_target == "request_aggregation_window"
        and exactness.exactness_rung == "aggregation_window_blocker_exact"
    ):
        seam_rung = "aggregation_active_seam_exact"
        selected_seam = "pre_gate_admission_window"
        selected_seam_status = exactness.ingress_window_status
        preserved_secondary_dependencies = (
            "single_request_per_child_exchange_blocks_aggregated_dispatch",
            "stream_session_holds_gate_until_completion",
        )
        preserved_secondary_runtime_branch = "turboquant_preconditions"
        preserved_secondary_runtime_branch_status = (
            reentry.preserved_secondary_runtime_branch_status
        )
        residual_blocker = (
            "request aggregation now reduces to its active seam on this path: a missing pre-gate admission window before whole-request gate claim, while child exchange, stream hold, and TurboQuant remain secondary"
        )
        recommended_next_step = (
            "continue with the pre-gate admission window seam as the active request-aggregation reduction target without reopening scheduler-branch or carrier-local exactness"
        )

    return CacheRequestAggregationActiveSeam(
        request_aggregation_window_reentry=reentry,
        request_aggregation_window_exactness=exactness,
        status="partial",
        seam_rung=seam_rung,
        selected_seam=selected_seam,
        selected_seam_status=selected_seam_status,
        preserved_secondary_dependencies=preserved_secondary_dependencies,
        preserved_secondary_runtime_branch=preserved_secondary_runtime_branch,
        preserved_secondary_runtime_branch_status=preserved_secondary_runtime_branch_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_request_aggregation_active_seam_to_dict(
    seam: CacheRequestAggregationActiveSeam,
) -> dict[str, object]:
    """Serialize request-aggregation active seam truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_request_aggregation_active_seam",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "selected_seam",
                "preserved_secondary_dependencies",
                "preserved_secondary_runtime_branch",
            ],
        },
        "summary": {
            "status": seam.status,
            "seam_rung": seam.seam_rung,
            "residual_blocker": seam.residual_blocker,
            "recommended_next_step": seam.recommended_next_step,
        },
        "selected_seam": {
            "seam": seam.selected_seam,
            "status": seam.selected_seam_status,
        },
        "preserved_secondary_dependencies": list(seam.preserved_secondary_dependencies),
        "preserved_secondary_runtime_branch": {
            "branch": seam.preserved_secondary_runtime_branch,
            "status": seam.preserved_secondary_runtime_branch_status,
        },
    }
