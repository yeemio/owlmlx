from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryHarnessResult,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_defaults_unresolved() -> None:
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness()
        )
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_unresolved"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_stays_blocked_at_first_honest_unique_boundary() -> None:
    stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency_narrowed",
            earlier_runtime_owned_boundary_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker earlier runtime-owned boundary stem now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned boundary first-unique-boundary seam",
        )
    )
    harness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryHarnessResult(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_visible=True,
            leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_status="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_is_first_honest_unique_boundary_visible",
            shared_non_unique_prefix='{"ok": true, "runtime_owned_terminal_',
            first_honest_unique_boundary_prefix='{"ok": true, "runtime_owned_terminal_b',
            earlier_literal_prefix_is_not_runtime_owned_boundary=True,
        )
    )

    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
                    stem_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness=(
                    harness
                ),
            )
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency_still_blocked"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness.py",
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
