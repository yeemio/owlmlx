"""Runtime-owned exactness for the backend terminal-notice-marker seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_action_stem_exactness import (
    CacheStreamBackendTerminalNoticeActionStemExactness,
    build_cache_stream_backend_terminal_notice_action_stem_exactness,
)
from .cache_stream_backend_terminal_notice_marker_harness import (
    CacheStreamBackendTerminalNoticeMarkerHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeMarkerExactness:
    """Exact backend terminal-notice-marker truth after notice-action-stem narrowed."""

    backend_terminal_notice_action_stem_exactness: (
        CacheStreamBackendTerminalNoticeActionStemExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    notice_marker_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_marker_exactness(
    *,
    backend_terminal_notice_action_stem_exactness: (
        CacheStreamBackendTerminalNoticeActionStemExactness | None
    ) = None,
    backend_terminal_notice_marker_harness: (
        CacheStreamBackendTerminalNoticeMarkerHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeMarkerExactness:
    """Build exact backend terminal-notice-marker truth."""

    notice_action_stem_exactness = (
        backend_terminal_notice_action_stem_exactness
        if isinstance(
            backend_terminal_notice_action_stem_exactness,
            CacheStreamBackendTerminalNoticeActionStemExactness,
        )
        else build_cache_stream_backend_terminal_notice_action_stem_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_marker_unresolved"
    verdict = "backend_terminal_notice_marker_dependency_still_blocked"
    notice_marker_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_marker_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice-marker exactness is not yet frozen because terminal-notice-action-stem narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-notice-action-stem narrowing before reducing the remaining backend terminal-notice-marker seam"
    )

    if (
        notice_action_stem_exactness.exactness_rung
        == "stream_backend_terminal_notice_action_stem_exact"
        and notice_action_stem_exactness.next_active_dependency
        == "backend_terminal_notice_marker_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_marker_exact"
        notice_marker_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_marker_detection"
        )
        next_active_dependency = "backend_terminal_notice_marker_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_detection"
        )
        preserved_non_stream_handoff_status = (
            notice_action_stem_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before child stdout reaches the terminal-notice action stem, but the live backend stream exchange still owns the serial boundary until child stdout reaches the earlier explicit terminal-notice marker field, so terminal-notice marker detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice-marker seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_marker_harness is not None
            and backend_terminal_notice_marker_harness.backend_terminal_notice_marker_boundary_visible
            and backend_terminal_notice_marker_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_marker_harness.second_stream_request_written_before_first_terminal_notice_marker_detected
            and backend_terminal_notice_marker_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_notice_marker_dependency_narrowed"
            notice_marker_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_marker_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_marker_prefix_detected_before_notice_marker_detection"
            )
            next_active_dependency = "backend_terminal_notice_marker_prefix_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_prefix_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-notice marker detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches the explicit terminal-notice marker field, but it still cannot enter before child stdout reaches the earlier terminal-notice marker prefix that proves the marker key itself inside the runtime-owned transport record, so backend-terminal-notice marker-prefix detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice marker-prefix detection as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalNoticeMarkerExactness(
        backend_terminal_notice_action_stem_exactness=notice_action_stem_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        notice_marker_status=notice_marker_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_marker_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeMarkerExactness,
) -> dict[str, object]:
    """Serialize backend terminal-notice-marker exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_marker_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_marker",
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
        "backend_terminal_notice_marker": {
            "notice_marker_status": exactness.notice_marker_status,
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
