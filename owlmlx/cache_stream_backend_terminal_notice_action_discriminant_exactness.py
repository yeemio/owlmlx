"""Runtime-owned exactness for the backend terminal-notice-action-discriminant seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_action_discriminant_harness import (
    CacheStreamBackendTerminalNoticeActionDiscriminantHarnessResult,
)
from .cache_stream_backend_terminal_notice_prefix_exactness import (
    CacheStreamBackendTerminalNoticePrefixExactness,
    build_cache_stream_backend_terminal_notice_prefix_exactness,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeActionDiscriminantExactness:
    """Exact backend terminal-notice-action-discriminant truth after notice-prefix narrowed."""

    backend_terminal_notice_prefix_exactness: CacheStreamBackendTerminalNoticePrefixExactness
    status: str
    exactness_rung: str
    verdict: str
    notice_action_discriminant_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_action_discriminant_exactness(
    *,
    backend_terminal_notice_prefix_exactness: (
        CacheStreamBackendTerminalNoticePrefixExactness | None
    ) = None,
    backend_terminal_notice_action_discriminant_harness: (
        CacheStreamBackendTerminalNoticeActionDiscriminantHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeActionDiscriminantExactness:
    """Build exact backend terminal-notice-action-discriminant truth."""

    notice_prefix_exactness = (
        backend_terminal_notice_prefix_exactness
        if isinstance(
            backend_terminal_notice_prefix_exactness,
            CacheStreamBackendTerminalNoticePrefixExactness,
        )
        else build_cache_stream_backend_terminal_notice_prefix_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_action_discriminant_unresolved"
    verdict = "backend_terminal_notice_action_discriminant_dependency_still_blocked"
    notice_action_discriminant_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_action_discriminant_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice-action-discriminant exactness is not yet frozen because terminal-notice-prefix narrowing is not exact"
    )
    recommended_next_step = (
        "freeze terminal-notice-prefix narrowing before reducing the remaining backend terminal-notice-action-discriminant seam"
    )

    if (
        notice_prefix_exactness.exactness_rung
        == "stream_backend_terminal_notice_prefix_exact"
        and notice_prefix_exactness.next_active_dependency
        == "backend_terminal_notice_action_discriminant_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_action_discriminant_exact"
        notice_action_discriminant_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_discriminant_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_action_discriminant_detection"
        )
        next_active_dependency = "backend_terminal_notice_action_discriminant_dependency"
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_discriminant_detection"
        )
        preserved_non_stream_handoff_status = (
            notice_prefix_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "stream gate release is already decoupled from outer consumer drain on this path, and a second backend stream request can already enter the live backend exchange before child stdout fully matches the first terminal-notice prefix, but the live backend stream exchange still owns the serial boundary until child stdout reaches the terminal-notice action discriminant that proves the notice family, so terminal-notice action-discriminant detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice-action-discriminant seam next without inflating this into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_action_discriminant_harness is not None
            and backend_terminal_notice_action_discriminant_harness.backend_terminal_notice_action_discriminant_boundary_visible
            and backend_terminal_notice_action_discriminant_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_action_discriminant_harness.second_stream_request_written_before_first_terminal_notice_action_discriminant_detected
            and backend_terminal_notice_action_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_notice_action_discriminant_dependency_narrowed"
            notice_action_discriminant_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_action_discriminant_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_action_stem_detected_before_notice_action_discriminant"
            )
            next_active_dependency = "backend_terminal_notice_action_stem_dependency"
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_stem_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than terminal-notice action-discriminant detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches the terminal-notice action discriminant that proves the notice family, but it still cannot enter before child stdout reaches the earlier terminal-notice action stem that first distinguishes the notice record from the other stream action families, so backend-terminal-notice action-stem detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice action-stem detection as the next exact stream dependency without reopening broader stream interleaving, continuous batching, or cache parity claims"
            )

    return CacheStreamBackendTerminalNoticeActionDiscriminantExactness(
        backend_terminal_notice_prefix_exactness=notice_prefix_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        notice_action_discriminant_status=notice_action_discriminant_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_action_discriminant_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeActionDiscriminantExactness,
) -> dict[str, object]:
    """Serialize backend terminal-notice-action-discriminant exactness."""

    return {
        "contract": {
            "surface": (
                "owlmlx.cache_stream_backend_terminal_notice_action_discriminant_exactness"
            ),
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_action_discriminant",
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
        "backend_terminal_notice_action_discriminant": {
            "notice_action_discriminant_status": exactness.notice_action_discriminant_status,
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
