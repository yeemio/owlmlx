"""Runtime-owned exactness for the backend terminal-action-discriminant stream seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_record_prefix_exactness import (
    CacheStreamBackendTerminalRecordPrefixExactness,
    build_cache_stream_backend_terminal_record_prefix_exactness,
)
from .cache_stream_backend_terminal_action_discriminant_harness import (
    CacheStreamBackendTerminalActionDiscriminantHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalActionDiscriminantExactness:
    """Exact backend terminal-action-discriminant truth after record-prefix narrowed."""

    backend_terminal_record_prefix_exactness: (
        CacheStreamBackendTerminalRecordPrefixExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    action_discriminant_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_action_discriminant_exactness(
    *,
    backend_terminal_record_prefix_exactness: (
        CacheStreamBackendTerminalRecordPrefixExactness | None
    ) = None,
    backend_terminal_action_discriminant_harness: (
        CacheStreamBackendTerminalActionDiscriminantHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalActionDiscriminantExactness:
    """Build exact backend terminal-action-discriminant truth for the active stream path."""

    record_prefix_exactness = (
        backend_terminal_record_prefix_exactness
        if isinstance(
            backend_terminal_record_prefix_exactness,
            CacheStreamBackendTerminalRecordPrefixExactness,
        )
        else build_cache_stream_backend_terminal_record_prefix_exactness()
    )

    exactness_rung = "stream_backend_terminal_action_discriminant_unresolved"
    verdict = "backend_terminal_action_discriminant_dependency_still_blocked"
    action_discriminant_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_action_discriminant_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-action-discriminant exactness is not yet frozen because terminal-record-prefix narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-record-prefix narrowing before reducing the remaining backend terminal-action-discriminant seam"
    )

    if (
        record_prefix_exactness.exactness_rung
        == "stream_backend_terminal_record_prefix_exact"
        and record_prefix_exactness.next_active_dependency
        == "backend_terminal_action_discriminant_dependency"
    ):
        exactness_rung = "stream_backend_terminal_action_discriminant_exact"
        action_discriminant_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_action_discriminant_detection"
        )
        next_active_dependency = "backend_terminal_action_discriminant_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection"
        )
        preserved_non_stream_handoff_status = (
            record_prefix_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before the first stream fully matches its terminal-record prefix on child stdout, but the live backend stream exchange still owns the serial boundary until the first stream captures an explicit terminal notice before the done payload, so terminal-action discriminant detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-action-discriminant seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_action_discriminant_harness is not None
            and backend_terminal_action_discriminant_harness.backend_terminal_action_discriminant_boundary_visible
            and backend_terminal_action_discriminant_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_action_discriminant_harness.second_stream_request_written_before_first_terminal_action_discriminant_detected
            and backend_terminal_action_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_action_discriminant_dependency_narrowed"
            action_discriminant_status = (
                "backend_serial_boundary_decoupled_from_terminal_action_discriminant_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_captured_before_terminal_action_discriminant_detection"
            )
            next_active_dependency = "backend_terminal_notice_capture_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-action discriminant detection on this path: a second backend stream request can enter the live backend exchange before the first terminal done payload reaches its action discriminant on child stdout, but it still cannot enter before the backend captures the explicit terminal notice that precedes that done payload, so backend-terminal notice capture is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice capture as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalActionDiscriminantExactness(
        backend_terminal_record_prefix_exactness=record_prefix_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        action_discriminant_status=action_discriminant_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_action_discriminant_exactness_to_dict(
    exactness: CacheStreamBackendTerminalActionDiscriminantExactness,
) -> dict[str, object]:
    """Serialize backend terminal-action-discriminant exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_action_discriminant_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_action_discriminant",
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
        "backend_terminal_action_discriminant": {
            "action_discriminant_status": exactness.action_discriminant_status,
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
