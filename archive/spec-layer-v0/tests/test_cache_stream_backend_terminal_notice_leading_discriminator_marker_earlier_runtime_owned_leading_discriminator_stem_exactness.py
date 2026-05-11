from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemHarnessResult,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness_defaults_unresolved() -> None:
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness()
        )
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_unresolved"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness_marks_narrowing() -> None:
    earlier_runtime_owned_leading_discriminator_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=object(),  # type: ignore[arg-type]
                status="partial",
                exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exact",
                verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency_still_blocked",
                earlier_runtime_owned_discriminator_first_unique_boundary_status="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_is_first_honest_unique_boundary_visible",
                exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_is_first_honest_unique_boundary_visible",
                next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency",
                next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
                preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
                residual_blocker="earlier runtime-owned discriminator discriminant remains the first honest unique boundary",
                recommended_next_step="introduce a new earlier runtime-owned leading discriminator if one can be made honest",
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_introduced",
            earlier_runtime_owned_leading_discriminator_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="one new earlier runtime-owned leading discriminator record now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned leading discriminator seam",
        )
    )
    earlier_runtime_owned_leading_discriminator_prefix_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
                earlier_runtime_owned_leading_discriminator_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency_narrowed",
            earlier_runtime_owned_leading_discriminator_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier runtime-owned leading discriminator prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned leading discriminator stem seam",
        )
    )
    harness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemHarnessResult(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_boundary_visible=True,
            earlier_runtime_owned_leading_discriminator_stem_status="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_boundary_visible",
            second_stream_blocked_before_terminal_window=True,
            second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected=True,
            second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected=True,
            second_stream_request_written_before_first_terminal_event_consumed=True,
            terminal_window_ms=180,
            first_stream_events=("token", "done"),
            second_stream_events=("token", "done"),
        )
    )

    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness=(
                    earlier_runtime_owned_leading_discriminator_prefix_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness=(
                    harness
                ),
            )
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_dependency_narrowed"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness.py",
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
