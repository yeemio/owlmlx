"""Runtime-owned exactness for the backend terminal-notice-marker-key-lead seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_marker_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_marker_key_lead_harness import (
    CacheStreamBackendTerminalNoticeMarkerKeyLeadHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness:
    """Exact backend terminal-notice-marker-key-lead truth after marker-discriminant narrowed."""

    backend_terminal_notice_marker_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    notice_marker_key_lead_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_marker_key_lead_exactness(
    *,
    backend_terminal_notice_marker_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness | None
    ) = None,
    backend_terminal_notice_marker_key_lead_harness: (
        CacheStreamBackendTerminalNoticeMarkerKeyLeadHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness:
    """Build exact backend terminal-notice-marker-key-lead truth."""

    marker_discriminant_exactness = (
        backend_terminal_notice_marker_discriminant_exactness
        if isinstance(
            backend_terminal_notice_marker_discriminant_exactness,
            CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness,
        )
        else build_cache_stream_backend_terminal_notice_marker_discriminant_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_marker_key_lead_unresolved"
    verdict = "backend_terminal_notice_marker_key_lead_dependency_still_blocked"
    notice_marker_key_lead_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_marker_key_lead_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice-marker-key-lead exactness is not yet frozen because terminal-notice-marker-discriminant narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-notice-marker-discriminant narrowing before reducing the remaining backend terminal-notice-marker-key-lead seam"
    )

    if (
        marker_discriminant_exactness.exactness_rung
        == "stream_backend_terminal_notice_marker_discriminant_exact"
        and marker_discriminant_exactness.next_active_dependency
        == "backend_terminal_notice_marker_key_lead_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_marker_key_lead_exact"
        notice_marker_key_lead_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_marker_key_lead_detection"
        )
        next_active_dependency = "backend_terminal_notice_marker_key_lead_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection"
        )
        preserved_non_stream_handoff_status = (
            marker_discriminant_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before child stdout reaches the terminal-notice marker discriminant, but the live backend stream exchange still owns the serial boundary until child stdout reaches the first unique terminal-notice marker-key character after the ok field inside the runtime-owned terminal-notice transport record, because the earlier opening quote of that key still collides with ordinary ok-true stream records on this path, so terminal-notice marker-key-lead detection remains the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice-marker-key-lead seam honestly on this path without inflating an earlier non-unique key-quote prefix into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_marker_key_lead_harness is not None
            and backend_terminal_notice_marker_key_lead_harness.backend_terminal_notice_marker_key_lead_boundary_visible
            and backend_terminal_notice_marker_key_lead_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_marker_key_lead_harness.second_stream_request_written_after_first_terminal_notice_marker_key_lead_detected
            and backend_terminal_notice_marker_key_lead_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            notice_marker_key_lead_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_marker_key_lead_is_first_unique_notice_marker_boundary_visible"
            )
            residual_blocker = (
                "the remaining exact stream seam stays at terminal-notice marker-key-lead detection on this path: a second backend stream request remains blocked until child stdout reaches the first unique terminal-notice marker-key character after the ok field, because the earlier opening quote of that first key still collides with ordinary ok-true stream records and therefore is not an honest earlier live boundary"
            )
            recommended_next_step = (
                "treat backend-terminal notice marker-key lead detection as the current exact stream dependency unless owlmlx introduces a new earlier runtime-owned leading discriminator without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness(
        backend_terminal_notice_marker_discriminant_exactness=(
            marker_discriminant_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        notice_marker_key_lead_status=notice_marker_key_lead_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_marker_key_lead_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness,
) -> dict[str, object]:
    """Serialize backend terminal-notice-marker-key-lead exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_marker_key_lead_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_marker_key_lead",
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
        "backend_terminal_notice_marker_key_lead": {
            "notice_marker_key_lead_status": exactness.notice_marker_key_lead_status,
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
