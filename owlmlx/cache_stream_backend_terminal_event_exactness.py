"""Runtime-owned exactness for the backend terminal-event stream seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_hold_dependency_exactness import (
    CacheStreamHoldDependencyExactness,
    build_cache_stream_hold_dependency_exactness,
)
from .cache_stream_backend_terminal_event_harness import (
    CacheStreamBackendTerminalEventHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalEventExactness:
    """Exact backend-terminal-event truth after stream hold narrowed past consumer drain."""

    stream_hold_exactness: CacheStreamHoldDependencyExactness
    status: str
    exactness_rung: str
    verdict: str
    terminal_event_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_event_exactness(
    *,
    stream_hold_exactness: CacheStreamHoldDependencyExactness | None = None,
    backend_terminal_event_harness: CacheStreamBackendTerminalEventHarnessResult | None = None,
) -> CacheStreamBackendTerminalEventExactness:
    """Build exact backend-terminal-event truth for the active stream path."""

    hold_exactness = (
        stream_hold_exactness
        if isinstance(stream_hold_exactness, CacheStreamHoldDependencyExactness)
        else build_cache_stream_hold_dependency_exactness()
    )

    exactness_rung = "stream_backend_terminal_event_unresolved"
    verdict = "backend_stream_terminal_event_dependency_still_blocked"
    terminal_event_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_stream_terminal_event_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-event exactness is not yet frozen because stream-hold narrowing is not exact"
    )
    recommended_next_step = (
        "freeze stream-hold narrowing before reducing the remaining backend terminal-event seam"
    )

    if hold_exactness.exactness_rung == "stream_hold_dependency_exact":
        exactness_rung = "stream_backend_terminal_event_exact"
        terminal_event_status = "backend_terminal_event_serial_boundary_not_yet_visible"
        exchange_boundary = "backend_stream_exchange_until_terminal_event"
        next_active_dependency = "backend_stream_terminal_event_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_event"
        )
        preserved_non_stream_handoff_status = (
            hold_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, but the live backend stream exchange still owns the serial boundary until its terminal event, so backend-terminal-event commitment is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-event seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_event_harness is not None
            and backend_terminal_event_harness.backend_terminal_event_boundary_visible
            and backend_terminal_event_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_event_harness.second_stream_started_before_first_terminal_event_consumed
            and backend_terminal_event_harness.second_stream_started_before_first_iterator_completed
        ):
            verdict = "backend_stream_terminal_event_dependency_narrowed"
            terminal_event_status = (
                "backend_terminal_event_serial_boundary_visible"
            )
            exchange_boundary = (
                "backend_terminal_payload_commit_before_iterator_terminal_event_delivery"
            )
            next_active_dependency = "backend_terminal_payload_commit_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than generic backend terminal-event delivery on this path: a second backend stream still cannot enter the live backend exchange before the first stream commits its terminal payload on the backend side, but it can start before the first backend iterator consumer receives that terminal event, so backend-terminal-payload commit is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal-payload commit as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=hold_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        terminal_event_status=terminal_event_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_event_exactness_to_dict(
    exactness: CacheStreamBackendTerminalEventExactness,
) -> dict[str, object]:
    """Serialize backend-terminal-event exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_event_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_event",
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
        "backend_terminal_event": {
            "terminal_event_status": exactness.terminal_event_status,
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
