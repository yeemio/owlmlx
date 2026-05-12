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
    assert summary["measurement_mode"] == "synthetic_native_prompt_cache_ttft_smoke"
    assert summary["evidence_strength"] == "smoke_only_no_real_model_or_allocator_claim"
    assert summary["warm_cache_p50_improvement_ratio"] >= 5.0
    assert summary["meets_5x_ttft_gate"] is True

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
