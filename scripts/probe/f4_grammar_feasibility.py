"""F-4 Grammar Constrained Decoding Feasibility Probe.

Determines whether mlx-lm's ``logits_processors`` hook (exposed in
``mlx_lm.generate.generate_step``) can be composed with xgrammar to constrain
structured-output generation in-process, on the same model family that F-4.1
measured.

Scope per ``docs/phase-prompts/owlmlx-f4-grammar-feasibility-probe-20260528.md``:

  * 1 model (Qwen 35B-A3B 4bit DWQ — F-4.1 was the only model with any pass)
  * 1 family (``json_schema_flat`` — highest failure rate 12/12 in F-4.1)
  * 10 control samples + 10 treatment samples
  * No ``owlmlx/`` change, no ``tests/`` change, no ``pyproject.toml`` change
  * Direct in-process ``mlx_lm.stream_generate`` (NOT through MlxLmSubprocessBackend;
    subprocess plumbing is F-4.2 design-grade scope)

Mount path: xgrammar's ``apply_token_bitmask_inplace`` requires torch, so this
probe decodes the bitmask manually via numpy ``unpackbits`` and applies it as a
where-mask on mlx logits. This adds Python-side overhead per token; the
treatment tokens/sec figure measures that overhead.

Outputs:

  * ``files/evidence/owlmlx/bench/structured-output-invariance/
    <ts>-f4-grammar-feasibility-probe.jsonl`` — per-sample rows
  * ``files/evidence/owlmlx/bench/structured-output-invariance/
    <ts>-f4-grammar-feasibility-probe-summary.json`` — verdict and rollup

NOT a production code path. NOT a capability promotion. The probe verdict
informs F-4.2 design-grade direction; it does NOT promote any label.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import mlx.core as mx
import numpy as np

import xgrammar as xgr
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

# Family: json_schema_flat (per F-4.1 case f4-json-flat-001)
PROBE_PROMPT = (
    "Return JSON only. No markdown. No prose. "
    'Schema: {"task_id": string, "category": one of ["bugfix","feature","docs","test"], '
    '"priority": integer, "requires_review": boolean}. '
    'Use task_id "F4-JSON-001" and category "bugfix".'
)

PROBE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "category": {"type": "string", "enum": ["bugfix", "feature", "docs", "test"]},
        "priority": {"type": "integer"},
        "requires_review": {"type": "boolean"},
    },
    "required": ["task_id", "category", "priority", "requires_review"],
    "additionalProperties": False,
}

EVIDENCE_DIR = Path("files/evidence/owlmlx/bench/structured-output-invariance")


def make_xgrammar_logits_processor(
    matcher: xgr.GrammarMatcher,
    vocab_size: int,
    rejection_flag: dict[str, bool],
) -> Callable[[mx.array, mx.array], mx.array]:
    """Build an mlx logits_processor backed by an xgrammar matcher.

    mlx-lm's ``generate_step`` runs the bulk of the prompt through the model
    without touching ``tokens`` or ``logits_processors`` (the prefill loop at
    generate.py:430 only refreshes the KV cache). The final prompt token is
    then handed to ``_step`` once, and from that call onward ``tokens``
    accumulates that prompt-last token plus every sampled token. So on the
    very first processor call ``tokens.shape[0] == 1`` and the single token
    is a prompt token (NOT a generation). We must NOT feed that into the
    matcher.

    Strategy: on the first call, treat all current tokens as prompt-context
    (matcher stays at its initial state). On every later call, accept the
    newly-arrived tokens (all of which are generated).

    On each step:
      * Accept any newly-generated tokens into the matcher.
      * If the matcher has terminated, return logits unchanged.
      * Otherwise build a vocab bitmask via xgrammar, decode via numpy
        unpackbits (little-endian within each int32 word), and set disallowed
        logits to ``-inf`` via ``mx.where``.

    Notes:
      * xgrammar's ``apply_token_bitmask_inplace`` is torch-only; we avoid that
        path and decode the bitmask via numpy bit-unpacking, then apply with
        ``mx.where`` to keep the hot loop on mlx arrays.
      * ``xgr.allocate_token_bitmask`` returns a CPU torch.int32 tensor; we
        use it as the canonical buffer (its ``.numpy()`` shares memory).
    """
    bitmask_t = xgr.allocate_token_bitmask(1, vocab_size)
    # -1 sentinel: first call sets this to cur_len so we never accept the
    # prompt-tail token(s) into the matcher.
    state = {"last_seen_len": -1}

    def processor(tokens: mx.array, logits: mx.array) -> mx.array:
        cur_len = int(tokens.shape[0])
        if state["last_seen_len"] < 0:
            # First call: tokens holds prompt-tail token(s) only. Don't feed
            # them into the matcher; just record where generation starts.
            state["last_seen_len"] = cur_len
        elif cur_len > state["last_seen_len"]:
            new_token_ids = tokens[state["last_seen_len"] : cur_len].tolist()
            for tok in new_token_ids:
                if matcher.is_terminated():
                    break
                accepted = matcher.accept_token(int(tok))
                if not accepted:
                    rejection_flag["rejected"] = True
                    # Matcher diverged — leave logits unchanged and stop
                    # constraining (data point goes into evidence).
                    state["last_seen_len"] = cur_len
                    return logits
            state["last_seen_len"] = cur_len

        if matcher.is_terminated():
            return logits

        # Fill next-token bitmask. bitmask_t is a CPU torch.int32 tensor; its
        # .numpy() view shares memory so we can decode without a copy.
        matcher.fill_next_token_bitmask(bitmask_t)
        bitmask_np = bitmask_t.numpy()
        flat_bytes = bitmask_np.view(np.uint8).reshape(-1)
        allowed = np.unpackbits(flat_bytes, bitorder="little")[:vocab_size]
        # logits shape: [1, vocab_size]. Build a [1, vocab_size] mask.
        allowed_mx = mx.array(allowed.astype(np.bool_)).reshape((1, vocab_size))
        neg_inf = mx.full(logits.shape, -mx.inf, dtype=logits.dtype)
        return mx.where(allowed_mx, logits, neg_inf)

    return processor


def hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def try_json_parse(text: str) -> tuple[bool, str | None]:
    """Return (parsed_ok, error_kind_or_None).

    Mirrors F-4 validator's basic JSON-parse check; does not enforce the schema
    here — probe verdict is on json_parse_failed rate, which is what F-4.1 also
    measured as the dominant break.
    """
    stripped = text.strip()
    if not stripped:
        return False, "empty_output"
    try:
        json.loads(stripped)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"json_decode_error:{e.msg[:80]}"


def run_one(
    model,
    tokenizer,
    prompt_token_ids: list[int],
    *,
    arm: str,
    sample_idx: int,
    temperature: float,
    max_tokens: int,
    compiled_grammar: xgr.CompiledGrammar | None,
    vocab_size: int,
) -> dict[str, Any]:
    sampler = make_sampler(temp=temperature)
    logits_processors: list[Callable] = []
    matcher = None
    rejection_flag: dict[str, bool] = {"rejected": False}
    if arm == "treatment":
        assert compiled_grammar is not None
        matcher = xgr.GrammarMatcher(compiled_grammar)
        processor = make_xgrammar_logits_processor(
            matcher,
            vocab_size,
            rejection_flag=rejection_flag,
        )
        logits_processors.append(processor)

    text_parts: list[str] = []
    t0 = time.monotonic()
    finish_reason = "stop"
    generation_tokens = 0
    prompt_tokens = 0
    last_resp = None
    try:
        for resp in stream_generate(
            model,
            tokenizer,
            prompt=prompt_token_ids,
            max_tokens=max_tokens,
            sampler=sampler,
            logits_processors=logits_processors,
        ):
            text_parts.append(resp.text)
            last_resp = resp
        if last_resp is not None:
            finish_reason = getattr(last_resp, "finish_reason", "stop") or "stop"
            generation_tokens = getattr(last_resp, "generation_tokens", 0)
            prompt_tokens = getattr(last_resp, "prompt_tokens", len(prompt_token_ids))
        gen_error = None
    except Exception as e:  # noqa: BLE001
        gen_error = f"{type(e).__name__}:{str(e)[:200]}"
        finish_reason = "error"

    elapsed_s = time.monotonic() - t0
    output_text = "".join(text_parts)
    parse_ok, parse_err = try_json_parse(output_text)

    failure_codes: list[str] = []
    if gen_error is not None:
        failure_codes.append("generation_error")
    if not parse_ok:
        failure_codes.append("json_parse_failed")
    if matcher is not None and not matcher.is_terminated() and not gen_error:
        # Matcher didn't finish — possibly truncated at max_tokens
        if finish_reason == "length":
            failure_codes.append("grammar_unterminated_at_max_tokens")

    return {
        "schema_version": "f4.grammar_feasibility_probe.cell.v1",
        "arm": arm,
        "sample_idx": sample_idx,
        "temperature": temperature,
        "model_id_probe": "Qwen3.6-35B-A3B-4bit (local MLX, owlmlx catalog name qwen3.6-35b-a3b-4bit)",
        "family": "json_schema_flat",
        "prompt_hash": hash_text(PROBE_PROMPT),
        "output_text": output_text,
        "output_hash": hash_text(output_text),
        "metrics": {
            "elapsed_s": round(elapsed_s, 4),
            "generation_tokens": int(generation_tokens),
            "prompt_tokens": int(prompt_tokens),
            "tokens_per_sec": (
                round(generation_tokens / elapsed_s, 3) if elapsed_s > 0 else 0.0
            ),
            "finish_reason": finish_reason,
        },
        "parse_ok": parse_ok,
        "parse_error_kind": parse_err,
        "generation_error": gen_error,
        "failure_codes": failure_codes,
        "matcher_rejected_token": (
            None if matcher is None else bool(rejection_flag["rejected"])
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="F-4 Grammar feasibility probe")
    parser.add_argument(
        "--model",
        default="/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit",
        help=(
            "Local filesystem path to the MLX-format model, OR an HF model id "
            "if the shards are already fully cached. Probe default is the local "
            "path used by F-4.1 evidence to avoid HuggingFace re-download."
        ),
    )
    parser.add_argument(
        "--samples-per-arm",
        type=int,
        default=10,
        help="number of samples for control AND for treatment",
    )
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=EVIDENCE_DIR,
        help="output directory for evidence files",
    )
    args = parser.parse_args()

    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows_path = args.evidence_dir / f"{ts}-f4-grammar-feasibility-probe.jsonl"
    summary_path = (
        args.evidence_dir / f"{ts}-f4-grammar-feasibility-probe-summary.json"
    )

    print(f"[probe] mlx-lm import OK; loading model {args.model} …", flush=True)
    t_load_start = time.monotonic()
    model, tokenizer = load(args.model)
    load_s = time.monotonic() - t_load_start
    print(f"[probe] model loaded in {load_s:.1f}s", flush=True)

    # mlx-lm TokenizerWrapper wraps an HF tokenizer at .tokenizer or ._tokenizer
    hf_tok = getattr(tokenizer, "tokenizer", None) or getattr(
        tokenizer, "_tokenizer", None
    )
    if hf_tok is None:
        # last-resort: mlx-lm TokenizerWrapper IS the tokenizer-like; try
        # passing it directly
        hf_tok = tokenizer
    print(f"[probe] tokenizer type: {type(hf_tok).__name__}", flush=True)

    # Resolve the model's actual logits vocab_size from config.json. mlx-lm
    # quantized multimodal Qwen models pad vocab beyond the tokenizer's nominal
    # vocab; xgrammar must use the model dimension or the bitmask will not
    # broadcast against the logits tensor.
    model_vocab_size = _resolve_model_vocab_size(args.model)
    print(f"[probe] model logits vocab_size={model_vocab_size}", flush=True)

    print("[probe] building xgrammar TokenizerInfo …", flush=True)
    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        hf_tok, vocab_size=model_vocab_size
    )
    vocab_size = tokenizer_info.vocab_size
    print(
        f"[probe] xgrammar vocab_size={vocab_size} "
        f"(tokenizer-native may be smaller; model dim wins)",
        flush=True,
    )

    print("[probe] compiling JSON schema grammar …", flush=True)
    compiler = xgr.GrammarCompiler(tokenizer_info)
    t_compile = time.monotonic()
    compiled = compiler.compile_json_schema(json.dumps(PROBE_JSON_SCHEMA))
    compile_s = time.monotonic() - t_compile
    print(f"[probe] grammar compiled in {compile_s:.2f}s", flush=True)

    # Encode prompt once (so both arms see identical prompt token sequence).
    prompt_token_ids = tokenizer.encode(PROBE_PROMPT)
    if isinstance(prompt_token_ids, mx.array):
        prompt_token_ids = prompt_token_ids.tolist()
    prompt_len = len(prompt_token_ids)
    print(f"[probe] prompt_tokens={prompt_len}", flush=True)

    rows: list[dict[str, Any]] = []

    with rows_path.open("w") as f_rows:
        for arm in ("control", "treatment"):
            for i in range(args.samples_per_arm):
                row = run_one(
                    model,
                    tokenizer,
                    prompt_token_ids,
                    arm=arm,
                    sample_idx=i,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    compiled_grammar=compiled if arm == "treatment" else None,
                    vocab_size=vocab_size,
                )
                f_rows.write(json.dumps(row, ensure_ascii=False) + "\n")
                f_rows.flush()
                rows.append(row)
                short_status = (
                    "GEN_ERR"
                    if row["generation_error"]
                    else ("OK" if row["parse_ok"] else "FAIL")
                )
                print(
                    f"[probe] {arm:9s} {i+1:2d}/{args.samples_per_arm}  "
                    f"{short_status:7s} "
                    f"tok={row['metrics']['generation_tokens']:3d} "
                    f"tok/s={row['metrics']['tokens_per_sec']:5.2f} "
                    f"finish={row['metrics']['finish_reason']}",
                    flush=True,
                )

    # Rollup
    def arm_summary(arm: str) -> dict[str, Any]:
        sub = [r for r in rows if r["arm"] == arm]
        n = len(sub)
        parse_ok = sum(1 for r in sub if r["parse_ok"])
        gen_err = sum(1 for r in sub if r["generation_error"])
        tok_per_s = [
            r["metrics"]["tokens_per_sec"] for r in sub if r["metrics"]["tokens_per_sec"] > 0
        ]
        return {
            "n": n,
            "json_parse_ok": parse_ok,
            "json_parse_failed": n - parse_ok,
            "json_parse_failed_rate": (n - parse_ok) / n if n else 0.0,
            "generation_error_count": gen_err,
            "tokens_per_sec_median": (
                float(np.median(tok_per_s)) if tok_per_s else 0.0
            ),
            "tokens_per_sec_mean": (
                float(np.mean(tok_per_s)) if tok_per_s else 0.0
            ),
        }

    control = arm_summary("control")
    treatment = arm_summary("treatment")

    # Verdict logic per handoff §1.3:
    #   probe-positive: Step 3 ran AND treatment hard_break_rate <= 20% AND
    #     tokens/sec degradation <= 5x
    #   probe-negative-with-fallback: mount succeeded but thresholds not met
    #   probe-negative-stop: not reached here (would be reported at Step 2)
    t_break = treatment["json_parse_failed_rate"]
    tps_c = control["tokens_per_sec_median"]
    tps_t = treatment["tokens_per_sec_median"]
    degradation = (tps_c / tps_t) if tps_t > 0 else float("inf")

    if t_break <= 0.20 and degradation <= 5.0:
        verdict = "probe-positive"
    else:
        verdict = "probe-negative-with-fallback"

    rationale_parts = [
        (
            f"mount path: xgrammar 0.2.1 → mlx logits_processors via numpy "
            f"unpackbits bridge (apply_token_bitmask_inplace is torch-only)."
        ),
        (
            f"control json_parse_failed_rate={control['json_parse_failed_rate']:.2f}; "
            f"treatment json_parse_failed_rate={t_break:.2f}; "
            f"tokens/sec median control={tps_c:.2f}, treatment={tps_t:.2f}; "
            f"degradation={degradation:.2f}x."
        ),
    ]
    if verdict == "probe-positive":
        rationale_parts.append(
            "Treatment meets handoff thresholds (break ≤ 0.20, degradation ≤ 5x); "
            "in-process grammar-constrained decoding is viable."
        )
    else:
        if t_break > 0.20:
            rationale_parts.append(
                f"Treatment json_parse_failed_rate {t_break:.2f} exceeds the 0.20 "
                "handoff threshold."
            )
        if degradation > 5.0:
            rationale_parts.append(
                f"Tokens/sec degradation {degradation:.2f}x exceeds the 5x "
                "handoff threshold."
            )
    rationale_parts.append(
        "F-4.2 production path also has to thread logits_processors through "
        "MlxLmSubprocessBackend (probe was in-process direct); that is F-4.2 "
        "design-grade scope, not probe scope."
    )
    rationale_parts.append(
        "Probe was executed in the same session as the F-4.1 closeout per user "
        "direction, NOT in a fresh session as the handoff originally specified. "
        "Recorded here for audit per feedback-fresh-session-grade-transitions."
    )

    summary = {
        "schema_version": "f4.grammar_feasibility_probe.summary.v1",
        "phase": "f4-grammar-feasibility-probe",
        "verdict": verdict,
        "ts_utc": ts,
        "mlx_lm_version": _resolve_mlx_lm_version(),
        "mlx_lm_fork": "mainline-pypi",
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
        },
        "api_surface": {
            "logits_processors_exposed": True,
            "sampler_hook_exposed": True,
            "notes": (
                "mlx_lm.generate.generate_step exposes both `sampler` and "
                "`logits_processors`; stream_generate kwargs pass through. "
                "Hook signature (tokens, logits) -> logits with logits shape "
                "[1, vocab_size]."
            ),
        },
        "library_attempted": "xgrammar",
        "library_version": "0.2.1",
        "library_mount_succeeded": True,
        "step3_ran": True,
        "model": args.model,
        "model_load_s": round(load_s, 2),
        "grammar_compile_s": round(compile_s, 2),
        "family": "json_schema_flat",
        "schema_used": PROBE_JSON_SCHEMA,
        "samples_per_arm": args.samples_per_arm,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "prompt_tokens": prompt_len,
        "control": control,
        "treatment": treatment,
        "tokens_per_sec_degradation_x": round(degradation, 3),
        "evidence": {
            "rows_path": str(rows_path),
            "summary_path": str(summary_path),
        },
        "verdict_rationale": " ".join(rationale_parts),
        "out_of_scope_caveats": [
            "Probe is in-process direct mlx_lm.stream_generate; production wiring "
            "through MlxLmSubprocessBackend is F-4.2 design-grade.",
            "xgrammar's `apply_token_bitmask_inplace` is torch-only; this probe "
            "uses numpy unpackbits which adds Python-side per-token cost. A "
            "production path may want a native mlx mask op for hot loop.",
            "Probe model is the 4bit DWQ variant for tractable in-process load; "
            "F-4.1 measured the same model family but via subprocess backend.",
        ],
    }

    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[probe] wrote rows  → {rows_path}", flush=True)
    print(f"[probe] wrote summary → {summary_path}", flush=True)
    print(f"[probe] VERDICT: {verdict}", flush=True)
    return 0


def _resolve_model_vocab_size(model_dir_or_id: str) -> int:
    """Read the model's logits vocab_size from config.json.

    Multimodal Qwen3.6 nests it under ``text_config.vocab_size``; older flat
    configs put it at the root. Falls back to the first non-None value found
    in a recursive walk.
    """
    from pathlib import Path as _P

    cfg_path = _P(model_dir_or_id) / "config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"config.json not found at {cfg_path}; probe requires a local model directory"
        )
    cfg = json.loads(cfg_path.read_text())

    def _walk(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k == "vocab_size" and isinstance(v, int):
                    yield v
                yield from _walk(v)

    for v in _walk(cfg):
        return v
    raise RuntimeError(f"could not find vocab_size in {cfg_path}")


def _resolve_mlx_lm_version() -> str:
    try:
        from mlx_lm import _version  # type: ignore[attr-defined]

        v = getattr(_version, "__version__", None)
        if v:
            return v
    except Exception:  # noqa: BLE001
        pass
    try:
        import importlib.metadata as md

        return md.version("mlx-lm")
    except Exception:  # noqa: BLE001
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
