"""Runtime-owned exact ownership boundary for pre-claim metadata/ticket state."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_staging_seam_exactness import (
    CachePreClaimStagingSeamExactness,
    build_cache_pre_claim_staging_seam_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMetadataTicketOwnership:
    """Exact runtime truth for pre-claim metadata/ticket ownership boundaries."""

    staging_seam_exactness: CachePreClaimStagingSeamExactness
    status: str
    exactness_rung: str
    ticket_ownership_status: str
    metadata_ownership_status: str
    ownership_scope_boundary: str
    forbidden_promotions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_metadata_ticket_ownership(
    *,
    staging_seam_exactness: CachePreClaimStagingSeamExactness | None = None,
) -> CachePreClaimMetadataTicketOwnership:
    """Build exact ownership boundary for pre-claim metadata/ticket state."""

    seam = (
        staging_seam_exactness
        if isinstance(staging_seam_exactness, CachePreClaimStagingSeamExactness)
        else build_cache_pre_claim_staging_seam_exactness()
    )

    exactness_rung = "ownership_unresolved"
    ticket_ownership_status = "not_frozen"
    metadata_ownership_status = "not_frozen"
    ownership_scope_boundary = "not_frozen"
    forbidden_promotions = ()
    residual_blocker = (
        "metadata/ticket ownership exactness is not yet frozen because the pre-claim staging seam is not exact"
    )
    recommended_next_step = (
        "freeze the pre-claim staging seam before reducing the remaining cache blocker to exact metadata/ticket ownership boundaries"
    )

    if seam.exactness_rung == "staging_seam_exact":
        exactness_rung = "ownership_boundary_exact"
        ticket_ownership_status = (
            "reservation_only_no_execution_rights_before_gate_claim"
        )
        metadata_ownership_status = (
            "immutable_snapshot_only_no_mutation_rights_before_gate_claim"
        )
        ownership_scope_boundary = "pre_claim_state_is_inert_until_gate_claim"
        forbidden_promotions = (
            "no_gate_claim_rights_from_ticket_reservation",
            "no_mutable_request_state_from_metadata_snapshot",
            "no_child_or_stream_handle_derivation_before_claim",
            "no_model_execution_entitlement_before_claim",
        )
        residual_blocker = (
            "the pre-claim metadata/ticket ownership boundary is now exact: ticket reservation remains inert and grants no execution rights before gate claim, immutable request metadata remains read-only before gate claim, and neither staged unit may promote into child, stream, or model-execution state before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as inert pre-claim state-boundary work on this path; if a future seam expands, keep ticket reservation observational-only, keep metadata snapshots immutable, and freeze any later cohort/drop semantics without granting execution rights before whole-request gate claim"
        )

    return CachePreClaimMetadataTicketOwnership(
        staging_seam_exactness=seam,
        status="partial",
        exactness_rung=exactness_rung,
        ticket_ownership_status=ticket_ownership_status,
        metadata_ownership_status=metadata_ownership_status,
        ownership_scope_boundary=ownership_scope_boundary,
        forbidden_promotions=forbidden_promotions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_metadata_ticket_ownership_to_dict(
    exactness: CachePreClaimMetadataTicketOwnership,
) -> dict[str, object]:
    """Serialize exact pre-claim metadata/ticket ownership truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_metadata_ticket_ownership",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "ownership_boundary",
                "forbidden_promotions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "ownership_boundary": {
            "ticket_ownership_status": exactness.ticket_ownership_status,
            "metadata_ownership_status": exactness.metadata_ownership_status,
            "ownership_scope_boundary": exactness.ownership_scope_boundary,
        },
        "forbidden_promotions": list(exactness.forbidden_promotions),
    }
