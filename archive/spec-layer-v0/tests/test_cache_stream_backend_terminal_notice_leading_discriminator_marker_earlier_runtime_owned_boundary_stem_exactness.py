from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemHarnessResult,
)


def _prefix_exactness() -> (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness
):
    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=object(),  # type: ignore[arg-type]
        status="partial",
        exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exact",
        verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency_narrowed",
        earlier_runtime_owned_boundary_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection_visible",
        exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection",
        next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="earlier runtime-owned boundary prefix now blocks more exactly",
        recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned boundary stem seam",
    )


def test_boundary_stem_exactness_defaults_when_prefix_not_exact() -> None:
    unresolved = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness()
    )

    assert (
        unresolved.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_unresolved"
    )
    assert (
        unresolved.verdict
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency_still_blocked"
    )
    assert (
        unresolved.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency"
    )


def test_boundary_stem_exactness_narrows_when_harness_visible() -> None:
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=_prefix_exactness(),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemHarnessResult(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible=True,
                earlier_runtime_owned_boundary_stem_status="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible",
                second_stream_blocked_before_terminal_window=True,
                second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected=True,
                second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected=True,
                second_stream_request_written_before_first_terminal_event_consumed=True,
                terminal_window_ms=180,
                first_stream_events=("token", "done"),
                second_stream_events=("token", "done"),
            ),
        )
    )

    assert (
        exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exact"
    )
    assert (
        exactness.verdict
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency_narrowed"
    )
    assert (
        exactness.exchange_boundary
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection"
    )
    assert (
        exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency"
    )
    assert (
        exactness.next_active_dependency_status
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection"
    )
