#!/usr/bin/env python3
"""Emit runtime-owned multi-model governance transition ledger for owlmlx."""

from __future__ import annotations

import argparse
import asyncio
import json

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_multi_model_governance_transition_ledger,
    multi_model_governance_transition_ledger_to_dict,
)
from owlmlx.memory_budget import MachineMemoryProfile


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def _run_transition_harness() -> RuntimeKernel:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())

    kernel.load_model("model-a")
    kernel.load_model("model-b")

    asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    kernel.unload_model("model-b")
    kernel.restart_model("model-a")
    return kernel


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx multi-model governance transition ledger."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    if args.run_harness:
        kernel = _run_transition_harness()

    runtime_status = kernel.status_dict()

    payload = multi_model_governance_transition_ledger_to_dict(
        build_multi_model_governance_transition_ledger(
            runtime_status,
        )
    )
    if args.run_harness:
        payload["harness"] = runtime_status.get("governance_observations")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
