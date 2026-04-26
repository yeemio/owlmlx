"""Runtime-owned exactness for the cohort-to-child handoff dependency."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_child_exchange_aggregated_dispatch_exactness import (
    CacheChildExchangeAggregatedDispatchExactness,
    build_cache_child_exchange_aggregated_dispatch_exactness,
)
from .cache_cohort_to_child_exchange_handoff_harness import (
    CacheCohortToChildExchangeHandoffHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheCohortToChildExchangeHandoffExactness:
    """Exact handoff truth after child exchange itself is already widened."""

    child_exchange_exactness: CacheChildExchangeAggregatedDispatchExactness
    status: str
    exactness_rung: str
    handoff_status: str
    main_path_shape: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_stream_dependency_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_cohort_to_child_exchange_handoff_exactness(
    *,
    child_exchange_exactness: CacheChildExchangeAggregatedDispatchExactness | None = None,
    handoff_harness: CacheCohortToChildExchangeHandoffHarnessResult | None = None,
) -> CacheCohortToChildExchangeHandoffExactness:
    """Build exact main-path handoff truth for the active request-aggregation path."""

    child_exactness = (
        child_exchange_exactness
        if isinstance(
            child_exchange_exactness,
            CacheChildExchangeAggregatedDispatchExactness,
        )
        else build_cache_child_exchange_aggregated_dispatch_exactness()
    )

    exactness_rung = "cohort_to_child_handoff_unresolved"
    handoff_status = "not_frozen"
    main_path_shape = "not_frozen"
    next_active_dependency = "cohort_to_child_exchange_handoff_dependency"
    next_active_dependency_status = "not_selected"
    preserved_stream_dependency_status = "not_frozen"
    residual_blocker = (
        "cohort-to-child handoff exactness is not yet frozen because child-exchange exactness is not strong enough"
    )
    recommended_next_step = (
        "freeze child-exchange exactness before reducing the next dependency to main-path cohort handoff"
    )

    if child_exactness.exactness_rung == "child_exchange_dependency_exact":
        exactness_rung = "cohort_to_child_handoff_exact"
        handoff_status = (
            "pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange"
        )
        main_path_shape = "bounded_pre_gate_cohort_stops_before_main_path_child_handoff"
        next_active_dependency = "cohort_to_child_exchange_handoff_dependency"
        next_active_dependency_status = handoff_status
        preserved_stream_dependency_status = (
            child_exactness.preserved_stream_dependency_status
        )
        residual_blocker = (
            "the bounded pre-gate cohort still stops before the main serving path child exchange on this path: child exchange itself is widened for one non-stream aggregated dispatch, but the live runtime path still does not hand that cohort into one aggregated child exchange while stream hold remains secondary"
        )
        recommended_next_step = (
            "reduce the main-path cohort-to-child handoff dependency next without reopening child exchange capability, stream rewrite, or continuous batching"
        )

        if (
            handoff_harness is not None
            and handoff_harness.cohort_handoff_visible
            and handoff_harness.handoff_status
            == "cohort_handed_off_to_aggregated_child_exchange_visible"
            and handoff_harness.child_exchange_mode
            == "aggregated_non_stream_child_exchange_visible"
            and handoff_harness.aggregated_batch_count >= 1
            and handoff_harness.aggregated_request_count >= 2
            and handoff_harness.max_concurrent == 1
            and handoff_harness.queue_discipline == "serial"
            and handoff_harness.gate_total_served >= 2
            and handoff_harness.handoff_request_count >= 2
        ):
            handoff_status = "cohort_handed_off_to_aggregated_child_exchange_visible"
            main_path_shape = (
                "bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange"
            )
            next_active_dependency = "stream_session_holds_gate_until_completion"
            next_active_dependency_status = (
                "stream_session_holds_gate_until_completion"
            )
            residual_blocker = (
                "the non-stream main serving path now hands a bounded pre-gate cohort into one aggregated child exchange while preserving post-claim serial safety, so stream-session hold becomes the next active request-aggregation dependency"
            )
            recommended_next_step = (
                "freeze stream-session hold exact next without reopening non-stream cohort handoff, child exchange capability, or continuous batching"
            )

    return CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        handoff_status=handoff_status,
        main_path_shape=main_path_shape,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_stream_dependency_status=preserved_stream_dependency_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_cohort_to_child_exchange_handoff_exactness_to_dict(
    exactness: CacheCohortToChildExchangeHandoffExactness,
) -> dict[str, object]:
    """Serialize cohort-to-child handoff exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_cohort_to_child_exchange_handoff_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "handoff",
                "next_active_dependency",
                "preserved_secondary_stream",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "handoff": {
            "handoff_status": exactness.handoff_status,
            "main_path_shape": exactness.main_path_shape,
        },
        "next_active_dependency": {
            "dependency": exactness.next_active_dependency,
            "status": exactness.next_active_dependency_status,
        },
        "preserved_secondary_stream": {
            "status": exactness.preserved_stream_dependency_status,
        },
    }
