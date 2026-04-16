"""Runtime-owned exact locality-lifetime coupling for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_locality_isolation_exactness import (
    CachePreClaimMarkerLocalityIsolationExactness,
    build_cache_pre_claim_marker_locality_isolation_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerLocalityLifetimeCoupling:
    """Exact runtime truth for isolated pre-claim marker locality lifetime."""

    locality_isolation: CachePreClaimMarkerLocalityIsolationExactness
    status: str
    exactness_rung: str
    locality_lifetime_status: str
    reclaim_boundary_status: str
    allowed_lifetime_couplings: tuple[str, ...]
    forbidden_lifetime_coupling_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_locality_lifetime_coupling(
    *,
    locality_isolation: CachePreClaimMarkerLocalityIsolationExactness | None = None,
) -> CachePreClaimMarkerLocalityLifetimeCoupling:
    """Build exact pre-claim marker locality-lifetime coupling truth."""

    isolation = (
        locality_isolation
        if isinstance(locality_isolation, CachePreClaimMarkerLocalityIsolationExactness)
        else build_cache_pre_claim_marker_locality_isolation_exactness()
    )

    exactness_rung = "locality_lifetime_coupling_unresolved"
    locality_lifetime_status = "not_frozen"
    reclaim_boundary_status = "not_frozen"
    allowed_lifetime_couplings = ()
    forbidden_lifetime_coupling_expansions = ()
    residual_blocker = (
        "marker locality-lifetime coupling is not yet frozen because marker locality isolation is not exact"
    )
    recommended_next_step = (
        "freeze marker locality isolation before reducing the remaining cache blocker to exact locality-lifetime coupling"
    )

    if isolation.exactness_rung == "locality_isolation_exact":
        exactness_rung = "locality_lifetime_coupling_exact"
        locality_lifetime_status = (
            "isolated_marker_slot_lifetime_coupled_only_to_own_staged_request_before_gate_claim"
        )
        reclaim_boundary_status = (
            "reclaimed_only_by_same_request_pre_claim_discard_or_gate_claim_expiry_transition"
        )
        allowed_lifetime_couplings = (
            "same_request_pre_claim_drop_cancel_reclaims_isolated_slot",
            "same_request_gate_claim_expiry_reclaims_isolated_slot",
            "no_slot_survives_beyond_own_staged_request_boundary",
        )
        forbidden_lifetime_coupling_expansions = (
            "no_cross_request_slot_reuse_before_reclaim",
            "no_scheduler_extended_slot_lifetime_before_claim",
            "no_backend_stream_retained_slot_lifetime_before_claim",
            "no_execution_entitlement_from_marker_slot_lifetime",
        )
        residual_blocker = (
            "the pre-claim marker locality-lifetime coupling is now exact: the isolated adjacent marker slot is coupled only to its own staged request lifetime before whole-request gate claim, it may be reclaimed only by same-request pre-claim discard or gate-claim expiry transition, and it may not survive into cross-request reuse, scheduler-managed retention, backend/stream retention, or execution entitlement"
        )
        recommended_next_step = (
            "treat batching as marker reclaim-reset exactness work on this path; if a future seam expands, freeze the exact clean-state reset left by reclaim before any later staged request may reuse adjacent locality"
        )

    return CachePreClaimMarkerLocalityLifetimeCoupling(
        locality_isolation=isolation,
        status="partial",
        exactness_rung=exactness_rung,
        locality_lifetime_status=locality_lifetime_status,
        reclaim_boundary_status=reclaim_boundary_status,
        allowed_lifetime_couplings=allowed_lifetime_couplings,
        forbidden_lifetime_coupling_expansions=forbidden_lifetime_coupling_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_locality_lifetime_coupling_to_dict(
    exactness: CachePreClaimMarkerLocalityLifetimeCoupling,
) -> dict[str, object]:
    """Serialize exact pre-claim marker locality-lifetime coupling truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_locality_lifetime_coupling",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "locality_lifetime_coupling",
                "forbidden_lifetime_coupling_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "locality_lifetime_coupling": {
            "locality_lifetime_status": exactness.locality_lifetime_status,
            "reclaim_boundary_status": exactness.reclaim_boundary_status,
            "allowed_lifetime_couplings": list(exactness.allowed_lifetime_couplings),
        },
        "forbidden_lifetime_coupling_expansions": list(
            exactness.forbidden_lifetime_coupling_expansions
        ),
    }
