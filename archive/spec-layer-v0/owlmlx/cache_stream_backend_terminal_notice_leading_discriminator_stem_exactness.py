"""Runtime-owned exactness for backend terminal-notice leading-discriminator stem narrowing."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_stem_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness:
    """Exact truth for the backend terminal-notice leading-discriminator stem seam."""

    backend_terminal_notice_leading_discriminator_prefix_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    leading_discriminator_stem_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness(
    *,
    backend_terminal_notice_leading_discriminator_prefix_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness | None
    ) = None,
    backend_terminal_notice_leading_discriminator_stem_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemHarnessResult | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness:
    """Build exact truth for the leading-discriminator stem seam."""

    leading_discriminator_prefix_exactness = (
        backend_terminal_notice_leading_discriminator_prefix_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_prefix_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness()
    )

    exactness_rung = "stream_backend_terminal_notice_leading_discriminator_stem_unresolved"
    verdict = "backend_terminal_notice_leading_discriminator_prefix_dependency_still_blocked"
    leading_discriminator_stem_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = (
        "backend_terminal_notice_leading_discriminator_prefix_dependency"
    )
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator stem exactness is not yet frozen because leading-discriminator-prefix truth is not exact"
    )
    recommended_next_step = (
        "freeze backend terminal-notice leading-discriminator-prefix truth before reducing the remaining leading-discriminator-stem seam"
    )

    if (
        leading_discriminator_prefix_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_prefix_exact"
        and leading_discriminator_prefix_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_prefix_dependency"
    ):
        exactness_rung = "stream_backend_terminal_notice_leading_discriminator_stem_exact"
        leading_discriminator_stem_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_stem_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_leading_discriminator_stem_detection"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_stem_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_stem_detection"
        )
        preserved_non_stream_handoff_status = (
            leading_discriminator_prefix_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx already owns an earlier runtime-owned leading-discriminator prefix ahead of the full action on this path, but the live backend stream exchange still owns the serial boundary until child stdout reaches the earlier leading-discriminator stem inside that same runtime-owned transport record, so leading-discriminator stem detection is now the next exact stream seam"
        )
        recommended_next_step = (
            "freeze the backend terminal-notice leading-discriminator-stem seam next without inflating this transport-owned narrowing into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_stem_harness is not None
            and backend_terminal_notice_leading_discriminator_stem_harness.backend_terminal_notice_leading_discriminator_stem_boundary_visible
            and backend_terminal_notice_leading_discriminator_stem_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_stem_detected
            and backend_terminal_notice_leading_discriminator_stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_prefix_detected
            and backend_terminal_notice_leading_discriminator_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = (
                "backend_terminal_notice_leading_discriminator_prefix_dependency_narrowed"
            )
            leading_discriminator_stem_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_prefix_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_stem_detected_before_notice_leading_discriminator_prefix_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_stem_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_stem_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than runtime-owned leading-discriminator prefix detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches that internal leading-discriminator prefix, but it still cannot enter before child stdout reaches the earlier leading-discriminator stem inside the same runtime-owned transport record, so backend-terminal notice leading-discriminator stem detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator stem detection as the current exact stream dependency without inflating this runtime-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness(
        backend_terminal_notice_leading_discriminator_prefix_exactness=(
            leading_discriminator_prefix_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        leading_discriminator_stem_status=leading_discriminator_stem_status,
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness,
) -> dict[str, object]:
    """Serialize terminal-notice leading-discriminator stem exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_stem",
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
        "backend_terminal_notice_leading_discriminator_stem": {
            "leading_discriminator_stem_status": (
                exactness.leading_discriminator_stem_status
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
