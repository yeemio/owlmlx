#!/usr/bin/env python3
"""Emit runtime-owned repeated-serving cache evidence for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_repeatability_evidence,
    build_cache_residency_evidence,
    cache_repeatability_evidence_to_dict,
)
from owlmlx.serving import GenerationGate


def _build_run(status: str, served: int) -> object:
    gate = GenerationGate()
    for _ in range(max(served, 0)):
        gate.execute(lambda: None)

    if status == "configuration_only":
        return build_cache_residency_evidence(
            gate=gate,
            configured_flags={"hot_cache_max_size": "8GB"},
            runtime_profile="unknown",
        )
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
            configured_flags={"hot_cache_max_size": "8GB"},
            runtime_profile="cache-enabled",
            runtime_flags={"hot_cache_max_size": "8GB"},
            metrics={"entries": 3, "resident_bytes": 1024},
        )
    if status == "reuse_signal_visible":
        return build_cache_residency_evidence(
            gate=gate,
            configured_flags={"hot_cache_max_size": "8GB"},
            runtime_profile="cache-enabled",
            runtime_flags={"hot_cache_max_size": "8GB"},
            metrics={"reuse_events": 2, "hit_count": 5},
        )
    if status == "repeat_eviction_visible":
        return build_cache_residency_evidence(
            gate=gate,
            configured_flags={"hot_cache_max_size": "8GB"},
            runtime_profile="cache-enabled",
            runtime_flags={"hot_cache_max_size": "8GB"},
            metrics={"reuse_events": 2, "hit_count": 5, "eviction_events": 1},
        )
    return build_cache_residency_evidence(gate=gate)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx repeated-serving cache evidence."
    )
    parser.add_argument(
        "--run-status",
        action="append",
        choices=(
            "no_runtime_evidence",
            "configuration_only",
            "profile_active_under_load",
            "residency_signal_visible",
            "reuse_signal_visible",
            "repeat_eviction_visible",
        ),
        help="Append one synthetic repeated run status.",
    )
    parser.add_argument(
        "--served-per-run",
        type=int,
        action="append",
        help="Optional requests served per synthetic run, aligned by position.",
    )
    args = parser.parse_args()

    statuses = args.run_status or []
    served = args.served_per_run or []
    runs = []
    for index, status in enumerate(statuses):
        runs.append(_build_run(status, served[index] if index < len(served) else 1))

    evidence = build_cache_repeatability_evidence(runs)
    print(json.dumps(cache_repeatability_evidence_to_dict(evidence), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
