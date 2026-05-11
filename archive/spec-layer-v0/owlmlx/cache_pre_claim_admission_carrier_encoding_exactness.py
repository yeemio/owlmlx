"""Runtime-owned exact encoding boundary for bounded pre-claim admission carriers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_field_exactness import (
    CachePreClaimAdmissionCarrierFieldExactness,
    build_cache_pre_claim_admission_carrier_field_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierEncodingExactness:
    """Exact runtime truth for encoding inert pre-claim carrier fields."""

    field_exactness: CachePreClaimAdmissionCarrierFieldExactness
    status: str
    exactness_rung: str
    encoding_status: str
    allowed_combined_encodings: tuple[str, ...]
    forbidden_encoding_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_encoding_exactness(
    *,
    field_exactness: CachePreClaimAdmissionCarrierFieldExactness | None = None,
) -> CachePreClaimAdmissionCarrierEncodingExactness:
    """Build exact pre-claim admission-carrier encoding truth."""

    fields = (
        field_exactness
        if isinstance(field_exactness, CachePreClaimAdmissionCarrierFieldExactness)
        else build_cache_pre_claim_admission_carrier_field_exactness()
    )

    exactness_rung = "admission_carrier_encoding_unresolved"
    encoding_status = "not_frozen"
    allowed_combined_encodings = ()
    forbidden_encoding_expansions = ()
    residual_blocker = (
        "pre-claim admission-carrier encoding exactness is not yet frozen because admission-carrier field exactness is not exact"
    )
    recommended_next_step = (
        "freeze admission-carrier field exactness before reducing the remaining cache blocker to exact carrier-encoding semantics"
    )

    if fields.exactness_rung == "admission_carrier_field_exact":
        exactness_rung = "admission_carrier_encoding_exact"
        encoding_status = (
            "fields_encode_only_as_one_bounded_inert_pre_claim_record_before_gate_claim"
        )
        allowed_combined_encodings = (
            "immutable_metadata_snapshot_plus_observational_ticket_reservation",
            "fully_reset_inert_marker_presence_bit_in_same_bounded_record",
            "no_field_combination_grants_identity_or_execution_rights",
        )
        forbidden_encoding_expansions = (
            "no_queue_identity_or_position_encoding",
            "no_scheduler_priority_or_batch_membership_encoding",
            "no_child_payload_or_stream_handle_encoding",
            "no_execution_entitlement_or_prefill_decode_encoding",
        )
        residual_blocker = (
            "the pre-claim admission-carrier encoding is now exact: before whole-request gate claim immutable request metadata, observational ticket reservation, and a fully reset inert marker presence bit may be encoded only as one bounded inert pre-claim record, and no combined encoding may smuggle queue identity, scheduler priority, batch membership, child/stream attachment, or execution-bearing state"
        )
        recommended_next_step = (
            "treat batching as admission-carrier locality exactness work on this path; if a future carrier expands, freeze where that bounded inert record may live before gate claim without turning encoding into hidden queue ownership"
        )

    return CachePreClaimAdmissionCarrierEncodingExactness(
        field_exactness=fields,
        status="partial",
        exactness_rung=exactness_rung,
        encoding_status=encoding_status,
        allowed_combined_encodings=allowed_combined_encodings,
        forbidden_encoding_expansions=forbidden_encoding_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_carrier_encoding_exactness_to_dict(
    exactness: CachePreClaimAdmissionCarrierEncodingExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim admission-carrier encoding truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_encoding_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "carrier_encoding_boundary",
                "forbidden_encoding_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "carrier_encoding_boundary": {
            "encoding_status": exactness.encoding_status,
            "allowed_combined_encodings": list(exactness.allowed_combined_encodings),
        },
        "forbidden_encoding_expansions": list(exactness.forbidden_encoding_expansions),
    }
