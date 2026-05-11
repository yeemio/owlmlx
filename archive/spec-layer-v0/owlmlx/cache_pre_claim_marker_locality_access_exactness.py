"""Runtime-owned exact locality-access boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_storage_locality_exactness import (
    CachePreClaimMarkerStorageLocalityExactness,
    build_cache_pre_claim_marker_storage_locality_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerLocalityAccessExactness:
    """Exact runtime truth for pre-claim marker locality access."""

    storage_locality: CachePreClaimMarkerStorageLocalityExactness
    status: str
    exactness_rung: str
    locality_access_status: str
    allowed_access_paths: tuple[str, ...]
    forbidden_access_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_locality_access_exactness(
    *,
    storage_locality: CachePreClaimMarkerStorageLocalityExactness | None = None,
) -> CachePreClaimMarkerLocalityAccessExactness:
    """Build exact pre-claim marker locality-access truth."""

    locality = (
        storage_locality
        if isinstance(storage_locality, CachePreClaimMarkerStorageLocalityExactness)
        else build_cache_pre_claim_marker_storage_locality_exactness()
    )

    exactness_rung = "locality_access_unresolved"
    locality_access_status = "not_frozen"
    allowed_access_paths = ()
    forbidden_access_expansions = ()
    residual_blocker = (
        "marker locality-access exactness is not yet frozen because marker storage locality is not exact"
    )
    recommended_next_step = (
        "freeze marker storage locality before reducing the remaining cache blocker to exact locality-access semantics"
    )

    if locality.exactness_rung == "storage_locality_exact":
        exactness_rung = "locality_access_exact"
        locality_access_status = (
            "access_limited_to_clearers_and_observer_before_gate_claim"
        )
        allowed_access_paths = (
            "explicit_pre_claim_drop_cancel_access",
            "gate_claim_expiry_access",
            "pre_claim_discard_observer_access",
        )
        forbidden_access_expansions = (
            "no_scheduler_locality_access_before_claim",
            "no_child_backend_locality_access_before_claim",
            "no_stream_locality_access_before_claim",
            "no_execution_priority_locality_access_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker locality access is now exact: before whole-request gate claim only explicit pre-claim drop/cancel logic, gate-claim expiry, and pre-claim discard observation may reach the adjacent inert marker slot, and scheduler, child/backend, stream, or execution-priority paths may not access it"
        )
        recommended_next_step = (
            "treat batching as marker locality-isolation work on this path; if a future seam expands, freeze whether the adjacent inert slot is isolated per staged request or could become shared pending state without turning it into hidden queue ownership"
        )

    return CachePreClaimMarkerLocalityAccessExactness(
        storage_locality=locality,
        status="partial",
        exactness_rung=exactness_rung,
        locality_access_status=locality_access_status,
        allowed_access_paths=allowed_access_paths,
        forbidden_access_expansions=forbidden_access_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_locality_access_exactness_to_dict(
    exactness: CachePreClaimMarkerLocalityAccessExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim marker locality-access truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_locality_access_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "locality_access_boundary",
                "forbidden_access_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "locality_access_boundary": {
            "locality_access_status": exactness.locality_access_status,
            "allowed_access_paths": list(exactness.allowed_access_paths),
        },
        "forbidden_access_expansions": list(exactness.forbidden_access_expansions),
    }
