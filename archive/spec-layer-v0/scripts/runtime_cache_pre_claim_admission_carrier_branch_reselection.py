#!/usr/bin/env python3
"""Emit runtime-owned admission-carrier branch reselection truth."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    cache_pre_claim_admission_carrier_branch_reselection_to_dict,
    build_cache_pre_claim_admission_carrier_branch_reselection,
)
from owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness import (
    CachePreClaimAdmissionCarrierReclaimResetExactness,
)


def _build_harness_payload() -> dict[str, object]:
    carrier_reclaim_reset = CachePreClaimAdmissionCarrierReclaimResetExactness(
        locality_lifetime_coupling=object(),
        status="partial",
        exactness_rung="admission_carrier_reclaim_reset_exact",
        reclaim_reset_status="reclaim_resets_bounded_inert_carrier_to_fully_empty_state_before_reuse",
        reset_boundary_status="reuse_allowed_only_after_empty_reset_without_history_or_execution_state",
        allowed_reset_semantics=(
            "reclaim_clears_inert_carrier_presence_to_empty_state",
            "no_prior_request_history_visible_after_carrier_reclaim",
            "later_staged_request_may_reuse_only_after_empty_carrier_reset",
        ),
        forbidden_reset_expansions=(
            "no_reuse_with_stale_carrier_history",
            "no_partial_reset_leaving_scheduler_or_backend_hints",
            "no_cross_request_transfer_of_reclaim_reason",
            "no_execution_priority_or_queue_state_retained_after_carrier_reclaim",
        ),
        residual_blocker="the pre-claim admission-carrier reclaim-reset semantics are now exact",
        recommended_next_step="treat cache as admission-carrier branch reselection work on this path",
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
        **cache_pre_claim_admission_carrier_branch_reselection_to_dict(
            build_cache_pre_claim_admission_carrier_branch_reselection(
                reclaim_reset_exactness=carrier_reclaim_reset
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
        payload = cache_pre_claim_admission_carrier_branch_reselection_to_dict(
            build_cache_pre_claim_admission_carrier_branch_reselection()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
