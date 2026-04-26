from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryHarnessResult,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_defaults_unresolved() -> None:
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness()
        )
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_unresolved"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_stays_blocked_at_first_unique_boundary() -> None:
    marker_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_marker_stem_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_stem_dependency_narrowed",
            leading_discriminator_marker_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_discriminant_detected_before_notice_leading_discriminator_marker_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker first unique boundary seam",
        )
    )
    harness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryHarnessResult(
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible=True,
            leading_discriminator_marker_first_unique_boundary_status="backend_terminal_notice_leading_discriminator_marker_discriminant_is_first_unique_boundary_visible",
            shared_non_unique_prefix='{"ok": true, "terminal_notice',
            first_unique_boundary_prefix='{"ok": true, "terminal_notice_',
            earlier_prefix_collides_with_old_notice_record=True,
        )
    )

    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                    marker_discriminant_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness=(
                    harness
                ),
            )
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency_still_blocked"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.py",
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
