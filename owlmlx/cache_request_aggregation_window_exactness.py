"""Runtime-owned exactness for the request-aggregation-window subgap."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_child_exchange_aggregated_dispatch_harness import (
    CacheChildExchangeAggregatedDispatchHarnessResult,
)
from .cache_cohort_to_child_exchange_handoff_harness import (
    CacheCohortToChildExchangeHandoffHarnessResult,
)
from .cache_batching_mechanism_subgap import (
    CacheBatchingMechanismSubgap,
    build_cache_batching_mechanism_subgap,
)
from .cache_pre_gate_admission_hook_harness import PreGateAdmissionHookHarnessResult


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
    hook_harness: PreGateAdmissionHookHarnessResult | None = None,
    child_exchange_harness: CacheChildExchangeAggregatedDispatchHarnessResult | None = None,
    handoff_harness: CacheCohortToChildExchangeHandoffHarnessResult | None = None,
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
        if (
            hook_harness is not None
            and hook_harness.runtime_owned_hook_present
            and hook_harness.hook_boundary == "before_whole_request_gate_claim"
            and hook_harness.hook_mode == "bounded_runtime_owned_cohort_window"
            and hook_harness.observed_peak_cohort_size >= 2
            and hook_harness.observed_total_cohorts_formed >= 1
            and hook_harness.aggregation_scope == "pre_claim_window_only"
        ):
            ingress_window_status = "bounded_pre_gate_admission_window_present"
            admission_boundary_status = "cohort_forms_before_generation_gate_claim"
            residual_blocker = (
                "request aggregation has now cleared its ingress window on the active path: a bounded runtime-owned pre-gate admission window forms cohorts before whole-request gate claim, but child exchange still remains one-request-per-exchange and the stream path still holds the serial gate for a full session"
            )
            recommended_next_step = (
                "freeze request aggregation at its remaining downstream dependencies on this path; keep the new cohort window bounded to pre-claim aggregation only, preserve post-claim serial invariants, and do not inflate this into aggregated child dispatch, stream rewrite, or continuous batching"
            )
            if (
                child_exchange_harness is not None
                and child_exchange_harness.aggregated_dispatch_visible
                and child_exchange_harness.child_exchange_mode
                == "aggregated_non_stream_child_exchange_visible"
                and child_exchange_harness.exchange_count == 1
                and child_exchange_harness.batch_size >= 2
                and child_exchange_harness.aggregated_request_count >= 2
            ):
                child_dependency_status = "aggregated_non_stream_child_exchange_visible"
                residual_blocker = (
                    "request aggregation has now cleared both ingress and the single-request child protocol on the active path: a bounded pre-gate admission window forms cohorts before whole-request gate claim and one non-stream child exchange can carry multiple requests, but the bounded cohort is not yet handed off into that aggregated child exchange on the main serving path while stream hold remains secondary"
                )
                recommended_next_step = (
                    "freeze the cohort-to-child handoff dependency next; keep the visible child widening non-stream only, preserve post-claim serial invariants, and do not widen this into stream rewrite or continuous batching"
                )
                if (
                    handoff_harness is not None
                    and handoff_harness.cohort_handoff_visible
                    and handoff_harness.handoff_status
                    == "cohort_handed_off_to_aggregated_child_exchange_visible"
                    and handoff_harness.aggregated_batch_count >= 1
                    and handoff_harness.aggregated_request_count >= 2
                    and handoff_harness.handoff_request_count >= 2
                ):
                    child_dependency_status = (
                        "cohort_handed_off_to_aggregated_child_exchange_visible"
                    )
                    residual_blocker = (
                        "request aggregation has now cleared ingress, child exchange capability, and the non-stream main-path cohort handoff on the active path: a bounded pre-gate cohort now reaches one aggregated non-stream child exchange, but stream sessions still hold the serial gate for a full session"
                    )
                    recommended_next_step = (
                        "freeze the stream-session hold dependency next without reopening non-stream handoff, child exchange capability, or continuous batching"
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
