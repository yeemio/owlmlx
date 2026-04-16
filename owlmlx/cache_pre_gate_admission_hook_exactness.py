"""Runtime-owned exactness for a bounded pre-gate admission hook."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_gate_cohort_window_feasibility import (
    CachePreGateCohortWindowFeasibility,
    build_cache_pre_gate_cohort_window_feasibility,
)


@dataclass(frozen=True, slots=True)
class CachePreGateAdmissionHookExactness:
    """Exact runtime truth for the next admission-hook blocker."""

    cohort_window_feasibility: CachePreGateCohortWindowFeasibility
    status: str
    exactness_rung: str
    admission_hook_status: str
    owned_boundary_status: str
    preserved_safety_invariants: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_gate_admission_hook_exactness(
    *,
    cohort_window_feasibility: CachePreGateCohortWindowFeasibility | None = None,
) -> CachePreGateAdmissionHookExactness:
    """Build exact pre-gate admission-hook truth for the active path."""

    feasibility = (
        cohort_window_feasibility
        if isinstance(cohort_window_feasibility, CachePreGateCohortWindowFeasibility)
        else build_cache_pre_gate_cohort_window_feasibility()
    )

    exactness_rung = "admission_hook_unresolved"
    admission_hook_status = "not_frozen"
    owned_boundary_status = "not_frozen"
    preserved_safety_invariants = ()
    residual_blocker = (
        "pre-gate admission-hook exactness is not yet frozen because cohort-window feasibility is not exact"
    )
    recommended_next_step = (
        "freeze cohort-window feasibility before reducing the next ingress blocker to admission-hook exactness"
    )

    if feasibility.feasibility_rung == "cohort_window_boundary_exact":
        exactness_rung = "admission_hook_blocker_exact"
        admission_hook_status = "no_bounded_hook_before_gate_claim"
        owned_boundary_status = "whole_request_gate_claim_is_first_runtime_owned_boundary"
        preserved_safety_invariants = (
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        )
        residual_blocker = (
            "a bounded pre-gate admission hook is now the exact next ingress blocker: owlmlx still has no runtime-owned hook before whole-request gate claim, and any new hook must preserve max_concurrent=1, ticketed FIFO discipline after claim, and the validated serial safety boundary that begins only once the gate owns the request"
        )
        recommended_next_step = (
            "treat batching as bounded pre-gate admission-hook work on this path; first define a runtime-owned hook or buffer before whole-request gate claim, while preserving max_concurrent=1 and ticketed FIFO discipline after claim, and keep aggregated child dispatch and stream release secondary"
        )

    return CachePreGateAdmissionHookExactness(
        cohort_window_feasibility=feasibility,
        status="partial",
        exactness_rung=exactness_rung,
        admission_hook_status=admission_hook_status,
        owned_boundary_status=owned_boundary_status,
        preserved_safety_invariants=preserved_safety_invariants,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_gate_admission_hook_exactness_to_dict(
    exactness: CachePreGateAdmissionHookExactness,
) -> dict[str, object]:
    """Serialize exact pre-gate admission-hook truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_gate_admission_hook_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "admission_hook",
                "safety_invariants",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "admission_hook": {
            "admission_hook_status": exactness.admission_hook_status,
            "owned_boundary_status": exactness.owned_boundary_status,
        },
        "safety_invariants": list(exactness.preserved_safety_invariants),
    }
