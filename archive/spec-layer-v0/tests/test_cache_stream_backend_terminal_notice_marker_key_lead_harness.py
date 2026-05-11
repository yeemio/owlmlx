from __future__ import annotations

from owlmlx.cache_stream_backend_terminal_notice_marker_key_lead_harness import (
    run_cache_stream_backend_terminal_notice_marker_key_lead_harness,
)


def test_cache_stream_backend_terminal_notice_marker_key_lead_harness_observes_boundary() -> None:
    result = run_cache_stream_backend_terminal_notice_marker_key_lead_harness()

    assert result.backend_terminal_notice_marker_key_lead_boundary_visible is True
    assert (
        result.notice_marker_key_lead_status
        == "backend_terminal_notice_marker_key_lead_boundary_visible"
    )
    assert (
        result.second_stream_blocked_before_terminal_window
        is True
    )
    assert (
        result.second_stream_request_written_after_first_terminal_notice_marker_key_lead_detected
        is True
    )
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")
