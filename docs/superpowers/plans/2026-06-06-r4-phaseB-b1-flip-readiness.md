# R4 Phase B · B1 Flip-Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the owlmlx-side **flip-readiness go/no-go gate** + **flipped-state evidence** for staging the OwlCoda default flip (owlmlx-primary + `:8009` fallback retained), plus the consumer flip/rollback runbook. **Promotes nothing; consumer flip EXECUTION stays gated.**

**Architecture:** A thin orchestrator (`scripts/replacement/r4_phaseb_b1_flip_readiness.py`) that **reuses** `r2_control_plane_conformance.run_contracts` (read-only consumer-contract check) + `r4_ops_cutover_pilot.run_probe_readiness` (model/tool-lane readiness), combined by a **pure** `evaluate_flip_readiness(...)` that gates the OwlCoda flip on OwlCoda-side conformance + readiness — the known OwlCC `/v1/models` gap does NOT block (OwlCC repoint is B3). A pure `build_flip_state_evidence(...)` records the post-flip real-traffic coverage + `fallback_used` baseline. Pure functions are unit-tested with no live server (mirrors R2/R4).

**Tech Stack:** Python 3 stdlib (`argparse`/`json`/`urllib`), pytest. `scripts/` is not a package — tests load the module via `importlib.util.spec_from_file_location`; the orchestrator imports its siblings via `sys.path.insert(0, <this dir>)`.

**Spec:** `docs/architect/design/R4-phaseB-b1-flip-readiness-spec.md`
**Reused (verified APIs):**
- `scripts/replacement/r2_control_plane_conformance.py`: `run_contracts(base_url) -> {"verdict": "passed"|"contract_gap_found", "contracts": [{"contract": str, "status": "pass"|"gap", ...}], ...}`. OwlCoda contracts: `owlcoda_gate_openai_models|model_visibility|loaded_inventory|runtime_status`. OwlCC contract: `owlcc_preflight_v1_models` (the lone known gap).
- `scripts/replacement/r4_ops_cutover_pilot.py`: `run_probe_readiness(base_url, model_id, owlmlx_commit, evidence_dir, timeout_s) -> {"verdict": str, "ready": bool, "failures": [str], "artifact_filename", "artifact_path"}` (writes an R4 readiness artifact; its tool-lane check POSTs `/v1/chat/completions` → **loads a model**). Evidence helpers reused: `_write_json`, `_now_iso_utc`, `_now_compact_utc`, `_HONESTY_NOTE`.

**Hard rules (spec §9):** code only in `scripts/replacement/` + `tests/` (no new `owlmlx/` module); `:8009` fallback RETAINED (never deleted in B1); consumer flip is gated runbook only (do NOT auto-edit consumer repos/config); evidence-language calibrated (no sustained/parity/replaces/complete); stage only round-scope files — never `uv.lock`/`owlmlx/speculative/*`/pre-existing dirty.

---

### Task 1: `evaluate_flip_readiness` pure function + tests

**Files:**
- Create: `scripts/replacement/r4_phaseb_b1_flip_readiness.py`
- Test: `tests/test_r4_phaseb_b1_flip_readiness.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_r4_phaseb_b1_flip_readiness.py
import importlib.util
from pathlib import Path

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "replacement" / "r4_phaseb_b1_flip_readiness.py"
_spec = importlib.util.spec_from_file_location("r4_phaseb_b1_flip_readiness", _MOD)
b1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b1)


def _conf(*, owlcoda_gap=False, owlcc_gap=True):
    contracts = [
        {"contract": "owlcoda_gate_openai_models", "status": "gap" if owlcoda_gap else "pass"},
        {"contract": "owlcoda_gate_model_visibility", "status": "pass"},
        {"contract": "owlcc_preflight_v1_models", "status": "gap" if owlcc_gap else "pass"},
    ]
    has_gap = any(c["status"] == "gap" for c in contracts)
    return {"verdict": "contract_gap_found" if has_gap else "passed", "contracts": contracts}


def test_go_when_owlcoda_clean_and_ready_even_with_owlcc_gap():
    v = b1.evaluate_flip_readiness(_conf(owlcoda_gap=False, owlcc_gap=True),
                                   {"ready": True, "failures": [], "verdict": "readiness_passed"})
    assert v["verdict"] == "go", v["blocking"]
    assert v["blocking"] == []


def test_no_go_when_owlcoda_contract_gaps():
    v = b1.evaluate_flip_readiness(_conf(owlcoda_gap=True),
                                   {"ready": True, "failures": [], "verdict": "readiness_passed"})
    assert v["verdict"] == "no_go"
    assert any("owlcoda_gate_openai_models" in b for b in v["blocking"])


def test_no_go_when_readiness_not_ready():
    v = b1.evaluate_flip_readiness(_conf(owlcoda_gap=False),
                                   {"ready": False, "failures": ["model_visible"], "verdict": "pilot_readiness_failed"})
    assert v["verdict"] == "no_go"
    assert any("readiness:model_visible" in b for b in v["blocking"])
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/python -m pytest tests/test_r4_phaseb_b1_flip_readiness.py -v`
Expected: FAIL (module/function not defined).

- [ ] **Step 3: Implement (file header + pure function)**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_r4_phaseb_b1_flip_readiness.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_phaseb_b1_flip_readiness.py tests/test_r4_phaseb_b1_flip_readiness.py
git commit -m "feat(r4-phaseB-b1): flip-readiness pure gate (OwlCoda-gates-only)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: orchestrator (`run_flip_readiness`) + `check` CLI + artifact

**Files:**
- Modify: `scripts/replacement/r4_phaseb_b1_flip_readiness.py`
- Test: `tests/test_r4_phaseb_b1_flip_readiness.py`

- [ ] **Step 1: Write failing test for the artifact builder**

```python
def test_build_flip_readiness_artifact_shape():
    verdict = {"round": "R4-phaseB-B1", "tier": "flip-readiness", "verdict": "go", "blocking": []}
    art = b1.build_flip_readiness_artifact(verdict=verdict, base_url="http://x", model_id="m",
                                           owlmlx_commit="abc", recorded_at="2026-01-01T00:00:00Z")
    assert art["kind"] == "flip_readiness"
    assert art["verdict"] == "go"
    assert art["promotes"] == "nothing"
    assert art["reproduction"]["model_id"] == "m"
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/python -m pytest tests/test_r4_phaseb_b1_flip_readiness.py -k artifact -v`
Expected: FAIL (`AttributeError`).

- [ ] **Step 3: Implement orchestrator + artifact + CLI (append)**

```python
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
    args = parser.parse_args(argv)
    if args.command == "check":
        result = run_flip_readiness(base_url=args.base_url, model_id=args.model_id,
                                    owlmlx_commit=args.owlmlx_commit, evidence_dir=args.evidence_dir,
                                    timeout_s=args.timeout_s)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["verdict"] == "go" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests + smoke the import/CLI**

Run: `.venv/bin/python -m pytest tests/test_r4_phaseb_b1_flip_readiness.py -v`
Expected: PASS (4 tests).
Run: `.venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py --help`
Expected: usage with `check` subcommand, no import error (confirms sibling imports resolve).

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_phaseb_b1_flip_readiness.py tests/test_r4_phaseb_b1_flip_readiness.py
git commit -m "feat(r4-phaseB-b1): flip-readiness orchestrator (reuse R2+R4) + check CLI

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: flipped-state evidence (`build_flip_state_evidence`) + `assemble-flip-state` CLI

**Files:**
- Modify: `scripts/replacement/r4_phaseb_b1_flip_readiness.py`
- Test: `tests/test_r4_phaseb_b1_flip_readiness.py`

- [ ] **Step 1: Write failing tests**

```python
def test_flip_state_inbound_covered_and_fallback_zero():
    cap = {"request_ids": ["a", "b"],
           "owlmlx_inbound": {"served_request_ids": ["a", "b", "c"]},
           "consumer": {"fallback_count": 0, "outbound_hosts": ["127.0.0.1:8066"]}}
    ev = b1.build_flip_state_evidence(flip_readiness={"verdict": "go"}, post_flip_capture=cap,
                                      reproduction={"session_id": "s"}, recorded_at="t")
    assert ev["inbound_coverage_ok"] is True
    assert ev["fallback_used_count"] == 0
    assert ev["fallback_retained"] is True
    assert ev["promotes"] == "nothing"


def test_flip_state_fallback_used_is_honest_signal():
    cap = {"request_ids": ["a", "b"],
           "owlmlx_inbound": {"served_request_ids": ["a"]},
           "consumer": {"fallback_count": 3, "outbound_hosts": ["127.0.0.1:8066", "127.0.0.1:8009"]}}
    ev = b1.build_flip_state_evidence(flip_readiness={"verdict": "go"}, post_flip_capture=cap,
                                      reproduction={"session_id": "s"}, recorded_at="t")
    assert ev["inbound_coverage_ok"] is False   # 'b' not served
    assert ev["fallback_used_count"] == 3        # honest owlmlx-gap signal, not hidden
    assert "not sustained" in ev["honesty"].lower()
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/python -m pytest tests/test_r4_phaseb_b1_flip_readiness.py -k flip_state -v`
Expected: FAIL.

- [ ] **Step 3: Implement (append)**

```python
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
```

Then wire a second subcommand in `main()` (add before `return 1`):

```python
    if args.command == "assemble-flip-state":
        result = run_assemble_flip_state(capture_path=args.capture, evidence_dir=args.evidence_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
```

And register it in the parser (after the `check` parser):

```python
    asm = sub.add_parser("assemble-flip-state", help="Assemble operator-captured post-flip data into flip-state evidence.")
    asm.add_argument("--capture", type=Path, required=True)
    asm.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_r4_phaseb_b1_flip_readiness.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_phaseb_b1_flip_readiness.py tests/test_r4_phaseb_b1_flip_readiness.py
git commit -m "feat(r4-phaseB-b1): flipped-state evidence assembler (fallback baseline, honest)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: consumer flip + rollback runbook

**Files:**
- Create: `docs/architect/design/R4-phaseB-b1-runbook.md`

- [ ] **Step 1: Write the runbook (no placeholders)**

Content must include, concretely:
1. **Pre-flip gate (owlmlx-side, safe-ish but loads a model):**
   ```bash
   .venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py check \
     --base-url http://127.0.0.1:8066 --model-id <model> --owlmlx-commit <sha>
   ```
   `go` (exit 0) → proceed; `no_go` (exit 1) → STOP, the artifact lists blocking items. Cost note: the readiness tool-lane check loads a model.
2. **OwlCC preflight fix (gated, consumer repo `owlcc/src/preflight.ts`):** change the model-availability probe to read `GET /v1/openai/models` (`data[].id`) instead of `GET /v1/models` — owlmlx serves availability truth there (R2 frozen contract). This is the prerequisite that unblocks a future OwlCC repoint (repoint itself is B3). Verify OwlCC's other preflight checks (`/healthz`) are unchanged.
3. **OwlCoda default flip (gated, consumer config — gitignored, environment-specific):** set the owlmlx-gate so owlmlx is the **primary** backend; keep `:8009`/other backends as **fallback** (OwlCoda native cross-backend failover). **Do NOT remove the `:8009` fallback** (that is B3).
4. **Post-flip evidence capture → assemble:**
   ```bash
   .venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py assemble-flip-state \
     --capture <operator-capture.json>
   ```
   where `<operator-capture.json>` = `{flip_readiness, post_flip_capture:{request_ids, owlmlx_inbound:{served_request_ids}, consumer:{fallback_count, outbound_hosts}}, reproduction:{session_id,...}}`. `fallback_used_count>0` is an honest owlmlx-gap signal (feed to R1/diagnosis), not a failure to hide.
5. **Rollback:** revert the OwlCoda config (owlmlx-gate back to the prior default); the OwlCC preflight change is a pure read-the-right-endpoint enhancement (no revert needed). Reversible.
6. **Bounds (verbatim honesty):** B1 = flip staged + initial real traffic served by owlmlx + `:8009` fallback retained. **NOT** sustained (B2), **NOT** `:8009` removed (B3), **NOT** replacement-complete, promotes nothing. verdict stays `not yet replaceable`.

- [ ] **Step 2: Commit**

```bash
git add docs/architect/design/R4-phaseB-b1-runbook.md
git commit -m "docs(r4-phaseB-b1): consumer flip + rollback runbook (fallback retained)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: final verification + cost-flag the live gate

- [ ] **Step 1: Run the B1 test suite**

Run: `.venv/bin/python -m pytest tests/test_r4_phaseb_b1_flip_readiness.py -v`
Expected: PASS (6 tests).

- [ ] **Step 2: Confirm sibling imports + both subcommands parse (no live call)**

Run: `.venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py --help`
Run: `.venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py check --help`
Run: `.venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py assemble-flip-state --help`
Expected: all print usage, no `ImportError` (confirms `r2_control_plane_conformance` + `r4_ops_cutover_pilot` import cleanly).

- [ ] **Step 3: Flag the live `check` run (cost-gated, do NOT auto-run)**

The live `check` reuses R4 readiness, whose tool-lane probe POSTs `/v1/chat/completions` → **loads a model** (the smallest loadable is ~52G; see the operability cost note). **Do not auto-run.** Surface to the user: run-now-vs-defer. The gate code + unit tests are landed regardless; the live `go/no_go` run is the gated step (naturally paired with the actual consumer flip).

- [ ] **Step 4: DoD self-check vs spec §7**

Confirm: flip-readiness gate harness ✓ (go/no_go, OwlCoda-gates-only); flipped-state evidence schema ✓; runbook ✓ (flip + rollback + OwlCC fix); pure-function unit tests ✓; `:8009` not deleted ✓; OwlCC repoint not in this gate ✓; honest wording / promotes nothing ✓.

---

## Self-Review (filled by plan author)

**Spec coverage:** §2 flip-readiness gate → Task 1+2; §4 flipped-state evidence → Task 3; §3 consumer flip + OwlCC fix + rollback → Task 4 (runbook, gated); §7 DoD → Task 5. All covered.

**Placeholder scan:** all code steps carry complete code; the only deferred action is the *live* `check` run (model load, cost-gated) — correct per spec Hard Rule + the operability precedent. The OwlCC code fix + actual flip are gated runbook steps (spec §3 / Hard Rule 4), documented concretely in Task 4, not auto-applied.

**Type consistency:** `evaluate_flip_readiness(conformance, readiness)` consumes the R2 dict (`contracts[].contract/status`) + R4 result dict (`ready`/`failures`) — both verified against the real source. `build_flip_readiness_artifact` / `build_flip_state_evidence` return plain dicts. Verdict vocab: `go`/`no_go` (gate); flip-state uses booleans + counts. Reused R4 internals (`_write_json`, `_now_iso_utc`, `_now_compact_utc`, `_HONESTY_NOTE`) match the verified harness.
