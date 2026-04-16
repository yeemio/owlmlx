#!/usr/bin/env python3
"""Emit runtime-owned pre-gate admission-window seam truth."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_pre_gate_admission_window_seam,
    cache_pre_gate_admission_window_seam_to_dict,
)
from owlmlx.cache_pre_gate_admission_hook_exactness import CachePreGateAdmissionHookExactness
from owlmlx.cache_request_aggregation_active_seam import CacheRequestAggregationActiveSeam


def _build_harness_payload() -> dict[str, object]:
    active_seam = CacheRequestAggregationActiveSeam(
        request_aggregation_window_reentry=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        seam_rung="aggregation_active_seam_exact",
        selected_seam="pre_gate_admission_window",
        selected_seam_status="missing_pre_gate_admission_window",
        preserved_secondary_dependencies=(
            "single_request_per_child_exchange_blocks_aggregated_dispatch",
            "stream_session_holds_gate_until_completion",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="pre-gate window stays active",
        recommended_next_step="bounded hook",
    )
    hook_exactness = CachePreGateAdmissionHookExactness(
        cohort_window_feasibility=object(),
        status="partial",
        exactness_rung="admission_hook_blocker_exact",
        admission_hook_status="no_bounded_hook_before_gate_claim",
        owned_boundary_status="whole_request_gate_claim_is_first_runtime_owned_boundary",
        preserved_safety_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ),
        residual_blocker="bounded hook still missing",
        recommended_next_step="bounded hook",
    )
    return cache_pre_gate_admission_window_seam_to_dict(
        build_cache_pre_gate_admission_window_seam(
            request_aggregation_active_seam=active_seam,
            pre_gate_admission_hook_exactness=hook_exactness,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()
    if args.run_harness:
        payload = _build_harness_payload()
    else:
        payload = cache_pre_gate_admission_window_seam_to_dict(
            build_cache_pre_gate_admission_window_seam()
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
