"""Small B-2 prefix-cache compatibility probes.

This script is intentionally narrow. It exercises the native backend's opt-in
automatic prefix scope without requiring ``X-Owlmlx-Session-Id`` and records
whether cached-token metadata comes from the runtime event detail.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime.mlx_native_backend import MlxNativeBackend
from owlmlx.runtime.kernel import RuntimeKernel


DEFAULT_OUTPUT_DIR = Path("files/evidence/owlmlx/bench/prefix-cache-compatibility")
DEFAULT_MODEL = "/Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit"
DEFAULT_MODEL_GB = 27.0
DEFAULT_MAX_RESIDENT_BYTES = 2 * 1024 * 1024 * 1024


@contextmanager
def _auto_prefix_env(max_resident_bytes: int) -> Iterator[None]:
    keys = {
        "OWLMLX_SESSION_CACHE_ENABLED": "1",
        "OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED": "1",
        "OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES": str(int(max_resident_bytes)),
    }
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key, value in keys.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _now_compact_utc() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _now_iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stream_once(
    kernel: RuntimeKernel,
    *,
    model_id: str,
    prompt: str,
    max_tokens: int,
) -> dict[str, Any]:
    text_parts: list[str] = []
    terminal: Any | None = None

    async def _collect() -> None:
        nonlocal terminal
        async for event in kernel.generate_stream(
            prompt,
            model_id=model_id,
            max_tokens=max_tokens,
        ):
            if event.text:
                text_parts.append(event.text)
            terminal = event

    asyncio.run(_collect())
    detail = getattr(terminal, "detail", {}) if terminal is not None else {}
    return {
        "ok": terminal is not None and getattr(terminal, "event", None) == "done",
        "text": "".join(text_parts),
        "prompt_tokens": getattr(terminal, "prompt_tokens", None),
        "completion_tokens": getattr(terminal, "completion_tokens", None),
        "finish_reason": getattr(terminal, "finish_reason", None),
        "detail": detail if isinstance(detail, dict) else {},
    }


def _unique_bypass_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, object, object]] = set()
    events: list[dict[str, Any]] = []
    for record in records:
        event = record.get("status_after", {}).get("last_bypass_event")
        if not isinstance(event, dict):
            continue
        key = (
            str(event.get("reason_code", "")),
            event.get("cache_object_id"),
            event.get("time_s"),
        )
        if key in seen:
            continue
        seen.add(key)
        events.append(event)
    return events


def run_auto_prefix_hit_probe(
    *,
    model_id: str,
    model_gb: float,
    output_dir: Path,
    max_tokens: int,
    max_resident_bytes: int,
    run_id: str | None = None,
) -> dict[str, Any]:
    timestamp = _now_compact_utc()
    actual_run_id = run_id or f"{timestamp}-b2-auto-prefix-real-hit"
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / f"{actual_run_id}.jsonl"
    summary_path = output_dir / f"{actual_run_id}-summary.json"
    prompts = [
        (
            "prefix_seed",
            "System: You are verifying prefix cache behavior.\n"
            "User: Summarize alpha in one short phrase.\n"
            "Assistant:",
        ),
        (
            "strict_prefix_extension",
            "System: You are verifying prefix cache behavior.\n"
            "User: Summarize alpha in one short phrase.\n"
            "Assistant:\nContinue with one extra word:",
        ),
        (
            "reject_seed",
            "System: You are verifying non-prefix cache isolation.\n"
            "User: Summarize beta in one short phrase.\n"
            "Assistant:",
        ),
        (
            "non_prefix_control",
            "System: This is a different request.\n"
            "User: Produce an unrelated short phrase.\n"
            "Assistant:",
        ),
    ]

    records: list[dict[str, Any]] = []
    with _auto_prefix_env(max_resident_bytes):
        backend = MlxNativeBackend()
        kernel = RuntimeKernel(
            backend,
            host_pressure_sampler=host_pressure_not_sampled_snapshot,
        )
        load = kernel.load_model(model_id, memory_gb=model_gb)
        cleanup = None
        try:
            with ledger_path.open("w", encoding="utf-8") as stream:
                for index, (case, prompt) in enumerate(prompts, start=1):
                    before = kernel.status().backend.detail.get("session_kv_cache", {})
                    result = _stream_once(
                        kernel,
                        model_id=model_id,
                        prompt=prompt,
                        max_tokens=max_tokens,
                    )
                    after = kernel.status().backend.detail.get("session_kv_cache", {})
                    cache_detail = result["detail"].get("session_kv_cache", {})
                    record = {
                        "schema_version": "b2.automatic_prefix_reuse.v1",
                        "run_id": actual_run_id,
                        "timestamp_utc": _now_iso_utc(),
                        "case": case,
                        "sample_index": index,
                        "model_id": model_id,
                        "model_gb": model_gb,
                        "prompt_chars": len(prompt),
                        "request": {
                            "session_id_header_set": False,
                            "max_tokens": max_tokens,
                        },
                        "generation": {
                            "ok": result["ok"],
                            "prompt_tokens": result["prompt_tokens"],
                            "completion_tokens": result["completion_tokens"],
                            "finish_reason": result["finish_reason"],
                        },
                        "session_kv_cache": cache_detail,
                        "status_before": before,
                        "status_after": after,
                    }
                    records.append(record)
                    stream.write(json.dumps(record, sort_keys=True))
                    stream.write("\n")
        finally:
            cleanup = kernel.unload_model(model_id)

    hit_records = [
        record
        for record in records
        if record["session_kv_cache"].get("cache_decision") == "reuse"
        and int(record["session_kv_cache"].get("cached_prompt_tokens") or 0) > 0
    ]
    fallback_records = [
        record
        for record in records
        if str(record["session_kv_cache"].get("cache_reason_code", "")).startswith(
            "auto_prefix_ineligible_"
        )
    ]
    bypass_events = _unique_bypass_events(records)
    bypass_reason_counts: dict[str, int] = {}
    for event in bypass_events:
        reason = str(event.get("reason_code", "unknown"))
        bypass_reason_counts[reason] = bypass_reason_counts.get(reason, 0) + 1
    reuse_trim_bypass_count = bypass_reason_counts.get(
        "reuse_trim_unavailable_fresh_cache",
        0,
    )
    completion_trim_unavailable_count = bypass_reason_counts.get(
        "auto_prefix_completion_trim_unavailable",
        0,
    )
    auto_prefix_ineligible_count = sum(
        count
        for reason, count in bypass_reason_counts.items()
        if reason.startswith("auto_prefix_ineligible_")
    )
    last_counters = records[-1]["status_after"].get("counters", {}) if records else {}
    known_blocker = None
    if len(hit_records) == 0 and completion_trim_unavailable_count >= 1:
        known_blocker = "auto_prefix_completion_trim_unavailable"
    elif len(hit_records) == 0 and reuse_trim_bypass_count >= 1:
        known_blocker = "reuse_trim_unavailable_fresh_cache"
    summary = {
        "schema_version": "b2.automatic_prefix_reuse.summary.v1",
        "run_id": actual_run_id,
        "timestamp_utc": _now_iso_utc(),
        "ledger": str(ledger_path),
        "model_id": model_id,
        "model_gb": model_gb,
        "sample_count": len(records),
        "usable_hit_count": len(hit_records),
        "terminal_fallback_count": len(fallback_records),
        "reuse_trim_bypass_count": reuse_trim_bypass_count,
        "completion_trim_unavailable_count": completion_trim_unavailable_count,
        "auto_prefix_ineligible_count": auto_prefix_ineligible_count,
        "bypass_reason_counts": bypass_reason_counts,
        "hits_total": int(last_counters.get("hits", 0)),
        "misses_total": int(last_counters.get("misses", 0)),
        "trim_bypasses_total": int(last_counters.get("trim_bypasses", 0)),
        "trim_evictions_total": int(last_counters.get("trim_evictions", 0)),
        "drops_total": int(last_counters.get("drops", 0)),
        "rejects_total": int(last_counters.get("rejects", 0)),
        "expirations_total": int(last_counters.get("expirations", 0)),
        "load_ok": bool(load.ok),
        "cleanup_unload_ok": bool(cleanup.ok if cleanup is not None else False),
        "known_blocker": known_blocker,
        "verdict": (
            "passed"
            if load.ok
            and cleanup is not None
            and cleanup.ok
            and len(hit_records) >= 1
            and (
                len(fallback_records) >= 1
                or len(auto_prefix_ineligible_records) >= 1
            )
            and all(record["generation"]["ok"] for record in records)
            and int(last_counters.get("drops", 0)) == 0
            else "failed"
        ),
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    auto = subparsers.add_parser("auto-prefix-hit")
    auto.add_argument("--model", default=DEFAULT_MODEL)
    auto.add_argument("--model-gb", type=float, default=DEFAULT_MODEL_GB)
    auto.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    auto.add_argument("--max-tokens", type=int, default=1)
    auto.add_argument(
        "--max-resident-bytes",
        type=int,
        default=DEFAULT_MAX_RESIDENT_BYTES,
    )
    auto.add_argument("--run-id", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "auto-prefix-hit":
        summary = run_auto_prefix_hit_probe(
            model_id=args.model,
            model_gb=args.model_gb,
            output_dir=args.output_dir,
            max_tokens=args.max_tokens,
            max_resident_bytes=args.max_resident_bytes,
            run_id=args.run_id,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary.get("verdict") == "passed" else 1
    raise ValueError(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
