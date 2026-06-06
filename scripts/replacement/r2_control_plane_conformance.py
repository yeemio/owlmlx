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


def evaluate_owlcoda_openai_models(payload):
    # owlcoda/src/runtime-probe.ts:61-66 parseOpenAiModelIds -> data[].id
    ok = _is_openai_list(payload)
    return {
        "contract": "owlcoda_gate_openai_models",
        "endpoint": "/v1/openai/models",
        "consumer_ref": "owlcoda/src/runtime-probe.ts:61-66",
        "consumer_reads": ["data[].id"],
        "status": PASS if ok else GAP,
        "missing": [] if ok else ["data[].id"],
        "notes": "Availability-truth surface for owlmlx-gate.",
    }


def evaluate_owlcoda_model_visibility(payload):
    # owlcoda/src/runtime-probe.ts:93-154 probeOwmlxRuntimeVisibility
    scalar = [
        "rule", "contract_version",
        "formal_surface.endpoint", "diagnostic_surface.endpoint",
        "loaded_inventory_surface.endpoint", "loaded_inventory_surface.semantic_role",
        "gate.owner", "gate.kind", "gate.models_root",
    ]
    missing = [p for p in scalar if not _dot_present(payload, p)]
    for key in ("visible_model_ids", "blocked_model_ids"):
        if not isinstance(payload.get(key), list):
            missing.append(key)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        missing.append("entries[]")
    elif entries:
        e0 = entries[0]
        for f in ("model_id", "visible", "block_reason"):
            if not isinstance(e0, dict) or f not in e0:
                missing.append("entries[].%s" % f)
    return {
        "contract": "owlcoda_gate_model_visibility",
        "endpoint": "/v1/runtime/model-visibility",
        "consumer_ref": "owlcoda/src/runtime-probe.ts:93-154; admin/src/api/types.ts:43-63",
        "consumer_reads": scalar + ["visible_model_ids", "blocked_model_ids",
                                    "entries[].model_id", "entries[].visible", "entries[].block_reason"],
        "status": PASS if not missing else GAP,
        "missing": missing,
        "notes": "Diagnostic surface; all fields owlmlx-gate parses must be present.",
    }


def evaluate_owlcoda_loaded_inventory(payload):
    # owlcoda/src/runtime-probe.ts:68-84 parseLoadedInventory
    missing = []
    inv = payload.get("inventory")
    if not isinstance(inv, dict):
        missing.append("inventory")
    else:
        if not isinstance(inv.get("model_count"), int):
            missing.append("inventory.model_count")
        entries = inv.get("entries")
        if not isinstance(entries, list):
            missing.append("inventory.entries[]")
        elif entries and "model_id" not in entries[0]:
            missing.append("inventory.entries[].model_id")
    if not _dot_present(payload, "visibility_contract.loaded_inventory_surface.semantic_role"):
        missing.append("visibility_contract.loaded_inventory_surface.semantic_role")
    return {
        "contract": "owlcoda_gate_loaded_inventory",
        "endpoint": "/v1/models",
        "consumer_ref": "owlcoda/src/runtime-probe.ts:68-84",
        "consumer_reads": ["inventory.entries[].model_id", "inventory.model_count",
                           "visibility_contract.loaded_inventory_surface.semantic_role"],
        "status": PASS if not missing else GAP,
        "missing": missing,
        "notes": "owlmlx /v1/models = loaded-inventory only (owlmlx-gate reads it correctly).",
    }


def evaluate_owlcoda_runtime_status(payload):
    # owlcoda/src/runtime-probe.ts:231-245
    missing = []
    if not _dot_present(payload, "health.readiness"):
        missing.append("health.readiness")
    if not _dot_present(payload, "backend.healthy"):
        missing.append("backend.healthy")
    inv = payload.get("inventory")
    if not isinstance(inv, dict):
        missing.append("inventory")
    else:
        if not isinstance(inv.get("model_count"), int):
            missing.append("inventory.model_count")
        entries = inv.get("entries")
        if not isinstance(entries, list):
            missing.append("inventory.entries[]")
        elif entries and "model_id" not in entries[0]:
            missing.append("inventory.entries[].model_id")
    backend = payload.get("backend")
    if not isinstance(backend, dict):
        missing.append("backend")
    else:
        lm = backend.get("loaded_models")
        if not isinstance(lm, list):
            missing.append("backend.loaded_models[]")
        elif lm and "model_id" not in lm[0]:
            missing.append("backend.loaded_models[].model_id")
    return {
        "contract": "owlcoda_gate_runtime_status",
        "endpoint": "/v1/runtime/status",
        "consumer_ref": "owlcoda/src/runtime-probe.ts:231-245",
        "consumer_reads": ["health.readiness", "backend.healthy",
                           "inventory.entries[].model_id", "inventory.model_count",
                           "backend.loaded_models[].model_id"],
        "status": PASS if not missing else GAP,
        "missing": missing,
        "notes": "Probe reports actual owlmlx status shape; missing fields are honest gaps.",
    }
