"""R2 consumer-contract conformance probe (read-only).

Asserts owlmlx control-plane endpoint response shapes satisfy the fields the
consumers actually parse. Contract field lists are derived from consumer source
(read-only), cited inline:
  OwlCC  : owlcc/src/preflight.ts  (/healthz status<400; /v1/models data[].id)
  OwlCoda: owlcoda/src/runtime-probe.ts + owlcoda/admin/src/api/types.ts
Promotes nothing. Evidence-language: conformance only, never parity/equivalent.
"""
from __future__ import annotations

PASS = "pass"
GAP = "gap"


def _dot_present(d, dotted):
    """True if a nested dict scalar path (no lists) exists."""
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return True


def _is_openai_list(payload):
    """True if payload has OpenAI list shape {data:[{id}...]} (empty data ok)."""
    data = payload.get("data")
    if not isinstance(data, list):
        return False
    return (not data) or (isinstance(data[0], dict) and "id" in data[0])


def evaluate_owlcc_healthz(payload):
    # owlcc/src/preflight.ts:36 requires HTTP<400; ok/readiness are owlmlx extras.
    missing = [k for k in ("ok", "readiness") if k not in payload]
    return {
        "contract": "owlcc_preflight_healthz",
        "endpoint": "/healthz",
        "consumer_ref": "owlcc/src/preflight.ts:36,57",
        "consumer_reads": ["HTTP status < 400", "ok", "readiness"],
        "status": PASS if not missing else GAP,
        "missing": missing,
        "notes": "Preflight only needs HTTP<400; ok/readiness checked as health extras.",
    }


def evaluate_owlcc_v1_models(payload):
    # owlcc/src/preflight.ts:119-120 reads data[].id. owlmlx /v1/models is a
    # status-dict with no data[] -> known gap.
    ok = _is_openai_list(payload)
    return {
        "contract": "owlcc_preflight_v1_models",
        "endpoint": "/v1/models",
        "consumer_ref": "owlcc/src/preflight.ts:119-120",
        "consumer_reads": ["data[].id"],
        "status": PASS if ok else GAP,
        "missing": [] if ok else ["data[].id (owlmlx /v1/models is loaded-inventory status-dict, not an OpenAI list)"],
        "notes": "Resolution: post-cutover OwlCC must probe /v1/openai/models for availability truth.",
    }


def evaluate_owlcc_openai_models_resolution(payload):
    ok = _is_openai_list(payload)
    return {
        "contract": "owlcc_resolution_openai_models",
        "endpoint": "/v1/openai/models",
        "consumer_ref": "owlcc/src/preflight.ts:119-120 (resolution surface)",
        "consumer_reads": ["data[].id"],
        "status": PASS if ok else GAP,
        "missing": [] if ok else ["data[].id"],
        "notes": "Availability-truth surface OwlCC should read post-cutover.",
    }
