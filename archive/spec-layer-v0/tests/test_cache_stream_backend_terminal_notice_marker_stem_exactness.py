from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_marker_prefix_exactness import (
    CacheStreamBackendTerminalNoticeMarkerPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_stem_exactness import (
    build_cache_stream_backend_terminal_notice_marker_stem_exactness,
    cache_stream_backend_terminal_notice_marker_stem_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_stem_harness import (
    CacheStreamBackendTerminalNoticeMarkerStemHarnessResult,
)


def test_cache_stream_backend_terminal_notice_marker_stem_exactness_defaults_unresolved() -> None:
    payload = cache_stream_backend_terminal_notice_marker_stem_exactness_to_dict(
        build_cache_stream_backend_terminal_notice_marker_stem_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_marker_stem_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_marker_stem_unresolved"
    )


def test_cache_stream_backend_terminal_notice_marker_stem_exactness_narrows_to_terminal_notice_marker_discriminant_dependency() -> None:
    marker_prefix_exactness = CacheStreamBackendTerminalNoticeMarkerPrefixExactness(
        backend_terminal_notice_marker_exactness=object(),  # type: ignore[arg-type]
        status="partial",
        exactness_rung="stream_backend_terminal_notice_marker_prefix_exact",
        verdict="backend_terminal_notice_marker_prefix_dependency_narrowed",
        notice_marker_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_marker_prefix_detection_visible",
        exchange_boundary="backend_terminal_notice_marker_stem_detected_before_notice_marker_prefix_detection",
        next_active_dependency="backend_terminal_notice_marker_stem_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_stem_detection",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal notice marker stem now blocks more exactly",
        recommended_next_step="freeze backend terminal notice marker stem seam",
    )
    harness = CacheStreamBackendTerminalNoticeMarkerStemHarnessResult(
        backend_terminal_notice_marker_stem_boundary_visible=True,
        notice_marker_stem_status="backend_terminal_notice_marker_stem_boundary_visible",
        second_stream_blocked_before_terminal_window=True,
        second_stream_request_written_before_first_terminal_notice_marker_stem_detected=True,
        second_stream_request_written_before_first_terminal_event_consumed=True,
        terminal_window_ms=180,
        first_stream_events=("token", "done"),
        second_stream_events=("token", "done"),
    )

    payload = cache_stream_backend_terminal_notice_marker_stem_exactness_to_dict(
        build_cache_stream_backend_terminal_notice_marker_stem_exactness(
            backend_terminal_notice_marker_prefix_exactness=marker_prefix_exactness,
            backend_terminal_notice_marker_stem_harness=harness,
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_marker_stem_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_marker_stem_dependency_narrowed"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_marker_discriminant_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_discriminant_detection"
    )


def test_cache_stream_backend_terminal_notice_marker_stem_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_stream_backend_terminal_notice_marker_stem_exactness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
