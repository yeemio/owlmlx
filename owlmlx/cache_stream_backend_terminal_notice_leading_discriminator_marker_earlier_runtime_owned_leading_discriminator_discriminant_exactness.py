"""Runtime-owned exactness for earlier runtime-owned leading-discriminator discriminant narrowing."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantHarnessResult,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness:
    """Exact truth for the earlier runtime-owned leading-discriminator discriminant seam."""

    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    earlier_runtime_owned_leading_discriminator_discriminant_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness(
    *,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness
        | None
    ) = None,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantHarnessResult
        | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness:
    """Build exact truth for the earlier runtime-owned leading-discriminator discriminant seam."""

    earlier_runtime_owned_leading_discriminator_stem_exactness = (
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_unresolved"
    )
    verdict = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency_still_blocked"
    )
    earlier_runtime_owned_leading_discriminator_discriminant_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency"
    )
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator marker earlier runtime-owned leading-discriminator-discriminant exactness is not yet frozen because earlier runtime-owned leading-discriminator-stem truth is not exact"
    )
    recommended_next_step = (
        "freeze backend terminal-notice leading-discriminator marker earlier-runtime-owned-leading-discriminator stem truth before reducing the remaining discriminant seam inside that runtime-owned record"
    )

    if (
        earlier_runtime_owned_leading_discriminator_stem_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exact"
        and earlier_runtime_owned_leading_discriminator_stem_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency"
    ):
        exactness_rung = (
            "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exact"
        )
        earlier_runtime_owned_leading_discriminator_discriminant_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection_visible"
        )
        exchange_boundary = (
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection_remains_current_exact_boundary"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection"
        )
        preserved_non_stream_handoff_status = (
            earlier_runtime_owned_leading_discriminator_stem_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx already owns an earlier runtime-owned leading-discriminator stem ahead of the fuller earlier-runtime-owned-leading-discriminator prefix on this path, but the live backend stream exchange still owns the serial boundary until child stdout reaches the earlier runtime-owned leading-discriminator stem, so that stem detection remains the current exact seam until an earlier discriminant boundary is visibly frozen"
        )
        recommended_next_step = (
            "freeze whether backend-terminal notice leading-discriminator marker earlier-runtime-owned-leading-discriminator discriminant detection is already the next exact stream seam without inflating this runtime-owned narrowing into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness
            is not None
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_boundary_visible
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency_narrowed"
            )
            earlier_runtime_owned_leading_discriminator_discriminant_status = (
                "backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection"
            )
            residual_blocker = (
                "the remaining exact stream seam is now closer than earlier-runtime-owned-leading-discriminator stem detection on this path: a second backend stream request can enter the live backend exchange before child stdout reaches that earlier runtime-owned leading-discriminator stem, but it still cannot enter before child stdout reaches the earlier runtime-owned leading-discriminator discriminant inside the same runtime-owned transport record, so backend-terminal notice leading-discriminator marker earlier-runtime-owned-leading-discriminator discriminant detection is now the active blocker"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator marker earlier-runtime-owned-leading-discriminator discriminant detection as the current exact stream dependency without inflating this runtime-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness=(
            earlier_runtime_owned_leading_discriminator_stem_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        earlier_runtime_owned_leading_discriminator_discriminant_status=(
            earlier_runtime_owned_leading_discriminator_discriminant_status
        ),
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness,
) -> dict[str, object]:
    """Serialize earlier runtime-owned leading-discriminator discriminant exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant",
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
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant": {
            "earlier_runtime_owned_leading_discriminator_discriminant_status": (
                exactness.earlier_runtime_owned_leading_discriminator_discriminant_status
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
