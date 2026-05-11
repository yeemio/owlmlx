from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_repeatability_evidence,
    build_cache_closure_rung,
    build_cache_counter_gap,
    build_cache_counter_feasibility,
    build_cache_scheduler_turboquant_split,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_turboquant_preconditions_gap,
    build_dominant_gap_reselection,
    dominant_gap_reselection_to_dict,
)
from owlmlx.heavy_weight_repeatability_status import HeavyWeightRuntimeRepeatabilityStatus
from owlmlx.multi_model_governance_policy_gap import MultiModelGovernancePolicyGap


def _heavy_local_blocked() -> HeavyWeightRuntimeRepeatabilityStatus:
    return HeavyWeightRuntimeRepeatabilityStatus(
        host_stability=object(),
        first_smoke_decision=object(),
        supported_host_proof_visible=False,
        supported_host_repeat_runs=0,
        status="partial",
        repeatability_rung="local_blocked",
        blocked_reason="supported host/system image is still required",
        recommended_next_step="move repeated heavy-weight validation to a supported host",
    )


def _heavy_local_preconditions_incomplete() -> HeavyWeightRuntimeRepeatabilityStatus:
    return HeavyWeightRuntimeRepeatabilityStatus(
        host_stability=object(),
        first_smoke_decision=object(),
        supported_host_proof_visible=False,
        supported_host_repeat_runs=0,
        status="partial",
        repeatability_rung="local_preconditions_incomplete",
        blocked_reason="specimen download still in progress",
        recommended_next_step="complete specimen prerequisites before stronger baseline validation",
    )


def _heavy_budget_fit_boundary_entered() -> HeavyWeightRuntimeRepeatabilityStatus:
    return HeavyWeightRuntimeRepeatabilityStatus(
        host_stability=object(),
        first_smoke_decision=object(),
        supported_host_proof_visible=False,
        supported_host_repeat_runs=0,
        status="partial",
        repeatability_rung="budget_fit_heavy_boundary_entered",
        blocked_reason="one budget-fit heavy boundary has been entered on the current host, but repeated proof is not yet established",
        recommended_next_step="stop here and require coordinator authorization before repeated heavy-weight validation",
        boundary_required_memory_gb=62.0,
        boundary_preconditions_satisfied=True,
        boundary_preconditions_reason="loading 62.0G fits within budget: 62.0G projected of 116.0G budget (54.0G headroom)",
        boundary_preconditions_verdict="fits",
        boundary_entry_visible=True,
        boundary_entry_reason="load/generate/unload succeeded on gemma-4-31B-it",
    )


def _heavy_supported_host_repeatability_visible() -> HeavyWeightRuntimeRepeatabilityStatus:
    return HeavyWeightRuntimeRepeatabilityStatus(
        host_stability=object(),
        first_smoke_decision=object(),
        supported_host_proof_visible=True,
        supported_host_repeat_runs=2,
        status="partial",
        repeatability_rung="supported_host_repeatability_visible",
        blocked_reason=(
            "supported-host repeatability is visible, but broader customer runtime evidence still remains below reference-grade parity"
        ),
        recommended_next_step=(
            "promote supported-host repeatability into broader customer runtime evidence instead of re-running first-smoke gating"
        ),
        boundary_required_memory_gb=62.0,
        boundary_preconditions_satisfied=True,
        boundary_preconditions_reason="supported-host repeated proof is already visible on the selected path",
        boundary_preconditions_verdict="fits",
        boundary_entry_visible=True,
        boundary_entry_reason="repeat runs succeeded on gemma-4-31B-it",
    )


def _governance_policy_exact() -> MultiModelGovernancePolicyGap:
    return MultiModelGovernancePolicyGap(
        controls=object(),
        transition_ledger=object(),
        status="partial",
        policy_gap_rung="policy_gap_exact",
        residual_blocker="remaining governance gap is policy-grade only",
        recommended_next_step="implement policy-grade controls",
        observed_runtime_behavior_frozen=True,
        absent_policy_controls=("pinning", "ttl_policy", "eviction_history_governance"),
        present_policy_controls=(),
    )


def _governance_policy_reduced() -> MultiModelGovernancePolicyGap:
    return MultiModelGovernancePolicyGap(
        controls=object(),
        transition_ledger=object(),
        status="partial",
        policy_gap_rung="policy_gap_reduced",
        residual_blocker="ttl_policy, eviction_history_governance",
        recommended_next_step="continue governance fallback branch",
        observed_runtime_behavior_frozen=True,
        absent_policy_controls=("ttl_policy", "eviction_history_governance"),
        present_policy_controls=("pinning",),
    )


def _governance_policy_closed() -> MultiModelGovernancePolicyGap:
    return MultiModelGovernancePolicyGap(
        controls=object(),
        transition_ledger=object(),
        status="partial",
        policy_gap_rung="policy_gap_closed",
        residual_blocker=None,
        recommended_next_step="return to supported-host baseline establishment",
        observed_runtime_behavior_frozen=True,
        absent_policy_controls=(),
        present_policy_controls=("pinning", "ttl_policy", "eviction_history_governance"),
    )


def test_dominant_gap_reselection_keeps_cache_when_cache_backlog_is_exact() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    turboquant_gap = build_cache_turboquant_preconditions_gap(readiness=closure.turboquant)

    payload = dominant_gap_reselection_to_dict(
        build_dominant_gap_reselection(
            cache_scheduler_backlog=backlog,
            cache_turboquant_preconditions=turboquant_gap,
            governance_policy_gap=_governance_policy_exact(),
            heavy_weight_repeatability=_heavy_local_blocked(),
        )
    )

    assert payload["summary"]["decision_rung"] == "reselection_exact"
    assert payload["summary"]["selected_gap"] == "cache_scheduler_depth"


def test_dominant_gap_reselection_switches_to_governance_when_policy_gap_is_reduced() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    turboquant_gap = build_cache_turboquant_preconditions_gap(readiness=closure.turboquant)

    payload = dominant_gap_reselection_to_dict(
        build_dominant_gap_reselection(
            cache_scheduler_backlog=backlog,
            cache_turboquant_preconditions=turboquant_gap,
            governance_policy_gap=_governance_policy_reduced(),
            heavy_weight_repeatability=_heavy_local_blocked(),
        )
    )

    assert payload["summary"]["selected_gap"] == "multi_model_lifecycle_governance"


def test_dominant_gap_reselection_returns_to_host_when_policy_gap_is_closed() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    turboquant_gap = build_cache_turboquant_preconditions_gap(readiness=closure.turboquant)

    payload = dominant_gap_reselection_to_dict(
        build_dominant_gap_reselection(
            cache_scheduler_backlog=backlog,
            cache_turboquant_preconditions=turboquant_gap,
            governance_policy_gap=_governance_policy_closed(),
            heavy_weight_repeatability=_heavy_local_blocked(),
        )
    )

    assert payload["summary"]["selected_gap"] == "host_stable_execution"


def test_dominant_gap_reselection_keeps_host_when_candidate_baseline_exists() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    turboquant_gap = build_cache_turboquant_preconditions_gap(readiness=closure.turboquant)

    payload = dominant_gap_reselection_to_dict(
        build_dominant_gap_reselection(
            cache_scheduler_backlog=backlog,
            cache_turboquant_preconditions=turboquant_gap,
            governance_policy_gap=_governance_policy_closed(),
            heavy_weight_repeatability=_heavy_local_preconditions_incomplete(),
        )
    )

    assert payload["summary"]["selected_gap"] == "host_stable_execution"
    assert "supported candidate baseline" in payload["summary"]["rationale"]


def test_dominant_gap_reselection_records_budget_fit_boundary_entry() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    turboquant_gap = build_cache_turboquant_preconditions_gap(readiness=closure.turboquant)

    payload = dominant_gap_reselection_to_dict(
        build_dominant_gap_reselection(
            cache_scheduler_backlog=backlog,
            cache_turboquant_preconditions=turboquant_gap,
            governance_policy_gap=_governance_policy_closed(),
            heavy_weight_repeatability=_heavy_budget_fit_boundary_entered(),
        )
    )

    assert payload["summary"]["selected_gap"] == "host_stable_execution"
    assert "budget-fit heavy boundary" in payload["summary"]["rationale"]


def test_dominant_gap_reselection_moves_to_cache_after_repeated_proof_visible() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    turboquant_gap = build_cache_turboquant_preconditions_gap(readiness=closure.turboquant)

    payload = dominant_gap_reselection_to_dict(
        build_dominant_gap_reselection(
            cache_scheduler_backlog=backlog,
            cache_turboquant_preconditions=turboquant_gap,
            governance_policy_gap=_governance_policy_closed(),
            heavy_weight_repeatability=_heavy_supported_host_repeatability_visible(),
        )
    )

    assert payload["summary"]["selected_gap"] == "cache_scheduler_depth"
    assert "repeated heavy-weight proof is now visible" in payload["summary"]["rationale"]


def test_dominant_gap_reselection_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "dominant_gap_reselection.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
