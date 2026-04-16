"""Runtime-owned exact construction boundary for pre-claim admission carriers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_reclaim_reset_exactness import (
    CachePreClaimMarkerReclaimResetExactness,
    build_cache_pre_claim_marker_reclaim_reset_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierConstruction:
    """Exact runtime truth for any bounded pre-claim admission carrier."""

    reclaim_reset: CachePreClaimMarkerReclaimResetExactness
    status: str
    exactness_rung: str
    construction_status: str
    allowed_construction_units: tuple[str, ...]
    forbidden_construction_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_construction(
    *,
    reclaim_reset: CachePreClaimMarkerReclaimResetExactness | None = None,
) -> CachePreClaimAdmissionCarrierConstruction:
    """Build exact pre-claim admission-carrier construction truth."""

    reset = (
        reclaim_reset
        if isinstance(reclaim_reset, CachePreClaimMarkerReclaimResetExactness)
        else build_cache_pre_claim_marker_reclaim_reset_exactness()
    )

    exactness_rung = "admission_carrier_construction_unresolved"
    construction_status = "not_frozen"
    allowed_construction_units = ()
    forbidden_construction_expansions = ()
    residual_blocker = (
        "pre-claim admission-carrier construction is not yet frozen because marker reclaim-reset exactness is not exact"
    )
    recommended_next_step = (
        "freeze marker reclaim-reset exactness before reducing the remaining cache blocker to exact admission-carrier construction"
    )

    if reset.exactness_rung == "reclaim_reset_exact":
        exactness_rung = "admission_carrier_construction_exact"
        construction_status = (
            "bounded_inert_carrier_may_be_constructed_only_from_already_frozen_pre_claim_units"
        )
        allowed_construction_units = (
            "immutable_request_metadata_snapshot",
            "observational_ticket_reservation",
            "fully_reset_inert_marker_slot",
        )
        forbidden_construction_expansions = (
            "no_queue_owned_admission_record_before_claim",
            "no_execution_bearing_carrier_before_claim",
            "no_child_or_stream_attached_carrier_before_claim",
            "no_mutable_scheduler_priority_payload_before_claim",
        )
        residual_blocker = (
            "the pre-claim admission-carrier construction is now exact: before whole-request gate claim owlmlx may construct only a bounded inert carrier from immutable request metadata, observational ticket reservation, and a fully reset inert marker slot, and it may not construct any queue-owned, execution-bearing, child/stream-attached, or scheduler-priority carrier on this path"
        )
        recommended_next_step = (
            "treat batching as admission-carrier field exactness work on this path; if a future carrier expands, freeze which exact fields can inhabit that bounded inert carrier before gate claim without turning it into hidden queue ownership"
        )

    return CachePreClaimAdmissionCarrierConstruction(
        reclaim_reset=reset,
        status="partial",
        exactness_rung=exactness_rung,
        construction_status=construction_status,
        allowed_construction_units=allowed_construction_units,
        forbidden_construction_expansions=forbidden_construction_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_carrier_construction_to_dict(
    exactness: CachePreClaimAdmissionCarrierConstruction,
) -> dict[str, object]:
    """Serialize exact pre-claim admission-carrier construction truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_construction",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "admission_carrier_construction",
                "forbidden_construction_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "admission_carrier_construction": {
            "construction_status": exactness.construction_status,
            "allowed_construction_units": list(exactness.allowed_construction_units),
        },
        "forbidden_construction_expansions": list(
            exactness.forbidden_construction_expansions
        ),
    }
