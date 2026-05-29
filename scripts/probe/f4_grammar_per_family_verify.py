"""F-4.2 Per-Family Grammar Construction Verification (model-free).

Resolves the F-4.2 design-grade spec §4 central design risk: the five F-4
families do NOT all want the same grammar, and `thinking_tag_closed` in
particular needs a structural tag rather than a plain JSON-schema grammar.

This probe is MODEL-FREE on purpose. It does not load a 35B model or generate
tokens; the end-to-end constrained-generation effect is already proven for
`json_schema_flat` by the main probe (`20260528T063524Z-...`). The open
question this probe answers is narrower and faster to test:

  For each family, does the chosen xgrammar construction
    (a) compile, and
    (b) accept a known-good exemplar while rejecting a known-bad one?

It uses ``GrammarMatcher.accept_string`` (whole-string accept) against
hand-written good/bad exemplars derived from the F-4 case fixtures
(`tests/fixtures/structured_output_invariance/f4_cases.jsonl`).

NOTE on the `enum_constrained` family: its schema legitimately contains the
string ``"supported"`` as one capability-label ENUM VALUE. That is a fixture
enum, NOT a claim that any owlmlx model (DSV4 or otherwise) is `supported`.
The evidence file inherits that enum value; do not read it as a capability
claim.

Output:
  files/evidence/owlmlx/bench/structured-output-invariance/
    <ts>-f4-2-per-family-grammar-verify.json

This script lives under scripts/ (not owlmlx/) per the AGENTS module-as-spec
rule; it has no runtime consumer and is a bench/probe verification.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import xgrammar as xgr
from transformers import AutoTokenizer

EVIDENCE_DIR = Path("files/evidence/owlmlx/bench/structured-output-invariance")
DEFAULT_MODEL_DIR = "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit"
DEFAULT_VOCAB_SIZE = 248320  # Qwen3.6 text_config.vocab_size


# Per-family grammar plan. Each entry:
#   kind: "json_schema" | "structural_tag"
#   schema: the JSON schema (for json_schema kind, or the post-trigger schema
#           for structural_tag kind)
#   begin/end: structural-tag trigger boundaries (structural_tag kind only)
#   good: an exemplar that MUST be accepted
#   bad:  an exemplar that MUST be rejected
FAMILIES: dict[str, dict[str, Any]] = {
    "json_schema_flat": {
        "kind": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["bugfix", "feature", "docs", "test"],
                },
                "priority": {"type": "integer"},
                "requires_review": {"type": "boolean"},
            },
            "required": ["task_id", "category", "priority", "requires_review"],
            "additionalProperties": False,
        },
        "good": '{"task_id": "F4-JSON-001", "category": "bugfix", "priority": 1, "requires_review": true}',
        # bad: category not in enum
        "bad": '{"task_id": "F4-JSON-001", "category": "not_a_category", "priority": 1, "requires_review": true}',
    },
    "function_call_arguments": {
        "kind": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "enum": ["apply_patch", "run_tests", "inspect_logs"],
                },
                "arguments": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "risk_level": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                    "required": ["target", "risk_level"],
                    "additionalProperties": False,
                },
            },
            "required": ["tool_name", "arguments"],
            "additionalProperties": False,
        },
        "good": '{"tool_name": "run_tests", "arguments": {"target": "tests/test_x.py", "risk_level": "low"}}',
        # bad: missing required "arguments"
        "bad": '{"tool_name": "run_tests"}',
    },
    "nested_object": {
        "kind": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "diagnosis": {
                    "type": "object",
                    "properties": {
                        "root_cause": {"type": "string"},
                        "evidence": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "summary": {"type": "string"},
                                },
                                "required": ["source", "summary"],
                                "additionalProperties": False,
                            },
                        },
                        "next_action": {
                            "type": "object",
                            "properties": {
                                "kind": {
                                    "type": "string",
                                    "enum": ["retry", "fix", "escalate"],
                                },
                                "owner": {
                                    "type": "string",
                                    "enum": ["runtime", "operator"],
                                },
                            },
                            "required": ["kind", "owner"],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["root_cause", "evidence", "next_action"],
                    "additionalProperties": False,
                }
            },
            "required": ["diagnosis"],
            "additionalProperties": False,
        },
        "good": '{"diagnosis": {"root_cause": "schema drift", "evidence": [{"source": "log", "summary": "parse failed"}], "next_action": {"kind": "fix", "owner": "runtime"}}}',
        # bad: next_action.kind not in enum
        "bad": '{"diagnosis": {"root_cause": "x", "evidence": [], "next_action": {"kind": "ignore", "owner": "runtime"}}}',
    },
    "enum_constrained": {
        "kind": "json_schema",
        # NOTE: "supported" below is a fixture ENUM VALUE, not a capability claim.
        "schema": {
            "type": "object",
            "properties": {
                "capability_label": {
                    "type": "string",
                    "enum": ["supported", "partial", "experimental", "not_in_scope"],
                },
                "reason_code": {"type": "string"},
            },
            "required": ["capability_label", "reason_code"],
            "additionalProperties": False,
        },
        "good": '{"capability_label": "experimental", "reason_code": "measurement_only_smoke"}',
        # bad: capability_label not in enum
        "bad": '{"capability_label": "totally_made_up", "reason_code": "x"}',
    },
    "thinking_tag_closed": {
        "kind": "structural_tag",
        # The reasoning envelope <thinking>...</thinking> is free text; the
        # structural tag triggers on the closing tag and constrains the JSON
        # that follows. begin is the trigger that switches into schema mode.
        "begin": "</thinking>",
        "schema": {
            "type": "object",
            "properties": {
                "final": {"type": "string"},
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
            },
            "required": ["final", "confidence"],
            "additionalProperties": False,
        },
        "end": "",
        "good": '<thinking>short reasoning</thinking>{"final": "done", "confidence": "low"}',
        # bad: confidence not in enum
        "bad": '<thinking>x</thinking>{"final": "done", "confidence": "certain"}',
    },
}


def build_compiled_grammar(
    compiler: xgr.GrammarCompiler, plan: dict[str, Any]
) -> tuple[xgr.CompiledGrammar, str]:
    """Return (compiled_grammar, construction_note). Raises on compile failure."""
    kind = plan["kind"]
    if kind == "json_schema":
        cg = compiler.compile_json_schema(json.dumps(plan["schema"]))
        return cg, "compile_json_schema"
    if kind == "structural_tag":
        # xgrammar's structural tag triggers on `begin`, constrains `schema`,
        # closes on `end`. In 0.2.1 the StructuralTag pydantic class exposes
        # only {type, format} (OpenAI-style) and does not take begin/end
        # directly; the StructuralTagItem(begin, schema, end) + triggers form
        # is reached via the (deprecated-but-functional) 2-arg
        # compile_structural_tag(tags, triggers) call. Verified working in
        # 0.2.1. F-4.2a code-grade should prefer the StructuralTag-class form
        # if it can express the begin/end envelope there; otherwise this
        # legacy form is the documented fallback.
        item = xgr.StructuralTagItem(
            begin=plan["begin"],
            schema=json.dumps(plan["schema"]),
            end=plan["end"],
        )
        cg = compiler.compile_structural_tag([item], [plan["begin"]])
        return cg, "compile_structural_tag([StructuralTagItem], [trigger]) legacy-2arg"
    raise ValueError(f"unknown grammar kind: {kind}")


def check_accept(compiled: xgr.CompiledGrammar, exemplar: str) -> dict[str, Any]:
    """Feed an exemplar string into a fresh matcher; report acceptance."""
    matcher = xgr.GrammarMatcher(compiled)
    try:
        accepted = matcher.accept_string(exemplar)
    except Exception as e:  # noqa: BLE001
        return {"accepted": False, "error": f"{type(e).__name__}:{str(e)[:120]}"}
    return {
        "accepted": bool(accepted),
        "terminated_after": bool(matcher.is_terminated()),
        "completed_after": bool(matcher.is_completed()),
        "error": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="F-4.2 per-family grammar construction verification (model-free)"
    )
    parser.add_argument("--model", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--vocab-size", type=int, default=DEFAULT_VOCAB_SIZE)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    args = parser.parse_args()

    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.evidence_dir / f"{ts}-f4-2-per-family-grammar-verify.json"

    print(f"[verify] loading tokenizer from {args.model} …", flush=True)
    hf_tok = AutoTokenizer.from_pretrained(args.model)
    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        hf_tok, vocab_size=args.vocab_size
    )
    compiler = xgr.GrammarCompiler(tokenizer_info)
    print(f"[verify] xgrammar vocab_size={tokenizer_info.vocab_size}", flush=True)

    results: dict[str, Any] = {}
    all_pass = True
    for family, plan in FAMILIES.items():
        entry: dict[str, Any] = {"kind": plan["kind"]}
        try:
            compiled, note = build_compiled_grammar(compiler, plan)
            entry["compiled"] = True
            entry["construction"] = note
        except Exception as e:  # noqa: BLE001
            entry["compiled"] = False
            entry["construction"] = None
            entry["compile_error"] = f"{type(e).__name__}:{str(e)[:200]}"
            entry["family_pass"] = False
            all_pass = False
            results[family] = entry
            print(f"[verify] {family:26s} COMPILE-FAIL {entry['compile_error']}", flush=True)
            continue

        good = check_accept(compiled, plan["good"])
        bad = check_accept(compiled, plan["bad"])
        entry["good_exemplar"] = good
        entry["bad_exemplar"] = bad
        # Family passes if the good exemplar is accepted AND the bad one is not.
        family_pass = bool(good.get("accepted")) and not bool(bad.get("accepted"))
        entry["family_pass"] = family_pass
        all_pass = all_pass and family_pass
        results[family] = entry
        status = "PASS" if family_pass else "FAIL"
        print(
            f"[verify] {family:26s} {status}  "
            f"good_accept={good.get('accepted')} bad_accept={bad.get('accepted')} "
            f"({entry['construction']})",
            flush=True,
        )

    summary = {
        "schema_version": "f4.2.per_family_grammar_verify.v1",
        "phase": "f4-2-per-family-grammar-verify",
        "ts_utc": ts,
        "model_dir": args.model,
        "vocab_size": args.vocab_size,
        "xgrammar_version": "0.2.1",
        "model_free": True,
        "all_families_pass": all_pass,
        "families": results,
        "notes": (
            "Model-free grammar compile + accept_string verification. The "
            "enum_constrained family schema contains 'supported' as a fixture "
            "ENUM VALUE; that is not a capability claim about any owlmlx model. "
            "End-to-end constrained generation is proven separately for "
            "json_schema_flat by 20260528T063524Z-f4-grammar-feasibility-probe."
        ),
        "design_risk_resolved": (
            "F-4.2 design spec §4 per-family grammar strategy: confirms which "
            "families compile via compile_json_schema and whether "
            "thinking_tag_closed is expressible via compile_structural_tag."
        ),
    }
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[verify] wrote {out_path}", flush=True)
    print(f"[verify] ALL FAMILIES PASS: {all_pass}", flush=True)
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
