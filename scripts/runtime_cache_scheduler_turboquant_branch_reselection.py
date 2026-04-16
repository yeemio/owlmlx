#!/usr/bin/env python3
"""Emit runtime-owned scheduler-vs-TurboQuant branch reselection truth."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_scheduler_turboquant_branch_reselection,
    cache_scheduler_turboquant_branch_reselection_to_dict,
)
from owlmlx.cache_pre_claim_admission_carrier_branch_reselection import (
    CachePreClaimAdmissionCarrierBranchReselection,
)
from owlmlx.cache_scheduler_branch_selection import CacheSchedulerBranchSelection
from owlmlx.cache_turboquant_preconditions_gap import CacheTurboQuantPreconditionsGap


def _build_harness_payload() -> dict[str, object]:
    carrier = CachePreClaimAdmissionCarrierBranchReselection(
        reclaim_reset_exactness=object(),
        status="partial",
        reselection_rung="carrier_branch_reselection_exact",
        carrier_branch_status="carrier_exactness_chain_complete_on_current_path",
        residual_carrier_subgap=None,
        next_cache_subbranch="scheduler_turboquant_branch_reselection",
        preserved_ingress_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
        ),
        residual_blocker="carrier exactness chain is complete",
        recommended_next_step="scheduler-vs-TurboQuant branch reselection",
    )
    scheduler = CacheSchedulerBranchSelection(
        scheduler_backlog=object(),
        status="partial",
        selection_rung="branch_selection_exact",
        selected_branch="continuous_batching",
        selected_branch_status="locally_reducible_on_current_path",
        secondary_branch="multi_worker_scheduler_depth",
        secondary_branch_status="safety_revalidation_required",
        residual_blocker="scheduler backlog remains open",
        recommended_next_step="continuous batching first",
    )
    turboquant = CacheTurboQuantPreconditionsGap(
        readiness=object(),
        status="partial",
        preconditions_rung="preconditions_exact",
        missing_preconditions=("bits_in_cache_key",),
        residual_blocker="TurboQuant exact-but-secondary",
        recommended_next_step="keep TurboQuant secondary",
    )
    return {
        "cache_harness": {
            "cache_counter_visibility": {
                "reuse": True,
                "residency": False,
                "eviction": False,
            },
            "reuse_counter": 1,
            "persistent_child_reuse_visible": True,
            "repeated_generation_models": ["cache-runtime-probe"],
            "total_generation_count": 2,
        },
        **cache_scheduler_turboquant_branch_reselection_to_dict(
            build_cache_scheduler_turboquant_branch_reselection(
                carrier_branch_reselection=carrier,
                scheduler_branch_selection=scheduler,
                turboquant_preconditions_gap=turboquant,
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        payload = _build_harness_payload()
    else:
        payload = cache_scheduler_turboquant_branch_reselection_to_dict(
            build_cache_scheduler_turboquant_branch_reselection()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
