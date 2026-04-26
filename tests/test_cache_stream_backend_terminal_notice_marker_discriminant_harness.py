from __future__ import annotations

from owlmlx.cache_stream_backend_terminal_notice_marker_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_marker_discriminant_harness,
)


def test_cache_stream_backend_terminal_notice_marker_discriminant_harness_observes_boundary() -> None:
    result = run_cache_stream_backend_terminal_notice_marker_discriminant_harness()

    assert result.backend_terminal_notice_marker_discriminant_boundary_visible is True
    assert (
        result.notice_marker_discriminant_status
        == "backend_terminal_notice_marker_discriminant_boundary_visible"
    )
    assert (
        result.second_stream_request_written_before_first_terminal_notice_marker_discriminant_detected
        is True
    )
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")
