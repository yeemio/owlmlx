"""Runtime-owned exactness for earlier runtime-owned discriminator introduction."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness:
    """Exact truth for introducing a new earlier runtime-owned discriminator record."""

    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness
    )
    status: str
    exactness_rung: str
    verdict: str
    earlier_runtime_owned_discriminator_status: str
    exchange_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness(
    *,
    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness
        | None
    ) = None,
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorHarnessResult
        | None
    ) = None,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness:
    """Build exact truth for the earlier runtime-owned discriminator round."""

    first_unique_boundary_exactness = (
        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
        if isinstance(
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness,
            CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
        )
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness()
    )

    exactness_rung = (
        "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_unresolved"
    )
    verdict = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_not_introduced"
    )
    earlier_runtime_owned_discriminator_status = "not_frozen"
    exchange_boundary = "not_frozen"
    next_active_dependency = (
        "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency"
    )
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "backend terminal-notice leading-discriminator marker earlier runtime-owned discriminator exactness is not yet frozen because current marker first-unique-boundary truth is not exact"
    )
    recommended_next_step = (
        "freeze whether the current runtime-owned marker-discriminant seam is already the first honest unique boundary before claiming a new earlier runtime-owned discriminator"
    )

    if (
        first_unique_boundary_exactness.exactness_rung
        == "stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exact"
        and first_unique_boundary_exactness.next_active_dependency
        == "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency"
    ):
        exactness_rung = (
            "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exact"
        )
        earlier_runtime_owned_discriminator_status = (
            "earlier_runtime_owned_discriminator_not_introduced"
        )
        exchange_boundary = (
            "backend_terminal_notice_leading_discriminator_marker_discriminant_remains_current_exact_boundary"
        )
        next_active_dependency = (
            "backend_terminal_notice_leading_discriminator_marker_discriminant_dependency"
        )
        next_active_dependency_status = (
            "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection"
        )
        preserved_non_stream_handoff_status = (
            first_unique_boundary_exactness.preserved_non_stream_handoff_status
        )
        residual_blocker = (
            "owlmlx has already frozen runtime-owned leading-discriminator marker-discriminant detection as the first honest unique boundary on the current marker-first record, but no earlier runtime-owned discriminator record exists ahead of that seam yet, so the live backend stream exchange still owns the serial boundary until current marker-discriminant detection"
        )
        recommended_next_step = (
            "either keep the current marker-discriminant seam frozen honestly or introduce one new earlier runtime-owned discriminator record ahead of it without widening the claim into stream interleaving, continuous batching, or cache parity"
        )

        if (
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness
            is not None
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_boundary_visible
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_blocked_before_terminal_window
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_discriminant_detected
            and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_request_written_before_first_terminal_event_consumed
        ):
            verdict = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_introduced"
            )
            earlier_runtime_owned_discriminator_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection_visible"
            )
            exchange_boundary = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected_before_notice_leading_discriminator_marker_discriminant_detection"
            )
            next_active_dependency = (
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency"
            )
            next_active_dependency_status = (
                "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection"
            )
            residual_blocker = (
                "owlmlx now owns a new earlier runtime-owned terminal-notice discriminator record ahead of the current marker-discriminant seam on this path: a second backend stream request can be written once child stdout reaches that new runtime-owned discriminator and before child stdout reaches runtime-owned leading-discriminator marker-discriminant detection, so the remaining exact stream seam now sits at earlier runtime-owned discriminator detection"
            )
            recommended_next_step = (
                "treat backend-terminal notice leading-discriminator marker earlier runtime-owned discriminator detection as the current exact stream dependency without inflating this transport-owned narrowing into stream interleaving, continuous batching, or cache parity"
            )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness(
        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
            first_unique_boundary_exactness
        ),
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        earlier_runtime_owned_discriminator_status=(
            earlier_runtime_owned_discriminator_status
        ),
        exchange_boundary=exchange_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness_to_dict(
    exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness,
) -> dict[str, object]:
    """Serialize earlier runtime-owned discriminator exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator",
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
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator": {
            "earlier_runtime_owned_discriminator_status": (
                exactness.earlier_runtime_owned_discriminator_status
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
