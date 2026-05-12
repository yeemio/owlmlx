#!/usr/bin/env python3
"""Emit runtime-owned eviction-history governance truth for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_multi_model_eviction_history_governance,
    multi_model_eviction_history_governance_to_dict,
)
from owlmlx.memory_budget import MachineMemoryProfile


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def _run_harness() -> RuntimeKernel:
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
    kernel.pin_model("model-a")
    kernel.set_model_ttl("model-a", 30.0)
    kernel.set_model_ttl("model-b", 30.0)
    state["now"] = 140.0
    kernel.sweep_expired_models()
    return kernel


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx multi-model eviction-history governance truth."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    runtime_status: dict[str, object] = {}
    if args.run_harness:
        runtime_status = _run_harness().status_dict()

    payload = multi_model_eviction_history_governance_to_dict(
        build_multi_model_eviction_history_governance(runtime_status)
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
