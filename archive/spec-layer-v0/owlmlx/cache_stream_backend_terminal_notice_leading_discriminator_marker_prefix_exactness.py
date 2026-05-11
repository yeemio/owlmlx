"""Runtime-owned exactness for backend terminal-notice leading-discriminator marker-prefix narrowing."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness:
    """Exact truth for the backend terminal-notice leading-discriminator marker-prefix seam."""

    backend_terminal_notice_leading_discriminator_marker_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    leading_discriminator_marker_prefix_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness(
    *,
    backend_terminal_notice_leading_discriminator_marker_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness | None
    ) = None,
    backend_terminal_notice_leading_discriminator_marker_prefix_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixHarnessResult
        | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness:
    """Build exact truth for the leading-discriminator marker-prefix seam."""

    leading_discriminator_marker_exactness = (
        backend_terminal_notice_leading_discriminator_marker_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_marker_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_marker_prefix_unresolved"
    )
    verdict = (
        "backend_terminal_notice_leading_discriminator_marker_dependency_still_blocked"
    )
    leading_discriminator_marker_prefix_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_leading_discriminator_marker_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator marker-prefix exactness is not yet frozen because leading-discriminator-marker truth is not exact"
    )
    recommended_next_step = (
        "freeze backend terminal-notice leading-discriminator-marker truth before reducing the remaining leading-discriminator-marker-prefix seam"
    )

    if (
        leading_discriminator_marker_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_exact"
        and leading_discriminator_marker_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_dependency"
    ):
        exactness_rung = (
            "stream_backend_terminal_notice_leading_discriminator_marker_prefix_exact"
        )
        leading_discriminator_marker_prefix_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_prefix_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_leading_discriminator_marker_prefix_detection"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_marker_prefix_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_prefix_detection"
        )
        preserved_non_stream_handoff_status = (
            leading_discriminator_marker_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx already owns an earlier runtime-owned terminal_notice_lead marker on the leading-discriminator record on this path, but the live backend stream exchange still owns the serial boundary until child stdout reaches the earlier terminal_notice_lead marker-prefix on that same record, so leading-discriminator marker-prefix detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice leading-discriminator marker-prefix seam next without inflating this runtime-owned narrowing into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_marker_prefix_harness
            is not None
            and backend_terminal_notice_leading_discriminator_marker_prefix_harness.backend_terminal_notice_leading_discriminator_marker_prefix_boundary_visible
            and backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_prefix_detected
            and backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_detected
            and backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = (
                "backend_terminal_notice_leading_discriminator_marker_dependency_narrowed"
            )
            leading_discriminator_marker_prefix_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_marker_prefix_detected_before_notice_leading_discriminator_marker_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_marker_prefix_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_prefix_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than runtime-owned terminal_notice_lead marker detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches that internal terminal_notice_lead marker, but it still cannot enter before child stdout reaches the earlier terminal_notice_lead marker-prefix on the same record, so backend-terminal notice leading-discriminator marker-prefix detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator marker-prefix detection as the current exact stream dependency without inflating this runtime-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness(
        backend_terminal_notice_leading_discriminator_marker_exactness=(
            leading_discriminator_marker_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        leading_discriminator_marker_prefix_status=(
            leading_discriminator_marker_prefix_status
        ),
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness,
) -> dict[str, object]:
    """Serialize terminal-notice leading-discriminator marker-prefix exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_marker_prefix",
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
        "backend_terminal_notice_leading_discriminator_marker_prefix": {
            "leading_discriminator_marker_prefix_status": (
                exactness.leading_discriminator_marker_prefix_status
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
