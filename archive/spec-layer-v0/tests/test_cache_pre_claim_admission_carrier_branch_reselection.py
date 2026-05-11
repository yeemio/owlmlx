from __future__ import annotations

from pathlib import Path

from owlmlx import build_cache_pre_claim_admission_carrier_branch_reselection
from owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness import (
    CachePreClaimAdmissionCarrierReclaimResetExactness,
)
from owlmlx.cache_pre_claim_admission_carrier_branch_reselection import (
    cache_pre_claim_admission_carrier_branch_reselection_to_dict,
)


def test_cache_pre_claim_admission_carrier_branch_reselection_defaults_unresolved() -> None:
    payload = cache_pre_claim_admission_carrier_branch_reselection_to_dict(
        build_cache_pre_claim_admission_carrier_branch_reselection()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_pre_claim_admission_carrier_branch_reselection"
    )
    assert payload["summary"]["reselection_rung"] == "carrier_branch_reselection_unresolved"


def test_cache_pre_claim_admission_carrier_branch_reselection_freezes_exact() -> None:
    carrier_reclaim_reset = CachePreClaimAdmissionCarrierReclaimResetExactness(
        locality_lifetime_coupling=object(),
        status="partial",
        exactness_rung="admission_carrier_reclaim_reset_exact",
        reclaim_reset_status="reclaim_resets_bounded_inert_carrier_to_fully_empty_state_before_reuse",
        reset_boundary_status="reuse_allowed_only_after_empty_reset_without_history_or_execution_state",
        allowed_reset_semantics=(
            "reclaim_clears_inert_carrier_presence_to_empty_state",
            "no_prior_request_history_visible_after_carrier_reclaim",
            "later_staged_request_may_reuse_only_after_empty_carrier_reset",
        ),
        forbidden_reset_expansions=(
            "no_reuse_with_stale_carrier_history",
            "no_partial_reset_leaving_scheduler_or_backend_hints",
            "no_cross_request_transfer_of_reclaim_reason",
            "no_execution_priority_or_queue_state_retained_after_carrier_reclaim",
        ),
        residual_blocker="the pre-claim admission-carrier reclaim-reset semantics are now exact",
        recommended_next_step="treat cache as admission-carrier branch reselection work on this path",
    )

    payload = cache_pre_claim_admission_carrier_branch_reselection_to_dict(
        build_cache_pre_claim_admission_carrier_branch_reselection(
            reclaim_reset_exactness=carrier_reclaim_reset
        )
    )

    assert payload["summary"]["reselection_rung"] == "carrier_branch_reselection_exact"
    assert (
        payload["branch_status"]["next_cache_subbranch"]
        == "scheduler_turboquant_branch_reselection"
    )


def test_cache_pre_claim_admission_carrier_branch_reselection_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_pre_claim_admission_carrier_branch_reselection.py"
    ).read_text()
    forbidden = ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]
    for pattern in forbidden:
        assert pattern not in source
