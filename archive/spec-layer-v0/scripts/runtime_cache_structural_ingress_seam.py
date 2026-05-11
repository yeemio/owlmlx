#!/usr/bin/env python3
"""Emit runtime-owned structural ingress seam truth for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_pre_claim_staging_seam_exactness,
    build_cache_pre_gate_admission_window_seam,
    build_cache_structural_ingress_seam,
    cache_structural_ingress_seam_to_dict,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    run_pre_gate_admission_hook_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    harness = run_pre_gate_admission_hook_harness() if args.run_harness else None
    payload = cache_structural_ingress_seam_to_dict(
        build_cache_structural_ingress_seam(
            pre_gate_admission_window_seam=build_cache_pre_gate_admission_window_seam(),
            pre_claim_staging_seam_exactness=build_cache_pre_claim_staging_seam_exactness(),
            hook_harness=harness,
        )
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
