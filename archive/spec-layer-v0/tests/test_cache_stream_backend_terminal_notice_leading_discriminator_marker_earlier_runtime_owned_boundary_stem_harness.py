from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness,
)


def test_earlier_runtime_owned_boundary_stem_harness_visible() -> None:
    result = (
        run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness()
    )

    assert (
        result.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible
        is True
    )
    assert (
        result.earlier_runtime_owned_boundary_stem_status
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible"
    )
    assert result.second_stream_blocked_before_terminal_window is True
    assert (
        result.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected
        is True
    )
    assert (
        result.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected
        is True
    )
    assert result.second_stream_request_written_before_first_terminal_event_consumed is True
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")
    assert result.terminal_window_ms == 180
