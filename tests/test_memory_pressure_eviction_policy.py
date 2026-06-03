from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.memory_pressure_eviction_policy import (
    MEMORY_PRESSURE_EVICTION_DECISIONS,
    MEMORY_PRESSURE_EVICTION_POLICY_SURFACE,
    build_memory_pressure_eviction_policy,
    memory_pressure_eviction_policy_to_dict,
)
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app


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
    loaded_models: tuple[dict[str, object], ...] = (),
    active_model_id: str | None = None,
    pinned_model_ids: tuple[str, ...] = (),
    ttl_expired_model_ids: tuple[str, ...] = (),
    ttl_expired_pinned_model_ids: tuple[str, ...] = (),
    backend_healthy: bool = True,
    abort_recovery: dict[str, object] | None = None,
    restart_exhausted_models: tuple[str, ...] = (),
) -> dict[str, object]:
    payload: dict[str, object] = {
        "summary": {
            "backend_healthy": backend_healthy,
            "active_model_id": active_model_id,
        },
        "active_model_id": active_model_id,
        "inventory": {
            "model_count": len(loaded_models),
            "total_loaded_gb": currently_loaded_gb,
        },
        "backend": {
            "loaded_models": list(loaded_models),
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
            "pinned_model_ids": list(pinned_model_ids),
            "ttl_expired_model_ids": list(ttl_expired_model_ids),
            "ttl_expired_pinned_model_ids": list(ttl_expired_pinned_model_ids),
        },
        "governance_observations": {},
        "health": {"readiness": "ready" if backend_healthy else "blocked"},
    }
    if abort_recovery is not None:
        payload["abort_recovery"] = abort_recovery
    return payload


def _model_entry(
    *,
    model_id: str,
    memory_gb: float = 1.0,
) -> dict[str, object]:
    return {
        "model_id": model_id,
        "memory_gb": memory_gb,
        "backend": "fake",
        "loaded_at": None,
    }


def test_within_budget_does_not_evict() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_models=(_model_entry(model_id="fake-a"),),
                active_model_id="fake-a",
            )
        )
    )

    assert payload["contract"]["surface"] == MEMORY_PRESSURE_EVICTION_POLICY_SURFACE
    assert payload["summary"]["decision"] == "defer"
    assert payload["reason"]["code"] == "within_budget_no_pressure_trigger"
    assert payload["selected_victim"] is None
    assert payload["summary"]["pressure_classification"] == "within_budget"


def test_near_budget_defers_rather_than_evicting() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=101.0,
                available_gb=15.0,
                utilization=0.871,
                loaded_models=(
                    _model_entry(model_id="fake-a", memory_gb=50.0),
                    _model_entry(model_id="fake-b", memory_gb=51.0),
                ),
                active_model_id="fake-a",
            )
        )
    )

    assert payload["summary"]["decision"] == "defer"
    assert payload["reason"]["code"] == "near_budget_pressure_not_strong_enough_to_evict"
    assert payload["selected_victim"] is None


def test_over_budget_selects_deterministic_candidate_order() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=130.0,
                available_gb=-14.0,
                utilization=1.121,
                loaded_models=(
                    _model_entry(model_id="fake-a", memory_gb=40.0),
                    _model_entry(model_id="fake-b", memory_gb=50.0),
                    _model_entry(model_id="fake-c", memory_gb=40.0),
                ),
                active_model_id="fake-a",
                ttl_expired_model_ids=("fake-c",),
            )
        )
    )

    assert payload["summary"]["decision"] == "evict"
    assert payload["summary"]["selected_victim_model_id"] == "fake-c"
    candidate_ids = [entry["model_id"] for entry in payload["candidate_order"]]
    assert candidate_ids[0] == "fake-c"
    assert candidate_ids[1] == "fake-b"
    eligible = [entry for entry in payload["candidate_order"] if entry["eligible"]]
    assert all(not entry["pinned"] for entry in eligible)


def test_over_budget_with_all_pinned_rejects_with_named_blocker() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=130.0,
                available_gb=-14.0,
                utilization=1.121,
                loaded_models=(
                    _model_entry(model_id="fake-a", memory_gb=60.0),
                    _model_entry(model_id="fake-b", memory_gb=70.0),
                ),
                active_model_id="fake-a",
                pinned_model_ids=("fake-a", "fake-b"),
            )
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert payload["reason"]["code"] == "over_budget_but_all_candidates_pinned"
    blockers = [
        item
        for item in payload["blocking_signals"]
        if item["layer"] == "residency"
    ]
    assert blockers


def test_over_budget_with_only_active_protected_rejects() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=130.0,
                available_gb=-14.0,
                utilization=1.121,
                loaded_models=(_model_entry(model_id="fake-a", memory_gb=130.0),),
                active_model_id="fake-a",
            )
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert (
        payload["reason"]["code"]
        == "over_budget_but_only_candidate_is_protected_active_model"
    )


def test_recovery_hard_barrier_fails_closed_with_reject() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=130.0,
                available_gb=-14.0,
                utilization=1.121,
                loaded_models=(
                    _model_entry(model_id="fake-a", memory_gb=40.0),
                    _model_entry(model_id="fake-b", memory_gb=90.0),
                ),
                active_model_id="fake-a",
                backend_healthy=False,
            )
        )
    )

    assert payload["summary"]["decision"] == "reject"
    assert payload["reason"]["code"] == "recovery_hard_barrier_eviction_unsafe"


def test_unknown_when_budget_truth_missing() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status={"budget": {}}
        )
    )

    assert payload["summary"]["decision"] == "unknown"
    assert payload["reason"]["code"] == "pressure_truth_absent_for_eviction_decision"


def test_decision_vocabulary_is_stable() -> None:
    payload = memory_pressure_eviction_policy_to_dict(
        build_memory_pressure_eviction_policy(
            runtime_status=_runtime_status_payload(
                currently_loaded_gb=40.0,
                available_gb=76.0,
                utilization=0.345,
                loaded_models=(_model_entry(model_id="fake-a"),),
                active_model_id="fake-a",
            )
        )
    )

    assert payload["summary"]["supported_decisions"] == list(
        MEMORY_PRESSURE_EVICTION_DECISIONS
    )
    assert set(payload["decision_support"].keys()) == set(
        MEMORY_PRESSURE_EVICTION_DECISIONS
    )
    assert "no_post_claim_gate_bypass" in payload["preserved_invariants"]
    assert "pinned_models_never_evicted" in payload["preserved_invariants"]


def test_runtime_kernel_executes_pressure_eviction_with_observable_residency_change() -> None:
    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=16.0,
            system_reserve_gb=2.0,
            serving_budget_gb=12.0,
            warning_threshold_gb=10.0,
        ),
    )
    kernel.load_model("fake-a", memory_gb=2.0)
    kernel.load_model("fake-b", memory_gb=2.0)
    kernel.load_model("fake-c", memory_gb=2.0)
    # Tighten the profile so the already-loaded inventory becomes over_budget.
    kernel.profile = MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=4.0,
        warning_threshold_gb=3.0,
    )

    pre_status = kernel.status_dict()
    pre_loaded = {
        entry["model_id"]
        for entry in pre_status["backend"]["loaded_models"]
    }
    assert {"fake-a", "fake-b", "fake-c"} <= pre_loaded

    result = kernel.execute_memory_pressure_eviction()

    assert result["ok"] is True
    assert result["executed"] is True
    assert result["decision"] == "evict"
    victim_id = result["selected_victim"]["model_id"]
    assert victim_id in pre_loaded

    post_loaded = {
        entry.model_id for entry in kernel.backend.status().loaded_models
    }
    assert victim_id not in post_loaded
    assert pre_loaded - post_loaded == {victim_id}

    history_event = result["eviction_history_event"]
    assert history_event["model_id"] == victim_id
    assert history_event["event"] == "memory_pressure_evicted"
    assert history_event["source"] == "memory_pressure_policy"


def test_load_model_evict_to_fit_unloads_non_pinned_resident_for_switch() -> None:
    from owlmlx.runtime.types import RuntimeErrorCode

    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=16.0,
            system_reserve_gb=2.0,
            serving_budget_gb=10.0,
            warning_threshold_gb=8.0,
        ),
    )
    assert kernel.load_model("model-a", memory_gb=7.0).ok is True

    # model-b alone fits (8 <= 10) but model-a (7) + model-b (8) = 15 > 10,
    # so a plain switch is refused on budget.
    blocked = kernel.load_model("model-b", memory_gb=8.0)
    assert blocked.ok is False
    assert blocked.error_code is RuntimeErrorCode.memory_budget_exceeded

    # evict_to_fit frees the non-pinned resident (model-a) and loads model-b.
    switched = kernel.load_model("model-b", memory_gb=8.0, evict_to_fit=True)
    assert switched.ok is True
    loaded = {entry.model_id for entry in kernel.backend.status().loaded_models}
    assert "model-b" in loaded
    assert "model-a" not in loaded
    assert kernel.active_model_id == "model-b"


def test_load_model_evict_to_fit_never_unloads_pinned_blocker() -> None:
    from owlmlx.runtime.types import RuntimeErrorCode

    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=16.0,
            system_reserve_gb=2.0,
            serving_budget_gb=10.0,
            warning_threshold_gb=8.0,
        ),
    )
    assert kernel.load_model("pinned-a", memory_gb=7.0).ok is True
    kernel.pin_model("pinned-a")

    # A pinned resident must never be unloaded, so the switch is refused with a
    # clear budget error rather than evicting the pinned model.
    result = kernel.load_model("model-b", memory_gb=8.0, evict_to_fit=True)
    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.memory_budget_exceeded
    loaded = {entry.model_id for entry in kernel.backend.status().loaded_models}
    assert "pinned-a" in loaded


def test_runtime_kernel_pressure_eviction_skips_pinned_candidates() -> None:
    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=16.0,
            system_reserve_gb=2.0,
            serving_budget_gb=12.0,
            warning_threshold_gb=10.0,
        ),
    )
    kernel.load_model("fake-a", memory_gb=2.0)
    kernel.load_model("fake-b", memory_gb=2.0)
    kernel.load_model("fake-c", memory_gb=2.0)
    kernel.pin_model("fake-c")
    kernel.profile = MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=4.0,
        warning_threshold_gb=3.0,
    )

    result = kernel.execute_memory_pressure_eviction()
    assert result["ok"] is True
    assert result["executed"] is True
    assert result["selected_victim"]["model_id"] != "fake-c"
    post_loaded = {
        entry.model_id for entry in kernel.backend.status().loaded_models
    }
    assert "fake-c" in post_loaded


def test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change() -> None:
    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=20.0,
            system_reserve_gb=2.0,
            serving_budget_gb=16.0,
            warning_threshold_gb=14.0,
        ),
    )
    kernel.load_model("alpha", memory_gb=2.0)
    kernel.load_model("beta", memory_gb=2.0)
    kernel.load_model("gamma", memory_gb=2.0)
    kernel.load_model("delta", memory_gb=2.0)
    # Tighten budget so 8.0 GB loaded > 4.0 GB budget -> over_budget.
    kernel.profile = MachineMemoryProfile(
        system_memory_gb=20.0,
        system_reserve_gb=2.0,
        serving_budget_gb=4.0,
        warning_threshold_gb=3.0,
    )

    initial_loaded = {
        entry.model_id for entry in kernel.backend.status().loaded_models
    }
    assert {"alpha", "beta", "gamma", "delta"} <= initial_loaded

    evicted_ids: list[str] = []
    for _ in range(2):
        decision_result = kernel.execute_memory_pressure_eviction()
        assert decision_result["ok"] is True
        assert decision_result["executed"] is True
        assert decision_result["decision"] == "evict"
        evicted_ids.append(decision_result["selected_victim"]["model_id"])

    assert len(set(evicted_ids)) == 2

    post_loaded = {
        entry.model_id for entry in kernel.backend.status().loaded_models
    }
    assert post_loaded == initial_loaded - set(evicted_ids)

    governance = kernel.status_dict()["governance_policy"]
    pressure_history = [
        event
        for event in governance["recent_eviction_history"]
        if event.get("source") == "memory_pressure_policy"
    ]
    assert len(pressure_history) == 2
    assert {event["model_id"] for event in pressure_history} == set(evicted_ids)


def test_runtime_kernel_pressure_eviction_refuses_execution_when_decision_is_defer() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_profile())
    kernel.load_model("fake-a", memory_gb=1.0)

    result = kernel.execute_memory_pressure_eviction()
    assert result["ok"] is False
    assert result["executed"] is False
    assert result["decision"] == "defer"
    assert result["reason_code"] == "execution_refused_unless_decision_is_evict"


def test_runtime_memory_pressure_eviction_policy_route_returns_payload() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 1.0})

    response = client.get("/v1/runtime/memory-pressure-eviction-policy")
    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == MEMORY_PRESSURE_EVICTION_POLICY_SURFACE
    assert payload["summary"]["decision"] in MEMORY_PRESSURE_EVICTION_DECISIONS


def test_runtime_memory_pressure_eviction_route_executes_under_pressure() -> None:
    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=16.0,
            system_reserve_gb=2.0,
            serving_budget_gb=12.0,
            warning_threshold_gb=10.0,
        ),
    )
    client = TestClient(create_app(kernel))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})
    client.post("/v1/load", json={"model_id": "fake-b", "memory_gb": 2.0})
    client.post("/v1/load", json={"model_id": "fake-c", "memory_gb": 2.0})
    kernel.profile = MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=4.0,
        warning_threshold_gb=3.0,
    )

    response = client.post(
        "/v1/runtime/memory-pressure-eviction",
        json={"protect_active": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["executed"] is True
    assert body["decision"] == "evict"
    assert body["eviction_history_event"]["source"] == "memory_pressure_policy"

    loaded_after = {
        entry.model_id for entry in kernel.backend.status().loaded_models
    }
    victim_id = body["selected_victim"]["model_id"]
    assert victim_id not in loaded_after


def test_runtime_memory_pressure_eviction_route_includes_loadability_lineage_after_state(
    tmp_path: Path,
) -> None:
    """Per release floor 3.2 §7: after eviction, loadability lineage after-state
    remains inspectable for the evicted model."""

    from owlmlx.runtime_model_visibility import RegisteredRuntimeVisibleModel

    for model_id in ("fake-a", "fake-b", "fake-c"):
        model_dir = tmp_path / model_id
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}")

    def _record(model_id: str, mem: float) -> dict[str, object]:
        return {
            "base_model": model_id,
            "base_format": "safetensors",
            "quantizer": "owlmlx",
            "quant_method": "q4",
            "served_format": "mlx",
            "conversion_path": "direct",
            "conversion_patches": [],
            "local_path": str(tmp_path / model_id),
            "file_size_gb": mem,
            "sha256": f"hash-{model_id}",
            "runtime": "mlx_lm",
            "runtime_version": "1.0",
            "verified_date": "2026-04-26",
            "verified_context": 4096,
            "known_caveats": [],
        }

    lineage_records = {
        model_id: _record(model_id, 2.0)
        for model_id in ("fake-a", "fake-b", "fake-c")
    }

    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=16.0,
            system_reserve_gb=2.0,
            serving_budget_gb=12.0,
            warning_threshold_gb=10.0,
        ),
    )
    client = TestClient(
        create_app(
            kernel,
            visibility_models_root=str(tmp_path),
            visibility_registry=[
                RegisteredRuntimeVisibleModel(model_id)
                for model_id in ("fake-a", "fake-b", "fake-c")
            ],
            loadability_lineage_records=lineage_records,
        )
    )
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})
    client.post("/v1/load", json={"model_id": "fake-b", "memory_gb": 2.0})
    client.post("/v1/load", json={"model_id": "fake-c", "memory_gb": 2.0})
    kernel.profile = MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=4.0,
        warning_threshold_gb=3.0,
    )

    response = client.post(
        "/v1/runtime/memory-pressure-eviction",
        json={"protect_active": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True

    assert "loadability_lineage_after" in body
    after = body["loadability_lineage_after"]
    # The evicted model is now non-resident; loadability lineage still reports
    # whether it is loadable, not whether it is loaded.
    assert after["summary"]["decision"] == "known_loadable"
    victim_id = body["selected_victim"]["model_id"]
    assert after["summary"]["target_model_id"] == victim_id
    assert body["residency_after"]["evicted_model_id"] == victim_id
    assert body["residency_after"]["victim_still_resident"] is False


def test_memory_pressure_eviction_policy_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "memory_pressure_eviction_policy.py")
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
