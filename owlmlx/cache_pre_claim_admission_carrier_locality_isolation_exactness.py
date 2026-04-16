"""Runtime-owned exact locality-isolation boundary for bounded pre-claim admission carriers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_locality_access_exactness import (
    CachePreClaimAdmissionCarrierLocalityAccessExactness,
    build_cache_pre_claim_admission_carrier_locality_access_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierLocalityIsolationExactness:
    """Exact runtime truth for pre-claim admission-carrier locality isolation."""

    locality_access: CachePreClaimAdmissionCarrierLocalityAccessExactness
    status: str
    exactness_rung: str
    locality_isolation_status: str
    allowed_isolation_semantics: tuple[str, ...]
    forbidden_isolation_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_locality_isolation_exactness(
    *,
    locality_access: CachePreClaimAdmissionCarrierLocalityAccessExactness | None = None,
) -> CachePreClaimAdmissionCarrierLocalityIsolationExactness:
    """Build exact pre-claim admission-carrier locality-isolation truth."""

    access = (
        locality_access
        if isinstance(locality_access, CachePreClaimAdmissionCarrierLocalityAccessExactness)
        else build_cache_pre_claim_admission_carrier_locality_access_exactness()
    )

    exactness_rung = "admission_carrier_locality_isolation_unresolved"
    locality_isolation_status = "not_frozen"
    allowed_isolation_semantics = ()
    forbidden_isolation_expansions = ()
    residual_blocker = (
        "pre-claim admission-carrier locality-isolation exactness is not yet frozen because admission-carrier locality-access exactness is not exact"
    )
    recommended_next_step = (
        "freeze admission-carrier locality-access exactness before reducing the remaining cache blocker to exact carrier-locality-isolation semantics"
    )

    if access.exactness_rung == "admission_carrier_locality_access_exact":
        exactness_rung = "admission_carrier_locality_isolation_exact"
        locality_isolation_status = (
            "carrier_isolated_per_staged_request_before_gate_claim"
        )
        allowed_isolation_semantics = (
            "carrier_isolated_per_staged_request_before_gate_claim",
            "no_shared_pending_carrier_pool_before_gate_claim",
            "no_cross_request_carrier_visibility_before_gate_claim",
        )
        forbidden_isolation_expansions = (
            "no_shared_scheduler_pending_carrier_before_claim",
            "no_shared_backend_pending_carrier_before_claim",
            "no_shared_stream_pending_carrier_before_claim",
            "no_cross_request_pending_carrier_merge_before_claim",
        )
        residual_blocker = (
            "the pre-claim admission-carrier locality isolation is now exact: before whole-request gate claim the bounded inert pre-claim carrier remains isolated per staged request, and no shared scheduler/backend/stream pending-state carrier locality or cross-request carrier merge may exist on this path"
        )
        recommended_next_step = (
            "treat batching as admission-carrier locality-lifetime coupling work on this path; if a future carrier expands, freeze how isolated pre-claim carrier locality is reclaimed or expired without turning isolation into hidden queue ownership"
        )

    return CachePreClaimAdmissionCarrierLocalityIsolationExactness(
        locality_access=access,
        status="partial",
        exactness_rung=exactness_rung,
        locality_isolation_status=locality_isolation_status,
        allowed_isolation_semantics=allowed_isolation_semantics,
        forbidden_isolation_expansions=forbidden_isolation_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_carrier_locality_isolation_exactness_to_dict(
    exactness: CachePreClaimAdmissionCarrierLocalityIsolationExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim admission-carrier locality-isolation truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_locality_isolation_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "carrier_locality_isolation_boundary",
                "forbidden_isolation_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "carrier_locality_isolation_boundary": {
            "locality_isolation_status": exactness.locality_isolation_status,
            "allowed_isolation_semantics": list(exactness.allowed_isolation_semantics),
        },
        "forbidden_isolation_expansions": list(
            exactness.forbidden_isolation_expansions
        ),
    }
