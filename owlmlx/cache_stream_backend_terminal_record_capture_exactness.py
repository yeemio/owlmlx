"""Runtime-owned exactness for the backend terminal-record-capture stream seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_payload_capture_exactness import (
    CacheStreamBackendTerminalPayloadCaptureExactness,
    build_cache_stream_backend_terminal_payload_capture_exactness,
)
from .cache_stream_backend_terminal_record_capture_harness import (
    CacheStreamBackendTerminalRecordCaptureHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalRecordCaptureExactness:
    """Exact backend terminal-record-capture truth after payload-capture narrowed."""

    backend_terminal_payload_capture_exactness: (
        CacheStreamBackendTerminalPayloadCaptureExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    record_capture_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_record_capture_exactness(
    *,
    backend_terminal_payload_capture_exactness: (
        CacheStreamBackendTerminalPayloadCaptureExactness | None
    ) = None,
    backend_terminal_record_capture_harness: (
        CacheStreamBackendTerminalRecordCaptureHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalRecordCaptureExactness:
    """Build exact backend terminal-record-capture truth for the active stream path."""

    payload_capture_exactness = (
        backend_terminal_payload_capture_exactness
        if isinstance(
            backend_terminal_payload_capture_exactness,
            CacheStreamBackendTerminalPayloadCaptureExactness,
        )
        else build_cache_stream_backend_terminal_payload_capture_exactness()
    )

    exactness_rung = "stream_backend_terminal_record_capture_unresolved"
    verdict = "backend_terminal_record_capture_dependency_still_blocked"
    record_capture_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_record_capture_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-record-capture exactness is not yet frozen because terminal-payload-capture narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-payload-capture narrowing before reducing the remaining backend terminal-record-capture seam"
    )

    if (
        payload_capture_exactness.exactness_rung
        == "stream_backend_terminal_payload_capture_exact"
        and payload_capture_exactness.next_active_dependency
        == "backend_terminal_record_capture_dependency"
    ):
        exactness_rung = "stream_backend_terminal_record_capture_exact"
        record_capture_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture"
        )
        exchange_boundary = "backend_stream_exchange_until_terminal_record_capture"
        next_active_dependency = "backend_terminal_record_capture_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture"
        )
        preserved_non_stream_handoff_status = (
            payload_capture_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream can already start before the first terminal payload is decoded and captured, but the live backend stream exchange still owns the serial boundary until the first stream captures its terminal record from child stdout, so terminal-record capture is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-record-capture seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_record_capture_harness is not None
            and backend_terminal_record_capture_harness.backend_terminal_record_capture_boundary_visible
            and backend_terminal_record_capture_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_record_capture_harness.second_stream_request_written_before_first_terminal_record_captured
            and backend_terminal_record_capture_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_record_capture_dependency_narrowed"
            record_capture_status = (
                "backend_serial_boundary_decoupled_from_terminal_record_capture_visible"
            )
            exchange_boundary = (
                "backend_terminal_record_prefix_detected_before_record_capture"
            )
            next_active_dependency = "backend_terminal_record_prefix_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-record capture on this path: a second backend stream request can enter the live backend exchange before the first stream fully captures its terminal record from child stdout, but it still cannot enter before the terminal record has been identified as terminal, so backend-terminal-record prefix detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal-record prefix detection as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalRecordCaptureExactness(
        backend_terminal_payload_capture_exactness=payload_capture_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        record_capture_status=record_capture_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_record_capture_exactness_to_dict(
    exactness: CacheStreamBackendTerminalRecordCaptureExactness,
) -> dict[str, object]:
    """Serialize backend terminal-record-capture exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_record_capture_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_record_capture",
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
        "backend_terminal_record_capture": {
            "record_capture_status": exactness.record_capture_status,
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
