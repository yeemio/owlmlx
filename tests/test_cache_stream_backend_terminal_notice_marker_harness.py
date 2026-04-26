from __future__ import annotations

from owlmlx.cache_stream_backend_terminal_notice_marker_harness import (
    run_cache_stream_backend_terminal_notice_marker_harness,
)


def test_cache_stream_backend_terminal_notice_marker_harness_observes_boundary() -> None:
    result = run_cache_stream_backend_terminal_notice_marker_harness()

    assert result.backend_terminal_notice_marker_boundary_visible is True
    assert result.notice_marker_status == "backend_terminal_notice_marker_boundary_visible"
    assert result.second_stream_blocked_before_terminal_window is True
    assert (
        result.second_stream_request_written_before_first_terminal_notice_marker_detected
        is True
    )
    assert result.second_stream_request_written_before_first_terminal_event_consumed is True
    assert result.terminal_window_ms >= 100
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")
