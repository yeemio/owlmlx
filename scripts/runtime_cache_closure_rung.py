#!/usr/bin/env python3
"""Emit runtime-owned cache closure rung for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_closure_rung,
    build_cache_repeatability_evidence,
    build_cache_residency_evidence,
    build_turboquant_readiness,
    cache_closure_rung_to_dict,
)
from owlmlx.serving import GenerationGate
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def _residency(status: str):
    gate = GenerationGate()
    gate.execute(lambda: None)
    if status == "no_runtime_evidence":
        return build_cache_residency_evidence()
    if status == "profile_active_under_load":
        return build_cache_residency_evidence(
            gate=gate,
            configured_flags={"hot_cache_max_size": "8GB"},
            runtime_profile="cache-enabled",
            runtime_flags={"hot_cache_max_size": "8GB"},
        )
    if status == "residency_signal_visible":
        return build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"entries": 2, "resident_bytes": 1024},
        )
    return build_cache_residency_evidence(
        gate=gate,
        runtime_profile="cache-enabled",
        metrics={"reuse_events": 2, "hit_count": 4},
    )


def _repeatability(status: str):
    gate = GenerationGate()
    gate.execute(lambda: None)
    gate.execute(lambda: None)
    if status == "no_repeat_runs":
        return build_cache_repeatability_evidence([])
    if status == "runtime_activity_visible_counter_gap":
        return build_cache_repeatability_evidence(
            [],
            backend_status={
                "detail": {
                    "cache_runtime_observations": {
                        "persistent_child_reuse_visible": True,
                        "repeated_generation_models": ["model-a"],
                    }
                }
            },
        )
    if status == "repeat_reuse_visible":
        runs = [
            build_cache_residency_evidence(
                gate=gate,
                runtime_profile="cache-enabled",
                metrics={"reuse_events": 2, "hit_count": 4},
            ),
            build_cache_residency_evidence(
                gate=gate,
                runtime_profile="cache-enabled",
                metrics={"reuse_events": 3, "hit_count": 6},
            ),
        ]
        return build_cache_repeatability_evidence(runs)
    runs = [
        build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"entries": 2},
        ),
        build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"entries": 3},
        ),
    ]
    return build_cache_repeatability_evidence(runs)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit owlmlx cache closure rung.")
    parser.add_argument(
        "--residency-status",
        choices=(
            "no_runtime_evidence",
            "profile_active_under_load",
            "residency_signal_visible",
            "reuse_signal_visible",
        ),
        default="no_runtime_evidence",
    )
    parser.add_argument(
        "--repeatability-status",
        choices=(
            "no_repeat_runs",
            "runtime_activity_visible_counter_gap",
            "repeat_residency_visible",
            "repeat_reuse_visible",
        ),
        default="no_repeat_runs",
    )
    parser.add_argument("--bits-in-cache-key", action="store_true")
    parser.add_argument("--invalidates-on-config-toggle", action="store_true")
    parser.add_argument("--runtime-verified", action="store_true")
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        harness = run_cache_runtime_observation_harness()
        rung = build_cache_closure_rung(
            repeatability=harness.repeatability,
            turboquant=harness.turboquant,
        )
        payload = cache_closure_rung_to_dict(rung)
        payload["cache_harness"] = harness.backend_observations
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    residency = _residency(args.residency_status)
    repeatability = _repeatability(args.repeatability_status)
    turboquant = build_turboquant_readiness(
        bits_in_cache_key=args.bits_in_cache_key,
        invalidates_on_config_toggle=args.invalidates_on_config_toggle,
        runtime_verified=args.runtime_verified,
        repeatability=repeatability,
    )
    rung = build_cache_closure_rung(
        residency=residency,
        repeatability=repeatability,
        turboquant=turboquant,
    )
    print(json.dumps(cache_closure_rung_to_dict(rung), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
