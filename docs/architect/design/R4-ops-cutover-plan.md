# R4 — Ops Cutover (Phase 1: Readiness + Controlled Smoke) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Document grade:** code-grade implementation plan, downstream of the design spec
> [`R4-ops-cutover-spec.md`](R4-ops-cutover-spec.md). Plan-grade source:
> [`runtime13`](../../source-of-truth/runtime13-replacement-rebaseline-verdict.md) §5 (R4).
> **Phase 1 only** — owlmlx-side readiness + ONE controlled non-default OwlCoda agentic smoke.
> **Does NOT** flip a default, **does NOT** remove `:8009` globally, **does NOT** claim
> "replacement complete", **promotes NO capability.** Verdict stays `not yet replaceable`.

**Goal:** Build an owlmlx-internal pilot harness (`scripts/replacement/`, tested in `tests/`) that (1) probes a running owlmlx server for cutover readiness and (2) assembles the controlled-smoke evidence into an honest pilot verdict (`passed` / `pilot_readiness_failed` / `loop_failed`), feeding blocker ④ / gap 5 / R1 findings.

**Architecture:** A single harness module `scripts/replacement/r4_ops_cutover_pilot.py` with two CLI subcommands (`probe-readiness`, `assemble-evidence`). All decision logic lives in **pure functions** (frozen dataclasses + evaluators) that are unit-tested with canned dicts — no live server needed for tests, mirroring the project's `--backend fake` philosophy. The live HTTP I/O is a thin shell over the copied `urllib`-based `_http_json` helper. The controlled OwlCoda smoke itself is an **operator-executed manual procedure** (documented in a runbook); the harness automates readiness + evidence assembly around it. No `owlmlx/` package module is created (AGENTS rule); no OwlCoda/OwlCC repo file is committed.

**Tech Stack:** Python 3.11 (project `.venv`), stdlib only (`argparse`, `urllib`, `json`, `dataclasses`, `time`), pytest with `tmp_path`. Run tests via `uv run pytest` or `.venv/bin/python -m pytest` (the root `conftest.py` warns loudly if off-venv).

---

## Hard Rules (inherited verbatim from the spec §9 — every task must hold these)

1. owlmlx-side code only in owlmlx repo; harness in `scripts/`, tests in `tests/`; **no new `owlmlx/` package module.**
2. Base URL via `OWLMLX_PILOT_BASE_URL` (default example `http://127.0.0.1:8066`); **`:8066` is a default, not a contract** — never hardcode the port as a guarantee. Model id parameterized too.
3. `fallback_used=false` requires **double proof** (consumer-side config snapshot + no-`:8009`-outbound) — and note: **owlmlx never makes outbound `:8009` calls** (it is passive on `:8066`), so the no-`:8009` leg is necessarily **consumer-side**; owlmlx contributes the corroborating *inbound coverage* proof (every pilot request-id was served by owlmlx).
4. Tool lane = **4 independent sub-gates**, each recorded true/false even when one fails; loop "looks done" never substitutes for them.
5. Readiness failure **must still produce an artifact** (`pilot_readiness_failed`) — never "no result".
6. Watermark `red` is a **per-session health gate**, recorded as "this session did not trigger RED" — **never** written as a sustained-stability conclusion.
7. **No default flip, no `replacement complete` claim, no capability promotion.** Evidence-language stays calibrated (a `passed` pilot = "this one controlled session's gates were met", nothing more).

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `scripts/replacement/__init__.py` | namespace package marker (mirrors `scripts/bench/__init__.py`) | Create |
| `scripts/replacement/r4_ops_cutover_pilot.py` | the harness: copied I/O helpers, pure evaluators, artifact builders, two CLI subcommands | Create |
| `tests/test_r4_ops_cutover_pilot.py` | pytest for every pure evaluator + both subcommands (monkeypatched I/O) | Create |
| `docs/architect/design/R4-ops-cutover-runbook.md` | operator procedure for the controlled OwlCoda smoke + the exact captures the harness consumes | Create |
| `files/evidence/owlmlx/replacement/r4-ops-cutover/` | evidence output dir (artifacts + jsonl ledger); created at runtime by the harness | (runtime mkdir) |

Endpoint reference (all served at `$OWLMLX_PILOT_BASE_URL`, verified read-only against the runtime):
- `/healthz` → `{"ok": bool, "readiness": str, "active_model_id": str|None, "model_count": int, ...}` (`owlmlx/runtime/server.py:1192`)
- `/v1/runtime/model-visibility` → `{"visible_model_ids": [...], "blocked_model_ids": [...], "entries": [...], ...}` (`owlmlx/runtime/server.py:1288`)
- `/v1/openai/models` → `{"object": "list", "data": [{"id", "object", "owned_by"}]}` (`owlmlx/runtime/server_routes_openai.py:1405`)
- `/v1/chat/completions` (tool lane) → response `choices[0].message.tool_calls[]`, `choices[0].finish_reason == "tool_calls"`; request `tool_choice="required"` forces a call (`owlmlx/runtime/server_routes_openai.py:690`, forcing grammar `owlmlx/runtime/mlx_native_backend.py:475`)
- `/v1/runtime/monitor/snapshot` → `resources.host_pressure.classification ∈ {"green","yellow","red","fatal","unknown"}` (`owlmlx/runtime/server.py:1341`; builder `owlmlx/runtime_monitor_test_console.py:821`)
- Request-id: response header `x-request-id` (generated `req_<uuid4hex>` if absent); inbound requests logged via the `owlmlx.runtime.server.request` logger as `request.start`/`request.finish` with `owlmlx_request_id` / `owlmlx_http_path` (`owlmlx/runtime/server.py:243`, `owlmlx/runtime/serving_hardening.py:133`). **No ledger endpoint exists** → owlmlx-side inbound proof comes from the captured server log.

---

## Task 1: Scaffold the harness module + copied helpers

**Files:**
- Create: `scripts/replacement/__init__.py`
- Create: `scripts/replacement/r4_ops_cutover_pilot.py`
- Test: `tests/test_r4_ops_cutover_pilot.py`

- [ ] **Step 1: Create the package marker**

Create `scripts/replacement/__init__.py`:

```python
"""owlmlx replacement-campaign (R-series) operator harnesses.

R4 Phase-1 ops-cutover pilot lives here. Per the AGENTS module-as-spec rule,
harness/validation code lives under scripts/ (and tests under tests/), never as
a new owlmlx/ package module.
"""
```

- [ ] **Step 2: Create the harness module skeleton with copied I/O helpers**

Create `scripts/replacement/r4_ops_cutover_pilot.py`. The helpers `_now_compact_utc`, `_now_iso_utc`, `_write_json`, `_append_jsonl`, `_http_json` are copied verbatim from `scripts/runtime_model_release_candidate.py:54-100` (house pattern — stdlib `urllib`, `time.gmtime()`):

```python
#!/usr/bin/env python3
"""R4 Phase-1 ops-cutover pilot harness.

owlmlx-internal readiness probe + controlled-smoke evidence assembler for the
boundary-replacement campaign (runtime13 §5, R4). Phase 1 only: probes a running
owlmlx server for cutover readiness, then assembles one controlled non-default
OwlCoda agentic smoke into an honest pilot verdict.

This harness PROMOTES NOTHING. A `passed` verdict means "this one controlled
pilot session met its gates" — not "replacement complete", not a capability
promotion. The replacement verdict stays `not yet replaceable`.

Subcommands:
  probe-readiness    Probe $OWLMLX_PILOT_BASE_URL; emit readiness_passed OR
                     pilot_readiness_failed artifact (failure ALWAYS produces an
                     artifact).
  assemble-evidence  Combine operator-captured smoke artifacts into the §4
                     evidence schema + pilot verdict (passed / pilot_readiness_failed
                     / loop_failed).
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_BASE_URL = "http://127.0.0.1:8066"
DEFAULT_EVIDENCE_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "replacement"
    / "r4-ops-cutover"
)
EVIDENCE_SURFACE = "owlmlx.replacement.r4_ops_cutover_pilot"
EVIDENCE_VERSION = "v1"

# The tool lane is verified as 4 INDEPENDENT sub-gates (spec constraint #3).
TOOL_LANE_SUBGATES: tuple[str, ...] = (
    "tool_call_emitted",
    "tool_call_executed",
    "tool_result_roundtrip",
    "final_answer_after_tool",
)
# A watermark classification in this set means the per-session health gate tripped.
WATERMARK_RED_CLASSIFICATIONS: frozenset[str] = frozenset({"red", "fatal"})


def _now_compact_utc() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _now_iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True))
        stream.write("\n")


def _http_json(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout_s: float,
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8")
            return int(response.status), json.loads(raw or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body = json.loads(raw or "{}")
        except json.JSONDecodeError:
            body = {"raw": raw}
        return int(exc.code), body
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        return 0, {"error": str(exc)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="R4 Phase-1 ops-cutover pilot harness (owlmlx-internal)."
    )
    parser.add_subparsers(dest="command", required=True)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Create the test file with an import smoke test**

Create `tests/test_r4_ops_cutover_pilot.py`:

```python
from __future__ import annotations

from scripts.replacement import r4_ops_cutover_pilot as pilot


def test_module_imports_and_exposes_constants() -> None:
    assert pilot.DEFAULT_BASE_URL == "http://127.0.0.1:8066"
    assert pilot.EVIDENCE_SURFACE == "owlmlx.replacement.r4_ops_cutover_pilot"
    assert pilot.TOOL_LANE_SUBGATES == (
        "tool_call_emitted",
        "tool_call_executed",
        "tool_result_roundtrip",
        "final_answer_after_tool",
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -v`
Expected: PASS (`test_module_imports_and_exposes_constants`)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/__init__.py scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): scaffold ops-cutover pilot harness + I/O helpers

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Readiness evaluator (pure)

**Files:**
- Modify: `scripts/replacement/r4_ops_cutover_pilot.py` (add `ReadinessCheck`, `ReadinessVerdict`, `evaluate_readiness`)
- Test: `tests/test_r4_ops_cutover_pilot.py`

`evaluate_readiness` takes a `probes` dict (each entry `{"status": int, "body": dict}`) and the target `model_id`, and returns a verdict with one `ReadinessCheck` per gate. Readiness passes only if every check is ok. A failure still yields a full verdict (so the caller can write a `pilot_readiness_failed` artifact — constraint #5).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_r4_ops_cutover_pilot.py`:

```python
def _all_pass_probes(model_id: str = "Qwen3.6-27B") -> dict:
    return {
        "healthz": {"status": 200, "body": {"ok": True, "readiness": "ready"}},
        "model_visibility": {
            "status": 200,
            "body": {"visible_model_ids": [model_id], "blocked_model_ids": []},
        },
        "openai_models": {
            "status": 200,
            "body": {"object": "list", "data": [{"id": model_id}]},
        },
        "tool_lane": {
            "status": 200,
            "body": {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {"id": "call_1", "type": "function",
                                 "function": {"name": "get_weather", "arguments": "{}"}}
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
        },
        "monitor": {
            "status": 200,
            "body": {"resources": {"host_pressure": {"classification": "green"}}},
        },
    }


def test_evaluate_readiness_all_pass() -> None:
    verdict = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    assert verdict.ready is True
    assert verdict.verdict == "readiness_passed"
    assert verdict.failures == ()
    assert {c.name for c in verdict.checks} == {
        "healthz_ok",
        "model_visible",
        "model_in_openai_models",
        "tool_lane_live",
        "monitor_reachable",
    }


def test_evaluate_readiness_model_not_visible_fails_with_artifact_verdict() -> None:
    probes = _all_pass_probes()
    probes["model_visibility"]["body"]["visible_model_ids"] = ["some-other-model"]
    verdict = pilot.evaluate_readiness(probes, model_id="Qwen3.6-27B")
    assert verdict.ready is False
    assert verdict.verdict == "pilot_readiness_failed"
    assert "model_visible" in verdict.failures


def test_evaluate_readiness_tool_lane_empty_fails() -> None:
    probes = _all_pass_probes()
    probes["tool_lane"]["body"]["choices"][0]["message"]["tool_calls"] = []
    verdict = pilot.evaluate_readiness(probes, model_id="Qwen3.6-27B")
    assert verdict.ready is False
    assert "tool_lane_live" in verdict.failures
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k readiness -v`
Expected: FAIL with `AttributeError: module ... has no attribute 'evaluate_readiness'`

- [ ] **Step 3: Implement the evaluator**

Add to `scripts/replacement/r4_ops_cutover_pilot.py` (above `main`):

```python
@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    name: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReadinessVerdict:
    verdict: str  # "readiness_passed" | "pilot_readiness_failed"
    ready: bool
    checks: tuple[ReadinessCheck, ...]
    failures: tuple[str, ...]


def _tool_calls_from_chat_body(body: Mapping[str, Any]) -> list[Any]:
    choices = body.get("choices") or []
    if not choices:
        return []
    message = choices[0].get("message") or {}
    return list(message.get("tool_calls") or [])


def evaluate_readiness(
    probes: Mapping[str, Any], *, model_id: str
) -> ReadinessVerdict:
    """Evaluate cutover readiness from probe responses (pure; no I/O).

    `probes` maps probe name -> {"status": int, "body": dict}. Readiness passes
    only when every check is ok. A failing input still returns a full verdict so
    the caller can persist a `pilot_readiness_failed` artifact (constraint #5).
    """

    def _entry(name: str) -> tuple[int, dict[str, Any]]:
        entry = probes.get(name) or {}
        return int(entry.get("status") or 0), dict(entry.get("body") or {})

    checks: list[ReadinessCheck] = []

    hz_status, hz_body = _entry("healthz")
    checks.append(
        ReadinessCheck(
            "healthz_ok",
            hz_status == 200 and bool(hz_body.get("ok")),
            {"status": hz_status, "readiness": hz_body.get("readiness")},
        )
    )

    mv_status, mv_body = _entry("model_visibility")
    visible = list(mv_body.get("visible_model_ids") or [])
    checks.append(
        ReadinessCheck(
            "model_visible",
            mv_status == 200 and model_id in visible,
            {"status": mv_status, "visible_model_ids": visible},
        )
    )

    om_status, om_body = _entry("openai_models")
    openai_ids = [str(m.get("id")) for m in (om_body.get("data") or [])]
    checks.append(
        ReadinessCheck(
            "model_in_openai_models",
            om_status == 200 and model_id in openai_ids,
            {"status": om_status, "ids": openai_ids},
        )
    )

    tl_status, tl_body = _entry("tool_lane")
    tool_calls = _tool_calls_from_chat_body(tl_body)
    checks.append(
        ReadinessCheck(
            "tool_lane_live",
            tl_status == 200 and len(tool_calls) > 0,
            {"status": tl_status, "tool_call_count": len(tool_calls)},
        )
    )

    mon_status, mon_body = _entry("monitor")
    classification = (
        (mon_body.get("resources") or {}).get("host_pressure") or {}
    ).get("classification")
    checks.append(
        ReadinessCheck(
            "monitor_reachable",
            mon_status == 200 and classification is not None,
            {"status": mon_status, "classification": classification},
        )
    )

    failures = tuple(c.name for c in checks if not c.ok)
    ready = not failures
    return ReadinessVerdict(
        verdict="readiness_passed" if ready else "pilot_readiness_failed",
        ready=ready,
        checks=tuple(checks),
        failures=failures,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k readiness -v`
Expected: PASS (3 readiness tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): readiness evaluator (failure still yields a verdict)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Tool-lane 4-sub-gate evaluator (pure, constraint #3)

**Files:**
- Modify: `scripts/replacement/r4_ops_cutover_pilot.py` (add `ToolLaneVerdict`, `evaluate_tool_lane`)
- Test: `tests/test_r4_ops_cutover_pilot.py`

The agentic loop "looking done" must NOT substitute for the 4 sub-gates. Each sub-gate is recorded independently (true/false) even when one fails.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_r4_ops_cutover_pilot.py`:

```python
def test_evaluate_tool_lane_all_true_passes() -> None:
    verdict = pilot.evaluate_tool_lane(
        {
            "tool_call_emitted": True,
            "tool_call_executed": True,
            "tool_result_roundtrip": True,
            "final_answer_after_tool": True,
        }
    )
    assert verdict.passed is True
    assert verdict.failing == ()
    assert verdict.subgates == {
        "tool_call_emitted": True,
        "tool_call_executed": True,
        "tool_result_roundtrip": True,
        "final_answer_after_tool": True,
    }


def test_evaluate_tool_lane_one_false_fails_and_records_all_four() -> None:
    verdict = pilot.evaluate_tool_lane(
        {
            "tool_call_emitted": True,
            "tool_call_executed": True,
            "tool_result_roundtrip": False,
            "final_answer_after_tool": True,
        }
    )
    assert verdict.passed is False
    assert verdict.failing == ("tool_result_roundtrip",)
    # all four sub-gates are still present in the record
    assert set(verdict.subgates) == set(pilot.TOOL_LANE_SUBGATES)


def test_evaluate_tool_lane_missing_subgate_is_treated_false() -> None:
    verdict = pilot.evaluate_tool_lane({"tool_call_emitted": True})
    assert verdict.passed is False
    assert "tool_call_executed" in verdict.failing
    assert verdict.subgates["final_answer_after_tool"] is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k tool_lane -v`
Expected: FAIL with `AttributeError: ... 'evaluate_tool_lane'`

- [ ] **Step 3: Implement the evaluator**

Add to `scripts/replacement/r4_ops_cutover_pilot.py`:

```python
@dataclass(frozen=True, slots=True)
class ToolLaneVerdict:
    passed: bool
    subgates: dict[str, bool]
    failing: tuple[str, ...]


def evaluate_tool_lane(subgates: Mapping[str, bool]) -> ToolLaneVerdict:
    """Evaluate the 4 INDEPENDENT tool-lane sub-gates (constraint #3).

    Every sub-gate is normalized into the record (missing -> False), so the
    artifact always carries all four booleans. The lane passes only when all
    four are True.
    """
    normalized = {name: bool(subgates.get(name, False)) for name in TOOL_LANE_SUBGATES}
    failing = tuple(name for name in TOOL_LANE_SUBGATES if not normalized[name])
    return ToolLaneVerdict(
        passed=not failing,
        subgates=normalized,
        failing=failing,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k tool_lane -v`
Expected: PASS (3 tool-lane tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): tool-lane 4-sub-gate evaluator (independent record)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Fallback double-proof evaluator (pure, constraint #2)

**Files:**
- Modify: `scripts/replacement/r4_ops_cutover_pilot.py` (add `FallbackProof`, `evaluate_fallback_proof`)
- Test: `tests/test_r4_ops_cutover_pilot.py`

`fallback_used=false` is proven only when all three legs hold: (a) the consumer config snapshot points at the pilot base URL with fallback disabled and no `:8009`; (b) consumer-side outbound shows `fallback_count == 0` and every outbound host is the pilot host; (c) owlmlx-side inbound coverage — every pilot request-id appears in the captured owlmlx request log. (a)+(b) are the consumer-side no-`:8009` proof; (c) is owlmlx's corroboration (owlmlx itself never calls `:8009`).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_r4_ops_cutover_pilot.py`:

```python
def _proof_inputs():
    return dict(
        config_snapshot={
            "base_url": "http://127.0.0.1:8066",
            "provider": "owlmlx",
            "fallback_enabled": False,
        },
        consumer_outbound={
            "fallback_count": 0,
            "outbound_hosts": ["127.0.0.1:8066"],
        },
        owlmlx_inbound={"served_request_ids": ["req_a", "req_b", "req_c"]},
        pilot_request_ids=["req_a", "req_b"],
        pilot_base_url="http://127.0.0.1:8066",
    )


def test_evaluate_fallback_proof_all_legs_pass() -> None:
    proof = pilot.evaluate_fallback_proof(**_proof_inputs())
    assert proof.proven is True
    assert proof.config_ok is True
    assert proof.consumer_outbound_ok is True
    assert proof.owlmlx_inbound_ok is True
    assert proof.reasons == ()


def test_evaluate_fallback_proof_config_points_at_8009_fails() -> None:
    args = _proof_inputs()
    args["config_snapshot"]["base_url"] = "http://127.0.0.1:8009"
    proof = pilot.evaluate_fallback_proof(**args)
    assert proof.proven is False
    assert proof.config_ok is False
    assert any("8009" in r or "base_url" in r for r in proof.reasons)


def test_evaluate_fallback_proof_outbound_fallback_count_nonzero_fails() -> None:
    args = _proof_inputs()
    args["consumer_outbound"]["fallback_count"] = 2
    proof = pilot.evaluate_fallback_proof(**args)
    assert proof.proven is False
    assert proof.consumer_outbound_ok is False


def test_evaluate_fallback_proof_inbound_coverage_gap_fails() -> None:
    args = _proof_inputs()
    args["owlmlx_inbound"]["served_request_ids"] = ["req_a"]  # missing req_b
    proof = pilot.evaluate_fallback_proof(**args)
    assert proof.proven is False
    assert proof.owlmlx_inbound_ok is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k fallback -v`
Expected: FAIL with `AttributeError: ... 'evaluate_fallback_proof'`

- [ ] **Step 3: Implement the evaluator**

Add to `scripts/replacement/r4_ops_cutover_pilot.py`:

```python
@dataclass(frozen=True, slots=True)
class FallbackProof:
    proven: bool
    config_ok: bool
    consumer_outbound_ok: bool
    owlmlx_inbound_ok: bool
    reasons: tuple[str, ...]


def _host_of(url: str) -> str:
    # "http://127.0.0.1:8066/v1/..." -> "127.0.0.1:8066"
    rest = url.split("://", 1)[-1]
    return rest.split("/", 1)[0]


def evaluate_fallback_proof(
    *,
    config_snapshot: Mapping[str, Any],
    consumer_outbound: Mapping[str, Any],
    owlmlx_inbound: Mapping[str, Any],
    pilot_request_ids: Sequence[str],
    pilot_base_url: str,
) -> FallbackProof:
    """Double-proof that the pilot used owlmlx with NO `:8009` fallback (#2).

    Leg (a) consumer config snapshot, (b) consumer outbound, (c) owlmlx inbound
    coverage. owlmlx never makes outbound `:8009` calls, so the no-`:8009` leg is
    consumer-side; owlmlx contributes inbound coverage as corroboration.
    """
    reasons: list[str] = []
    pilot_host = _host_of(pilot_base_url)

    # Leg (a): consumer config points at the pilot, fallback disabled, not :8009.
    cfg_base = str(config_snapshot.get("base_url") or "")
    cfg_host = _host_of(cfg_base)
    cfg_fallback_disabled = config_snapshot.get("fallback_enabled") is False
    config_ok = cfg_host == pilot_host and ":8009" not in cfg_base and cfg_fallback_disabled
    if cfg_host != pilot_host:
        reasons.append(f"config base_url host {cfg_host!r} != pilot host {pilot_host!r}")
    if ":8009" in cfg_base:
        reasons.append("config base_url still references :8009")
    if not cfg_fallback_disabled:
        reasons.append("config fallback_enabled is not False")

    # Leg (b): consumer outbound — no fallback, only the pilot host.
    fallback_count = int(consumer_outbound.get("fallback_count", -1))
    outbound_hosts = [str(h) for h in (consumer_outbound.get("outbound_hosts") or [])]
    hosts_ok = bool(outbound_hosts) and all(h == pilot_host for h in outbound_hosts)
    consumer_outbound_ok = fallback_count == 0 and hosts_ok
    if fallback_count != 0:
        reasons.append(f"consumer fallback_count={fallback_count} (expected 0)")
    if not hosts_ok:
        reasons.append(f"consumer outbound_hosts {outbound_hosts} not all == {pilot_host!r}")

    # Leg (c): owlmlx inbound coverage — every pilot request-id was served.
    served = set(str(r) for r in (owlmlx_inbound.get("served_request_ids") or []))
    pilot_ids = set(str(r) for r in pilot_request_ids)
    missing = sorted(pilot_ids - served)
    owlmlx_inbound_ok = bool(pilot_ids) and not missing
    if not pilot_ids:
        reasons.append("no pilot_request_ids supplied for inbound coverage")
    if missing:
        reasons.append(f"owlmlx inbound log missing request_ids: {missing}")

    proven = config_ok and consumer_outbound_ok and owlmlx_inbound_ok
    return FallbackProof(
        proven=proven,
        config_ok=config_ok,
        consumer_outbound_ok=consumer_outbound_ok,
        owlmlx_inbound_ok=owlmlx_inbound_ok,
        reasons=tuple(reasons),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k fallback -v`
Expected: PASS (4 fallback tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): fallback double-proof evaluator (consumer + owlmlx inbound)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Watermark health-gate evaluator (pure, constraint #6)

**Files:**
- Modify: `scripts/replacement/r4_ops_cutover_pilot.py` (add `WatermarkHealth`, `evaluate_watermark_health`)
- Test: `tests/test_r4_ops_cutover_pilot.py`

`watermark_red_observed` is a **per-session health gate**. The artifact's `interpretation` field states plainly it is NOT a sustained-stability claim (that is R4 Phase B / soak).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_r4_ops_cutover_pilot.py`:

```python
def test_evaluate_watermark_health_no_red() -> None:
    health = pilot.evaluate_watermark_health(["green", "green", "yellow"])
    assert health.watermark_red_observed is False
    assert health.classifications_seen == ("green", "yellow")
    assert "not" in health.interpretation.lower()
    assert "stability" in health.interpretation.lower()


def test_evaluate_watermark_health_red_trips_gate() -> None:
    health = pilot.evaluate_watermark_health(["green", "red"])
    assert health.watermark_red_observed is True
    assert "red" in health.classifications_seen


def test_evaluate_watermark_health_fatal_counts_as_red() -> None:
    health = pilot.evaluate_watermark_health(["fatal"])
    assert health.watermark_red_observed is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k watermark -v`
Expected: FAIL with `AttributeError: ... 'evaluate_watermark_health'`

- [ ] **Step 3: Implement the evaluator**

Add to `scripts/replacement/r4_ops_cutover_pilot.py`:

```python
@dataclass(frozen=True, slots=True)
class WatermarkHealth:
    watermark_red_observed: bool
    classifications_seen: tuple[str, ...]
    interpretation: str


def evaluate_watermark_health(classifications: Sequence[str]) -> WatermarkHealth:
    """Per-session memory-watermark HEALTH gate (constraint #6).

    `watermark_red_observed=False` means "this session did not trigger RED" —
    it is explicitly NOT a sustained-stability conclusion (that is R4 Phase B).
    """
    seen = tuple(dict.fromkeys(str(c).lower() for c in classifications))
    red = any(c in WATERMARK_RED_CLASSIFICATIONS for c in seen)
    interpretation = (
        "RED/FATAL observed in this session — health gate tripped. "
        if red
        else "This session did not trigger RED. "
    ) + "Health gate for THIS pilot session only; NOT a sustained-stability claim (see R4 Phase B / soak)."
    return WatermarkHealth(
        watermark_red_observed=red,
        classifications_seen=seen,
        interpretation=interpretation,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k watermark -v`
Expected: PASS (3 watermark tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): watermark per-session health-gate evaluator

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Pilot verdict synthesis + artifact builders (pure)

**Files:**
- Modify: `scripts/replacement/r4_ops_cutover_pilot.py` (add `PilotVerdict`, `build_pilot_verdict`, `build_readiness_artifact`, `build_pilot_artifact`)
- Test: `tests/test_r4_ops_cutover_pilot.py`

The pilot verdict is exactly one of `passed` / `pilot_readiness_failed` / `loop_failed`. Precedence: readiness failure dominates; then loop-not-completed; then any of {tool-lane fail, fallback unproven, watermark RED} → `loop_failed`; else `passed`. A `passed` verdict carries an explicit honesty note.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_r4_ops_cutover_pilot.py`:

```python
def _passing_components():
    readiness = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    tool_lane = pilot.evaluate_tool_lane(
        {k: True for k in pilot.TOOL_LANE_SUBGATES}
    )
    fallback = pilot.evaluate_fallback_proof(**_proof_inputs())
    watermark = pilot.evaluate_watermark_health(["green", "green"])
    return readiness, tool_lane, fallback, watermark


def test_build_pilot_verdict_passed() -> None:
    readiness, tool_lane, fallback, watermark = _passing_components()
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "passed"
    assert verdict.reasons == ()


def test_build_pilot_verdict_readiness_failure_dominates() -> None:
    probes = _all_pass_probes()
    probes["healthz"]["body"]["ok"] = False
    readiness = pilot.evaluate_readiness(probes, model_id="Qwen3.6-27B")
    _, tool_lane, fallback, watermark = _passing_components()
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "pilot_readiness_failed"


def test_build_pilot_verdict_tool_lane_fail_is_loop_failed() -> None:
    readiness, _, fallback, watermark = _passing_components()
    tool_lane = pilot.evaluate_tool_lane(
        {**{k: True for k in pilot.TOOL_LANE_SUBGATES}, "final_answer_after_tool": False}
    )
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "loop_failed"
    assert any("final_answer_after_tool" in r for r in verdict.reasons)


def test_build_pilot_verdict_watermark_red_is_loop_failed() -> None:
    readiness, tool_lane, fallback, _ = _passing_components()
    watermark = pilot.evaluate_watermark_health(["green", "red"])
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "loop_failed"
    assert any("watermark" in r.lower() for r in verdict.reasons)


def test_build_readiness_artifact_shape() -> None:
    readiness = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    artifact = pilot.build_readiness_artifact(
        verdict=readiness,
        base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B",
        owlmlx_commit="abc1234",
        recorded_at="2026-06-03T00:00:00Z",
    )
    assert artifact["surface"] == pilot.EVIDENCE_SURFACE
    assert artifact["version"] == pilot.EVIDENCE_VERSION
    assert artifact["kind"] == "readiness"
    assert artifact["verdict"] == "readiness_passed"
    assert artifact["reproduction"]["owlmlx_commit"] == "abc1234"
    assert artifact["promotes"] == "nothing"


def test_build_pilot_artifact_shape_records_all_subgates() -> None:
    readiness, tool_lane, fallback, watermark = _passing_components()
    verdict = pilot.build_pilot_verdict(
        readiness=readiness, tool_lane=tool_lane, fallback=fallback,
        watermark=watermark, loop_completed=True,
    )
    reproduction = {
        "launch_command": "uv run python -m owlmlx.runtime.server ...",
        "env": {"OWLMLX_PILOT_BASE_URL": "http://127.0.0.1:8066"},
        "owlmlx_commit": "abc1234",
        "base_url": "http://127.0.0.1:8066",
        "model_id": "Qwen3.6-27B",
        "session_id": "pilot-001",
        "request_ids": ["req_a", "req_b"],
    }
    artifact = pilot.build_pilot_artifact(
        pilot_verdict=verdict,
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        reproduction=reproduction,
        recorded_at="2026-06-03T00:00:00Z",
    )
    assert artifact["kind"] == "pilot"
    assert artifact["verdict"] == "passed"
    assert set(artifact["tool_lane"]["subgates"]) == set(pilot.TOOL_LANE_SUBGATES)
    assert artifact["fallback"]["fallback_used"] is False
    assert artifact["watermark"]["watermark_red_observed"] is False
    assert artifact["reproduction"]["request_ids"] == ["req_a", "req_b"]
    assert "replacement complete" in artifact["honesty_note"].lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k "verdict or artifact" -v`
Expected: FAIL with `AttributeError: ... 'build_pilot_verdict'`

- [ ] **Step 3: Implement verdict + artifact builders**

Add to `scripts/replacement/r4_ops_cutover_pilot.py`:

```python
_HONESTY_NOTE = (
    "A `passed` verdict means this ONE controlled pilot session met its gates. "
    "It does NOT claim replacement complete, does NOT flip any default, and "
    "promotes NO capability. The replacement verdict stays `not yet replaceable`."
)


@dataclass(frozen=True, slots=True)
class PilotVerdict:
    verdict: str  # "passed" | "pilot_readiness_failed" | "loop_failed"
    reasons: tuple[str, ...]


def build_pilot_verdict(
    *,
    readiness: ReadinessVerdict,
    tool_lane: ToolLaneVerdict,
    fallback: FallbackProof,
    watermark: WatermarkHealth,
    loop_completed: bool,
) -> PilotVerdict:
    """Synthesize the single honest pilot verdict (precedence-ordered)."""
    if not readiness.ready:
        return PilotVerdict(
            "pilot_readiness_failed",
            tuple(f"readiness:{name}" for name in readiness.failures),
        )

    reasons: list[str] = []
    if not loop_completed:
        reasons.append("agentic loop did not complete (operator-reported)")
    if not tool_lane.passed:
        reasons.extend(f"tool_lane:{name}" for name in tool_lane.failing)
    if not fallback.proven:
        reasons.extend(f"fallback:{reason}" for reason in fallback.reasons)
    if watermark.watermark_red_observed:
        reasons.append("watermark health gate tripped (RED/FATAL this session)")

    if reasons:
        return PilotVerdict("loop_failed", tuple(reasons))
    return PilotVerdict("passed", ())


def _readiness_to_dict(verdict: ReadinessVerdict) -> dict[str, Any]:
    return {
        "verdict": verdict.verdict,
        "ready": verdict.ready,
        "failures": list(verdict.failures),
        "checks": [
            {"name": c.name, "ok": c.ok, "detail": c.detail} for c in verdict.checks
        ],
    }


def build_readiness_artifact(
    *,
    verdict: ReadinessVerdict,
    base_url: str,
    model_id: str,
    owlmlx_commit: str,
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface": EVIDENCE_SURFACE,
        "version": EVIDENCE_VERSION,
        "kind": "readiness",
        "recorded_at": recorded_at,
        "verdict": verdict.verdict,
        "readiness": _readiness_to_dict(verdict),
        "reproduction": {
            "base_url": base_url,
            "model_id": model_id,
            "owlmlx_commit": owlmlx_commit,
        },
        "promotes": "nothing",
        "honesty_note": _HONESTY_NOTE,
    }


def build_pilot_artifact(
    *,
    pilot_verdict: PilotVerdict,
    readiness: ReadinessVerdict,
    tool_lane: ToolLaneVerdict,
    fallback: FallbackProof,
    watermark: WatermarkHealth,
    reproduction: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface": EVIDENCE_SURFACE,
        "version": EVIDENCE_VERSION,
        "kind": "pilot",
        "recorded_at": recorded_at,
        "verdict": pilot_verdict.verdict,
        "verdict_reasons": list(pilot_verdict.reasons),
        "readiness": _readiness_to_dict(readiness),
        "tool_lane": {
            "passed": tool_lane.passed,
            "subgates": dict(tool_lane.subgates),
            "failing": list(tool_lane.failing),
        },
        "fallback": {
            "fallback_used": not fallback.proven,
            "proven_not_used": fallback.proven,
            "config_ok": fallback.config_ok,
            "consumer_outbound_ok": fallback.consumer_outbound_ok,
            "owlmlx_inbound_ok": fallback.owlmlx_inbound_ok,
            "reasons": list(fallback.reasons),
        },
        "watermark": {
            "watermark_red_observed": watermark.watermark_red_observed,
            "classifications_seen": list(watermark.classifications_seen),
            "interpretation": watermark.interpretation,
        },
        "reproduction": dict(reproduction),
        "promotes": "nothing",
        "honesty_note": _HONESTY_NOTE,
    }
```

`fallback_used` is the negation of `fallback.proven` (i.e. proof that fallback was NOT used).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k "verdict or artifact" -v`
Expected: PASS (6 verdict/artifact tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): pilot verdict synthesis + readiness/pilot artifact builders

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: `probe-readiness` subcommand (live I/O shell + monkeypatched test)

**Files:**
- Modify: `scripts/replacement/r4_ops_cutover_pilot.py` (add `_probe_live`, `run_probe_readiness`, wire subparser)
- Test: `tests/test_r4_ops_cutover_pilot.py`

The live shell calls the five endpoints via `_http_json`, builds the `probes` dict, runs `evaluate_readiness`, and ALWAYS writes an artifact (`readiness_passed` or `pilot_readiness_failed`). Tests monkeypatch `_http_json` so no live server is needed.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_r4_ops_cutover_pilot.py`:

```python
import json as _json


def _install_fake_http(monkeypatch, model_id: str, *, tool_calls: bool = True):
    def fake_http_json(*, method, url, payload=None, timeout_s):
        if url.endswith("/healthz"):
            return 200, {"ok": True, "readiness": "ready"}
        if url.endswith("/v1/runtime/model-visibility"):
            return 200, {"visible_model_ids": [model_id], "blocked_model_ids": []}
        if url.endswith("/v1/openai/models"):
            return 200, {"object": "list", "data": [{"id": model_id}]}
        if url.endswith("/v1/chat/completions"):
            calls = [{"id": "c1", "type": "function",
                      "function": {"name": "t", "arguments": "{}"}}] if tool_calls else []
            return 200, {"choices": [{"message": {"tool_calls": calls},
                                      "finish_reason": "tool_calls"}]}
        if url.endswith("/v1/runtime/monitor/snapshot"):
            return 200, {"resources": {"host_pressure": {"classification": "green"}}}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(pilot, "_http_json", fake_http_json)


def test_run_probe_readiness_writes_passed_artifact(tmp_path, monkeypatch) -> None:
    _install_fake_http(monkeypatch, "Qwen3.6-27B")
    result = pilot.run_probe_readiness(
        base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B",
        owlmlx_commit="abc1234",
        evidence_dir=tmp_path,
        timeout_s=5.0,
    )
    assert result["verdict"] == "readiness_passed"
    artifact_path = tmp_path / result["artifact_filename"]
    assert artifact_path.exists()
    written = _json.loads(artifact_path.read_text())
    assert written["kind"] == "readiness"
    assert written["verdict"] == "readiness_passed"


def test_run_probe_readiness_failure_still_writes_artifact(tmp_path, monkeypatch) -> None:
    _install_fake_http(monkeypatch, "Qwen3.6-27B", tool_calls=False)
    result = pilot.run_probe_readiness(
        base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B",
        owlmlx_commit="abc1234",
        evidence_dir=tmp_path,
        timeout_s=5.0,
    )
    assert result["verdict"] == "pilot_readiness_failed"
    assert "tool_lane_live" in result["failures"]
    artifact_path = tmp_path / result["artifact_filename"]
    assert artifact_path.exists()  # constraint #5: failure ALWAYS yields an artifact
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k probe_readiness -v`
Expected: FAIL with `AttributeError: ... 'run_probe_readiness'`

- [ ] **Step 3: Implement the live shell + runner**

Add to `scripts/replacement/r4_ops_cutover_pilot.py`:

```python
def _probe_live(base_url: str, *, model_id: str, timeout_s: float) -> dict[str, Any]:
    base = base_url.rstrip("/")

    hz_status, hz_body = _http_json(method="GET", url=f"{base}/healthz", timeout_s=timeout_s)
    mv_status, mv_body = _http_json(
        method="GET", url=f"{base}/v1/runtime/model-visibility", timeout_s=timeout_s
    )
    om_status, om_body = _http_json(
        method="GET", url=f"{base}/v1/openai/models", timeout_s=timeout_s
    )
    tl_status, tl_body = _http_json(
        method="POST",
        url=f"{base}/v1/chat/completions",
        payload={
            "model": model_id,
            "messages": [{"role": "user", "content": "What is the weather in Paris?"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather for a city.",
                        "parameters": {
                            "type": "object",
                            "properties": {"city": {"type": "string"}},
                            "required": ["city"],
                        },
                    },
                }
            ],
            "tool_choice": "required",
            "max_tokens": 64,
            "stream": False,
        },
        timeout_s=timeout_s,
    )
    mon_status, mon_body = _http_json(
        method="GET", url=f"{base}/v1/runtime/monitor/snapshot", timeout_s=timeout_s
    )
    return {
        "healthz": {"status": hz_status, "body": hz_body},
        "model_visibility": {"status": mv_status, "body": mv_body},
        "openai_models": {"status": om_status, "body": om_body},
        "tool_lane": {"status": tl_status, "body": tl_body},
        "monitor": {"status": mon_status, "body": mon_body},
    }


def run_probe_readiness(
    *,
    base_url: str,
    model_id: str,
    owlmlx_commit: str,
    evidence_dir: Path,
    timeout_s: float,
) -> dict[str, Any]:
    probes = _probe_live(base_url, model_id=model_id, timeout_s=timeout_s)
    verdict = evaluate_readiness(probes, model_id=model_id)
    recorded_at = _now_iso_utc()
    artifact = build_readiness_artifact(
        verdict=verdict,
        base_url=base_url,
        model_id=model_id,
        owlmlx_commit=owlmlx_commit,
        recorded_at=recorded_at,
    )
    artifact["probes"] = probes  # raw probe payloads for audit
    safe_model = model_id.strip("/").replace("/", "-")
    filename = f"{_now_compact_utc()}-readiness-{verdict.verdict}-{safe_model}.json"
    _write_json(evidence_dir / filename, artifact)
    return {
        "verdict": verdict.verdict,
        "ready": verdict.ready,
        "failures": list(verdict.failures),
        "artifact_filename": filename,
        "artifact_path": str(evidence_dir / filename),
    }
```

Then replace the body of `main` to wire the subparser:

```python
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="R4 Phase-1 ops-cutover pilot harness (owlmlx-internal)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser(
        "probe-readiness",
        help="Probe a running owlmlx server; emit readiness_passed OR pilot_readiness_failed.",
    )
    probe.add_argument(
        "--base-url",
        default=os.environ.get("OWLMLX_PILOT_BASE_URL", DEFAULT_BASE_URL),
        help="owlmlx base URL (default $OWLMLX_PILOT_BASE_URL or %(default)s; port is NOT a contract).",
    )
    probe.add_argument(
        "--model-id",
        default=os.environ.get("OWLMLX_PILOT_MODEL_ID"),
        required=os.environ.get("OWLMLX_PILOT_MODEL_ID") is None,
        help="Pilot model id (default $OWLMLX_PILOT_MODEL_ID).",
    )
    probe.add_argument("--owlmlx-commit", required=True, help="owlmlx git commit under test.")
    probe.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    probe.add_argument("--timeout-s", type=float, default=60.0)

    args = parser.parse_args(argv)

    if args.command == "probe-readiness":
        result = run_probe_readiness(
            base_url=args.base_url,
            model_id=args.model_id,
            owlmlx_commit=args.owlmlx_commit,
            evidence_dir=args.evidence_dir,
            timeout_s=args.timeout_s,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ready"] else 1

    return 0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k probe_readiness -v`
Expected: PASS (2 probe-readiness tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): probe-readiness subcommand (live shell, always writes artifact)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: `assemble-evidence` subcommand

**Files:**
- Modify: `scripts/replacement/r4_ops_cutover_pilot.py` (add `run_assemble_evidence`, wire subparser)
- Test: `tests/test_r4_ops_cutover_pilot.py`

`assemble-evidence` reads ONE operator-captured input JSON file (the controlled-smoke captures) plus a readiness artifact, runs every evaluator, and writes the pilot artifact + appends a jsonl ledger row.

The input JSON file schema (operator fills it from the runbook captures):

```json
{
  "loop_completed": true,
  "tool_lane_subgates": {
    "tool_call_emitted": true, "tool_call_executed": true,
    "tool_result_roundtrip": true, "final_answer_after_tool": true
  },
  "fallback": {
    "config_snapshot": {"base_url": "http://127.0.0.1:8066", "provider": "owlmlx", "fallback_enabled": false},
    "consumer_outbound": {"fallback_count": 0, "outbound_hosts": ["127.0.0.1:8066"]},
    "owlmlx_inbound": {"served_request_ids": ["req_a", "req_b"]}
  },
  "watermark_classifications": ["green", "green", "yellow"],
  "reproduction": {
    "launch_command": "uv run python -m owlmlx.runtime.server ...",
    "env": {"OWLMLX_PILOT_BASE_URL": "http://127.0.0.1:8066", "OWLMLX_PILOT_MODEL_ID": "Qwen3.6-27B"},
    "owlmlx_commit": "abc1234",
    "base_url": "http://127.0.0.1:8066",
    "model_id": "Qwen3.6-27B",
    "session_id": "pilot-001",
    "request_ids": ["req_a", "req_b"]
  }
}
```

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_r4_ops_cutover_pilot.py`:

```python
def _write_capture(tmp_path, *, override=None):
    capture = {
        "loop_completed": True,
        "tool_lane_subgates": {k: True for k in pilot.TOOL_LANE_SUBGATES},
        "fallback": {
            "config_snapshot": {"base_url": "http://127.0.0.1:8066",
                                 "provider": "owlmlx", "fallback_enabled": False},
            "consumer_outbound": {"fallback_count": 0, "outbound_hosts": ["127.0.0.1:8066"]},
            "owlmlx_inbound": {"served_request_ids": ["req_a", "req_b"]},
        },
        "watermark_classifications": ["green", "green"],
        "reproduction": {
            "launch_command": "uv run python -m owlmlx.runtime.server",
            "env": {"OWLMLX_PILOT_BASE_URL": "http://127.0.0.1:8066"},
            "owlmlx_commit": "abc1234",
            "base_url": "http://127.0.0.1:8066",
            "model_id": "Qwen3.6-27B",
            "session_id": "pilot-001",
            "request_ids": ["req_a", "req_b"],
        },
    }
    if override:
        override(capture)
    path = tmp_path / "capture.json"
    path.write_text(_json.dumps(capture))
    return path


def _write_passing_readiness_artifact(tmp_path):
    readiness = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    artifact = pilot.build_readiness_artifact(
        verdict=readiness, base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B", owlmlx_commit="abc1234",
        recorded_at="2026-06-03T00:00:00Z",
    )
    path = tmp_path / "readiness.json"
    path.write_text(_json.dumps(artifact))
    return path


def test_run_assemble_evidence_passed(tmp_path) -> None:
    capture = _write_capture(tmp_path)
    readiness = _write_passing_readiness_artifact(tmp_path)
    result = pilot.run_assemble_evidence(
        capture_path=capture,
        readiness_artifact_path=readiness,
        pilot_base_url="http://127.0.0.1:8066",
        evidence_dir=tmp_path,
    )
    assert result["verdict"] == "passed"
    artifact = _json.loads((tmp_path / result["artifact_filename"]).read_text())
    assert artifact["fallback"]["fallback_used"] is False
    assert set(artifact["tool_lane"]["subgates"]) == set(pilot.TOOL_LANE_SUBGATES)
    ledger_rows = [
        _json.loads(line)
        for line in (tmp_path / "pilot-ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert ledger_rows[-1]["verdict"] == "passed"


def test_run_assemble_evidence_subgate_false_is_loop_failed(tmp_path) -> None:
    def _break(cap):
        cap["tool_lane_subgates"]["tool_result_roundtrip"] = False
    capture = _write_capture(tmp_path, override=_break)
    readiness = _write_passing_readiness_artifact(tmp_path)
    result = pilot.run_assemble_evidence(
        capture_path=capture,
        readiness_artifact_path=readiness,
        pilot_base_url="http://127.0.0.1:8066",
        evidence_dir=tmp_path,
    )
    assert result["verdict"] == "loop_failed"
    assert any("tool_result_roundtrip" in r for r in result["reasons"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k assemble_evidence -v`
Expected: FAIL with `AttributeError: ... 'run_assemble_evidence'`

- [ ] **Step 3: Implement the runner + wire the subparser**

Add to `scripts/replacement/r4_ops_cutover_pilot.py`:

```python
def _rebuild_readiness_from_artifact(artifact: Mapping[str, Any]) -> ReadinessVerdict:
    payload = artifact.get("readiness") or {}
    checks = tuple(
        ReadinessCheck(c["name"], bool(c["ok"]), dict(c.get("detail") or {}))
        for c in (payload.get("checks") or [])
    )
    return ReadinessVerdict(
        verdict=str(artifact.get("verdict") or payload.get("verdict")),
        ready=bool(payload.get("ready")),
        checks=checks,
        failures=tuple(payload.get("failures") or []),
    )


def run_assemble_evidence(
    *,
    capture_path: Path,
    readiness_artifact_path: Path,
    pilot_base_url: str,
    evidence_dir: Path,
) -> dict[str, Any]:
    capture = json.loads(Path(capture_path).read_text(encoding="utf-8"))
    readiness_artifact = json.loads(
        Path(readiness_artifact_path).read_text(encoding="utf-8")
    )
    readiness = _rebuild_readiness_from_artifact(readiness_artifact)

    tool_lane = evaluate_tool_lane(capture.get("tool_lane_subgates") or {})
    fb = capture.get("fallback") or {}
    reproduction = capture.get("reproduction") or {}
    fallback = evaluate_fallback_proof(
        config_snapshot=fb.get("config_snapshot") or {},
        consumer_outbound=fb.get("consumer_outbound") or {},
        owlmlx_inbound=fb.get("owlmlx_inbound") or {},
        pilot_request_ids=reproduction.get("request_ids") or [],
        pilot_base_url=pilot_base_url,
    )
    watermark = evaluate_watermark_health(capture.get("watermark_classifications") or [])
    pilot_verdict = build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=bool(capture.get("loop_completed")),
    )
    recorded_at = _now_iso_utc()
    artifact = build_pilot_artifact(
        pilot_verdict=pilot_verdict,
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        reproduction=reproduction,
        recorded_at=recorded_at,
    )
    session_id = str(reproduction.get("session_id") or "session")
    filename = f"{_now_compact_utc()}-pilot-{pilot_verdict.verdict}-{session_id}.json"
    _write_json(evidence_dir / filename, artifact)
    _append_jsonl(
        evidence_dir / "pilot-ledger.jsonl",
        {
            "recorded_at": recorded_at,
            "verdict": pilot_verdict.verdict,
            "session_id": session_id,
            "artifact": filename,
        },
    )
    return {
        "verdict": pilot_verdict.verdict,
        "reasons": list(pilot_verdict.reasons),
        "artifact_filename": filename,
        "artifact_path": str(evidence_dir / filename),
    }
```

Add the subparser inside `main` (after the `probe-readiness` parser, before `args = parser.parse_args(argv)`):

```python
    assemble = sub.add_parser(
        "assemble-evidence",
        help="Assemble controlled-smoke captures into a pilot verdict artifact.",
    )
    assemble.add_argument("--capture", type=Path, required=True,
                          help="Operator-captured smoke JSON (see runbook).")
    assemble.add_argument("--readiness-artifact", type=Path, required=True,
                          help="The readiness artifact emitted by probe-readiness.")
    assemble.add_argument(
        "--base-url",
        default=os.environ.get("OWLMLX_PILOT_BASE_URL", DEFAULT_BASE_URL),
    )
    assemble.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
```

And the dispatch branch (after the `probe-readiness` branch):

```python
    if args.command == "assemble-evidence":
        result = run_assemble_evidence(
            capture_path=args.capture,
            readiness_artifact_path=args.readiness_artifact,
            pilot_base_url=args.base_url,
            evidence_dir=args.evidence_dir,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["verdict"] == "passed" else 1
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -k assemble_evidence -v`
Expected: PASS (2 assemble-evidence tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/replacement/r4_ops_cutover_pilot.py tests/test_r4_ops_cutover_pilot.py
git commit -m "feat(r4): assemble-evidence subcommand (pilot verdict + jsonl ledger)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Operator runbook for the controlled OwlCoda smoke

**Files:**
- Create: `docs/architect/design/R4-ops-cutover-runbook.md`

This is the **manual, operator-executed** half of Phase 1 (spec §1 part B). It must NOT commit any OwlCoda/OwlCC repo file; it records the launch command, env, commit, base URL, model id, session id, and request ids (constraint #5) into the capture JSON consumed by `assemble-evidence`.

- [ ] **Step 1: Write the runbook**

Create `docs/architect/design/R4-ops-cutover-runbook.md` with the following content:

````markdown
# R4 Phase-1 Controlled-Smoke Operator Runbook

> Operator procedure for the ONE controlled non-default OwlCoda agentic smoke.
> Pairs with the harness `scripts/replacement/r4_ops_cutover_pilot.py` and the
> design spec [`R4-ops-cutover-spec.md`](R4-ops-cutover-spec.md).
> **Non-default, single session.** Does NOT flip OwlCoda/OwlCC defaults, does NOT
> remove `:8009` globally, claims NO replacement-complete, promotes NO capability.

## 0. Variables (port is NOT a contract — set per host)

```bash
export OWLMLX_PILOT_BASE_URL="http://127.0.0.1:8066"   # default example only
export OWLMLX_PILOT_MODEL_ID="<the Qwen pilot model id, e.g. Qwen3.6-27B>"
export OWLMLX_COMMIT="$(git -C /Users/yeemio/AI/gitrep/owlmlx rev-parse HEAD)"
export PILOT_SESSION_ID="pilot-001"
```

## 1. Launch owlmlx (native backend) and capture its request log

Start the runtime so the Qwen pilot model is loadable on the native backend, and
**redirect the request log to a file** (there is no ledger endpoint — owlmlx logs
inbound requests via the `owlmlx.runtime.server.request` logger as
`request.start` / `request.finish` with `owlmlx_request_id` / `owlmlx_http_path`).

Record the exact launch command into the capture's `reproduction.launch_command`.

## 2. Probe readiness (harness)

```bash
uv run python -m scripts.replacement.r4_ops_cutover_pilot probe-readiness \
  --base-url "$OWLMLX_PILOT_BASE_URL" \
  --model-id "$OWLMLX_PILOT_MODEL_ID" \
  --owlmlx-commit "$OWLMLX_COMMIT"
```

- Writes `files/evidence/owlmlx/replacement/r4-ops-cutover/<ts>-readiness-<verdict>-<model>.json`.
- If `pilot_readiness_failed`: STOP. That artifact IS the deliverable for this run
  (feed it to R1/R4 blocker). Do not run the smoke.

## 3. Configure a NON-DEFAULT OwlCoda pilot pointing at owlmlx

- In a throwaway/non-default OwlCoda profile (NOT the committed default), set the
  provider base URL to `$OWLMLX_PILOT_BASE_URL` and the model to `$OWLMLX_PILOT_MODEL_ID`.
- Disable `:8009` legacy fallback **for this session** (the point under test).
- **Commit no OwlCoda repo file.** Snapshot the effective config (base_url, provider,
  fallback_enabled) into the capture's `fallback.config_snapshot`.

## 4. Run ONE real agentic tool loop

Drive a real task that forces at least one tool call → execution → result round-trip
→ final answer. As it runs, record the four sub-gates HONESTLY (each independent):

| Sub-gate | How to confirm |
|---|---|
| `tool_call_emitted` | owlmlx response had `choices[0].message.tool_calls[]` non-empty (`finish_reason == "tool_calls"`) |
| `tool_call_executed` | OwlCoda actually ran the named tool |
| `tool_result_roundtrip` | the tool result was posted back to owlmlx as a `tool` message |
| `final_answer_after_tool` | owlmlx produced a final assistant answer after the tool result |

## 5. Capture the fallback double-proof + watermark health

- `fallback.consumer_outbound`: from OwlCoda's side — `fallback_count` (must be 0)
  and the set of outbound hosts (must be only the pilot host). owlmlx never calls
  `:8009`, so this no-`:8009` proof is necessarily consumer-side.
- `fallback.owlmlx_inbound.served_request_ids`: grep the captured owlmlx request log
  for `owlmlx_request_id` values; every pilot request-id must appear (inbound coverage).
- `reproduction.request_ids`: the `x-request-id` values from the session.
- `watermark_classifications`: sample `GET $OWLMLX_PILOT_BASE_URL/v1/runtime/monitor/snapshot`
  during the run; collect each `resources.host_pressure.classification`.

## 6. Assemble the verdict

Fill `capture.json` (schema in the plan, Task 8) and run:

```bash
uv run python -m scripts.replacement.r4_ops_cutover_pilot assemble-evidence \
  --capture capture.json \
  --readiness-artifact files/evidence/owlmlx/replacement/r4-ops-cutover/<readiness-artifact>.json \
  --base-url "$OWLMLX_PILOT_BASE_URL"
```

- Writes `<ts>-pilot-<verdict>-<session>.json` + appends `pilot-ledger.jsonl`.
- `passed` = this ONE session's gates met. NOT replacement-complete. Promotes nothing.

## 7. What this run feeds

- `passed` / `loop_failed` / `pilot_readiness_failed` → blocker ④ + gap 5 evidence,
  plus any tool-lane shortfall → R1 findings. The replacement verdict stays
  `not yet replaceable` regardless.
````

- [ ] **Step 2: Verify the runbook renders and links resolve**

Run: `ls docs/architect/design/R4-ops-cutover-runbook.md && grep -c "OWLMLX_PILOT_BASE_URL" docs/architect/design/R4-ops-cutover-runbook.md`
Expected: file exists; `OWLMLX_PILOT_BASE_URL` appears ≥ 3 times.

- [ ] **Step 3: Commit**

```bash
git add docs/architect/design/R4-ops-cutover-runbook.md
git commit -m "docs(r4): controlled-smoke operator runbook

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Final verification (full suite + synthetic dry-run + DoD checklist)

**Files:** none created; verification only.

- [ ] **Step 1: Run the full harness test module**

Run: `uv run pytest tests/test_r4_ops_cutover_pilot.py -v`
Expected: PASS — all tests (≈ 1 import + 3 readiness + 3 tool-lane + 4 fallback + 3 watermark + 6 verdict/artifact + 2 probe + 2 assemble = 24).

- [ ] **Step 2: Confirm no `owlmlx/` package module was added (AGENTS rule)**

Run: `git status --porcelain owlmlx/`
Expected: NO new files under `owlmlx/` from this plan (pre-existing dirty `owlmlx/speculative/...` is NOT ours — do not stage it).

- [ ] **Step 3: Synthetic end-to-end dry-run (no live server)**

Exercise the whole `assemble-evidence` pipeline with a synthetic passing capture to prove the schema + ledger path, writing to a scratch dir (NOT the canonical evidence dir):

Run:
```bash
uv run python - <<'PY'
import json, tempfile, pathlib
from scripts.replacement import r4_ops_cutover_pilot as pilot
d = pathlib.Path(tempfile.mkdtemp())
# minimal passing readiness artifact
r = pilot.evaluate_readiness(
    {
        "healthz": {"status": 200, "body": {"ok": True, "readiness": "ready"}},
        "model_visibility": {"status": 200, "body": {"visible_model_ids": ["M"]}},
        "openai_models": {"status": 200, "body": {"data": [{"id": "M"}]}},
        "tool_lane": {"status": 200, "body": {"choices": [{"message": {"tool_calls": [{"id": "c"}]}}]}},
        "monitor": {"status": 200, "body": {"resources": {"host_pressure": {"classification": "green"}}}},
    },
    model_id="M",
)
(d / "readiness.json").write_text(json.dumps(pilot.build_readiness_artifact(
    verdict=r, base_url="http://127.0.0.1:8066", model_id="M",
    owlmlx_commit="dryrun", recorded_at="2026-06-03T00:00:00Z")))
(d / "capture.json").write_text(json.dumps({
    "loop_completed": True,
    "tool_lane_subgates": {k: True for k in pilot.TOOL_LANE_SUBGATES},
    "fallback": {
        "config_snapshot": {"base_url": "http://127.0.0.1:8066", "fallback_enabled": False},
        "consumer_outbound": {"fallback_count": 0, "outbound_hosts": ["127.0.0.1:8066"]},
        "owlmlx_inbound": {"served_request_ids": ["req_a"]}},
    "watermark_classifications": ["green"],
    "reproduction": {"owlmlx_commit": "dryrun", "base_url": "http://127.0.0.1:8066",
                     "model_id": "M", "session_id": "dryrun", "request_ids": ["req_a"]},
}))
res = pilot.run_assemble_evidence(
    capture_path=d / "capture.json", readiness_artifact_path=d / "readiness.json",
    pilot_base_url="http://127.0.0.1:8066", evidence_dir=d)
print(json.dumps(res, indent=2))
assert res["verdict"] == "passed", res
print("DRY-RUN OK")
PY
```
Expected: prints `DRY-RUN OK` and `"verdict": "passed"`. (Scratch dir only — nothing written under `files/evidence/`.)

- [ ] **Step 4: DoD checklist against spec §7**

Confirm each spec §7 item maps to a delivered capability:

1. readiness pass OR `pilot_readiness_failed` artifact → `run_probe_readiness` (Task 7) ✓
2. real agentic loop owlmlx-only → operator runbook §4 (Task 9) ✓
3. reproduction info (cmd/env/commit/base/model/session/request-ids) → capture `reproduction{}` + artifact (Tasks 6/8) ✓
4. `fallback_used=false` double-proof → `evaluate_fallback_proof` (Task 4) ✓
5. tool-lane 4 sub-gates recorded independently → `evaluate_tool_lane` (Task 3) ✓
6. watermark health-gate-only wording → `evaluate_watermark_health.interpretation` (Task 5) ✓
7. pilot verdict + feeds blocker ④/gap 5/R1 → `build_pilot_verdict` + runbook §7 (Tasks 6/9) ✓
8. zero unsourced claims; no replacement-complete; no promotion → `honesty_note` + `promotes: nothing` on every artifact ✓

- [ ] **Step 5: Stop for review — no push**

Do NOT push. Surface the commit list + full test output to the user and hold for the standing push-authorization gate.

---

## Out of scope (do not let the plan creep)

- Flipping OwlCoda/OwlCC defaults; removing `:8009` globally.
- Non-Qwen tool calling or broader interaction-shape parity (→ R1).
- Sustained soak / sustained-stability claims (→ R4 Phase B).
- Any new `owlmlx/` package module; any committed OwlCoda/OwlCC file.
- Promoting Session KV / prefix cache or any capability; changing the §1a Promotion Gate.
