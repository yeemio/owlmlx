# R1 — Gemma Tool-Calling Feasibility + Family-Parity Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land an honest verdict for R1 (tool-calling family parity, Qwen + Gemma, native, OpenAI shape): confirm Gemma `auto`/`none` tool-calling and resolve whether `tool_choice` *forcing* for Gemma is feasible — correcting or gracefully retiring the committed gemma4 forcing grammar based on a model-free xgrammar probe, then (gated) confirming end-to-end on a live Gemma.

**Architecture:** R1 component **(B)** — family-aware forcing dispatch — is **already built and tested** (`178292fa`: `_gemma4_forcing_ebnf`, `_infer_tool_choice_forcing_family`, `_tool_choice_forcing_ebnf(..., parser_family=)`, runtime verdict wiring, 4 tests). This plan finishes R1 component **(A)**: a model-free feasibility probe + the gemma4 forcing correction-or-retirement it dictates, plus a gated live confirmation, evidence, and capability-wording. **No new `owlmlx/` module** (AGENTS rule): the probe lives in `scripts/probe/`, tests in `tests/`, and the only runtime change is editing the *existing* `owlmlx/runtime/mlx_native_backend.py`.

**Tech Stack:** Python 3.11, mlx_lm 0.31.x (installed; has `tool_parsers/gemma4.py`), xgrammar (EBNF grammar compile/match), transformers `AutoTokenizer`, pytest. Local models: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it-4bit` (tokenizer ~MB for model-free tier; full 4bit weights ~62GB for the gated live tier). owlmlx native runtime daemon on `127.0.0.1:8066`.

---

## State going in (verified 2026-06-04, read against current `main` @ `178292fa`)

**Already done (do NOT rebuild):**
- `owlmlx/runtime/mlx_native_backend.py:522` `_gemma4_forcing_ebnf(funcs, param_names)` — builder exists.
- `owlmlx/runtime/mlx_native_backend.py:550` `_infer_tool_choice_forcing_family(tokenizer)` — returns `qwen3_coder` / `gemma4` / `unsupported` from `tokenizer.tool_parser_type` then the `tool_call_start` marker.
- `owlmlx/runtime/mlx_native_backend.py:602` `_tool_choice_forcing_ebnf(..., *, parser_family="qwen3_coder")` — dispatch qwen→qwen, gemma→gemma, unknown→None.
- Runtime wiring at `owlmlx/runtime/mlx_native_backend.py:1510-1543` — sets `detail` keys `tool_choice_forcing_family`, `tool_choice_forcing_unsupported_family`, `tool_choice_forced`, and `tool_choice_forcing_verdict` ∈ {`applied`,`documented_infeasible`,`unsupported`}.
- Tests: `tests/test_mlx_native_backend.py` — `test_native_backend_generate_records_unsupported_tool_choice_family` (337), `test_tool_choice_forcing_ebnf_dispatches_by_tool_parser_family` (722), `test_infer_tool_choice_forcing_family_uses_parser_type_then_marker` (740), `test_tool_choice_forcing_ebnf_compiles_as_valid_xgrammar` (762, **qwen-only**, `from_ebnf` parse only).

**Two facts this plan is built on (verified by reading mlx_lm's installed parser + tokenizing the markers):**
1. **Real gemma4 wire format** (`.venv/.../mlx_lm/tool_parsers/gemma4.py`): a call is `<|tool_call>call:NAME{...}<tool_call|>`; args use **unquoted keys** and **`<|"|>…<|"|>` string delimiters**, e.g.
   `<|tool_call>call:run_bash{command: <|"|>ls -la /tmp<|"|>}<tool_call|>`.
   The committed `_gemma4_forcing_ebnf` instead emits JSON-style **quoted** keys `{"command":value}` — a **format bug**: a model forced into that shape produces calls the real gemma4 parser cannot parse (`_gemma4_args_to_json` expects unquoted keys + `<|"|>` strings).
2. **The envelope is single special tokens**: `<|tool_call>`→id 48, `<tool_call|>`→id 49, `<|"|>`→id 52 (each one token; `call:`→ ordinary text `call`,`:`). So the open §3.2 question — *can an xgrammar EBNF over the tokenizer's vocab force a model to emit these specific special tokens?* — is real and **model-free-answerable** with just the Gemma tokenizer + xgrammar.

**⚡ Model-free feasibility PRE-RESOLVED (2026-06-04, throwaway probe — plan-grade due diligence):** ran the Task-2 checks inline against the Gemma tokenizer + xgrammar. Results:
- `accept_token(48)` (can xgrammar force the special token `<|tool_call>` as first token) = **True** for minimal / committed / corrected grammars → **forcing is construction-feasible → verdict `applied`**.
- Committed (JSON-quoted) EBNF **rejects** the real gemma4 exemplar (format bug confirmed); **corrected** EBNF (unquoted keys + `<|"|>` delimiters) **accepts** the real exemplar and **rejects** plain text.
- mlx_lm gemma4 parser round-trips the real exemplar → `{"name":"run_bash","arguments":{"command":"ls -la /tmp"}}` (auto/none load-path-compatible).

**→ Take Task 3a (correct the EBNF). Task 3b (documented_infeasible) is moot — retained below only for the record.** The fresh code session still runs the committed probe to produce the evidence artifact (Task 6), but the outcome is known.

**Live-bug note:** the committed grammar *compiles* at runtime, so today a Gemma `tool_choice:"required"` request logs `tool_choice_forcing_verdict:"applied"` yet forces JSON-quoted output the real gemma4 parser cannot `json.loads` → the call is silently dropped. Task 3a fixes this false-`applied` in already-pushed experimental code.

**Posture:** **Stays `experimental`; promotes nothing; §1a untouched.** Both `applied`/`documented_infeasible` were acceptable per spec §7 DoD #2; the probe landed `applied`.

**Reference spec:** `docs/architect/design/R1-tool-calling-family-parity-spec.md`. **Reference probe to mirror:** `scripts/probe/phase2_tool_choice_forcing_feasibility.py` (the proven model-free pattern: load tokenizer → `xgr.TokenizerInfo.from_huggingface` → `GrammarCompiler` → `GrammarMatcher.accept_string` + `is_completed`).

---

## File structure

- **Create:** `scripts/probe/r1_gemma_tool_calling_feasibility.py` — the R1 probe. Two tiers behind subcommands: `model-free` (default; ~MB; runs now, free) and `live` (gated; needs running 8066 + Gemma ~62GB). Pure-ish: prints a JSON verdict to stdout and writes an evidence artifact. No runtime import beyond the public functions under test + mlx_lm's gemma4 parser.
- **Modify:** `owlmlx/runtime/mlx_native_backend.py` — *only* `_gemma4_forcing_ebnf` (correct the format) **or** the gemma4 dispatch branch of `_tool_choice_forcing_ebnf` (retire to `None` if infeasible). Exactly one of these, decided by Task 2.
- **Modify/Test:** `tests/test_mlx_native_backend.py` — extend the xgrammar-compile test to gemma4; add a builder-content test for the corrected format **or** a graceful-degrade test for the infeasible branch.
- **Create:** `files/evidence/owlmlx/replacement/r1-tool-parity/<UTC>-r1-gemma-feasibility-*.json` — probe verdict + reproduction metadata.
- **Modify (docs, Task 7):** `docs/architect/design/R1-tool-calling-family-parity-spec.md` (status), `docs/architect/design/README.md` (R-series row), and the capability-matrix wording in the relevant source-of-truth doc; plus the R-series memory.

---

## Task 1: Extend the xgrammar-compile test to gemma4 (model-free, free)

The existing compile test (line 762) only parses the **qwen** EBNF. Prove the **gemma4** EBNF string is at least syntactically valid EBNF — independent of the format/feasibility question — so a later format edit can't silently produce un-parseable grammar.

**Files:**
- Test: `tests/test_mlx_native_backend.py` (modify near line 762)

- [ ] **Step 1: Write the failing assertion (extend the existing test)**

Add to the body of `test_tool_choice_forcing_ebnf_compiles_as_valid_xgrammar` (after the existing qwen assertion at line 772):

```python
    gemma_ebnf = _tool_choice_forcing_ebnf(
        _FORCE_TOOLS, "required", parser_family="gemma4"
    )
    assert gemma_ebnf is not None
    # from_ebnf parses the grammar without a tokenizer -> proves valid EBNF.
    assert xgr.Grammar.from_ebnf(gemma_ebnf) is not None
```

- [ ] **Step 2: Run it**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py::test_tool_choice_forcing_ebnf_compiles_as_valid_xgrammar -v`
Expected: PASS if xgrammar is installed (the committed gemma4 EBNF is syntactically valid EBNF, only its *content* is wrong); SKIP if xgrammar absent. If it unexpectedly FAILS on `from_ebnf`, that is itself a finding — record it and stop to investigate before Task 2.

- [ ] **Step 3: Commit**

```bash
git add tests/test_mlx_native_backend.py
git commit -m "test(r1): assert gemma4 forcing EBNF is valid xgrammar

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Write + run the model-free feasibility probe (the decisive gate, free)

This is the heart of R1-(A). It answers, with only the Gemma **tokenizer** (~MB, no 62GB weights):
(1) does mlx_lm's real gemma4 parser round-trip a hand-built real-format exemplar? (sanity on the exemplar)
(2) does the **committed** gemma4 forcing EBNF accept that real exemplar? (expected: NO — the format bug)
(3) does a **corrected** gemma4 forcing EBNF (unquoted keys + `<|"|>` delims) compile against the Gemma `TokenizerInfo` and accept-good / reject-bad? (this is the feasibility verdict)

**Files:**
- Create: `scripts/probe/r1_gemma_tool_calling_feasibility.py`

- [ ] **Step 1: Write the probe (model-free tier)**

```python
"""R1 Gemma tool-calling feasibility probe.

R1 component (A). Resolves the open feasibility question from the R1 spec
(docs/architect/design/R1-tool-calling-family-parity-spec.md, sec 3.2): can an
xgrammar EBNF over the Gemma tokenizer's vocab FORCE a model to emit a parseable
gemma4 tool call, whose envelope is built from SINGLE SPECIAL TOKENS
(<|tool_call>=48, <tool_call|>=49, <|"|>=52)?

Two tiers:
  model-free (default): tokenizer + xgrammar only (~MB). Decides the forcing
    construction verdict (applied | documented_infeasible) and confirms the
    gemma4 parser round-trips a real-format exemplar (auto/none load-path).
  live: hits a running owlmlx (8066) with Gemma loaded for end-to-end
    auto/none/forced confirmation. Costs ~62GB load -- gated, run on request.

scripts/ (not owlmlx/) per the AGENTS module-as-spec rule: probe, no runtime
consumer, no capability promotion. Stays experimental.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request

DEFAULT_MODEL_DIR = "/Users/yeemio/AI/Agent/models/gemma-4-31B-it-4bit"

# Real gemma4 wire format (verified against mlx_lm tool_parsers/gemma4.py):
# unquoted keys, <|"|>...<|"|> string delimiters, call:NAME{...} envelope.
GOOD_GEMMA_CALL = (
    "<|tool_call>call:run_bash{command: " '<|"|>ls -la /tmp<|"|>' "}<tool_call|>"
)
GOOD_GEMMA_READ = (
    "<|tool_call>call:read_file{path: " '<|"|>/tmp/x<|"|>' "}<tool_call|>"
)
PLAIN_TEXT = "I will run ls -la /tmp for you now."

# The COMMITTED gemma4 forcing EBNF (178292fa) -- JSON-quoted keys (the suspected
# format bug). Reproduced here so the probe can demonstrate the mismatch.
COMMITTED_EBNF = "\n".join(
    [
        r'root ::= "<|tool_call>call:" fname "{" plist "}<tool_call|>"',
        'fname ::= "run_bash" | "read_file"',
        r'plist ::= pair ("," pair)*',
        r'pair ::= "\"" pname "\":" value',
        'pname ::= "command" | "path"',
        r'value ::= [^,}]*',
    ]
)

# CORRECTED gemma4 forcing EBNF candidate: unquoted keys, <|"|>-delimited string
# values, matching the real parser. This is what Task 3a would land if feasible.
CORRECTED_EBNF = "\n".join(
    [
        r'root ::= "<|tool_call>call:" fname "{" plist "}<tool_call|>"',
        'fname ::= "run_bash" | "read_file"',
        r'plist ::= pair ("," " "? pair)*',
        r'pair ::= pname ": " strval',
        'pname ::= "command" | "path"',
        r'strval ::= "<|\"|>" [^<]* "<|\"|>"',
    ]
)


def _gemma4_parser_roundtrips(exemplar: str) -> tuple[bool, str]:
    try:
        from mlx_lm.tool_parsers import gemma4
    except Exception as exc:  # noqa: BLE001
        return False, f"import gemma4 parser failed: {type(exc).__name__}: {exc}"
    # The parser regex matches `call:NAME{...}`; the envelope markers are context.
    try:
        parsed = gemma4.parse_tool_call(exemplar)
    except Exception as exc:  # noqa: BLE001
        return False, f"parse_tool_call raised: {type(exc).__name__}: {exc}"
    ok = isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed
    return ok, json.dumps(parsed) if ok else f"unexpected parse result: {parsed!r}"


def _accepts(compiled, exemplar: str) -> bool:
    import xgrammar as xgr

    matcher = xgr.GrammarMatcher(compiled)
    try:
        accepted = bool(matcher.accept_string(exemplar))
    except Exception as exc:  # noqa: BLE001
        print(f"      accept_string error: {type(exc).__name__}: {str(exc)[:160]}")
        return False
    return accepted and bool(matcher.is_completed())


def run_model_free(model_dir: str, vocab_size: int | None) -> dict:
    import xgrammar as xgr
    from transformers import AutoTokenizer

    result: dict = {"tier": "model-free", "model_dir": model_dir, "checks": {}}

    rt_ok, rt_detail = _gemma4_parser_roundtrips(GOOD_GEMMA_CALL)
    result["checks"]["gemma4_parser_roundtrips_real_exemplar"] = rt_ok
    result["gemma4_parse_detail"] = rt_detail

    print(f"[probe] loading tokenizer from {model_dir} ...", flush=True)
    hf_tok = AutoTokenizer.from_pretrained(model_dir)
    vsize = vocab_size or len(hf_tok)
    tok_info = xgr.TokenizerInfo.from_huggingface(hf_tok, vocab_size=vsize)
    compiler = xgr.GrammarCompiler(tok_info)
    result["vocab_size"] = tok_info.vocab_size

    # (2) committed EBNF should REJECT the real exemplar (demonstrates the bug).
    committed = compiler.compile_grammar(xgr.Grammar.from_ebnf(COMMITTED_EBNF))
    committed_accepts_real = _accepts(committed, GOOD_GEMMA_CALL)
    result["checks"]["committed_ebnf_rejects_real_call"] = not committed_accepts_real

    # (3) corrected EBNF: accepts both real calls, rejects plain text.
    try:
        corrected = compiler.compile_grammar(xgr.Grammar.from_ebnf(CORRECTED_EBNF))
        c_run = _accepts(corrected, GOOD_GEMMA_CALL)
        c_read = _accepts(corrected, GOOD_GEMMA_READ)
        c_plain = _accepts(corrected, PLAIN_TEXT)
    except Exception as exc:  # noqa: BLE001
        result["checks"]["corrected_ebnf_compiles"] = False
        result["corrected_compile_error"] = f"{type(exc).__name__}: {exc}"
        c_run = c_read = c_plain = False
    else:
        result["checks"]["corrected_ebnf_compiles"] = True
    result["checks"]["corrected_accepts_run_bash"] = c_run
    result["checks"]["corrected_accepts_read_file"] = c_read
    result["checks"]["corrected_rejects_plain_text"] = not c_plain

    forcing_feasible = bool(
        result["checks"].get("corrected_ebnf_compiles")
        and c_run
        and c_read
        and not c_plain
    )
    result["forcing_construction_verdict"] = (
        "applied" if forcing_feasible else "documented_infeasible"
    )
    # auto/none load-path: parser round-trips a real exemplar with no owlmlx change.
    result["auto_none_verdict"] = (
        "load-path-compatible" if rt_ok else "documented_gap"
    )
    result["all_checks_pass"] = all(result["checks"].values())
    return result


def run_live(base_url: str, model: str) -> dict:
    """End-to-end against a running owlmlx (Gemma must be loadable -- ~62GB)."""
    result: dict = {"tier": "live", "base_url": base_url, "model": model, "checks": {}}
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_bash",
                "description": "Run a bash command",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
        }
    ]

    def _chat(tool_choice) -> dict:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": "List files in /tmp."}],
            "tools": tools,
            "tool_choice": tool_choice,
            "max_tokens": 256,
            "stream": False,
        }
        req = urllib.request.Request(
            base_url.rstrip("/") + "/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read())

    auto = _chat("auto")
    auto_msg = auto["choices"][0]["message"]
    result["auto_finish_reason"] = auto["choices"][0].get("finish_reason")
    result["checks"]["auto_emits_tool_call"] = bool(auto_msg.get("tool_calls"))
    result["auto_tool_calls"] = auto_msg.get("tool_calls")

    forced = _chat("required")
    forced_msg = forced["choices"][0]["message"]
    result["forced_finish_reason"] = forced["choices"][0].get("finish_reason")
    result["checks"]["forced_emits_tool_call"] = bool(forced_msg.get("tool_calls"))
    result["forced_tool_calls"] = forced_msg.get("tool_calls")
    result["all_checks_pass"] = all(result["checks"].values())
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    mf = sub.add_parser("model-free")
    mf.add_argument("--model", default=DEFAULT_MODEL_DIR)
    mf.add_argument("--vocab-size", type=int, default=None)
    lv = sub.add_parser("live")
    lv.add_argument("--base-url", default="http://127.0.0.1:8066")
    lv.add_argument("--model", default="gemma-4-31B-it-4bit")
    args = ap.parse_args()

    if args.cmd == "model-free":
        result = run_model_free(args.model, args.vocab_size)
    else:
        result = run_live(args.base_url, args.model)

    print("\n[probe] results:")
    for name, ok in result["checks"].items():
        print(f"   [{'PASS' if ok else 'FAIL'}] {name}")
    print("\n[probe] verdict JSON:")
    print(json.dumps(result, indent=2))
    return 0 if result.get("all_checks_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the model-free probe**

Run: `.venv/bin/python scripts/probe/r1_gemma_tool_calling_feasibility.py model-free`
Expected, check-by-check:
- `gemma4_parser_roundtrips_real_exemplar` = PASS (confirms the exemplar is real and `auto`/`none` is load-path-compatible).
- `committed_ebnf_rejects_real_call` = PASS (confirms the committed JSON-quoted EBNF really is format-wrong).
- `corrected_ebnf_compiles` + `corrected_accepts_run_bash` + `corrected_accepts_read_file` + `corrected_rejects_plain_text`: **this cluster is the feasibility verdict.** If all PASS → `forcing_construction_verdict: applied` → Task 3a. If `corrected` rejects the good exemplar or fails to compile (xgrammar cannot constrain to special tokens 48/49/52) → `documented_infeasible` → Task 3b.

- [ ] **Step 3: Record the raw verdict**

Save stdout to a scratch file you will fold into the evidence artifact in Task 6:
```bash
.venv/bin/python scripts/probe/r1_gemma_tool_calling_feasibility.py model-free \
  | tee /tmp/r1-gemma-model-free.out
```
Note the `forcing_construction_verdict` value — it selects Task 3a vs 3b. **Do not commit yet** (commit the probe with the matching runtime change in Task 4).

---

## Task 3: Land the gemma4 forcing outcome the probe dictates

Do **exactly one** of 3a / 3b based on `forcing_construction_verdict` from Task 2.

### Task 3a — FEASIBLE (`forcing_construction_verdict == "applied"`): correct the EBNF

**Files:**
- Modify: `owlmlx/runtime/mlx_native_backend.py:522-547` (`_gemma4_forcing_ebnf`)
- Test: `tests/test_mlx_native_backend.py` (dispatch test, line 722)

- [ ] **Step 1: Write the failing builder-content test**

Replace the gemma assertions in `test_tool_choice_forcing_ebnf_dispatches_by_tool_parser_family` (lines 734-736) with the real-format expectations:

```python
    assert gemma is not None and "<|tool_call>call:" in gemma
    assert "run_bash" in gemma and "read_file" in gemma
    assert "command" in gemma and "path" in gemma
    # real gemma4 format: unquoted keys + <|"|> string delimiters, NOT JSON quotes
    assert r'"\"" pname "\":"' not in gemma  # no JSON-quoted keys
    assert r'<|\"|>' in gemma or '<|"|>' in gemma  # uses the gemma string delimiter
```

- [ ] **Step 2: Run it to confirm it fails against the committed builder**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py::test_tool_choice_forcing_ebnf_dispatches_by_tool_parser_family -v`
Expected: FAIL (committed builder emits JSON-quoted keys).

- [ ] **Step 3: Correct `_gemma4_forcing_ebnf`**

Replace the body of `_gemma4_forcing_ebnf` (mlx_native_backend.py:522) with the format the Task-2 probe proved acceptable (unquoted keys + `<|"|>` string delimiters). Use the exact EBNF lines the probe's `CORRECTED_EBNF` validated, generalized over `funcs`/`param_names`:

```python
def _gemma4_forcing_ebnf(funcs: list[str], param_names: list[str]) -> str:
    """EBNF constraining output to the real gemma4 tool-call envelope.

    Real gemma4 format (mlx_lm tool_parsers/gemma4.py): ``call:NAME{key: <|"|>v<|"|>}``
    with UNQUOTED keys and ``<|"|>``-delimited string values, wrapped in the
    ``<|tool_call> ... <tool_call|>`` envelope. Mirrors the qwen3_coder scope:
    constrain envelope + function name + parameter keys, leave values loose.
    Validated model-free against the Gemma tokenizer by
    scripts/probe/r1_gemma_tool_calling_feasibility.py.
    """
    fname_alt = " | ".join(_ebnf_string_literal(f) for f in funcs)
    if param_names:
        pname_alt = " | ".join(_ebnf_string_literal(p) for p in param_names)
        return "\n".join(
            [
                r'root ::= "<|tool_call>call:" fname "{" plist "}<tool_call|>"',
                "fname ::= " + fname_alt,
                r'plist ::= pair ("," " "? pair)*',
                r'pair ::= pname ": " strval',
                "pname ::= " + pname_alt,
                r'strval ::= "<|\"|>" [^<]* "<|\"|>"',
            ]
        )
    return "\n".join(
        [
            r'root ::= "<|tool_call>call:" fname "{}" "<tool_call|>"',
            "fname ::= " + fname_alt,
        ]
    )
```

> If the Task-2 probe's `CORRECTED_EBNF` differed from the above (e.g. spacing around `:` or the comma), copy the **exact** lines the probe validated — the probe is the source of truth, not this snippet.

- [ ] **Step 4: Run the builder test + the existing dispatch/compile/infer tests**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py -k "tool_choice_forcing or forcing_family" -v`
Expected: PASS (4+ tests).

- [ ] **Step 5: Re-run the probe to confirm the shipped builder matches**

Add a guard to the probe so it also checks the *shipped* builder, then re-run. Append to `run_model_free` before the verdict (Task 2's file), then re-run `model-free`:

```python
    from owlmlx.runtime.mlx_native_backend import _gemma4_forcing_ebnf

    shipped = compiler.compile_grammar(
        xgr.Grammar.from_ebnf(
            _gemma4_forcing_ebnf(["run_bash", "read_file"], ["command", "path"])
        )
    )
    result["checks"]["shipped_builder_accepts_real_call"] = _accepts(
        shipped, GOOD_GEMMA_CALL
    )
```
Run: `.venv/bin/python scripts/probe/r1_gemma_tool_calling_feasibility.py model-free`
Expected: `shipped_builder_accepts_real_call` = PASS. Proceed to Task 4.

### Task 3b — INFEASIBLE (`forcing_construction_verdict == "documented_infeasible"`): retire gemma4 forcing to graceful degrade

If xgrammar cannot constrain to the special-token envelope, do **not** ship a grammar that compiles but can never be satisfied (it would falsely log `tool_choice_forcing_verdict="applied"`). Retire the gemma4 branch to `None` so the runtime degrades to unforced and the diagnostic is honest.

**Files:**
- Modify: `owlmlx/runtime/mlx_native_backend.py:620-624` (dispatch) and `:1525-1543` (verdict wiring)
- Test: `tests/test_mlx_native_backend.py`

- [ ] **Step 1: Write the failing test — gemma4 forcing degrades to None + documented_infeasible**

```python
def test_gemma4_tool_choice_forcing_documented_infeasible() -> None:
    from owlmlx.runtime.mlx_native_backend import _tool_choice_forcing_ebnf

    # gemma4 special-token envelope is not xgrammar-expressible (see probe);
    # forcing must degrade to None rather than ship an unenforceable grammar.
    assert (
        _tool_choice_forcing_ebnf(_FORCE_TOOLS, "required", parser_family="gemma4")
        is None
    )
```

- [ ] **Step 2: Run it (fails — committed code returns an EBNF string)**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py::test_gemma4_tool_choice_forcing_documented_infeasible -v`
Expected: FAIL.

- [ ] **Step 3: Retire the gemma4 dispatch branch**

In `_tool_choice_forcing_ebnf` (line 620-623), drop the gemma4 case so it falls through to `None`:

```python
    if parser_family == "qwen3_coder":
        return _qwen3_coder_forcing_ebnf(forced_names, param_names)
    # gemma4 forcing is documented_infeasible: the tool-call envelope is built
    # from single special tokens (<|tool_call>=48, <tool_call|>=49, <|"|>=52)
    # that xgrammar cannot constrain to (see
    # scripts/probe/r1_gemma_tool_calling_feasibility.py). Degrade to unforced;
    # auto/none still work via the generic gemma4 parser.
    return None
```

- [ ] **Step 4: Make the runtime verdict honest for gemma4-requested-but-degraded**

At the wiring (line 1542), the `forcing_ebnf is None` + `forcing_requested` path currently only labels `unsupported` when `forcing_family == "unsupported"`. Add a `gemma4` documented-infeasible label. Replace lines 1542-1543:

```python
        elif forcing_requested and forcing_family == "unsupported":
            forcing_detail["tool_choice_forcing_verdict"] = "unsupported"
        elif forcing_requested and forcing_family == "gemma4":
            forcing_detail["tool_choice_forcing_verdict"] = "documented_infeasible"
            forcing_detail["tool_choice_forcing_infeasible_family"] = "gemma4"
```

- [ ] **Step 5: Add a generate-level test mirroring `test_native_backend_generate_records_unsupported_tool_choice_family` for gemma4**

```python
def test_native_backend_generate_records_gemma4_forcing_documented_infeasible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = types.ModuleType("mlx_lm")
    captured: dict[str, object] = {}

    class _GemmaTokenizer:
        tool_call_start = "<|tool_call>"

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), _GemmaTokenizer())

    def fake_generate(model, tokenizer, *, prompt, max_tokens, logits_processors=None):  # type: ignore[no-untyped-def]
        captured["logits_processors"] = logits_processors
        return "done"

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    previous_mlx_lm = sys.modules.get("mlx_lm")
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")
        result = backend.generate(
            "fake-model", "hi", max_tokens=3, tools=_force_tool(), tool_choice="required"
        )
        assert result.ok is True
        assert captured["logits_processors"] is None
        assert result.detail["tool_choice_forcing_verdict"] == "documented_infeasible"
        assert result.detail["tool_choice_forcing_family"] == "gemma4"
    finally:
        if previous_mlx_lm is None:
            sys.modules.pop("mlx_lm", None)
        else:
            sys.modules["mlx_lm"] = previous_mlx_lm
        importlib.reload(mod)
```

- [ ] **Step 6: Run the gemma4 tests + full forcing cluster**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py -k "tool_choice_forcing or forcing_family or gemma4" -v`
Expected: PASS. Then proceed to Task 4.

> If 3b is taken, also drop or `pytest.mark.skip` the Task-1 gemma compile assertion's *content* expectations that no longer apply, but keep `from_ebnf` validity for the qwen path. Leave `_gemma4_forcing_ebnf` defined (still referenced by the dispatch test's prior behavior? no — remove its dispatch call). Keep the function only if a test still imports it; otherwise delete it and its Task-1 assertion to avoid dead code.

---

## Task 4: Full model-free suite + commit probe and runtime change together

**Files:** all of the above.

- [ ] **Step 1: Run the focused suite**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py -v`
Expected: all PASS (xgrammar-dependent tests SKIP only if xgrammar missing — it is installed here, so they should run).

- [ ] **Step 2: Run the broader native + openai-route regression slice**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py tests/test_server_routes_openai.py -q --continue-on-collection-errors`
Expected: PASS (the pre-existing `psutil`-missing collection error in `test_runtime_comparative_evidence_measured_runner` is unrelated; `--continue-on-collection-errors` isolates it).

- [ ] **Step 3: Commit (code + probe + tests in one commit; NO evidence yet, NO docs yet)**

Stage only R1-scope files (staging discipline — never sweep `uv.lock` / `owlmlx/speculative/*`):
```bash
git add scripts/probe/r1_gemma_tool_calling_feasibility.py \
        owlmlx/runtime/mlx_native_backend.py \
        tests/test_mlx_native_backend.py
git status   # verify ONLY these three are staged
git commit -m "feat(r1): gemma4 tool-call forcing feasibility probe + <applied|infeasible> outcome

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
(Pick the verb/summary to match the branch taken: `fix(r1): correct gemma4 forcing EBNF to real wire format` for 3a, or `fix(r1): retire gemma4 forcing to documented_infeasible graceful degrade` for 3b.)

---

## Task 5 (GATED — ~62GB Gemma load): live end-to-end confirmation — **DEFERRED**

> **DECISION 2026-06-05 (user):** live tier is **deferred**. R1 closes on model-free evidence — `auto`/`none` recorded as "load-path-compatible (live deferred)" and forcing as `applied` (model-free construction-confirmed). **Do NOT run this task** as part of the R1 closeout. Keep it here so it can be run later if/when "live-confirmed" wording is wanted; if run later, fold its output into the Task 6 evidence artifact and upgrade the Task 7 wording. The steps below are retained for that future run only.

**This is the only task that loads Gemma weights (~62GB). Per the cost-flag rule, surface cost + run-now-vs-defer before running it.** Without it, `auto`/`none` stays "load-path-compatible" (model-free) rather than "live-confirmed"; the R1 spec §7 DoD #1 explicitly accepts a documented gap in lieu of the live run.

**Pre-req:** owlmlx native daemon on `127.0.0.1:8066` (already a launchd daemon). Gemma must be loadable within the memory budget — if a large model is resident, the live request will trigger eviction (409 if it cannot fit; that is expected, not a probe failure).

- [ ] **Step 1: Confirm the daemon is up**

Run: `curl -s http://127.0.0.1:8066/healthz`
Expected: `{"ok": true, ...}`.

- [ ] **Step 2: Run the live tier**

Run:
```bash
.venv/bin/python scripts/probe/r1_gemma_tool_calling_feasibility.py live \
  --base-url http://127.0.0.1:8066 --model gemma-4-31B-it-4bit \
  | tee /tmp/r1-gemma-live.out
```
Expected (first call loads Gemma — slow, minutes):
- `auto_emits_tool_call` = PASS, `auto_finish_reason` = `tool_calls`, `auto_tool_calls[0].function.name` = `run_bash` with parseable JSON `arguments`. This upgrades `auto`/`none` to **live-confirmed**.
- `forced_emits_tool_call`: if Task 3a was taken, expect PASS and inspect that the emitted call parses; if Task 3b (infeasible), `forced` runs **unforced** — the model may or may not emit a call, and that is the documented graceful-degrade behavior (not a failure). Record whichever occurs.

- [ ] **Step 3: Record the live verdict** into `/tmp/r1-gemma-live.out` (already tee'd). No commit yet — folded into Task 6's evidence artifact.

---

## Task 6: Write the evidence artifact

**Files:**
- Create: `files/evidence/owlmlx/replacement/r1-tool-parity/<UTC>-r1-gemma-feasibility.json`

- [ ] **Step 1: Assemble the artifact**

Combine the model-free verdict (always) and the live verdict (if Task 5 ran) into one JSON with reproduction metadata. Use a UTC compact timestamp for the filename (e.g. `20260605T0000Z`). The artifact MUST contain: `owlmlx_commit` (`git rev-parse HEAD`), `model_id`, `model_dir`, both tier verdicts, the exact probe commands, and an honest `evidence_language` field per the calibration rule:

```json
{
  "round": "R1",
  "owlmlx_commit": "<git rev-parse HEAD>",
  "model_id": "gemma-4-31B-it-4bit",
  "model_dir": "/Users/yeemio/AI/Agent/models/gemma-4-31B-it-4bit",
  "model_free": { "...": "paste run_model_free JSON" },
  "live": { "...": "paste run_live JSON, or null if deferred" },
  "repro": {
    "model_free_cmd": "scripts/probe/r1_gemma_tool_calling_feasibility.py model-free",
    "live_cmd": "scripts/probe/r1_gemma_tool_calling_feasibility.py live --base-url http://127.0.0.1:8066 --model gemma-4-31B-it-4bit"
  },
  "evidence_language": {
    "auto_none": "live-confirmed | load-path-compatible (live deferred)",
    "forcing": "applied (model-free construction-confirmed [+ live-confirmed]) | documented_infeasible"
  },
  "promotes": "nothing; stays experimental"
}
```

- [ ] **Step 2: Commit the evidence (evidence-only commit)**

```bash
git add files/evidence/owlmlx/replacement/r1-tool-parity/
git commit -m "bench(r1): gemma tool-calling feasibility evidence (<verdict>)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Capability wording + spec/README/memory (docs-only commit)

**Files:**
- Modify: `docs/architect/design/R1-tool-calling-family-parity-spec.md` (Status line → closeout)
- Modify: `docs/architect/design/README.md` (R-series row for R1)
- Modify: the capability-matrix doc in `docs/source-of-truth/` that records tool-calling support (locate with `grep -rl "tool_choice\|tool-calling\|qwen3_coder" docs/source-of-truth/`)
- Modify: `/Users/yeemio/.claude/projects/-Users-yeemio-AI-gitrep-owlmlx/memory/project-owlmlx-replacement-r-series-state.md` + `MEMORY.md`

- [ ] **Step 1: Update wording — honest + calibrated**

State, in each doc, exactly what the evidence supports and nothing more:
- Qwen + Gemma native, OpenAI shape, tool-calling **`experimental`** (NOT promoted to supported; §1a untouched).
- Gemma `auto`/`none`: "live-confirmed" if Task 5 ran, else "load-path-compatible (live deferred)".
- Gemma forcing: `applied` (with "model-free construction-confirmed" and, if Task 5 ran and forced parsed, "live-confirmed") **or** `documented_infeasible` (special-token envelope not xgrammar-expressible; gracefully degrades to unforced). Cite the evidence artifact path.
- "promotes nothing."

- [ ] **Step 2: Commit (docs-only)**

```bash
git add docs/architect/design/R1-tool-calling-family-parity-spec.md \
        docs/architect/design/README.md \
        docs/source-of-truth/<capability-doc>.md
git commit -m "docs(r1): record tool-calling family parity verdict (experimental, promotes nothing)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
(Memory files are outside the repo — update them with the Write tool, not git.)

---

## Task 8: DoD self-check + final verification

- [ ] **Step 1: Walk the R1 spec §7 DoD and check each item**

Against `docs/architect/design/R1-tool-calling-family-parity-spec.md` §7:
1. Gemma `auto`/`none` live-confirmed OR documented gap — ✅ (Task 5 or documented in Task 6/7).
2. Family-aware forcing: qwen3_coder unchanged (verify `git diff 178292fa -- owlmlx/runtime/mlx_native_backend.py` touches no qwen path); gemma4 branch verdict = `applied` OR `documented_infeasible` — ✅.
3. Unknown family → None + `tool_choice_forcing_unsupported_family` — ✅ (pre-existing test).
4. Model-free tests: gemma4 builder/dispatch — ✅ (Tasks 1, 3).
5. Evidence + reproduction on disk — ✅ (Task 6).
6. Capability matrix wording, still experimental — ✅ (Task 7).
7. Zero unsourced claims; experimental stays; promotes nothing — ✅.

- [ ] **Step 2: Confirm qwen path untouched**

Run: `.venv/bin/python -m pytest tests/test_mlx_native_backend.py -k "qwen or qwen3_coder" -v`
Expected: PASS — no Qwen regression.

- [ ] **Step 3: Report** the R1 closeout: what the probe found, which branch (3a/3b) landed, whether live ran, the evidence path, and that R1 promotes nothing / stays `experimental`. Note remaining R-series gates (R2 control-plane closure; R4 Phase B sustained soak + default flip).

---

## Self-Review (run before handing off)

**Spec coverage (R1 §7 DoD):**
1. auto/none confirmation → Tasks 2 (model-free load-path) + 5 (live) + 6 (recorded). ✅
2. family-aware forcing verdict applied|documented_infeasible → Tasks 2→3a/3b. ✅
3. unknown family → None + diagnostic → pre-existing, re-verified Task 8. ✅
4. model-free gemma4 builder/dispatch tests → Tasks 1, 3. ✅
5. evidence + repro → Task 6. ✅
6. capability wording, experimental → Task 7. ✅
7. zero unsourced claims, promotes nothing → Tasks 6-8 calibration. ✅

**Placeholder scan:** the only deliberate branch is Task 3a vs 3b, fully specified on both sides and selected by a concrete probe field (`forcing_construction_verdict`). No TBD/TODO. The Task-3a EBNF snippet defers to the probe's validated `CORRECTED_EBNF` as source of truth — flagged explicitly.

**Type/name consistency:** probe subcommands `model-free`/`live`; functions `run_model_free`/`run_live`/`_accepts`/`_gemma4_parser_roundtrips`; verdict fields `forcing_construction_verdict`/`auto_none_verdict`/`all_checks_pass` used consistently across Tasks 2,3,5,6. Runtime detail keys (`tool_choice_forcing_verdict`, `tool_choice_forcing_family`, `tool_choice_forcing_infeasible_family`) match the wiring at mlx_native_backend.py:1521-1543.

**Discipline:** probe in `scripts/probe/`, tests in `tests/`, runtime change only edits the *existing* `mlx_native_backend.py` (no new `owlmlx/` module — AGENTS rule). Commits are scoped (code / evidence / docs separated). Stays `experimental`; no §1a promotion. Live tier (62GB) is gated behind an explicit cost-flag step. Push is NOT in this plan — authorization is requested separately.

---

## Execution Handoff

**Decisions locked (2026-06-05, user):**
- **Code lands in a FRESH session** (this session only wrote the plan — plan→code fresh-session rule). Start a new conversation and execute Tasks 1→4, then 6→8.
- **Live tier (Task 5) is DEFERRED.** Execute the model-free path only. R1 closes on model-free evidence.
- **Feasibility is pre-resolved to Task 3a** (correct the EBNF). Skip Task 3b. The fresh session still runs the committed model-free probe to produce the Task-6 evidence artifact, but the verdict is known: `applied` + format-bug fix.
- **Push needs explicit authorization.** The fix is a new commit on top of already-pushed `178292fa`; do not push without asking.

**Fresh-session runbook (model-free only):** Task 1 (gemma compile test) → Task 2 (write + run the probe) → Task 3a (correct `_gemma4_forcing_ebnf` + tests) → Task 4 (suite + scoped commit) → Task 6 (evidence artifact, `live: null` / "live deferred") → Task 7 (capability wording: forcing `applied` model-free construction-confirmed, auto/none "load-path-compatible (live deferred)", stays experimental) → Task 8 (DoD self-check, confirm Qwen untouched). Recommended executor: superpowers:subagent-driven-development (fresh subagent per task) or superpowers:executing-plans (inline with checkpoints).
