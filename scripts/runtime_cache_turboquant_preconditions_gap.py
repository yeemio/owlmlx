#!/usr/bin/env python3
"""Emit the active-path TurboQuant preconditions gap."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_turboquant_preconditions_gap,
    cache_turboquant_preconditions_gap_to_dict,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx TurboQuant preconditions gap."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        harness = run_cache_runtime_observation_harness()
        payload = cache_turboquant_preconditions_gap_to_dict(
            build_cache_turboquant_preconditions_gap(readiness=harness.turboquant)
        )
        payload["cache_harness"] = harness.backend_observations
    else:
        payload = cache_turboquant_preconditions_gap_to_dict(
            build_cache_turboquant_preconditions_gap()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
