from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_child_exchange_aggregated_dispatch_exactness,
    cache_child_exchange_aggregated_dispatch_exactness_to_dict,
)
from owlmlx.cache_child_exchange_aggregated_dispatch_harness import (
    CacheChildExchangeAggregatedDispatchHarnessResult,
)
from owlmlx.cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
)


def test_cache_child_exchange_aggregated_dispatch_exactness_defaults_to_unresolved() -> None:
    payload = cache_child_exchange_aggregated_dispatch_exactness_to_dict(
        build_cache_child_exchange_aggregated_dispatch_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_child_exchange_aggregated_dispatch_exactness"
    )
    assert payload["summary"]["exactness_rung"] == "child_exchange_dependency_unresolved"


def test_cache_child_exchange_aggregated_dispatch_exactness_freezes_single_request_blocker() -> None:
    window_exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="child exchange still blocks",
        recommended_next_step="freeze child exchange",
    )

    payload = cache_child_exchange_aggregated_dispatch_exactness_to_dict(
        build_cache_child_exchange_aggregated_dispatch_exactness(
            request_aggregation_window_exactness=window_exactness
        )
    )

    assert payload["summary"]["exactness_rung"] == "child_exchange_dependency_exact"
    assert (
        payload["child_exchange"]["child_exchange_status"]
        == "single_request_per_child_exchange_blocks_aggregated_dispatch"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "child_exchange_aggregated_dispatch_dependency"
    )


def test_cache_child_exchange_aggregated_dispatch_exactness_advances_after_visible_batch_exchange() -> None:
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
    harness = CacheChildExchangeAggregatedDispatchHarnessResult(
        aggregated_dispatch_visible=True,
        child_exchange_mode="aggregated_non_stream_child_exchange_visible",
        exchange_count=1,
        batch_size=2,
        aggregated_request_count=2,
        max_aggregated_batch_size=2,
        pid=123,
        stream_secondary_status="stream_session_holds_gate_until_completion",
        texts=("child-a :: child", "child-b :: child"),
    )

    payload = cache_child_exchange_aggregated_dispatch_exactness_to_dict(
        build_cache_child_exchange_aggregated_dispatch_exactness(
            request_aggregation_window_exactness=window_exactness,
            child_exchange_harness=harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "child_exchange_dependency_exact"
    assert (
        payload["child_exchange"]["child_exchange_status"]
        == "aggregated_non_stream_child_exchange_visible"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "cohort_to_child_exchange_handoff_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange"
    )
    assert (
        payload["preserved_secondary_stream"]["status"]
        == "stream_session_holds_gate_until_completion"
    )


def test_cache_child_exchange_aggregated_dispatch_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_child_exchange_aggregated_dispatch_exactness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
