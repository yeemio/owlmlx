#!/usr/bin/env python3
"""Emit runtime-owned request-aggregation-window reentry truth."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_request_aggregation_window_reentry,
    cache_request_aggregation_window_reentry_to_dict,
)
from owlmlx.cache_continuous_batching_branch_reduction import (
    CacheContinuousBatchingBranchReduction,
)
from owlmlx.cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
)


def _build_harness_payload() -> dict[str, object]:
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
    return cache_request_aggregation_window_reentry_to_dict(
        build_cache_request_aggregation_window_reentry(
            continuous_batching_branch_reduction=branch_reduction,
            request_aggregation_window_exactness=aggregation_exactness,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        payload = _build_harness_payload()
    else:
        payload = cache_request_aggregation_window_reentry_to_dict(
            build_cache_request_aggregation_window_reentry()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
