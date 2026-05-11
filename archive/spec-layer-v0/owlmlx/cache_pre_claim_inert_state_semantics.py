"""Runtime-owned exact inert-state semantics for pre-claim cache ingress."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_gate_admission_hook_harness import PreGateAdmissionHookHarnessResult
from .cache_pre_claim_metadata_ticket_ownership import (
    CachePreClaimMetadataTicketOwnership,
    build_cache_pre_claim_metadata_ticket_ownership,
)
from .cache_pre_gate_cohort_window_feasibility import (
    CachePreGateCohortWindowFeasibility,
    build_cache_pre_gate_cohort_window_feasibility,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimInertStateSemantics:
    """Exact runtime truth for inert pre-claim cohort/drop semantics."""

    metadata_ticket_ownership: CachePreClaimMetadataTicketOwnership
    cohort_window_feasibility: CachePreGateCohortWindowFeasibility
    status: str
    exactness_rung: str
    cohort_candidate_status: str
    drop_cancel_status: str
    allowed_inert_semantics: tuple[str, ...]
    forbidden_inert_semantics: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_inert_state_semantics(
    *,
    metadata_ticket_ownership: CachePreClaimMetadataTicketOwnership | None = None,
    cohort_window_feasibility: CachePreGateCohortWindowFeasibility | None = None,
    hook_harness: PreGateAdmissionHookHarnessResult | None = None,
) -> CachePreClaimInertStateSemantics:
    """Build exact inert-state semantics for the active pre-claim path."""

    ownership = (
        metadata_ticket_ownership
        if isinstance(metadata_ticket_ownership, CachePreClaimMetadataTicketOwnership)
        else build_cache_pre_claim_metadata_ticket_ownership()
    )
    cohort = (
        cohort_window_feasibility
        if isinstance(cohort_window_feasibility, CachePreGateCohortWindowFeasibility)
        else build_cache_pre_gate_cohort_window_feasibility()
    )

    exactness_rung = "inert_state_semantics_unresolved"
    cohort_candidate_status = "not_frozen"
    drop_cancel_status = "not_frozen"
    allowed_inert_semantics = ()
    forbidden_inert_semantics = ()
    residual_blocker = (
        "inert-state semantics are not yet exact because ownership and pre-gate cohort feasibility are not both frozen strongly enough"
    )
    recommended_next_step = (
        "freeze pre-claim ownership boundaries and pre-gate cohort feasibility before reducing the remaining cache blocker to inert-state semantics"
    )

    if (
        ownership.exactness_rung == "ownership_boundary_exact"
        and cohort.feasibility_rung == "cohort_window_boundary_exact"
    ):
        exactness_rung = "inert_state_semantics_exact"
        cohort_candidate_status = "no_runtime_owned_cohort_membership_before_gate_claim"
        drop_cancel_status = "inert_drop_or_cancel_marker_allowed_before_gate_claim"
        allowed_inert_semantics = ("drop_or_cancel_marker_before_gate_claim",)
        forbidden_inert_semantics = (
            "no_cohort_membership_before_gate_claim",
            "no_execution_priority_before_gate_claim",
            "no_prefill_batch_membership_before_gate_claim",
        )
        residual_blocker = (
            "the inert pre-claim semantics are now exact: owlmlx may carry only an inert drop/cancel marker before gate claim, it still owns no cohort membership before gate claim, and inert state may not acquire execution priority or prefill-batch membership before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as pre-claim inert-state boundary work on this path; if a future seam expands, freeze exact ticket drop/cancel lifetime and keep cohort membership and execution priority unavailable until whole-request gate claim"
        )
        if (
            hook_harness is not None
            and hook_harness.hook_mode == "bounded_runtime_owned_cohort_window"
            and hook_harness.observed_peak_cohort_size >= 2
            and hook_harness.aggregation_scope == "pre_claim_window_only"
        ):
            cohort_candidate_status = (
                "bounded_runtime_owned_cohort_membership_before_gate_claim_without_execution_rights"
            )
            allowed_inert_semantics = (
                "drop_or_cancel_marker_before_gate_claim",
                "bounded_pre_claim_cohort_membership_without_execution_rights",
            )
            forbidden_inert_semantics = (
                "no_execution_priority_before_gate_claim",
                "no_prefill_batch_membership_before_gate_claim",
            )
            residual_blocker = (
                "the inert pre-claim semantics are now re-frozen after the cohort-window widening: owlmlx may carry an inert drop/cancel marker and bounded pre-claim cohort membership before gate claim, but that state still grants no execution priority or prefill-batch membership before the first runtime-owned claim boundary"
            )
            recommended_next_step = (
                "treat request aggregation as downstream dependency work on this path; preserve bounded pre-claim cohort membership without granting pre-claim execution rights or post-claim concurrency"
            )

    return CachePreClaimInertStateSemantics(
        metadata_ticket_ownership=ownership,
        cohort_window_feasibility=cohort,
        status="partial",
        exactness_rung=exactness_rung,
        cohort_candidate_status=cohort_candidate_status,
        drop_cancel_status=drop_cancel_status,
        allowed_inert_semantics=allowed_inert_semantics,
        forbidden_inert_semantics=forbidden_inert_semantics,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_inert_state_semantics_to_dict(
    exactness: CachePreClaimInertStateSemantics,
) -> dict[str, object]:
    """Serialize exact inert pre-claim semantics."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_inert_state_semantics",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "inert_state_boundary",
                "forbidden_inert_semantics",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "inert_state_boundary": {
            "cohort_candidate_status": exactness.cohort_candidate_status,
            "drop_cancel_status": exactness.drop_cancel_status,
            "allowed_inert_semantics": list(exactness.allowed_inert_semantics),
        },
        "forbidden_inert_semantics": list(exactness.forbidden_inert_semantics),
    }
