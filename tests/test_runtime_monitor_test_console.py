from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.model_release_candidate_history import ModelReleaseCandidateLedger
from owlmlx.model_release_candidate_record import build_model_release_candidate_record
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime_model_visibility import RegisteredRuntimeVisibleModel


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def _large_profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=128.0,
        system_reserve_gb=8.0,
        serving_budget_gb=120.0,
        warning_threshold_gb=112.0,
    )


def _normal_host_pressure() -> dict:
    return {
        "available": True,
        "source": "memory_pressure",
        "classification": "normal",
        "reason_code": "free_percent_above_warning_threshold",
        "reason_message": "Host free memory is above threshold.",
        "free_percent": 80.0,
    }


def _seed_model_rc_record(
    ledger_path,
    model_dir,
    *,
    model_id: str = "Qwen3.6-35B-A3B",
    peak_resident_set_bytes: int = 4 * 1024**3,
) -> None:
    ModelReleaseCandidateLedger(ledger_path).append(
        build_model_release_candidate_record(
            created_at="2026-05-06T00:00:00Z",
            model_id=model_id,
            lane="mainline",
            runtime_url="http://127.0.0.1:8066",
            host_class="test-host",
            artifact_path=str(model_dir),
            visibility_status="visible",
            load_result={"status": "pass", "detail": "loaded"},
            generation_result={"status": "pass", "detail": "generated"},
            unload_result={"status": "pass", "detail": "unloaded"},
            reload_result={"status": "pass", "detail": "reloaded"},
            repeat_count=2,
            failure_count=0,
            first_token_latency_ms=1200.0,
            tokens_per_second=4.0,
            wall_clock_ms=2500.0,
            peak_resident_set_bytes=peak_resident_set_bytes,
            memory_headroom_bytes=2 * 1024**3,
            output_sanity_label="ok",
            owlops_observation_path="files/evidence/owlmlx/model-release-candidates/test",
            verdict="needs_optimization",
            blockers=("decode_speed_below_target",),
            ttft_ms=1200.0,
            decode_tokens_per_second=3.5,
            memory_peak_source="process_tree_rss",
        )
    )


def test_monitor_snapshot_exposes_clean_idle_degraded_and_model_rc_history(tmp_path) -> None:
    models_root = tmp_path / "models"
    model_dir = models_root / "Qwen3.6-35B-A3B"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    ledger_path = tmp_path / "model-rc-ledger.jsonl"
    _seed_model_rc_record(ledger_path, model_dir)
    client = TestClient(
        create_app(
            RuntimeKernel(FakeBackend(), profile=_profile()),
            visibility_models_root=str(models_root),
            visibility_registry=[RegisteredRuntimeVisibleModel("Qwen3.6-35B-A3B")],
            model_release_candidate_ledger_path=str(ledger_path),
        )
    )

    response = client.get("/v1/runtime/monitor/snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.runtime.monitor.snapshot"
    assert payload["contract"]["version"] == "v1"
    assert payload["service"]["ok"] is True
    assert payload["service"]["readiness"] == "degraded"
    assert payload["service"]["health_classification"] == "healthy_clean_idle"
    assert payload["service"]["clean_idle_degraded"] is True
    assert payload["release_candidates"]["ledger_status"] == "available"
    assert payload["release_candidates"]["history_count"] == 1
    latest = payload["release_candidates"]["latest_by_model"]["Qwen3.6-35B-A3B"]
    assert latest["verdict"] == "needs_optimization"
    assert latest["evidence_path"] == "files/evidence/owlmlx/model-release-candidates/test"
    source_names = {source["name"] for source in payload["sources"]}
    assert {"runtime_status", "model_load_admission", "model_release_candidate_ledger"} <= source_names


def test_monitor_history_records_runtime_owned_snapshot_samples(tmp_path) -> None:
    trend_ledger = tmp_path / "runtime-monitor-trends.jsonl"
    client = TestClient(
        create_app(
            RuntimeKernel(
                FakeBackend(),
                profile=_profile(),
                host_pressure_sampler=_normal_host_pressure,
            ),
            runtime_monitor_trend_ledger_path=str(trend_ledger),
        )
    )

    first = client.get("/v1/runtime/monitor/snapshot")
    second = client.get("/v1/runtime/monitor/snapshot")
    history = client.get("/v1/runtime/monitor/history?limit=10")

    assert first.status_code == 200
    assert second.status_code == 200
    assert history.status_code == 200
    payload = history.json()
    assert payload["contract"]["surface"] == "owlmlx.runtime.monitor.history"
    assert payload["ledger_status"] == "available"
    assert payload["ledger_path"] == str(trend_ledger)
    assert payload["history_count"] == 2
    assert trend_ledger.exists()
    sample = payload["samples"][-1]
    assert sample["contract"]["surface"] == "owlmlx.runtime.monitor.sample"
    assert sample["source"] == "runtime_monitor_snapshot_route"
    assert sample["truth_level"] == "runtime_owned"
    assert sample["service"]["health_classification"] == "healthy_clean_idle"
    assert sample["resources"]["available_gb"] == 6.0
    assert sample["test_runs"]["known_run_count"] == 0
    assert sample["policy_boundaries"]["does_not_load_model"] is True
    assert sample["policy_boundaries"]["does_not_generate"] is True


def test_monitor_background_sampler_writes_history_without_model_work(tmp_path) -> None:
    trend_ledger = tmp_path / "runtime-monitor-background.jsonl"
    app = create_app(
        RuntimeKernel(
            FakeBackend(),
            profile=_profile(),
            host_pressure_sampler=_normal_host_pressure,
        ),
        runtime_monitor_trend_ledger_path=str(trend_ledger),
        runtime_monitor_sample_interval_s=0.01,
        runtime_monitor_url="http://127.0.0.1:8066",
    )

    with TestClient(app) as client:
        for _ in range(30):
            history = client.get("/v1/runtime/monitor/history?limit=5")
            if history.status_code == 200 and history.json()["history_count"] > 0:
                break
            time.sleep(0.02)

        payload = history.json()
        assert payload["history_count"] > 0
        sample = payload["samples"][-1]
        assert sample["source"] == "runtime_monitor_background_sampler"
        assert sample["runtime_url"] == "http://127.0.0.1:8066"
        assert sample["policy_boundaries"]["does_not_abort_process"] is True
        assert client.get("/healthz").json()["active_model_id"] is None


def test_test_run_preflight_returns_unknown_when_model_visibility_absent() -> None:
    client = TestClient(
        create_app(
            RuntimeKernel(
                FakeBackend(),
                profile=_profile(),
                host_pressure_sampler=_normal_host_pressure,
            )
        )
    )

    response = client.post(
        "/v1/runtime/test-runs/preflight",
        json={
            "model_id": "Qwen3.6-27B",
            "test_profile_id": "qwen36-27b-decode",
            "mode": "live",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.runtime.test_run.preflight"
    assert payload["decision"] == "unknown"
    assert payload["reason"] == "known_peak_missing"
    assert payload["host_pressure"]["classification"] == "normal"
    assert payload["policy_boundaries"]["read_only"] is True
    assert payload["policy_boundaries"]["does_not_load_model"] is True
    assert payload["required_operator_confirmation"]["required"] is True


def test_test_run_preflight_defers_when_generation_gate_busy() -> None:
    runtime = RuntimeKernel(FakeBackend(), profile=_profile())
    with runtime.generation_gate._condition:
        runtime.generation_gate._active = True
    client = TestClient(create_app(runtime))

    response = client.post(
        "/v1/runtime/test-runs/preflight",
        json={
            "model_id": "Qwen3.6-27B",
            "test_profile_id": "qwen36-27b-decode",
            "mode": "live",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "defer"
    assert payload["reason"] == "generation_gate_busy"
    assert payload["generation_gate"]["generation_gate"] == "active"


def test_test_run_launch_requires_audit_ledger_and_abort_is_audited() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    launch = client.post(
        "/v1/runtime/test-runs",
        json={
            "model_id": "gemma-4-31B-it",
            "test_profile_id": "gemma-repetitive-output-template",
            "mode": "live",
        },
    )
    assert launch.status_code == 503
    launch_payload = launch.json()
    assert launch_payload["status"] == "unsupported"
    assert launch_payload["unsupported_feature"] == "runtime_test_run_ledger"
    assert launch_payload["preflight"]["contract"]["surface"] == "owlmlx.runtime.test_run.preflight"
    assert launch_payload["policy_boundaries"]["does_not_touch_legacy_listeners"] == ["8001", "8009"]

    index = client.get("/v1/runtime/test-runs")
    assert index.status_code == 200
    assert index.json()["contract"]["surface"] == "owlmlx.runtime.test_run.index"

    monitor_events = client.get("/v1/runtime/monitor/events")
    assert monitor_events.status_code == 200
    assert monitor_events.headers["content-type"].startswith("text/event-stream")

    run_events = client.get("/v1/runtime/test-runs/run_missing/events")
    assert run_events.status_code == 404
    assert run_events.json()["status"] == "not_found"

    missing_abort = client.post("/v1/runtime/test-runs/run_missing/abort")
    assert missing_abort.status_code == 404
    assert missing_abort.json()["status"] == "not_found"

    client.app.state.runtime_test_runs["run_active"] = {
        "run_id": "run_active",
        "status": "running",
        "phase": "generate",
    }
    status = client.get("/v1/runtime/test-runs/run_active")
    assert status.status_code == 200
    assert status.json()["run"]["phase"] == "generate"

    abort = client.post("/v1/runtime/test-runs/run_active/abort")
    assert abort.status_code == 202
    assert abort.json()["status"] == "aborting"
    assert abort.json()["policy_boundaries"]["does_not_abort_process"] is True


def test_runtime_test_run_registry_launches_worker_and_replays_events(tmp_path) -> None:
    ledger_path = tmp_path / "runtime-test-runs.jsonl"
    model_rc_ledger = tmp_path / "model-rc-ledger.jsonl"
    models_root = tmp_path / "models"
    model_dir = models_root / "Qwen3.6-27B"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    _seed_model_rc_record(
        model_rc_ledger,
        model_dir,
        model_id="Qwen3.6-27B",
        peak_resident_set_bytes=1 * 1024**3,
    )
    app = create_app(
        RuntimeKernel(
            FakeBackend(),
            profile=_large_profile(),
            host_pressure_sampler=_normal_host_pressure,
        ),
        visibility_models_root=str(models_root),
        visibility_registry=[RegisteredRuntimeVisibleModel("Qwen3.6-27B")],
        model_release_candidate_ledger_path=str(model_rc_ledger),
        runtime_test_run_ledger_path=str(ledger_path),
    )

    with TestClient(app) as client:
        launch = client.post(
            "/v1/runtime/test-runs",
            json={
                "model_id": "Qwen3.6-27B",
                "test_profile_id": "qwen36-27b-decode",
                "mode": "live",
                "parameters": {"max_tokens": 8, "memory_gb": 1, "repeat_count": 1},
                "operator": {"surface": "owlops", "session_id": "test-session"},
            },
        )

        assert launch.status_code == 202
        launch_payload = launch.json()
        assert launch_payload["status"] == "queued"
        assert launch_payload["launch_decision"] == "accepted"
        assert launch_payload["audit_ledger_status"] == "available"
        run_id = launch_payload["run_id"]
        assert run_id.startswith("run_")
        assert ledger_path.exists()
        assert launch_payload["run"]["status"] == "queued"
        assert launch_payload["run"]["preflight_decision"] == "admit"
        assert launch_payload["run"]["operator"]["surface"] == "owlops"

        index = client.get("/v1/runtime/test-runs")
        assert index.status_code == 200
        index_payload = index.json()
        assert index_payload["audit_ledger_status"] == "available"
        assert index_payload["audit_ledger_path"] == str(ledger_path)
        assert [run["run_id"] for run in index_payload["runs"]] == [run_id]

        status = client.get(f"/v1/runtime/test-runs/{run_id}")
        assert status.status_code == 200
        status_payload = status.json()
        assert status_payload["run"]["launch_decision"] == "accepted"
        assert status_payload["run"]["status"] in {"queued", "running", "succeeded"}

        snapshot = client.get("/v1/runtime/monitor/snapshot")
        assert snapshot.status_code == 200
        assert snapshot.json()["test_runs"]["audit_ledger_status"] == "available"
        assert snapshot.json()["test_runs"]["known_run_count"] == 1

        for _ in range(80):
            status = client.get(f"/v1/runtime/test-runs/{run_id}")
            if status.json()["run"]["status"] == "succeeded":
                break
            time.sleep(0.05)
        final = client.get(f"/v1/runtime/test-runs/{run_id}").json()["run"]
        assert final["status"] == "succeeded"
        assert final["metrics"]["output_tokens"] > 0
        assert final["evidence_path"]

        events = client.get(f"/v1/runtime/test-runs/{run_id}/events")
        assert events.status_code == 200
        assert events.headers["content-type"].startswith("text/event-stream")
        assert "test_run.preflight_completed" in events.text
        assert "test_run.launch_accepted" in events.text
        assert "test_run.generate_completed" in events.text
        assert "test_run.completed" in events.text

        after = client.get("/healthz").json()
        assert after["active_model_id"] is None
        assert after["model_count"] == 0
