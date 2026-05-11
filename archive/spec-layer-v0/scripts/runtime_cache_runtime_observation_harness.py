#!/usr/bin/env python3
"""Run a real owlmlx repeated-serving backend path and emit cache observations."""

from __future__ import annotations

import json

from owlmlx import (
    build_cache_closure_rung,
    cache_closure_rung_to_dict,
    cache_repeatability_evidence_to_dict,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def main() -> int:
    result = run_cache_runtime_observation_harness()
    print(
        json.dumps(
            {
                "contract": {
                    "surface": "owlmlx.cache_runtime_observation_harness",
                    "version": "phase45",
                    "stable_sections": [
                        "summary",
                        "backend_observations",
                        "cache_repeatability",
                        "cache_closure",
                    ],
                },
                "summary": {
                    "status": "ok",
                    "blocked_reason": None,
                },
                "backend_observations": result.backend_observations,
                "cache_repeatability": cache_repeatability_evidence_to_dict(
                    result.repeatability
                )["summary"],
                "cache_closure": cache_closure_rung_to_dict(
                    build_cache_closure_rung(
                        repeatability=result.repeatability,
                        turboquant=result.turboquant,
                    )
                )["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
