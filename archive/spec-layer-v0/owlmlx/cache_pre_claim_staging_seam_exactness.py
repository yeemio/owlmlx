"""Runtime-owned exactness for the bounded pre-claim staging seam."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_contract import (
    CachePreClaimAdmissionContract,
    build_cache_pre_claim_admission_contract,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimStagingSeamExactness:
    """Exact runtime truth for the only allowable pre-claim staging seam."""

    pre_claim_contract: CachePreClaimAdmissionContract
    status: str
    exactness_rung: str
    allowed_staging_units: tuple[str, ...]
    staging_scope_boundary: str
    forbidden_staging_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_staging_seam_exactness(
    *,
    pre_claim_contract: CachePreClaimAdmissionContract | None = None,
) -> CachePreClaimStagingSeamExactness:
    """Build exact bounded pre-claim staging-seam truth for the active path."""

    contract = (
        pre_claim_contract
        if isinstance(pre_claim_contract, CachePreClaimAdmissionContract)
        else build_cache_pre_claim_admission_contract()
    )

    exactness_rung = "staging_seam_unresolved"
    allowed_staging_units = ()
    staging_scope_boundary = "not_frozen"
    forbidden_staging_expansions = ()
    residual_blocker = (
        "pre-claim staging seam exactness is not yet frozen because the pre-claim admission contract is not exact"
    )
    recommended_next_step = (
        "freeze the pre-claim admission contract before reducing the remaining cache blocker to an exact staging seam"
    )

    if contract.contract_rung == "pre_claim_contract_exact":
        exactness_rung = "staging_seam_exact"
        allowed_staging_units = (
            "immutable_request_metadata_snapshot",
            "ticket_reservation_without_gate_claim",
        )
        staging_scope_boundary = (
            "staging_must_stop_before_first_runtime_owned_gate_boundary"
        )
        forbidden_staging_expansions = (
            "no_gate_ownership_transfer_before_claim",
            "no_child_payload_assembly_before_claim",
            "no_stream_handle_allocation_before_claim",
            "no_model_state_or_prefill_before_claim",
        )
        residual_blocker = (
            "the pre-claim staging seam is now exact: owlmlx may only stage an immutable request-metadata snapshot and ticket reservation before whole-request gate claim, and it may not transfer gate ownership, assemble child payloads, allocate stream handles, or start model state/prefill before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as pre-claim metadata/ticket ownership work on this path; if a future seam is introduced, keep it limited to immutable request metadata plus ticket reservation and leave child, stream, and model execution work behind whole-request gate claim"
        )

    return CachePreClaimStagingSeamExactness(
        pre_claim_contract=contract,
        status="partial",
        exactness_rung=exactness_rung,
        allowed_staging_units=allowed_staging_units,
        staging_scope_boundary=staging_scope_boundary,
        forbidden_staging_expansions=forbidden_staging_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_staging_seam_exactness_to_dict(
    exactness: CachePreClaimStagingSeamExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim staging-seam truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_staging_seam_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "allowed_staging_units",
                "forbidden_staging_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "allowed_staging_units": {
            "allowed_staging_units": list(exactness.allowed_staging_units),
            "staging_scope_boundary": exactness.staging_scope_boundary,
        },
        "forbidden_staging_expansions": list(exactness.forbidden_staging_expansions),
    }
