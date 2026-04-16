#!/usr/bin/env python3
"""Emit runtime-owned multi-model pinning control truth for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_multi_model_pinning_control,
    multi_model_pinning_control_to_dict,
)
from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import RuntimeErrorCode


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def _run_pinning_harness() -> tuple[RuntimeKernel, dict[str, object]]:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    kernel.pin_model("model-a")
    unload = kernel.unload_model("model-a")
    restart = kernel.restart_model("model-a")
    evidence = {
        "unload_block_visible": (not unload.ok and unload.error_code is RuntimeErrorCode.model_pinned),
        "restart_retains_pin_visible": (
            restart.ok and "model-a" in kernel.status_dict().get("governance_policy", {}).get("pinned_model_ids", [])
        ),
    }
    return kernel, evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx multi-model pinning control truth."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    harness_evidence: dict[str, object] = {}
    if args.run_harness:
        kernel, harness_evidence = _run_pinning_harness()

    payload = multi_model_pinning_control_to_dict(
        build_multi_model_pinning_control(
            kernel.status_dict(),
            harness_evidence=harness_evidence,
        )
    )
    if args.run_harness:
        payload["harness"] = harness_evidence
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
