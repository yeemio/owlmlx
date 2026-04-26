"""Runtime-owned exactness for the backend terminal-record-prefix stream seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_record_capture_exactness import (
    CacheStreamBackendTerminalRecordCaptureExactness,
    build_cache_stream_backend_terminal_record_capture_exactness,
)
from .cache_stream_backend_terminal_record_prefix_harness import (
    CacheStreamBackendTerminalRecordPrefixHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalRecordPrefixExactness:
    """Exact backend terminal-record-prefix truth after record-capture narrowed."""

    backend_terminal_record_capture_exactness: (
        CacheStreamBackendTerminalRecordCaptureExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    prefix_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_record_prefix_exactness(
    *,
    backend_terminal_record_capture_exactness: (
        CacheStreamBackendTerminalRecordCaptureExactness | None
    ) = None,
    backend_terminal_record_prefix_harness: (
        CacheStreamBackendTerminalRecordPrefixHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalRecordPrefixExactness:
    """Build exact backend terminal-record-prefix truth for the active stream path."""

    record_capture_exactness = (
        backend_terminal_record_capture_exactness
        if isinstance(
            backend_terminal_record_capture_exactness,
            CacheStreamBackendTerminalRecordCaptureExactness,
        )
        else build_cache_stream_backend_terminal_record_capture_exactness()
    )

    exactness_rung = "stream_backend_terminal_record_prefix_unresolved"
    verdict = "backend_terminal_record_prefix_dependency_still_blocked"
    prefix_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_record_prefix_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-record-prefix exactness is not yet frozen because terminal-record-capture narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-record-capture narrowing before reducing the remaining backend terminal-record-prefix seam"
    )

    if (
        record_capture_exactness.exactness_rung
        == "stream_backend_terminal_record_capture_exact"
        and record_capture_exactness.next_active_dependency
        == "backend_terminal_record_prefix_dependency"
    ):
        exactness_rung = "stream_backend_terminal_record_prefix_exact"
        prefix_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_record_prefix_detection"
        )
        next_active_dependency = "backend_terminal_record_prefix_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection"
        )
        preserved_non_stream_handoff_status = (
            record_capture_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before the first stream fully captures its terminal record from child stdout, but the live backend stream exchange still owns the serial boundary until the first stream fully matches its terminal-record prefix, so terminal-record prefix detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-record-prefix seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_record_prefix_harness is not None
            and backend_terminal_record_prefix_harness.backend_terminal_record_prefix_boundary_visible
            and backend_terminal_record_prefix_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_record_prefix_harness.second_stream_request_written_before_first_terminal_record_prefix_detected
            and backend_terminal_record_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_record_prefix_dependency_narrowed"
            prefix_status = (
                "backend_serial_boundary_decoupled_from_terminal_record_prefix_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_action_discriminant_detected_before_full_record_prefix"
            )
            next_active_dependency = "backend_terminal_action_discriminant_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-record prefix on this path: a second backend stream request can enter the live backend exchange before the first stream fully matches its terminal-record prefix on child stdout, but it still cannot enter before the terminal action has been discriminated as terminal, so backend-terminal action discriminant detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal action discriminant detection as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalRecordPrefixExactness(
        backend_terminal_record_capture_exactness=record_capture_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        prefix_status=prefix_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_record_prefix_exactness_to_dict(
    exactness: CacheStreamBackendTerminalRecordPrefixExactness,
) -> dict[str, object]:
    """Serialize backend terminal-record-prefix exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_record_prefix_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_record_prefix",
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
        "backend_terminal_record_prefix": {
            "prefix_status": exactness.prefix_status,
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
