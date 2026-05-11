"""Runtime-owned exactness for the backend terminal-notice-marker-stem seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_marker_prefix_exactness import (
    CacheStreamBackendTerminalNoticeMarkerPrefixExactness,
    build_cache_stream_backend_terminal_notice_marker_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_marker_stem_harness import (
    CacheStreamBackendTerminalNoticeMarkerStemHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeMarkerStemExactness:
    """Exact backend terminal-notice-marker-stem truth after marker-prefix narrowed."""

    backend_terminal_notice_marker_prefix_exactness: (
        CacheStreamBackendTerminalNoticeMarkerPrefixExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    notice_marker_stem_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_marker_stem_exactness(
    *,
    backend_terminal_notice_marker_prefix_exactness: (
        CacheStreamBackendTerminalNoticeMarkerPrefixExactness | None
    ) = None,
    backend_terminal_notice_marker_stem_harness: (
        CacheStreamBackendTerminalNoticeMarkerStemHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeMarkerStemExactness:
    """Build exact backend terminal-notice-marker-stem truth."""

    marker_prefix_exactness = (
        backend_terminal_notice_marker_prefix_exactness
        if isinstance(
            backend_terminal_notice_marker_prefix_exactness,
            CacheStreamBackendTerminalNoticeMarkerPrefixExactness,
        )
        else build_cache_stream_backend_terminal_notice_marker_prefix_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_marker_stem_unresolved"
    verdict = "backend_terminal_notice_marker_stem_dependency_still_blocked"
    notice_marker_stem_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_marker_stem_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice-marker-stem exactness is not yet frozen because terminal-notice-marker-prefix narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-notice-marker-prefix narrowing before reducing the remaining backend terminal-notice-marker-stem seam"
    )

    if (
        marker_prefix_exactness.exactness_rung
        == "stream_backend_terminal_notice_marker_prefix_exact"
        and marker_prefix_exactness.next_active_dependency
        == "backend_terminal_notice_marker_stem_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_marker_stem_exact"
        notice_marker_stem_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_stem_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_marker_stem_detection"
        )
        next_active_dependency = "backend_terminal_notice_marker_stem_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_stem_detection"
        )
        preserved_non_stream_handoff_status = (
            marker_prefix_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before child stdout reaches the terminal-notice marker key itself, but the live backend stream exchange still owns the serial boundary until child stdout reaches the earlier terminal-notice marker discriminant that first isolates the marker-key family, so terminal-notice marker-stem detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice-marker-stem seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_marker_stem_harness is not None
            and backend_terminal_notice_marker_stem_harness.backend_terminal_notice_marker_stem_boundary_visible
            and backend_terminal_notice_marker_stem_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_marker_stem_harness.second_stream_request_written_before_first_terminal_notice_marker_stem_detected
            and backend_terminal_notice_marker_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_notice_marker_stem_dependency_narrowed"
            notice_marker_stem_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_marker_stem_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_marker_discriminant_detected_before_notice_marker_stem_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_marker_discriminant_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_discriminant_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-notice marker-stem detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches the terminal-notice marker stem, but it still cannot enter before child stdout reaches the earlier terminal-notice marker discriminant that first isolates the marker-key family inside the runtime-owned transport record, so backend-terminal-notice marker-discriminant detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice marker-discriminant detection as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalNoticeMarkerStemExactness(
        backend_terminal_notice_marker_prefix_exactness=marker_prefix_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        notice_marker_stem_status=notice_marker_stem_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_marker_stem_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeMarkerStemExactness,
) -> dict[str, object]:
    """Serialize backend terminal-notice-marker-stem exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_marker_stem_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_marker_stem",
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
        "backend_terminal_notice_marker_stem": {
            "notice_marker_stem_status": exactness.notice_marker_stem_status,
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

