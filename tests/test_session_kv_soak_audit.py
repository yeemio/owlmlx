from __future__ import annotations

import json
from pathlib import Path

from scripts.bench import session_kv_soak_audit


def _write_jsonl(path: Path, *records: dict) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _clean_blocked_b1c2_rollup(**overrides: object) -> dict:
    record = {
        "schema_version": "b1c2.rollup.v1",
        "gate": "B-1c section 2",
        "run_id": "b1c2-segment",
        "conclusion": "blocked",
        "soak_plus_swap_stability": "blocked",
        "hard_failure": False,
        "backend": "native",
        "measurement_mode": "mlx_core_active_memory",
        "measurement_duration_s": 14400.0,
        "required_duration_s": 86400.0,
        "duration_requirement_met": False,
        "swap_count": 1,
        "required_swap_count": 6,
        "swap_requirement_met": False,
        "ledger_gap_free": True,
        "measurement_wall_clock_gap_free": True,
        "session_mix_complete": True,
        "session_mix_balanced": True,
        "allocator_truth_claimable": True,
        "prerequisite_satisfied": True,
        "max_drift_bytes": 0,
        "drift_budget_bytes": 209715200,
        "max_drift_within_budget": True,
        "fatal_watermark_count": 0,
        "failure_measurement_count": 0,
        "unresolved_reclaim_barrier_events": 0,
        "session_cache_drops_total": 0,
        "session_cache_expirations_total": 0,
        "session_cache_rejects_total": 0,
        "swap_boundaries_clean": True,
        "graduates": {
            "soak_plus_swap_stability": False,
            "session_kv_supported": False,
        },
    }
    record.update(overrides)
    return record


def test_b1c2_ledger_audit_reports_live_health(tmp_path):
    ledger = tmp_path / "segment.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "warmup",
            "sample_index": 1,
            "prompt_id": "short",
            "elapsed_s": 1.0,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {"drops": 0}},
            "memory": {"watermark_after_generation": "GREEN"},
        },
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 2,
            "prompt_id": "medium",
            "elapsed_s": 2.0,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {"drops": 1, "rejects": 0}},
            "memory": {
                "drift_from_measurement_start_bytes": 512,
                "watermark_after_generation": "GREEN",
            },
        },
        {
            "schema_version": "b1c2.v1",
            "phase": "swap",
            "sample_index": 3,
            "elapsed_s": 3.0,
            "session_cache": {"counter_delta": {}},
            "swap": {
                "unload_ok": True,
                "settle_barrier_state": "clean",
                "load_ok": True,
            },
        },
    )

    result = session_kv_soak_audit.audit_b1c2_ledger(ledger)

    assert result["record_count"] == 3
    assert result["ledger_gap_free"] is True
    assert result["last_sample_index"] == 3
    assert result["last_phase"] == "swap"
    assert result["swap_count"] == 1
    assert result["drop_sample_indices"] == [2]
    assert result["drop_samples"] == [
        {
            "sample_index": 2,
            "elapsed_s": 2.0,
            "phase": "measurement",
            "prompt_id": "medium",
            "model_id": None,
            "prompt_chars_before_generation": None,
            "prompt_chars_after_generation": None,
            "counter_delta": {"drops": 1, "rejects": 0},
        }
    ]
    assert result["session_cache_drops_total"] == 1
    assert result["max_measurement_drift_bytes"] == 512
    assert result["errors"] == []


def test_b1c2_segment_rollup_audit_allows_clean_blocked_segment(tmp_path):
    rollup = tmp_path / "segment-rollup.jsonl"
    _write_jsonl(rollup, _clean_blocked_b1c2_rollup())

    result = session_kv_soak_audit.audit_b1c2_segment_rollup(rollup)

    assert result["errors"] == []
    assert result["conclusion"] == "blocked"
    assert result["clean_for_interrupted_aggregate"] is True
    assert result["duration_requirement_met"] is False
    assert result["swap_requirement_met"] is False
    assert result["graduates"]["session_kv_supported"] is False


def test_b1c2_segment_rollup_audit_rejects_unsafe_pass_claim(tmp_path):
    rollup = tmp_path / "unsafe-rollup.jsonl"
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            graduates={
                "soak_plus_swap_stability": True,
                "session_kv_supported": False,
            },
        ),
    )

    result = session_kv_soak_audit.audit_b1c2_segment_rollup(rollup)

    assert "unsafe_claim:soak_plus_swap_passed_without_all_gates" in result["errors"]
    assert "unsafe_claim:passed_without_duration_requirement" in result["errors"]
    assert "unsafe_claim:passed_without_swap_requirement" in result["errors"]


def test_b1c2_aggregate_rollup_audit_rejects_supported_claim(tmp_path):
    aggregate = tmp_path / "aggregate-rollup.jsonl"
    _write_jsonl(
        aggregate,
        {
            "schema_version": "b1c2.aggregate.v1",
            "run_id": "aggregate",
            "conclusion": "blocked",
            "soak_plus_swap_stability": "blocked",
            "interrupted_soak_plus_swap": {
                "all_segments_ok_for_rehearsal": True,
                "prerequisite_satisfied": True,
                "duration_requirement_met": False,
                "swap_requirement_met": False,
                "allocator_truth_claimable": True,
            },
            "graduates": {
                "soak_plus_swap_stability": False,
                "session_kv_supported": True,
            },
        },
    )

    result = session_kv_soak_audit.audit_b1c2_aggregate_rollup(aggregate)

    assert result["errors"] == ["unsafe_claim:session_kv_supported=true"]


def test_session_kv_soak_audit_cli_returns_nonzero_for_unsafe_claim(tmp_path, capsys):
    rollup = tmp_path / "unsafe-rollup.jsonl"
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            graduates={
                "soak_plus_swap_stability": True,
                "session_kv_supported": False,
            },
        ),
    )

    code = session_kv_soak_audit.main(["--segment-rollup", str(rollup)])
    captured = capsys.readouterr()

    assert code == 1
    assert "unsafe_claim" in captured.out
