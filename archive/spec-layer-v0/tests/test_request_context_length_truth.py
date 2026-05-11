from __future__ import annotations

from pathlib import Path

from owlmlx.context_concurrency import HIGH_CONTEXT_THRESHOLD_TOKENS
from owlmlx.request_context_length_truth import (
    build_request_context_length_truth,
    request_context_length_truth_to_dict,
)


def test_request_context_length_truth_classifies_low_token_count_as_non_high_context() -> None:
    payload = request_context_length_truth_to_dict(
        build_request_context_length_truth(context_tokens=HIGH_CONTEXT_THRESHOLD_TOKENS)
    )

    assert payload["contract"]["surface"] == "owlmlx.request_context_length_truth"
    assert payload["summary"]["classification"] == "non_high_context"
    assert payload["summary"]["confidence"] == "high"
    assert payload["classification"]["reason_code"] == (
        "explicit_context_tokens_at_or_below_high_context_threshold"
    )
    assert payload["source"]["tokenizer_invoked"] is False
    assert payload["source"]["exact_token_accounting"] is True


def test_request_context_length_truth_classifies_high_token_count_as_high_context() -> None:
    payload = request_context_length_truth_to_dict(
        build_request_context_length_truth(context_tokens=HIGH_CONTEXT_THRESHOLD_TOKENS + 1)
    )

    assert payload["summary"]["classification"] == "high_context"
    assert payload["classification"]["reason_code"] == (
        "explicit_context_tokens_above_high_context_threshold"
    )
    assert payload["source"]["gate_entry"]["max_concurrency"] == 1


def test_request_context_length_truth_keeps_missing_context_unknown() -> None:
    payload = request_context_length_truth_to_dict(build_request_context_length_truth())

    assert payload["summary"]["classification"] == "unknown"
    assert payload["summary"]["confidence"] == "low"
    assert payload["source"]["source_status"] == "insufficient_signal"
    assert payload["missing_signals"][0]["signal"] == "runtime_visible_context_tokens"


def test_request_context_length_truth_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "request_context_length_truth.py")
        .read_text()
    )
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
