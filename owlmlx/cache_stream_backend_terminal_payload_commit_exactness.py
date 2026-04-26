"""Runtime-owned exactness for the backend terminal-payload-commit stream seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_event_exactness import (
    CacheStreamBackendTerminalEventExactness,
    build_cache_stream_backend_terminal_event_exactness,
)
from .cache_stream_backend_terminal_payload_commit_harness import (
    CacheStreamBackendTerminalPayloadCommitHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalPayloadCommitExactness:
    """Exact backend terminal-payload-commit truth after terminal-event delivery narrowed."""

    backend_terminal_event_exactness: CacheStreamBackendTerminalEventExactness
    status: str
    exactness_rung: str
    verdict: str
    payload_commit_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_payload_commit_exactness(
    *,
    backend_terminal_event_exactness: CacheStreamBackendTerminalEventExactness | None = None,
    backend_terminal_payload_commit_harness: (
        CacheStreamBackendTerminalPayloadCommitHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalPayloadCommitExactness:
    """Build exact backend terminal-payload-commit truth for the active stream path."""

    terminal_event_exactness = (
        backend_terminal_event_exactness
        if isinstance(
            backend_terminal_event_exactness,
            CacheStreamBackendTerminalEventExactness,
        )
        else build_cache_stream_backend_terminal_event_exactness()
    )

    exactness_rung = "stream_backend_terminal_payload_commit_unresolved"
    verdict = "backend_terminal_payload_commit_dependency_still_blocked"
    payload_commit_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_payload_commit_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-payload-commit exactness is not yet frozen because terminal-event narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-event narrowing before reducing the remaining backend terminal-payload-commit seam"
    )

    if (
        terminal_event_exactness.exactness_rung == "stream_backend_terminal_event_exact"
        and terminal_event_exactness.next_active_dependency
        == "backend_terminal_payload_commit_dependency"
    ):
        exactness_rung = "stream_backend_terminal_payload_commit_exact"
        payload_commit_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit"
        )
        exchange_boundary = "backend_stream_exchange_until_terminal_payload_commit"
        next_active_dependency = "backend_terminal_payload_commit_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit"
        )
        preserved_non_stream_handoff_status = (
            terminal_event_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream can already start before the first iterator consumer receives the terminal event, but the live backend stream exchange still owns the serial boundary until the first stream commits its terminal payload, so terminal-payload commit is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-payload-commit seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_payload_commit_harness is not None
            and backend_terminal_payload_commit_harness.backend_terminal_payload_commit_boundary_visible
            and backend_terminal_payload_commit_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_payload_commit_harness.second_stream_started_before_first_terminal_payload_committed
            and backend_terminal_payload_commit_harness.second_stream_started_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_payload_commit_dependency_narrowed"
            payload_commit_status = (
                "backend_serial_boundary_decoupled_from_terminal_payload_commit_visible"
            )
            exchange_boundary = "backend_terminal_payload_capture_before_payload_commit"
            next_active_dependency = "backend_terminal_payload_capture_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-payload commit on this path: a second backend stream still cannot enter the live backend exchange before the first stream captures its terminal payload under the subprocess I/O lock, but it can start before that terminal payload is committed to the first stream queue or consumed by the iterator, so backend-terminal-payload capture is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal-payload capture as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalPayloadCommitExactness(
        backend_terminal_event_exactness=terminal_event_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        payload_commit_status=payload_commit_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_payload_commit_exactness_to_dict(
    exactness: CacheStreamBackendTerminalPayloadCommitExactness,
) -> dict[str, object]:
    """Serialize backend terminal-payload-commit exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_payload_commit_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_payload_commit",
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
        "backend_terminal_payload_commit": {
            "payload_commit_status": exactness.payload_commit_status,
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
