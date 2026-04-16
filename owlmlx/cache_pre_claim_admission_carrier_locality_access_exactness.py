"""Runtime-owned exact locality-access boundary for bounded pre-claim admission carriers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_locality_exactness import (
    CachePreClaimAdmissionCarrierLocalityExactness,
    build_cache_pre_claim_admission_carrier_locality_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierLocalityAccessExactness:
    """Exact runtime truth for which pre-claim paths may reach a bounded carrier."""

    locality_exactness: CachePreClaimAdmissionCarrierLocalityExactness
    status: str
    exactness_rung: str
    locality_access_status: str
    allowed_access_paths: tuple[str, ...]
    forbidden_access_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_locality_access_exactness(
    *,
    locality_exactness: CachePreClaimAdmissionCarrierLocalityExactness | None = None,
) -> CachePreClaimAdmissionCarrierLocalityAccessExactness:
    """Build exact pre-claim admission-carrier locality-access truth."""

    locality = (
        locality_exactness
        if isinstance(locality_exactness, CachePreClaimAdmissionCarrierLocalityExactness)
        else build_cache_pre_claim_admission_carrier_locality_exactness()
    )

    exactness_rung = "admission_carrier_locality_access_unresolved"
    locality_access_status = "not_frozen"
    allowed_access_paths = ()
    forbidden_access_expansions = ()
    residual_blocker = (
        "pre-claim admission-carrier locality-access exactness is not yet frozen because admission-carrier locality exactness is not exact"
    )
    recommended_next_step = (
        "freeze admission-carrier locality exactness before reducing the remaining cache blocker to exact carrier-locality-access semantics"
    )

    if locality.exactness_rung == "admission_carrier_locality_exact":
        exactness_rung = "admission_carrier_locality_access_exact"
        locality_access_status = (
            "access_limited_to_staging_ticket_and_same_request_pre_claim_paths_before_gate_claim"
        )
        allowed_access_paths = (
            "staged_request_metadata_snapshot_builder_access_before_claim",
            "observational_ticket_reservation_access_before_claim",
            "same_request_pre_claim_drop_cancel_reset_access_before_claim",
            "same_request_pre_claim_discard_observer_access_before_claim",
        )
        forbidden_access_expansions = (
            "no_queue_or_cohort_scheduler_access_before_claim",
            "no_child_backend_payload_access_before_claim",
            "no_stream_handle_access_before_claim",
            "no_execution_entitlement_or_model_runtime_access_before_claim",
        )
        residual_blocker = (
            "the pre-claim admission-carrier locality access is now exact: before whole-request gate claim only staged metadata snapshot building, observational ticket reservation, same-request pre-claim drop/cancel reset, and same-request pre-claim discard observation may reach the bounded inert pre-claim carrier, and queue/cohort scheduler, child/backend payload, stream-handle, or execution-entitlement paths may not access it on this path"
        )
        recommended_next_step = (
            "treat batching as admission-carrier locality-isolation work on this path; if a future carrier expands, freeze whether that bounded inert pre-claim carrier remains isolated per staged request without turning locality access into hidden queue ownership"
        )

    return CachePreClaimAdmissionCarrierLocalityAccessExactness(
        locality_exactness=locality,
        status="partial",
        exactness_rung=exactness_rung,
        locality_access_status=locality_access_status,
        allowed_access_paths=allowed_access_paths,
        forbidden_access_expansions=forbidden_access_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_carrier_locality_access_exactness_to_dict(
    exactness: CachePreClaimAdmissionCarrierLocalityAccessExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim admission-carrier locality-access truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_locality_access_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "carrier_locality_access_boundary",
                "forbidden_access_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "carrier_locality_access_boundary": {
            "locality_access_status": exactness.locality_access_status,
            "allowed_access_paths": list(exactness.allowed_access_paths),
        },
        "forbidden_access_expansions": list(exactness.forbidden_access_expansions),
    }
