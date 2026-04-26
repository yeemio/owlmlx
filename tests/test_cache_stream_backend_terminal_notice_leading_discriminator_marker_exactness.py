from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerHarnessResult,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness_defaults_unresolved() -> None:
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness()
        )
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_unresolved"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness_marks_narrowing() -> None:
    leading_discriminator_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_stem_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_stem_dependency_narrowed",
            leading_discriminator_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_discriminant_detected_before_notice_leading_discriminator_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="leading discriminator discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator discriminant seam",
        )
    )
    harness = CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerHarnessResult(
        backend_terminal_notice_leading_discriminator_marker_boundary_visible=True,
        leading_discriminator_marker_status="backend_terminal_notice_leading_discriminator_marker_boundary_visible",
        second_stream_blocked_before_terminal_window=True,
        second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_detected=True,
        second_stream_request_written_before_first_terminal_notice_leading_discriminator_discriminant_detected=True,
        second_stream_request_written_before_first_terminal_event_consumed=True,
        terminal_window_ms=180,
        first_stream_events=("token", "done"),
        second_stream_events=("token", "done"),
    )

    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness(
                backend_terminal_notice_leading_discriminator_discriminant_exactness=(
                    leading_discriminator_discriminant_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_harness=harness,
            )
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_leading_discriminator_discriminant_dependency_narrowed"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_leading_discriminator_marker_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_detection"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness.py",
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
