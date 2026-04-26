#!/usr/bin/env python3
"""Emit exact child-exchange aggregated-dispatch truth for owlmlx cache closure."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_batching_mechanism_subgap,
    build_cache_child_exchange_aggregated_dispatch_exactness,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_child_exchange_aggregated_dispatch_exactness_to_dict,
)
from owlmlx.cache_child_exchange_aggregated_dispatch_harness import (
    run_cache_child_exchange_aggregated_dispatch_harness,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    run_pre_gate_admission_hook_harness,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx child-exchange aggregated-dispatch exactness."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        cache_harness = run_cache_runtime_observation_harness()
        hook_harness = run_pre_gate_admission_hook_harness()
        child_exchange_harness = run_cache_child_exchange_aggregated_dispatch_harness()
        counter_gap = build_cache_counter_gap(
            closure=cache_harness.closure,
            backend_observations=cache_harness.backend_observations,
        )
        counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
        split = build_cache_scheduler_turboquant_split(
            counter_feasibility=counter_feasibility,
            scheduler=cache_harness.closure.scheduler,
            turboquant=cache_harness.turboquant,
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
        window_exactness = build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap,
            hook_harness=hook_harness,
            child_exchange_harness=child_exchange_harness,
        )
        payload = cache_child_exchange_aggregated_dispatch_exactness_to_dict(
            build_cache_child_exchange_aggregated_dispatch_exactness(
                request_aggregation_window_exactness=window_exactness,
                child_exchange_harness=child_exchange_harness,
            )
        )
        payload["cache_harness"] = cache_harness.backend_observations
        payload["pre_gate_hook_harness"] = {
            "runtime_owned_hook_present": hook_harness.runtime_owned_hook_present,
            "hook_boundary": hook_harness.hook_boundary,
            "hook_mode": hook_harness.hook_mode,
            "cohort_window_status": hook_harness.cohort_window_status,
            "observed_peak_cohort_size": hook_harness.observed_peak_cohort_size,
            "observed_total_cohorts_formed": hook_harness.observed_total_cohorts_formed,
            "aggregation_scope": hook_harness.aggregation_scope,
        }
        payload["child_exchange_harness"] = {
            "aggregated_dispatch_visible": child_exchange_harness.aggregated_dispatch_visible,
            "child_exchange_mode": child_exchange_harness.child_exchange_mode,
            "exchange_count": child_exchange_harness.exchange_count,
            "batch_size": child_exchange_harness.batch_size,
            "aggregated_request_count": child_exchange_harness.aggregated_request_count,
            "max_aggregated_batch_size": child_exchange_harness.max_aggregated_batch_size,
            "stream_secondary_status": child_exchange_harness.stream_secondary_status,
            "texts": list(child_exchange_harness.texts),
        }
    else:
        payload = cache_child_exchange_aggregated_dispatch_exactness_to_dict(
            build_cache_child_exchange_aggregated_dispatch_exactness()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
