"""Runtime-owned exact pre-claim admission contract for the active path."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_admission_hook_safety_contract import (
    CacheAdmissionHookSafetyContract,
    build_cache_admission_hook_safety_contract,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionContract:
    """Exact contract for any future pre-claim admission seam."""

    safety_contract: CacheAdmissionHookSafetyContract
    status: str
    contract_rung: str
    possible_pre_claim_seam: str
    pre_claim_scope_limit: str
    forbidden_pre_claim_actions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_contract(
    *,
    safety_contract: CacheAdmissionHookSafetyContract | None = None,
) -> CachePreClaimAdmissionContract:
    """Build exact pre-claim admission contract truth for the active path."""

    contract = (
        safety_contract
        if isinstance(safety_contract, CacheAdmissionHookSafetyContract)
        else build_cache_admission_hook_safety_contract()
    )

    contract_rung = "pre_claim_contract_unresolved"
    possible_pre_claim_seam = "not_frozen"
    pre_claim_scope_limit = "not_frozen"
    forbidden_pre_claim_actions = ()
    residual_blocker = (
        "pre-claim admission contract is not yet exact because the admission-hook safety contract is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze the admission-hook safety contract before defining the exact pre-claim admission contract"
    )

    if contract.contract_rung == "safety_contract_exact":
        contract_rung = "pre_claim_contract_exact"
        possible_pre_claim_seam = "bounded_metadata_or_ticket_staging_before_gate_claim"
        pre_claim_scope_limit = "may_stage_only_before_first_runtime_owned_gate_boundary"
        forbidden_pre_claim_actions = (
            "no_gate_claim_from_pre_claim_seam",
            "no_child_exchange_from_pre_claim_seam",
            "no_stream_start_from_pre_claim_seam",
            "no_model_execution_from_pre_claim_seam",
        )
        residual_blocker = (
            "the pre-claim admission contract is now exact: owlmlx may only define a bounded metadata/ticket staging seam before whole-request gate claim, and that seam may not claim the gate, start child exchange, start streaming, or execute model work before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as pre-claim staging-contract work on this path; if a future admission seam is introduced, keep it limited to bounded metadata/ticket staging before gate claim and preserve the exact post-claim safety contract unchanged"
        )

    return CachePreClaimAdmissionContract(
        safety_contract=contract,
        status="partial",
        contract_rung=contract_rung,
        possible_pre_claim_seam=possible_pre_claim_seam,
        pre_claim_scope_limit=pre_claim_scope_limit,
        forbidden_pre_claim_actions=forbidden_pre_claim_actions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_contract_to_dict(
    contract: CachePreClaimAdmissionContract,
) -> dict[str, object]:
    """Serialize exact pre-claim admission contract truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_contract",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "possible_pre_claim_seam",
                "forbidden_pre_claim_actions",
            ],
        },
        "summary": {
            "status": contract.status,
            "contract_rung": contract.contract_rung,
            "residual_blocker": contract.residual_blocker,
            "recommended_next_step": contract.recommended_next_step,
        },
        "possible_pre_claim_seam": {
            "possible_pre_claim_seam": contract.possible_pre_claim_seam,
            "pre_claim_scope_limit": contract.pre_claim_scope_limit,
        },
        "forbidden_pre_claim_actions": list(contract.forbidden_pre_claim_actions),
    }
