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


def test_b1c1_fake_no_swap_soak_writes_gap_free_blocked_ledger_and_rollup(tmp_path):
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

    assert summary["ok"] is False
    assert summary["no_swap_soak_stability"] == "blocked"
    assert summary["graduates"]["unblock_B_1c_section_2"] is False
    assert summary["samples"] == 6
    assert summary["warmup_samples"] == 3
    assert summary["measurement_samples"] == 3
    assert summary["ledger_gap_free"] is True
    assert summary["warmup_cycle_complete"] is True
    assert summary["session_mix_complete"] is True
    assert summary["session_mix_balanced"] is True
    assert summary["claimable_24h_duration"] is False
    assert summary["allocator_truth_claimable"] is False
    assert summary["hard_failure"] is False
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
        record["config"]["OWLMLX_SESSION_CACHE_TTL_S"] >= 90000.0
        for record in ledger
    )
    assert all(
        record["operation"]["artificial_unload_or_swap_during_soak"] is False
        for record in ledger
    )
    assert all(
        record["config"]["session_id"].startswith("b1c1-no-swap-")
        for record in ledger
    )
    assert rollup[0]["no_swap_soak_stability"] == "blocked"


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


def test_b1c1_duration_clock_starts_after_warmup(tmp_path):
    summary = eviction_soak.run_b1c1_no_swap_soak(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        output_dir=tmp_path,
        duration_s=0.0,
        required_duration_s=0.0,
        sample_interval_s=0.0,
    )

    assert summary["warmup_samples"] == 3
    assert summary["measurement_samples"] == 1
    assert summary["duration_requirement_met"] is True
    assert summary["claimable_24h_duration"] is False
    assert summary["session_mix_complete"] is False
    assert summary["ok"] is False


def test_b1c1_warmup_cycle_is_required_for_graduation(tmp_path):
    summary = eviction_soak.run_b1c1_no_swap_soak(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        output_dir=tmp_path,
        duration_s=0.0,
        required_duration_s=0.0,
        sample_interval_s=0.0,
        max_samples=3,
        warmup_cycles=0,
    )

    assert summary["warmup_samples"] == 0
    assert summary["measurement_samples"] == 3
    assert summary["warmup_cycle_complete"] is False
    assert summary["session_mix_complete"] is True
    assert summary["no_swap_soak_stability"] == "blocked"
    assert summary["graduates"]["unblock_B_1c_section_2"] is False


def test_b1c1_generation_failure_is_failed_not_blocked(monkeypatch, tmp_path):
    async def failed_generation(*args, **kwargs):
        return eviction_soak.StreamGenerationResult(
            ok=False,
            message="synthetic failure",
            error_code=eviction_soak.RuntimeErrorCode.backend_error,
            model_id="gemma-4-31B-it",
        )

    monkeypatch.setattr(eviction_soak, "_stream_generate_once", failed_generation)

    summary = eviction_soak.run_b1c1_no_swap_soak(
        runtime="owlmlx",
        backend="fake",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        output_dir=tmp_path,
        duration_s=0.0,
        required_duration_s=24 * 60 * 60,
        sample_interval_s=0.0,
        max_samples=6,
    )

    assert summary["samples"] == 1
    assert summary["hard_failure"] is True
    assert summary["no_swap_soak_stability"] == "failed"
    assert summary["graduates"]["unblock_B_1c_section_2"] is False


def _write_b1c1_segment_rollup(
    path,
    *,
    run_id,
    duration_s=28800.0,
    conclusion="blocked",
    hard_failure=False,
    expirations_total=0,
):
    payload = {
        "schema_version": "b1c1.v1",
        "gate": "B-1c section 1",
        "run_id": run_id,
        "backend": "native",
        "measurement_mode": eviction_soak.MlxMemorySampler.measurement_mode,
        "measurement_duration_s": duration_s,
        "ledger_gap_free": True,
        "warmup_cycle_complete": True,
        "session_mix_complete": True,
        "session_mix_balanced": True,
        "max_drift_within_budget": True,
        "fatal_watermark_count": 0,
        "session_cache_drops_total": 0,
        "session_cache_expirations_total": expirations_total,
        "session_cache_rejects_total": 0,
        "failure_measurement_count": 0,
        "unresolved_reclaim_barrier_events": 0,
        "hard_failure": hard_failure,
        "no_swap_soak_stability": conclusion,
        "interrupted_no_swap_rehearsal": {
            "rehearsal_group_id": "b1c1-rehearsal",
            "rehearsal_segment_id": run_id,
            "segment_duration_s": duration_s,
            "interruption_reason": "planned_stop",
            "resumes_prior_segment": run_id != "segment-1",
            "aggregate_measurement_duration_s": duration_s,
            "no_swap_soak_stability": "blocked",
        },
    }
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def test_b1c1_interrupted_rehearsal_aggregates_segments_without_graduating(tmp_path):
    rollups = []
    for index in range(1, 4):
        path = tmp_path / f"segment-{index}-rollup.jsonl"
        _write_b1c1_segment_rollup(path, run_id=f"segment-{index}")
        rollups.append(path)

    summary = eviction_soak.run_b1c1_interrupted_rehearsal(
        segment_rollups=rollups,
        output_dir=tmp_path,
        run_id="aggregate",
        rehearsal_group_id="b1c1-rehearsal",
        required_total_duration_s=86400.0,
    )

    assert summary["ok"] is True
    assert summary["interrupted_no_swap_rehearsal"] == "passed"
    assert summary["aggregate_measurement_duration_s"] == 86400.0
    assert summary["duration_requirement_met"] is True
    assert summary["all_segments_ok_for_rehearsal"] is True
    assert summary["no_swap_soak_stability"] == "blocked"
    assert summary["graduates"]["interrupted_no_swap_rehearsal"] is True
    assert summary["graduates"]["no_swap_soak_stability"] is False
    assert summary["graduates"]["unblock_B_1c_section_2"] is False

    written = _records(tmp_path / summary["rollup_path"].split("/")[-1])
    assert len(written) == 1
    assert written[0]["schema_version"] == "b1c1.rehearsal.v1"
    assert written[0]["segments"][1]["resumes_prior_segment"] is True


def test_b1c1_interrupted_rehearsal_failure_stays_failed(tmp_path):
    first = tmp_path / "segment-1-rollup.jsonl"
    second = tmp_path / "segment-2-rollup.jsonl"
    _write_b1c1_segment_rollup(first, run_id="segment-1")
    _write_b1c1_segment_rollup(
        second,
        run_id="segment-2",
        conclusion="failed",
        hard_failure=True,
    )

    summary = eviction_soak.run_b1c1_interrupted_rehearsal(
        segment_rollups=[first, second],
        output_dir=tmp_path,
        run_id="aggregate-failed",
        required_total_duration_s=1.0,
    )

    assert summary["ok"] is False
    assert summary["interrupted_no_swap_rehearsal"] == "failed"
    assert summary["no_swap_soak_stability"] == "blocked"
    assert summary["graduates"]["interrupted_no_swap_rehearsal"] is False


def test_b1c1_interrupted_rehearsal_blocks_expiring_segments(tmp_path):
    segment = tmp_path / "segment-expired-rollup.jsonl"
    _write_b1c1_segment_rollup(
        segment,
        run_id="segment-expired",
        duration_s=86400.0,
        expirations_total=1,
    )

    summary = eviction_soak.run_b1c1_interrupted_rehearsal(
        segment_rollups=[segment],
        output_dir=tmp_path,
        run_id="aggregate-expired",
        required_total_duration_s=86400.0,
    )

    assert summary["ok"] is False
    assert summary["interrupted_no_swap_rehearsal"] == "blocked"
    assert summary["all_segments_ok_for_rehearsal"] is False
    assert summary["no_swap_soak_stability"] == "blocked"


def test_b1c1_interrupted_rehearsal_rejects_empty_segment_list(tmp_path):
    with pytest.raises(ValueError, match="segment-rollup is required"):
        eviction_soak.run_b1c1_interrupted_rehearsal(
            segment_rollups=[],
            output_dir=tmp_path,
        )


def test_cli_b1c1_interrupted_rehearsal_writes_aggregate_rollup(tmp_path):
    segment = tmp_path / "segment-rollup.jsonl"
    output_dir = tmp_path / "out"
    _write_b1c1_segment_rollup(segment, run_id="segment-cli", duration_s=12.0)

    code = eviction_soak.main(
        [
            "--gate",
            eviction_soak.B1C1_REHEARSAL_GATE,
            "--output",
            str(output_dir),
            "--segment-rollup",
            str(segment),
            "--aggregate-required-duration-s",
            "1",
            "--rehearsal-group-id",
            "cli-rehearsal",
        ]
    )

    assert code == 0
    rollups = list(output_dir.glob("*interrupted-no-swap-rehearsal-rollup.jsonl"))
    assert len(rollups) == 1
    record = _records(rollups[0])[0]
    assert record["schema_version"] == "b1c1.rehearsal.v1"
    assert record["rehearsal_group_id"] == "cli-rehearsal"
    assert record["interrupted_no_swap_rehearsal"] == "passed"
    assert record["no_swap_soak_stability"] == "blocked"
