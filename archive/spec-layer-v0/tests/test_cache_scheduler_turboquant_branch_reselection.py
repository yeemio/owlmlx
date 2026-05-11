from __future__ import annotations

from pathlib import Path

from owlmlx import build_cache_scheduler_turboquant_branch_reselection
from owlmlx.cache_pre_claim_admission_carrier_branch_reselection import (
    CachePreClaimAdmissionCarrierBranchReselection,
)
from owlmlx.cache_scheduler_branch_selection import CacheSchedulerBranchSelection
from owlmlx.cache_scheduler_turboquant_branch_reselection import (
    cache_scheduler_turboquant_branch_reselection_to_dict,
)
from owlmlx.cache_turboquant_preconditions_gap import CacheTurboQuantPreconditionsGap


def test_cache_scheduler_turboquant_branch_reselection_defaults_unresolved() -> None:
    payload = cache_scheduler_turboquant_branch_reselection_to_dict(
        build_cache_scheduler_turboquant_branch_reselection()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_scheduler_turboquant_branch_reselection"
    )


def test_cache_scheduler_turboquant_branch_reselection_freezes_exact() -> None:
    carrier = CachePreClaimAdmissionCarrierBranchReselection(
        reclaim_reset_exactness=object(),
        status="partial",
        reselection_rung="carrier_branch_reselection_exact",
        carrier_branch_status="carrier_exactness_chain_complete_on_current_path",
        residual_carrier_subgap=None,
        next_cache_subbranch="scheduler_turboquant_branch_reselection",
        preserved_ingress_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
        ),
        residual_blocker="carrier exactness chain is complete",
        recommended_next_step="scheduler-vs-TurboQuant branch reselection",
    )
    scheduler = CacheSchedulerBranchSelection(
        scheduler_backlog=object(),
        status="partial",
        selection_rung="branch_selection_exact",
        selected_branch="continuous_batching",
        selected_branch_status="locally_reducible_on_current_path",
        secondary_branch="multi_worker_scheduler_depth",
        secondary_branch_status="safety_revalidation_required",
        residual_blocker="scheduler backlog remains open",
        recommended_next_step="continuous batching first",
    )
    turboquant = CacheTurboQuantPreconditionsGap(
        readiness=object(),
        status="partial",
        preconditions_rung="preconditions_exact",
        missing_preconditions=("bits_in_cache_key",),
        residual_blocker="TurboQuant exact-but-secondary",
        recommended_next_step="keep TurboQuant secondary",
    )

    payload = cache_scheduler_turboquant_branch_reselection_to_dict(
        build_cache_scheduler_turboquant_branch_reselection(
            carrier_branch_reselection=carrier,
            scheduler_branch_selection=scheduler,
            turboquant_preconditions_gap=turboquant,
        )
    )

    assert payload["summary"]["reselection_rung"] == "scheduler_turboquant_branch_exact"
    assert payload["selected_branch"]["branch"] == "scheduler_depth"
    assert payload["selected_branch"]["status"] == "continuous_batching"
    assert payload["secondary_branch"]["branch"] == "turboquant_preconditions"


def test_cache_scheduler_turboquant_branch_reselection_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_scheduler_turboquant_branch_reselection.py"
    ).read_text()
    forbidden = ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]
    for pattern in forbidden:
        assert pattern not in source
