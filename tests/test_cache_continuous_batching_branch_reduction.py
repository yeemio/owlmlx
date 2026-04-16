from __future__ import annotations

from pathlib import Path

from owlmlx import build_cache_continuous_batching_branch_reduction
from owlmlx.cache_batching_mechanism_subgap import CacheBatchingMechanismSubgap
from owlmlx.cache_continuous_batching_branch_reduction import (
    cache_continuous_batching_branch_reduction_to_dict,
)
from owlmlx.cache_continuous_batching_feasibility import CacheContinuousBatchingFeasibility
from owlmlx.cache_scheduler_turboquant_branch_reselection import (
    CacheSchedulerTurboQuantBranchReselection,
)


def test_cache_continuous_batching_branch_reduction_defaults_unresolved() -> None:
    payload = cache_continuous_batching_branch_reduction_to_dict(
        build_cache_continuous_batching_branch_reduction()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_continuous_batching_branch_reduction"
    )


def test_cache_continuous_batching_branch_reduction_freezes_exact() -> None:
    branch_reselection = CacheSchedulerTurboQuantBranchReselection(
        carrier_branch_reselection=object(),
        scheduler_branch_selection=object(),
        turboquant_preconditions_gap=object(),
        status="partial",
        reselection_rung="scheduler_turboquant_branch_exact",
        selected_branch="scheduler_depth",
        selected_branch_status="continuous_batching",
        secondary_branch="turboquant_preconditions",
        secondary_branch_status="preconditions_exact",
        residual_blocker="scheduler depth stays primary on this path",
        recommended_next_step="continuous batching branch reduction",
    )
    feasibility = CacheContinuousBatchingFeasibility(
        branch_selection=object(),
        status="partial",
        feasibility_rung="feasibility_blocker_exact",
        generation_gate_mode="serial_ticketed_fifo_whole_request",
        child_exchange_mode="single_request_per_child_exchange",
        stream_holds_full_session=True,
        missing_batching_mechanisms=(
            "request_aggregation_window",
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        residual_blocker="continuous batching remains structurally blocked",
        recommended_next_step="request aggregation first",
    )
    mechanism_subgap = CacheBatchingMechanismSubgap(
        feasibility=feasibility,
        status="partial",
        subgap_rung="mechanism_subgap_exact",
        selected_mechanism="request_aggregation_window",
        selected_mechanism_status="locally_reducible_first_blocker",
        request_aggregation_window_status="locally_reducible_first_blocker",
        shared_prefill_batch_step_status="blocked_by_missing_request_aggregation_window",
        interleaved_decode_scheduler_status="blocked_by_missing_request_aggregation_window_and_full_session_stream_hold",
        residual_blocker="request aggregation stays first",
        recommended_next_step="re-enter request aggregation",
    )

    payload = cache_continuous_batching_branch_reduction_to_dict(
        build_cache_continuous_batching_branch_reduction(
            scheduler_turboquant_branch_reselection=branch_reselection,
            batching_mechanism_subgap=mechanism_subgap,
        )
    )

    assert payload["summary"]["reduction_rung"] == "continuous_batching_branch_exact"
    assert payload["selected_scheduler_branch"]["branch"] == "continuous_batching"
    assert payload["selected_reduction_target"]["target"] == "request_aggregation_window"
    assert payload["secondary_runtime_branch"]["status"] == "preconditions_exact"


def test_cache_continuous_batching_branch_reduction_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_continuous_batching_branch_reduction.py"
    ).read_text()
    forbidden = ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]
    for pattern in forbidden:
        assert pattern not in source
