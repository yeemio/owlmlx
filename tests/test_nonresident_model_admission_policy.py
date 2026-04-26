from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.nonresident_model_admission_policy import (
    NONRESIDENT_ADMISSION_DECISIONS,
    NONRESIDENT_MODEL_ADMISSION_POLICY_SURFACE,
    build_nonresident_model_admission_policy,
    nonresident_model_admission_policy_to_dict,
)
from owlmlx.nonresident_loadability_lineage import (
    build_nonresident_loadability_lineage,
)
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime_model_visibility import (
    DEFAULT_MODELS_ROOT,
    RegisteredRuntimeVisibleModel,
    RuntimeModelVisibilityGate,
    RuntimeVisibleModelState,
)


def _stub_visibility_gate(
    *,
    target_model_id: str = "fake-b",
    visible: bool = True,
    block_reason: str | None = None,
) -> RuntimeModelVisibilityGate:
    local_dir = f"/runtime-owned/models/{target_model_id}"
    state = RuntimeVisibleModelState(
        model_id=target_model_id,
        local_model_dir=local_dir,
        config_path=f"{local_dir}/config.json",
        local_model_dir_present=visible,
        config_present=visible,
        visible=visible,
        block_reason=block_reason,
    )
    return RuntimeModelVisibilityGate(
        rule="runtime_gate_required_before_visible",
        contract_version="runtime-owned-2",
        models_root="/runtime-owned/models",
        entries=(state,),
        visible_model_ids=((target_model_id,) if visible else ()),
        loaded_model_ids=(),
    )


def _stub_lineage_record(local_path: str = "/runtime-owned/models/fake-b") -> dict[str, object]:
    return {
        "base_model": "fake-b",
        "base_format": "safetensors",
        "quantizer": "owlmlx",
        "quant_method": "q4",
        "served_format": "mlx",
        "conversion_path": "direct",
        "conversion_patches": ["patch-a"],
        "local_path": local_path,
        "file_size_gb": 4.5,
        "sha256": "deadbeef",
        "runtime": "mlx_lm",
        "runtime_version": "1.0",
        "verified_date": "2026-04-25",
        "verified_context": 4096,
        "known_caveats": [],
    }


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def _runtime_status_payload(
    *,
    currently_loaded_gb: float,
    available_gb: float,
    utilization: float,
    loaded_model_ids: tuple[str, ...] = (),
    backend_healthy: bool = True,
    abort_recovery: dict[str, object] | None = None,
    restart_exhausted_models: tuple[str, ...] = (),
) -> dict[str, object]:
    payload: dict[str, object] = {
        "summary": {
            "backend_healthy": backend_healthy,
            "active_model_id": loaded_model_ids[0] if loaded_model_ids else None,
        },
        "active_model_id": loaded_model_ids[0] if loaded_model_ids else None,
        "inventory": {
            "model_count": len(loaded_model_ids),
            "total_loaded_gb": currently_loaded_gb,
        },
        "backend": {
            "loaded_models": [
                {
                    "model_id": model_id,
                    "memory_gb": 1.0,
                    "backend": "fake",
                    "loaded_at": None,
                }
                for model_id in loaded_model_ids
            ],
        },
        "budget": {
            "system_memory_gb": 128.0,
            "system_reserve_gb": 12.0,
            "serving_budget_gb": 116.0,
            "warning_threshold_gb": 100.0,
            "currently_loaded_gb": currently_loaded_gb,
            "available_gb": available_gb,
            "utilization": utilization,
        },
        "restart": {
            "restartable_models": [],
            "restart_exhausted_models": list(restart_exhausted_models),
            "auto_restart_dead_session": False,
        },
        "governance_policy": {
            "ttl_expired_model_ids": [],
            "ttl_expired_pinned_model_ids": [],
        },
        "governance_observations": {},
        "health": {"readiness": "ready" if backend_healthy else "blocked"},
    }
    if abort_recovery is not None:
        payload["abort_recovery"] = abort_recovery
    return payload


def test_nonresident_admission_returns_admit_for_known_loadable_within_budget() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
        )
    )

    assert payload["contract"]["surface"] == NONRESIDENT_MODEL_ADMISSION_POLICY_SURFACE
    assert payload["summary"]["decision"] == "admit_and_load"
    assert payload["summary"]["target_model_id"] == "fake-b"
    assert payload["reason"]["code"] == "non_resident_target_known_loadable_admit"
    assert "memory_budget_preflight_must_still_hold_at_load_time" in (
        payload["required_preconditions"]
    )
    assert payload["blocking_signals"] == []
    assert "max_concurrent_1_after_gate_claim" in payload["preserved_invariants"]
    assert payload["inputs"]["known_loadable_truth_status"] == "operator_supplied"
    assert payload["inputs"]["memory_pressure"]["pressure_classification"] == "within_budget"


def test_nonresident_admission_returns_unknown_when_lineage_truth_missing() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-c",
        )
    )

    assert payload["summary"]["decision"] == "unknown"
    assert payload["reason"]["code"] == "lineage_loadability_truth_missing"
    assert payload["inputs"]["known_loadable_truth_status"] == "missing"
    assert any(
        item["layer"] == "loadability"
        for item in payload["blocking_signals"]
    )
    assert any(
        item["layer"] == "loadability"
        for item in payload["missing_signals"]
    )


def test_nonresident_admission_rejects_over_budget_with_eviction_policy_blocker() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=120.0,
                available_gb=-4.0,
                utilization=1.034,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert payload["summary"]["confidence"] == "high"
    assert payload["reason"]["code"] == "over_budget_and_no_pressure_eviction_policy_owned"
    eviction_blockers = [
        item for item in payload["blocking_signals"] if item["layer"] == "eviction"
    ]
    assert eviction_blockers, "over-budget reject must name eviction policy blocker"
    assert (
        "release_floor_3_2_memory_pressure_decision_closure_must_close"
        in payload["required_preconditions"]
    )


def test_nonresident_admission_rejects_under_recovery_hard_barrier() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
                backend_healthy=False,
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert payload["reason"]["code"] == "recovery_hard_barrier_fail_closed"
    assert payload["inputs"]["recovery"]["hard_recovery_barrier"] is True
    recovery_blockers = [
        item for item in payload["blocking_signals"] if item["layer"] == "recovery"
    ]
    assert recovery_blockers


def test_nonresident_admission_defers_high_context_under_recovery_probing() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
                abort_recovery={
                    "state": "probing",
                    "recovery_required": False,
                },
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
            request_context_class="high_context",
        )
    )

    assert payload["summary"]["decision"] == "defer"
    assert payload["reason"]["code"] == "recovery_probing_defers_high_context_load"
    assert "abort_recovery_probe_must_complete" in payload["required_preconditions"]


def test_nonresident_admission_defers_near_budget_without_pressure_action_policy() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=101.0,
                available_gb=15.0,
                utilization=0.871,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
        )
    )

    assert payload["summary"]["decision"] == "defer"
    assert payload["reason"]["code"] == "near_budget_no_pressure_action_policy"


def test_nonresident_admission_rejects_when_target_already_resident() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a", "fake-b"),
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert payload["reason"]["code"] == "target_already_resident_no_admission_needed"


def test_nonresident_admission_rejects_when_no_target_model_provided() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
            ),
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert payload["reason"]["code"] == "no_target_model_requested"
    assert payload["summary"]["target_model_id"] is None


def test_nonresident_admission_returns_unknown_when_pressure_truth_missing() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status={"budget": {}},
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
        )
    )

    assert payload["summary"]["decision"] == "unknown"
    assert payload["reason"]["code"] == "pressure_truth_absent_for_admission_decision"


def test_nonresident_admission_decision_vocabulary_is_stable() -> None:
    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
        )
    )

    assert payload["summary"]["supported_decisions"] == list(
        NONRESIDENT_ADMISSION_DECISIONS
    )
    assert set(payload["decision_support"].keys()) == set(NONRESIDENT_ADMISSION_DECISIONS)
    assert (
        payload["policy_boundaries"]["round_trip_surfaces"]
        == [
            "owlmlx.model_residency_policy",
            "owlmlx.memory_pressure_contract",
            "owlmlx.recovery_supervisor_contract",
            "owlmlx.nonresident_loadability_lineage",
        ]
    )
    assert (
        "post_claim_gate_bypass"
        in payload["policy_boundaries"]["out_of_scope"]
    )
    scheduler_integration_pending = [
        item
        for item in payload["missing_signals"]
        if item["layer"] == "scheduler_admission_integration"
    ]
    assert scheduler_integration_pending, (
        "policy must explicitly record that scheduler_admission_contract "
        "integration is deferred"
    )


def test_runtime_nonresident_model_admission_policy_route_returns_surface() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get(
        "/v1/runtime/nonresident-model-admission-policy",
        params={
            "model_id": "fake-b",
            "known_loadable_model_ids": ["fake-b"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == NONRESIDENT_MODEL_ADMISSION_POLICY_SURFACE
    assert payload["summary"]["decision"] == "admit_and_load"
    assert payload["summary"]["target_model_id"] == "fake-b"
    assert payload["inputs"]["residency"]["resident_model_ids"] == ["fake-a"]


def test_runtime_nonresident_admission_route_unknown_without_lineage_hint() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get(
        "/v1/runtime/nonresident-model-admission-policy",
        params={"model_id": "fake-b"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["decision"] == "unknown"
    assert payload["reason"]["code"] == "lineage_loadability_truth_missing"


def test_nonresident_admission_admits_via_runtime_owned_loadability_lineage_without_operator_hint() -> None:
    visibility_gate = _stub_visibility_gate(target_model_id="fake-b")
    lineage = build_nonresident_loadability_lineage(
        model_id="fake-b",
        runtime_visibility_gate=visibility_gate,
        lineage_records={"fake-b": _stub_lineage_record()},
    )
    assert lineage.decision == "known_loadable"

    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-b",
            loadability_lineage=lineage,
        )
    )

    assert payload["summary"]["decision"] == "admit_and_load"
    assert (
        payload["reason"]["code"]
        == "non_resident_target_runtime_owned_loadability_lineage_admit"
    )
    assert payload["inputs"]["loadability_lineage"]["decision"] == "known_loadable"
    assert (
        payload["inputs"]["loadability_lineage"]["loadability_lineage_truth_status"]
        == "runtime_owned_connected"
    )
    assert payload["inputs"]["known_loadable_truth_status"] == "missing"
    assert (
        "runtime_owned_loadability_lineage_must_remain_known_loadable_at_load_time"
        in payload["required_preconditions"]
    )
    layers = {item["layer"] for item in payload["missing_signals"]}
    assert "loadability" not in layers, (
        "runtime-owned loadability_lineage must remove the legacy missing signal"
    )


def test_nonresident_admission_rejects_when_runtime_owned_lineage_says_not_loadable() -> None:
    visibility_gate = _stub_visibility_gate(target_model_id="fake-b")
    lineage = build_nonresident_loadability_lineage(
        model_id="fake-b",
        runtime_visibility_gate=visibility_gate,
        lineage_records={
            "fake-b": _stub_lineage_record(local_path="/somewhere/else/fake-b"),
        },
    )
    assert lineage.decision == "not_loadable"

    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
            loadability_lineage=lineage,
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert (
        payload["reason"]["code"]
        == "runtime_owned_loadability_lineage_says_not_loadable"
    )
    assert any(
        item["layer"] == "lineage_alignment"
        for item in payload["blocking_signals"]
    )
    layers = {item["layer"] for item in payload["missing_signals"]}
    assert "loadability" not in layers


def test_nonresident_admission_falls_back_to_operator_hint_when_lineage_unknown() -> None:
    visibility_gate = _stub_visibility_gate(target_model_id="fake-b")
    lineage = build_nonresident_loadability_lineage(
        model_id="fake-b",
        runtime_visibility_gate=visibility_gate,
        lineage_records=None,
    )
    assert lineage.decision == "unknown"

    payload = nonresident_model_admission_policy_to_dict(
        build_nonresident_model_admission_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_model_ids=("fake-a",),
            ),
            model_id="fake-b",
            known_loadable_model_ids=("fake-b",),
            loadability_lineage=lineage,
        )
    )

    assert payload["summary"]["decision"] == "admit_and_load"
    assert payload["reason"]["code"] == "non_resident_target_known_loadable_admit"
    layers = {item["layer"] for item in payload["missing_signals"]}
    assert "loadability" in layers, (
        "operator-hint fallback must keep the loadability missing signal active"
    )
    assert (
        "operator_supplied_loadability_hint_must_remain_valid_at_load_time"
        in payload["required_preconditions"]
    )


def test_nonresident_model_admission_policy_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "nonresident_model_admission_policy.py")
        .read_text()
    )
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
