#!/usr/bin/env python3
"""Emit a structured host-level MLX crash forensics report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx.runtime import build_mlx_host_forensics_report, host_forensics_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit host-level MLX crash forensics for owlmlx."
    )
    parser.add_argument(
        "--execution-mode",
        choices=("default_metal", "force_cpu"),
        default="default_metal",
        help="Execution mode to report readiness against.",
    )
    parser.add_argument(
        "--crash-report-directory",
        type=Path,
        default=None,
        help="Override macOS crash report directory.",
    )
    parser.add_argument(
        "--crash-limit",
        type=int,
        default=5,
        help="Maximum number of crash reports to include.",
    )
    args = parser.parse_args()

    report = build_mlx_host_forensics_report(
        preferred_execution_mode=args.execution_mode,
        crash_report_directory=args.crash_report_directory,
        crash_limit=args.crash_limit,
    )
    print(json.dumps(host_forensics_to_dict(report), indent=2, sort_keys=True))
    return 0 if report.readiness.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
