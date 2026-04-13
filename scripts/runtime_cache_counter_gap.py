#!/usr/bin/env python3
"""Emit the exact residual cache counter gap for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_closure_rung,
    build_cache_counter_gap,
    cache_counter_gap_to_dict,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx cache counter-gap truth."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        harness = run_cache_runtime_observation_harness()
        payload = cache_counter_gap_to_dict(
            build_cache_counter_gap(
                closure=harness.closure,
                backend_observations=harness.backend_observations,
            )
        )
        payload["cache_harness"] = harness.backend_observations
    else:
        payload = cache_counter_gap_to_dict(
            build_cache_counter_gap(closure=build_cache_closure_rung())
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
