from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

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


def test_b1c1_rollup_blocks_when_measurement_wall_clock_has_sleep_gap(tmp_path):
    now = time.monotonic()
    base = {
        "schema_version": "b1c1.v1",
        "gate": "B-1c section 1",
        "mode": "no_swap_soak",
        "sample_verdict": "passed",
        "config": {"sample_interval_s": 60.0},
        "memory": {
            "drift_from_measurement_start_bytes": 0,
            "watermark_after_generation": "GREEN",
        },
        "session_cache": {"counter_delta": {}},
        "reclaim_barrier_stats_after_sample": {
            "summary": {
                "failure_measurement_count": 0,
                "unresolved_event_count": 0,
            }
        },
    }
    records = [
        {
            **base,
            "sample_index": 1,
            "phase": "warmup",
            "prompt_id": "short",
            "timestamp_utc": "2026-05-18T00:00:00Z",
        },
        {
            **base,
            "sample_index": 2,
            "phase": "warmup",
            "prompt_id": "medium",
            "timestamp_utc": "2026-05-18T00:00:01Z",
        },
        {
            **base,
            "sample_index": 3,
            "phase": "warmup",
            "prompt_id": "long",
            "timestamp_utc": "2026-05-18T00:00:02Z",
        },
        {
            **base,
            "sample_index": 4,
            "phase": "measurement",
            "prompt_id": "short",
            "timestamp_utc": "2026-05-18T00:01:02Z",
        },
        {
            **base,
            "sample_index": 5,
            "phase": "measurement",
            "prompt_id": "medium",
            "timestamp_utc": "2026-05-18T01:01:02Z",
        },
        {
            **base,
            "sample_index": 6,
            "phase": "measurement",
            "prompt_id": "long",
            "timestamp_utc": "2026-05-18T01:02:02Z",
        },
    ]

    rollup = eviction_soak._b1c1_rollup(
        run_id="b1c1-wall-gap",
        model=eviction_soak.ModelSpec("gemma-4-31B-it", 1.0),
        model_label="gemma-4-31B-it",
        backend="native",
        measurement_mode=eviction_soak.MlxMemorySampler.measurement_mode,
        output_path=tmp_path / "ledger.jsonl",
        records=records,
        started_monotonic_s=now - 90000.0,
        measurement_started_monotonic_s=now - 90000.0,
        measurement_finished_monotonic_s=now,
        required_duration_s=86400.0,
        drift_budget_bytes=eviction_soak.B1C1_DRIFT_BUDGET_BYTES,
        load=SimpleNamespace(ok=True, message="loaded", error_code=None, model_id=None),
        cleanup_unload=SimpleNamespace(
            ok=True,
            message="unloaded",
            error_code=None,
            model_id="gemma-4-31B-it",
            freed_gb=1.0,
        ),
        cleanup_settle=eviction_soak.SettleResult(
            active_memory_bytes=0,
            iterations=1,
            duration_ms=0.0,
        ),
    )

    assert rollup["duration_requirement_met"] is True
    assert rollup["ledger_gap_free"] is True
    assert rollup["measurement_wall_clock_gap_free"] is False
    assert rollup["wall_clock_continuity"]["measurement_wall_clock_gap_violation_count"] == 1
    assert rollup["wall_clock_continuity"]["max_measurement_wall_clock_gap_s"] == 3600.0
    assert rollup["hard_failure"] is False
    assert rollup["no_swap_soak_stability"] == "blocked"
    assert rollup["graduates"]["no_swap_soak_stability"] is False


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


def test_cli_b1c1_sigterm_writes_blocked_segment_rollup(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "scripts/bench/eviction_soak.py",
            "--gate",
            eviction_soak.B1C1_GATE,
            "--backend",
            "fake",
            "--output",
            str(tmp_path),
            "--duration-s",
            "60",
            "--required-duration-s",
            "86400",
            "--sample-interval-s",
            "10",
            "--warmup-cycles",
            "1",
            "--max-tokens",
            "1",
            "--interruption-reason",
            "planned_stop",
        ],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        ledger_path = None
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            ledgers = sorted(tmp_path.glob("*b1c1-*-no-swap-soak.jsonl"))
            if ledgers:
                ledger_path = ledgers[0]
                if len(_records(ledger_path)) >= 4:
                    break
            time.sleep(0.05)
        assert ledger_path is not None
        process.terminate()
        stdout, stderr = process.communicate(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()

    assert process.returncode == 1, (stdout, stderr)
    rollups = sorted(tmp_path.glob("*b1c1-*-no-swap-soak-rollup.jsonl"))
    assert len(rollups) == 1
    rollup = _records(rollups[0])[0]
    assert rollup["conclusion"] == "blocked"
    assert rollup["no_swap_soak_stability"] == "blocked"
    assert rollup["graduates"]["no_swap_soak_stability"] is False
    assert rollup["cleanup_unload_result"]["ok"] is True
    assert rollup["interrupted_no_swap_rehearsal"]["interruption_reason"] == "planned_stop"
    assert rollup["measurement_duration_s"] > 0


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
        "measurement_wall_clock_gap_free": True,
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
    assert summary["current_mac_section_1_prerequisite_met"] is True
    assert summary["section_2_prerequisite_met"] is True
    assert summary["no_swap_soak_stability"] == "blocked"
    assert summary["graduates"]["interrupted_no_swap_rehearsal"] is True
    assert summary["graduates"]["no_swap_soak_stability"] is False
    assert summary["graduates"]["unblock_B_1c_section_2"] is False

    written = _records(tmp_path / summary["rollup_path"].split("/")[-1])
    assert len(written) == 1
    assert written[0]["schema_version"] == "b1c1.rehearsal.v1"
    assert written[0]["segments"][1]["resumes_prior_segment"] is True
    assert written[0]["segments"][1]["measurement_wall_clock_gap_free"] is True
    assert written[0]["segments"][1]["wall_clock_continuity"] is None


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


def test_b1c1_interrupted_rehearsal_blocks_wall_clock_gap_segments(tmp_path):
    segment = tmp_path / "segment-wall-gap-rollup.jsonl"
    _write_b1c1_segment_rollup(
        segment,
        run_id="segment-wall-gap",
        duration_s=86400.0,
    )
    payload = _records(segment)[0]
    payload["measurement_wall_clock_gap_free"] = False
    payload["wall_clock_continuity"] = {
        "measurement_wall_clock_gap_violation_count": 1,
        "max_measurement_wall_clock_gap_s": 3600.0,
    }
    segment.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    summary = eviction_soak.run_b1c1_interrupted_rehearsal(
        segment_rollups=[segment],
        output_dir=tmp_path,
        run_id="aggregate-wall-gap",
        required_total_duration_s=86400.0,
    )

    assert summary["ok"] is False
    assert summary["interrupted_no_swap_rehearsal"] == "blocked"
    assert summary["all_segments_ok_for_rehearsal"] is False
    assert summary["no_swap_soak_stability"] == "blocked"


def test_b1c1_interrupted_rehearsal_blocks_missing_wall_clock_gate(tmp_path):
    segment = tmp_path / "segment-missing-wall-gate-rollup.jsonl"
    _write_b1c1_segment_rollup(
        segment,
        run_id="segment-missing-wall-gate",
        duration_s=86400.0,
    )
    payload = _records(segment)[0]
    payload.pop("measurement_wall_clock_gap_free")
    segment.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    summary = eviction_soak.run_b1c1_interrupted_rehearsal(
        segment_rollups=[segment],
        output_dir=tmp_path,
        run_id="aggregate-missing-wall-gate",
        required_total_duration_s=86400.0,
    )

    assert summary["ok"] is False
    assert summary["interrupted_no_swap_rehearsal"] == "blocked"
    assert summary["current_mac_section_1_prerequisite_met"] is False
    assert summary["section_2_prerequisite_met"] is False
    assert summary["all_segments_ok_for_rehearsal"] is False
    assert summary["segments"][0]["measurement_wall_clock_gap_free"] is None
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


def test_b1c2_fake_soak_plus_swap_writes_swap_phase_and_blocked_rollup(tmp_path):
    summary = eviction_soak.run_b1c2_soak_plus_swap(
        runtime="owlmlx",
        backend="fake",
        output_dir=tmp_path,
        swap_count=1,
        required_swap_count=eviction_soak.B1C2_REQUIRED_SWAP_COUNT,
        required_duration_s=24 * 60 * 60,
        sample_interval_s=0.0,
    )

    assert summary["ok"] is False
    assert summary["schema_version"] == "b1c2.rollup.v1"
    assert summary["soak_plus_swap_stability"] == "blocked"
    assert summary["swap_count"] == 1
    assert summary["swap_requirement_met"] is False
    assert summary["duration_requirement_met"] is False
    assert summary["allocator_truth_claimable"] is False
    assert summary["graduates"]["soak_plus_swap_stability"] is False
    assert summary["graduates"]["session_kv_supported"] is False

    ledger = _records(tmp_path / summary["ledger"].split("/")[-1])
    rollup = _records(tmp_path / summary["rollup_path"].split("/")[-1])
    swap_records = [record for record in ledger if record["phase"] == "swap"]
    assert len(rollup) == 1
    assert len(swap_records) == 1
    assert {record["schema_version"] for record in ledger} == {"b1c2.v1"}
    assert {record["mode"] for record in ledger} == {"soak_plus_swap"}
    assert [record["phase"] for record in ledger[:3]] == ["warmup", "warmup", "warmup"]
    assert {record["prompt_id"] for record in ledger if record["phase"] == "measurement"} == {
        "short",
        "medium",
        "long",
    }
    warmup_short = next(
        record
        for record in ledger
        if record["phase"] == "warmup" and record["prompt_id"] == "short"
    )
    measurement_short = next(
        record
        for record in ledger
        if record["phase"] == "measurement" and record["prompt_id"] == "short"
    )
    assert (
        measurement_short["config"]["prompt_chars_before_generation"]
        > warmup_short["config"]["prompt_chars_before_generation"]
    )
    swap = swap_records[0]["swap"]
    assert swap["index"] == 1
    assert swap["from_model"] == "qwen3.6-27b"
    assert swap["to_model"] == "gemma-4-31B-it"
    assert swap["unload_ok"] is True
    assert swap["settle_barrier_state"] == "clean"
    assert swap["load_ok"] is True
    assert rollup[0]["soak_plus_swap_stability"] == "blocked"


def test_b1c2_missing_b1c1_prerequisite_blocks_promotion(tmp_path):
    summary = eviction_soak.run_b1c2_soak_plus_swap(
        runtime="owlmlx",
        backend="fake",
        output_dir=tmp_path,
        swap_count=1,
        required_swap_count=1,
        required_duration_s=0.0,
        sample_interval_s=0.0,
        b1c1_prerequisite_satisfied=False,
    )

    assert summary["duration_requirement_met"] is True
    assert summary["swap_requirement_met"] is True
    assert summary["prerequisite_satisfied"] is False
    assert summary["b1c1_prerequisite"]["satisfied"] is False
    assert summary["soak_plus_swap_stability"] == "blocked"
    assert summary["graduates"]["soak_plus_swap_stability"] is False
    assert summary["graduates"]["session_kv_supported"] is False


def test_b1c2_duration_loop_waits_before_scheduled_swap(tmp_path):
    summary = eviction_soak.run_b1c2_soak_plus_swap(
        runtime="owlmlx",
        backend="fake",
        output_dir=tmp_path,
        swap_count=1,
        required_swap_count=1,
        duration_s=0.02,
        required_duration_s=0.01,
        sample_interval_s=0.005,
        b1c1_prerequisite_satisfied=True,
    )

    assert summary["duration_requirement_met"] is True
    assert summary["swap_requirement_met"] is True
    assert summary["measurement_duration_s"] >= 0.01
    assert summary["soak_plus_swap_stability"] == "blocked"


def test_b1c2_native_requires_b1c1_prerequisite(tmp_path):
    rotation = (
        eviction_soak.ModelSpec("/models/qwen27", 58.0),
        eviction_soak.ModelSpec("/models/gemma31", 60.0),
        eviction_soak.ModelSpec("/models/qwen35", 70.0),
    )

    with pytest.raises(ValueError, match="requires a satisfied B-1c section 1"):
        eviction_soak.run_b1c2_soak_plus_swap(
            runtime="owlmlx",
            backend="native",
            output_dir=tmp_path,
            model_rotation=rotation,
            swap_count=1,
            required_swap_count=1,
            required_duration_s=0.0,
            sample_interval_s=0.0,
            b1c1_prerequisite_satisfied=False,
        )


def test_b1c2_native_requires_explicit_three_model_rotation(tmp_path):
    with pytest.raises(ValueError, match="requires explicit three-model rotation"):
        eviction_soak.run_b1c2_soak_plus_swap(
            runtime="owlmlx",
            backend="native",
            output_dir=tmp_path,
            swap_count=1,
            required_swap_count=1,
            required_duration_s=0.0,
            sample_interval_s=0.0,
            b1c1_prerequisite_satisfied=True,
        )


def test_b1c2_cli_model_rotation_uses_explicit_paths():
    args = SimpleNamespace(
        model_a="/models/qwen27",
        model="/models/gemma31",
        model_b="/models/qwen35",
        model_a_gb=58.0,
        model_gb=60.0,
        model_b_gb=70.0,
    )

    rotation = eviction_soak._b1c2_cli_model_rotation(args)

    assert rotation == (
        eviction_soak.ModelSpec("/models/qwen27", 58.0),
        eviction_soak.ModelSpec("/models/gemma31", 60.0),
        eviction_soak.ModelSpec("/models/qwen35", 70.0),
    )


def test_b1c2_cli_model_rotation_keeps_schema_defaults():
    args = SimpleNamespace(
        model_a="model-a",
        model=eviction_soak.B1B_MODEL_PATH,
        model_b="model-b",
        model_a_gb=1.0,
        model_gb=1.0,
        model_b_gb=1.0,
    )

    assert eviction_soak._b1c2_cli_model_rotation(args) is None
