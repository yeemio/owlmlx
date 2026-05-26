"""Compare mlx-lm prefill chunk sizes through the owlmlx subprocess path.

This is the B-prefill-chunking workload runner. It measures the existing
mlx-lm ``prefill_step_size`` knob as consumed by owlmlx serving, not a custom
prefill implementation.

Usage:
    python scripts/bench/prefill_chunk_compare.py --smoke

    python scripts/bench/prefill_chunk_compare.py \\
        --models qwen3.6-27b-4bit \\
        --lengths 4096 16384 \\
        --chunk-sizes 512 2048 8192 \\
        --runs 1
"""

from __future__ import annotations

import argparse
import hashlib
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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from owlmlx.runtime import MlxLmSubprocessBackend  # noqa: E402
from scripts.bench.long_context_ladder import (  # noqa: E402
    MODEL_PATHS,
    _build_prompt_to_token_count,
)


DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "files" / "evidence" / "owlmlx" / "bench" / "prefill-chunking"
)
DEFAULT_MODELS: tuple[str, ...] = (
    "qwen3.6-27b-4bit",
    "gemma-4-31b-it-4bit",
    "qwen3.6-35b-a3b-4bit",
)
DEFAULT_LENGTHS: tuple[int, ...] = (4096, 16384, 32768, 65536)
DEFAULT_CHUNK_SIZES: tuple[int, ...] = (512, 2048, 8192)
DEFAULT_RUNS = 3
DEFAULT_OUTPUT_TOKENS = 32

SCHEMA_VERSION_CELL = "b.prefill_chunk.cell.v1"
SCHEMA_VERSION_ROLLUP = "b.prefill_chunk.rollup.v2"


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


def _append_jsonl_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True))
        f.write("\n")


def _peak_rss_bytes() -> int:
    ru = resource.getrusage(resource.RUSAGE_SELF)
    if sys.platform == "darwin":
        return int(ru.ru_maxrss)
    return int(ru.ru_maxrss) * 1024


def _rss_bytes_for_pid(pid: int | None) -> int | None:
    if pid is None:
        return None
    try:
        result = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return int(result.stdout.strip().splitlines()[-1].strip()) * 1024
    except (ValueError, IndexError):
        return None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_tokenizer(model_name: str) -> Any:
    from transformers import AutoTokenizer  # type: ignore

    return AutoTokenizer.from_pretrained(
        MODEL_PATHS[model_name],
        trust_remote_code=True,
    )


def _model_path_resolver(model_name: str) -> str:
    return MODEL_PATHS[model_name]


def _child_pid(backend: MlxLmSubprocessBackend, model_name: str) -> int | None:
    status = backend.status()
    children = status.detail.get("children")
    if not isinstance(children, dict):
        return None
    child = children.get(model_name)
    if not isinstance(child, dict):
        return None
    pid = child.get("pid")
    return int(pid) if isinstance(pid, int) else None


def _run_cell(
    *,
    backend: MlxLmSubprocessBackend,
    model_name: str,
    prompt: str,
    chunk_size: int,
    max_output_tokens: int,
) -> tuple[dict[str, Any], str]:
    t_start = time.perf_counter()
    t_first_token: float | None = None
    output_chunks: list[str] = []
    prefill_progress_event_count = 0
    last_prefill_progress: dict[str, Any] | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None

    try:
        for event in backend.stream_generate(
            model_name,
            prompt,
            max_tokens=max_output_tokens,
            temperature=0.0,
            prefill_chunk_tokens=chunk_size,
        ):
            if event.event == "prefill_progress":
                prefill_progress_event_count += 1
                last_prefill_progress = dict(event.detail)
                continue
            if event.event == "token":
                if t_first_token is None:
                    t_first_token = time.perf_counter()
                output_chunks.append(event.text)
                prompt_tokens = event.prompt_tokens or prompt_tokens
                completion_tokens = event.completion_tokens or completion_tokens
                finish_reason = event.finish_reason or finish_reason
                continue
            if event.event == "done":
                prompt_tokens = event.prompt_tokens or prompt_tokens
                completion_tokens = event.completion_tokens or completion_tokens
                finish_reason = event.finish_reason or finish_reason
                break
            if event.event == "error":
                return (
                    {
                        "status": "failed",
                        "error": str(event.detail.get("message") or event.error_code),
                    },
                    "",
                )
    except Exception as exc:
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}, ""

    t_done = time.perf_counter()
    text = "".join(output_chunks)
    wall_ms = (t_done - t_start) * 1000
    ttft_ms = (t_first_token - t_start) * 1000 if t_first_token is not None else None
    decode_window_s = (
        max(t_done - t_first_token, 1e-9) if t_first_token is not None else None
    )
    child_rss = _rss_bytes_for_pid(_child_pid(backend, model_name))
    parent_peak = _peak_rss_bytes()
    aggregate_rss = parent_peak + (child_rss or 0)

    return (
        {
            "status": "ok",
            "ttft_ms": round(ttft_ms, 3) if ttft_ms is not None else None,
            "decode_tps": (
                round(float(completion_tokens or len(output_chunks)) / decode_window_s, 3)
                if decode_window_s is not None
                else None
            ),
            "wall_ms": round(wall_ms, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens or len(output_chunks),
            "peak_rss_gb_process_lifetime": round(aggregate_rss / (1024**3), 4),
            "child_rss_gb_observed_after_cell": (
                round(child_rss / (1024**3), 4) if child_rss is not None else None
            ),
            "prefill_progress_event_count": prefill_progress_event_count,
            "last_prefill_progress": last_prefill_progress,
            "finish_reason": finish_reason,
        },
        text,
    )


def _within_chunk_determinism_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, int, int], list[str]] = {}
    for row in rows:
        if row.get("verdict") != "pass":
            continue
        key = (
            str(row.get("model_id")),
            int(row.get("target_input_tokens") or 0),
            int(row.get("chunk_size") or 0),
        )
        output_hash = row.get("output_byte_hash")
        if isinstance(output_hash, str):
            groups.setdefault(key, []).append(output_hash)
    repeated_groups = [hashes for hashes in groups.values() if len(hashes) >= 2]
    deterministic = sum(1 for hashes in repeated_groups if len(set(hashes)) == 1)
    if not repeated_groups:
        status = "not_measured"
        match_rate: float | None = None
    else:
        match_rate = round(deterministic / len(repeated_groups), 6)
        status = "passed" if deterministic == len(repeated_groups) else "failed"
    return {
        "gate": "required",
        "status": status,
        "total_groups": len(groups),
        "groups_with_repeated_runs": len(repeated_groups),
        "repeated_groups_with_identical_output": deterministic,
        "repeat_match_rate": match_rate,
    }


def _cross_chunk_consistency_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, int, int], set[str]] = {}
    for row in rows:
        if row.get("verdict") != "pass":
            continue
        key = (
            str(row.get("model_id")),
            int(row.get("target_input_tokens") or 0),
            int(row.get("run_idx") or 0),
        )
        output_hash = row.get("output_byte_hash")
        if isinstance(output_hash, str):
            groups.setdefault(key, set()).add(output_hash)
    total_groups = len(groups)
    identical = sum(1 for hashes in groups.values() if len(hashes) == 1)
    return {
        "gate": "informational_only",
        "total_groups": total_groups,
        "groups_with_identical_output": identical,
        "match_rate": round(identical / total_groups, 6) if total_groups else None,
        "note": (
            "Different prefill_step_size values may follow different deterministic "
            "mlx-lm numeric paths; this metric is diagnostic and does not gate B."
        ),
    }


def _write_rollup(
    *,
    path: Path,
    run_id: str,
    rows: list[dict[str, Any]],
    run_complete: bool = True,
    stop_reason: str | None = None,
    time_limit_s: float | None = None,
    elapsed_s: float | None = None,
) -> None:
    within_chunk_determinism = _within_chunk_determinism_summary(rows)
    cross_chunk_consistency = _cross_chunk_consistency_summary(rows)
    ok_cells = sum(1 for row in rows if row.get("verdict") == "pass")
    failed_cells = len(rows) - ok_cells
    progress_candidates = [
        row
        for row in rows
        if row.get("verdict") == "pass" and int(row.get("target_input_tokens") or 0) >= 8192
    ]
    progress_observable: bool | None
    if progress_candidates:
        progress_observable = all(
            int((row.get("metrics") or {}).get("prefill_progress_event_count") or 0) >= 2
            for row in progress_candidates
        )
    else:
        progress_observable = None
    determinism_status = within_chunk_determinism.get("status")
    if determinism_status == "not_measured":
        determinism_holds: bool | None = None
    else:
        determinism_holds = determinism_status == "passed"
    rollup = {
        "schema_version": SCHEMA_VERSION_ROLLUP,
        "gate": "B",
        "run_id": run_id,
        "created_at": _now_iso(),
        "cell_count": len(rows),
        "ok_cells": ok_cells,
        "failed_cells": failed_cells,
        "run_complete": run_complete,
        "stop_reason": stop_reason,
        "time_limit_s": time_limit_s,
        "elapsed_s": round(elapsed_s, 3) if elapsed_s is not None else None,
        "within_chunk_determinism": within_chunk_determinism,
        "cross_chunk_consistency": cross_chunk_consistency,
        "baseline_regression_long_context_ladder": {
            "available": False,
            "delta_pct": None,
            "note": "not computed by this runner; compare separately against 20260526 long-context baseline",
        },
        "graduates": {
            "chunk_param_exposed": ok_cells > 0,
            "progress_events_observable": progress_observable,
            "within_chunk_determinism_holds": determinism_holds,
            "cross_chunk_consistency_holds": (
                cross_chunk_consistency.get("match_rate") == 1.0
            ),
            "baseline_no_regression": None,
        },
    }
    _append_jsonl_row(path, rollup)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--lengths", nargs="+", type=int, default=list(DEFAULT_LENGTHS))
    parser.add_argument(
        "--chunk-sizes",
        nargs="+",
        type=int,
        default=list(DEFAULT_CHUNK_SIZES),
    )
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_OUTPUT_TOKENS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--timeout-s", type=float, default=1800.0)
    parser.add_argument(
        "--time-limit-s",
        type=float,
        default=None,
        help="Stop at the next cell boundary after this many seconds and write a partial rollup.",
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)

    if args.smoke:
        args.models = [args.models[0]]
        args.lengths = [4096]
        args.chunk_sizes = [512, 2048]
        args.runs = 1
        args.max_output_tokens = min(args.max_output_tokens, 8)

    run_id = args.run_id or f"{_now_compact_utc()}-prefill-chunk-compare"
    output_dir: Path = args.output_dir
    ledger_path = output_dir / f"{run_id}.jsonl"
    rollup_path = output_dir / f"{run_id}-rollup.jsonl"
    host = _host_label()
    rows: list[dict[str, Any]] = []
    started_monotonic = time.perf_counter()
    stop_reason: str | None = None

    def time_limit_reached() -> bool:
        return (
            args.time_limit_s is not None
            and time.perf_counter() - started_monotonic >= args.time_limit_s
        )

    for model_name in args.models:
        if time_limit_reached():
            stop_reason = f"time_limit_before_model:{model_name}"
            break
        tokenizer = _load_tokenizer(model_name)
        backend = MlxLmSubprocessBackend(
            model_path_resolver=_model_path_resolver,
            timeout_s=args.timeout_s,
        )
        load_result = backend.load(model_name)
        if not load_result.ok:
            row = {
                "schema_version": SCHEMA_VERSION_CELL,
                "gate": "B",
                "run_id": run_id,
                "created_at": _now_iso(),
                "host": host,
                "model_id": model_name,
                "target_input_tokens": None,
                "actual_input_tokens": None,
                "chunk_size": None,
                "run_idx": None,
                "metrics": {},
                "output_byte_hash": None,
                "verdict": "fail",
                "blocker_summary": load_result.message,
            }
            rows.append(row)
            _append_jsonl_row(ledger_path, row)
            continue
        try:
            for target_tokens in args.lengths:
                if stop_reason:
                    break
                if time_limit_reached():
                    stop_reason = f"time_limit_before_length:{model_name}:{target_tokens}"
                    break
                prompt, actual_tokens = _build_prompt_to_token_count(
                    tokenizer,
                    target_tokens,
                )
                for run_idx in range(1, args.runs + 1):
                    if stop_reason:
                        break
                    for chunk_size in args.chunk_sizes:
                        if time_limit_reached():
                            stop_reason = (
                                "time_limit_before_cell:"
                                f"{model_name}:{target_tokens}:run{run_idx}:chunk{chunk_size}"
                            )
                            break
                        metrics, text = _run_cell(
                            backend=backend,
                            model_name=model_name,
                            prompt=prompt,
                            chunk_size=chunk_size,
                            max_output_tokens=args.max_output_tokens,
                        )
                        ok = metrics.get("status") == "ok"
                        row = {
                            "schema_version": SCHEMA_VERSION_CELL,
                            "gate": "B",
                            "run_id": run_id,
                            "created_at": _now_iso(),
                            "host": host,
                            "model_id": model_name,
                            "target_input_tokens": target_tokens,
                            "actual_input_tokens": actual_tokens,
                            "chunk_size": chunk_size,
                            "run_idx": run_idx,
                            "metrics": metrics,
                            "output_byte_hash": _sha256_text(text) if ok else None,
                            "output_byte_length": len(text.encode("utf-8")) if ok else None,
                            "output_text_preview": text[:240] if ok else None,
                            "verdict": "pass" if ok else "fail",
                        }
                        if not ok:
                            row["blocker_summary"] = metrics.get("error")
                        rows.append(row)
                        _append_jsonl_row(ledger_path, row)
        finally:
            backend.unload(model_name)

    elapsed_s = time.perf_counter() - started_monotonic
    _write_rollup(
        path=rollup_path,
        run_id=run_id,
        rows=rows,
        run_complete=stop_reason is None,
        stop_reason=stop_reason,
        time_limit_s=args.time_limit_s,
        elapsed_s=elapsed_s,
    )
    print(json.dumps({"ledger": str(ledger_path), "rollup": str(rollup_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
