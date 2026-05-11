"""Runtime-owned exactness for backend terminal-notice leading-discriminator introduction."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_marker_key_lead_exactness import (
    CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness,
    build_cache_stream_backend_terminal_notice_marker_key_lead_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness:
    """Exact truth for introducing an earlier runtime-owned terminal-notice discriminator."""

    backend_terminal_notice_marker_key_lead_exactness: (
        CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    leading_discriminator_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_exactness(
    *,
    backend_terminal_notice_marker_key_lead_exactness: (
        CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness | None
    ) = None,
    backend_terminal_notice_leading_discriminator_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness:
    """Build exact truth for the leading-discriminator round."""

    key_lead_exactness = (
        backend_terminal_notice_marker_key_lead_exactness
        if isinstance(
            backend_terminal_notice_marker_key_lead_exactness,
            CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness,
        )
        else build_cache_stream_backend_terminal_notice_marker_key_lead_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_leading_discriminator_unresolved"
    verdict = "backend_terminal_notice_leading_discriminator_dependency_not_introduced"
    leading_discriminator_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_marker_key_lead_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "terminal-notice leading-discriminator exactness is not yet frozen because terminal-notice marker-key-lead truth is not exact"
    )
    recommended_next_step = (
        "freeze terminal-notice marker-key-lead truth before deciding whether owlmlx introduces a new earlier runtime-owned leading discriminator"
    )

    if (
        key_lead_exactness.exactness_rung
        == "stream_backend_terminal_notice_marker_key_lead_exact"
        and key_lead_exactness.next_active_dependency
        == "backend_terminal_notice_marker_key_lead_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_leading_discriminator_exact"
        leading_discriminator_status = (
            "runtime_owned_terminal_notice_leading_discriminator_not_introduced"
        )
        exchange_boundary = (
            "backend_terminal_notice_marker_key_lead_remains_first_unique_boundary"
        )
        next_active_dependency = "backend_terminal_notice_marker_key_lead_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection"
        )
        preserved_non_stream_handoff_status = (
            key_lead_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx has now frozen terminal-notice marker-key-lead detection as the first unique boundary on this path, but no earlier runtime-owned terminal-notice leading discriminator has been introduced yet, so the live backend stream exchange still owns the serial boundary until that marker-key lead"
        )
        recommended_next_step = (
            "either keep terminal-notice marker-key-lead detection frozen as the current exact seam or introduce a new earlier runtime-owned leading discriminator without widening the story into interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_harness is not None
            and backend_terminal_notice_leading_discriminator_harness.backend_terminal_notice_leading_discriminator_boundary_visible
            and backend_terminal_notice_leading_discriminator_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected
            and backend_terminal_notice_leading_discriminator_harness.second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected
            and backend_terminal_notice_leading_discriminator_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = (
                "backend_terminal_notice_leading_discriminator_dependency_introduced"
            )
            leading_discriminator_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_detected_before_notice_marker_key_lead_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection"
            )
            residual_blocker = (
                "owlmlx now owns a runtime-owned terminal-notice leading discriminator ahead of the old marker-key-lead seam on this path: a second backend stream request can be written once child stdout reaches that internal leading-discriminator record and before child stdout reaches the first terminal-notice marker-key lead, so the remaining exact stream seam now sits at terminal-notice leading-discriminator detection"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator detection as the current exact stream dependency without inflating this transport-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness(
        backend_terminal_notice_marker_key_lead_exactness=key_lead_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        leading_discriminator_status=leading_discriminator_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness,
) -> dict[str, object]:
    """Serialize terminal-notice leading-discriminator exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator",
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
        "backend_terminal_notice_leading_discriminator": {
            "leading_discriminator_status": exactness.leading_discriminator_status,
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
