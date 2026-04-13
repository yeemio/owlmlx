#!/usr/bin/env python3
"""Emit the current machine-level MLX import blocker report."""

from __future__ import annotations

import json
import argparse

from owlmlx.runtime import (
    blocker_report_to_dict,
    build_mlx_import_blocker_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the current machine-level MLX import blocker report."
    )
    parser.add_argument(
        "--execution-mode",
        choices=("default_metal", "force_cpu"),
        default="default_metal",
        help="Execution mode to diagnose.",
    )
    args = parser.parse_args()

    report = build_mlx_import_blocker_report(
        include_known_candidates=True,
        preferred_execution_mode=args.execution_mode,
    )
    payload = blocker_report_to_dict(report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.readiness.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
