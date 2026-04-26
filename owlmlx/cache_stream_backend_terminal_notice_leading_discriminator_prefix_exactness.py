"""Runtime-owned exactness for backend terminal-notice leading-discriminator prefix narrowing."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_prefix_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness:
    """Exact truth for the backend terminal-notice leading-discriminator prefix seam."""

    backend_terminal_notice_leading_discriminator_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    leading_discriminator_prefix_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness(
    *,
    backend_terminal_notice_leading_discriminator_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness | None
    ) = None,
    backend_terminal_notice_leading_discriminator_prefix_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness:
    """Build exact truth for the leading-discriminator prefix seam."""

    leading_discriminator_exactness = (
        backend_terminal_notice_leading_discriminator_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_prefix_unresolved"
    )
    verdict = "backend_terminal_notice_leading_discriminator_dependency_still_blocked"
    leading_discriminator_prefix_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = "backend_terminal_notice_leading_discriminator_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator prefix exactness is not yet frozen because leading-discriminator truth is not exact"
    )
    recommended_next_step = (
        "freeze backend terminal-notice leading-discriminator truth before reducing the remaining leading-discriminator-prefix seam"
    )

    if (
        leading_discriminator_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_exact"
        and leading_discriminator_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_leading_discriminator_prefix_exact"
        leading_discriminator_prefix_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_prefix_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_leading_discriminator_prefix_detection"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_prefix_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_prefix_detection"
        )
        preserved_non_stream_handoff_status = (
            leading_discriminator_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx already owns a runtime-owned terminal-notice leading discriminator ahead of the old marker-key lead on this path, but the live backend stream exchange still owns the serial boundary until child stdout fully matches that internal leading-discriminator action, so leading-discriminator prefix detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice leading-discriminator-prefix seam next without inflating this transport-owned narrowing into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_prefix_harness is not None
            and backend_terminal_notice_leading_discriminator_prefix_harness.backend_terminal_notice_leading_discriminator_prefix_boundary_visible
            and backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_prefix_detected
            and backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_detected
            and backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = "backend_terminal_notice_leading_discriminator_dependency_narrowed"
            leading_discriminator_prefix_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_prefix_detected_before_notice_leading_discriminator_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_prefix_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_prefix_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than full terminal-notice leading-discriminator detection on this path: a second backend stream request can enter the live backend exchange before child stdout fully matches the runtime-owned leading-discriminator action, but it still cannot enter before child stdout reaches the earlier leading-discriminator prefix inside that internal transport record, so backend-terminal notice leading-discriminator prefix detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator prefix detection as the current exact stream dependency without inflating this runtime-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness(
        backend_terminal_notice_leading_discriminator_exactness=(
            leading_discriminator_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        leading_discriminator_prefix_status=leading_discriminator_prefix_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness,
) -> dict[str, object]:
    """Serialize terminal-notice leading-discriminator prefix exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_prefix",
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
        "backend_terminal_notice_leading_discriminator_prefix": {
            "leading_discriminator_prefix_status": (
                exactness.leading_discriminator_prefix_status
            ),
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
