#!/usr/bin/env python3
"""Emit the stable owlmlx MLX environment readiness contract as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx.runtime import build_mlx_environment_readiness, readiness_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report owlmlx MLX environment readiness."
    )
    parser.add_argument(
        "--include-known-venvs",
        action="store_true",
        help="Expand diagnostics to broader known local environments.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=20.0,
        help="Probe timeout in seconds.",
    )
    parser.add_argument(
        "--quarantine-path",
        type=Path,
        default=None,
        help="Override the quarantine file path.",
    )
    parser.add_argument(
        "--execution-mode",
        choices=("default_metal", "force_cpu"),
        default="default_metal",
        help="Execution mode to validate.",
    )
    args = parser.parse_args()

    readiness = build_mlx_environment_readiness(
        include_known_candidates=args.include_known_venvs,
        preferred_execution_mode=args.execution_mode,
        timeout_s=args.timeout_s,
        quarantine_path=args.quarantine_path,
    )
    print(json.dumps(readiness_to_dict(readiness), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
