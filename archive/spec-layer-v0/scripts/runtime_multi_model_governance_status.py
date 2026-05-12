#!/usr/bin/env python3
"""Emit runtime-owned multi-model governance status for owlmlx."""

from __future__ import annotations

import argparse
import asyncio
import json

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_multi_model_governance_status,
    multi_model_governance_status_to_dict,
)
from owlmlx.memory_budget import MachineMemoryProfile


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx multi-model governance status."
    )
    parser.add_argument("--load-model", action="append", help="Model id to load in order.")
    parser.add_argument(
        "--run-harness",
        action="store_true",
        help="Run a repeated multi-model harness before emitting governance status.",
    )
    args = parser.parse_args()

    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    for model_id in args.load_model or []:
        kernel.load_model(model_id)

    harness = None
    if args.run_harness:
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
        active_generation = asyncio.run(kernel.generate("hello-active"))
        explicit_generation = asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
        restart = kernel.restart_model("model-b")
        unload = kernel.unload_model("model-c")
        state["now"] = 140.0
        ttl_sweep = kernel.sweep_expired_models()
        harness = {
            "active_generation_model_id": active_generation.model_id,
            "explicit_generation_model_id": explicit_generation.model_id,
            "restart_stage": restart.stage,
            "unload_ok": unload.ok,
            "ttl_unloaded_model_ids": list(ttl_sweep.unloaded_model_ids),
            "ttl_skipped_pinned_model_ids": list(ttl_sweep.skipped_pinned_model_ids),
        }

    payload = multi_model_governance_status_to_dict(
        build_multi_model_governance_status(kernel.status_dict())
    )
    if harness is not None:
        payload["harness"] = harness
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
