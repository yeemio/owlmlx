"""Runtime-owned exact storage-locality boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_encoding_carrier_exactness import (
    CachePreClaimMarkerEncodingCarrierExactness,
    build_cache_pre_claim_marker_encoding_carrier_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerStorageLocalityExactness:
    """Exact runtime truth for pre-claim marker storage locality."""

    encoding_carrier: CachePreClaimMarkerEncodingCarrierExactness
    status: str
    exactness_rung: str
    storage_locality_status: str
    allowed_storage_locality_semantics: tuple[str, ...]
    forbidden_storage_locality_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_storage_locality_exactness(
    *,
    encoding_carrier: CachePreClaimMarkerEncodingCarrierExactness | None = None,
) -> CachePreClaimMarkerStorageLocalityExactness:
    """Build exact pre-claim marker storage-locality truth."""

    carrier = (
        encoding_carrier
        if isinstance(encoding_carrier, CachePreClaimMarkerEncodingCarrierExactness)
        else build_cache_pre_claim_marker_encoding_carrier_exactness()
    )

    exactness_rung = "storage_locality_unresolved"
    storage_locality_status = "not_frozen"
    allowed_storage_locality_semantics = ()
    forbidden_storage_locality_expansions = ()
    residual_blocker = (
        "marker storage-locality exactness is not yet frozen because marker encoding carrier is not exact"
    )
    recommended_next_step = (
        "freeze marker encoding carrier before reducing the remaining cache blocker to exact storage-locality semantics"
    )

    if carrier.exactness_rung == "encoding_carrier_exact":
        exactness_rung = "storage_locality_exact"
        storage_locality_status = (
            "adjacent_inert_slot_outside_metadata_and_ticket_identity_before_gate_claim"
        )
        allowed_storage_locality_semantics = (
            "adjacent_to_staged_metadata_snapshot_before_gate_claim",
            "not_part_of_ticket_identity_before_gate_claim",
            "not_part_of_immutable_metadata_payload_before_gate_claim",
        )
        forbidden_storage_locality_expansions = (
            "no_queue_cell_locality_before_claim",
            "no_scheduler_bucket_locality_before_claim",
            "no_child_payload_locality_before_claim",
            "no_stream_or_execution_locality_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker storage locality is now exact: before whole-request gate claim the inert boolean marker slot may live only adjacent to staged metadata and outside ticket identity or immutable metadata payload, and it may not occupy queue, scheduler, child, stream, or execution-local storage"
        )
        recommended_next_step = (
            "treat batching as marker locality-access work on this path; if a future seam expands, freeze which pre-claim paths may reach that adjacent inert slot without turning locality into hidden queue ownership"
        )

    return CachePreClaimMarkerStorageLocalityExactness(
        encoding_carrier=carrier,
        status="partial",
        exactness_rung=exactness_rung,
        storage_locality_status=storage_locality_status,
        allowed_storage_locality_semantics=allowed_storage_locality_semantics,
        forbidden_storage_locality_expansions=forbidden_storage_locality_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_storage_locality_exactness_to_dict(
    exactness: CachePreClaimMarkerStorageLocalityExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim marker storage-locality truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_storage_locality_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "storage_locality_boundary",
                "forbidden_storage_locality_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "storage_locality_boundary": {
            "storage_locality_status": exactness.storage_locality_status,
            "allowed_storage_locality_semantics": list(
                exactness.allowed_storage_locality_semantics
            ),
        },
        "forbidden_storage_locality_expansions": list(
            exactness.forbidden_storage_locality_expansions
        ),
    }
