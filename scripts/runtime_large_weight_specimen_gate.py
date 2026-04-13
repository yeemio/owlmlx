#!/usr/bin/env python3
"""Emit the stable owlmlx large-weight specimen gate as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx.runtime import build_large_weight_specimen_gate, specimen_gate_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report the owlmlx large-weight specimen validation gate."
    )
    parser.add_argument("--specimen-path", required=True, help="Local model path to assess.")
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
        help="Execution mode to require for the specimen gate.",
    )
    args = parser.parse_args()

    gate = build_large_weight_specimen_gate(
        specimen_path=args.specimen_path,
        include_known_candidates=args.include_known_venvs,
        preferred_execution_mode=args.execution_mode,
        timeout_s=args.timeout_s,
        quarantine_path=args.quarantine_path,
    )
    print(json.dumps(specimen_gate_to_dict(gate), indent=2, sort_keys=True))
    return 0 if gate.smoke_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
