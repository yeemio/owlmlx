from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from owlmlx import build_cache_pre_gate_admission_window_seam
from owlmlx.cache_pre_gate_admission_hook_exactness import CachePreGateAdmissionHookExactness
from owlmlx.cache_pre_gate_admission_window_seam import (
    cache_pre_gate_admission_window_seam_to_dict,
)
from owlmlx.cache_request_aggregation_active_seam import (
    build_cache_request_aggregation_active_seam,
)


def _active_seam(**overrides: object) -> object:
    return replace(build_cache_request_aggregation_active_seam(), **overrides)


def test_cache_pre_gate_admission_window_seam_defaults_unresolved() -> None:
    payload = cache_pre_gate_admission_window_seam_to_dict(
        build_cache_pre_gate_admission_window_seam()
    )
    assert payload["contract"]["surface"] == "owlmlx.cache_pre_gate_admission_window_seam"


def test_cache_pre_gate_admission_window_seam_freezes_exact() -> None:
    active_seam = _active_seam(
        status="partial",
        seam_rung="aggregation_active_seam_exact",
        selected_seam="pre_gate_admission_window",
        selected_seam_status="missing_pre_gate_admission_window",
        preserved_secondary_dependencies=(
            "single_request_per_child_exchange_blocks_aggregated_dispatch",
            "stream_session_holds_gate_until_completion",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="pre-gate window stays active",
        recommended_next_step="bounded hook",
    )
    hook_exactness = CachePreGateAdmissionHookExactness(
        cohort_window_feasibility=object(),
        status="partial",
        exactness_rung="admission_hook_blocker_exact",
        admission_hook_status="no_bounded_hook_before_gate_claim",
        owned_boundary_status="whole_request_gate_claim_is_first_runtime_owned_boundary",
        preserved_safety_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ),
        residual_blocker="bounded hook still missing",
        recommended_next_step="bounded hook",
    )
    payload = cache_pre_gate_admission_window_seam_to_dict(
        build_cache_pre_gate_admission_window_seam(
            request_aggregation_active_seam=active_seam,
            pre_gate_admission_hook_exactness=hook_exactness,
        )
    )
    assert payload["summary"]["seam_rung"] == "pre_gate_admission_window_seam_exact"
    assert payload["selected_seam"]["seam"] == "bounded_pre_gate_admission_hook"


def test_cache_pre_gate_admission_window_seam_revalidates_after_structural_ingress() -> None:
    active_seam = _active_seam(
        status="partial",
        seam_rung="aggregation_active_seam_exact",
        selected_seam="pre_gate_admission_window",
        selected_seam_status="missing_pre_gate_admission_window",
        preserved_secondary_dependencies=(
            "single_request_per_child_exchange_blocks_aggregated_dispatch",
            "stream_session_holds_gate_until_completion",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="pre-gate window stays active",
        recommended_next_step="bounded hook",
    )
    hook_exactness = CachePreGateAdmissionHookExactness(
        cohort_window_feasibility=object(),
        status="partial",
        exactness_rung="admission_hook_blocker_exact",
        admission_hook_status="bounded_hook_present_but_no_request_aggregation_window",
        owned_boundary_status="bounded_hook_precedes_whole_request_gate_claim_without_gate_transfer",
        preserved_safety_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ),
        residual_blocker="bounded hook exists but remains inert",
        recommended_next_step="post-structural pre-gate work",
    )
    payload = cache_pre_gate_admission_window_seam_to_dict(
        build_cache_pre_gate_admission_window_seam(
            request_aggregation_active_seam=active_seam,
            pre_gate_admission_hook_exactness=hook_exactness,
        )
    )
    assert payload["summary"]["seam_rung"] == "pre_gate_admission_window_seam_exact"
    assert payload["selected_seam"]["seam"] == "bounded_pre_gate_admission_hook"
    assert (
        payload["selected_seam"]["status"]
        == "bounded_hook_present_but_no_request_aggregation_window"
    )


def test_cache_pre_gate_admission_window_seam_stops_being_active_after_window_entry() -> None:
    active_seam = _active_seam(
        status="partial",
        seam_rung="aggregation_active_seam_exact",
        selected_seam="child_exchange_aggregated_dispatch_dependency",
        selected_seam_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        preserved_secondary_dependencies=("stream_session_holds_gate_until_completion",),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="window already entered",
        recommended_next_step="freeze child dependency",
    )
    hook_exactness = CachePreGateAdmissionHookExactness(
        cohort_window_feasibility=object(),
        status="partial",
        exactness_rung="admission_hook_blocker_exact",
        admission_hook_status="bounded_request_aggregation_window_present_before_gate_claim",
        owned_boundary_status="bounded_cohort_window_precedes_whole_request_gate_claim_without_gate_transfer",
        preserved_safety_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ),
        residual_blocker="window already present",
        recommended_next_step="freeze downstream dependency",
    )

    payload = cache_pre_gate_admission_window_seam_to_dict(
        build_cache_pre_gate_admission_window_seam(
            request_aggregation_active_seam=active_seam,
            pre_gate_admission_hook_exactness=hook_exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "pre_gate_admission_window_seam_unresolved"


def test_cache_pre_gate_admission_window_seam_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_pre_gate_admission_window_seam.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
