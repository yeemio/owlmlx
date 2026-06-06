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


# --- sibling imports (scripts/ is not a package) ---
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2_control_plane_conformance as _r2  # noqa: E402
import r4_ops_cutover_pilot as _r4  # noqa: E402

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[2]
    / "files" / "evidence" / "owlmlx" / "replacement" / "r4-phaseB-b1"
)


def build_flip_readiness_artifact(*, verdict, base_url, model_id, owlmlx_commit, recorded_at):
    return {
        "surface": "owlmlx.replacement.r4_phaseb_b1_flip_readiness",
        "version": "v1",
        "kind": "flip_readiness",
        "recorded_at": recorded_at,
        "verdict": verdict["verdict"],
        "blocking": list(verdict.get("blocking") or []),
        "flip_readiness": verdict,
        "reproduction": {"base_url": base_url, "model_id": model_id, "owlmlx_commit": owlmlx_commit},
        "promotes": "nothing",
        "honesty_note": _r4._HONESTY_NOTE,
    }


def run_flip_readiness(*, base_url, model_id, owlmlx_commit, evidence_dir, timeout_s):
    conformance = _r2.run_contracts(base_url)
    readiness = _r4.run_probe_readiness(
        base_url=base_url, model_id=model_id, owlmlx_commit=owlmlx_commit,
        evidence_dir=evidence_dir, timeout_s=timeout_s,
    )
    verdict = evaluate_flip_readiness(conformance, readiness)
    recorded_at = _r4._now_iso_utc()
    artifact = build_flip_readiness_artifact(
        verdict=verdict, base_url=base_url, model_id=model_id,
        owlmlx_commit=owlmlx_commit, recorded_at=recorded_at,
    )
    artifact["conformance"] = conformance
    artifact["readiness_artifact"] = readiness.get("artifact_filename")
    fname = f"{_r4._now_compact_utc()}-flip-readiness-{verdict['verdict']}.json"
    _r4._write_json(evidence_dir / fname, artifact)
    return {"verdict": verdict["verdict"], "blocking": verdict["blocking"],
            "artifact_path": str(evidence_dir / fname)}


def build_flip_state_evidence(*, flip_readiness, post_flip_capture, reproduction, recorded_at):
    """Pure. Record the POST-flip state: owlmlx serving the default + fallback baseline.

    post_flip_capture: operator-captured {request_ids:[...],
      owlmlx_inbound:{served_request_ids:[...]}, consumer:{fallback_count:int, outbound_hosts:[...]}}.
    HONEST: B1 = flip staged + initial real traffic served + :8009 fallback retained.
    NOT sustained (that is B2); fallback_used_count>0 is a truthful owlmlx-gap signal.
    """
    served = {str(r) for r in (post_flip_capture.get("owlmlx_inbound", {}).get("served_request_ids") or [])}
    req_ids = {str(r) for r in (post_flip_capture.get("request_ids") or [])}
    inbound_coverage_ok = bool(req_ids) and req_ids <= served
    fallback_count = int(post_flip_capture.get("consumer", {}).get("fallback_count", -1))
    return {
        "surface": "owlmlx.replacement.r4_phaseb_b1_flip_state",
        "version": "v1",
        "kind": "flip_state",
        "recorded_at": recorded_at,
        "flip_readiness": flip_readiness,
        "inbound_coverage_ok": inbound_coverage_ok,
        "missing_request_ids": sorted(req_ids - served),
        "fallback_used_count": fallback_count,
        "fallback_retained": True,
        "reproduction": dict(reproduction),
        "promotes": "nothing",
        "honesty": (
            "B1 flip staged + initial real traffic served by owlmlx + :8009 fallback "
            "RETAINED. NOT sustained (B2), NOT replacement-complete. fallback_used_count>0 "
            "is an honest owlmlx-gap signal (fed back to R1/diagnosis), not hidden."
        ),
    }


def run_assemble_flip_state(*, capture_path, evidence_dir):
    capture = json.loads(Path(capture_path).read_text(encoding="utf-8"))
    ev = build_flip_state_evidence(
        flip_readiness=capture.get("flip_readiness") or {},
        post_flip_capture=capture.get("post_flip_capture") or {},
        reproduction=capture.get("reproduction") or {},
        recorded_at=_r4._now_iso_utc(),
    )
    fname = f"{_r4._now_compact_utc()}-flip-state.json"
    _r4._write_json(evidence_dir / fname, ev)
    return {"inbound_coverage_ok": ev["inbound_coverage_ok"],
            "fallback_used_count": ev["fallback_used_count"],
            "artifact_path": str(evidence_dir / fname)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="R4 Phase B · B1 flip-readiness gate (owlmlx-side).")
    sub = parser.add_subparsers(dest="command", required=True)
    chk = sub.add_parser("check", help="Run R2 conformance + R4 readiness -> go/no_go (loads a model).")
    chk.add_argument("--base-url", default=os.environ.get("OWLMLX_PILOT_BASE_URL", "http://127.0.0.1:8066"))
    chk.add_argument("--model-id", default=os.environ.get("OWLMLX_PILOT_MODEL_ID"),
                     required=os.environ.get("OWLMLX_PILOT_MODEL_ID") is None)
    chk.add_argument("--owlmlx-commit", required=True)
    chk.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    chk.add_argument("--timeout-s", type=float, default=120.0)
    asm = sub.add_parser("assemble-flip-state", help="Assemble operator-captured post-flip data into flip-state evidence.")
    asm.add_argument("--capture", type=Path, required=True)
    asm.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    args = parser.parse_args(argv)
    if args.command == "check":
        result = run_flip_readiness(base_url=args.base_url, model_id=args.model_id,
                                    owlmlx_commit=args.owlmlx_commit, evidence_dir=args.evidence_dir,
                                    timeout_s=args.timeout_s)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["verdict"] == "go" else 1
    if args.command == "assemble-flip-state":
        result = run_assemble_flip_state(capture_path=args.capture, evidence_dir=args.evidence_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
