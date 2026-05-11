from __future__ import annotations

from pathlib import Path

from owlmlx import build_cache_request_aggregation_window_reentry
from owlmlx.cache_continuous_batching_branch_reduction import (
    CacheContinuousBatchingBranchReduction,
)
from owlmlx.cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
)
from owlmlx.cache_request_aggregation_window_reentry import (
    cache_request_aggregation_window_reentry_to_dict,
)


def test_cache_request_aggregation_window_reentry_defaults_unresolved() -> None:
    payload = cache_request_aggregation_window_reentry_to_dict(
        build_cache_request_aggregation_window_reentry()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_request_aggregation_window_reentry"


def test_cache_request_aggregation_window_reentry_freezes_exact() -> None:
    branch_reduction = CacheContinuousBatchingBranchReduction(
        scheduler_turboquant_branch_reselection=object(),
        batching_mechanism_subgap=object(),
        status="partial",
        reduction_rung="continuous_batching_branch_exact",
        selected_scheduler_branch="continuous_batching",
        selected_scheduler_branch_status="selected_on_current_path",
        selected_reduction_target="request_aggregation_window",
        selected_reduction_target_status="locally_reducible_first_blocker",
        secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        secondary_scheduler_reduction_statuses=(
            "blocked_by_missing_request_aggregation_window",
            "blocked_by_missing_request_aggregation_window_and_full_session_stream_hold",
        ),
        turboquant_branch_status="preconditions_exact",
        residual_blocker="request aggregation stays next",
        recommended_next_step="re-enter request aggregation",
    )
    aggregation_exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="missing_pre_gate_admission_window",
        admission_boundary_status="generation_gate_claims_session_before_cohort_formation",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="request aggregation still blocked",
        recommended_next_step="pre-gate cohort window feasibility",
    )

    payload = cache_request_aggregation_window_reentry_to_dict(
        build_cache_request_aggregation_window_reentry(
            continuous_batching_branch_reduction=branch_reduction,
            request_aggregation_window_exactness=aggregation_exactness,
        )
    )

    assert payload["summary"]["reentry_rung"] == "aggregation_reentry_exact"
    assert payload["selected_reentry_target"]["target"] == "request_aggregation_window"
    assert payload["preserved_secondary_runtime_branch"]["status"] == "preconditions_exact"


def test_cache_request_aggregation_window_reentry_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_request_aggregation_window_reentry.py"
    ).read_text()
    forbidden = ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]
    for pattern in forbidden:
        assert pattern not in source
