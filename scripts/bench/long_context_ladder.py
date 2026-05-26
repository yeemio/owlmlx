"""Long-context performance ladder for owlmlx main models.

Measures TTFT, decode TPS, peak RSS for the three main models at the input
token length ladder [1k, 4k, 16k, 32k, 64k, 96k, 128k]. Direct mlx_lm load
(not via runtime subprocess) for first-pass simplicity. Tests the upper bound
— owlmlx serving performance can only be this or lower; if the model+mlx_lm
can't do a given (model × length), neither can owlmlx.

Failure mode discipline: per-cell try/except so a single OOM/length-overflow
does not lose previously captured cells. Each successful cell row is appended
to the ledger immediately, so partial runs preserve evidence.

Usage:
    # smoke single cell to validate
    python scripts/bench/long_context_ladder.py --smoke

    # full matrix (default: 3 models × 7 lengths × 3 runs)
    python scripts/bench/long_context_ladder.py

    # custom slice
    python scripts/bench/long_context_ladder.py \\
        --models qwen3.6-27b-4bit \\
        --lengths 1024 4096 16384 \\
        --runs 1
"""

from __future__ import annotations

import argparse
import gc
import json
import platform
import resource
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
    / "long-context-ladder"
)

# Real local model paths confirmed via ls /Users/yeemio/AI/Agent/models/
MODEL_PATHS: dict[str, str] = {
    "qwen3.6-27b-4bit": "/Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit",
    "qwen3.6-27b": "/Users/yeemio/AI/Agent/models/Qwen3.6-27B",
    "gemma-4-31b-it-4bit": "/Users/yeemio/AI/Agent/models/gemma-4-31B-it-4bit",
    "gemma-4-31b-it": "/Users/yeemio/AI/Agent/models/gemma-4-31B-it",
    "qwen3.6-35b-a3b-4bit": "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit",
    "qwen3.6-35b-a3b": "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B",
}

DEFAULT_LENGTHS: tuple[int, ...] = (1024, 4096, 16384, 32768, 65536, 98304, 131072)
DEFAULT_MODELS: tuple[str, ...] = (
    "qwen3.6-27b-4bit",
    "gemma-4-31b-it-4bit",
    "qwen3.6-35b-a3b-4bit",
)
DEFAULT_RUNS = 3
DEFAULT_OUTPUT_TOKENS = 64  # enough for steady-state TPS, not so long it dominates time

SCHEMA_VERSION_CELL = "long_context_ladder.cell.v1"
SCHEMA_VERSION_ROLLUP = "long_context_ladder.rollup.v1"

# Reference text for prompt tiling. Plain technical English, no model-specific
# magic tokens, will tokenize differently per tokenizer (we record the actual
# token count per cell).
REFERENCE_TEXT = (
    "The runtime is responsible for loading a language model into memory, "
    "managing the key-value cache across consecutive requests, and serving "
    "generation responses to upstream callers. When a request arrives, the "
    "prefill phase processes the entire prompt in one pass, producing the "
    "initial activations and populating the key-value cache for the "
    "subsequent decoding loop. The decoding loop then produces one token at "
    "a time, attending against the cached keys and values, until either the "
    "maximum token budget is reached or the model emits an end-of-sequence "
    "marker. Throughout this process, the runtime must monitor memory "
    "pressure, enforce admission control, and surface honest status to "
    "observers so that downstream systems can make informed routing "
    "decisions without having to infer state from generation success or "
    "failure alone. A well-built runtime distinguishes its own contract "
    "promises from the model behaviour underneath, and it never lets a "
    "diagnostic surface masquerade as a production-grade guarantee. "
)


# ---------- helpers ---------------------------------------------------------


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


def _peak_rss_bytes() -> int:
    """Process peak RSS, in bytes. macOS reports bytes, Linux reports KB."""
    ru = resource.getrusage(resource.RUSAGE_SELF)
    if sys.platform == "darwin":
        return int(ru.ru_maxrss)
    return int(ru.ru_maxrss) * 1024


def _append_jsonl_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True))
        f.write("\n")


def _mlx_metal_clear_cache() -> None:
    """Best-effort: release MLX's GPU cache between cells.

    Newer MLX (>=0.32) moved these from mx.metal.* to mx.* directly.
    Try top-level first, fall back to mx.metal for older versions.
    """
    try:
        import mlx.core as mx  # type: ignore

        for attr in ("clear_cache", "reset_peak_memory"):
            fn = getattr(mx, attr, None)
            if not callable(fn) and hasattr(mx, "metal"):
                fn = getattr(mx.metal, attr, None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    pass
    except Exception:
        pass


# ---------- prompt construction --------------------------------------------


def _build_prompt_to_token_count(
    tokenizer: Any,
    target_tokens: int,
) -> tuple[str, int]:
    """Build a prompt with approximately target_tokens tokens.

    Strategy:
    1. Tokenize REFERENCE_TEXT.
    2. Tile the token list until length >= target_tokens.
    3. Slice to exactly target_tokens.
    4. Decode back to a string.
    5. Re-encode to capture the actual token count after decode round-trip
       (decode→encode can shift by a few tokens because of whitespace /
       BPE merging effects; we record the truth, not the request).
    """
    encode = getattr(tokenizer, "encode", None)
    if encode is None:
        raise RuntimeError("tokenizer has no .encode()")

    try:
        ref_tokens = tokenizer.encode(REFERENCE_TEXT, add_special_tokens=False)
    except TypeError:
        # Some tokenizers don't accept add_special_tokens kwarg
        ref_tokens = tokenizer.encode(REFERENCE_TEXT)

    if not ref_tokens:
        raise RuntimeError("tokenizer returned empty token list for reference text")

    tiled: list[int] = []
    while len(tiled) < target_tokens:
        tiled.extend(ref_tokens)
    tiled = tiled[:target_tokens]

    prompt = tokenizer.decode(tiled)

    try:
        actual_tokens = len(tokenizer.encode(prompt, add_special_tokens=False))
    except TypeError:
        actual_tokens = len(tokenizer.encode(prompt))

    return prompt, actual_tokens


# ---------- model load / unload --------------------------------------------


def _load_model(model_name: str) -> tuple[Any, Any]:
    from mlx_lm import load  # type: ignore

    path = MODEL_PATHS[model_name]
    return load(path)


def _free_model(model: Any, tokenizer: Any) -> None:
    del model
    del tokenizer
    gc.collect()
    _mlx_metal_clear_cache()


# ---------- cell execution -------------------------------------------------


def _run_cell(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_output_tokens: int,
) -> dict[str, Any]:
    """Stream-generate the prompt and capture TTFT / decode TPS.

    Returns a metrics dict (status, ttft_ms, decode_tps, output_tokens, ...).
    """
    from mlx_lm import stream_generate  # type: ignore

    t_start = time.perf_counter()
    t_first_token: float | None = None
    output_tokens = 0
    output_chunks: list[str] = []

    try:
        for response in stream_generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=max_output_tokens,
        ):
            if t_first_token is None:
                t_first_token = time.perf_counter()
            text = getattr(response, "text", None)
            if text is None:
                text = str(response)
            output_chunks.append(text)
            output_tokens += 1
    except Exception as exc:
        return {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tokens": output_tokens,
            "ttft_ms": None,
            "decode_tps": None,
            "decode_ms": None,
            "wall_ms": round((time.perf_counter() - t_start) * 1000, 3),
            "output_preview": "".join(output_chunks)[:120],
        }

    t_end = time.perf_counter()
    wall_ms = (t_end - t_start) * 1000
    ttft_ms = (t_first_token - t_start) * 1000 if t_first_token else None
    decode_ms = (t_end - t_first_token) * 1000 if t_first_token else None
    decode_tps: float | None = None
    if decode_ms and decode_ms > 0 and output_tokens > 1:
        decode_tps = (output_tokens - 1) / (decode_ms / 1000)

    return {
        "status": "ok",
        "output_tokens": output_tokens,
        "ttft_ms": round(ttft_ms, 3) if ttft_ms is not None else None,
        "decode_tps": round(decode_tps, 3) if decode_tps is not None else None,
        "decode_ms": round(decode_ms, 3) if decode_ms is not None else None,
        "wall_ms": round(wall_ms, 3),
        "output_preview": "".join(output_chunks)[:120],
    }


# ---------- rollup ---------------------------------------------------------


def _make_rollup(
    rows: list[dict[str, Any]],
    run_id: str,
    host_label: str,
    started_at: str,
) -> dict[str, Any]:
    cells_by_model: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("stage") in {"load", "prompt_build"}:
            continue
        model_id = row.get("model_id")
        if not model_id:
            continue
        cells_by_model.setdefault(model_id, []).append(row)

    per_model: dict[str, Any] = {}
    for model_id, model_rows in cells_by_model.items():
        ok_rows = [r for r in model_rows if r.get("status") == "ok"]
        # group ok rows by target_input_tokens, compute median-ish (just use mean for now)
        by_length: dict[int, list[dict[str, Any]]] = {}
        for r in ok_rows:
            by_length.setdefault(int(r["target_input_tokens"]), []).append(r)
        per_length: list[dict[str, Any]] = []
        for length in sorted(by_length):
            cells = by_length[length]
            ttfts = [c["ttft_ms"] for c in cells if c.get("ttft_ms") is not None]
            tpss = [c["decode_tps"] for c in cells if c.get("decode_tps") is not None]
            peaks = [c.get("peak_rss_gb") for c in cells if c.get("peak_rss_gb") is not None]
            per_length.append(
                {
                    "target_input_tokens": length,
                    "n": len(cells),
                    "ttft_ms_mean": round(sum(ttfts) / len(ttfts), 3) if ttfts else None,
                    "ttft_ms_min": round(min(ttfts), 3) if ttfts else None,
                    "ttft_ms_max": round(max(ttfts), 3) if ttfts else None,
                    "decode_tps_mean": round(sum(tpss) / len(tpss), 3) if tpss else None,
                    "peak_rss_gb_max": round(max(peaks), 4) if peaks else None,
                }
            )
        max_ok_length = max((r["target_input_tokens"] for r in ok_rows), default=None)
        failed_lengths = sorted(
            {
                int(r["target_input_tokens"])
                for r in model_rows
                if r.get("status") != "ok" and r.get("target_input_tokens") is not None
            }
        )
        per_model[model_id] = {
            "total_cells": len(model_rows),
            "ok_cells": len(ok_rows),
            "failed_cells": len(model_rows) - len(ok_rows),
            "max_input_tokens_ok": max_ok_length,
            "failed_at_lengths": failed_lengths,
            "per_length": per_length,
        }

    return {
        "schema_version": SCHEMA_VERSION_ROLLUP,
        "run_id": run_id,
        "host": host_label,
        "started_at": started_at,
        "ended_at": _now_iso(),
        "total_cells": sum(s["total_cells"] for s in per_model.values()),
        "ok_cells": sum(s["ok_cells"] for s in per_model.values()),
        "failed_cells": sum(s["failed_cells"] for s in per_model.values()),
        "per_model": per_model,
    }


# ---------- main -----------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(DEFAULT_MODELS),
        choices=list(MODEL_PATHS),
        help="Model names to test (default: 3 main 4-bit variants)",
    )
    parser.add_argument(
        "--lengths",
        nargs="+",
        type=int,
        default=list(DEFAULT_LENGTHS),
        help="Input token lengths to test (default: 1k 4k 16k 32k 64k 96k 128k)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_RUNS,
        help=f"Number of runs per cell (default: {DEFAULT_RUNS})",
    )
    parser.add_argument(
        "--output-tokens",
        type=int,
        default=DEFAULT_OUTPUT_TOKENS,
        help=f"Output tokens to generate per cell (default: {DEFAULT_OUTPUT_TOKENS})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for JSONL ledger",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke mode: 1st model × 1st length × 1 run only",
    )
    parser.add_argument(
        "--stop-after-first-fail-per-model",
        action="store_true",
        default=True,
        help="If a (model, length) cell fails, skip larger lengths for that model "
        "(default true; once 64k fails, 96k and 128k will also fail).",
    )
    args = parser.parse_args()

    if args.smoke:
        args.models = args.models[:1]
        args.lengths = args.lengths[:1]
        args.runs = 1

    run_id = _now_compact_utc() + "-long-context-ladder"
    if args.smoke:
        run_id += "-smoke"
    output_path = args.output_dir / f"{run_id}.jsonl"
    rollup_path = args.output_dir / f"{run_id}-rollup.jsonl"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    host_label = _host_label()
    started_at = _now_iso()

    print(f"[bench] run_id: {run_id}")
    print(f"[bench] host: {host_label}")
    print(f"[bench] models: {args.models}")
    print(f"[bench] lengths: {args.lengths}")
    print(f"[bench] runs per cell: {args.runs}")
    print(f"[bench] output_tokens per cell: {args.output_tokens}")
    print(f"[bench] ledger: {output_path}")
    print(f"[bench] rollup: {rollup_path}")
    print("")

    rows: list[dict[str, Any]] = []

    for model_name in args.models:
        print(f"[bench] === model: {model_name} ===")
        print(f"[bench] loading {MODEL_PATHS[model_name]} ...")
        load_start = time.perf_counter()
        try:
            model, tokenizer = _load_model(model_name)
        except Exception as exc:
            err_row = {
                "schema_version": SCHEMA_VERSION_CELL,
                "run_id": run_id,
                "host": host_label,
                "started_at": _now_iso(),
                "model_id": model_name,
                "model_path": MODEL_PATHS[model_name],
                "stage": "load",
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
            rows.append(err_row)
            _append_jsonl_row(output_path, err_row)
            print(f"[bench]   LOAD FAILED: {exc}")
            continue
        load_s = time.perf_counter() - load_start
        print(f"[bench]   loaded in {load_s:.1f}s")

        first_fail_at: int | None = None
        for target_tokens in args.lengths:
            if (
                args.stop_after_first_fail_per_model
                and first_fail_at is not None
                and target_tokens >= first_fail_at
            ):
                skip_row = {
                    "schema_version": SCHEMA_VERSION_CELL,
                    "run_id": run_id,
                    "host": host_label,
                    "started_at": _now_iso(),
                    "model_id": model_name,
                    "model_path": MODEL_PATHS[model_name],
                    "target_input_tokens": target_tokens,
                    "stage": "skipped",
                    "status": "skipped",
                    "skipped_because": f"first_fail_at_length={first_fail_at}",
                }
                rows.append(skip_row)
                _append_jsonl_row(output_path, skip_row)
                print(f"[bench]   length={target_tokens}: SKIPPED (>= first_fail {first_fail_at})")
                continue

            any_failed_at_this_length = False
            for run_idx in range(1, args.runs + 1):
                print(f"[bench]   length={target_tokens} run={run_idx}/{args.runs}")
                cell_started = _now_iso()

                try:
                    prompt, actual_tokens = _build_prompt_to_token_count(
                        tokenizer, target_tokens
                    )
                except Exception as exc:
                    row = {
                        "schema_version": SCHEMA_VERSION_CELL,
                        "run_id": run_id,
                        "host": host_label,
                        "started_at": cell_started,
                        "ended_at": _now_iso(),
                        "model_id": model_name,
                        "model_path": MODEL_PATHS[model_name],
                        "target_input_tokens": target_tokens,
                        "run_idx": run_idx,
                        "stage": "prompt_build",
                        "status": "failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                    rows.append(row)
                    _append_jsonl_row(output_path, row)
                    print(f"[bench]     PROMPT BUILD FAILED: {exc}")
                    any_failed_at_this_length = True
                    continue

                cell_metrics = _run_cell(model, tokenizer, prompt, args.output_tokens)
                peak_rss_gb = round(_peak_rss_bytes() / (1024**3), 4)

                row = {
                    "schema_version": SCHEMA_VERSION_CELL,
                    "run_id": run_id,
                    "host": host_label,
                    "started_at": cell_started,
                    "ended_at": _now_iso(),
                    "model_id": model_name,
                    "model_path": MODEL_PATHS[model_name],
                    "load_time_s": round(load_s, 3),
                    "target_input_tokens": target_tokens,
                    "actual_input_tokens": actual_tokens,
                    "max_output_tokens": args.output_tokens,
                    "run_idx": run_idx,
                    "peak_rss_gb_process_lifetime": peak_rss_gb,
                    "stage": "generate",
                    **cell_metrics,
                }
                rows.append(row)
                _append_jsonl_row(output_path, row)

                ttft_str = (
                    f"{cell_metrics['ttft_ms']:.0f}ms"
                    if cell_metrics.get("ttft_ms") is not None
                    else "—"
                )
                tps_str = (
                    f"{cell_metrics['decode_tps']:.1f}tps"
                    if cell_metrics.get("decode_tps") is not None
                    else "—"
                )
                status = cell_metrics.get("status", "?")
                print(
                    f"[bench]     status={status} ttft={ttft_str} decode={tps_str} "
                    f"peak_rss={peak_rss_gb:.2f}GB actual_input={actual_tokens}"
                )
                if status != "ok":
                    any_failed_at_this_length = True

                # Best-effort: release any transient memory between runs
                _mlx_metal_clear_cache()

            if any_failed_at_this_length and first_fail_at is None:
                first_fail_at = target_tokens

        print(f"[bench] unloading {model_name}")
        _free_model(model, tokenizer)
        print("")

    rollup = _make_rollup(rows, run_id, host_label, started_at)
    _append_jsonl_row(rollup_path, rollup)
    print(f"[bench] done.")
    print(f"[bench] ledger: {output_path}")
    print(f"[bench] rollup: {rollup_path}")
    print(f"[bench] total cells: {rollup['total_cells']}  ok: {rollup['ok_cells']}  failed: {rollup['failed_cells']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
