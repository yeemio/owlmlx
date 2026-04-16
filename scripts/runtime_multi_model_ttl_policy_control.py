#!/usr/bin/env python3
"""Emit runtime-owned TTL policy control truth for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_multi_model_ttl_policy_control,
    multi_model_ttl_policy_control_to_dict,
)
from owlmlx.memory_budget import MachineMemoryProfile


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def _run_harness() -> tuple[RuntimeKernel, dict[str, object]]:
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
    sweep = kernel.sweep_expired_models()
    evidence = {
        "sweep_unloaded_visible": "model-b" in sweep.unloaded_model_ids,
        "pinned_expiry_block_visible": "model-a" in sweep.skipped_pinned_model_ids,
    }
    return kernel, evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx multi-model TTL policy control truth."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    runtime_status: dict[str, object] = {}
    evidence: dict[str, object] = {}
    if args.run_harness:
        kernel, evidence = _run_harness()
        runtime_status = kernel.status_dict()

    payload = multi_model_ttl_policy_control_to_dict(
        build_multi_model_ttl_policy_control(runtime_status, harness_evidence=evidence)
    )
    if args.run_harness:
        payload["harness"] = evidence
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
