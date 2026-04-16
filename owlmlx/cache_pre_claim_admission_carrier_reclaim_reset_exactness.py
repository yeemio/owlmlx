"""Runtime-owned exact reclaim-reset semantics for bounded pre-claim admission carriers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_locality_lifetime_coupling import (
    CachePreClaimAdmissionCarrierLocalityLifetimeCoupling,
    build_cache_pre_claim_admission_carrier_locality_lifetime_coupling,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierReclaimResetExactness:
    """Exact runtime truth for pre-claim admission-carrier reclaim/reset semantics."""

    locality_lifetime_coupling: CachePreClaimAdmissionCarrierLocalityLifetimeCoupling
    status: str
    exactness_rung: str
    reclaim_reset_status: str
    reset_boundary_status: str
    allowed_reset_semantics: tuple[str, ...]
    forbidden_reset_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_reclaim_reset_exactness(
    *,
    locality_lifetime_coupling: CachePreClaimAdmissionCarrierLocalityLifetimeCoupling
    | None = None,
) -> CachePreClaimAdmissionCarrierReclaimResetExactness:
    """Build exact pre-claim admission-carrier reclaim/reset truth."""

    coupling = (
        locality_lifetime_coupling
        if isinstance(
            locality_lifetime_coupling,
            CachePreClaimAdmissionCarrierLocalityLifetimeCoupling,
        )
        else build_cache_pre_claim_admission_carrier_locality_lifetime_coupling()
    )

    exactness_rung = "admission_carrier_reclaim_reset_unresolved"
    reclaim_reset_status = "not_frozen"
    reset_boundary_status = "not_frozen"
    allowed_reset_semantics = ()
    forbidden_reset_expansions = ()
    residual_blocker = (
        "pre-claim admission-carrier reclaim-reset exactness is not yet frozen because admission-carrier locality-lifetime coupling is not exact"
    )
    recommended_next_step = (
        "freeze admission-carrier locality-lifetime coupling before reducing the remaining cache blocker to exact carrier reclaim-reset semantics"
    )

    if (
        coupling.exactness_rung
        == "admission_carrier_locality_lifetime_coupling_exact"
    ):
        exactness_rung = "admission_carrier_reclaim_reset_exact"
        reclaim_reset_status = (
            "reclaim_resets_bounded_inert_carrier_to_fully_empty_state_before_reuse"
        )
        reset_boundary_status = (
            "reuse_allowed_only_after_empty_reset_without_history_or_execution_state"
        )
        allowed_reset_semantics = (
            "reclaim_clears_inert_carrier_presence_to_empty_state",
            "no_prior_request_history_visible_after_carrier_reclaim",
            "later_staged_request_may_reuse_only_after_empty_carrier_reset",
        )
        forbidden_reset_expansions = (
            "no_reuse_with_stale_carrier_history",
            "no_partial_reset_leaving_scheduler_or_backend_hints",
            "no_cross_request_transfer_of_reclaim_reason",
            "no_execution_priority_or_queue_state_retained_after_carrier_reclaim",
        )
        residual_blocker = (
            "the pre-claim admission-carrier reclaim-reset semantics are now exact: reclaim clears the bounded inert pre-claim carrier back to an empty inert state, no prior request history or reclaim reason remains visible after reclaim, and later staged requests may reuse adjacent locality only after a fully inert reset with no scheduler/backend/stream/execution residue"
        )
        recommended_next_step = (
            "treat cache as admission-carrier branch reselection work on this path; the carrier reclaim/reset chain is now exact, so either freeze the next residual carrier subgap explicitly or reselect the dominant cache sub-branch without regressing the already-frozen ingress invariants"
        )

    return CachePreClaimAdmissionCarrierReclaimResetExactness(
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


def cache_pre_claim_admission_carrier_reclaim_reset_exactness_to_dict(
    exactness: CachePreClaimAdmissionCarrierReclaimResetExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim admission-carrier reclaim/reset truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness",
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
