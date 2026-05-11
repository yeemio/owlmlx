from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryHarnessResult,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness,
)


def _first_unique_boundary_exactness() -> (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness
):
    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=object(),  # type: ignore[arg-type]
        status="partial",
        exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exact",
        verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency_still_blocked",
        earlier_runtime_owned_boundary_first_unique_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection_visible",
        exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_is_first_honest_unique_boundary_visible",
        next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="earlier-runtime-owned-boundary stem is the first honest unique boundary",
        recommended_next_step="introduce a new earlier runtime-owned boundary",
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness_defaults_unresolved() -> None:
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness()
        )
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_unresolved"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness_introduces_new_boundary() -> None:
    harness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryHarnessResult(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_visible=True,
            earlier_runtime_owned_boundary_earlier_boundary_status="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_visible",
            second_stream_blocked_before_terminal_window=True,
            second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected=True,
            second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected=True,
            second_stream_request_written_before_first_terminal_event_consumed=True,
            terminal_window_ms=180,
            first_stream_events=("token", "done"),
            second_stream_events=("token", "done"),
        )
    )

    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
                    _first_unique_boundary_exactness()
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness=(
                    harness
                ),
            )
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_introduced"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection"
    )
    assert "runtime_owned_terminal_earlier_boundary" in payload["summary"]["residual_blocker"]


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness.py",
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
