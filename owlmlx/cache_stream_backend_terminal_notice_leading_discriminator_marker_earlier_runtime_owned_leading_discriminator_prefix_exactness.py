"""Runtime-owned exactness for earlier runtime-owned leading-discriminator prefix narrowing."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness:
    """Exact truth for the earlier runtime-owned leading-discriminator prefix seam."""

    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    earlier_runtime_owned_leading_discriminator_prefix_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness(
    *,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness
        | None
    ) = None,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixHarnessResult
        | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness:
    """Build exact truth for the earlier runtime-owned leading-discriminator prefix seam."""

    earlier_runtime_owned_leading_discriminator_exactness = (
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_unresolved"
    )
    verdict = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency_still_blocked"
    )
    earlier_runtime_owned_leading_discriminator_prefix_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency"
    )
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator marker earlier runtime-owned leading-discriminator-prefix exactness is not yet frozen because earlier runtime-owned leading-discriminator truth is not exact"
    )
    recommended_next_step = (
        "freeze backend terminal-notice leading-discriminator marker earlier-runtime-owned-leading-discriminator truth before reducing the remaining prefix seam inside that runtime-owned record"
    )

    if (
        earlier_runtime_owned_leading_discriminator_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exact"
        and earlier_runtime_owned_leading_discriminator_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency"
    ):
        exactness_rung = (
            "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exact"
        )
        earlier_runtime_owned_leading_discriminator_prefix_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_visible"
        )
        exchange_boundary = (
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_remains_current_exact_boundary"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection"
        )
        preserved_non_stream_handoff_status = (
            earlier_runtime_owned_leading_discriminator_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx now owns one new earlier runtime-owned terminal-notice leading-discriminator record ahead of the newer runtime-owned discriminator record on this path, but the live backend stream exchange still owns the serial boundary until child stdout reaches full earlier-runtime-owned-leading-discriminator detection, so that runtime-owned leading-discriminator detection remains the current exact seam until an earlier unique prefix boundary is visibly frozen"
        )
        recommended_next_step = (
            "freeze whether backend-terminal notice leading-discriminator marker earlier-runtime-owned-leading-discriminator prefix detection is already the next exact stream seam without inflating this transport-owned narrowing into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness
            is not None
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_boundary_visible
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency_narrowed"
            )
            earlier_runtime_owned_leading_discriminator_prefix_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than full earlier-runtime-owned-leading-discriminator detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches full earlier-runtime-owned-leading-discriminator detection, but it still cannot enter before child stdout reaches the earlier runtime-owned leading-discriminator prefix on that same internal record, so backend-terminal notice leading-discriminator marker earlier-runtime-owned-leading-discriminator prefix detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator marker earlier-runtime-owned-leading-discriminator prefix detection as the current exact stream dependency without inflating this runtime-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
            earlier_runtime_owned_leading_discriminator_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        earlier_runtime_owned_leading_discriminator_prefix_status=(
            earlier_runtime_owned_leading_discriminator_prefix_status
        ),
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness,
) -> dict[str, object]:
    """Serialize earlier runtime-owned leading-discriminator prefix exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix",
                "next_active_dependency",
                "preserved_non_stream_handoff",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "verdict": exactness.verdict,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix": {
            "earlier_runtime_owned_leading_discriminator_prefix_status": (
                exactness.earlier_runtime_owned_leading_discriminator_prefix_status
            ),
            "exchange_boundary": exactness.exchange_boundary,
        },
        "next_active_dependency": {
            "dependency": exactness.next_active_dependency,
            "status": exactness.next_active_dependency_status,
        },
        "preserved_non_stream_handoff": {
            "status": exactness.preserved_non_stream_handoff_status,
        },
    }
