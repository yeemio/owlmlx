"""Runtime-owned exactness for a pre-gate cohort window on the active path."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_gate_admission_hook_harness import PreGateAdmissionHookHarnessResult
from .cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
    build_cache_request_aggregation_window_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreGateCohortWindowFeasibility:
    """Exact feasibility truth for a pre-gate cohort window."""

    aggregation_exactness: CacheRequestAggregationWindowExactness
    status: str
    feasibility_rung: str
    cohort_window_status: str
    gate_boundary_status: str
    serial_safety_constraint: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_gate_cohort_window_feasibility(
    *,
    aggregation_exactness: CacheRequestAggregationWindowExactness | None = None,
    hook_harness: PreGateAdmissionHookHarnessResult | None = None,
) -> CachePreGateCohortWindowFeasibility:
    """Build exact pre-gate cohort window feasibility for the active path."""

    exactness = (
        aggregation_exactness
        if isinstance(aggregation_exactness, CacheRequestAggregationWindowExactness)
        else build_cache_request_aggregation_window_exactness()
    )

    feasibility_rung = "cohort_window_unresolved"
    cohort_window_status = "not_frozen"
    gate_boundary_status = "not_frozen"
    serial_safety_constraint = "not_frozen"
    residual_blocker = (
        "pre-gate cohort window feasibility is not yet exact because request-aggregation exactness is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze request-aggregation exactness before judging whether a pre-gate cohort window is locally expressible"
    )

    if exactness.exactness_rung == "aggregation_window_blocker_exact":
        feasibility_rung = "cohort_window_boundary_exact"
        cohort_window_status = "not_runtime_owned_before_gate_entry"
        gate_boundary_status = "generation_gate_has_no_pre_admission_hook"
        serial_safety_constraint = (
            "serial_safety_validated_only_after_whole_request_gate_claim"
        )
        residual_blocker = (
            "a pre-gate cohort window is not yet locally expressible on the current path: owlmlx only owns queueing once a whole request enters GenerationGate, while the validated serial safety boundary is defined at that whole-request gate claim rather than at a pre-admission cohort boundary"
        )
        recommended_next_step = (
            "treat batching as pre-gate admission-hook work on this path; first introduce a bounded cohort buffer or admission hook ahead of whole-request gate entry while preserving max_concurrent=1 and the validated ticketed FIFO safety boundary after gate claim"
        )
        if (
            hook_harness is not None
            and hook_harness.runtime_owned_hook_present
            and hook_harness.hook_mode == "bounded_runtime_owned_cohort_window"
            and hook_harness.observed_peak_cohort_size >= 2
            and hook_harness.aggregation_scope == "pre_claim_window_only"
        ):
            cohort_window_status = (
                "runtime_owned_bounded_cohort_window_present_before_gate_entry"
            )
            gate_boundary_status = "bounded_pre_admission_window_precedes_gate_claim"
            residual_blocker = (
                "a bounded pre-gate cohort window is now locally expressible and runtime-owned on the active path: multiple requests may form a cohort before whole-request gate claim, while serial safety still remains validated only after claim and request aggregation now reduces to downstream child-exchange and stream-hold dependencies"
            )
            recommended_next_step = (
                "freeze request aggregation at its downstream child/stream dependencies without widening the bounded pre-claim cohort window into aggregated dispatch or post-claim concurrency"
            )

    return CachePreGateCohortWindowFeasibility(
        aggregation_exactness=exactness,
        status="partial",
        feasibility_rung=feasibility_rung,
        cohort_window_status=cohort_window_status,
        gate_boundary_status=gate_boundary_status,
        serial_safety_constraint=serial_safety_constraint,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_gate_cohort_window_feasibility_to_dict(
    feasibility: CachePreGateCohortWindowFeasibility,
) -> dict[str, object]:
    """Serialize exact pre-gate cohort window feasibility."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_gate_cohort_window_feasibility",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "cohort_window",
                "safety_boundary",
            ],
        },
        "summary": {
            "status": feasibility.status,
            "feasibility_rung": feasibility.feasibility_rung,
            "residual_blocker": feasibility.residual_blocker,
            "recommended_next_step": feasibility.recommended_next_step,
        },
        "cohort_window": {
            "cohort_window_status": feasibility.cohort_window_status,
            "gate_boundary_status": feasibility.gate_boundary_status,
        },
        "safety_boundary": {
            "serial_safety_constraint": feasibility.serial_safety_constraint,
        },
    }
