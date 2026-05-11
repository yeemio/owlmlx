from __future__ import annotations

from pathlib import Path

from owlmlx.cache_child_exchange_aggregated_dispatch_harness import (
    run_cache_child_exchange_aggregated_dispatch_harness,
)


def test_cache_child_exchange_aggregated_dispatch_harness_exposes_single_exchange_batch() -> None:
    result = run_cache_child_exchange_aggregated_dispatch_harness()

    assert result.aggregated_dispatch_visible is True
    assert result.child_exchange_mode == "aggregated_non_stream_child_exchange_visible"
    assert result.exchange_count == 1
    assert result.batch_size == 2
    assert result.aggregated_request_count == 2
    assert result.max_aggregated_batch_size == 2
    assert result.stream_secondary_status == "stream_session_holds_gate_until_completion"
    assert result.texts == ("child-a :: child", "child-b :: child")


def test_cache_child_exchange_aggregated_dispatch_harness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_child_exchange_aggregated_dispatch_harness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
