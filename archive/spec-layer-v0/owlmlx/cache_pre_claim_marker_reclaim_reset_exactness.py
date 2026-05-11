"""Runtime-owned exact reclaim-reset semantics for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_locality_lifetime_coupling import (
    CachePreClaimMarkerLocalityLifetimeCoupling,
    build_cache_pre_claim_marker_locality_lifetime_coupling,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerReclaimResetExactness:
    """Exact runtime truth for pre-claim marker reclaim/reset semantics."""

    locality_lifetime_coupling: CachePreClaimMarkerLocalityLifetimeCoupling
    status: str
    exactness_rung: str
    reclaim_reset_status: str
    reset_boundary_status: str
    allowed_reset_semantics: tuple[str, ...]
    forbidden_reset_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_reclaim_reset_exactness(
    *,
    locality_lifetime_coupling: CachePreClaimMarkerLocalityLifetimeCoupling | None = None,
) -> CachePreClaimMarkerReclaimResetExactness:
    """Build exact pre-claim marker reclaim/reset truth."""

    coupling = (
        locality_lifetime_coupling
        if isinstance(
            locality_lifetime_coupling, CachePreClaimMarkerLocalityLifetimeCoupling
        )
        else build_cache_pre_claim_marker_locality_lifetime_coupling()
    )

    exactness_rung = "reclaim_reset_unresolved"
    reclaim_reset_status = "not_frozen"
    reset_boundary_status = "not_frozen"
    allowed_reset_semantics = ()
    forbidden_reset_expansions = ()
    residual_blocker = (
        "marker reclaim-reset exactness is not yet frozen because marker locality-lifetime coupling is not exact"
    )
    recommended_next_step = (
        "freeze marker locality-lifetime coupling before reducing the remaining cache blocker to exact reclaim-reset semantics"
    )

    if coupling.exactness_rung == "locality_lifetime_coupling_exact":
        exactness_rung = "reclaim_reset_exact"
        reclaim_reset_status = (
            "reclaim_resets_adjacent_marker_slot_to_fully_inert_empty_state_before_reuse"
        )
        reset_boundary_status = (
            "reuse_allowed_only_after_empty_reset_without_history_or_execution_state"
        )
        allowed_reset_semantics = (
            "reclaim_clears_marker_presence_bit_to_empty_state",
            "no_prior_request_history_visible_after_reclaim",
            "later_staged_request_may_reuse_only_after_empty_reset",
        )
        forbidden_reset_expansions = (
            "no_reuse_with_stale_marker_history",
            "no_partial_reset_leaving_scheduler_or_backend_hints",
            "no_cross_request_transfer_of_reclaim_reason",
            "no_execution_priority_or_queue_state_retained_after_reclaim",
        )
        residual_blocker = (
            "the pre-claim marker reclaim-reset semantics are now exact: reclaim clears the adjacent inert marker slot back to an empty inert state, no prior request history or reclaim reason remains visible after reclaim, and later staged requests may reuse that locality only after a fully inert reset with no scheduler/backend/stream/execution residue"
        )
        recommended_next_step = (
            "treat batching as pre-claim admission-carrier construction work on this path; if a future seam expands, freeze how any bounded admission record is created before gate claim without turning reset state into hidden queue ownership"
        )

    return CachePreClaimMarkerReclaimResetExactness(
        locality_lifetime_coupling=coupling,
        status="partial",
        exactness_rung=exactness_rung,
        reclaim_reset_status=reclaim_reset_status,
        reset_boundary_status=reset_boundary_status,
        allowed_reset_semantics=allowed_reset_semantics,
        forbidden_reset_expansions=forbidden_reset_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_reclaim_reset_exactness_to_dict(
    exactness: CachePreClaimMarkerReclaimResetExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim marker reclaim/reset truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_reclaim_reset_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "reclaim_reset_boundary",
                "forbidden_reset_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "reclaim_reset_boundary": {
            "reclaim_reset_status": exactness.reclaim_reset_status,
            "reset_boundary_status": exactness.reset_boundary_status,
            "allowed_reset_semantics": list(exactness.allowed_reset_semantics),
        },
        "forbidden_reset_expansions": list(exactness.forbidden_reset_expansions),
    }
