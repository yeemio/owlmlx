# scripts/replacement/r4_phaseb_b1_flip_readiness.py
"""R4 Phase B · B1 flip-readiness gate (owlmlx-side).

Combines the read-only R2 consumer-contract conformance check with the R4
model/tool-lane readiness probe into a single go/no-go gate for flipping the
OwlCoda default to owlmlx (owlmlx-primary + :8009 fallback RETAINED). The known
OwlCC `/v1/models` gap does NOT block — OwlCC repoint is B3. Promotes nothing;
the consumer flip EXECUTION is a gated runbook step, never automated here.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping


def evaluate_flip_readiness(conformance: Mapping[str, Any], readiness: Mapping[str, Any]) -> dict:
    """Pure. Gate the OwlCoda flip.

    conformance: r2 aggregate dict {"verdict", "contracts": [{"contract", "status"}]}.
    readiness:   r4 result dict {"ready": bool, "failures": [str], "verdict": str}.
    go iff (no OwlCoda-side conformance gap) AND (readiness.ready). The OwlCC-side
    gap (contract name starts with "owlcc") does NOT block the OwlCoda flip.
    """
    blocking: list[str] = []
    for c in conformance.get("contracts", []):
        name = str(c.get("contract", ""))
        if c.get("status") == "gap" and name.startswith("owlcoda"):
            blocking.append(f"conformance:{name}")
    if not readiness.get("ready", False):
        for f in readiness.get("failures", []):
            blocking.append(f"readiness:{f}")
    return {
        "round": "R4-phaseB-B1",
        "tier": "flip-readiness",
        "verdict": "go" if not blocking else "no_go",
        "blocking": blocking,
        "conformance_verdict": conformance.get("verdict"),
        "readiness_verdict": readiness.get("verdict"),
        "note": (
            "go = owlmlx ready to be the OwlCoda default (owlmlx-primary + :8009 "
            "fallback RETAINED). The OwlCC-side /v1/models gap does NOT block "
            "(OwlCC repoint is B3). promotes nothing; not sustained; not "
            "replacement-complete."
        ),
    }
