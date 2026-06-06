# R2 Control-Plane Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify owlmlx's existing control-plane endpoints satisfy the *actual* contracts the consumers (OwlCoda owlmlx-gate, OwlCC preflight) parse, run one controlled control-plane operability rehearsal, and freeze the last-mile contract — producing evidence + an operator runbook. **Promotes nothing.**

**Architecture:** Two read-only/bench probes under `scripts/replacement/`, each built around **pure-function evaluators** (response dict → verdict) so the logic is unit-testable with no live server (mirrors `scripts/replacement/r4_ops_cutover_pilot.py`). Conformance probe runs read-only against live `:8066`; operability rehearsal mutates runtime state so it runs against an isolated bench server (cost-flagged). Three-state verdict: `passed` / `contract_gap_found` / `rehearsal_failed`.

**Tech Stack:** Python 3 (stdlib `urllib.request` for HTTP GET/POST — no new deps), pytest. Tests load the non-package `scripts/` module via `importlib.util.spec_from_file_location` (the established repo pattern — `scripts/` is not a package).

**Spec:** `docs/architect/design/R2-control-plane-closure-spec.md`
**Consumer-contract source of truth (read-only refs, cited in code):**
- OwlCC: `/Users/yeemio/AI/gitrep/owlcc/src/preflight.ts` (`/healthz` status<400; `/v1/models` → `data[].id`), `owlcc/src/config.ts:66` (routerUrl default `:8009`).
- OwlCoda: `/Users/yeemio/AI/gitrep/owlcoda/src/runtime-probe.ts` (`probeOwmlxRuntimeVisibility`, `parseOpenAiModelIds`, `parseLoadedInventory`, `/v1/runtime/status` parse), `owlcoda/admin/src/api/types.ts:43-63` (`PlatformVisibilityInfo`).

**Hard rules (from spec §9):** no new `owlmlx/` modules (probes/tests only in `scripts/replacement/` + `tests/`); conformance probe read-only; operability only on isolated bench, never `:8066`; evidence-language calibrated (no parity/equivalent/replaces); stage only round-scope files — **never** `uv.lock` / `owlmlx/speculative/*` / pre-existing dirty files.

---

## Reference shapes (verified 2026-06-05/06)

**owlmlx `/v1/openai/models`** → `{"object":"list","data":[{"id":<str>,"object":"model","owned_by":"owlmlx"}]}`
**owlmlx `/v1/models`** → status-dict: `{"active_model_id":<str>,"inventory":{"entries":[{"model_id":<str>,...}],"model_count":<int>},"budget":{...},"health":{...},"generation_gate":{...},"backend":{...},"visibility_contract":{"loaded_inventory_surface":{"semantic_role":<str>},...}}` — **no top-level `data[]`**.
**owlmlx `/v1/runtime/model-visibility`** → `{"surface","contract_version","rule","formal_surface":{"endpoint",...},"diagnostic_surface":{"endpoint",...},"loaded_inventory_surface":{"endpoint","semantic_role",...},"gate":{"owner","kind","models_root","required_artifact"},"visible_model_ids":[...],"technical_preview_visible_model_ids":[...],"blocked_model_ids":[...],"entries":[{"model_id","tier","registered","visible","block_reason",...}]}`
**owlmlx `/healthz`** → `{"ok":<bool>,"readiness":<str>,"active_model_id":<str>,"model_count":<int>,...}`
**owlmlx `/v1/runtime/status`** → `runtime.status_dict()` with `contract`, `summary`, `backend`, `inventory`, `health` sections (exact `health.readiness` / `backend.healthy` / `backend.loaded_models[]` presence is what the probe **discovers** live — assert and let the verdict report reality).

---

### Task 1: Conformance probe scaffolding + OwlCC contract evaluators

**Files:**
- Create: `scripts/replacement/r2_control_plane_conformance.py`
- Test: `tests/test_r2_control_plane_conformance.py`

- [ ] **Step 1: Write failing tests for shared helper + OwlCC evaluators**

```python
# tests/test_r2_control_plane_conformance.py
import importlib.util
from pathlib import Path

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "replacement" / "r2_control_plane_conformance.py"
_spec = importlib.util.spec_from_file_location("r2_control_plane_conformance", _MOD)
r2c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r2c)


def test_dot_present_nested_scalar():
    assert r2c._dot_present({"a": {"b": 1}}, "a.b") is True
    assert r2c._dot_present({"a": {"b": 1}}, "a.c") is False
    assert r2c._dot_present({"a": 1}, "a.b") is False


def test_owlcc_healthz_pass():
    v = r2c.evaluate_owlcc_healthz({"ok": True, "readiness": "ready", "model_count": 1})
    assert v["status"] == r2c.PASS
    assert v["missing"] == []


def test_owlcc_healthz_gap_when_missing_readiness():
    v = r2c.evaluate_owlcc_healthz({"ok": True})
    assert v["status"] == r2c.GAP
    assert "readiness" in v["missing"]


def test_owlcc_v1_models_gap_on_statusdict():
    # owlmlx /v1/models is a status-dict with NO data[] -> gap vs OwlCC preflight data[].id
    payload = {"active_model_id": "m", "inventory": {"entries": [{"model_id": "m"}], "model_count": 1}}
    v = r2c.evaluate_owlcc_v1_models(payload)
    assert v["status"] == r2c.GAP
    assert any("data[].id" in m for m in v["missing"])


def test_owlcc_v1_models_pass_on_openai_list():
    v = r2c.evaluate_owlcc_v1_models({"object": "list", "data": [{"id": "m"}]})
    assert v["status"] == r2c.PASS


def test_owlcc_openai_models_resolution_pass():
    v = r2c.evaluate_owlcc_openai_models_resolution({"object": "list", "data": [{"id": "m"}]})
    assert v["status"] == r2c.PASS
    assert v["endpoint"] == "/v1/openai/models"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_conformance.py -v`
Expected: FAIL — `ModuleNotFoundError`/`AttributeError` (module/functions not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/replacement/r2_control_plane_conformance.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_conformance.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r2_control_plane_conformance.py tests/test_r2_control_plane_conformance.py
git commit -m "feat(r2): conformance probe scaffolding + OwlCC contract evaluators

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: OwlCoda owlmlx-gate contract evaluators

**Files:**
- Modify: `scripts/replacement/r2_control_plane_conformance.py`
- Test: `tests/test_r2_control_plane_conformance.py`

- [ ] **Step 1: Write failing tests (append)**

```python
def _owlmlx_model_visibility_sample():
    return {
        "surface": "/v1/runtime/model-visibility",
        "contract_version": "runtime-owned-2",
        "rule": "registered_base_model_config_present",
        "formal_surface": {"endpoint": "/v1/openai/models"},
        "diagnostic_surface": {"endpoint": "/v1/runtime/model-visibility"},
        "loaded_inventory_surface": {"endpoint": "/v1/models", "semantic_role": "loaded_inventory_only"},
        "gate": {"owner": "owlmlx", "kind": "registry", "models_root": "/m"},
        "visible_model_ids": ["m"],
        "blocked_model_ids": [],
        "entries": [{"model_id": "m", "visible": True, "block_reason": None}],
    }


def test_owlcoda_model_visibility_pass():
    v = r2c.evaluate_owlcoda_model_visibility(_owlmlx_model_visibility_sample())
    assert v["status"] == r2c.PASS, v["missing"]


def test_owlcoda_model_visibility_gap_when_entry_field_missing():
    s = _owlmlx_model_visibility_sample()
    del s["entries"][0]["block_reason"]
    v = r2c.evaluate_owlcoda_model_visibility(s)
    assert v["status"] == r2c.GAP
    assert "entries[].block_reason" in v["missing"]


def test_owlcoda_loaded_inventory_pass():
    payload = {
        "inventory": {"entries": [{"model_id": "m"}], "model_count": 1},
        "visibility_contract": {"loaded_inventory_surface": {"semantic_role": "loaded_inventory_only"}},
    }
    v = r2c.evaluate_owlcoda_loaded_inventory(payload)
    assert v["status"] == r2c.PASS, v["missing"]


def test_owlcoda_runtime_status_reports_missing_fields():
    # Probe the truth: a status-dict missing health.readiness must surface a gap.
    payload = {"backend": {"healthy": True, "loaded_models": [{"model_id": "m"}]},
               "inventory": {"entries": [{"model_id": "m"}], "model_count": 1}}
    v = r2c.evaluate_owlcoda_runtime_status(payload)
    assert v["status"] == r2c.GAP
    assert "health.readiness" in v["missing"]


def test_owlcoda_openai_models_pass():
    v = r2c.evaluate_owlcoda_openai_models({"object": "list", "data": [{"id": "m"}]})
    assert v["status"] == r2c.PASS
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_conformance.py -k owlcoda -v`
Expected: FAIL (`AttributeError` — evaluators not defined).

- [ ] **Step 3: Implement (append to script)**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_conformance.py -v`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r2_control_plane_conformance.py tests/test_r2_control_plane_conformance.py
git commit -m "feat(r2): OwlCoda owlmlx-gate contract evaluators

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Conformance aggregation + `probe-contracts` CLI + evidence writer

**Files:**
- Modify: `scripts/replacement/r2_control_plane_conformance.py`
- Test: `tests/test_r2_control_plane_conformance.py`

- [ ] **Step 1: Write failing tests (append)**

```python
def test_aggregate_passed_when_all_pass():
    verdicts = [{"status": r2c.PASS}, {"status": r2c.PASS}]
    agg = r2c.aggregate_conformance(verdicts)
    assert agg["verdict"] == "passed"
    assert agg["gap_count"] == 0


def test_aggregate_gap_found_when_any_gap():
    verdicts = [{"status": r2c.PASS}, {"status": r2c.GAP}]
    agg = r2c.aggregate_conformance(verdicts)
    assert agg["verdict"] == "contract_gap_found"
    assert agg["gap_count"] == 1
    assert agg["round"] == "R2"
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_conformance.py -k aggregate -v`
Expected: FAIL (`AttributeError: aggregate_conformance`).

- [ ] **Step 3: Implement aggregation + HTTP layer + CLI (append to script)**

```python
import argparse
import json
import os
import sys
import urllib.request


def aggregate_conformance(verdicts):
    gaps = [v for v in verdicts if v.get("status") == GAP]
    return {
        "round": "R2",
        "tier": "consumer-contract-conformance",
        "verdict": "contract_gap_found" if gaps else "passed",
        "gap_count": len(gaps),
        "contracts": verdicts,
    }


def _http_get_json(base_url, path, timeout=15):
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (local trusted URL)
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body)


# (endpoint, evaluator) pairs; each evaluator takes the parsed JSON body.
_CONTRACTS = [
    ("/healthz", evaluate_owlcc_healthz),
    ("/v1/models", evaluate_owlcc_v1_models),
    ("/v1/openai/models", evaluate_owlcc_openai_models_resolution),
    ("/v1/openai/models", evaluate_owlcoda_openai_models),
    ("/v1/runtime/model-visibility", evaluate_owlcoda_model_visibility),
    ("/v1/models", evaluate_owlcoda_loaded_inventory),
    ("/v1/runtime/status", evaluate_owlcoda_runtime_status),
]


def run_contracts(base_url):
    verdicts = []
    for path, evaluator in _CONTRACTS:
        try:
            status, body = _http_get_json(base_url, path)
        except Exception as exc:  # noqa: BLE001 — record fetch failure as a gap, don't crash
            verdicts.append({"contract": evaluator.__name__, "endpoint": path,
                             "status": GAP, "missing": ["<fetch failed: %s>" % exc]})
            continue
        v = evaluator(body if isinstance(body, dict) else {})
        v["http_status"] = status
        verdicts.append(v)
    return aggregate_conformance(verdicts)


def main(argv=None):
    parser = argparse.ArgumentParser(description="R2 control-plane consumer-contract conformance probe (read-only)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe-contracts", help="probe owlmlx control-plane endpoints (read-only)")
    p.add_argument("--base-url", default=os.environ.get("OWLMLX_BASE_URL", "http://127.0.0.1:8066"))
    p.add_argument("--out", default=None, help="write evidence JSON to this path")
    args = parser.parse_args(argv)

    if args.cmd == "probe-contracts":
        result = run_contracts(args.base_url)
        result["base_url"] = args.base_url
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.out:
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        print(text)
        return 0 if result["verdict"] == "passed" else 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass + smoke the CLI parses**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_conformance.py -v`
Expected: PASS (13 tests).
Run: `.venv/bin/python scripts/replacement/r2_control_plane_conformance.py --help`
Expected: usage text with `probe-contracts` subcommand (no crash).

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r2_control_plane_conformance.py tests/test_r2_control_plane_conformance.py
git commit -m "feat(r2): conformance aggregation + probe-contracts CLI + evidence writer

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Operability rehearsal step evaluators (pure functions)

**Files:**
- Create: `scripts/replacement/r2_control_plane_operability.py`
- Test: `tests/test_r2_control_plane_operability.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_r2_control_plane_operability.py
import importlib.util
from pathlib import Path

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "replacement" / "r2_control_plane_operability.py"
_spec = importlib.util.spec_from_file_location("r2_control_plane_operability", _MOD)
r2o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r2o)


def test_load_step_pass():
    healthz = {"active_model_id": "m", "readiness": "ready"}
    status = {"summary": {"active_model_id": "m"}}
    v = r2o.evaluate_load_step("m", healthz, status)
    assert v["status"] == r2o.PASS, v["reasons"]


def test_load_step_fail_when_wrong_active():
    healthz = {"active_model_id": "other", "readiness": "ready"}
    status = {"summary": {"active_model_id": "other"}}
    v = r2o.evaluate_load_step("m", healthz, status)
    assert v["status"] == r2o.FAIL
    assert any("active_model_id" in r for r in v["reasons"])


def test_switch_step_pass():
    v = r2o.evaluate_switch_step("m2", {"summary": {"active_model_id": "m2"}})
    assert v["status"] == r2o.PASS


def test_evict_step_pass():
    v = r2o.evaluate_evict_step("victim", {"selected_victim": "victim"}, {"summary": {"active_model_id": "keep"}})
    assert v["status"] == r2o.PASS


def test_evict_step_fail_when_no_victim():
    v = r2o.evaluate_evict_step("victim", {}, {"summary": {"active_model_id": "keep"}})
    assert v["status"] == r2o.FAIL


def test_restart_step_pass():
    v = r2o.evaluate_restart_step({"recovery": "ok"}, {"summary": {"readiness": "ready"}})
    assert v["status"] == r2o.PASS


def test_watermark_step_pass():
    v = r2o.evaluate_watermark_step({"level": "GREEN", "recommended_action": "none"})
    assert v["status"] == r2o.PASS


def test_watermark_step_fail_on_unknown():
    v = r2o.evaluate_watermark_step({"level": "UNKNOWN"})
    assert v["status"] == r2o.FAIL


def test_aggregate_lifecycle_passed():
    steps = [{"status": r2o.PASS}, {"status": r2o.PASS}]
    agg = r2o.aggregate_lifecycle(steps)
    assert agg["verdict"] == "passed"


def test_aggregate_lifecycle_failed():
    steps = [{"status": r2o.PASS}, {"status": r2o.FAIL}]
    agg = r2o.aggregate_lifecycle(steps)
    assert agg["verdict"] == "rehearsal_failed"
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_operability.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement step evaluators**

```python
# scripts/replacement/r2_control_plane_operability.py
"""R2 control-plane operability rehearsal (mutates runtime state).

Drives the control-plane lifecycle (load -> switch -> evict -> restart) via the
EXISTING owlmlx endpoints and asserts each transition is correctly reported, plus
watermark coherence. Pure-function step evaluators are unit-tested; the live
`rehearse` run MUST target an isolated bench server (never :8066) and is
cost-flagged. Promotes nothing; one controlled run != sustained stability.
"""
from __future__ import annotations

PASS = "pass"
FAIL = "fail"

_WATERMARK_OK = {"GREEN", "YELLOW", "RED", "FATAL"}


def _active(status):
    return (status or {}).get("summary", {}).get("active_model_id")


def _readiness(status):
    return (status or {}).get("summary", {}).get("readiness")


def evaluate_load_step(model_id, healthz, status):
    reasons = []
    if healthz.get("active_model_id") != model_id:
        reasons.append("healthz.active_model_id != %s" % model_id)
    if healthz.get("readiness") != "ready":
        reasons.append("healthz.readiness != ready")
    if _active(status) != model_id:
        reasons.append("status.summary.active_model_id != %s" % model_id)
    return {"step": "load", "model_id": model_id, "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_switch_step(model_id, status):
    reasons = [] if _active(status) == model_id else ["status.summary.active_model_id != %s" % model_id]
    return {"step": "model_switch", "model_id": model_id, "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_evict_step(expected_victim, evict_response, status):
    reasons = []
    if evict_response.get("selected_victim") != expected_victim:
        reasons.append("selected_victim != %s" % expected_victim)
    if _active(status) == expected_victim:
        reasons.append("evicted model still active")
    return {"step": "evict", "expected_victim": expected_victim,
            "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_restart_step(recovery_contract, status):
    reasons = []
    if not isinstance(recovery_contract, dict) or not recovery_contract:
        reasons.append("recovery-supervisor-contract empty")
    if _readiness(status) not in ("ready", "loading"):
        reasons.append("post-restart readiness not ready/loading")
    return {"step": "restart", "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_watermark_step(watermark):
    level = (watermark or {}).get("level")
    reasons = [] if level in _WATERMARK_OK else ["watermark level %r not in known set" % level]
    return {"step": "watermark", "level": level, "status": PASS if not reasons else FAIL, "reasons": reasons}


def aggregate_lifecycle(steps):
    failed = [s for s in steps if s.get("status") == FAIL]
    return {
        "round": "R2",
        "tier": "control-plane-operability-rehearsal",
        "verdict": "rehearsal_failed" if failed else "passed",
        "failed_count": len(failed),
        "steps": steps,
    }
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_operability.py -v`
Expected: PASS (10 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r2_control_plane_operability.py tests/test_r2_control_plane_operability.py
git commit -m "feat(r2): operability rehearsal step evaluators (pure functions)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Operability `rehearse` CLI (live drive — bench only, cost-flagged)

**Files:**
- Modify: `scripts/replacement/r2_control_plane_operability.py`

- [ ] **Step 1: Implement the CLI drive layer (no new pure-function logic to test — wiring only)**

Add HTTP helpers + the `rehearse` subcommand. The drive layer calls existing endpoints in order, feeds responses to the Task-4 evaluators, aggregates, and writes evidence. It performs **state-mutating** calls (`POST /v1/load`, `POST /v1/runtime/memory-pressure-eviction`, `POST /v1/runtime/restart`) so it refuses to run unless `--i-understand-bench-only` is passed, and warns if `--base-url` looks like `:8066`.

```python
import argparse
import json
import os
import sys
import urllib.request


def _http(base_url, method, path, body=None, timeout=120):
    url = base_url.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"content-type": "application/json", "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (local trusted URL)
        raw = resp.read().decode("utf-8")
        return resp.status, (json.loads(raw) if raw else {})


def rehearse(base_url, model_a, model_b, *, victim=None):
    """Drive load -> switch -> evict -> restart and sample watermark each phase."""
    steps = []
    _http(base_url, "POST", "/v1/load", {"model_id": model_a})
    _, hz = _http(base_url, "GET", "/healthz")
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_load_step(model_a, hz, st))
    steps.append(evaluate_watermark_step(_http(base_url, "GET", "/v1/runtime/memory-watermark")[1]))

    _http(base_url, "POST", "/v1/load", {"model_id": model_b})
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_switch_step(model_b, st))

    evict_victim = victim or model_a
    _, ev = _http(base_url, "POST", "/v1/runtime/memory-pressure-eviction", {"protect_active": True})
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_evict_step(evict_victim, ev, st))

    _http(base_url, "POST", "/v1/runtime/restart", {})
    _, rec = _http(base_url, "GET", "/v1/runtime/recovery-supervisor-contract")
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_restart_step(rec, st))
    steps.append(evaluate_watermark_step(_http(base_url, "GET", "/v1/runtime/memory-watermark")[1]))

    return aggregate_lifecycle(steps)


def main(argv=None):
    parser = argparse.ArgumentParser(description="R2 control-plane operability rehearsal (bench only — mutates state)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("rehearse", help="drive control-plane lifecycle on an ISOLATED bench server")
    p.add_argument("--base-url", required=True)
    p.add_argument("--model-a", required=True)
    p.add_argument("--model-b", required=True)
    p.add_argument("--victim", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--i-understand-bench-only", action="store_true",
                   help="required ack: this mutates runtime state; never run against :8066")
    args = parser.parse_args(argv)

    if args.cmd == "rehearse":
        if not args.i_understand_bench_only:
            print("REFUSED: rehearse mutates runtime state. Pass --i-understand-bench-only "
                  "and target an isolated bench server (never :8066).", file=sys.stderr)
            return 3
        if ":8066" in args.base_url:
            print("REFUSED: --base-url points at :8066 (the default daemon). Use an isolated bench.",
                  file=sys.stderr)
            return 3
        result = rehearse(args.base_url, args.model_a, args.model_b, victim=args.victim)
        result["base_url"] = args.base_url
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.out:
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        print(text)
        return 0 if result["verdict"] == "passed" else 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Verify safety guards + help (no live run yet)**

Run: `.venv/bin/python scripts/replacement/r2_control_plane_operability.py rehearse --base-url http://127.0.0.1:8066 --model-a a --model-b b`
Expected: `REFUSED` (no `--i-understand-bench-only`), exit 3.
Run: `.venv/bin/python scripts/replacement/r2_control_plane_operability.py rehearse --base-url http://127.0.0.1:8066 --model-a a --model-b b --i-understand-bench-only`
Expected: `REFUSED` (`:8066` guard), exit 3.
Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_operability.py -v`
Expected: PASS (unchanged, 10 tests).

- [ ] **Step 3: Commit**

```bash
git add scripts/replacement/r2_control_plane_operability.py
git commit -m "feat(r2): operability rehearse CLI with bench-only safety guards

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Operator runbook + last-mile contract freeze

**Files:**
- Create: `docs/architect/design/R2-control-plane-runbook.md`

- [ ] **Step 1: Write the runbook**

Include, with no placeholders: (a) the consumer-contract table (each contract → endpoint → fields the consumer parses → expected owlmlx response → pass/gap), (b) the **frozen last-mile contract** for the `/v1/models` vs `/v1/openai/models` semantic — stated as: *owlmlx `/v1/models` is loaded-inventory-only (status-dict, no `data[]`); availability truth is `/v1/openai/models` (OpenAI list, `data[].id`); OwlCoda's owlmlx-gate already reads this correctly; **OwlCC preflight must read `/v1/openai/models`, not `/v1/models`, when its `routerUrl` is repointed to owlmlx** (owlcc/src/preflight.ts:119-120)*, (c) the read-only conformance command, (d) the bench-only operability rehearsal command + cost note, (e) how to read the three-state verdict.

```markdown
# R2 — Control-Plane Operator Runbook

> design-grade · companion to [`R2-control-plane-closure-spec.md`](R2-control-plane-closure-spec.md). Promotes nothing.

## 1. Consumer-contract conformance (read-only — safe against live :8066)

```bash
.venv/bin/python scripts/replacement/r2_control_plane_conformance.py probe-contracts \
  --base-url http://127.0.0.1:8066 \
  --out files/evidence/owlmlx/replacement/r2-control-plane/<ts>-r2-conformance.json
```
Verdict: `passed` (exit 0) or `contract_gap_found` (exit 2). A gap is an honest, documented outcome — see §3.

## 2. Frozen last-mile contract — model-availability surface

- `GET /v1/openai/models` → **availability truth** (OpenAI list, `data[].id`).
- `GET /v1/models` → **loaded-inventory only** (status-dict: `inventory.entries[].model_id`, `inventory.model_count`, `visibility_contract.loaded_inventory_surface.semantic_role`); **no `data[]`**.
- `GET /v1/runtime/model-visibility` → diagnostic (visible/blocked + per-model gate reason).
- **OwlCoda** owlmlx-gate already reads these correctly (`owlcoda/src/runtime-probe.ts`).
- **OwlCC** preflight currently reads `/v1/models` → `data[].id` (`owlcc/src/preflight.ts:119-120`). When `routerUrl` is repointed to owlmlx, **OwlCC must read `/v1/openai/models`** for availability (its `/v1/models` probe will find no `data[]`). This is the R2 cutover prerequisite for OwlCC.

## 3. Control-plane operability rehearsal (bench only — mutates state, cost-flagged)

Launch an isolated bench server (never the :8066 default daemon), then:
```bash
.venv/bin/python scripts/replacement/r2_control_plane_operability.py rehearse \
  --base-url http://127.0.0.1:<bench-port> \
  --model-a <small-model> --model-b <small-model-2> \
  --i-understand-bench-only \
  --out files/evidence/owlmlx/replacement/r2-control-plane/<ts>-r2-operability.json
```
Cost: each `--model-*` is a real load (GBs, minutes). Use the smallest sufficient registered models. Verdict: `passed` or `rehearsal_failed`.
```

- [ ] **Step 2: Commit**

```bash
git add docs/architect/design/R2-control-plane-runbook.md
git commit -m "docs(r2): operator runbook + frozen model-availability surface contract

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Final verification + real read-only conformance evidence

**Files:**
- Create (runtime output): `files/evidence/owlmlx/replacement/r2-control-plane/<ts>-r2-conformance.json`

- [ ] **Step 1: Run the full R2 test suite**

Run: `.venv/bin/python -m pytest tests/test_r2_control_plane_conformance.py tests/test_r2_control_plane_operability.py -v`
Expected: PASS (23 tests).

- [ ] **Step 2: Capture REAL conformance evidence (read-only) against the live :8066**

The conformance probe is read-only (GET only) — safe to run against the user's daemon. Confirm `:8066` is up first (`curl -s http://127.0.0.1:8066/healthz`). Then:
Run: `.venv/bin/python scripts/replacement/r2_control_plane_conformance.py probe-contracts --base-url http://127.0.0.1:8066 --out files/evidence/owlmlx/replacement/r2-control-plane/$(... timestamp ...)-r2-conformance.json`
Expected: a JSON verdict — almost certainly `contract_gap_found` (the OwlCC `/v1/models` `data[].id` gap), with OwlCoda contracts `pass`. **Record whatever is real.** (If `:8066` is down, skip this step and note it; the read-only run can be done later.)

- [ ] **Step 3: Flag the operability rehearsal for run-now-vs-defer**

The operability rehearsal needs an isolated bench server + 2 real model loads (GBs, minutes) + eviction/restart. **Do not auto-run.** Surface the cost to the user and ask run-now-vs-defer (per the flag-machine-cost rule). The code + safety guards are landed and unit-tested regardless.

- [ ] **Step 4: DoD self-check against spec §7**

Confirm each spec §7 item: per-contract verdicts ✓, `/v1/models` semantic explicit ✓, operability rehearsal code+guards ✓ (live run gated), three-state verdict ✓, pure-function evaluators unit-tested ✓, evidence+repro ✓ (conformance real if :8066 up), runbook ✓, honest wording / promotes nothing ✓.

- [ ] **Step 5: Commit evidence (if captured)**

```bash
git add files/evidence/owlmlx/replacement/r2-control-plane/
git commit -m "bench(r2): read-only consumer-contract conformance evidence (live :8066)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review (filled by plan author)

**Spec coverage:** §0 (A) consumer-contract closure → Tasks 1-3; (B) operability rehearsal → Tasks 4-5; (C) last-mile freeze → Task 6. §2 contracts → Tasks 1-2 (each contract = one evaluator). §3 components → Tasks 1-6. §4 evidence → Tasks 3,5,7. §7 DoD → Task 7 self-check. All covered.

**Placeholder scan:** all code steps contain complete code; the only deliberately deferred action is the *live* operability rehearsal (gated on cost + isolated bench), which is correct per spec §3.2 / Hard Rule 4 — its code and unit tests are fully specified.

**Type consistency:** verdict dicts use `status` ∈ {`pass`,`gap`} (conformance) / {`pass`,`fail`} (operability steps); aggregates use `verdict` ∈ {`passed`,`contract_gap_found`,`rehearsal_failed`}. `PASS`/`GAP` live in the conformance module; `PASS`/`FAIL` in the operability module. Evaluator names referenced in `_CONTRACTS` (Task 3) all defined in Tasks 1-2.
