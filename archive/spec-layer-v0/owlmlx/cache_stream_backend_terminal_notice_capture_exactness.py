"""Runtime-owned exactness for the backend terminal-notice capture stream seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_action_discriminant_exactness import (
    CacheStreamBackendTerminalActionDiscriminantExactness,
    build_cache_stream_backend_terminal_action_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_capture_harness import (
    CacheStreamBackendTerminalNoticeCaptureHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeCaptureExactness:
    """Exact backend terminal-notice capture truth after action-discriminant narrowed."""

    backend_terminal_action_discriminant_exactness: (
        CacheStreamBackendTerminalActionDiscriminantExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    notice_capture_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_capture_exactness(
    *,
    backend_terminal_action_discriminant_exactness: (
        CacheStreamBackendTerminalActionDiscriminantExactness | None
    ) = None,
    backend_terminal_notice_capture_harness: (
        CacheStreamBackendTerminalNoticeCaptureHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeCaptureExactness:
    """Build exact backend terminal-notice capture truth for the active stream path."""

    action_discriminant_exactness = (
        backend_terminal_action_discriminant_exactness
        if isinstance(
            backend_terminal_action_discriminant_exactness,
            CacheStreamBackendTerminalActionDiscriminantExactness,
        )
        else build_cache_stream_backend_terminal_action_discriminant_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_capture_unresolved"
    verdict = "backend_terminal_notice_capture_dependency_still_blocked"
    notice_capture_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_capture_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice capture exactness is not yet frozen because terminal-action-discriminant narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-action-discriminant narrowing before reducing the remaining backend terminal-notice capture seam"
    )

    if (
        action_discriminant_exactness.exactness_rung
        == "stream_backend_terminal_action_discriminant_exact"
        and action_discriminant_exactness.next_active_dependency
        == "backend_terminal_notice_capture_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_capture_exact"
        notice_capture_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture"
        )
        exchange_boundary = "backend_stream_exchange_until_terminal_notice_capture"
        next_active_dependency = "backend_terminal_notice_capture_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture"
        )
        preserved_non_stream_handoff_status = (
            action_discriminant_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before the first terminal done payload reaches its action discriminant on child stdout, but the live backend stream exchange still owns the serial boundary until the first stream fully captures the earlier terminal-notice record, so terminal-notice capture is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice capture seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_capture_harness is not None
            and backend_terminal_notice_capture_harness.backend_terminal_notice_capture_boundary_visible
            and backend_terminal_notice_capture_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_capture_harness.second_stream_request_written_before_first_terminal_notice_captured
            and backend_terminal_notice_capture_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_notice_capture_dependency_narrowed"
            notice_capture_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_capture_visible"
            )
            exchange_boundary = "backend_terminal_notice_prefix_detected_before_notice_capture"
            next_active_dependency = "backend_terminal_notice_prefix_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_prefix_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than full terminal-notice capture on this path: a second backend stream request can enter the live backend exchange before the first terminal-notice record is fully captured, but it still cannot enter before child stdout reaches the terminal-notice prefix that proves the record family, so backend-terminal-notice prefix detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice prefix detection as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalNoticeCaptureExactness(
        backend_terminal_action_discriminant_exactness=action_discriminant_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        notice_capture_status=notice_capture_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_capture_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeCaptureExactness,
) -> dict[str, object]:
    """Serialize backend terminal-notice capture exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_capture_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_capture",
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
        "backend_terminal_notice_capture": {
            "notice_capture_status": exactness.notice_capture_status,
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
