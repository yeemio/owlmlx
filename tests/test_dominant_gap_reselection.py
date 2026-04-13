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
