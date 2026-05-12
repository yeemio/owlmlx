#!/usr/bin/env python3
"""Emit runtime-owned TurboQuant readiness for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_residency_evidence,
    build_cache_repeatability_evidence,
    build_turboquant_readiness,
    turboquant_readiness_to_dict,
)
from owlmlx.serving import GenerationGate


def _build_repeatability(status: str) -> object:
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

    if status == "no_repeat_runs":
        return build_cache_repeatability_evidence([])

    gate = GenerationGate()
    gate.execute(lambda: None)
    gate.execute(lambda: None)

    if status == "repeat_profile_active_under_load":
        runs = [
            build_cache_residency_evidence(
                gate=gate,
                configured_flags={"hot_cache_max_size": "8GB"},
                runtime_profile="cache-enabled",
                runtime_flags={"hot_cache_max_size": "8GB"},
            ),
            build_cache_residency_evidence(
                gate=gate,
                configured_flags={"hot_cache_max_size": "8GB"},
                runtime_profile="cache-enabled",
                runtime_flags={"hot_cache_max_size": "8GB"},
            ),
        ]
        return build_cache_repeatability_evidence(runs)

    if status == "repeat_residency_visible":
        runs = [
            build_cache_residency_evidence(
                gate=gate,
                runtime_profile="cache-enabled",
                metrics={"entries": 2, "resident_bytes": 1024},
            ),
            build_cache_residency_evidence(
                gate=gate,
                runtime_profile="cache-enabled",
                metrics={"entries": 3, "resident_bytes": 2048},
            ),
        ]
        return build_cache_repeatability_evidence(runs)

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
            metrics={"reuse_events": 2, "hit_count": 4, "eviction_events": 1},
        ),
        build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"reuse_events": 3, "hit_count": 6},
        ),
    ]
    return build_cache_repeatability_evidence(runs)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the current owlmlx TurboQuant readiness decision."
    )
    parser.add_argument("--bits-in-cache-key", action="store_true")
    parser.add_argument("--invalidates-on-config-toggle", action="store_true")
    parser.add_argument("--runtime-verified", action="store_true")
    parser.add_argument(
        "--repeatability-status",
        choices=(
            "no_repeat_runs",
            "runtime_activity_visible_counter_gap",
            "repeat_profile_active_under_load",
            "repeat_residency_visible",
            "repeat_reuse_visible",
            "repeat_eviction_visible",
        ),
        default="no_repeat_runs",
    )
    args = parser.parse_args()

    repeatability = _build_repeatability(args.repeatability_status)

    readiness = build_turboquant_readiness(
        bits_in_cache_key=args.bits_in_cache_key,
        invalidates_on_config_toggle=args.invalidates_on_config_toggle,
        runtime_verified=args.runtime_verified,
        repeatability=repeatability,
    )
    print(json.dumps(turboquant_readiness_to_dict(readiness), indent=2, sort_keys=True))
    return 0 if readiness.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
