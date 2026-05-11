"""Runtime-owned exactness for the backend leading-discriminator marker first-unique-boundary seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness:
    """Exact truth for whether marker-discriminant is already the first honest unique boundary."""

    backend_terminal_notice_leading_discriminator_marker_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    leading_discriminator_marker_first_unique_boundary_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness(
    *,
    backend_terminal_notice_leading_discriminator_marker_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness
        | None
    ) = None,
    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryHarnessResult
        | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness:
    """Build exact truth for the current marker-discriminant first-unique-boundary decision."""

    marker_discriminant_exactness = (
        backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_marker_discriminant_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_unresolved"
    )
    verdict = (
        "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency_still_blocked"
    )
    leading_discriminator_marker_first_unique_boundary_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = (
        "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency"
    )
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator marker first-unique-boundary exactness is not yet frozen because leading-discriminator-marker-discriminant truth is not exact"
    )
    recommended_next_step = (
        "freeze backend terminal-notice leading-discriminator marker-discriminant truth before deciding whether that seam is already the first honest unique boundary on the runtime-owned marker-first record"
    )

    if (
        marker_discriminant_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exact"
        and marker_discriminant_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency"
    ):
        exactness_rung = (
            "stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exact"
        )
        leading_discriminator_marker_first_unique_boundary_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_leading_discriminator_marker_discriminant_detection"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection"
        )
        preserved_non_stream_handoff_status = (
            marker_discriminant_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx has already decoupled stream gate release from the fuller runtime-owned terminal_notice_l marker-stem on this path, but the live backend stream exchange still owns the serial boundary until child stdout reaches the first honest unique boundary on the runtime-owned marker-first leading-discriminator record, because the earlier terminal_notice lead-in still collides with the older terminal-notice marker-first record on this path, so leading-discriminator marker-discriminant detection remains the next exact stream seam"
        )
        recommended_next_step = (
            "freeze whether backend-terminal notice leading-discriminator marker-discriminant detection is already the first honest unique boundary on this runtime-owned record before claiming any earlier seam"
        )

        if (
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness
            is not None
            and backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible
            and backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.earlier_prefix_collides_with_old_notice_record
        ):
            leading_discriminator_marker_first_unique_boundary_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_marker_discriminant_is_first_unique_boundary_visible"
            )
            residual_blocker = (
                "the remaining exact stream seam stays at runtime-owned terminal-notice leading-discriminator marker-discriminant detection on this path: the earlier terminal_notice lead-in still collides with the older terminal-notice marker-first record, so marker-discriminant detection is already the first honest unique boundary on the current runtime-owned record and no earlier live seam is yet available"
            )
            recommended_next_step = (
                "either keep backend-terminal notice leading-discriminator marker-discriminant detection frozen as the current exact seam or introduce a new earlier runtime-owned marker-first discriminator ahead of this first unique boundary without widening the claim into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness(
        backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
            marker_discriminant_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        leading_discriminator_marker_first_unique_boundary_status=(
            leading_discriminator_marker_first_unique_boundary_status
        ),
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
) -> dict[str, object]:
    """Serialize backend leading-discriminator marker first-unique-boundary exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_marker_first_unique_boundary",
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
        "backend_terminal_notice_leading_discriminator_marker_first_unique_boundary": {
            "leading_discriminator_marker_first_unique_boundary_status": (
                exactness.leading_discriminator_marker_first_unique_boundary_status
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
