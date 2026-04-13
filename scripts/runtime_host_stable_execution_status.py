#!/usr/bin/env python3
"""Emit the host-stable execution status contract for owlmlx."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx.runtime import (
    build_host_stable_execution_status,
    host_stability_to_dict,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the host-stable execution status for owlmlx."
    )
    parser.add_argument(
        "--include-known-venvs",
        action="store_true",
        help="Expand diagnostics to broader known local environments.",
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

    status = build_host_stable_execution_status(
        include_known_candidates=args.include_known_venvs,
        crash_report_directory=args.crash_report_directory,
        crash_limit=args.crash_limit,
    )
    print(json.dumps(host_stability_to_dict(status), indent=2, sort_keys=True))
    return 0 if status.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())

