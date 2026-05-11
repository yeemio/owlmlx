from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryHarnessResult,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_defaults_unresolved() -> None:
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness()
        )
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_unresolved"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_stays_blocked_at_first_honest_unique_boundary() -> None:
    earlier_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_introduced",
            earlier_runtime_owned_boundary_earlier_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected_before_boundary_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier-boundary record introduced ahead of stem",
            recommended_next_step="freeze whether earlier-boundary detection is the first honest unique boundary on the new earlier-boundary record",
        )
    )
    harness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryHarnessResult(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_visible=True,
            leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_is_first_honest_unique_boundary_visible",
            shared_non_unique_prefix='{"ok": true, "runtime_owned_terminal_',
            first_honest_unique_boundary_prefix='{"ok": true, "runtime_owned_terminal_earlier_b',
            earlier_literal_prefix_is_not_runtime_owned_earlier_boundary=True,
        )
    )

    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
                    earlier_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness=(
                    harness
                ),
            )
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency_still_blocked"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection"
    )
    assert (
        payload["backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary"][
            "exchange_boundary"
        ]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_is_first_honest_unique_boundary_visible"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.py",
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
