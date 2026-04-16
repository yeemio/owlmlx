from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from owlmlx import build_customer_runtime_evidence, customer_runtime_evidence_to_dict


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


def test_customer_runtime_evidence_only_upgrades_to_structural_ingress_seam(monkeypatch) -> None:
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
        "owlmlx.customer_runtime_evidence.build_cache_structural_ingress_seam",
        lambda **_: _structural_ingress(
            seam_rung="structural_ingress_seam_introduced",
            residual_blocker="structural ingress seam exists but request aggregation remains unsupported",
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

    cache = next(
        item for item in payload["gap_evidence"] if item["gap_id"] == "cache_scheduler_depth"
    )
    assert cache["contract_surface"] == "owlmlx.cache_structural_ingress_seam"
    assert cache["closure_level"] == "structural_ingress_seam_introduced"
    assert "structural ingress seam introduced only" in payload["summary"]["recommended_next_step"]
