from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from owlmlx import build_customer_runtime_evidence, customer_runtime_evidence_to_dict
from owlmlx.dominant_gap_reselection import DominantGapReselection


def _host(*, ready: bool, status: str, blocked_reason: str | None):
    return SimpleNamespace(
        ready=ready,
        status=status,
        blocked_reason=blocked_reason,
        preferred_execution_mode="default_metal" if ready else None,
    )


def _cache(*, closure_rung: str, blocked_reason: str | None):
    return SimpleNamespace(
        status="partial",
        closure_rung=closure_rung,
        blocked_reason=blocked_reason,
    )


def _cache_counter_gap(*, counter_gap_rung: str, residual_blocker: str | None):
    return SimpleNamespace(
        status="partial",
        counter_gap_rung=counter_gap_rung,
        residual_blocker=residual_blocker,
    )


def _cache_counter_feasibility(
    *, feasibility_rung: str, residual_blocker: str | None
):
    return SimpleNamespace(
        status="partial",
        feasibility_rung=feasibility_rung,
        residual_blocker=residual_blocker,
    )


def _structural_ingress(*, seam_rung: str, residual_blocker: str | None):
    return SimpleNamespace(
        status="partial",
        seam_rung=seam_rung,
        residual_blocker=residual_blocker,
    )


def _pre_gate_window_seam(
    *,
    seam_rung: str,
    selected_seam_status: str,
    residual_blocker: str | None,
):
    return SimpleNamespace(
        status="partial",
        seam_rung=seam_rung,
        selected_seam_status=selected_seam_status,
        residual_blocker=residual_blocker,
    )


def _request_aggregation_active_seam(
    *,
    seam_rung: str,
    selected_seam: str,
    selected_seam_status: str,
    residual_blocker: str | None,
):
    return SimpleNamespace(
        status="partial",
        seam_rung=seam_rung,
        selected_seam=selected_seam,
        selected_seam_status=selected_seam_status,
        residual_blocker=residual_blocker,
    )


def _governance(*, governance_rung: str, blocked_reason: str | None):
    return SimpleNamespace(
        status="partial",
        governance_rung=governance_rung,
        blocked_reason=blocked_reason,
    )


def _governance_controls(*, controls_rung: str, blocked_reason: str | None):
    return SimpleNamespace(
        status="partial",
        controls_rung=controls_rung,
        blocked_reason=blocked_reason,
    )


def _governance_transition_ledger(*, ledger_rung: str, blocked_reason: str | None):
    return SimpleNamespace(
        status="partial",
        ledger_rung=ledger_rung,
        blocked_reason=blocked_reason,
    )


def _governance_policy_gap(
    *,
    policy_gap_rung: str,
    residual_blocker: str | None,
    absent_policy_controls: tuple[str, ...] = (),
    present_policy_controls: tuple[str, ...] = (),
):
    return SimpleNamespace(
        status="partial",
        policy_gap_rung=policy_gap_rung,
        residual_blocker=residual_blocker,
        absent_policy_controls=absent_policy_controls,
        present_policy_controls=present_policy_controls,
    )


def _heavy(
    *,
    repeatability_rung: str,
    blocked_reason: str | None,
):
    return SimpleNamespace(
        status="partial",
        repeatability_rung=repeatability_rung,
        blocked_reason=blocked_reason,
    )


def _dominant_gap(*, selected_gap: str, rationale: str):
    return DominantGapReselection(
        cache_scheduler_backlog=object(),
        cache_turboquant_preconditions=object(),
        governance_policy_gap=object(),
        heavy_weight_repeatability=object(),
        status="partial",
        decision_rung="reselection_exact",
        selected_gap=selected_gap,
        rationale=rationale,
    )


def test_customer_runtime_evidence_defaults_to_early_formal_runtime(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="partial_closure",
            blocked_reason="scheduler depth remains serial-only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="observation_gap_open",
            residual_blocker="runtime-owned cache observations are still too weak",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_unresolved",
            residual_blocker="cache counter ownership is still unresolved",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="restart_visibility_visible",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="transition_evidence_visible",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning, TTL, and eviction-history governance remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_blocked",
            blocked_reason="supported host/system image is required",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["contract"]["surface"] == "owlmlx.customer_runtime_evidence"
    assert payload["summary"]["evidence_label"] == "early_formal_runtime"
    assert payload["summary"]["externally_blocked_gaps"] == [
        "host_stable_execution",
        "heavy_weight_runtime_repeatability",
    ]
    governance = next(
        item
        for item in payload["gap_evidence"]
        if item["gap_id"] == "multi_model_lifecycle_governance"
    )
    assert governance["contract_surface"] == "owlmlx.multi_model_governance_policy_gap"
    assert governance["closure_level"] == "policy_gap_exact"
    assert payload["next_step"]["dominant_next_gap"] == "cache_scheduler_depth"


def test_customer_runtime_evidence_can_mark_runtime_evidence_expanding(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="partial_closure",
            blocked_reason="scheduler depth remains serial-only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="observation_gap_open",
            residual_blocker="runtime-owned cache observations are still too weak",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_unresolved",
            residual_blocker="cache counter ownership is still unresolved",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="host_ready_not_repeated",
            blocked_reason="supported host repeated proof not yet established",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["summary"]["evidence_label"] == "runtime_evidence_expanding"
    assert payload["summary"]["externally_blocked_gaps"] == []


def test_customer_runtime_evidence_switches_to_governance_on_policy_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="partial_closure",
            blocked_reason="serial scheduler still below reference-grade parity",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="scheduler backlog remains open",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="scheduler depth / TurboQuant remain open",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="TTL policy and eviction-history governance remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="TTL policy and eviction-history governance remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="TTL policy and eviction-history governance remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_reduced",
            residual_blocker="TTL policy and eviction-history governance remain absent",
            absent_policy_controls=("ttl_policy", "eviction_history_governance"),
            present_policy_controls=("pinning",),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_blocked",
            blocked_reason="supported host/system image is required",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["next_step"]["dominant_next_gap"] == "multi_model_lifecycle_governance"
    assert payload["summary"]["recommended_next_step"] == (
        "treat governance as the active fallback branch on this host: runtime pinning now exists, so continue with TTL policy or eviction-history governance instead of reopening cache widening"
    )


def test_customer_runtime_evidence_recommends_eviction_after_ttl_lands(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="eviction-history governance remains absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="eviction-history governance remains absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="eviction-history governance remains absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_reduced",
            residual_blocker="eviction-history governance remains absent",
            absent_policy_controls=("eviction_history_governance",),
            present_policy_controls=("pinning", "ttl_policy"),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_blocked",
            blocked_reason="supported host/system image is required",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["next_step"]["dominant_next_gap"] == "multi_model_lifecycle_governance"
    assert payload["summary"]["recommended_next_step"] == (
        "treat governance as the active fallback branch on this host: runtime pinning and TTL policy now exist, so continue with eviction-history governance instead of reopening cache widening"
    )


def test_customer_runtime_evidence_returns_to_supported_host_after_governance_policy_closes(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_blocked",
            blocked_reason="supported host/system image is required",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["next_step"]["dominant_next_gap"] == "host_stable_execution"
    assert payload["summary"]["recommended_next_step"] == (
        "local governance fallback is now exhausted on this host; return to supported-host baseline establishment and do not reopen cache widening without fresh authorization"
    )


def test_customer_runtime_evidence_advances_to_stronger_baseline_validation_once_candidate_exists(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_preconditions_incomplete",
            blocked_reason="specimen download still in progress",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["next_step"]["dominant_next_gap"] == "host_stable_execution"
    assert payload["next_step"]["exact_external_blocker"] is None
    assert payload["summary"]["recommended_next_step"] == (
        "freeze the selected heavy-weight boundary blocker exact on this host and do not reopen cache widening or governance micro-rounds"
    )


def test_customer_runtime_evidence_freezes_boundary_blocker_exact(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="partial_closure",
            blocked_reason="scheduler depth remains serial-only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="scheduler backlog remains open",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="residency and eviction counters are not runtime-owned",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_scheduler_turboquant_split",
        lambda **_: SimpleNamespace(
            status="partial",
            split_rung="branch_selection_exact",
            residual_blocker="continuous batching remains primary",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_scheduler_floor_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            floor_rung="serial_floor_exact",
            residual_blocker="continuous batching and multi-worker depth remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_scheduler_implementation_backlog",
        lambda **_: SimpleNamespace(
            status="partial",
            backlog_rung="implementation_gap_exact",
            residual_blocker="continuous batching remains unimplemented",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant still waits behind scheduler work",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="request aggregation remains unsupported",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_preconditions_incomplete",
            blocked_reason="loading 122.0G would exceed serving budget: 0.0G loaded + 122.0G requested = 122.0G > 116.0G limit",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            heavy_weight_boundary_memory_gb=122.0,
        )
    )

    assert payload["summary"]["blocked_reason"] == (
        "runtime-owned evidence has expanded and the current host still keeps its supported candidate baseline, but the selected heavy-weight boundary remains preconditions-blocked even though cache stays frozen at a structural seam"
    )
    assert payload["summary"]["recommended_next_step"] == (
        "freeze the selected heavy-weight boundary blocker exact on this host and do not reopen cache widening or governance micro-rounds"
    )


def test_customer_runtime_evidence_records_budget_fit_boundary_entry(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="partial_closure",
            blocked_reason="scheduler depth remains serial-only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="scheduler backlog remains open",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="residency and eviction counters are not runtime-owned",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_scheduler_turboquant_split",
        lambda **_: SimpleNamespace(
            status="partial",
            split_rung="branch_selection_exact",
            residual_blocker="continuous batching remains primary",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_scheduler_floor_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            floor_rung="serial_floor_exact",
            residual_blocker="continuous batching and multi-worker depth remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_scheduler_implementation_backlog",
        lambda **_: SimpleNamespace(
            status="partial",
            backlog_rung="implementation_gap_exact",
            residual_blocker="continuous batching remains unimplemented",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant still waits behind scheduler work",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="request aggregation remains unsupported",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="budget_fit_heavy_boundary_entered",
            blocked_reason="one budget-fit heavy boundary has been entered on the current host, but repeated proof is not yet established",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            heavy_weight_boundary_memory_gb=62.0,
            heavy_weight_boundary_entered=True,
            heavy_weight_boundary_entry_reason="load/generate/unload succeeded on gemma-4-31B-it",
        )
    )

    assert payload["summary"]["blocked_reason"] == (
        "runtime-owned evidence has expanded and one budget-fit heavy boundary has been entered on the current host, but owlmlx still remains below reference-grade stability because repeated heavy-weight proof is not yet authorized and cache remains frozen at a structural seam"
    )
    assert payload["summary"]["recommended_next_step"] == (
        "one budget-fit heavy boundary is now entered on this host; stop here and require coordinator authorization before repeated heavy-weight validation"
    )


def test_customer_runtime_evidence_can_mark_approaching_reference_grade(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="partial_closure",
            blocked_reason="scheduler depth remains serial-only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="observation_gap_open",
            residual_blocker="runtime-owned cache observations are still too weak",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_unresolved",
            residual_blocker="cache counter ownership is still unresolved",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["summary"]["evidence_label"] == "approaching_reference_grade_stability"
    assert payload["next_step"]["exact_external_blocker"] is None


def test_customer_runtime_evidence_freezes_repeated_proof_checkpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="structural_ingress_seam_introduced",
            blocked_reason="cache remains frozen at a structural seam",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is already exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="governance policy controls now exist locally",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=(
                "supported-host repeatability is visible, but broader customer runtime evidence still remains below reference-grade parity"
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_dominant_gap_reselection",
        lambda **_: _dominant_gap(
            selected_gap="multi_model_lifecycle_governance",
            rationale="supported-host repeated heavy-weight proof is now visible on the current host but cache has not been reauthorized yet",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["summary"]["evidence_label"] == "early_formal_runtime"
    assert payload["next_step"]["dominant_next_gap"] == "multi_model_lifecycle_governance"
    assert payload["summary"]["blocked_reason"] == (
        "runtime-owned evidence has expanded and supported-host repeated heavy-weight proof is now visible on the selected path, but owlmlx still remains below reference-grade stability because cache depth remains frozen at a structural seam and governance still remains below reference-grade parity"
    )
    assert payload["summary"]["recommended_next_step"] == (
        "freeze supported-host repeated heavy-weight proof exact and take a fresh coordinator checkpoint before reopening cache/governance"
    )


def test_customer_runtime_evidence_requires_specimen_path_without_heavy_weight() -> None:
    try:
        build_customer_runtime_evidence()
    except ValueError as exc:
        assert "specimen_path is required" in str(exc)
    else:
        raise AssertionError("expected ValueError when specimen_path is missing")


def test_customer_runtime_evidence_prefers_controls_surface_without_transition_ledger(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="truth_only",
            blocked_reason="runtime-owned cache evidence still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="observation_gap_open",
            residual_blocker="runtime-owned cache observations are still too weak",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_unresolved",
            residual_blocker="cache counter ownership is still unresolved",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="restart_visibility_visible",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="transition_evidence_visible",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="no_transition_runs",
            blocked_reason="repeated governance-transition evidence is still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="observation_gap_open",
            residual_blocker="governance observations still too weak",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_blocked",
            blocked_reason="supported host/system image is required",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    governance = next(
        item
        for item in payload["gap_evidence"]
        if item["gap_id"] == "multi_model_lifecycle_governance"
    )
    assert governance["contract_surface"] == "owlmlx.multi_model_governance_controls"
    assert governance["closure_level"] == "transition_evidence_visible"


def test_customer_runtime_evidence_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx",
        "customer_runtime_evidence.py",
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source


def test_customer_runtime_evidence_moves_dominant_gap_to_cache_when_governance_policy_gap_is_exact(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="local_blocked",
            blocked_reason="supported host/system image is required",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(specimen_path="/tmp/specimen")
    )

    assert payload["next_step"]["dominant_next_gap"] == "cache_scheduler_depth"
    cache = next(
        item for item in payload["gap_evidence"] if item["gap_id"] == "cache_scheduler_depth"
    )
    assert (
        cache["contract_surface"]
        == "owlmlx.cache_pre_gate_admission_window_seam"
    )
    assert (
        cache["closure_level"]
        == "pre_gate_admission_window_seam_exact"
    )
    assert (
        "the active seam is now the missing bounded pre-gate admission hook"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_prefers_post_structural_pre_gate_window_over_structural_checkpoint(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_exact",
            selected_seam_status="bounded_hook_present_but_no_request_aggregation_window",
            residual_blocker="bounded hook exists but remains inert and does not form a request-aggregation window",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    cache = next(
        item for item in payload["gap_evidence"] if item["gap_id"] == "cache_scheduler_depth"
    )
    assert (
        cache["contract_surface"]
        == "owlmlx.cache_pre_gate_admission_window_seam"
    )
    assert (
        cache["closure_level"]
        == "pre_gate_admission_window_seam_exact"
    )
    assert (
        "bounded pre-gate hook now exists before whole-request gate claim"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_advances_to_post_window_request_aggregation_dependency(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="child_exchange_aggregated_dispatch_dependency",
            selected_seam_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
            residual_blocker="window already entered; child exchange still blocks aggregated dispatch",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    cache = next(
        item for item in payload["gap_evidence"] if item["gap_id"] == "cache_scheduler_depth"
    )
    assert (
        cache["contract_surface"]
        == "owlmlx.cache_request_aggregation_active_seam"
    )
    assert cache["closure_level"] == "aggregation_active_seam_exact"
    assert (
        "a bounded pre-gate admission window now forms cohorts before whole-request gate claim"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_narrowed_stream_hold_when_active_seam_has_moved(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="stream_backend_iterator_completion_dependency",
            selected_seam_status="stream_backend_iterator_holds_gate_until_completion",
            residual_blocker="stream gate release is now decoupled from outer consumer completion",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "stream gate release is now decoupled from outer consumer completion"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_backend_terminal_event_when_active_seam_has_moved(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_stream_terminal_event_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_event",
            residual_blocker="backend terminal event now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal-event commitment"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_payload_commit_when_active_seam_has_moved_again(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_payload_commit_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
            residual_blocker="backend terminal payload commit now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "backend-terminal-payload commit" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_payload_capture_when_active_seam_has_moved_again(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_payload_capture_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            residual_blocker="backend terminal payload capture now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal-payload capture"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_record_capture_when_active_seam_has_moved_again(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_record_capture_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
            residual_blocker="backend terminal record capture now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal-record capture"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_record_prefix_when_active_seam_has_moved_again(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_record_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection",
            residual_blocker="backend terminal record prefix now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal-record prefix"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_action_discriminant_when_active_seam_has_moved_yet_again(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_action_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection",
            residual_blocker="backend terminal action discriminant now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal action discriminant"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_notice_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_capture_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture",
            residual_blocker="backend terminal notice now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal notice"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_notice_prefix_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_prefix_detection",
            residual_blocker="backend terminal notice prefix now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal-notice prefix"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_notice_action_discriminant_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_action_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_discriminant_detection",
            residual_blocker="backend terminal notice action discriminant now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "backend-terminal notice-action-discriminant"
        in payload["summary"]["recommended_next_step"]
    )


def test_customer_runtime_evidence_mentions_terminal_notice_action_stem_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_action_stem_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_stem_detection",
            residual_blocker="backend terminal notice action stem now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "backend-terminal notice-action-stem" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_marker_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_marker_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_detection",
            residual_blocker="backend terminal notice marker now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-action-stem" in payload["summary"]["recommended_next_step"]
    assert "notice-marker detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_marker_prefix_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_marker_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_prefix_detection",
            residual_blocker="backend terminal notice marker prefix now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
            absent_policy_controls=(),
            present_policy_controls=(
                "pinning",
                "ttl_policy",
                "eviction_history_governance",
            ),
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-marker" in payload["summary"]["recommended_next_step"]
    assert "notice-marker-prefix detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_marker_stem_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_marker_stem_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_stem_detection",
            residual_blocker="backend terminal notice marker stem now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_closed",
            residual_blocker=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-marker-prefix" in payload["summary"]["recommended_next_step"]
    assert "notice-marker-stem detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_marker_discriminant_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_marker_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_discriminant_detection",
            residual_blocker="backend terminal notice marker discriminant now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "post-terminal-notice-marker-stem"
        in payload["summary"]["recommended_next_step"]
    )
    assert "notice-marker-discriminant detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_marker_key_lead_when_active_seam_has_moved_even_further(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_marker_key_lead_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection",
            residual_blocker="backend terminal notice marker key lead now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert (
        "post-terminal-notice-marker-discriminant"
        in payload["summary"]["recommended_next_step"]
    )
    assert "notice-marker-key lead detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_marker_key_lead_as_first_unique_boundary_when_active_seam_stays_blocked(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_marker_key_lead_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection",
            residual_blocker="backend terminal notice marker key lead remains the first unique boundary",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="controls_partial",
            blocked_reason="governance controls remain partial",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="transition_truth_present",
            blocked_reason="transition history remains narrow",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-marker-discriminant" in payload["summary"]["recommended_next_step"]
    assert "notice-marker-key lead detection" in payload["summary"]["recommended_next_step"]
    assert "earliest unique terminal-notice marker boundary" in payload["summary"]["recommended_next_step"]
    assert "opening quote" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_when_active_seam_moves_beyond_key_lead(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection",
            residual_blocker="backend terminal notice leading discriminator now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "runtime-owned terminal-notice leading discriminator" in payload["summary"]["recommended_next_step"]
    assert "backend-terminal notice leading-discriminator detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_prefix_when_active_seam_moves_beyond_leading_discriminator(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_prefix_detection",
            residual_blocker="backend terminal notice leading discriminator prefix now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-leading-discriminator freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator prefix detection" in payload["summary"]["recommended_next_step"]
    assert "internal leading-discriminator action" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_stem_when_active_seam_moves_beyond_prefix(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_stem_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_stem_detection",
            residual_blocker="backend terminal notice leading discriminator stem now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-leading-discriminator-prefix freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator stem detection" in payload["summary"]["recommended_next_step"]
    assert "internal leading-discriminator prefix" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_discriminant_when_active_seam_moves_beyond_stem(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_discriminant_detection",
            residual_blocker="backend terminal notice leading discriminator discriminant now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-leading-discriminator-stem freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator discriminant detection" in payload["summary"]["recommended_next_step"]
    assert "internal leading-discriminator stem" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_marker_when_active_seam_moves_beyond_discriminant(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_detection",
            residual_blocker="backend terminal notice leading discriminator marker now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-leading-discriminator-discriminant freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator marker detection" in payload["summary"]["recommended_next_step"]
    assert "internal leading-discriminator discriminant" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_marker_prefix_when_active_seam_moves_beyond_marker(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_prefix_detection",
            residual_blocker="backend terminal notice leading discriminator marker prefix now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-leading-discriminator-marker freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator marker-prefix detection" in payload["summary"]["recommended_next_step"]
    assert "internal terminal_notice_lead marker" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_marker_stem_when_active_seam_moves_beyond_marker_prefix(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_stem_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_stem_detection",
            residual_blocker="backend terminal notice leading discriminator marker stem now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-leading-discriminator-marker-prefix freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator marker-stem detection" in payload["summary"]["recommended_next_step"]
    assert "internal terminal_notice_lead marker-prefix" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_terminal_notice_leading_discriminator_marker_discriminant_when_active_seam_moves_beyond_marker_stem(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection",
            residual_blocker="backend terminal notice leading discriminator marker discriminant now blocks more exactly",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )
    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-terminal-notice-leading-discriminator-marker-stem freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator marker-discriminant detection" in payload["summary"]["recommended_next_step"]
    assert "internal terminal_notice_l marker-stem" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_discriminator_when_active_seam_moves_beyond_marker_discriminant(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection",
            residual_blocker="owlmlx now owns a new earlier runtime-owned terminal-notice discriminator record ahead of the current marker-discriminant seam",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )
    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice discriminator introduction work" in payload["summary"]["recommended_next_step"]
    assert "earlier-runtime-owned-discriminator detection" in payload["summary"]["recommended_next_step"]
    assert "new runtime-owned discriminator record" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_discriminator_prefix_when_active_seam_moves_beyond_full_discriminator_detection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection",
            residual_blocker="the remaining exact stream seam is now closer than full earlier-runtime-owned-discriminator detection",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )
    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice discriminator prefix freeze work" in payload["summary"]["recommended_next_step"]
    assert "earlier-runtime-owned-discriminator prefix detection" in payload["summary"]["recommended_next_step"]
    assert "before child stdout reaches full earlier-runtime-owned-discriminator detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_discriminator_stem_when_active_seam_moves_beyond_prefix_detection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection",
            residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-discriminator prefix detection",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )
    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice discriminator stem freeze work" in payload["summary"]["recommended_next_step"]
    assert "earlier-runtime-owned-discriminator stem detection" in payload["summary"]["recommended_next_step"]
    assert "before child stdout reaches that fuller prefix boundary" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_discriminator_discriminant_when_active_seam_moves_beyond_stem_detection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="scheduler depth remains the next cache blocker",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counters are already exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
            residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-discriminator stem detection",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress is already exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="governance_truth_visible",
            blocked_reason="governance still below residency parity",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="controls_truth_visible",
            blocked_reason="residency controls still incomplete",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="transition_truth_visible",
            blocked_reason="residency controls still incomplete",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )
    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice discriminator discriminant freeze work" in payload["summary"]["recommended_next_step"]
    assert "earlier-runtime-owned-discriminator discriminant detection" in payload["summary"]["recommended_next_step"]
    assert "before child stdout reaches that fuller stem boundary" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_first_unique_boundary_when_leading_discriminator_marker_discriminant_stays_active(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection",
            residual_blocker="backend terminal notice leading discriminator marker discriminant is already the first honest unique boundary",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "first-unique-boundary work" in payload["summary"]["recommended_next_step"]
    assert "first honest unique boundary" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_first_unique_boundary_when_earlier_runtime_owned_discriminator_discriminant_stays_active(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_closure_rung",
        lambda **_: _cache(
            closure_rung="repeatability_visible",
            blocked_reason="direct runtime-owned reuse counters are still absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
            residual_blocker="backend terminal notice leading discriminator marker earlier runtime-owned discriminator discriminant is already the first honest unique boundary on the newer runtime-owned record",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice discriminator first-unique-boundary work" in payload["summary"]["recommended_next_step"]
    assert "first honest unique boundary" in payload["summary"]["recommended_next_step"]
    assert "newer runtime-owned record" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_leading_discriminator_prefix_when_active_seam_moves_beyond_earlier_runtime_owned_leading_discriminator_introduction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection",
            residual_blocker="owlmlx now owns a new runtime-owned leading-discriminator-prefix boundary ahead of full earlier-runtime-owned-leading-discriminator detection on the current internal record",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice leading-discriminator prefix freeze work" in payload["summary"]["recommended_next_step"]
    assert "new runtime-owned leading-discriminator-prefix boundary" in payload["summary"]["recommended_next_step"]
    assert "full earlier-runtime-owned-leading-discriminator detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_leading_discriminator_stem_when_active_seam_moves_beyond_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection",
            residual_blocker="owlmlx now owns an earlier runtime-owned leading-discriminator stem boundary ahead of the fuller earlier-runtime-owned-leading-discriminator prefix on the current internal record",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice leading-discriminator stem freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator stem boundary" in payload["summary"]["recommended_next_step"]
    assert "remaining exact blocker now sits at backend-terminal notice leading-discriminator marker earlier-runtime-owned-leading-discriminator stem detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_boundary_when_boundary_is_active_seam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection",
            residual_blocker="owlmlx now owns one new earlier runtime-owned boundary record ahead of the newer runtime-owned leading-discriminator record on this path",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="boundary introduction remains cache-local",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice boundary introduction work" in payload["summary"]["recommended_next_step"]
    assert "new earlier runtime-owned boundary record" in payload["summary"]["recommended_next_step"]
    assert "backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_boundary_prefix_when_prefix_is_active_seam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
            residual_blocker="the remaining exact stream seam is now closer than full earlier-runtime-owned-boundary detection on this path",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="boundary-prefix narrowing remains cache-local",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice boundary prefix freeze work" in payload["summary"]["recommended_next_step"]
    assert "boundary-prefix boundary" in payload["summary"]["recommended_next_step"]
    assert "backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary prefix detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_boundary_earlier_boundary_when_active_seam_moves_beyond_stem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection",
            residual_blocker="owlmlx now owns one distinct earlier runtime-owned boundary record ahead of the current earlier-runtime-owned-boundary stem seam: a second backend stream request can be written once child stdout reaches runtime_owned_terminal_earlier_boundary and before child stdout reaches runtime_owned_terminal_b",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="boundary-earlier-boundary introduction remains cache-local",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice boundary earlier-boundary introduction work" in payload["summary"]["recommended_next_step"]
    assert "runtime_owned_terminal_earlier_boundary" in payload["summary"]["recommended_next_step"]
    assert "runtime_owned_terminal_b" in payload["summary"]["recommended_next_step"]
    assert "backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary earlier-boundary detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_earlier_boundary_when_active_seam_advances_to_earlier_earlier_boundary_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection",
            residual_blocker="owlmlx now owns one distinct earlier-earlier runtime-owned boundary record ahead of the previous earlier-runtime-owned-boundary earlier-boundary seam: a second backend stream request can be written once child stdout reaches runtime_owned_terminal_earlier_earlier_boundary and before child stdout reaches runtime_owned_terminal_earlier_boundary",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="earlier-earlier-boundary introduction remains cache-local",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice boundary earlier-earlier-boundary introduction work" in payload["summary"]["recommended_next_step"]
    assert "runtime_owned_terminal_earlier_earlier_boundary" in payload["summary"]["recommended_next_step"]
    assert "runtime_owned_terminal_earlier_boundary" in payload["summary"]["recommended_next_step"]
    assert "backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary earlier-earlier-boundary detection" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_boundary_first_unique_boundary_when_active_seam_freezes_first_honest_unique_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection",
            residual_blocker="owlmlx already owns one distinct earlier runtime-owned boundary record (runtime_owned_terminal_earlier_boundary) ahead of the previous boundary stem (runtime_owned_terminal_b), and the remaining exact stream seam stays at earlier-runtime-owned-boundary earlier-boundary detection on this path: the literal prefix before runtime_owned_terminal_earlier_b is not yet an honest runtime-owned transport boundary, so earlier-boundary detection is already the first honest unique boundary on the newer earlier-boundary record and no earlier live seam is yet available",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="boundary-earlier-boundary first-unique-boundary remains cache-local",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice boundary earlier-boundary first-unique-boundary work" in payload["summary"]["recommended_next_step"]
    assert "first honest unique boundary on the newer earlier-boundary record" in payload["summary"]["recommended_next_step"]
    assert "runtime_owned_terminal_earlier_b" in payload["summary"]["recommended_next_step"]


def test_customer_runtime_evidence_mentions_earlier_runtime_owned_leading_discriminator_discriminant_when_active_seam_moves_beyond_stem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_gap",
        lambda **_: _cache_counter_gap(
            counter_gap_rung="counter_gap_exact",
            residual_blocker="remaining cache gap is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_counter_feasibility",
        lambda **_: _cache_counter_feasibility(
            feasibility_rung="counter_ownership_exact",
            residual_blocker="cache counter ownership is now exact",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_request_aggregation_active_seam",
        lambda **_: _request_aggregation_active_seam(
            seam_rung="aggregation_active_seam_exact",
            selected_seam="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_dependency",
            selected_seam_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection",
            residual_blocker="owlmlx now owns an earlier runtime-owned leading-discriminator discriminant boundary ahead of the fuller earlier-runtime-owned-leading-discriminator stem on the current internal record",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_pre_gate_admission_window_seam",
        lambda **_: _pre_gate_window_seam(
            seam_rung="pre_gate_admission_window_seam_unresolved",
            selected_seam_status="not_selected",
            residual_blocker="window already entered",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_status",
        lambda **_: _governance(
            governance_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_controls",
        lambda **_: _governance_controls(
            controls_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_transition_ledger",
        lambda **_: _governance_transition_ledger(
            ledger_rung="partial_closure",
            blocked_reason="pinning and TTL remain absent",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_multi_model_governance_policy_gap",
        lambda **_: _governance_policy_gap(
            policy_gap_rung="policy_gap_exact",
            residual_blocker="remaining governance gap is policy-grade only",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_heavy_weight_runtime_repeatability_status",
        lambda **_: _heavy(
            repeatability_rung="supported_host_repeatability_visible",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.customer_runtime_evidence.build_cache_turboquant_preconditions_gap",
        lambda **_: SimpleNamespace(
            status="partial",
            preconditions_rung="preconditions_exact",
            residual_blocker="TurboQuant remains exact but secondary",
        ),
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path="/tmp/specimen",
            dominant_gap_reselection=_dominant_gap(
                selected_gap="cache_scheduler_depth",
                rationale="cache remains dominant",
            ),
        )
    )

    assert "post-runtime-owned earlier terminal-notice leading-discriminator discriminant first-unique-boundary freeze work" in payload["summary"]["recommended_next_step"]
    assert "leading-discriminator discriminant boundary" in payload["summary"]["recommended_next_step"]
    assert "first honest unique boundary on that newer runtime-owned record" in payload["summary"]["recommended_next_step"]
