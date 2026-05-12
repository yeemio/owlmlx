#!/usr/bin/env python3
"""Emit runtime-owned heavy-weight repeatability status for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_heavy_weight_runtime_repeatability_status,
    heavy_weight_repeatability_status_to_dict,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx heavy-weight runtime repeatability status."
    )
    parser.add_argument("--specimen-path", required=True)
    parser.add_argument("--include-known-venvs", action="store_true")
    parser.add_argument("--supported-host-proof-visible", action="store_true")
    parser.add_argument("--supported-host-repeat-runs", type=int, default=0)
    parser.add_argument("--boundary-memory-gb", type=float)
    parser.add_argument("--boundary-entered", action="store_true")
    parser.add_argument("--boundary-entry-reason")
    args = parser.parse_args()

    status = build_heavy_weight_runtime_repeatability_status(
        specimen_path=args.specimen_path,
        include_known_candidates=args.include_known_venvs,
        supported_host_proof_visible=args.supported_host_proof_visible,
        supported_host_repeat_runs=args.supported_host_repeat_runs,
        boundary_required_memory_gb=args.boundary_memory_gb,
        boundary_entry_visible=args.boundary_entered,
        boundary_entry_reason=args.boundary_entry_reason,
    )
    print(json.dumps(heavy_weight_repeatability_status_to_dict(status), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
