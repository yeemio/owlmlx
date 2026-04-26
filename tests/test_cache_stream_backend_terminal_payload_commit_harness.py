from __future__ import annotations

from owlmlx.cache_stream_backend_terminal_payload_commit_harness import (
    run_cache_stream_backend_terminal_payload_commit_harness,
)


def test_cache_stream_backend_terminal_payload_commit_harness_observes_payload_commit_boundary() -> None:
    result = run_cache_stream_backend_terminal_payload_commit_harness()

    assert result.backend_terminal_payload_commit_boundary_visible is True
    assert result.payload_commit_status == "backend_terminal_payload_commit_boundary_visible"
    assert result.second_stream_blocked_before_terminal_window is True
    assert result.second_stream_started_before_first_terminal_payload_committed is True
    assert result.second_stream_started_before_first_terminal_event_consumed is True
    assert result.terminal_window_ms >= 100
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")
