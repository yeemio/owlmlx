# Comparative-Evidence Refresh (Cold + Warm, vs References) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh owlmlx-vs-reference (oMLX/vMLX) comparative evidence on a **fair warm-server basis** across two workloads — `single_prompt_short` (cold worst-case) and `multi_prompt_serial` (warm session-reuse, owlmlx's actual differentiator, never measured) — and produce an honest two-axis gap map. Reuse the frozen comparative-evidence harness unchanged; all new code is a uniform HTTP wrapper driver + a multi-turn prompt set + one operator subcommand + runner configs + tests.

**Architecture:** The runner (`owlmlx/comparative_evidence_runner.py`) executes each attempt as a caller-supplied subprocess (argv with `{prompt}`/`{model_path}`/`{max_tokens}`/`{temperature}`/`{model_id}` placeholders) and measures wall-clock / first-token / RSS (server RSS via `external_listener_ports`/`external_pid_file`). `workload_class` is a metadata label, not execution logic — so multi-turn lives entirely in the wrapper driver. We replace the 2026-04 *asymmetric* setup (owlmlx cold-CLI vs oMLX warm-server) with **one uniform HTTP driver** that hits each runtime's warm OpenAI-compatible server; owlmlx gets `x-owlmlx-session-id` continuity for the multi-turn axis. A new `run-measured-multi-turn` operator subcommand mirrors the existing `run-measured-short-prompt`.

**Tech Stack:** Python 3.11, stdlib `urllib.request`/`hashlib`/`json`, pytest. Reuses `owlmlx/comparative_evidence_{runner,schema,record,history}.py` (UNCHANGED). Runtimes as warm servers: owlmlx `:8066`, oMLX `:8063`, vMLX (best-effort, its OpenAI port). Model: `gemma-4-31B-it-4bit` (see Task 7 RAM note). No new `owlmlx/` module (AGENTS rule): driver + tests in `scripts/`/`tests/`; only the operator script (already in `scripts/`) gains a subcommand.

---

## State going in (verified 2026-06-05 against current `main`)

**Reused unchanged (do NOT modify — frozen per the harness contract):**
- `owlmlx/comparative_evidence_runner.py` — `RuntimeRunnerConfig` (fields: `runtime_id, runtime_version, argv, env, cwd, timeout_s, first_token_strategy, tokens_method, external_pids, external_pid_file, external_listener_ports`), `WorkloadInputs` (`prompt, decode_max_tokens, decode_temperature, model_id, model_path, model_quantization, prompt_set_hash, serving_budget_bytes, workload_class`), `execute_attempt`, `aggregate_runtime`, `aggregate_to_record_runtime`, `compute_verdict`, `load_runner_config_file`, `write_run_artifacts`. Placeholders supported in argv: `{prompt} {max_tokens} {temperature} {model_id} {model_path}`. `tokens_method` ∈ `max_tokens | stdout_word_count | stdout_line_count | json_field:<key>`. `first_token_strategy` ∈ `first_nonempty_chunk | after_marker:<sub> | regex:<pat>`.
- `owlmlx/comparative_evidence_schema.py` — validator + **banned verdict vocab** (`parity, equivalent, replaces, replacement, production-ready, superior, wins, beats, matches`), `RUNTIME_IDS=(owlmlx,omlx,vmlx)`, `WORKLOAD_CLASSES=(single_prompt_short, single_prompt_long, multi_prompt_serial, multi_prompt_aggregated)`, `VERDICT_GRADES=(measured, inconclusive, rejected)`.
- `owlmlx/comparative_evidence_record.py` (`build_comparative_evidence_record`, `ComparativeEvidenceMeasurement`, `ComparativeEvidenceRuntime`), `owlmlx/comparative_evidence_history.py` (`ComparativeEvidenceLedger`), HTTP endpoints `/v1/runtime/comparative-evidence[/history]`.
- `scripts/runtime_comparative_evidence.py` — operator entry; `run-measured-short-prompt` (`scripts/runtime_comparative_evidence.py:111-222`) is the exact pattern Task 4 mirrors.

**The 2026-04 asymmetry (the bug this refresh fixes):** `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/runner-config.json` — owlmlx argv = `scripts/runtime_large_weight_first_smoke.py` (loads the model **every attempt** → cold, load-dominated), reference = oMLX **warm server** at `http://127.0.0.1:8063/v1/chat/completions`. The measured "owlmlx 0.1613 vs oMLX 0.5778 tok/s (~3.6× slower)" compared owlmlx-cold to oMLX-warm. The refresh runs **both warm**.

**Spec:** `docs/architect/design/comparative-evidence-refresh-spec.md`. **Honesty rails:** schema bans parity-vocab; verdict ∈ measured/inconclusive/rejected; evidence-language = "single-host point measurements vs upstream references"; promotes nothing; §1a untouched.

---

## File structure

- **Create** `scripts/bench/comparative_http_driver.py` — uniform HTTP wrapper driver. Runtime-agnostic via `--base-url`; `--session-id` (owlmlx only) for multi-turn reuse. Modes: `single` (one prompt) and `multi-turn` (sequence from a prompt-set file, accumulating history). Prints each turn's content (for first-token detection) + a final `{"generated_tokens": N}` line. Pure helpers separated for model-free testing.
- **Create** `scripts/bench/fixtures/comparative_multi_turn_agentic.json` — the realistic multi-turn prompt set (shared, growing context).
- **Create** `scripts/bench/comparative_runner_configs/` — runner-config JSONs: `{owlmlx_omlx,owlmlx_vmlx}_x_{short,serial}.json` (argv → the driver).
- **Modify** `scripts/runtime_comparative_evidence.py` — add `run-measured-multi-turn` subcommand (mirrors `_run_measured_short_prompt`; computes `prompt_set_hash` from the prompt-set file).
- **Create** `tests/test_comparative_http_driver.py` — model-free tests for the driver's pure helpers + output format.
- **Create** `tests/test_runtime_comparative_evidence_multi_turn.py` — model-free test that the new subcommand builds a schema-valid record (with faked runner functions).
- **Evidence (Task 7-8)** `files/evidence/owlmlx/comparative-evidence/<UTC>-refresh-cold-warm/` — runner configs, manifests, ledger rows, two-axis summary.

---

## Task 1: Multi-turn prompt-set fixture

**Files:**
- Create: `scripts/bench/fixtures/comparative_multi_turn_agentic.json`

- [ ] **Step 1: Write the fixture**

A realistic agentic sequence with a large shared prefix that grows each turn — this is where owlmlx's prefix/session-KV reuse pays off. Each entry is one user turn; the driver accumulates assistant replies between them.

```json
{
  "description": "Realistic agentic coding session: shared growing context. Each turn appends to history; warm runtimes reuse the common prefix.",
  "system": "You are a senior Python engineer. Be concise. When asked to edit code, output only the changed function.",
  "turns": [
    "Here is a module:\n\n```python\ndef parse_config(path):\n    import json\n    return json.load(open(path))\n```\nExplain what's fragile about this in 2 sentences.",
    "Rewrite parse_config to close the file handle and raise a clear error when the file is missing. Output only the function.",
    "Now add support for a default config dict merged under the file's values. Output only the function.",
    "Write one pytest test for the missing-file case. Output only the test function."
  ]
}
```

- [ ] **Step 2: Commit the fixture**

```bash
git add scripts/bench/fixtures/comparative_multi_turn_agentic.json
git commit -m "test(对标): realistic multi-turn agentic prompt set for comparative refresh

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Uniform HTTP wrapper driver

**Files:**
- Create: `scripts/bench/comparative_http_driver.py`
- Test: `tests/test_comparative_http_driver.py`

- [ ] **Step 1: Write failing tests for the pure helpers**

```python
# tests/test_comparative_http_driver.py
import json
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "comparative_http_driver",
    Path(__file__).parents[1] / "scripts" / "bench" / "comparative_http_driver.py",
)
driver = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(driver)


def test_load_prompt_set_returns_system_and_turns(tmp_path):
    p = tmp_path / "ps.json"
    p.write_text(json.dumps({"system": "sys", "turns": ["a", "b"]}), encoding="utf-8")
    system, turns = driver.load_prompt_set(str(p))
    assert system == "sys"
    assert turns == ["a", "b"]


def test_build_messages_accumulates_history():
    history = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "A"}]
    msgs = driver.build_messages(system="sys", history=history, user_turn="b")
    assert msgs[0] == {"role": "system", "content": "sys"}
    assert msgs[-1] == {"role": "user", "content": "b"}
    assert {"role": "assistant", "content": "A"} in msgs


def test_summarize_emits_total_tokens_line():
    out = driver.format_output(turn_texts=["hello", "world"], total_tokens=7)
    lines = out.strip().splitlines()
    assert lines[0] == "hello"
    assert json.loads(lines[-1]) == {"generated_tokens": 7}
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_comparative_http_driver.py -v`
Expected: FAIL (module/functions not defined).

- [ ] **Step 3: Write the driver**

```python
#!/usr/bin/env python3
"""Uniform HTTP wrapper driver for the comparative-evidence runner.

One subprocess invocation = one runner attempt. Hits a runtime's warm
OpenAI-compatible /v1/chat/completions server (owlmlx :8066, oMLX :8063, vMLX).
The runner measures this process's wall-clock + first-token (stdout) and the
server's RSS (via the runner config's external_listener_ports/external_pid_file).

Modes:
  single     : one user prompt, one request.
  multi-turn : a sequence from --prompt-set; accumulate assistant replies into
               history each turn. With --session-id (owlmlx only), every request
               carries x-owlmlx-session-id so the runtime can reuse cached prefix.

stdout contract for the runner:
  - each turn's assistant text is printed as it arrives (first non-empty chunk =>
    first-token latency of the first turn)
  - a final line `{"generated_tokens": N}` (sum of completion_tokens across turns)
    => use tokens_method=json_field:generated_tokens in the runner config.

scripts/ (not owlmlx/) per the AGENTS module-as-spec rule: bench driver, no
runtime consumer, no capability promotion.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request


def load_prompt_set(path: str) -> tuple[str, list[str]]:
    payload = json.loads(open(path, encoding="utf-8").read())
    system = str(payload.get("system", ""))
    turns = [str(t) for t in payload.get("turns", [])]
    return system, turns


def build_messages(*, system: str, history: list[dict], user_turn: str) -> list[dict]:
    msgs: list[dict] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_turn})
    return msgs


def format_output(*, turn_texts: list[str], total_tokens: int) -> str:
    lines = list(turn_texts)
    lines.append(json.dumps({"generated_tokens": int(total_tokens)}))
    return "\n".join(lines) + "\n"


def post_chat(
    *, base_url: str, model: str, messages: list[dict], max_tokens: int,
    temperature: float, session_id: str | None,
) -> tuple[str, int]:
    body = {
        "model": model, "messages": messages,
        "max_tokens": max_tokens, "temperature": temperature, "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if session_id:
        headers["x-owlmlx-session-id"] = session_id
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(), headers=headers, method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read())
    content = data["choices"][0]["message"].get("content") or ""
    usage = data.get("usage") or {}
    completion = int(usage.get("completion_tokens", 0))
    return content, completion


def run(args: argparse.Namespace) -> int:
    if args.mode == "single":
        system, turns = ("", [args.prompt])
    else:
        system, turns = load_prompt_set(args.prompt_set)

    history: list[dict] = []
    turn_texts: list[str] = []
    total_tokens = 0
    for user_turn in turns:
        messages = build_messages(system=system, history=history, user_turn=user_turn)
        content, completion = post_chat(
            base_url=args.base_url, model=args.model, messages=messages,
            max_tokens=int(args.max_tokens), temperature=float(args.temperature),
            session_id=args.session_id,
        )
        # Print immediately so the runner's first-token timer fires on turn 1.
        print(content, flush=True)
        turn_texts.append(content)
        total_tokens += completion
        history.append({"role": "user", "content": user_turn})
        history.append({"role": "assistant", "content": content})

    sys.stdout.write(json.dumps({"generated_tokens": total_tokens}) + "\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["single", "multi-turn"], required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt", default="")
    ap.add_argument("--prompt-set", default="")
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--session-id", default=None)
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, verify pass**

Run: `.venv/bin/python -m pytest tests/test_comparative_http_driver.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/bench/comparative_http_driver.py tests/test_comparative_http_driver.py
git commit -m "feat(对标): uniform warm-server HTTP driver for comparative refresh

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Runner-config JSONs (argv → driver)

**Files:**
- Create: `scripts/bench/comparative_runner_configs/owlmlx_omlx_x_short.json`
- Create: `scripts/bench/comparative_runner_configs/owlmlx_omlx_x_serial.json`
- Create: `scripts/bench/comparative_runner_configs/owlmlx_vmlx_x_serial.json`

- [ ] **Step 1: Write the owlmlx-vs-oMLX short-prompt config (both warm servers)**

`owlmlx_omlx_x_short.json` — note owlmlx now hits its **warm** `:8066` server (the 2026-04 cold-CLI asymmetry is gone). `external_listener_ports` lets the runner sample each server's RSS.

```json
{
  "owlmlx": {
    "runtime_id": "owlmlx",
    "runtime_version": "local-checkout-warm-8066",
    "argv": [
      "python3", "scripts/bench/comparative_http_driver.py",
      "--mode", "single", "--base-url", "http://127.0.0.1:8066",
      "--model", "{model_id}", "--prompt", "{prompt}",
      "--max-tokens", "{max_tokens}", "--temperature", "{temperature}"
    ],
    "env": {"PYTHONPATH": "."},
    "cwd": "/Users/yeemio/AI/gitrep/owlmlx",
    "tokens_method": "json_field:generated_tokens",
    "first_token_strategy": "first_nonempty_chunk",
    "external_listener_ports": [8066],
    "timeout_s": 240.0
  },
  "reference": {
    "runtime_id": "omlx",
    "runtime_version": "0.3.5-warm-8063",
    "argv": [
      "python3", "scripts/bench/comparative_http_driver.py",
      "--mode", "single", "--base-url", "http://127.0.0.1:8063",
      "--model", "{model_id}", "--prompt", "{prompt}",
      "--max-tokens", "{max_tokens}", "--temperature", "{temperature}"
    ],
    "env": {},
    "cwd": "/Users/yeemio/AI/gitrep/owlmlx",
    "tokens_method": "json_field:generated_tokens",
    "first_token_strategy": "first_nonempty_chunk",
    "external_listener_ports": [8063],
    "timeout_s": 240.0
  }
}
```

- [ ] **Step 2: Write the multi-turn config** (`owlmlx_omlx_x_serial.json`)

Identical to Step 1 except `--mode multi-turn`, `--prompt-set scripts/bench/fixtures/comparative_multi_turn_agentic.json` replacing `--prompt {prompt}`, and **owlmlx adds `--session-id refresh-serial-001`** (oMLX does not — it has no session-reuse concept; this is the honest product difference). Full owlmlx argv:

```json
"argv": [
  "python3", "scripts/bench/comparative_http_driver.py",
  "--mode", "multi-turn", "--base-url", "http://127.0.0.1:8066",
  "--model", "{model_id}",
  "--prompt-set", "scripts/bench/fixtures/comparative_multi_turn_agentic.json",
  "--max-tokens", "{max_tokens}", "--temperature", "{temperature}",
  "--session-id", "refresh-serial-001"
]
```
Reference (oMLX) argv is the same minus `--session-id`, with `--base-url http://127.0.0.1:8063`.

- [ ] **Step 3: Write the vMLX variant** (`owlmlx_vmlx_x_serial.json`) — copy the serial config; reference `runtime_id: "vmlx"`, `--base-url` = vMLX's OpenAI port (confirm from `files/evidence/owlmlx/comparative-evidence/20260506T053916Z-deepseek-reference-closure/deepseek-vmlx-run/runner-config.json`), `external_listener_ports` set accordingly. vMLX is best-effort (Task 7).

- [ ] **Step 4: Commit**

```bash
git add scripts/bench/comparative_runner_configs/
git commit -m "test(对标): warm-server runner configs (owlmlx vs oMLX/vMLX, short+serial)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `run-measured-multi-turn` operator subcommand

**Files:**
- Modify: `scripts/runtime_comparative_evidence.py`
- Test: `tests/test_runtime_comparative_evidence_multi_turn.py`

- [ ] **Step 1: Write the failing test** (the subcommand builds a schema-valid record with faked runner functions)

```python
# tests/test_runtime_comparative_evidence_multi_turn.py
import hashlib
from pathlib import Path
import scripts.runtime_comparative_evidence as op  # importable: repo root on sys.path
from owlmlx.comparative_evidence_schema import validate_comparative_evidence_record


def test_prompt_set_hash_is_deterministic_sha256(tmp_path):
    f = tmp_path / "ps.json"
    f.write_text('{"turns":["a"]}', encoding="utf-8")
    h = op._prompt_set_hash(str(f))
    assert h == "sha256:" + hashlib.sha256(b'{"turns":["a"]}').hexdigest()
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_runtime_comparative_evidence_multi_turn.py -v`
Expected: FAIL (`_prompt_set_hash` not defined).

- [ ] **Step 3: Add `_prompt_set_hash` + the subcommand to `scripts/runtime_comparative_evidence.py`**

Add the helper near the top (after `_now_iso_utc`):

```python
def _prompt_set_hash(path: str) -> str:
    import hashlib
    data = Path(path).read_bytes()
    return "sha256:" + hashlib.sha256(data).hexdigest()
```

Add a `_run_measured_multi_turn` that reuses `_run_measured_short_prompt`'s body with two changes — `workload_class` defaults to `multi_prompt_serial`, and `prompt`/`prompt_set_hash` come from the prompt-set file:

```python
def _run_measured_multi_turn(*, ledger, args) -> dict:
    # The driver reads the prompt-set file itself (via the runner-config argv);
    # here `prompt` carries the path so {prompt} substitution stays valid, and
    # the hash is computed from the file for honest reproducibility.
    args.prompt = args.prompt_set
    args.prompt_set_hash = _prompt_set_hash(args.prompt_set)
    if not getattr(args, "workload_class", None):
        args.workload_class = "multi_prompt_serial"
    return _run_measured_short_prompt(ledger=ledger, args=args)
```

Register the subparser in `main()` (mirror `run-measured-short-prompt`, swapping `--prompt` for `--prompt-set`):

```python
    multi = sub.add_parser(
        "run-measured-multi-turn",
        help="Run multi-turn serial attempts (owlmlx warm + reference) and append one record",
    )
    multi.add_argument("--evidence-dir", required=True)
    multi.add_argument("--runner-config", required=True)
    multi.add_argument("--host-class", required=True)
    multi.add_argument("--workload-class", default="multi_prompt_serial")
    multi.add_argument("--model-id", required=True)
    multi.add_argument("--model-path", required=True)
    multi.add_argument("--model-quantization", default="full_precision_unquantized")
    multi.add_argument("--prompt-set", required=True)
    multi.add_argument("--decode-max-tokens", type=int, default=128)
    multi.add_argument("--decode-temperature", type=float, default=0.0)
    multi.add_argument("--serving-budget-bytes", type=int, default=85899345920)
    multi.add_argument("--repeats", type=int, default=5)
    multi.add_argument("--evidence-pointer", default=None)
```

And dispatch it in `main()` after the `run-measured-short-prompt` branch:

```python
    if args.command == "run-measured-multi-turn":
        payload = _run_measured_multi_turn(ledger=ledger, args=args)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
```

- [ ] **Step 4: Run the test + confirm the existing short-prompt path still imports**

Run: `.venv/bin/python -m pytest tests/test_runtime_comparative_evidence_multi_turn.py -v && .venv/bin/python scripts/runtime_comparative_evidence.py --help`
Expected: test PASS; `--help` lists `run-measured-multi-turn`.

- [ ] **Step 5: Commit**

```bash
git add scripts/runtime_comparative_evidence.py tests/test_runtime_comparative_evidence_multi_turn.py
git commit -m "feat(对标): run-measured-multi-turn operator subcommand (reuses runner)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Model-free full-suite check

- [ ] **Step 1: Run the new tests + the existing comparative-evidence tests**

Run: `.venv/bin/python -m pytest tests/test_comparative_http_driver.py tests/test_runtime_comparative_evidence_multi_turn.py tests/ -k "comparative" -q --continue-on-collection-errors`
Expected: PASS (the pre-existing `psutil`-missing collection error in `test_runtime_comparative_evidence_measured_runner` is unrelated and isolated by `--continue-on-collection-errors`; do NOT touch `uv.lock`).

- [ ] **Step 2: No-op if green.** If any new test fails, fix inline before proceeding — do not advance to the gated run on red.

---

## Task 6 (GATED — heavy, ~tens of GB + minutes): execute the two-axis runs

> **DECISION REQUIRED before this task (cost-flag rule).** This loads models into **two warm servers simultaneously** and runs N=5 × 2 runtimes × 2 workloads. Surface cost + run-now-vs-defer.
>
> **RAM constraint (must resolve first):** two *full* `gemma-4-31B-it` warm servers ≈ 62GB + 54GB ≈ **116GB** on a 128GB host — over comfortable budget. **Resolution: use `gemma-4-31B-it-4bit` for both runtimes** (~18–20GB each → ~40GB total, fits warm; fair same-quant comparison). This **amends spec §4's model knob** from full to 4-bit — confirm with the user. (Alternative: run each runtime in its own invocation with only its server up, then merge — more operator steps; only if 4-bit is unacceptable.)

**Pre-req:** owlmlx `:8066` daemon up with `gemma-4-31B-it-4bit` loadable; oMLX `:8063` server up with the same model; (vMLX best-effort). `host-class` must match the 2026-04 string for any cross-time context: `Mac17,6-arm64-macOS-26.4.1-128GB`.

- [ ] **Step 1: Confirm both servers are reachable**

Run: `curl -s http://127.0.0.1:8066/healthz && curl -s http://127.0.0.1:8063/v1/models`
Expected: owlmlx ok; oMLX lists the model.

- [ ] **Step 2: Cold axis — `single_prompt_short`, owlmlx vs oMLX, N=5**

```bash
.venv/bin/python scripts/runtime_comparative_evidence.py \
  --ledger-path data/comparative-evidence-ledger.jsonl \
  run-measured-short-prompt \
  --evidence-dir files/evidence/owlmlx/comparative-evidence/REFRESH-short \
  --runner-config scripts/bench/comparative_runner_configs/owlmlx_omlx_x_short.json \
  --host-class "Mac17,6-arm64-macOS-26.4.1-128GB" \
  --model-id gemma-4-31B-it-4bit \
  --model-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it-4bit \
  --model-quantization q4 \
  --prompt "List three Python stdlib modules for parsing JSON, one per line." \
  --prompt-set-hash "sha256:refresh-short-v1" \
  --decode-max-tokens 128 --repeats 5
```
Expected: a `measured` (or honest `rejected` if oMLX fails) record appended; note owlmlx-vs-oMLX throughput/TTFT/RSS.

- [ ] **Step 3: Warm axis — `multi_prompt_serial`, owlmlx vs oMLX, N=5**

```bash
.venv/bin/python scripts/runtime_comparative_evidence.py \
  --ledger-path data/comparative-evidence-ledger.jsonl \
  run-measured-multi-turn \
  --evidence-dir files/evidence/owlmlx/comparative-evidence/REFRESH-serial \
  --runner-config scripts/bench/comparative_runner_configs/owlmlx_omlx_x_serial.json \
  --host-class "Mac17,6-arm64-macOS-26.4.1-128GB" \
  --model-id gemma-4-31B-it-4bit \
  --model-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it-4bit \
  --model-quantization q4 \
  --prompt-set scripts/bench/fixtures/comparative_multi_turn_agentic.json \
  --decode-max-tokens 128 --repeats 5
```
Expected: a `measured` record for the warm/serial axis. This is the axis where owlmlx's session-reuse can show — compare to the cold axis.

- [ ] **Step 4: vMLX best-effort (optional).** Repeat Step 3 with `owlmlx_vmlx_x_serial.json`. If vMLX fails → the runner records `rejected` honestly; do not retry-storm.

- [ ] **Step 5: Capture raw outputs** — the runner already writes `manifest.json`/`commands.json`/`summary.md` + per-attempt artifacts under each `--evidence-dir`. Confirm they exist.

---

## Task 7: Two-axis gap map + honest verdict

**Files:**
- Create: `files/evidence/owlmlx/comparative-evidence/<UTC>-refresh-cold-warm/two-axis-summary.md`

- [ ] **Step 1: Read both ledger records**

Run: `.venv/bin/python scripts/runtime_comparative_evidence.py --ledger-path data/comparative-evidence-ledger.jsonl history`
Expected: the two new records (short + serial) present.

- [ ] **Step 2: Write the two-axis summary** — for each workload, owlmlx vs reference: throughput / TTFT / RSS, the ratio (e.g. "owlmlx 1/Nx the throughput"), CV/stable-label, and **each reference's reuse path** (oMLX = warm server, no session reuse; owlmlx = warm + session-id). Use **only** measured numbers; **no banned vocab**; frame as "single-host point measurements vs upstream references on gemma-4-31B-it-4bit." State plainly where owlmlx loses (likely cold) and whether the warm axis narrows or reverses the gap. If a record is `rejected`, say so — do not infer.

- [ ] **Step 3: Commit evidence**

```bash
git add files/evidence/owlmlx/comparative-evidence/
git commit -m "bench(对标): refreshed cold+warm comparative evidence vs references (gemma-4bit)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Capability wording + memory (docs-only)

**Files:**
- Modify: `docs/source-of-truth/runtime13-replacement-rebaseline-verdict.md` (§3 blocker ③ — add a dated note: refreshed warm-vs-warm comparative evidence exists; cite the ledger/summary; still no-regression-lens, promotes nothing, NOT vs `:8009`).
- Modify: `docs/architect/design/README.md` (对标 refresh row → status updated to evidence landed).
- Modify: `docs/source-of-truth/comparative-evidence-harness-contract.md` ONLY if a new closed `(host_class, workload_class=multi_prompt_serial)` pair warrants a §8.x closure note (follow the existing §8.1/§8.2 style; do not change frozen §5 contract).
- Memory: update `project-owlmlx-replacement-r-series-state.md` + `MEMORY.md` (对标 campaign done, two-axis result, promotes nothing).

- [ ] **Step 1: Update wording** — honest + calibrated: "single-host point measurements vs upstream references (oMLX/vMLX) on gemma-4-31B-it-4bit, warm-vs-warm; cold axis = X, warm/serial axis = Y; promotes nothing; not a parity/replacement claim; not vs legacy `:8009`." Cite evidence paths.

- [ ] **Step 2: Commit (docs-only)**

```bash
git add docs/source-of-truth/runtime13-replacement-rebaseline-verdict.md docs/architect/design/README.md
git commit -m "docs(对标): record refreshed comparative evidence (no-regression lens, promotes nothing)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: DoD self-check

- [ ] **Step 1: Walk spec §10** — two workloads × (oMLX required, vMLX best-effort) records present (measured or honest rejected); N≥5 with CV; **zero banned-vocab** (grep the summary + records for `parity|equivalent|matches|beats|replaces|superior|wins`); evidence-language calibrated; no promotion; runner/schema unchanged (`git diff --stat` touches only `scripts/`, `tests/`, `files/evidence/`, `docs/`, `data/ledger`); two-axis map reproducible (cmd · env · owlmlx commit · model id · prompt_set_hash · each reference's base-url + reuse path).
- [ ] **Step 2: Confirm frozen harness untouched** — `git diff <base> -- owlmlx/comparative_evidence_runner.py owlmlx/comparative_evidence_schema.py owlmlx/comparative_evidence_record.py owlmlx/comparative_evidence_history.py` is empty.
- [ ] **Step 3: Report** — the two-axis result, which references measured vs rejected, the 4-bit-model amendment, evidence path; restate promotes nothing / not vs `:8009`.

---

## Self-Review

**Spec coverage (comparative-evidence-refresh-spec §1-§10):** §1 acceptance → Tasks 6-7. §2 reuse-not-rebuild → Tasks 2-4 (frozen harness untouched, verified Task 9.2). §3.1 wrapper drivers → Task 2. §3.2 prompt set → Task 1. §3.3 fairness contract → Task 3 (session-id owlmlx-only) + Task 7.2 (reuse path recorded). §3.4 operator subcommand → Task 4. §4 knobs → Tasks 6 (model **amended to 4-bit**, flagged), 3 (references), 6 (N=5), 6 (both workloads). §5 data flow → Tasks 4+6. §6 metrics/verdict → reused runner + Task 7. §7 errors/honesty → `rejected` path reused; banned-vocab grep Task 9.1. §8 out-of-scope → no `:8009`, no CI/sidecar, no schema change. §9 hard rules → AGENTS (scripts/tests only), cost-flag (Task 6), fresh-session (this plan is plan-grade). §10 validation → Task 9.

**Placeholder scan:** no TBD/TODO. The one deviation — model knob full→4-bit — is explicit in Task 6 with rationale + user-confirm flag, not a placeholder. vMLX base-url in Task 3.3 is "confirm from the named existing config" (a real file pointer), not a blank.

**Type/name consistency:** driver helpers `load_prompt_set`/`build_messages`/`format_output`/`post_chat`/`run` consistent across Task 2 (code) + tests. `_prompt_set_hash` defined Task 4.3, tested Task 4.1, used Task 4.3. Runner functions (`execute_attempt`, `aggregate_runtime`, `compute_verdict`, `load_runner_config_file`, `write_run_artifacts`, `aggregate_to_record_runtime`) match `scripts/runtime_comparative_evidence.py:129-137`. `tokens_method:json_field:generated_tokens` matches the driver's final stdout line. Runtime ids (`owlmlx`/`omlx`/`vmlx`) and workload classes (`single_prompt_short`/`multi_prompt_serial`) match the frozen schema enums.

**Discipline:** new code only in `scripts/` + `tests/`; the sole `owlmlx/`-adjacent edit is a subcommand in the existing operator script (no new `owlmlx/` module, frozen harness untouched). Heavy run gated + cost-flagged. Code lands in a fresh session (this plan is the handoff). Push not in this plan.

---

## Execution Handoff

Per the plan→code fresh-session rule, execute this in a **fresh session**. Model-free tasks (1-5, 8 docs, 9 checks) are free; **Task 6 is gated** (two warm servers, ~40GB at 4-bit, minutes) — confirm the 4-bit model amendment + run-now-vs-defer first. Recommended executor: superpowers:subagent-driven-development or superpowers:executing-plans.
