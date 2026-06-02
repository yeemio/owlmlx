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

from fastapi.testclient import TestClient

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.mlx_native_backend import MlxNativeBackend
from owlmlx.runtime.server import create_app


DEFAULT_OUTPUT_DIR = Path("files/evidence/owlmlx/bench/prefix-cache-compatibility")
DEFAULT_MODEL = "/Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit"
DEFAULT_MODEL_GB = 27.0
DEFAULT_MAX_RESIDENT_BYTES = 2 * 1024 * 1024 * 1024
B2_COMPAT_REQUIRED_HIT_CASES = {
    "openai_chat_completions_sse": "openai_strict_prefix_extension",
    "anthropic_messages_sse": "anthropic_strict_prefix_extension",
}
B2_AUTO_PREFIX_REQUIRED_HIT_CASE = "strict_prefix_extension"


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


def _sse_json_payloads(response_text: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for line in response_text.splitlines():
        if not line.startswith("data: "):
            continue
        data = line.removeprefix("data: ").strip()
        if data == "[DONE]":
            continue
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _openai_cached_tokens(response_text: str) -> int | None:
    for payload in reversed(_sse_json_payloads(response_text)):
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            continue
        details = usage.get("prompt_tokens_details")
        if not isinstance(details, dict):
            continue
        cached = details.get("cached_tokens")
        if cached is None:
            continue
        try:
            return max(int(cached), 0)
        except (TypeError, ValueError):
            return None
    return None


def _anthropic_cache_read_tokens(response_text: str) -> int | None:
    for payload in reversed(_sse_json_payloads(response_text)):
        if payload.get("type") != "message_delta":
            continue
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            continue
        cached = usage.get("cache_read_input_tokens")
        if cached is None:
            continue
        try:
            return max(int(cached), 0)
        except (TypeError, ValueError):
            return None
    return None


def _route_response_ok(record: dict[str, Any]) -> bool:
    response = record.get("response")
    if not isinstance(response, dict):
        return False
    content_type = str(response.get("content_type") or "")
    return int(response.get("status_code") or 0) == 200 and "text/event-stream" in content_type


def _route_cached_tokens(record: dict[str, Any]) -> int:
    response = record.get("response")
    if not isinstance(response, dict):
        return 0
    if record.get("surface") == "openai_chat_completions_sse":
        value = response.get("openai_cached_tokens")
    elif record.get("surface") == "anthropic_messages_sse":
        value = response.get("anthropic_cache_read_input_tokens")
    else:
        value = None
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def _nonnegative_int(value: Any) -> int:
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def _required_route_hit_case_results(records: list[dict[str, Any]]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for surface, required_case in B2_COMPAT_REQUIRED_HIT_CASES.items():
        matching_records = [
            record
            for record in records
            if record.get("surface") == surface and record.get("case") == required_case
        ]
        cached_tokens = [
            _route_cached_tokens(record)
            for record in matching_records
            if _route_response_ok(record)
        ]
        results[surface] = {
            "required_case": required_case,
            "observed_count": len(matching_records),
            "route_response_ok_count": sum(
                1 for record in matching_records if _route_response_ok(record)
            ),
            "max_cached_tokens": max(cached_tokens, default=0),
            "hit_observed": bool(cached_tokens) and max(cached_tokens) > 0,
        }
    return results


def _read_jsonl_records(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return records, [f"read_error:{path}:{exc}"]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_json:{path}:{line_number}:{exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"non_object_record:{path}:{line_number}")
            continue
        records.append(record)
    return records, errors


def _compat_route_failure_reasons(
    *,
    records: list[dict[str, Any]],
    read_errors: list[str],
    all_route_responses_ok: bool,
    all_required_route_hits_observed: bool,
    drops_total: int,
    rejects_total: int,
    expirations_total: int,
) -> list[str]:
    reasons: list[str] = []
    if read_errors:
        reasons.append("ledger_read_errors")
    if not records:
        reasons.append("no_records")
    if not all_route_responses_ok:
        reasons.append("route_response_not_http_200_sse")
    if not all_required_route_hits_observed:
        reasons.append("required_strict_prefix_extension_hit_missing")
    if drops_total != 0:
        reasons.append("session_cache_drops_nonzero")
    if rejects_total != 0:
        reasons.append("session_cache_rejects_nonzero")
    if expirations_total != 0:
        reasons.append("session_cache_expirations_nonzero")
    return reasons


def audit_compat_route_ledger(path: Path) -> dict[str, Any]:
    records, read_errors = _read_jsonl_records(path)
    route_response_ok_count = sum(1 for record in records if _route_response_ok(record))
    all_route_responses_ok = bool(records) and route_response_ok_count == len(records)
    required_route_hit_case_results = _required_route_hit_case_results(records)
    all_required_route_hits_observed = all(
        bool(result.get("hit_observed"))
        for result in required_route_hit_case_results.values()
    )
    openai_hits = [
        record
        for record in records
        if record.get("surface") == "openai_chat_completions_sse"
        and _route_cached_tokens(record) > 0
    ]
    anthropic_hits = [
        record
        for record in records
        if record.get("surface") == "anthropic_messages_sse"
        and _route_cached_tokens(record) > 0
    ]
    last_counters = records[-1].get("status_after", {}).get("counters", {}) if records else {}
    if not isinstance(last_counters, dict):
        last_counters = {}
    drops_total = _nonnegative_int(last_counters.get("drops"))
    rejects_total = _nonnegative_int(last_counters.get("rejects"))
    expirations_total = _nonnegative_int(last_counters.get("expirations"))
    failure_reasons = _compat_route_failure_reasons(
        records=records,
        read_errors=read_errors,
        all_route_responses_ok=all_route_responses_ok,
        all_required_route_hits_observed=all_required_route_hits_observed,
        drops_total=drops_total,
        rejects_total=rejects_total,
        expirations_total=expirations_total,
    )
    return {
        "schema_version": "b2.compat_route_automatic_prefix_reuse.audit.v1",
        "kind": "compat_route_ledger_audit",
        "path": str(path),
        "record_count": len(records),
        "schema_versions": sorted(
            {str(record.get("schema_version", "missing")) for record in records}
        ),
        "run_ids": sorted({str(record.get("run_id", "missing")) for record in records}),
        "route_response_ok_count": route_response_ok_count,
        "all_route_responses_ok": all_route_responses_ok,
        "required_route_hit_cases": B2_COMPAT_REQUIRED_HIT_CASES,
        "required_route_hit_case_results": required_route_hit_case_results,
        "all_required_route_hits_observed": all_required_route_hits_observed,
        "openai_cached_token_hit_count": len(openai_hits),
        "anthropic_cache_read_hit_count": len(anthropic_hits),
        "drops_total": drops_total,
        "rejects_total": rejects_total,
        "expirations_total": expirations_total,
        "errors": read_errors,
        "failure_reasons": failure_reasons,
        "verdict": "passed" if not failure_reasons else "failed",
    }


def _auto_prefix_hit_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("session_kv_cache", {}).get("cache_decision") == "reuse"
        and _nonnegative_int(
            record.get("session_kv_cache", {}).get("cached_prompt_tokens")
        )
        > 0
    ]


def _auto_prefix_ineligible_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if str(
            record.get("session_kv_cache", {}).get("cache_reason_code", "")
        ).startswith("auto_prefix_ineligible_")
    ]


def _auto_prefix_bypass_reason_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in _unique_bypass_events(records):
        reason = str(event.get("reason_code", "unknown"))
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _auto_prefix_failure_reasons(
    *,
    records: list[dict[str, Any]],
    read_errors: list[str],
    strict_prefix_hit_observed: bool,
    auto_prefix_ineligible_count: int,
    all_generations_ok: bool,
    drops_total: int,
    rejects_total: int,
    expirations_total: int,
    bypass_reason_counts: dict[str, int],
) -> list[str]:
    reasons: list[str] = []
    if read_errors:
        reasons.append("ledger_read_errors")
    if not records:
        reasons.append("no_records")
    if not all_generations_ok:
        reasons.append("generation_not_ok")
    if not strict_prefix_hit_observed:
        reasons.append("required_strict_prefix_reuse_hit_missing")
    if auto_prefix_ineligible_count < 1:
        reasons.append("auto_prefix_ineligible_fallback_missing")
    if drops_total != 0:
        reasons.append("session_cache_drops_nonzero")
    if rejects_total != 0:
        reasons.append("session_cache_rejects_nonzero")
    if expirations_total != 0:
        reasons.append("session_cache_expirations_nonzero")
    if bypass_reason_counts.get("auto_prefix_completion_trim_unavailable", 0) > 0:
        reasons.append("auto_prefix_completion_trim_unavailable")
    if bypass_reason_counts.get("reuse_trim_unavailable_fresh_cache", 0) > 0:
        reasons.append("reuse_trim_unavailable_fresh_cache")
    return reasons


def audit_auto_prefix_ledger(path: Path) -> dict[str, Any]:
    records, read_errors = _read_jsonl_records(path)
    hit_records = _auto_prefix_hit_records(records)
    ineligible_records = _auto_prefix_ineligible_records(records)
    strict_prefix_hit_records = [
        record
        for record in hit_records
        if record.get("case") == B2_AUTO_PREFIX_REQUIRED_HIT_CASE
    ]
    strict_prefix_cached_tokens = [
        _nonnegative_int(
            record.get("session_kv_cache", {}).get("cached_prompt_tokens")
        )
        for record in strict_prefix_hit_records
    ]
    all_generations_ok = bool(records) and all(
        bool(record.get("generation", {}).get("ok")) for record in records
    )
    last_counters = records[-1].get("status_after", {}).get("counters", {}) if records else {}
    if not isinstance(last_counters, dict):
        last_counters = {}
    drops_total = _nonnegative_int(last_counters.get("drops"))
    rejects_total = _nonnegative_int(last_counters.get("rejects"))
    expirations_total = _nonnegative_int(last_counters.get("expirations"))
    bypass_reason_counts = _auto_prefix_bypass_reason_counts(records)
    strict_prefix_hit_observed = bool(strict_prefix_cached_tokens) and max(
        strict_prefix_cached_tokens
    ) > 0
    failure_reasons = _auto_prefix_failure_reasons(
        records=records,
        read_errors=read_errors,
        strict_prefix_hit_observed=strict_prefix_hit_observed,
        auto_prefix_ineligible_count=len(ineligible_records),
        all_generations_ok=all_generations_ok,
        drops_total=drops_total,
        rejects_total=rejects_total,
        expirations_total=expirations_total,
        bypass_reason_counts=bypass_reason_counts,
    )
    return {
        "schema_version": "b2.automatic_prefix_reuse.audit.v1",
        "kind": "auto_prefix_ledger_audit",
        "path": str(path),
        "record_count": len(records),
        "schema_versions": sorted(
            {str(record.get("schema_version", "missing")) for record in records}
        ),
        "run_ids": sorted({str(record.get("run_id", "missing")) for record in records}),
        "required_hit_case": B2_AUTO_PREFIX_REQUIRED_HIT_CASE,
        "strict_prefix_hit_count": len(strict_prefix_hit_records),
        "strict_prefix_cached_tokens": max(strict_prefix_cached_tokens, default=0),
        "strict_prefix_hit_observed": strict_prefix_hit_observed,
        "usable_hit_count": len(hit_records),
        "auto_prefix_ineligible_count": len(ineligible_records),
        "all_generations_ok": all_generations_ok,
        "bypass_reason_counts": bypass_reason_counts,
        "drops_total": drops_total,
        "rejects_total": rejects_total,
        "expirations_total": expirations_total,
        "errors": read_errors,
        "failure_reasons": failure_reasons,
        "verdict": "passed" if not failure_reasons else "failed",
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


def _route_hit_verdict(
    *,
    load_ok: bool,
    cleanup_unload_ok: bool,
    all_route_responses_ok: bool,
    all_required_route_hits_observed: bool,
    openai_cached_tokens: int | None,
    anthropic_cache_read_input_tokens: int | None,
    drops_total: int,
    rejects_total: int,
    expirations_total: int,
) -> str:
    if (
        load_ok
        and cleanup_unload_ok
        and all_route_responses_ok
        and all_required_route_hits_observed
        and int(openai_cached_tokens or 0) > 0
        and int(anthropic_cache_read_input_tokens or 0) > 0
        and drops_total == 0
        and rejects_total == 0
        and expirations_total == 0
    ):
        return "passed"
    return "failed"


def _auto_prefix_hit_verdict(
    *,
    load_ok: bool,
    cleanup_unload_ok: bool,
    usable_hit_count: int,
    terminal_fallback_count: int,
    auto_prefix_ineligible_count: int,
    all_generations_ok: bool,
    drops_total: int,
) -> str:
    if (
        load_ok
        and cleanup_unload_ok
        and usable_hit_count >= 1
        and (terminal_fallback_count >= 1 or auto_prefix_ineligible_count >= 1)
        and all_generations_ok
        and drops_total == 0
    ):
        return "passed"
    return "failed"


def _compat_route_cases(model_id: str) -> list[tuple[str, str, dict[str, Any]]]:
    seed_content = (
        "System: You are verifying prefix cache behavior.\n"
        "User: Summarize alpha in one short phrase.\n"
        "Assistant:"
    )
    extension_content = (
        "System: You are verifying prefix cache behavior.\n"
        "User: Summarize alpha in one short phrase.\n"
        "Assistant:\nContinue with one extra word:"
    )
    return [
        (
            "openai_prefix_seed",
            "openai_chat_completions_sse",
            {
                "path": "/v1/chat/completions",
                "json": {
                    "model": model_id,
                    "messages": [{"role": "user", "content": seed_content}],
                    "stream": True,
                    "max_tokens": 1,
                },
            },
        ),
        (
            "openai_strict_prefix_extension",
            "openai_chat_completions_sse",
            {
                "path": "/v1/chat/completions",
                "json": {
                    "model": model_id,
                    "messages": [{"role": "user", "content": extension_content}],
                    "stream": True,
                    "max_tokens": 1,
                },
            },
        ),
        (
            "anthropic_prefix_seed",
            "anthropic_messages_sse",
            {
                "path": "/v1/messages",
                "json": {
                    "model": model_id,
                    "messages": [{"role": "user", "content": seed_content}],
                    "stream": True,
                    "max_tokens": 1,
                },
            },
        ),
        (
            "anthropic_strict_prefix_extension",
            "anthropic_messages_sse",
            {
                "path": "/v1/messages",
                "json": {
                    "model": model_id,
                    "messages": [{"role": "user", "content": extension_content}],
                    "stream": True,
                    "max_tokens": 1,
                },
            },
        ),
    ]


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
        "verdict": _auto_prefix_hit_verdict(
            load_ok=bool(load.ok),
            cleanup_unload_ok=bool(cleanup.ok if cleanup is not None else False),
            usable_hit_count=len(hit_records),
            terminal_fallback_count=len(fallback_records),
            auto_prefix_ineligible_count=auto_prefix_ineligible_count,
            all_generations_ok=all(record["generation"]["ok"] for record in records),
            drops_total=int(last_counters.get("drops", 0)),
        ),
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def run_compat_route_hit_probe(
    *,
    model_id: str,
    model_gb: float,
    output_dir: Path,
    max_resident_bytes: int,
    run_id: str | None = None,
) -> dict[str, Any]:
    timestamp = _now_compact_utc()
    actual_run_id = run_id or f"{timestamp}-b2-compat-route-real-hit"
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / f"{actual_run_id}.jsonl"
    summary_path = output_dir / f"{actual_run_id}-summary.json"

    records: list[dict[str, Any]] = []
    with _auto_prefix_env(max_resident_bytes):
        backend = MlxNativeBackend()
        kernel = RuntimeKernel(
            backend,
            host_pressure_sampler=host_pressure_not_sampled_snapshot,
        )
        load = kernel.load_model(model_id, memory_gb=model_gb)
        cleanup = None
        client = TestClient(create_app(kernel))
        try:
            with ledger_path.open("w", encoding="utf-8") as stream:
                for index, (case, surface, request_spec) in enumerate(
                    _compat_route_cases(model_id),
                    start=1,
                ):
                    before = kernel.status().backend.detail.get("session_kv_cache", {})
                    response = client.post(
                        request_spec["path"],
                        json=request_spec["json"],
                    )
                    after = kernel.status().backend.detail.get("session_kv_cache", {})
                    openai_cached_tokens = (
                        _openai_cached_tokens(response.text)
                        if surface == "openai_chat_completions_sse"
                        else None
                    )
                    anthropic_cache_read_input_tokens = (
                        _anthropic_cache_read_tokens(response.text)
                        if surface == "anthropic_messages_sse"
                        else None
                    )
                    record = {
                        "schema_version": "b2.compat_route_automatic_prefix_reuse.v1",
                        "run_id": actual_run_id,
                        "timestamp_utc": _now_iso_utc(),
                        "case": case,
                        "sample_index": index,
                        "surface": surface,
                        "model_id": model_id,
                        "model_gb": model_gb,
                        "request": {
                            "path": request_spec["path"],
                            "session_id_header_set": False,
                            "stream": True,
                            "max_tokens": request_spec["json"].get("max_tokens"),
                        },
                        "response": {
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type"),
                            "openai_cached_tokens": openai_cached_tokens,
                            "anthropic_cache_read_input_tokens": (
                                anthropic_cache_read_input_tokens
                            ),
                        },
                        "status_before": before,
                        "status_after": after,
                    }
                    records.append(record)
                    stream.write(json.dumps(record, sort_keys=True))
                    stream.write("\n")
        finally:
            cleanup = kernel.unload_model(model_id)

    openai_hits = [
        record
        for record in records
        if int(record["response"].get("openai_cached_tokens") or 0) > 0
    ]
    anthropic_hits = [
        record
        for record in records
        if int(record["response"].get("anthropic_cache_read_input_tokens") or 0) > 0
    ]
    route_response_ok_count = sum(1 for record in records if _route_response_ok(record))
    all_route_responses_ok = bool(records) and route_response_ok_count == len(records)
    required_route_hit_case_results = _required_route_hit_case_results(records)
    all_required_route_hits_observed = all(
        bool(result.get("hit_observed"))
        for result in required_route_hit_case_results.values()
    )
    last_counters = records[-1]["status_after"].get("counters", {}) if records else {}
    summary = {
        "schema_version": "b2.compat_route_automatic_prefix_reuse.summary.v1",
        "run_id": actual_run_id,
        "timestamp_utc": _now_iso_utc(),
        "ledger": str(ledger_path),
        "model_id": model_id,
        "model_gb": model_gb,
        "sample_count": len(records),
        "openai_cached_token_hit_count": len(openai_hits),
        "anthropic_cache_read_hit_count": len(anthropic_hits),
        "route_response_ok_count": route_response_ok_count,
        "all_route_responses_ok": all_route_responses_ok,
        "required_route_hit_cases": B2_COMPAT_REQUIRED_HIT_CASES,
        "required_route_hit_case_results": required_route_hit_case_results,
        "all_required_route_hits_observed": all_required_route_hits_observed,
        "openai_cached_tokens": (
            int(openai_hits[-1]["response"]["openai_cached_tokens"])
            if openai_hits
            else None
        ),
        "anthropic_cache_read_input_tokens": (
            int(anthropic_hits[-1]["response"]["anthropic_cache_read_input_tokens"])
            if anthropic_hits
            else None
        ),
        "hits_total": int(last_counters.get("hits", 0)),
        "misses_total": int(last_counters.get("misses", 0)),
        "trim_bypasses_total": int(last_counters.get("trim_bypasses", 0)),
        "trim_evictions_total": int(last_counters.get("trim_evictions", 0)),
        "drops_total": int(last_counters.get("drops", 0)),
        "rejects_total": int(last_counters.get("rejects", 0)),
        "expirations_total": int(last_counters.get("expirations", 0)),
        "load_ok": bool(load.ok),
        "cleanup_unload_ok": bool(cleanup.ok if cleanup is not None else False),
        "verdict": _route_hit_verdict(
            load_ok=bool(load.ok),
            cleanup_unload_ok=bool(cleanup.ok if cleanup is not None else False),
            all_route_responses_ok=all_route_responses_ok,
            all_required_route_hits_observed=all_required_route_hits_observed,
            openai_cached_tokens=(
                int(openai_hits[-1]["response"]["openai_cached_tokens"])
                if openai_hits
                else None
            ),
            anthropic_cache_read_input_tokens=(
                int(anthropic_hits[-1]["response"]["anthropic_cache_read_input_tokens"])
                if anthropic_hits
                else None
            ),
            drops_total=int(last_counters.get("drops", 0)),
            rejects_total=int(last_counters.get("rejects", 0)),
            expirations_total=int(last_counters.get("expirations", 0)),
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
    compat = subparsers.add_parser("compat-route-hit")
    compat.add_argument("--model", default=DEFAULT_MODEL)
    compat.add_argument("--model-gb", type=float, default=DEFAULT_MODEL_GB)
    compat.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    compat.add_argument(
        "--max-resident-bytes",
        type=int,
        default=DEFAULT_MAX_RESIDENT_BYTES,
    )
    compat.add_argument("--run-id", default=None)
    auto_audit = subparsers.add_parser("audit-auto-prefix-ledger")
    auto_audit.add_argument("--ledger", type=Path, action="append", required=True)
    audit = subparsers.add_parser("audit-compat-route-ledger")
    audit.add_argument("--ledger", type=Path, action="append", required=True)
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
    if args.command == "compat-route-hit":
        summary = run_compat_route_hit_probe(
            model_id=args.model,
            model_gb=args.model_gb,
            output_dir=args.output_dir,
            max_resident_bytes=args.max_resident_bytes,
            run_id=args.run_id,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary.get("verdict") == "passed" else 1
    if args.command == "audit-auto-prefix-ledger":
        audits = [audit_auto_prefix_ledger(path) for path in args.ledger]
        payload: dict[str, Any] | list[dict[str, Any]]
        payload = audits[0] if len(audits) == 1 else audits
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if all(audit.get("verdict") == "passed" for audit in audits) else 1
    if args.command == "audit-compat-route-ledger":
        audits = [audit_compat_route_ledger(path) for path in args.ledger]
        payload: dict[str, Any] | list[dict[str, Any]]
        payload = audits[0] if len(audits) == 1 else audits
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if all(audit.get("verdict") == "passed" for audit in audits) else 1
    raise ValueError(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
