"""Exactness for the first honest unique boundary on the new earlier-boundary record."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness:
    """Exact truth for whether the earlier-boundary key is already the first honest unique boundary."""

    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness(
    *,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness
        | None
    ) = None,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryHarnessResult
        | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness:
    """Build exact truth for the earlier-boundary first-unique-boundary decision."""

    earlier_boundary_exactness = (
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_unresolved"
    )
    verdict = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency_still_blocked"
    )
    earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency"
    )
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator marker earlier-runtime-owned-boundary earlier-boundary first-unique-boundary exactness is not yet frozen because earlier-boundary truth is not exact"
    )
    recommended_next_step = (
        "freeze backend terminal-notice leading-discriminator marker earlier-runtime-owned-boundary earlier-boundary truth before deciding whether that seam is already the first honest unique boundary on the newer earlier-boundary record"
    )

    if (
        earlier_boundary_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exact"
        and earlier_boundary_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency"
    ):
        exactness_rung = (
            "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exact"
        )
        earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection"
        )
        exchange_boundary = (
            "backend_stream_exchange_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection"
        )
        preserved_non_stream_handoff_status = (
            earlier_boundary_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx has already introduced one distinct earlier runtime-owned boundary record (runtime_owned_terminal_earlier_boundary) ahead of the previous earlier-runtime-owned-boundary stem (runtime_owned_terminal_b), but the live backend stream exchange still owns the serial boundary until child stdout reaches the first honest unique boundary on this newer earlier-boundary record, so earlier-boundary detection remains the current exact seam unless one even earlier runtime-owned record is introduced"
        )
        recommended_next_step = (
            "freeze whether backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary earlier-boundary detection is already the first honest unique boundary on the newer earlier-boundary record before claiming any earlier seam"
        )

        if (
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness
            is not None
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_visible
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness.earlier_literal_prefix_is_not_runtime_owned_earlier_boundary
        ):
            earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_is_first_honest_unique_boundary_visible"
            )
            residual_blocker = (
                "owlmlx already owns one distinct earlier runtime-owned boundary record (runtime_owned_terminal_earlier_boundary) ahead of the previous boundary stem (runtime_owned_terminal_b), and the remaining exact stream seam stays at earlier-runtime-owned-boundary earlier-boundary detection on this path: the literal prefix before runtime_owned_terminal_earlier_b is not yet an honest runtime-owned transport boundary, so earlier-boundary detection is already the first honest unique boundary on the newer earlier-boundary record and no earlier live seam is yet available"
            )
            recommended_next_step = (
                "either keep backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary earlier-boundary detection frozen as the current exact seam or introduce one new earlier runtime-owned record ahead of this first honest unique boundary without widening the claim into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
            earlier_boundary_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status=(
            earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status
        ),
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness,
) -> dict[str, object]:
    """Serialize earlier-runtime-owned earlier-boundary first-unique-boundary exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary",
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
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary": {
            "earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status": (
                exactness.earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status
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
