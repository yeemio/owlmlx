"""Runtime-owned exact locality-isolation boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_locality_access_exactness import (
    CachePreClaimMarkerLocalityAccessExactness,
    build_cache_pre_claim_marker_locality_access_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerLocalityIsolationExactness:
    """Exact runtime truth for pre-claim marker locality isolation."""

    locality_access: CachePreClaimMarkerLocalityAccessExactness
    status: str
    exactness_rung: str
    locality_isolation_status: str
    allowed_isolation_semantics: tuple[str, ...]
    forbidden_isolation_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_locality_isolation_exactness(
    *,
    locality_access: CachePreClaimMarkerLocalityAccessExactness | None = None,
) -> CachePreClaimMarkerLocalityIsolationExactness:
    """Build exact pre-claim marker locality-isolation truth."""

    access = (
        locality_access
        if isinstance(locality_access, CachePreClaimMarkerLocalityAccessExactness)
        else build_cache_pre_claim_marker_locality_access_exactness()
    )

    exactness_rung = "locality_isolation_unresolved"
    locality_isolation_status = "not_frozen"
    allowed_isolation_semantics = ()
    forbidden_isolation_expansions = ()
    residual_blocker = (
        "marker locality-isolation exactness is not yet frozen because marker locality access is not exact"
    )
    recommended_next_step = (
        "freeze marker locality access before reducing the remaining cache blocker to exact locality-isolation semantics"
    )

    if access.exactness_rung == "locality_access_exact":
        exactness_rung = "locality_isolation_exact"
        locality_isolation_status = "isolated_per_staged_request_before_gate_claim"
        allowed_isolation_semantics = (
            "marker_slot_isolated_per_staged_request_before_gate_claim",
            "no_shared_pending_marker_pool_before_gate_claim",
            "no_cross_request_visibility_before_gate_claim",
        )
        forbidden_isolation_expansions = (
            "no_shared_scheduler_pending_slot_before_claim",
            "no_shared_backend_pending_slot_before_claim",
            "no_shared_stream_pending_slot_before_claim",
            "no_cross_request_pending_marker_merge_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker locality isolation is now exact: before whole-request gate claim the adjacent inert marker slot remains isolated per staged request, and no shared scheduler/backend/stream pending-state locality or cross-request marker merge may exist"
        )
        recommended_next_step = (
            "treat batching as marker locality-lifetime coupling work on this path; if a future seam expands, freeze how isolated marker locality is reclaimed or expired without turning isolation into hidden queue ownership"
        )

    return CachePreClaimMarkerLocalityIsolationExactness(
        locality_access=access,
        status="partial",
        exactness_rung=exactness_rung,
        locality_isolation_status=locality_isolation_status,
        allowed_isolation_semantics=allowed_isolation_semantics,
        forbidden_isolation_expansions=forbidden_isolation_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_locality_isolation_exactness_to_dict(
    exactness: CachePreClaimMarkerLocalityIsolationExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim marker locality-isolation truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_locality_isolation_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "locality_isolation_boundary",
                "forbidden_isolation_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "locality_isolation_boundary": {
            "locality_isolation_status": exactness.locality_isolation_status,
            "allowed_isolation_semantics": list(exactness.allowed_isolation_semantics),
        },
        "forbidden_isolation_expansions": list(
            exactness.forbidden_isolation_expansions
        ),
    }
