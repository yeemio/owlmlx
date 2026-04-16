"""Runtime-owned safety contract for any future pre-gate admission hook."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_gate_admission_hook_exactness import (
    CachePreGateAdmissionHookExactness,
    build_cache_pre_gate_admission_hook_exactness,
)


@dataclass(frozen=True, slots=True)
class CacheAdmissionHookSafetyContract:
    """Exact safety contract for a future bounded admission hook."""

    admission_hook_exactness: CachePreGateAdmissionHookExactness
    status: str
    contract_rung: str
    preserved_post_claim_invariants: tuple[str, ...]
    forbidden_bypasses: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_admission_hook_safety_contract(
    *,
    admission_hook_exactness: CachePreGateAdmissionHookExactness | None = None,
) -> CacheAdmissionHookSafetyContract:
    """Build the exact safety contract for any future admission hook."""

    exactness = (
        admission_hook_exactness
        if isinstance(admission_hook_exactness, CachePreGateAdmissionHookExactness)
        else build_cache_pre_gate_admission_hook_exactness()
    )

    contract_rung = "safety_contract_unresolved"
    preserved_post_claim_invariants = ()
    forbidden_bypasses = ()
    residual_blocker = (
        "admission-hook safety contract is not yet exact because admission-hook exactness is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze admission-hook exactness before defining the exact safety contract any future hook must preserve"
    )

    if exactness.exactness_rung == "admission_hook_blocker_exact":
        contract_rung = "safety_contract_exact"
        preserved_post_claim_invariants = (
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        )
        forbidden_bypasses = (
            "no_bypass_of_whole_request_gate_claim",
            "no_reordering_after_gate_claim",
            "no_post_claim_parallel_generation",
        )
        residual_blocker = (
            "the admission-hook safety contract is now exact: any future bounded hook must stop before whole-request gate claim, must not bypass the gate as the first runtime-owned boundary, must not reorder requests after claim, and must not weaken the validated post-claim serial generation discipline"
        )
        recommended_next_step = (
            "treat batching as a pre-claim admission-contract problem on this path; define a hook/buffer that stays outside whole-request gate claim, preserves FIFO order once claim occurs, and never weakens max_concurrent=1 after claim"
        )

    return CacheAdmissionHookSafetyContract(
        admission_hook_exactness=exactness,
        status="partial",
        contract_rung=contract_rung,
        preserved_post_claim_invariants=preserved_post_claim_invariants,
        forbidden_bypasses=forbidden_bypasses,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_admission_hook_safety_contract_to_dict(
    contract: CacheAdmissionHookSafetyContract,
) -> dict[str, object]:
    """Serialize the exact admission-hook safety contract."""

    return {
        "contract": {
            "surface": "owlmlx.cache_admission_hook_safety_contract",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "preserved_post_claim_invariants",
                "forbidden_bypasses",
            ],
        },
        "summary": {
            "status": contract.status,
            "contract_rung": contract.contract_rung,
            "residual_blocker": contract.residual_blocker,
            "recommended_next_step": contract.recommended_next_step,
        },
        "preserved_post_claim_invariants": list(
            contract.preserved_post_claim_invariants
        ),
        "forbidden_bypasses": list(contract.forbidden_bypasses),
    }
