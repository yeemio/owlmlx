"""Focused tests for the B-2 prefix-cache compatibility bench helpers."""

from __future__ import annotations

from scripts.bench.prefix_cache_compatibility import _auto_prefix_hit_verdict


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
