#!/usr/bin/env python3
"""Emit runtime-owned cache residency/reuse evidence for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_residency_evidence,
    cache_residency_evidence_to_dict,
)
from owlmlx.serving import GenerationGate


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the current owlmlx cache residency/reuse evidence."
    )
    parser.add_argument("--configured-cache-dir", default=None)
    parser.add_argument("--configured-cache-max-size", default=None)
    parser.add_argument("--configured-hot-cache-size", default=None)
    parser.add_argument(
        "--runtime-profile",
        choices=("baseline", "cache-enabled", "not_running", "unknown"),
        default=None,
    )
    parser.add_argument("--runtime-cache-dir", default=None)
    parser.add_argument("--runtime-cache-max-size", default=None)
    parser.add_argument("--runtime-hot-cache-size", default=None)
    parser.add_argument("--entries", type=int, default=None)
    parser.add_argument("--resident-bytes", type=int, default=None)
    parser.add_argument("--reuse-events", type=int, default=None)
    parser.add_argument("--hit-count", type=int, default=None)
    parser.add_argument("--eviction-events", type=int, default=None)
    parser.add_argument("--served", type=int, default=0)
    args = parser.parse_args()

    gate = GenerationGate()
    for _ in range(max(args.served, 0)):
        gate.execute(lambda: None)

    configured_flags = {
        "paged_ssd_cache_dir": args.configured_cache_dir,
        "paged_ssd_cache_max_size": args.configured_cache_max_size,
        "hot_cache_max_size": args.configured_hot_cache_size,
    }
    runtime_flags = {
        "paged_ssd_cache_dir": args.runtime_cache_dir,
        "paged_ssd_cache_max_size": args.runtime_cache_max_size,
        "hot_cache_max_size": args.runtime_hot_cache_size,
    }
    metrics = {
        "entries": args.entries,
        "resident_bytes": args.resident_bytes,
        "reuse_events": args.reuse_events,
        "hit_count": args.hit_count,
        "eviction_events": args.eviction_events,
    }

    evidence = build_cache_residency_evidence(
        gate=gate,
        configured_flags=configured_flags,
        runtime_profile=args.runtime_profile,
        runtime_flags=runtime_flags if any(runtime_flags.values()) else None,
        metrics=metrics if any(value is not None for value in metrics.values()) else None,
    )
    print(json.dumps(cache_residency_evidence_to_dict(evidence), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
