"""Phase-2 tool_choice forcing feasibility probe (MODEL-FREE).

Open question for Phase-2 #1 (`tool_choice` = "required" / named): can xgrammar
construct a grammar that FORCES a real Qwen3.6 to emit a parseable
`qwen3_coder` tool call (the `<tool_call><function=NAME>...` XML envelope), and
constrain it to a SPECIFIC function for named tool_choice?

This is model-free on purpose (loads only the tokenizer, ~MBs, no 35B weights):
the open question is grammar CONSTRUCTION, not generation. End-to-end
grammar-constrained generation on this model family is already proven by F-4.1
(`scripts/probe/f4_grammar_feasibility.py`), so if the tool-call envelope
grammar compiles and accepts-good / rejects-bad, forcing is feasible.

qwen3_coder is XML, not JSON, so this uses an EBNF grammar (`Grammar.from_ebnf`)
rather than the json_schema / structural_tag kinds the runner currently wires.

scripts/ (not owlmlx/) per the AGENTS module-as-spec rule: probe, no runtime
consumer, no capability promotion.
"""

from __future__ import annotations

import argparse
import sys

import xgrammar as xgr
from transformers import AutoTokenizer

DEFAULT_MODEL_DIR = "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit"
DEFAULT_VOCAB_SIZE = 248320  # Qwen3.6 text_config.vocab_size

# Exact qwen3_coder wire format (verified by the original tool-calling probe).
GOOD_RUN_BASH = (
    "<tool_call>\n<function=run_bash>\n"
    "<parameter=command>\nls -la /tmp\n</parameter>\n"
    "</function>\n</tool_call>"
)
GOOD_READ_FILE = (
    "<tool_call>\n<function=read_file>\n"
    "<parameter=path>\n/tmp/x\n</parameter>\n"
    "</function>\n</tool_call>"
)
PLAIN_TEXT = "I will run ls -la /tmp for you now."


def build_ebnf(funcs: list[str], params: list[str]) -> str:
    fn = " | ".join('"%s"' % f for f in funcs)
    pn = " | ".join('"%s"' % p for p in params)
    return "\n".join(
        [
            r'root ::= "<tool_call>\n<function=" fname ">\n" plist "</function>\n</tool_call>"',
            "fname ::= " + fn,
            "plist ::= param+",
            r'param ::= "<parameter=" pname ">\n" value "</parameter>\n"',
            "pname ::= " + pn,
            "value ::= [^<]*",
        ]
    )


def compile_ebnf(compiler: xgr.GrammarCompiler, ebnf: str):
    grammar = xgr.Grammar.from_ebnf(ebnf)
    return compiler.compile_grammar(grammar)


def check(compiled, exemplar: str) -> bool:
    matcher = xgr.GrammarMatcher(compiled)
    try:
        accepted = bool(matcher.accept_string(exemplar))
    except Exception as e:  # noqa: BLE001
        print(f"    accept_string error: {type(e).__name__}: {str(e)[:120]}")
        return False
    completed = bool(matcher.is_completed())
    return accepted and completed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL_DIR)
    ap.add_argument("--vocab-size", type=int, default=DEFAULT_VOCAB_SIZE)
    args = ap.parse_args()

    print(f"[probe] loading tokenizer from {args.model} …", flush=True)
    hf_tok = AutoTokenizer.from_pretrained(args.model)
    tok_info = xgr.TokenizerInfo.from_huggingface(hf_tok, vocab_size=args.vocab_size)
    compiler = xgr.GrammarCompiler(tok_info)
    print(f"[probe] xgrammar vocab_size={tok_info.vocab_size}", flush=True)

    checks: list[tuple[str, bool]] = []

    # 1) NAMED forcing: only run_bash is allowed.
    named = compile_ebnf(compiler, build_ebnf(["run_bash"], ["command", "path"]))
    checks.append(("named: accepts run_bash call", check(named, GOOD_RUN_BASH)))
    checks.append(("named: REJECTS read_file call", not check(named, GOOD_READ_FILE)))
    checks.append(("named: REJECTS plain text", not check(named, PLAIN_TEXT)))

    # 2) REQUIRED forcing: any tool in the set, but a tool call is mandatory.
    required = compile_ebnf(
        compiler, build_ebnf(["run_bash", "read_file"], ["command", "path"])
    )
    checks.append(("required: accepts run_bash call", check(required, GOOD_RUN_BASH)))
    checks.append(("required: accepts read_file call", check(required, GOOD_READ_FILE)))
    checks.append(("required: REJECTS plain text", not check(required, PLAIN_TEXT)))

    print("\n[probe] results:")
    all_pass = True
    for name, ok in checks:
        all_pass = all_pass and ok
        print(f"   [{'PASS' if ok else 'FAIL'}] {name}")

    verdict = "FEASIBLE" if all_pass else "NOT-FEASIBLE-AS-TESTED"
    print(f"\n[probe] VERDICT: tool_choice forcing via xgrammar EBNF = {verdict}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
