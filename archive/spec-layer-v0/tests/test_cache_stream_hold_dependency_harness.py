from __future__ import annotations

from owlmlx.cache_stream_hold_dependency_harness import (
    run_cache_stream_hold_dependency_harness,
)


def test_cache_stream_hold_dependency_harness_observes_narrowed_boundary() -> None:
    result = run_cache_stream_hold_dependency_harness()

    assert result.hold_dependency_narrowed is True
    assert result.hold_verdict == "stream_hold_dependency_narrowed"
    assert (
        result.hold_status
        == "stream_gate_release_decoupled_from_consumer_completion_visible"
    )
    assert (
        result.gate_release_boundary
        == "backend_stream_iterator_completion_before_consumer_drain"
    )
    assert result.second_stream_started_before_first_consumer_completed is True
    assert result.max_concurrent == 1
    assert result.queue_policy == "ticketed_fifo"
    assert result.gate_total_served == 2
    assert result.gate_total_queued == 2
    assert result.preserved_post_claim_invariants == (
        "max_concurrent_1_after_gate_claim",
        "ticketed_fifo_after_gate_claim",
        "serial_safety_validated_only_after_gate_claim",
    )
    assert result.first_stream_events[0] == "token"
    assert result.first_stream_events[-1] == "done"
    assert result.second_stream_events[0] == "token"
    assert result.second_stream_events[-1] == "done"
