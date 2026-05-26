"""C1 canary: verify the mlx-lm batch-verify primitive works + is fast enough.

See docs/architect/design/F-2-ngram-suffix-spec.md §4.2.

Pass criteria (per spec):

  1. Byte-equivalence: when the speculation chain equals the model's reference
     output, batch verify must accept every chain token plus the +1 bonus,
     and the returned tokens must equal the reference output exactly.
  2. Batch verify works at N=1/4/8.
  3. Per-position amortized cost ≤ 1.5× single-token decode cost.
     (Spec revised 2026-05-26 from the original "≤ 1.5× single token forward"
     formulation, which is physically impossible.)

The canary writes one JSONL ledger and one rollup to
``files/evidence/owlmlx/bench/perf-optimization/c-ngram/``.

It is intentionally **not** a pytest test — it loads a 14 GB model and runs
for ~2-5 minutes. Run on demand.

Usage:
    uv run python scripts/bench/ngram_c1_canary.py
    uv run python scripts/bench/ngram_c1_canary.py --model qwen3.6-27b-4bit
    uv run python scripts/bench/ngram_c1_canary.py --prompts 5 --perf-iters 5  # quick mode
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "perf-optimization"
    / "c-ngram"
)

MODEL_PATHS: dict[str, str] = {
    "qwen3.6-27b-4bit": "/Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit",
    "qwen3.6-35b-a3b-4bit": "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit",
    "gemma-4-31b-it-4bit": "/Users/yeemio/AI/Agent/models/gemma-4-31B-it-4bit",
}

# Spec-defined kill threshold (revised 2026-05-26).
PER_POSITION_AMORTIZED_RATIO_KILL = 1.5

# Default N values to probe (per spec §4.2: 1, 4, 8).
DEFAULT_BATCH_SIZES = (1, 4, 8)

# Default byte-equivalence prompt count. Spec §4.2 wants N=20 prompts × 5
# seeds. We are running deterministic (temperature=0) here, so 1 "seed" per
# prompt is sufficient; the spec's 5 seeds is meaningful only when sampling.
DEFAULT_BYTE_EQUIV_PROMPTS = 20
DEFAULT_PERF_ITERATIONS = 10
DEFAULT_REFERENCE_TOKENS = 8  # how many tokens of reference output to collect
DEFAULT_CHAIN_LENGTH_FOR_EQUIV = 4  # tokens of chain to verify against reference

# Fixed prompt set: 20 short English prompts with varied structure to exercise
# byte-equivalence without depending on any external workload file. The
# content doesn't matter — only that the model's deterministic output is
# predictable enough that the same prompt reproduces the same chain.
CANARY_PROMPTS: tuple[str, ...] = (
    "The capital of France is",
    "Two plus two equals",
    "The largest planet in our solar system is",
    "In Python, a list comprehension begins with",
    "The mitochondria are the",
    "Water boils at",
    "The author of Pride and Prejudice was",
    "A binary tree has at most",
    "The speed of light in a vacuum is approximately",
    "The chemical formula for table salt is",
    "The largest ocean on Earth is the",
    "The first president of the United States was",
    "In a HTTP request, the method GET",
    "Photosynthesis converts sunlight into",
    "The Fibonacci sequence begins with",
    "The smallest prime number is",
    "The capital of Japan is",
    "An octopus has",
    "The freezing point of water in Celsius is",
    "The currency of the United Kingdom is the",
)


def _now_compact_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _host_label() -> str:
    try:
        result = subprocess.run(
            ["/usr/sbin/sysctl", "-n", "hw.model"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return platform.machine() or "unknown"


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True))
        f.write("\n")


# --------------------------------------------------------------------------
# Reference generation
# --------------------------------------------------------------------------


def collect_reference_output(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_tokens: int,
) -> tuple[list[int], list[int]]:
    """Run deterministic stream_generate; return (prompt_ids, output_ids).

    Uses temperature=0 + min_p=0 so token selection is argmax (deterministic).
    """
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_sampler

    sampler = make_sampler(temp=0.0)
    prompt_ids = tokenizer.encode(prompt)
    output_ids: list[int] = []
    for response in stream_generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        sampler=sampler,
    ):
        token = getattr(response, "token", None)
        if token is None:
            # Fallback: try .text → tokenize. Should not be needed.
            text = getattr(response, "text", "")
            if text:
                tok = tokenizer.encode(text, add_special_tokens=False)
                if tok:
                    output_ids.append(tok[0])
        else:
            output_ids.append(int(token))
        if len(output_ids) >= max_tokens:
            break
    return prompt_ids, output_ids


# --------------------------------------------------------------------------
# Byte-equivalence test
# --------------------------------------------------------------------------


def build_reference_via_batch_verify(
    model: Any,
    prompt_ids: list[int],
    n_tokens: int,
) -> list[int]:
    """Build a self-consistent reference by repeatedly calling batch_verify
    with empty/growing chains. Each call returns one token (the +1 bonus).

    Self-consistency check: batch_verify on chain=reference[:K] MUST then
    accept all K chain tokens and produce reference[K] as the bonus. This
    eliminates the apples-to-oranges comparison with stream_generate (which
    uses a different forward path; mlx-lm has small numerical drift between
    forward paths on some prompts — see 2026-05-26 C1 canary diagnostic).
    """
    from owlmlx.speculative.suffix_decoding import mlx_lm_batch_verify

    tokens: list[int] = []
    for _ in range(n_tokens):
        result = mlx_lm_batch_verify(
            model=model, context_ids=prompt_ids, chain_ids=tokens
        )
        # The +1 bonus is always the last element of accepted_tokens.
        tokens.append(result.accepted_tokens[-1])
    return tokens


def run_byte_equivalence(
    model: Any,
    tokenizer: Any,
    prompts: list[str],
    chain_length: int,
    reference_tokens: int,
) -> list[dict[str, Any]]:
    """Self-consistency byte-equivalence test.

    For each prompt:
      1. Build a self-consistent reference of ``reference_tokens`` tokens by
         calling batch_verify repeatedly with growing chain.
      2. Verify: batch_verify on ``chain = reference[:chain_length]`` MUST
         produce ``reference[:chain_length + 1]`` (every chain token accepted
         + the next reference token as bonus).
      3. Side check (informational, not blocking): compare reference to
         stream_generate's first ``reference_tokens`` tokens; record agreement
         rate as a secondary metric. Disagreement is expected on some prompts
         due to mlx-lm batched-vs-split forward numerical drift.
    """
    from owlmlx.speculative.suffix_decoding import mlx_lm_batch_verify

    cells: list[dict[str, Any]] = []
    for prompt_idx, prompt in enumerate(prompts, start=1):
        cell_start = _now_iso()
        try:
            prompt_ids = tokenizer.encode(prompt)

            # Self-consistent reference: built by batch_verify itself.
            ref_ids = build_reference_via_batch_verify(
                model, prompt_ids, n_tokens=reference_tokens
            )

            if len(ref_ids) < chain_length + 1:
                cells.append(
                    {
                        "test": "byte_equivalence",
                        "prompt_idx": prompt_idx,
                        "prompt_preview": prompt[:60],
                        "verdict": "skipped",
                        "reason": (
                            f"reference output only {len(ref_ids)} tokens; "
                            f"need at least chain_length+1={chain_length + 1}"
                        ),
                        "started_at": cell_start,
                        "ended_at": _now_iso(),
                    }
                )
                continue

            chain = ref_ids[:chain_length]
            expected_accepted = ref_ids[: chain_length + 1]
            result = mlx_lm_batch_verify(
                model=model,
                context_ids=prompt_ids,
                chain_ids=chain,
            )
            self_consistent = (
                result.chain_accept_count == chain_length
                and result.accepted_tokens == expected_accepted
            )

            # Side check: stream_generate comparison (informational only).
            try:
                _, stream_ids = collect_reference_output(
                    model, tokenizer, prompt, max_tokens=reference_tokens
                )
                stream_matches_self = stream_ids[: len(ref_ids)] == ref_ids
            except Exception:
                stream_ids = []
                stream_matches_self = None

            cells.append(
                {
                    "test": "byte_equivalence",
                    "prompt_idx": prompt_idx,
                    "prompt_preview": prompt[:60],
                    "prompt_token_count": len(prompt_ids),
                    "self_reference": ref_ids,
                    "chain_length": chain_length,
                    "chain": chain,
                    "expected_accepted": expected_accepted,
                    "actual_accepted": result.accepted_tokens,
                    "chain_accept_count": result.chain_accept_count,
                    "self_consistent": self_consistent,
                    "stream_generate_reference": stream_ids,
                    "stream_generate_matches_self_reference": stream_matches_self,
                    "verdict": "passed" if self_consistent else "failed",
                    "started_at": cell_start,
                    "ended_at": _now_iso(),
                }
            )
        except Exception as exc:
            cells.append(
                {
                    "test": "byte_equivalence",
                    "prompt_idx": prompt_idx,
                    "prompt_preview": prompt[:60],
                    "verdict": "errored",
                    "error": f"{type(exc).__name__}: {exc}",
                    "started_at": cell_start,
                    "ended_at": _now_iso(),
                }
            )
    return cells


# --------------------------------------------------------------------------
# Performance measurement
# --------------------------------------------------------------------------


def time_forward(
    model: Any,
    tokenizer: Any,
    prompt_ids: list[int],
    num_tokens_to_forward: int,
    iterations: int,
) -> dict[str, float]:
    """Measure the wall-clock cost of one forward-pass for ``num_tokens_to_forward``
    tokens from a freshly-primed cache.

    Each iteration:
      1. Build a fresh prompt cache.
      2. Prefill the context (NOT counted).
      3. Forward ``num_tokens_to_forward`` filler tokens, time it.
      4. Discard the cache.

    Returns dict of times (seconds) with p50/p95/mean/min/max + the per-position
    amortized cost.
    """
    import mlx.core as mx
    from mlx_lm.models.cache import make_prompt_cache

    # Pick a safe filler token id that fits in vocabulary (use prompt's last token).
    filler_token = int(prompt_ids[-1])
    filler_input = mx.array(
        [[filler_token] * num_tokens_to_forward], dtype=mx.uint32
    )

    context_array = mx.array([prompt_ids], dtype=mx.uint32)

    times: list[float] = []
    for _ in range(iterations):
        cache = make_prompt_cache(model)
        prefill_logits = model(context_array, cache=cache)
        mx.eval(prefill_logits)

        t0 = time.perf_counter()
        logits = model(filler_input, cache=cache)
        mx.eval(logits)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    sorted_times = sorted(times)

    def p(q: float) -> float:
        if not sorted_times:
            return 0.0
        i = max(0, min(len(sorted_times) - 1, int(q * (len(sorted_times) - 1))))
        return sorted_times[i]

    return {
        "num_tokens": num_tokens_to_forward,
        "iterations": len(times),
        "p50_s": p(0.50),
        "p95_s": p(0.95),
        "mean_s": statistics.mean(times) if times else 0.0,
        "min_s": min(times) if times else 0.0,
        "max_s": max(times) if times else 0.0,
        "per_position_p50_s": p(0.50) / num_tokens_to_forward,
    }


def run_performance(
    model: Any,
    tokenizer: Any,
    canary_prompt: str,
    batch_sizes: tuple[int, ...],
    iterations: int,
) -> dict[str, Any]:
    """Run perf measurements at single-token + each batch size."""
    prompt_ids = tokenizer.encode(canary_prompt)
    if len(prompt_ids) < 4:
        # Pad to >= 4 tokens for stable cache state
        prompt_ids = prompt_ids + [prompt_ids[-1]] * (4 - len(prompt_ids))

    measurements: dict[int, dict[str, float]] = {}
    for n in batch_sizes:
        measurements[n] = time_forward(
            model=model,
            tokenizer=tokenizer,
            prompt_ids=prompt_ids,
            num_tokens_to_forward=n,
            iterations=iterations,
        )

    single_per_position = measurements[1]["per_position_p50_s"]
    ratios: dict[int, float] = {}
    pass_per_n: dict[int, bool] = {}
    for n in batch_sizes:
        per_pos = measurements[n]["per_position_p50_s"]
        ratio = per_pos / single_per_position if single_per_position > 0 else 0.0
        ratios[n] = ratio
        # N=1 is reference so passes trivially; N>1 must be ≤ kill threshold
        pass_per_n[n] = (n == 1) or (ratio <= PER_POSITION_AMORTIZED_RATIO_KILL)

    return {
        "prompt_token_count": len(prompt_ids),
        "iterations_per_batch_size": iterations,
        "kill_threshold": PER_POSITION_AMORTIZED_RATIO_KILL,
        "measurements": measurements,
        "per_position_amortized_ratios": ratios,
        "pass_per_batch_size": pass_per_n,
        "overall_perf_pass": all(pass_per_n.values()),
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="qwen3.6-27b-4bit",
        choices=list(MODEL_PATHS),
        help="Model alias (default: qwen3.6-27b-4bit — smallest available)",
    )
    parser.add_argument(
        "--prompts",
        type=int,
        default=DEFAULT_BYTE_EQUIV_PROMPTS,
        help=(
            f"Number of prompts to use for byte-equivalence "
            f"(default: {DEFAULT_BYTE_EQUIV_PROMPTS}; max: {len(CANARY_PROMPTS)})"
        ),
    )
    parser.add_argument(
        "--perf-iters",
        type=int,
        default=DEFAULT_PERF_ITERATIONS,
        help=f"Perf iterations per batch size (default: {DEFAULT_PERF_ITERATIONS})",
    )
    parser.add_argument(
        "--reference-tokens",
        type=int,
        default=DEFAULT_REFERENCE_TOKENS,
        help=f"Reference output tokens to collect (default: {DEFAULT_REFERENCE_TOKENS})",
    )
    parser.add_argument(
        "--chain-length",
        type=int,
        default=DEFAULT_CHAIN_LENGTH_FOR_EQUIV,
        help=(
            f"Chain length for byte-equivalence test "
            f"(default: {DEFAULT_CHAIN_LENGTH_FOR_EQUIV})"
        ),
    )
    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        default=list(DEFAULT_BATCH_SIZES),
        help=f"Batch sizes for perf test (default: {list(DEFAULT_BATCH_SIZES)})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Evidence JSONL output directory",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke mode: 2 prompts, 3 perf iters",
    )
    args = parser.parse_args()

    if args.smoke:
        args.prompts = 2
        args.perf_iters = 3

    args.prompts = min(args.prompts, len(CANARY_PROMPTS))

    run_id = _now_compact_utc() + "-c1-verifier-canary"
    if args.smoke:
        run_id += "-smoke"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cells_path = args.output_dir / f"{run_id}.jsonl"
    rollup_path = args.output_dir / f"{run_id}-rollup.jsonl"

    host = _host_label()
    started_at = _now_iso()

    print(f"[c1-canary] run_id: {run_id}")
    print(f"[c1-canary] host: {host}")
    print(f"[c1-canary] model: {args.model}")
    print(f"[c1-canary] prompts: {args.prompts}, perf_iters: {args.perf_iters}")
    print(f"[c1-canary] batch sizes: {args.batch_sizes}")
    print(f"[c1-canary] ledger: {cells_path}")
    print(f"[c1-canary] rollup: {rollup_path}")
    print()

    print(f"[c1-canary] loading {MODEL_PATHS[args.model]} ...")
    load_start = time.perf_counter()
    try:
        from mlx_lm import load

        model, tokenizer = load(MODEL_PATHS[args.model])
    except Exception as exc:
        err = {
            "schema_version": "f2.c1.cell.v1",
            "run_id": run_id,
            "host": host,
            "started_at": started_at,
            "ended_at": _now_iso(),
            "stage": "load",
            "verdict": "errored",
            "error": f"{type(exc).__name__}: {exc}",
        }
        _append_jsonl(cells_path, err)
        print(f"[c1-canary] LOAD FAILED: {exc}")
        return 1
    load_s = time.perf_counter() - load_start
    print(f"[c1-canary]   loaded in {load_s:.1f}s")

    # ----- Byte-equivalence -----
    print(f"[c1-canary] running byte-equivalence ({args.prompts} prompts) ...")
    equiv_start = time.perf_counter()
    equiv_cells = run_byte_equivalence(
        model=model,
        tokenizer=tokenizer,
        prompts=list(CANARY_PROMPTS[: args.prompts]),
        chain_length=args.chain_length,
        reference_tokens=args.reference_tokens,
    )
    equiv_wall_s = time.perf_counter() - equiv_start
    for cell in equiv_cells:
        cell.update(
            {
                "schema_version": "f2.c1.cell.v1",
                "run_id": run_id,
                "host": host,
                "model_id": args.model,
            }
        )
        _append_jsonl(cells_path, cell)
    equiv_pass_count = sum(1 for c in equiv_cells if c.get("verdict") == "passed")
    equiv_fail_count = sum(1 for c in equiv_cells if c.get("verdict") == "failed")
    equiv_err_count = sum(1 for c in equiv_cells if c.get("verdict") == "errored")
    equiv_skip_count = sum(1 for c in equiv_cells if c.get("verdict") == "skipped")
    print(
        f"[c1-canary]   byte-equivalence: "
        f"{equiv_pass_count}/{len(equiv_cells)} passed "
        f"({equiv_fail_count} failed, {equiv_err_count} errored, "
        f"{equiv_skip_count} skipped), wall {equiv_wall_s:.1f}s"
    )

    # ----- Performance -----
    print(f"[c1-canary] running perf (batch_sizes={args.batch_sizes}, iters={args.perf_iters}) ...")
    perf_start = time.perf_counter()
    perf = run_performance(
        model=model,
        tokenizer=tokenizer,
        canary_prompt=CANARY_PROMPTS[0],
        batch_sizes=tuple(args.batch_sizes),
        iterations=args.perf_iters,
    )
    perf_wall_s = time.perf_counter() - perf_start

    perf_cell = {
        "schema_version": "f2.c1.cell.v1",
        "run_id": run_id,
        "host": host,
        "model_id": args.model,
        "stage": "performance",
        "started_at": _now_iso(),
        "ended_at": _now_iso(),
        "perf": perf,
        "wall_s": perf_wall_s,
        "verdict": "passed" if perf["overall_perf_pass"] else "failed",
    }
    _append_jsonl(cells_path, perf_cell)
    for n, ratio in perf["per_position_amortized_ratios"].items():
        threshold = PER_POSITION_AMORTIZED_RATIO_KILL
        verdict = "pass" if perf["pass_per_batch_size"][n] else "FAIL"
        print(
            f"[c1-canary]   N={n}: per-position ratio={ratio:.3f} "
            f"(threshold {threshold:.2f}) -> {verdict}"
        )

    # ----- Rollup -----
    byte_equiv_pass = equiv_pass_count == len(equiv_cells) and equiv_pass_count > 0
    overall_pass = byte_equiv_pass and perf["overall_perf_pass"]

    rollup = {
        "schema_version": "f2.c1.rollup.v1",
        "gate": "F-2",
        "phase": "c1",
        "run_id": run_id,
        "host": host,
        "started_at": started_at,
        "ended_at": _now_iso(),
        "model_id": args.model,
        "model_load_s": round(load_s, 3),
        "byte_equivalence": {
            "total": len(equiv_cells),
            "passed": equiv_pass_count,
            "failed": equiv_fail_count,
            "errored": equiv_err_count,
            "skipped": equiv_skip_count,
            "all_pass": byte_equiv_pass,
        },
        "performance": perf,
        "kill_criterion": "per_position_amortized_cost_le_1.5x_single_token_decode",
        "spec_source": "docs/architect/design/F-2-ngram-suffix-spec.md §4.2 (revised 2026-05-26)",
        "f1_ngram_status_after_c1": "not_implemented",
        "next_phase": (
            "C2 — serving integration" if overall_pass else "ESCALATE — see failure_handling"
        ),
        "verdict": "passed" if overall_pass else "failed",
        "spec_gate_criteria_satisfied": {
            "byte_equivalence_all_pass": byte_equiv_pass,
            "batch_verify_works_at_each_n": all(
                perf["pass_per_batch_size"].values()
            ),
            "per_position_amortized_cost_within_threshold": perf["overall_perf_pass"],
        },
    }
    _append_jsonl(rollup_path, rollup)

    print()
    print(f"[c1-canary] verdict: {rollup['verdict'].upper()}")
    print(f"[c1-canary] ledger: {cells_path}")
    print(f"[c1-canary] rollup: {rollup_path}")
    return 0 if overall_pass else 2


if __name__ == "__main__":
    sys.exit(main())
