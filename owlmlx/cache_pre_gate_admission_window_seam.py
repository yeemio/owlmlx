"""Runtime-owned active seam reduction for the pre-gate admission window."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_gate_admission_hook_exactness import (
    CachePreGateAdmissionHookExactness,
    build_cache_pre_gate_admission_hook_exactness,
)
from .cache_request_aggregation_active_seam import (
    CacheRequestAggregationActiveSeam,
    build_cache_request_aggregation_active_seam,
)


@dataclass(frozen=True, slots=True)
class CachePreGateAdmissionWindowSeam:
    """Exact active seam truth once request aggregation narrows to pre-gate admission."""

    request_aggregation_active_seam: CacheRequestAggregationActiveSeam
    pre_gate_admission_hook_exactness: CachePreGateAdmissionHookExactness
    status: str
    seam_rung: str
    selected_seam: str
    selected_seam_status: str
    preserved_secondary_dependencies: tuple[str, ...]
    preserved_secondary_runtime_branch: str
    preserved_secondary_runtime_branch_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_gate_admission_window_seam(
    *,
    request_aggregation_active_seam: CacheRequestAggregationActiveSeam | None = None,
    pre_gate_admission_hook_exactness: CachePreGateAdmissionHookExactness | None = None,
) -> CachePreGateAdmissionWindowSeam:
    """Build exact pre-gate admission-window seam truth."""

    active_seam = (
        request_aggregation_active_seam
        if isinstance(request_aggregation_active_seam, CacheRequestAggregationActiveSeam)
        else build_cache_request_aggregation_active_seam()
    )
    hook_exactness = (
        pre_gate_admission_hook_exactness
        if isinstance(pre_gate_admission_hook_exactness, CachePreGateAdmissionHookExactness)
        else build_cache_pre_gate_admission_hook_exactness()
    )

    seam_rung = "pre_gate_admission_window_seam_unresolved"
    selected_seam = "request_aggregation_active_seam_not_yet_exact"
    selected_seam_status = "not_selected"
    preserved_secondary_dependencies = ("request_aggregation_active_seam_not_yet_exact",)
    preserved_secondary_runtime_branch = "request_aggregation_active_seam_not_yet_exact"
    preserved_secondary_runtime_branch_status = "not_selected"
    residual_blocker = (
        "pre-gate admission-window seam is not yet exact because request-aggregation active seam is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze request-aggregation active seam before narrowing the pre-gate admission-window seam further"
    )

    if (
        active_seam.seam_rung == "aggregation_active_seam_exact"
        and active_seam.selected_seam == "pre_gate_admission_window"
        and hook_exactness.exactness_rung == "admission_hook_blocker_exact"
    ):
        seam_rung = "pre_gate_admission_window_seam_exact"
        selected_seam = "bounded_pre_gate_admission_hook"
        selected_seam_status = hook_exactness.admission_hook_status
        preserved_secondary_dependencies = (
            "single_request_per_child_exchange_blocks_aggregated_dispatch",
            "stream_session_holds_gate_until_completion",
        )
        preserved_secondary_runtime_branch = "turboquant_preconditions"
        preserved_secondary_runtime_branch_status = "preconditions_exact"
        if (
            hook_exactness.admission_hook_status
            == "bounded_hook_present_but_no_request_aggregation_window"
        ):
            residual_blocker = (
                "request aggregation now reduces to the existing bounded pre-gate admission hook on this path: the hook is runtime-owned and precedes whole-request gate claim, but it remains inert/observational and still does not form a request-aggregation window; child exchange, stream hold, and TurboQuant remain secondary"
            )
            recommended_next_step = (
                "continue with post-structural pre-gate admission-window work on this path; the bounded hook now exists, so the next exact blocker is turning that inert seam into a cohort-forming request-aggregation window without weakening post-claim serial invariants"
            )
        else:
            residual_blocker = (
                "request aggregation now reduces to the pre-gate admission-window seam on this path: a bounded pre-gate admission hook is still missing before whole-request gate claim, while child exchange, stream hold, and TurboQuant remain secondary"
            )
            recommended_next_step = (
                "continue with bounded pre-gate admission-hook work on this path without reopening request-aggregation active-seam or carrier-local exactness"
            )

    return CachePreGateAdmissionWindowSeam(
        request_aggregation_active_seam=active_seam,
        pre_gate_admission_hook_exactness=hook_exactness,
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


def cache_pre_gate_admission_window_seam_to_dict(
    seam: CachePreGateAdmissionWindowSeam,
) -> dict[str, object]:
    """Serialize pre-gate admission-window seam truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_gate_admission_window_seam",
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
