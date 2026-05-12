from __future__ import annotations

import json

import pytest

from scripts.bench import eviction_soak


def _records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_fake_backend_smoke_writes_jsonl_and_no_allocator_claim(tmp_path):
    summary = eviction_soak.run_eviction_soak(
        runtime="owlmlx",
        backend="fake",
        model_a=eviction_soak.ModelSpec("small-a", 1.0),
        model_b=eviction_soak.ModelSpec("small-b", 1.5),
        rounds=3,
        output_dir=tmp_path,
    )

    assert summary["ok"] is True
    assert summary["total_drift_gb"] == 0.0
    assert summary["measurement_mode"] == "synthetic_runtime_inventory_smoke"

    output_path = tmp_path / f"{summary['run_id']}.jsonl"
    records = _records(output_path)
    assert len(records) == 3
    assert {record["evidence_strength"] for record in records} == {
        "smoke_only_no_allocator_claim"
    }
    assert records[0]["switch"] == "small-b\u2192small-a"
    assert records[1]["switch"] == "small-a\u2192small-b"
    assert records[0]["active_memory_gb_after_unload_settled"] == 0.0
    assert records[0]["load_result"]["ok"] is True
    assert records[0]["generate_result"]["ok"] is True
    assert records[0]["unload_result"]["ok"] is True


def test_only_owlmlx_runtime_is_implemented(tmp_path):
    with pytest.raises(ValueError, match="only --runtime owlmlx"):
        eviction_soak.run_eviction_soak(
            runtime="omlx",
            backend="fake",
            model_a=eviction_soak.ModelSpec("a", 1.0),
            model_b=eviction_soak.ModelSpec("b", 1.0),
            rounds=1,
            output_dir=tmp_path,
        )


def test_native_backend_reports_missing_mlx_as_usage_failure(monkeypatch, tmp_path):
    def fail_create():
        raise RuntimeError("native eviction soak requires mlx.core")

    monkeypatch.setattr(eviction_soak.MlxMemorySampler, "create", fail_create)

    code = eviction_soak.main(
        [
            "--runtime",
            "owlmlx",
            "--backend",
            "native",
            "--rounds",
            "1",
            "--output",
            str(tmp_path),
        ]
    )

    assert code == 2


def test_drift_summary_fails_when_settled_memory_exceeds_threshold():
    records = [
        {"ok": True, "active_memory_gb_after_unload_settled": 0.0},
        {"ok": True, "active_memory_gb_after_unload_settled": 0.75},
    ]

    summary = eviction_soak._record_summary(records, max_drift_gb=0.5)

    assert summary["ok"] is False
    assert summary["total_drift_gb"] == 0.75
