#!/usr/bin/env python3
"""Emit runtime-owned pre-gate admission-window seam truth."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_batching_mechanism_subgap,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_pre_gate_admission_hook_exactness,
    build_cache_pre_gate_admission_window_seam,
    build_cache_pre_gate_cohort_window_feasibility,
    build_cache_request_aggregation_active_seam,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_pre_gate_admission_window_seam_to_dict,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    run_pre_gate_admission_hook_harness,
)
from owlmlx.cache_request_aggregation_window_reentry import (
    CacheRequestAggregationWindowReentry,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()
    if args.run_harness:
        harness = run_cache_runtime_observation_harness()
        hook_harness = run_pre_gate_admission_hook_harness()
        counter_gap = build_cache_counter_gap(
            closure=harness.closure,
            backend_observations=harness.backend_observations,
        )
        counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
        split = build_cache_scheduler_turboquant_split(
            counter_feasibility=counter_feasibility,
            scheduler=harness.closure.scheduler,
            turboquant=harness.turboquant,
        )
        floor_gap = build_cache_scheduler_floor_gap(split=split)
        backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
        branch_selection = build_cache_scheduler_branch_selection(
            scheduler_backlog=backlog
        )
        feasibility = build_cache_continuous_batching_feasibility(
            branch_selection=branch_selection
        )
        mechanism_subgap = build_cache_batching_mechanism_subgap(
            feasibility=feasibility
        )
        aggregation_exactness = build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap,
            hook_harness=hook_harness,
        )
        cohort_window = build_cache_pre_gate_cohort_window_feasibility(
            aggregation_exactness=aggregation_exactness,
            hook_harness=hook_harness,
        )
        hook_exactness = build_cache_pre_gate_admission_hook_exactness(
            cohort_window_feasibility=cohort_window,
            hook_harness=hook_harness,
        )
        reentry = CacheRequestAggregationWindowReentry(
            continuous_batching_branch_reduction=object(),
            request_aggregation_window_exactness=aggregation_exactness,
            status="partial",
            reentry_rung="aggregation_reentry_exact",
            selected_reentry_target="request_aggregation_window",
            selected_reentry_target_status="reentered_as_active_cache_subchain",
            preserved_secondary_scheduler_reduction=(
                "shared_prefill_batch_step",
                "interleaved_decode_scheduler",
            ),
            preserved_secondary_runtime_branch="turboquant_preconditions",
            preserved_secondary_runtime_branch_status="preconditions_exact",
            residual_blocker="request aggregation reentered",
            recommended_next_step="active seam",
        )
        active_seam = build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=aggregation_exactness,
        )
        payload = cache_pre_gate_admission_window_seam_to_dict(
            build_cache_pre_gate_admission_window_seam(
                request_aggregation_active_seam=active_seam,
                pre_gate_admission_hook_exactness=hook_exactness,
            )
        )
        payload["cache_harness"] = harness.backend_observations
        payload["pre_gate_hook_harness"] = {
            "runtime_owned_hook_present": hook_harness.runtime_owned_hook_present,
            "hook_boundary": hook_harness.hook_boundary,
            "hook_mode": hook_harness.hook_mode,
            "cohort_window_status": hook_harness.cohort_window_status,
            "observed_peak_cohort_size": hook_harness.observed_peak_cohort_size,
            "observed_total_cohorts_formed": hook_harness.observed_total_cohorts_formed,
            "aggregation_scope": hook_harness.aggregation_scope,
        }
    else:
        payload = cache_pre_gate_admission_window_seam_to_dict(
            build_cache_pre_gate_admission_window_seam()
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
