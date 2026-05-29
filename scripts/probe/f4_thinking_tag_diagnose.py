"""F-4 residual #2 diagnosis: thinking_tag_closed trigger mismatch.

F-4.2b showed thinking_tag_closed breaks 12/12 across all models. The
structural tag triggers on '</thinking>', but reasoning models emit their
NATIVE '<think>' channel (from the chat template), never '<thinking>', so the
trigger never fires and the model rambles until max_tokens.

This probe tests, in-process on one Qwen model, whether re-pointing the
structural tag at the model's actual '</think>' tag (plus a larger token
budget for the reasoning) yields '<think>...</think>{valid json}'. It reuses
the production grammar builder so the diagnosis reflects real behavior.

Three arms on the same prompt:
  A. control (no grammar)            — observe native reasoning behavior
  B. grammar trigger on </thinking>  — confirm the current (broken) trigger
  C. grammar trigger on </think>     — the proposed fix

NOT committed as a gate; this is a diagnostic that decides the #2 fix shape.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import mlx.core as mx
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

from owlmlx.runtime.mlx_lm_runner import _build_grammar_logits_processor

MODEL_DIR = "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit"

PROMPT = (
    "Return a closed thinking envelope followed by JSON only. Format exactly: "
    '<thinking>one short sentence</thinking>{"final": string, "confidence": '
    '"low"|"medium"|"high"}. Do not add markdown or extra prose.'
)

INNER_SCHEMA = {
    "type": "object",
    "properties": {
        "final": {"type": "string"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["final", "confidence"],
    "additionalProperties": False,
}


def run_arm(model, tokenizer, label, grammar_spec, max_tokens):
    sampler = make_sampler(temp=0.3)
    procs = []
    if grammar_spec is not None:
        procs.append(_build_grammar_logits_processor(tokenizer, grammar_spec))
    parts = []
    t0 = time.monotonic()
    for resp in stream_generate(
        model, tokenizer, prompt=tokenizer.encode(PROMPT),
        max_tokens=max_tokens, sampler=sampler, logits_processors=procs,
    ):
        parts.append(resp.text)
    out = "".join(parts)
    dt = time.monotonic() - t0
    # Does valid JSON appear after the model's reasoning close tag?
    json_ok = False
    for close in ("</think>", "</thinking>"):
        if close in out:
            after = out.split(close, 1)[1].strip()
            try:
                json.loads(after)
                json_ok = True
                break
            except Exception:
                pass
    print(f"\n=== ARM {label} (max_tokens={max_tokens}, {dt:.1f}s) ===", flush=True)
    print(f"  json_after_close_ok={json_ok}", flush=True)
    print(f"  output[:400]={out[:400]!r}", flush=True)
    print(f"  output[-160:]={out[-160:]!r}", flush=True)
    return {"label": label, "json_after_close_ok": json_ok, "len": len(out)}


def main() -> int:
    if not Path(MODEL_DIR).is_dir():
        print(f"model dir absent: {MODEL_DIR}")
        return 3
    print(f"loading {MODEL_DIR} …", flush=True)
    model, tokenizer = load(MODEL_DIR)

    results = []
    results.append(run_arm(model, tokenizer, "A-control-no-grammar", None, 512))
    results.append(
        run_arm(
            model, tokenizer, "B-trigger-</thinking>",
            {"kind": "structural_tag", "begin": "</thinking>", "end": "", "schema": INNER_SCHEMA},
            512,
        )
    )
    results.append(
        run_arm(
            model, tokenizer, "C-trigger-</think>",
            {"kind": "structural_tag", "begin": "</think>", "end": "", "schema": INNER_SCHEMA},
            512,
        )
    )
    print("\n=== SUMMARY ===")
    for r in results:
        print(f"  {r['label']:24s} json_after_close_ok={r['json_after_close_ok']} len={r['len']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
