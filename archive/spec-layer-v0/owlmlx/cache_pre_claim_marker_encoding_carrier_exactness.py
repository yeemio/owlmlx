"""Runtime-owned exact encoding-carrier boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_payload_shape_exactness import (
    CachePreClaimMarkerPayloadShapeExactness,
    build_cache_pre_claim_marker_payload_shape_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerEncodingCarrierExactness:
    """Exact runtime truth for pre-claim marker encoding carrier."""

    payload_shape: CachePreClaimMarkerPayloadShapeExactness
    status: str
    exactness_rung: str
    encoding_carrier_status: str
    allowed_encoding_carrier_semantics: tuple[str, ...]
    forbidden_encoding_carrier_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_encoding_carrier_exactness(
    *,
    payload_shape: CachePreClaimMarkerPayloadShapeExactness | None = None,
) -> CachePreClaimMarkerEncodingCarrierExactness:
    """Build exact pre-claim marker encoding-carrier truth."""

    shape = (
        payload_shape
        if isinstance(payload_shape, CachePreClaimMarkerPayloadShapeExactness)
        else build_cache_pre_claim_marker_payload_shape_exactness()
    )

    exactness_rung = "encoding_carrier_unresolved"
    encoding_carrier_status = "not_frozen"
    allowed_encoding_carrier_semantics = ()
    forbidden_encoding_carrier_expansions = ()
    residual_blocker = (
        "marker encoding-carrier exactness is not yet frozen because marker payload shape is not exact"
    )
    recommended_next_step = (
        "freeze marker payload shape before reducing the remaining cache blocker to exact encoding-carrier semantics"
    )

    if shape.exactness_rung == "payload_shape_exact":
        exactness_rung = "encoding_carrier_exact"
        encoding_carrier_status = "single_inert_boolean_marker_slot_before_gate_claim"
        allowed_encoding_carrier_semantics = (
            "single_boolean_presence_slot_before_gate_claim",
            "absence_means_no_marker_before_gate_claim",
            "encoding_carrier_remains_inert_until_gate_claim",
        )
        forbidden_encoding_carrier_expansions = (
            "no_queue_identity_encoding_before_claim",
            "no_ticket_identity_encoding_before_claim",
            "no_child_payload_encoding_before_claim",
            "no_stream_or_execution_handle_encoding_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker encoding carrier is now exact: before whole-request gate claim marker presence may live only in one inert boolean slot, and that slot may not encode queue identity, ticket identity, child payload, or stream/execution handles"
        )
        recommended_next_step = (
            "treat batching as marker storage-locality work on this path; if a future seam expands, freeze where that inert boolean slot lives relative to staged metadata/ticket units without turning it into hidden queue ownership"
        )

    return CachePreClaimMarkerEncodingCarrierExactness(
        payload_shape=shape,
        status="partial",
        exactness_rung=exactness_rung,
        encoding_carrier_status=encoding_carrier_status,
        allowed_encoding_carrier_semantics=allowed_encoding_carrier_semantics,
        forbidden_encoding_carrier_expansions=forbidden_encoding_carrier_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_encoding_carrier_exactness_to_dict(
    exactness: CachePreClaimMarkerEncodingCarrierExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim marker encoding-carrier truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_encoding_carrier_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "encoding_carrier_boundary",
                "forbidden_encoding_carrier_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "encoding_carrier_boundary": {
            "encoding_carrier_status": exactness.encoding_carrier_status,
            "allowed_encoding_carrier_semantics": list(
                exactness.allowed_encoding_carrier_semantics
            ),
        },
        "forbidden_encoding_carrier_expansions": list(
            exactness.forbidden_encoding_carrier_expansions
        ),
    }
