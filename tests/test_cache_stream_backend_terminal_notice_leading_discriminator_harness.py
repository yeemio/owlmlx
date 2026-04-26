from __future__ import annotations

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_harness,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_harness_observes_boundary() -> None:
    result = run_cache_stream_backend_terminal_notice_leading_discriminator_harness()

    assert result.backend_terminal_notice_leading_discriminator_boundary_visible is True
    assert (
        result.leading_discriminator_status
        == "backend_terminal_notice_leading_discriminator_boundary_visible"
    )
    assert result.second_stream_blocked_before_terminal_window is True
    assert (
        result.second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected
        is True
    )
    assert (
        result.second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected
        is True
    )
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")
