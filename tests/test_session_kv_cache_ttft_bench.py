from __future__ import annotations

import json

import pytest

from scripts.bench import session_kv_cache_ttft


def _records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_fake_session_kv_cache_ttft_writes_jsonl_and_warm_improves(tmp_path):
    summary = session_kv_cache_ttft.run_session_kv_cache_ttft(
        runtime="owlmlx",
        backend="fake",
        model_id="fake-small",
        model_memory_gb=1.0,
        rounds=4,
        prompt_chars=512,
        output_dir=tmp_path,
        fake_cold_prefill_ms=20.0,
        fake_warm_prefill_ms=1.0,
    )

    assert summary["ok"] is True
    assert summary["gate"] == "baseline"
    assert summary["execution_boundary"] == "runtime-kernel"
    assert summary["measurement_mode"] == "synthetic_native_prompt_cache_ttft_smoke"
    assert summary["evidence_strength"] == "smoke_only_no_real_model_or_allocator_claim"
    assert summary["warm_cache_p50_improvement_formula"] == (
        "disabled.warm_p50_first_token_ms / enabled.warm_p50_first_token_ms"
    )
    assert summary["warm_cache_p50_improvement_ratio"] >= 5.0
    assert summary["meets_5x_ttft_gate"] is True
    assert summary["disabled"]["warm_min_first_token_ms"] is not None
    assert summary["disabled"]["warm_max_first_token_ms"] is not None
    assert summary["enabled"]["warm_min_first_token_ms"] is not None
    assert summary["enabled"]["warm_max_first_token_ms"] is not None

    output_path = tmp_path / f"{summary['run_id']}.jsonl"
    records = _records(output_path)
    assert len(records) == 8
    assert {record["cache_enabled"] for record in records} == {False, True}
    assert {record["evidence_strength"] for record in records} == {
        "smoke_only_no_real_model_or_allocator_claim"
    }

    disabled = [record for record in records if record["cache_enabled"] is False]
    enabled = [record for record in records if record["cache_enabled"] is True]
    assert disabled[-1]["session_kv_cache"]["counters"]["entries_created"] == 0
    assert enabled[-1]["session_kv_cache"]["counters"]["entries_created"] == 1
    assert enabled[-1]["session_kv_cache"]["counters"]["hits"] == 3
    assert enabled[-1]["first_token_ms"] < disabled[-1]["first_token_ms"]


def test_b1a_gemma4_fake_gate_writes_part_a_ledger_schema(tmp_path):
    summary = session_kv_cache_ttft.run_session_kv_cache_ttft(
        runtime="owlmlx",
        backend="fake",
        model_id="fake-gemma4",
        model_memory_gb=1.0,
        rounds=4,
        prompt_chars=512,
        output_dir=tmp_path,
        fake_cold_prefill_ms=24.0,
        fake_warm_prefill_ms=2.0,
        gate="b1a-gemma4",
    )

    assert summary["ok"] is True
    assert summary["schema_version"] == "b1a.v1"
    assert summary["gate"] == "B-1a"
    assert summary["part"] == "A"
    assert summary["backend"] == "native"
    assert summary["backend_mode"] == "fake"
    assert summary["execution_boundary"] == "runtime-kernel"
    assert summary["config"]["execution_boundary"] == "runtime-kernel"
    assert "b1a-gemma4-31b-it-session-kv-ttft" in summary["run_id"]
    assert summary["config"]["max_tokens"] == 2
    assert summary["test_shape"]["rounds"] == 4
    assert summary["model"]["id"] == "gemma-4-31B-it"
    assert summary["model"]["runtime_model_id"] == "fake-gemma4"
    assert summary["model"]["metadata_status"] == "not_sampled_fake_backend"
    assert set(summary["subprobes"]) == {
        "A3_session_lru_eviction",
        "A4_session_ttl",
        "A5_runtime_restart",
    }
    assert all(probe["passed"] for probe in summary["subprobes"].values())
    assert summary["verdict"] == "passed"

    output_path = tmp_path / f"{summary['run_id']}.jsonl"
    assert summary["output_path"] == str(output_path)
    records = _records(output_path)
    assert len(records) == 1
    assert records[0]["run_id"] == summary["run_id"]
    assert records[0]["schema_version"] == "b1a.v1"
    assert records[0]["execution_boundary"] == "runtime-kernel"
    assert sorted(tmp_path.rglob("*.jsonl")) == [output_path]


def test_b1a_gemma4_fake_direct_native_writes_boundary_and_restart_method(tmp_path):
    summary = session_kv_cache_ttft.run_session_kv_cache_ttft(
        runtime="owlmlx",
        backend="fake",
        model_id="fake-gemma4",
        model_memory_gb=1.0,
        rounds=4,
        prompt_chars=512,
        output_dir=tmp_path,
        fake_cold_prefill_ms=24.0,
        fake_warm_prefill_ms=2.0,
        gate="b1a-gemma4",
        execution_boundary="direct-native",
    )

    assert summary["ok"] is True
    assert summary["execution_boundary"] == "direct-native"
    assert summary["config"]["execution_boundary"] == "direct-native"
    assert {round_["ok"] for round_ in summary["rounds"]} == {True}
    assert summary["subprobes"]["A5_runtime_restart"]["passed"] is True
    assert (
        summary["subprobes"]["A5_runtime_restart"]["restart_method"]
        == "direct_native_unload_load"
    )
    assert (
        summary["subprobes"]["A5_runtime_restart"][
            "runtime_kernel_restart_model_used"
        ]
        is False
    )

    records = _records(tmp_path / f"{summary['run_id']}.jsonl")
    assert records[0]["execution_boundary"] == "direct-native"


def test_b1a_gemma4_improvement_ratio_uses_disabled_over_enabled_warm_p50(tmp_path):
    summary = session_kv_cache_ttft.run_session_kv_cache_ttft(
        runtime="owlmlx",
        backend="fake",
        model_id="fake-gemma4",
        model_memory_gb=1.0,
        rounds=4,
        prompt_chars=512,
        output_dir=tmp_path,
        fake_cold_prefill_ms=30.0,
        fake_warm_prefill_ms=3.0,
        gate="b1a-gemma4",
    )

    disabled_p50 = summary["disabled_baseline"]["warm_p50_first_token_ms"]
    enabled_p50 = summary["summary"]["warm_p50_first_token_ms"]
    assert disabled_p50 is not None
    assert enabled_p50 is not None
    assert summary["improvement_ratio_p50"] == round(disabled_p50 / enabled_p50, 3)
    assert summary["summary"]["A1_warm_ttft_improvement"]["passed"] is True
    assert summary["summary"]["A2_hit_miss_counters"]["passed"] is True


def test_session_kv_cache_ttft_cli_b1a_gate_applies_defaults(monkeypatch, tmp_path):
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(session_kv_cache_ttft, "run_session_kv_cache_ttft", fake_run)

    code = session_kv_cache_ttft.main(
        [
            "--gate",
            "b1a-gemma4",
            "--backend",
            "fake",
            "--output",
            str(tmp_path),
        ]
    )

    assert code == 0
    assert captured["gate"] == "b1a-gemma4"
    assert captured["model_id"] == session_kv_cache_ttft.B1A_MODEL_PATH
    assert captured["rounds"] == 4
    assert captured["prompt_chars"] == 4200
    assert captured["max_tokens"] == 2
    assert captured["output_dir"] == tmp_path
    assert captured["execution_boundary"] == "auto"


def test_session_kv_cache_ttft_cli_auto_boundary_passes_through_for_b1a_native(
    monkeypatch,
    tmp_path,
):
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(session_kv_cache_ttft, "run_session_kv_cache_ttft", fake_run)

    code = session_kv_cache_ttft.main(
        [
            "--gate",
            "b1a-gemma4",
            "--backend",
            "native",
            "--output",
            str(tmp_path),
        ]
    )

    assert code == 0
    assert captured["backend"] == "native"
    assert captured["execution_boundary"] == "auto"
    assert (
        session_kv_cache_ttft._resolve_execution_boundary(
            execution_boundary=captured["execution_boundary"],
            gate=captured["gate"],
            backend=captured["backend"],
        )
        == "direct-native"
    )


def test_session_kv_cache_ttft_requires_owlmlx_runtime(tmp_path):
    with pytest.raises(ValueError, match="only --runtime owlmlx"):
        session_kv_cache_ttft.run_session_kv_cache_ttft(
            runtime="omlx",
            backend="fake",
            model_id="m",
            model_memory_gb=1.0,
            rounds=2,
            prompt_chars=128,
            output_dir=tmp_path,
        )


def test_session_kv_cache_ttft_requires_warm_round(tmp_path):
    with pytest.raises(ValueError, match="--rounds must be >= 2"):
        session_kv_cache_ttft.run_session_kv_cache_ttft(
            runtime="owlmlx",
            backend="fake",
            model_id="m",
            model_memory_gb=1.0,
            rounds=1,
            prompt_chars=128,
            output_dir=tmp_path,
        )


def test_session_kv_cache_ttft_cli_reports_usage_failure(monkeypatch, tmp_path):
    def fail_run(**kwargs):
        _ = kwargs
        raise RuntimeError("boom")

    monkeypatch.setattr(session_kv_cache_ttft, "run_session_kv_cache_ttft", fail_run)

    code = session_kv_cache_ttft.main(
        [
            "--runtime",
            "owlmlx",
            "--backend",
            "fake",
            "--output",
            str(tmp_path),
        ]
    )

    assert code == 2
