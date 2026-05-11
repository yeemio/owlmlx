from __future__ import annotations

from pathlib import Path

from owlmlx.cache_child_exchange_aggregated_dispatch_exactness import (
    CacheChildExchangeAggregatedDispatchExactness,
)
from owlmlx.cache_cohort_to_child_exchange_handoff_exactness import (
    build_cache_cohort_to_child_exchange_handoff_exactness,
    cache_cohort_to_child_exchange_handoff_exactness_to_dict,
)
from owlmlx.cache_cohort_to_child_exchange_handoff_harness import (
    CacheCohortToChildExchangeHandoffHarnessResult,
)
from owlmlx.cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
)


def test_cache_cohort_to_child_exchange_handoff_exactness_defaults_unresolved() -> None:
    payload = cache_cohort_to_child_exchange_handoff_exactness_to_dict(
        build_cache_cohort_to_child_exchange_handoff_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_cohort_to_child_exchange_handoff_exactness"
    )
    assert payload["summary"]["exactness_rung"] == "cohort_to_child_handoff_unresolved"


def test_cache_cohort_to_child_exchange_handoff_exactness_freezes_missing_handoff() -> None:
    window_exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="aggregated_non_stream_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
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

    payload = cache_cohort_to_child_exchange_handoff_exactness_to_dict(
        build_cache_cohort_to_child_exchange_handoff_exactness(
            child_exchange_exactness=child_exactness
        )
    )

    assert payload["summary"]["exactness_rung"] == "cohort_to_child_handoff_exact"
    assert (
        payload["handoff"]["handoff_status"]
        == "pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "cohort_to_child_exchange_handoff_dependency"
    )


def test_cache_cohort_to_child_exchange_handoff_exactness_advances_after_visible_handoff() -> None:
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
    handoff_harness = CacheCohortToChildExchangeHandoffHarnessResult(
        cohort_handoff_visible=True,
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        child_exchange_mode="aggregated_non_stream_child_exchange_visible",
        aggregated_batch_count=1,
        aggregated_request_count=2,
        max_aggregated_batch_size=2,
        gate_total_served=2,
        gate_total_queued=2,
        max_concurrent=1,
        queue_discipline="serial",
        handoff_request_count=2,
        stream_secondary_status="stream_session_holds_gate_until_completion",
        texts=("a :: child", "b :: child"),
    )

    payload = cache_cohort_to_child_exchange_handoff_exactness_to_dict(
        build_cache_cohort_to_child_exchange_handoff_exactness(
            child_exchange_exactness=child_exactness,
            handoff_harness=handoff_harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "cohort_to_child_handoff_exact"
    assert (
        payload["handoff"]["handoff_status"]
        == "cohort_handed_off_to_aggregated_child_exchange_visible"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "stream_session_holds_gate_until_completion"
    )
    assert (
        payload["preserved_secondary_stream"]["status"]
        == "stream_session_holds_gate_until_completion"
    )


def test_cache_cohort_to_child_exchange_handoff_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_cohort_to_child_exchange_handoff_exactness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
