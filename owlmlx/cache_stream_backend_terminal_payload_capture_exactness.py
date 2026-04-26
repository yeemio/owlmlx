"""Runtime-owned exactness for the backend terminal-payload-capture stream seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_payload_capture_harness import (
    CacheStreamBackendTerminalPayloadCaptureHarnessResult,
)
from .cache_stream_backend_terminal_payload_commit_exactness import (
    CacheStreamBackendTerminalPayloadCommitExactness,
    build_cache_stream_backend_terminal_payload_commit_exactness,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalPayloadCaptureExactness:
    """Exact backend terminal-payload-capture truth after payload-commit narrowed."""

    backend_terminal_payload_commit_exactness: (
        CacheStreamBackendTerminalPayloadCommitExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    payload_capture_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_payload_capture_exactness(
    *,
    backend_terminal_payload_commit_exactness: (
        CacheStreamBackendTerminalPayloadCommitExactness | None
    ) = None,
    backend_terminal_payload_capture_harness: (
        CacheStreamBackendTerminalPayloadCaptureHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalPayloadCaptureExactness:
    """Build exact backend terminal-payload-capture truth for the active stream path."""

    payload_commit_exactness = (
        backend_terminal_payload_commit_exactness
        if isinstance(
            backend_terminal_payload_commit_exactness,
            CacheStreamBackendTerminalPayloadCommitExactness,
        )
        else build_cache_stream_backend_terminal_payload_commit_exactness()
    )

    exactness_rung = "stream_backend_terminal_payload_capture_unresolved"
    verdict = "backend_terminal_payload_capture_dependency_still_blocked"
    payload_capture_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_payload_capture_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-payload-capture exactness is not yet frozen because terminal-payload-commit narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-payload-commit narrowing before reducing the remaining backend terminal-payload-capture seam"
    )

    if (
        payload_commit_exactness.exactness_rung
        == "stream_backend_terminal_payload_commit_exact"
        and payload_commit_exactness.next_active_dependency
        == "backend_terminal_payload_capture_dependency"
    ):
        exactness_rung = "stream_backend_terminal_payload_capture_exact"
        payload_capture_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture"
        )
        exchange_boundary = "backend_stream_exchange_until_terminal_payload_capture"
        next_active_dependency = "backend_terminal_payload_capture_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture"
        )
        preserved_non_stream_handoff_status = (
            payload_commit_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream can already start before the first terminal payload is committed to the first stream queue, but the live backend stream exchange still owns the serial boundary until the first stream captures its terminal payload, so terminal-payload capture is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-payload-capture seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_payload_capture_harness is not None
            and backend_terminal_payload_capture_harness.backend_terminal_payload_capture_boundary_visible
            and backend_terminal_payload_capture_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_payload_capture_harness.second_stream_started_before_first_terminal_payload_captured
            and backend_terminal_payload_capture_harness.second_stream_started_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_payload_capture_dependency_narrowed"
            payload_capture_status = (
                "backend_serial_boundary_decoupled_from_terminal_payload_capture_visible"
            )
            exchange_boundary = "backend_terminal_record_capture_before_payload_decode"
            next_active_dependency = "backend_terminal_record_capture_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-payload capture on this path: a second backend stream still cannot enter the live backend exchange before the first stream captures its terminal record from child stdout, but it can start before that terminal record is decoded into a terminal payload, committed to the first stream queue, or consumed by the iterator, so backend-terminal-record capture is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal-record capture as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalPayloadCaptureExactness(
        backend_terminal_payload_commit_exactness=payload_commit_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        payload_capture_status=payload_capture_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_payload_capture_exactness_to_dict(
    exactness: CacheStreamBackendTerminalPayloadCaptureExactness,
) -> dict[str, object]:
    """Serialize backend terminal-payload-capture exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_payload_capture_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_payload_capture",
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
        "backend_terminal_payload_capture": {
            "payload_capture_status": exactness.payload_capture_status,
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
