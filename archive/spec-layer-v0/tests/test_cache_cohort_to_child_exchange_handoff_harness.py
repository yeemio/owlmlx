from __future__ import annotations

from owlmlx.cache_cohort_to_child_exchange_handoff_harness import (
    run_cache_cohort_to_child_exchange_handoff_harness,
)


def test_cache_cohort_to_child_exchange_handoff_harness_observes_main_path_handoff() -> None:
    result = run_cache_cohort_to_child_exchange_handoff_harness()

    assert result.cohort_handoff_visible is True
    assert (
        result.handoff_status
        == "cohort_handed_off_to_aggregated_child_exchange_visible"
    )
    assert result.child_exchange_mode == "aggregated_non_stream_child_exchange_visible"
    assert result.aggregated_batch_count >= 1
    assert result.aggregated_request_count >= 2
    assert result.max_aggregated_batch_size >= 2
    assert result.gate_total_served == 2
    assert result.gate_total_queued == 2
    assert result.max_concurrent == 1
    assert result.queue_discipline == "serial"
    assert result.handoff_request_count >= 2
    assert result.stream_secondary_status == "stream_session_holds_gate_until_completion"
    assert result.texts == ("handoff-a :: child", "handoff-b :: child")
