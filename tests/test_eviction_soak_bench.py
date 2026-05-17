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


def test_b1b_gate_both_mode_writes_two_ledgers_and_rollup(tmp_path):
    summary = eviction_soak.run_b1b_cache_on_no_regress(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        rounds=2,
        output_dir=tmp_path,
    )

    assert summary["ok"] is True
    assert summary["cache_on_no_regress"] == "passed"
    assert summary["baseline_rounds"] == 2
    assert summary["candidate_rounds"] == 2
    assert summary["candidate_warm_hits"] == 2

    baseline_path = tmp_path / summary["baseline_ledger"].split("/")[-1]
    candidate_path = tmp_path / summary["candidate_ledger"].split("/")[-1]
    rollup_path = tmp_path / summary["rollup_path"].split("/")[-1]
    assert baseline_path.exists()
    assert candidate_path.exists()
    assert rollup_path.exists()

    baseline = _records(baseline_path)
    candidate = _records(candidate_path)
    rollup = _records(rollup_path)
    assert len(baseline) == 2
    assert len(candidate) == 2
    assert len(rollup) == 1
    assert {record["mode"] for record in baseline} == {"cache_off_baseline"}
    assert {record["mode"] for record in candidate} == {"cache_on_candidate"}
    assert rollup[0]["candidate_ledger"] == str(candidate_path)


def test_b1b_cache_on_candidate_records_session_id_and_synthetic_warm_hit(tmp_path):
    summary = eviction_soak.run_b1b_cache_on_no_regress(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        rounds=1,
        output_dir=tmp_path,
        cache_mode="on",
        session_id_prefix="b1b-test-session",
    )

    candidate = _records(tmp_path / summary["candidate_ledger"].split("/")[-1])
    assert len(candidate) == 1
    record = candidate[0]
    assert record["config"]["OWLMLX_SESSION_CACHE_ENABLED"] == "1"
    assert record["config"]["session_id"] == "b1b-test-session-r1"
    assert record["session_cache"]["warm_request_hit"] is True
    assert record["session_cache"]["hits_delta"] == 1
    assert record["session_cache"]["misses_delta"] == 1
    assert record["session_cache"]["drops_delta"] == 0
    assert record["session_cache"]["synthetic"] is True
    assert record["session_cache"]["allocator_truth"] is False
    assert len(record["generate_results"]) == 2
    assert summary["required_ledgers_present"] is False
    assert summary["cache_on_no_regress"] == "blocked"
    assert summary["ok"] is False


def test_b1b_rollup_fails_if_candidate_has_drops_or_failure_counts(tmp_path):
    run_id = "b1b-test-run"
    baseline = [
        {
            "operation": {
                "unload_ok": True,
                "settle_barrier_duration_ms": 1.0,
            },
            "session_cache": {"warm_request_hit": None, "drops_delta": 0},
            "settle_barrier_event": {"barrier_state": "clean"},
            "reclaim_barrier_stats_after_round": {
                "summary": {
                    "failure_measurement_count": 0,
                    "unresolved_event_count": 0,
                },
                "missing_signals": [],
            },
            "round_verdict": "passed",
        }
    ]
    candidate = [
        {
            "operation": {
                "unload_ok": True,
                "settle_barrier_duration_ms": 1.0,
            },
            "session_cache": {"warm_request_hit": True, "drops_delta": 1},
            "settle_barrier_event": {"barrier_state": "clean"},
            "reclaim_barrier_stats_after_round": {
                "summary": {
                    "failure_measurement_count": 1,
                    "unresolved_event_count": 0,
                },
                "missing_signals": [],
            },
            "round_verdict": "failed",
        }
    ]

    rollup = eviction_soak._b1b_rollup(
        run_id=run_id,
        baseline_records=baseline,
        candidate_records=candidate,
        baseline_ledger=tmp_path / "baseline.jsonl",
        candidate_ledger=tmp_path / "candidate.jsonl",
    )

    assert rollup["candidate_drops_total"] == 1
    assert rollup["failure_measurement_count"] == 1
    assert rollup["cache_on_no_regress"] == "failed"
    assert rollup["conclusion"] == "failed"


def test_b1b_rollup_blocks_without_both_required_ledgers(tmp_path):
    summary = eviction_soak.run_b1b_cache_on_no_regress(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        rounds=1,
        output_dir=tmp_path,
        cache_mode="off",
    )

    assert summary["baseline_rounds"] == 1
    assert summary["candidate_rounds"] == 0
    assert summary["required_ledgers_present"] is False
    assert summary["cache_on_no_regress"] == "blocked"
    assert summary["graduates"]["cache_on_no_regress"] is False
    assert summary["ok"] is False


def test_b1c1_fake_no_swap_soak_writes_gap_free_ledger_and_rollup(tmp_path):
    summary = eviction_soak.run_b1c1_no_swap_soak(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        model_label="gemma-4-31B-it",
        output_dir=tmp_path,
        duration_s=0.0,
        required_duration_s=0.0,
        sample_interval_s=0.0,
        max_samples=6,
    )

    assert summary["ok"] is True
    assert summary["no_swap_soak_stability"] == "passed"
    assert summary["graduates"]["unblock_B_1c_section_2"] is True
    assert summary["samples"] == 6
    assert summary["warmup_samples"] == 3
    assert summary["measurement_samples"] == 3
    assert summary["ledger_gap_free"] is True
    assert summary["session_mix_balanced"] is True
    assert summary["prompt_mix_counts"] == {"short": 1, "medium": 1, "long": 1}
    assert summary["fatal_watermark_count"] == 0
    assert summary["failure_measurement_count"] == 0
    assert summary["cleanup_unload_result"]["ok"] is True

    ledger = _records(tmp_path / summary["ledger"].split("/")[-1])
    rollup = _records(tmp_path / summary["rollup_path"].split("/")[-1])
    assert len(ledger) == 6
    assert len(rollup) == 1
    assert [record["sample_index"] for record in ledger] == [1, 2, 3, 4, 5, 6]
    assert [record["phase"] for record in ledger[:3]] == ["warmup", "warmup", "warmup"]
    assert [record["phase"] for record in ledger[3:]] == [
        "measurement",
        "measurement",
        "measurement",
    ]
    assert {record["mode"] for record in ledger} == {"no_swap_soak"}
    assert {record["config"]["OWLMLX_SESSION_CACHE_ENABLED"] for record in ledger} == {"1"}
    assert all(
        record["operation"]["artificial_unload_or_swap_during_soak"] is False
        for record in ledger
    )
    assert all(
        record["config"]["session_id"].startswith("b1c1-no-swap-")
        for record in ledger
    )
    assert rollup[0]["no_swap_soak_stability"] == "passed"


def test_b1c1_short_run_blocks_instead_of_claiming_24h_soak(tmp_path):
    summary = eviction_soak.run_b1c1_no_swap_soak(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        output_dir=tmp_path,
        duration_s=0.0,
        required_duration_s=24 * 60 * 60,
        sample_interval_s=0.0,
        max_samples=1,
    )

    assert summary["ok"] is False
    assert summary["duration_requirement_met"] is False
    assert summary["no_swap_soak_stability"] == "blocked"
    assert summary["graduates"]["no_swap_soak_stability"] is False
