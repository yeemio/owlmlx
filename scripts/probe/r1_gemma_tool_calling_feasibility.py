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

    # (4) shipped builder check: confirm the corrected runtime function matches.
    try:
        from owlmlx.runtime.mlx_native_backend import _gemma4_forcing_ebnf

        shipped = compiler.compile_grammar(
            xgr.Grammar.from_ebnf(
                _gemma4_forcing_ebnf(["run_bash", "read_file"], ["command", "path"])
            )
        )
        result["checks"]["shipped_builder_accepts_real_call"] = _accepts(
            shipped, GOOD_GEMMA_CALL
        )
    except Exception as exc:  # noqa: BLE001
        result["checks"]["shipped_builder_accepts_real_call"] = False
        result["shipped_builder_error"] = f"{type(exc).__name__}: {exc}"

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
