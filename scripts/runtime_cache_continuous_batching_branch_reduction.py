#!/usr/bin/env python3
"""Emit runtime-owned continuous-batching branch reduction truth."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_continuous_batching_branch_reduction,
    cache_continuous_batching_branch_reduction_to_dict,
)
from owlmlx.cache_batching_mechanism_subgap import CacheBatchingMechanismSubgap
from owlmlx.cache_continuous_batching_feasibility import CacheContinuousBatchingFeasibility
from owlmlx.cache_scheduler_turboquant_branch_reselection import (
    CacheSchedulerTurboQuantBranchReselection,
)


def _build_harness_payload() -> dict[str, object]:
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
    return cache_continuous_batching_branch_reduction_to_dict(
        build_cache_continuous_batching_branch_reduction(
            scheduler_turboquant_branch_reselection=branch_reselection,
            batching_mechanism_subgap=mechanism_subgap,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        payload = _build_harness_payload()
    else:
        payload = cache_continuous_batching_branch_reduction_to_dict(
            build_cache_continuous_batching_branch_reduction()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
