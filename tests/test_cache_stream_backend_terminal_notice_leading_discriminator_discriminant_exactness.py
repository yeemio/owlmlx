from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_discriminant_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantHarnessResult,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness_defaults_unresolved() -> None:
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness()
        )
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_discriminant_unresolved"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness_marks_narrowing() -> None:
    leading_discriminator_stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness(
            backend_terminal_notice_leading_discriminator_prefix_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_prefix_dependency_narrowed",
            leading_discriminator_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_stem_detected_before_notice_leading_discriminator_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="leading discriminator stem now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator stem seam",
        )
    )
    harness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantHarnessResult(
            backend_terminal_notice_leading_discriminator_discriminant_boundary_visible=True,
            leading_discriminator_discriminant_status="backend_terminal_notice_leading_discriminator_discriminant_boundary_visible",
            second_stream_blocked_before_terminal_window=True,
            second_stream_request_written_after_first_terminal_notice_leading_discriminator_discriminant_detected=True,
            second_stream_request_written_before_first_terminal_notice_leading_discriminator_stem_detected=True,
            second_stream_request_written_before_first_terminal_event_consumed=True,
            terminal_window_ms=180,
            first_stream_events=("token", "done"),
            second_stream_events=("token", "done"),
        )
    )

    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness(
                backend_terminal_notice_leading_discriminator_stem_exactness=(
                    leading_discriminator_stem_exactness
                ),
                backend_terminal_notice_leading_discriminator_discriminant_harness=(
                    harness
                ),
            )
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_notice_leading_discriminator_discriminant_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_notice_leading_discriminator_stem_dependency_narrowed"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_leading_discriminator_discriminant_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_discriminant_detection"
    )


def test_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness.py",
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
