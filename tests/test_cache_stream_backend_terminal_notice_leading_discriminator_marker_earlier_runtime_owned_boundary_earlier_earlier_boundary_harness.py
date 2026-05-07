from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness_observes_boundary() -> None:
    result = run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness()

    assert (
        result.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_visible
        is True
    )
    assert (
        result.earlier_runtime_owned_boundary_earlier_earlier_boundary_status
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_visible"
    )
    assert result.second_stream_blocked_before_terminal_window is True
    assert (
        result.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected
        is True
    )
    assert (
        result.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected
        is True
    )
    assert (
        result.second_stream_request_written_before_first_terminal_event_consumed
        is True
    )
    assert result.first_stream_events == ("token", "done")
    assert result.second_stream_events == ("token", "done")


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_runner_emits_real_sentinel_first() -> None:
    runner_source = (
        Path(__file__).parents[1]
        / "owlmlx"
        / "runtime"
        / "mlx_lm_runner.py"
    ).read_text()

    stream_done_earlier_earlier = runner_source.index(
        '"action": "stream_runtime_owned_terminal_earlier_earlier_boundary",\n'
        '                        "terminal_action": "stream_done",'
    )
    stream_done_earlier = runner_source.index(
        '"action": "stream_runtime_owned_terminal_earlier_boundary",\n'
        '                        "terminal_action": "stream_done",'
    )
    stream_message_done_earlier_earlier = runner_source.index(
        '"action": "stream_runtime_owned_terminal_earlier_earlier_boundary",\n'
        '                        "terminal_action": "stream_message_done",'
    )
    stream_message_done_earlier = runner_source.index(
        '"action": "stream_runtime_owned_terminal_earlier_boundary",\n'
        '                        "terminal_action": "stream_message_done",'
    )

    assert stream_done_earlier_earlier < stream_done_earlier
    assert stream_message_done_earlier_earlier < stream_message_done_earlier
