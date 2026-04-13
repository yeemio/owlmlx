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
    args = parser.parse_args()

    status = build_heavy_weight_runtime_repeatability_status(
        specimen_path=args.specimen_path,
        include_known_candidates=args.include_known_venvs,
        supported_host_proof_visible=args.supported_host_proof_visible,
        supported_host_repeat_runs=args.supported_host_repeat_runs,
    )
    print(json.dumps(heavy_weight_repeatability_status_to_dict(status), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
