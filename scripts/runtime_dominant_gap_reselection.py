#!/usr/bin/env python3
"""Emit the next dominant-gap reselection for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    build_cache_turboquant_preconditions_gap,
    build_dominant_gap_reselection,
    build_heavy_weight_runtime_repeatability_status,
    build_multi_model_governance_controls,
    build_multi_model_governance_policy_gap,
    build_multi_model_governance_transition_ledger,
    dominant_gap_reselection_to_dict,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)
from owlmlx.memory_budget import MachineMemoryProfile


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def _governance_policy_gap():
    state = {"now": 100.0}

    def clock() -> float:
        return float(state["now"])

    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0),
        profile=_profile(),
        clock=clock,
    )
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    kernel.load_model("model-c")
    kernel.pin_model("model-a")
    kernel.set_model_ttl("model-a", 30.0)
    kernel.set_model_ttl("model-b", 30.0)

    import asyncio

    asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    kernel.unload_model("model-c")
    state["now"] = 140.0
    kernel.sweep_expired_models()
    kernel.restart_model("model-a")
    runtime_status = kernel.status_dict()
    controls = build_multi_model_governance_controls(runtime_status)
    transition_ledger = build_multi_model_governance_transition_ledger(runtime_status)
    return build_multi_model_governance_policy_gap(
        controls=controls,
        transition_ledger=transition_ledger,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx dominant-gap reselection."
    )
    parser.add_argument("--specimen-path", required=True)
    parser.add_argument("--include-known-venvs", action="store_true")
    args = parser.parse_args()

    cache_harness = run_cache_runtime_observation_harness()
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
    turboquant_gap = build_cache_turboquant_preconditions_gap(
        readiness=cache_harness.turboquant
    )
    governance_gap = _governance_policy_gap()
    heavy_weight = build_heavy_weight_runtime_repeatability_status(
        specimen_path=args.specimen_path,
        include_known_candidates=args.include_known_venvs,
    )

    payload = dominant_gap_reselection_to_dict(
        build_dominant_gap_reselection(
            cache_scheduler_backlog=backlog,
            cache_turboquant_preconditions=turboquant_gap,
            governance_policy_gap=governance_gap,
            heavy_weight_repeatability=heavy_weight,
        )
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
