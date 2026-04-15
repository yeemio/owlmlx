"""Runtime-owned exactness for the request-aggregation-window subgap."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_batching_mechanism_subgap import (
    CacheBatchingMechanismSubgap,
    build_cache_batching_mechanism_subgap,
)


@dataclass(frozen=True, slots=True)
class CacheRequestAggregationWindowExactness:
    """Exact ingress/runtime blockers for request aggregation on the active path."""

    mechanism_subgap: CacheBatchingMechanismSubgap
    status: str
    exactness_rung: str
    ingress_window_status: str
    admission_boundary_status: str
    child_dependency_status: str
    stream_dependency_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_request_aggregation_window_exactness(
    *,
    mechanism_subgap: CacheBatchingMechanismSubgap | None = None,
) -> CacheRequestAggregationWindowExactness:
    """Build exact request-aggregation-window truth for the active path."""

    subgap = (
        mechanism_subgap
        if isinstance(mechanism_subgap, CacheBatchingMechanismSubgap)
        else build_cache_batching_mechanism_subgap()
    )

    exactness_rung = "aggregation_window_unresolved"
    ingress_window_status = "not_frozen"
    admission_boundary_status = "not_frozen"
    child_dependency_status = "not_frozen"
    stream_dependency_status = "not_frozen"
    residual_blocker = (
        "request aggregation window exactness is not yet frozen because the batching mechanism subgap is not exact"
    )
    recommended_next_step = (
        "freeze the exact batching mechanism subgap before reducing request aggregation into ingress and dependency blockers"
    )

    if subgap.subgap_rung == "mechanism_subgap_exact":
        exactness_rung = "aggregation_window_blocker_exact"
        ingress_window_status = "missing_pre_gate_admission_window"
        admission_boundary_status = (
            "generation_gate_claims_session_before_cohort_formation"
        )
        child_dependency_status = "single_request_per_child_exchange_blocks_aggregated_dispatch"
        stream_dependency_status = "stream_session_holds_gate_until_completion"
        residual_blocker = (
            "request aggregation is now frozen as an exact ingress/runtime blocker: the current path has no pre-gate admission window where multiple requests can form a cohort before the generation gate claims the session, and even if such a window existed the child exchange and streaming path still assume one request at a time"
        )
        recommended_next_step = (
            "treat request aggregation as pre-gate admission-boundary work on this path; first introduce a bounded cohorting window ahead of whole-request gate entry, then revisit aggregated child dispatch and stream-session release without breaking the validated serial safety boundary"
        )

    return CacheRequestAggregationWindowExactness(
        mechanism_subgap=subgap,
        status="partial",
        exactness_rung=exactness_rung,
        ingress_window_status=ingress_window_status,
        admission_boundary_status=admission_boundary_status,
        child_dependency_status=child_dependency_status,
        stream_dependency_status=stream_dependency_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_request_aggregation_window_exactness_to_dict(
    exactness: CacheRequestAggregationWindowExactness,
) -> dict[str, object]:
    """Serialize exact request-aggregation-window truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_request_aggregation_window_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "ingress",
                "dependencies",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "ingress": {
            "ingress_window_status": exactness.ingress_window_status,
            "admission_boundary_status": exactness.admission_boundary_status,
        },
        "dependencies": {
            "child_dependency_status": exactness.child_dependency_status,
            "stream_dependency_status": exactness.stream_dependency_status,
        },
    }
