"""Runtime-owned exactness for the backend terminal-notice-action-stem seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_action_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeActionDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_action_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_action_stem_harness import (
    CacheStreamBackendTerminalNoticeActionStemHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeActionStemExactness:
    """Exact backend terminal-notice-action-stem truth after notice-action-discriminant narrowed."""

    backend_terminal_notice_action_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeActionDiscriminantExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    notice_action_stem_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_action_stem_exactness(
    *,
    backend_terminal_notice_action_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeActionDiscriminantExactness | None
    ) = None,
    backend_terminal_notice_action_stem_harness: (
        CacheStreamBackendTerminalNoticeActionStemHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeActionStemExactness:
    """Build exact backend terminal-notice-action-stem truth."""

    notice_action_discriminant_exactness = (
        backend_terminal_notice_action_discriminant_exactness
        if isinstance(
            backend_terminal_notice_action_discriminant_exactness,
            CacheStreamBackendTerminalNoticeActionDiscriminantExactness,
        )
        else build_cache_stream_backend_terminal_notice_action_discriminant_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_action_stem_unresolved"
    verdict = "backend_terminal_notice_action_stem_dependency_still_blocked"
    notice_action_stem_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_action_stem_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice-action-stem exactness is not yet frozen because terminal-notice-action-discriminant narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-notice-action-discriminant narrowing before reducing the remaining backend terminal-notice-action-stem seam"
    )

    if (
        notice_action_discriminant_exactness.exactness_rung
        == "stream_backend_terminal_notice_action_discriminant_exact"
        and notice_action_discriminant_exactness.next_active_dependency
        == "backend_terminal_notice_action_stem_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_action_stem_exact"
        notice_action_stem_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_stem_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_action_stem_detection"
        )
        next_active_dependency = "backend_terminal_notice_action_stem_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_stem_detection"
        )
        preserved_non_stream_handoff_status = (
            notice_action_discriminant_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before child stdout reaches the terminal-notice action discriminant that proves the notice family, but the live backend stream exchange still owns the serial boundary until child stdout reaches the earlier terminal-notice action stem, so terminal-notice action-stem detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice-action-stem seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_action_stem_harness is not None
            and backend_terminal_notice_action_stem_harness.backend_terminal_notice_action_stem_boundary_visible
            and backend_terminal_notice_action_stem_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_action_stem_harness.second_stream_request_written_before_first_terminal_notice_action_stem_detected
            and backend_terminal_notice_action_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_notice_action_stem_dependency_narrowed"
            notice_action_stem_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_action_stem_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_marker_detected_before_notice_action_stem"
            )
            next_active_dependency = "backend_terminal_notice_marker_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-notice action-stem detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches the terminal-notice action stem, but it still cannot enter before child stdout reaches the earlier explicit terminal-notice marker field that now precedes the action key in the runtime-owned transport record, so backend-terminal-notice marker detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice marker detection as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalNoticeActionStemExactness(
        backend_terminal_notice_action_discriminant_exactness=(
            notice_action_discriminant_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        notice_action_stem_status=notice_action_stem_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_action_stem_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeActionStemExactness,
) -> dict[str, object]:
    """Serialize backend terminal-notice-action-stem exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_action_stem_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_action_stem",
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
        "backend_terminal_notice_action_stem": {
            "notice_action_stem_status": exactness.notice_action_stem_status,
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
