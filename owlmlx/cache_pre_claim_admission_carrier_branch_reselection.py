"""Runtime-owned branch reselection truth after admission-carrier reclaim/reset exactness."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_reclaim_reset_exactness import (
    CachePreClaimAdmissionCarrierReclaimResetExactness,
    build_cache_pre_claim_admission_carrier_reclaim_reset_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierBranchReselection:
    """Exact truth for whether the admission-carrier branch is complete enough to reselect."""

    reclaim_reset_exactness: CachePreClaimAdmissionCarrierReclaimResetExactness
    status: str
    reselection_rung: str
    carrier_branch_status: str
    residual_carrier_subgap: str | None
    next_cache_subbranch: str | None
    preserved_ingress_invariants: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_branch_reselection(
    *,
    reclaim_reset_exactness: CachePreClaimAdmissionCarrierReclaimResetExactness | None = None,
) -> CachePreClaimAdmissionCarrierBranchReselection:
    """Build exact branch-reselection truth for the admission-carrier sub-branch."""

    reclaim_reset = (
        reclaim_reset_exactness
        if isinstance(
            reclaim_reset_exactness,
            CachePreClaimAdmissionCarrierReclaimResetExactness,
        )
        else build_cache_pre_claim_admission_carrier_reclaim_reset_exactness()
    )

    reselection_rung = "carrier_branch_reselection_unresolved"
    carrier_branch_status = "not_reselectable"
    residual_carrier_subgap = (
        "admission_carrier_reclaim_reset_exactness must be frozen before branch reselection"
    )
    next_cache_subbranch = None
    preserved_ingress_invariants = ()
    residual_blocker = (
        "the admission-carrier branch cannot be reselected yet because reclaim/reset exactness is not frozen"
    )
    recommended_next_step = (
        "freeze admission-carrier reclaim/reset exactness before deciding whether the cache branch should reselect away from carrier-local work"
    )

    if reclaim_reset.exactness_rung == "admission_carrier_reclaim_reset_exact":
        reselection_rung = "carrier_branch_reselection_exact"
        carrier_branch_status = "carrier_exactness_chain_complete_on_current_path"
        residual_carrier_subgap = None
        next_cache_subbranch = "scheduler_turboquant_branch_reselection"
        preserved_ingress_invariants = (
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
            "no_bounded_hook_before_gate_claim_without_new_runtime_owned_seam",
        )
        residual_blocker = (
            "the admission-carrier exactness chain is now complete on this path; remaining cache closure moves back to scheduler-vs-TurboQuant branch reselection without regressing the frozen ingress invariants"
        )
        recommended_next_step = (
            "treat cache as scheduler-vs-TurboQuant branch reselection work on this path; the admission-carrier exactness chain is now complete, so any next cache reduction must move outside the carrier-local branch without weakening the already-frozen ingress invariants"
        )

    return CachePreClaimAdmissionCarrierBranchReselection(
        reclaim_reset_exactness=reclaim_reset,
        status="partial",
        reselection_rung=reselection_rung,
        carrier_branch_status=carrier_branch_status,
        residual_carrier_subgap=residual_carrier_subgap,
        next_cache_subbranch=next_cache_subbranch,
        preserved_ingress_invariants=preserved_ingress_invariants,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_carrier_branch_reselection_to_dict(
    reselection: CachePreClaimAdmissionCarrierBranchReselection,
) -> dict[str, object]:
    """Serialize admission-carrier branch reselection truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_branch_reselection",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "branch_status",
                "preserved_ingress_invariants",
            ],
        },
        "summary": {
            "status": reselection.status,
            "reselection_rung": reselection.reselection_rung,
            "residual_blocker": reselection.residual_blocker,
            "recommended_next_step": reselection.recommended_next_step,
        },
        "branch_status": {
            "carrier_branch_status": reselection.carrier_branch_status,
            "residual_carrier_subgap": reselection.residual_carrier_subgap,
            "next_cache_subbranch": reselection.next_cache_subbranch,
        },
        "preserved_ingress_invariants": list(
            reselection.preserved_ingress_invariants
        ),
    }
