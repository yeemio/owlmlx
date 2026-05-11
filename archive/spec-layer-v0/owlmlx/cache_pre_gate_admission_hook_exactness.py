"""Runtime-owned exactness for a bounded pre-gate admission hook."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_gate_cohort_window_feasibility import (
    CachePreGateCohortWindowFeasibility,
    build_cache_pre_gate_cohort_window_feasibility,
)
from .cache_pre_gate_admission_hook_harness import PreGateAdmissionHookHarnessResult


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
    hook_harness: PreGateAdmissionHookHarnessResult | None = None,
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
        preserved_safety_invariants = (
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        )
        if (
            hook_harness is not None
            and hook_harness.runtime_owned_hook_present
            and hook_harness.hook_boundary == "before_whole_request_gate_claim"
            and hook_harness.observed_total_staged >= 1
            and hook_harness.observed_total_claimed >= 1
        ):
            if (
                hook_harness.hook_mode == "bounded_runtime_owned_cohort_window"
                and hook_harness.observed_peak_cohort_size >= 2
                and hook_harness.observed_total_cohorts_formed >= 1
                and hook_harness.aggregation_scope == "pre_claim_window_only"
            ):
                admission_hook_status = (
                    "bounded_request_aggregation_window_present_before_gate_claim"
                )
                owned_boundary_status = (
                    "bounded_cohort_window_precedes_whole_request_gate_claim_without_gate_transfer"
                )
                residual_blocker = (
                    "the pre-gate admission hook has now widened into a bounded runtime-owned request-aggregation window on the active path: multiple requests may form a pre-claim cohort before whole-request gate claim, but the widened hook still carries no post-claim execution bypass and downstream child/stream dependencies remain"
                )
                recommended_next_step = (
                    "treat request aggregation as downstream dependency reduction on this path; preserve the bounded pre-claim cohort window, keep child dispatch and stream hold secondary-to-active, and do not inflate this seam into continuous batching or parity"
                )
            else:
                admission_hook_status = (
                    "bounded_hook_present_but_no_request_aggregation_window"
                )
                owned_boundary_status = (
                    "bounded_hook_precedes_whole_request_gate_claim_without_gate_transfer"
                )
                residual_blocker = (
                    "a bounded pre-gate admission hook is now runtime-owned on the active path, but it remains limited to immutable metadata, observational ticket reservation, and bounded pre-claim bookkeeping; it still does not form a request-aggregation window or cohort ownership before whole-request gate claim"
                )
                recommended_next_step = (
                    "treat batching as post-structural pre-gate admission work on this path; revalidate request-aggregation exactness against the bounded hook that now exists, keep child dispatch and stream hold secondary, and do not inflate this seam into continuous batching or parity"
                )
            preserved_safety_invariants = hook_harness.preserved_post_claim_invariants
        else:
            admission_hook_status = "no_bounded_hook_before_gate_claim"
            owned_boundary_status = (
                "whole_request_gate_claim_is_first_runtime_owned_boundary"
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
