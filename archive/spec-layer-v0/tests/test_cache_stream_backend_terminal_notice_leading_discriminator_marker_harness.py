from __future__ import annotations

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_harness,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_harness_observes_boundary() -> None:
    result = run_cache_stream_backend_terminal_notice_leading_discriminator_marker_harness()

    assert (
        result.backend_terminal_notice_leading_discriminator_marker_boundary_visible
        is True
    )
    assert (
        result.leading_discriminator_marker_status
        == "backend_terminal_notice_leading_discriminator_marker_boundary_visible"
    )
    assert result.second_stream_blocked_before_terminal_window is True
    assert (
        result.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_detected
        is True
    )
    assert (
        result.second_stream_request_written_before_first_terminal_notice_leading_discriminator_discriminant_detected
        is True
    )
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")
