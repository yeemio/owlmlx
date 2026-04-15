#!/usr/bin/env python3
"""Emit exact pre-gate cohort window feasibility for owlmlx cache closure."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_batching_mechanism_subgap,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_pre_gate_cohort_window_feasibility,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_pre_gate_cohort_window_feasibility_to_dict,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx pre-gate cohort window feasibility."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        harness = run_cache_runtime_observation_harness()
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
            mechanism_subgap=mechanism_subgap
        )
        payload = cache_pre_gate_cohort_window_feasibility_to_dict(
            build_cache_pre_gate_cohort_window_feasibility(
                aggregation_exactness=aggregation_exactness
            )
        )
        payload["cache_harness"] = harness.backend_observations
    else:
        payload = cache_pre_gate_cohort_window_feasibility_to_dict(
            build_cache_pre_gate_cohort_window_feasibility()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
