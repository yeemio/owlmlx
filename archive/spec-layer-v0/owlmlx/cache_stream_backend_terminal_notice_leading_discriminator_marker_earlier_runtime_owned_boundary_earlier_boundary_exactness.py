"""Exactness for a new boundary ahead of earlier-runtime-owned boundary stem."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryHarnessResult,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness:
    """Exact truth for introducing a new earlier boundary before boundary stem."""

    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    earlier_runtime_owned_boundary_earlier_boundary_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness(
    *,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness
        | None
    ) = None,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryHarnessResult
        | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness:
    """Build exact truth for the new earlier-boundary introduction."""

    first_unique_boundary_exactness = (
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_unresolved"
    )
    verdict = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_not_introduced"
    )
    earlier_runtime_owned_boundary_earlier_boundary_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency"
    )
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator marker earlier-runtime-owned-boundary earlier-boundary exactness is not yet frozen because boundary first-unique-boundary truth is not exact"
    )
    recommended_next_step = (
        "freeze whether the current earlier-runtime-owned-boundary stem is already the first honest unique boundary before introducing a new earlier runtime-owned boundary"
    )

    if (
        first_unique_boundary_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exact"
        and first_unique_boundary_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency"
    ):
        exactness_rung = (
            "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exact"
        )
        earlier_runtime_owned_boundary_earlier_boundary_status = (
            "earlier_runtime_owned_boundary_earlier_boundary_not_introduced"
        )
        exchange_boundary = (
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_remains_current_exact_boundary"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection"
        )
        preserved_non_stream_handoff_status = (
            first_unique_boundary_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "earlier-runtime-owned-boundary stem detection is already the first honest unique boundary on the newer runtime-owned boundary record, but no distinct earlier runtime-owned boundary record has been proven ahead of it yet, so the live backend stream exchange still owns the serial boundary until earlier-runtime-owned-boundary stem detection"
        )
        recommended_next_step = (
            "either keep earlier-runtime-owned-boundary stem detection frozen as the current exact seam or introduce one new earlier runtime-owned boundary record ahead of it without widening the claim into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness
            is not None
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_visible
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_introduced"
            )
            earlier_runtime_owned_boundary_earlier_boundary_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected_before_boundary_stem_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection"
            )
            residual_blocker = (
                "owlmlx now owns one distinct earlier runtime-owned boundary record ahead of the current earlier-runtime-owned-boundary stem seam: a second backend stream request can be written once child stdout reaches runtime_owned_terminal_earlier_boundary and before child stdout reaches runtime_owned_terminal_b, so the remaining exact stream seam now sits at earlier-runtime-owned-boundary earlier-boundary detection"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary earlier-boundary detection as the current exact stream dependency without inflating this transport-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
            first_unique_boundary_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        earlier_runtime_owned_boundary_earlier_boundary_status=(
            earlier_runtime_owned_boundary_earlier_boundary_status
        ),
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
) -> dict[str, object]:
    """Serialize earlier runtime-owned earlier-boundary exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary",
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
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary": {
            "earlier_runtime_owned_boundary_earlier_boundary_status": (
                exactness.earlier_runtime_owned_boundary_earlier_boundary_status
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
