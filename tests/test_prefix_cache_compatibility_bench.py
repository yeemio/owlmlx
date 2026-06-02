"""Focused tests for the B-2 prefix-cache compatibility bench helpers."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.bench.prefix_cache_compatibility import audit_auto_prefix_ledger
from scripts.bench.prefix_cache_compatibility import audit_compat_route_ledger
from scripts.bench.prefix_cache_compatibility import main
from scripts.bench.prefix_cache_compatibility import _auto_prefix_hit_verdict
from scripts.bench.prefix_cache_compatibility import _anthropic_cache_read_tokens
from scripts.bench.prefix_cache_compatibility import _openai_cached_tokens
from scripts.bench.prefix_cache_compatibility import _required_route_hit_case_results
from scripts.bench.prefix_cache_compatibility import _route_hit_verdict
from scripts.bench.prefix_cache_compatibility import _route_response_ok


def _write_jsonl(path: Path, *records: dict[str, object]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _compat_route_record(
    *,
    case: str,
    surface: str,
    sample_index: int,
    openai_cached_tokens: int | None = None,
    anthropic_cache_read_input_tokens: int | None = None,
    status_code: int = 200,
    content_type: str = "text/event-stream; charset=utf-8",
    drops: int = 0,
    rejects: int = 0,
    expirations: int = 0,
) -> dict[str, object]:
    return {
        "schema_version": "b2.compat_route_automatic_prefix_reuse.v1",
        "run_id": "test-run",
        "case": case,
        "sample_index": sample_index,
        "surface": surface,
        "response": {
            "status_code": status_code,
            "content_type": content_type,
            "openai_cached_tokens": openai_cached_tokens,
            "anthropic_cache_read_input_tokens": anthropic_cache_read_input_tokens,
        },
        "status_after": {
            "counters": {
                "drops": drops,
                "rejects": rejects,
                "expirations": expirations,
            }
        },
    }


def _auto_prefix_record(
    *,
    case: str,
    sample_index: int,
    generation_ok: bool = True,
    cache_decision: str = "new",
    cache_reason_code: str = "session_cache_miss",
    cached_prompt_tokens: int = 0,
    drops: int = 0,
    rejects: int = 0,
    expirations: int = 0,
    bypass_reason_code: str | None = None,
) -> dict[str, object]:
    last_bypass_event: dict[str, object] | None = None
    if bypass_reason_code is not None:
        last_bypass_event = {
            "reason_code": bypass_reason_code,
            "cache_object_id": sample_index,
            "time_s": float(sample_index),
        }
    return {
        "schema_version": "b2.automatic_prefix_reuse.v1",
        "run_id": "test-run",
        "case": case,
        "sample_index": sample_index,
        "generation": {"ok": generation_ok},
        "session_kv_cache": {
            "cache_decision": cache_decision,
            "cache_reason_code": cache_reason_code,
            "cached_prompt_tokens": cached_prompt_tokens,
        },
        "status_after": {
            "counters": {
                "drops": drops,
                "rejects": rejects,
                "expirations": expirations,
            },
            "last_bypass_event": last_bypass_event,
        },
    }


def test_auto_prefix_hit_verdict_accepts_ineligible_reason_without_terminal_fallback() -> None:
    assert (
        _auto_prefix_hit_verdict(
            load_ok=True,
            cleanup_unload_ok=True,
            usable_hit_count=1,
            terminal_fallback_count=0,
            auto_prefix_ineligible_count=1,
            all_generations_ok=True,
            drops_total=0,
        )
        == "passed"
    )


def test_auto_prefix_hit_verdict_fails_without_a_real_hit() -> None:
    assert (
        _auto_prefix_hit_verdict(
            load_ok=True,
            cleanup_unload_ok=True,
            usable_hit_count=0,
            terminal_fallback_count=1,
            auto_prefix_ineligible_count=1,
            all_generations_ok=True,
            drops_total=0,
        )
        == "failed"
    )


def test_route_hit_verdict_requires_both_compat_surfaces() -> None:
    assert (
        _route_hit_verdict(
            load_ok=True,
            cleanup_unload_ok=True,
            all_route_responses_ok=True,
            all_required_route_hits_observed=True,
            openai_cached_tokens=5,
            anthropic_cache_read_input_tokens=5,
            drops_total=0,
            rejects_total=0,
            expirations_total=0,
        )
        == "passed"
    )
    assert (
        _route_hit_verdict(
            load_ok=True,
            cleanup_unload_ok=True,
            all_route_responses_ok=True,
            all_required_route_hits_observed=True,
            openai_cached_tokens=5,
            anthropic_cache_read_input_tokens=None,
            drops_total=0,
            rejects_total=0,
            expirations_total=0,
        )
        == "failed"
    )
    assert (
        _route_hit_verdict(
            load_ok=True,
            cleanup_unload_ok=True,
            all_route_responses_ok=False,
            all_required_route_hits_observed=True,
            openai_cached_tokens=5,
            anthropic_cache_read_input_tokens=5,
            drops_total=0,
            rejects_total=0,
            expirations_total=0,
        )
        == "failed"
    )
    assert (
        _route_hit_verdict(
            load_ok=True,
            cleanup_unload_ok=True,
            all_route_responses_ok=True,
            all_required_route_hits_observed=False,
            openai_cached_tokens=5,
            anthropic_cache_read_input_tokens=5,
            drops_total=0,
            rejects_total=0,
            expirations_total=0,
        )
        == "failed"
    )


def test_route_response_ok_requires_http_200_and_sse_content_type() -> None:
    assert _route_response_ok(
        {"response": {"status_code": 200, "content_type": "text/event-stream; charset=utf-8"}}
    )
    assert not _route_response_ok(
        {"response": {"status_code": 500, "content_type": "text/event-stream"}}
    )
    assert not _route_response_ok(
        {"response": {"status_code": 200, "content_type": "application/json"}}
    )


def test_required_route_hit_cases_require_strict_prefix_extension_hits() -> None:
    records = [
        {
            "case": "openai_prefix_seed",
            "surface": "openai_chat_completions_sse",
            "response": {
                "status_code": 200,
                "content_type": "text/event-stream",
                "openai_cached_tokens": 7,
            },
        },
        {
            "case": "openai_strict_prefix_extension",
            "surface": "openai_chat_completions_sse",
            "response": {
                "status_code": 200,
                "content_type": "text/event-stream",
                "openai_cached_tokens": 0,
            },
        },
        {
            "case": "anthropic_prefix_seed",
            "surface": "anthropic_messages_sse",
            "response": {
                "status_code": 200,
                "content_type": "text/event-stream",
                "anthropic_cache_read_input_tokens": 9,
            },
        },
        {
            "case": "anthropic_strict_prefix_extension",
            "surface": "anthropic_messages_sse",
            "response": {
                "status_code": 200,
                "content_type": "text/event-stream",
                "anthropic_cache_read_input_tokens": 0,
            },
        },
    ]

    results = _required_route_hit_case_results(records)

    assert results["openai_chat_completions_sse"]["required_case"] == (
        "openai_strict_prefix_extension"
    )
    assert results["openai_chat_completions_sse"]["max_cached_tokens"] == 0
    assert results["openai_chat_completions_sse"]["hit_observed"] is False
    assert results["anthropic_messages_sse"]["required_case"] == (
        "anthropic_strict_prefix_extension"
    )
    assert results["anthropic_messages_sse"]["max_cached_tokens"] == 0
    assert results["anthropic_messages_sse"]["hit_observed"] is False

    records[1]["response"]["openai_cached_tokens"] = 11
    records[3]["response"]["anthropic_cache_read_input_tokens"] = 13

    passing_results = _required_route_hit_case_results(records)

    assert passing_results["openai_chat_completions_sse"]["max_cached_tokens"] == 11
    assert passing_results["openai_chat_completions_sse"]["hit_observed"] is True
    assert passing_results["anthropic_messages_sse"]["max_cached_tokens"] == 13
    assert passing_results["anthropic_messages_sse"]["hit_observed"] is True


def test_compat_route_sse_cached_token_parsers() -> None:
    openai_sse = (
        "data: {\"choices\":[],\"usage\":{\"prompt_tokens_details\":{\"cached_tokens\":7}}}\n\n"
        "data: [DONE]\n\n"
    )
    anthropic_sse = (
        "event: message_delta\n"
        "data: {\"type\":\"message_delta\",\"usage\":{\"cache_read_input_tokens\":9}}\n\n"
    )

    assert _openai_cached_tokens(openai_sse) == 7
    assert _anthropic_cache_read_tokens(anthropic_sse) == 9


def test_audit_compat_route_ledger_accepts_strict_prefix_hits(tmp_path) -> None:
    ledger = tmp_path / "compat-route.jsonl"
    _write_jsonl(
        ledger,
        _compat_route_record(
            case="openai_prefix_seed",
            surface="openai_chat_completions_sse",
            sample_index=1,
            openai_cached_tokens=0,
        ),
        _compat_route_record(
            case="openai_strict_prefix_extension",
            surface="openai_chat_completions_sse",
            sample_index=2,
            openai_cached_tokens=12,
        ),
        _compat_route_record(
            case="anthropic_prefix_seed",
            surface="anthropic_messages_sse",
            sample_index=3,
            anthropic_cache_read_input_tokens=0,
        ),
        _compat_route_record(
            case="anthropic_strict_prefix_extension",
            surface="anthropic_messages_sse",
            sample_index=4,
            anthropic_cache_read_input_tokens=13,
        ),
    )

    audit = audit_compat_route_ledger(ledger)

    assert audit["verdict"] == "passed"
    assert audit["all_route_responses_ok"] is True
    assert audit["all_required_route_hits_observed"] is True
    assert audit["failure_reasons"] == []


def test_audit_compat_route_ledger_rejects_seed_only_hits(tmp_path) -> None:
    ledger = tmp_path / "compat-route.jsonl"
    _write_jsonl(
        ledger,
        _compat_route_record(
            case="openai_prefix_seed",
            surface="openai_chat_completions_sse",
            sample_index=1,
            openai_cached_tokens=12,
        ),
        _compat_route_record(
            case="openai_strict_prefix_extension",
            surface="openai_chat_completions_sse",
            sample_index=2,
            openai_cached_tokens=0,
        ),
        _compat_route_record(
            case="anthropic_prefix_seed",
            surface="anthropic_messages_sse",
            sample_index=3,
            anthropic_cache_read_input_tokens=13,
        ),
        _compat_route_record(
            case="anthropic_strict_prefix_extension",
            surface="anthropic_messages_sse",
            sample_index=4,
            anthropic_cache_read_input_tokens=0,
        ),
    )

    audit = audit_compat_route_ledger(ledger)

    assert audit["verdict"] == "failed"
    assert audit["all_route_responses_ok"] is True
    assert audit["all_required_route_hits_observed"] is False
    assert "required_strict_prefix_extension_hit_missing" in audit["failure_reasons"]


def test_audit_compat_route_ledger_cli_accepts_temp_ledgers(tmp_path, capsys) -> None:
    ledger = tmp_path / "compat-route.jsonl"
    _write_jsonl(
        ledger,
        _compat_route_record(
            case="openai_prefix_seed",
            surface="openai_chat_completions_sse",
            sample_index=1,
            openai_cached_tokens=0,
        ),
        _compat_route_record(
            case="openai_strict_prefix_extension",
            surface="openai_chat_completions_sse",
            sample_index=2,
            openai_cached_tokens=12,
        ),
        _compat_route_record(
            case="anthropic_prefix_seed",
            surface="anthropic_messages_sse",
            sample_index=3,
            anthropic_cache_read_input_tokens=0,
        ),
        _compat_route_record(
            case="anthropic_strict_prefix_extension",
            surface="anthropic_messages_sse",
            sample_index=4,
            anthropic_cache_read_input_tokens=13,
        ),
    )

    code = main(
        [
            "audit-compat-route-ledger",
            "--ledger",
            str(ledger),
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "all_required_route_hits_observed" in captured.out
    assert "required_strict_prefix_extension_hit_missing" not in captured.out


def test_audit_auto_prefix_ledger_accepts_strict_prefix_hit_and_fallback(tmp_path) -> None:
    ledger = tmp_path / "auto-prefix.jsonl"
    _write_jsonl(
        ledger,
        _auto_prefix_record(
            case="prefix_seed",
            sample_index=1,
        ),
        _auto_prefix_record(
            case="strict_prefix_extension",
            sample_index=2,
            cache_decision="reuse",
            cache_reason_code="session_cache_hit",
            cached_prompt_tokens=24,
        ),
        _auto_prefix_record(
            case="reject_seed",
            sample_index=3,
            cache_reason_code="auto_prefix_ineligible_not_token_prefix",
            bypass_reason_code="auto_prefix_ineligible_not_token_prefix",
        ),
    )

    audit = audit_auto_prefix_ledger(ledger)

    assert audit["verdict"] == "passed"
    assert audit["strict_prefix_hit_observed"] is True
    assert audit["strict_prefix_cached_tokens"] == 24
    assert audit["auto_prefix_ineligible_count"] == 1
    assert audit["failure_reasons"] == []


def test_audit_auto_prefix_ledger_rejects_old_trim_blocker(tmp_path) -> None:
    ledger = tmp_path / "auto-prefix.jsonl"
    _write_jsonl(
        ledger,
        _auto_prefix_record(
            case="prefix_seed",
            sample_index=1,
        ),
        _auto_prefix_record(
            case="strict_prefix_extension",
            sample_index=2,
            cache_reason_code="auto_prefix_completion_trim_unavailable",
            bypass_reason_code="auto_prefix_completion_trim_unavailable",
        ),
        _auto_prefix_record(
            case="reject_seed",
            sample_index=3,
            cache_reason_code="auto_prefix_ineligible_not_token_prefix",
            bypass_reason_code="auto_prefix_ineligible_not_token_prefix",
        ),
    )

    audit = audit_auto_prefix_ledger(ledger)

    assert audit["verdict"] == "failed"
    assert audit["strict_prefix_hit_observed"] is False
    assert "required_strict_prefix_reuse_hit_missing" in audit["failure_reasons"]
    assert "auto_prefix_completion_trim_unavailable" in audit["failure_reasons"]


def test_audit_auto_prefix_ledger_cli_accepts_temp_hit(capsys, tmp_path) -> None:
    ledger = tmp_path / "auto-prefix.jsonl"
    _write_jsonl(
        ledger,
        _auto_prefix_record(
            case="prefix_seed",
            sample_index=1,
        ),
        _auto_prefix_record(
            case="strict_prefix_extension",
            sample_index=2,
            cache_decision="reuse",
            cache_reason_code="session_cache_hit",
            cached_prompt_tokens=24,
        ),
        _auto_prefix_record(
            case="reject_seed",
            sample_index=3,
            cache_reason_code="auto_prefix_ineligible_not_token_prefix",
            bypass_reason_code="auto_prefix_ineligible_not_token_prefix",
        ),
    )

    code = main(
        [
            "audit-auto-prefix-ledger",
            "--ledger",
            str(ledger),
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "strict_prefix_hit_observed" in captured.out
    assert "auto_prefix_completion_trim_unavailable" not in captured.out
