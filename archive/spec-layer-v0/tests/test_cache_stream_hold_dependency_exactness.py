from __future__ import annotations

from pathlib import Path

from owlmlx.cache_child_exchange_aggregated_dispatch_exactness import (
    CacheChildExchangeAggregatedDispatchExactness,
)
from owlmlx.cache_cohort_to_child_exchange_handoff_exactness import (
    CacheCohortToChildExchangeHandoffExactness,
)
from owlmlx.cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
)
from owlmlx.cache_stream_hold_dependency_exactness import (
    build_cache_stream_hold_dependency_exactness,
    cache_stream_hold_dependency_exactness_to_dict,
)
from owlmlx.cache_stream_hold_dependency_harness import (
    CacheStreamHoldDependencyHarnessResult,
)


def test_cache_stream_hold_dependency_exactness_defaults_unresolved() -> None:
    payload = cache_stream_hold_dependency_exactness_to_dict(
        build_cache_stream_hold_dependency_exactness()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_stream_hold_dependency_exactness"
    assert payload["summary"]["exactness_rung"] == "stream_hold_dependency_unresolved"


def test_cache_stream_hold_dependency_exactness_narrows_after_visible_release_boundary() -> None:
    window_exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=window_exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_harness = CacheStreamHoldDependencyHarnessResult(
        hold_dependency_narrowed=True,
        hold_verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        second_stream_started_before_first_consumer_completed=True,
        max_concurrent=1,
        queue_policy="ticketed_fifo",
        gate_total_served=2,
        gate_total_queued=2,
        preserved_post_claim_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ),
        first_stream_events=("token", "done"),
        second_stream_events=("token", "done"),
    )

    payload = cache_stream_hold_dependency_exactness_to_dict(
        build_cache_stream_hold_dependency_exactness(
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_harness=stream_hold_harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "stream_hold_dependency_exact"
    assert payload["summary"]["verdict"] == "stream_hold_dependency_narrowed"
    assert (
        payload["stream_hold"]["hold_status"]
        == "stream_gate_release_decoupled_from_consumer_completion_visible"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "stream_backend_iterator_completion_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "stream_backend_iterator_holds_gate_until_completion"
    )


def test_cache_stream_hold_dependency_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_stream_hold_dependency_exactness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
