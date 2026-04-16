from __future__ import annotations

from pathlib import Path

from owlmlx import build_cache_request_aggregation_active_seam
from owlmlx.cache_request_aggregation_active_seam import (
    cache_request_aggregation_active_seam_to_dict,
)
from owlmlx.cache_request_aggregation_window_exactness import CacheRequestAggregationWindowExactness
from owlmlx.cache_request_aggregation_window_reentry import CacheRequestAggregationWindowReentry


def test_cache_request_aggregation_active_seam_defaults_unresolved() -> None:
    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_request_aggregation_active_seam"


def test_cache_request_aggregation_active_seam_freezes_exact() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="missing_pre_gate_admission_window",
        admission_boundary_status="generation_gate_claims_session_before_cohort_formation",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="request aggregation still blocked",
        recommended_next_step="pre-gate seam",
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "pre_gate_admission_window"
    assert payload["preserved_secondary_runtime_branch"]["status"] == "preconditions_exact"


def test_cache_request_aggregation_active_seam_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_request_aggregation_active_seam.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
