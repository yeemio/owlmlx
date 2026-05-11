"""Runtime-owned exactness for the child-exchange aggregated-dispatch dependency."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_child_exchange_aggregated_dispatch_harness import (
    CacheChildExchangeAggregatedDispatchHarnessResult,
)
from .cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
    build_cache_request_aggregation_window_exactness,
)


@dataclass(frozen=True, slots=True)
class CacheChildExchangeAggregatedDispatchExactness:
    """Exact child-exchange truth after the pre-gate window is already visible."""

    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness
    status: str
    exactness_rung: str
    child_exchange_status: str
    exchange_shape: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_stream_dependency_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_child_exchange_aggregated_dispatch_exactness(
    *,
    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness | None = None,
    child_exchange_harness: CacheChildExchangeAggregatedDispatchHarnessResult | None = None,
) -> CacheChildExchangeAggregatedDispatchExactness:
    """Build exact child-exchange truth on the active request-aggregation path."""

    window_exactness = (
        request_aggregation_window_exactness
        if isinstance(
            request_aggregation_window_exactness,
            CacheRequestAggregationWindowExactness,
        )
        else build_cache_request_aggregation_window_exactness()
    )

    exactness_rung = "child_exchange_dependency_unresolved"
    child_exchange_status = "not_frozen"
    exchange_shape = "not_frozen"
    next_active_dependency = "child_exchange_not_yet_selected"
    next_active_dependency_status = "not_selected"
    preserved_stream_dependency_status = "not_frozen"
    residual_blocker = (
        "child-exchange aggregated-dispatch exactness is not yet frozen because request-aggregation window exactness is not strong enough"
    )
    recommended_next_step = (
        "freeze request-aggregation window exactness before reducing the next dependency to child exchange"
    )

    if window_exactness.exactness_rung == "aggregation_window_blocker_exact":
        exactness_rung = "child_exchange_dependency_exact"
        child_exchange_status = (
            "single_request_per_child_exchange_blocks_aggregated_dispatch"
        )
        exchange_shape = "single_request_per_exchange"
        next_active_dependency = "child_exchange_aggregated_dispatch_dependency"
        next_active_dependency_status = child_exchange_status
        preserved_stream_dependency_status = window_exactness.stream_dependency_status
        residual_blocker = (
            "child exchange remains the next active request-aggregation dependency on this path: ingress already forms bounded pre-gate cohorts before whole-request gate claim, but each child exchange still carries only one non-stream request while stream hold remains secondary"
        )
        recommended_next_step = (
            "widen child exchange narrowly on the active path without reopening ingress, stream rewrite, or continuous batching"
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
            child_exchange_status = "aggregated_non_stream_child_exchange_visible"
            exchange_shape = "single_child_exchange_carries_multiple_non_stream_requests"
            next_active_dependency = "cohort_to_child_exchange_handoff_dependency"
            next_active_dependency_status = (
                "pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange"
            )
            residual_blocker = (
                "child exchange is no longer limited to one request per exchange on this path: one non-stream child exchange can now carry multiple requests, but the bounded pre-gate cohort is not yet handed off into that aggregated child exchange on the main serving path while stream hold remains secondary"
            )
            recommended_next_step = (
                "freeze the cohort-to-child handoff dependency next; keep aggregated child dispatch non-stream only, preserve post-claim serial invariants, and do not widen this into stream rewrite or continuous batching"
            )

    return CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=window_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        child_exchange_status=child_exchange_status,
        exchange_shape=exchange_shape,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_stream_dependency_status=preserved_stream_dependency_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_child_exchange_aggregated_dispatch_exactness_to_dict(
    exactness: CacheChildExchangeAggregatedDispatchExactness,
) -> dict[str, object]:
    """Serialize child-exchange aggregated-dispatch exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_child_exchange_aggregated_dispatch_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "child_exchange",
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
        "child_exchange": {
            "child_exchange_status": exactness.child_exchange_status,
            "exchange_shape": exactness.exchange_shape,
        },
        "next_active_dependency": {
            "dependency": exactness.next_active_dependency,
            "status": exactness.next_active_dependency_status,
        },
        "preserved_secondary_stream": {
            "status": exactness.preserved_stream_dependency_status,
        },
    }
