"""Runtime-owned exact field boundary for bounded pre-claim admission carriers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_construction import (
    CachePreClaimAdmissionCarrierConstruction,
    build_cache_pre_claim_admission_carrier_construction,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierFieldExactness:
    """Exact runtime truth for fields inside a bounded pre-claim carrier."""

    construction: CachePreClaimAdmissionCarrierConstruction
    status: str
    exactness_rung: str
    field_status: str
    allowed_field_set: tuple[str, ...]
    forbidden_field_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_field_exactness(
    *,
    construction: CachePreClaimAdmissionCarrierConstruction | None = None,
) -> CachePreClaimAdmissionCarrierFieldExactness:
    """Build exact pre-claim admission-carrier field truth."""

    carrier = (
        construction
        if isinstance(construction, CachePreClaimAdmissionCarrierConstruction)
        else build_cache_pre_claim_admission_carrier_construction()
    )

    exactness_rung = "admission_carrier_field_unresolved"
    field_status = "not_frozen"
    allowed_field_set = ()
    forbidden_field_expansions = ()
    residual_blocker = (
        "pre-claim admission-carrier field exactness is not yet frozen because admission-carrier construction is not exact"
    )
    recommended_next_step = (
        "freeze admission-carrier construction before reducing the remaining cache blocker to exact carrier-field semantics"
    )

    if carrier.exactness_rung == "admission_carrier_construction_exact":
        exactness_rung = "admission_carrier_field_exact"
        field_status = "field_set_limited_to_inert_identity_free_pre_claim_facts"
        allowed_field_set = (
            "immutable_request_metadata_snapshot",
            "observational_ticket_reservation",
            "fully_reset_inert_marker_presence_only",
        )
        forbidden_field_expansions = (
            "no_queue_position_or_queue_identity_field",
            "no_scheduler_priority_or_batch_membership_field",
            "no_child_payload_or_stream_handle_field",
            "no_execution_right_or_prefill_decode_state_field",
        )
        residual_blocker = (
            "the pre-claim admission-carrier field set is now exact: before whole-request gate claim a bounded inert carrier may hold only immutable request metadata, observational ticket reservation, and a fully reset inert marker presence bit, and it may not carry queue identity, scheduler priority, batch membership, child/stream attachment, or execution-bearing state"
        )
        recommended_next_step = (
            "treat batching as admission-carrier field-encoding exactness work on this path; if a future carrier expands, freeze how these inert fields are encoded together before gate claim without turning them into hidden queue ownership"
        )

    return CachePreClaimAdmissionCarrierFieldExactness(
        construction=carrier,
        status="partial",
        exactness_rung=exactness_rung,
        field_status=field_status,
        allowed_field_set=allowed_field_set,
        forbidden_field_expansions=forbidden_field_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_carrier_field_exactness_to_dict(
    exactness: CachePreClaimAdmissionCarrierFieldExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim admission-carrier field truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_field_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "carrier_field_boundary",
                "forbidden_field_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "carrier_field_boundary": {
            "field_status": exactness.field_status,
            "allowed_field_set": list(exactness.allowed_field_set),
        },
        "forbidden_field_expansions": list(exactness.forbidden_field_expansions),
    }
