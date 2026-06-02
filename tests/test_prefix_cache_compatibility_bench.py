"""Focused tests for the B-2 prefix-cache compatibility bench helpers."""

from __future__ import annotations

from scripts.bench.prefix_cache_compatibility import _auto_prefix_hit_verdict
from scripts.bench.prefix_cache_compatibility import _anthropic_cache_read_tokens
from scripts.bench.prefix_cache_compatibility import _openai_cached_tokens
from scripts.bench.prefix_cache_compatibility import _route_hit_verdict


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
            openai_cached_tokens=5,
            anthropic_cache_read_input_tokens=None,
            drops_total=0,
            rejects_total=0,
            expirations_total=0,
        )
        == "failed"
    )


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
