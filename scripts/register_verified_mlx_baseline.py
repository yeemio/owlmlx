#!/usr/bin/env python3
"""Register a verified-safe MLX baseline for owlmlx readiness selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx.runtime import (
    MlxEnvironmentCandidate,
    probe_mlx_environments,
    remember_verified_baseline,
    selection_to_dict,
    select_mlx_environment,
    verified_baseline_file_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify and register a safe MLX baseline interpreter."
    )
    parser.add_argument("--python", required=True, help="Python executable to verify.")
    parser.add_argument("--label", required=True, help="Stable label for this baseline.")
    parser.add_argument(
        "--execution-mode",
        choices=("default_metal", "force_cpu"),
        default="default_metal",
        help="Execution mode to verify for this interpreter.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=20.0,
        help="Probe timeout in seconds.",
    )
    args = parser.parse_args()

    candidate = MlxEnvironmentCandidate(args.python, args.label, args.execution_mode)
    probes = probe_mlx_environments((candidate,), timeout_s=args.timeout_s)
    selection = select_mlx_environment((candidate,), timeout_s=args.timeout_s)
    payload = {
        "probe": {
            "label": probes[0].candidate.label,
            "python_executable": probes[0].candidate.python_executable,
            "usable": probes[0].usable,
            "returncode": probes[0].result.returncode,
            "message": probes[0].result.message,
            "stderr": probes[0].result.stderr,
        },
        "selection": selection_to_dict(selection),
        "verified_baseline_file": str(verified_baseline_file_path()),
    }
    if not selection.ok:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    remember_verified_baseline(
        args.python,
        label=args.label,
        execution_mode=args.execution_mode,
    )
    payload["registered"] = {
        "python_executable": str(Path(args.python).expanduser()),
        "label": args.label,
        "execution_mode": args.execution_mode,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
