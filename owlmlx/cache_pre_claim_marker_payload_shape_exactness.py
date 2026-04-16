"""Runtime-owned exact payload-shape boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_immutability_boundary import (
    CachePreClaimMarkerImmutabilityBoundary,
    build_cache_pre_claim_marker_immutability_boundary,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerPayloadShapeExactness:
    """Exact runtime truth for pre-claim marker payload shape."""

    immutability_boundary: CachePreClaimMarkerImmutabilityBoundary
    status: str
    exactness_rung: str
    payload_shape_status: str
    allowed_payload_semantics: tuple[str, ...]
    forbidden_payload_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_payload_shape_exactness(
    *,
    immutability_boundary: CachePreClaimMarkerImmutabilityBoundary | None = None,
) -> CachePreClaimMarkerPayloadShapeExactness:
    """Build exact pre-claim marker payload-shape truth."""

    boundary = (
        immutability_boundary
        if isinstance(
            immutability_boundary, CachePreClaimMarkerImmutabilityBoundary
        )
        else build_cache_pre_claim_marker_immutability_boundary()
    )

    exactness_rung = "payload_shape_unresolved"
    payload_shape_status = "not_frozen"
    allowed_payload_semantics = ()
    forbidden_payload_expansions = ()
    residual_blocker = (
        "marker payload-shape exactness is not yet frozen because marker immutability is not exact"
    )
    recommended_next_step = (
        "freeze marker immutability before reducing the remaining cache blocker to exact payload-shape semantics"
    )

    if boundary.exactness_rung == "immutability_boundary_exact":
        exactness_rung = "payload_shape_exact"
        payload_shape_status = "presence_absence_only_before_gate_claim"
        allowed_payload_semantics = (
            "marker_presence_bit_only_before_gate_claim",
            "no_pre_claim_payload_fields_beyond_presence_absence",
        )
        forbidden_payload_expansions = (
            "no_reason_code_payload_before_claim",
            "no_priority_payload_before_claim",
            "no_queue_metadata_payload_before_claim",
            "no_child_stream_execution_payload_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker payload shape is now exact: before whole-request gate claim marker state collapses to pure presence/absence only, and no reason-code, priority, queue-metadata, or child/stream/execution payload fields may exist"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker encoding work on this path; if a future seam expands, freeze the exact inert encoding carrier and prove it still carries only presence/absence before whole-request gate claim"
        )

    return CachePreClaimMarkerPayloadShapeExactness(
        immutability_boundary=boundary,
        status="partial",
        exactness_rung=exactness_rung,
        payload_shape_status=payload_shape_status,
        allowed_payload_semantics=allowed_payload_semantics,
        forbidden_payload_expansions=forbidden_payload_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_payload_shape_exactness_to_dict(
    exactness: CachePreClaimMarkerPayloadShapeExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim marker payload-shape truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_payload_shape_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "payload_shape_boundary",
                "forbidden_payload_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "payload_shape_boundary": {
            "payload_shape_status": exactness.payload_shape_status,
            "allowed_payload_semantics": list(exactness.allowed_payload_semantics),
        },
        "forbidden_payload_expansions": list(exactness.forbidden_payload_expansions),
    }
