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


def _b1c2_all_axes_passed() -> dict:
    return {
        "load_stability": {"status": "passed"},
        "throughput_stability": {"status": "passed"},
        "switch_stability": {"status": "passed"},
        "concurrency_stability": {"status": "passed"},
    }


def _b1c2_all_axes_passed_with_eviction() -> dict:
    axes = _b1c2_all_axes_passed()
    axes["concurrency_stability"] = {
        "status": "passed",
        "cache_eviction_required": True,
        "cache_eviction_observed": True,
        "evictions_total": 1,
    }
    return axes


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
            "session_cache": {
                "counter_delta": {"drops": 1, "rejects": 0},
                "drop_reason_code": "completion_trim_mismatch",
                "last_drop_event_after": {
                    "reason_code": "completion_trim_mismatch",
                    "detail": {"trimmed_tokens": 1},
                },
            },
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
            "drop_reason_code": "completion_trim_mismatch",
            "last_drop_event_after": {
                "reason_code": "completion_trim_mismatch",
                "detail": {"trimmed_tokens": 1},
            },
        }
    ]
    assert result["session_cache_drops_total"] == 1
    assert result["max_measurement_drift_bytes"] == 512
    assert result["expected_rollup_exists"] is False
    assert result["ledger_acceptance_status"] == "diagnostic_partial_no_rollup"
    assert result["errors"] == []


def test_b1c2_ledger_audit_can_require_matching_rollup(tmp_path):
    ledger = tmp_path / "20260602T100243Z-b1c2-fast-count-soak-swap.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 1,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {}},
            "memory": {"watermark_after_generation": "GREEN"},
        },
    )

    result = session_kv_soak_audit.audit_b1c2_ledger(
        ledger,
        require_rollup=True,
    )

    expected_rollup = (
        tmp_path / "20260602T100243Z-b1c2-fast-count-soak-swap-rollup.jsonl"
    )
    assert result["expected_rollup_path"] == str(expected_rollup)
    assert result["expected_rollup_exists"] is False
    assert result["ledger_acceptance_status"] == "diagnostic_partial_no_rollup"
    assert result["errors"] == [f"missing_segment_rollup:{expected_rollup}"]


def test_b1c2_ledger_audit_accepts_matching_rollup_presence(tmp_path):
    ledger = tmp_path / "20260602T100243Z-b1c2-fast-count-soak-swap.jsonl"
    rollup = tmp_path / "20260602T100243Z-b1c2-fast-count-soak-swap-rollup.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 1,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {}},
            "memory": {"watermark_after_generation": "GREEN"},
        },
    )
    _write_jsonl(rollup, _clean_blocked_b1c2_rollup())

    result = session_kv_soak_audit.audit_b1c2_ledger(
        ledger,
        require_rollup=True,
    )

    assert result["expected_rollup_exists"] is True
    assert result["ledger_acceptance_status"] == "rollup_available"
    assert result["errors"] == []


def test_b1c2_ledger_audit_requires_expected_rollup_to_be_canonical(tmp_path):
    ledger = tmp_path / "20260602T095334Z-b1c2-threshold-soak-swap.jsonl"
    rollup = tmp_path / "20260602T095334Z-b1c2-threshold-soak-swap-rollup.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 1,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {}},
            "memory": {"watermark_after_generation": "GREEN"},
        },
    )
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=3,
            swap_count=3,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed(),
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 3,
                "canonical_switch_requirement_met": False,
                "soak_plus_swap_graduation_eligible": False,
            },
            graduates={
                "soak_plus_swap_stability": False,
                "session_kv_supported": False,
            },
        ),
    )

    result = session_kv_soak_audit.audit_b1c2_ledger(
        ledger,
        require_canonical=True,
    )

    assert result["expected_rollup_exists"] is True
    assert result["expected_rollup_canonical_acceptance_status"] == "not_canonical"
    assert "canonical_gate:canonical_switch_requirement_not_met" in (
        result["expected_rollup_canonical_errors"]
    )
    assert "expected_rollup:canonical_gate:canonical_switch_requirement_not_met" in (
        result["errors"]
    )


def test_b1c2_ledger_audit_accepts_expected_canonical_rollup(tmp_path):
    ledger = tmp_path / "20260602T120000Z-b1c2-canonical-soak-swap.jsonl"
    rollup = tmp_path / "20260602T120000Z-b1c2-canonical-soak-swap-rollup.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 1,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {}},
            "memory": {"watermark_after_generation": "GREEN"},
        },
    )
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=24,
            swap_count=24,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed(),
            interrupted_soak_plus_swap={
                "interrupted": False,
                "observed_record_count": 72,
                "observed_measurement_count": 48,
                "observed_swap_count": 24,
                "graduation_eligible": True,
            },
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 24,
                "canonical_switch_requirement_met": True,
                "soak_plus_swap_graduation_eligible": True,
            },
            graduates={
                "soak_plus_swap_stability": True,
                "session_kv_supported": False,
            },
        ),
    )

    result = session_kv_soak_audit.audit_b1c2_ledger(
        ledger,
        require_canonical=True,
    )

    assert result["expected_rollup_canonical_acceptance_status"] == "canonical_passed"
    assert result["expected_rollup_canonical_errors"] == []
    assert result["errors"] == []


def test_b1c2_ledger_audit_separates_global_and_same_model_epoch_drift(tmp_path):
    ledger = tmp_path / "segment.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 1,
            "prompt_id": "short",
            "elapsed_s": 1.0,
            "sample_verdict": "passed",
            "model": {"id": "model-a"},
            "session_cache": {
                "counter_delta": {},
                "resident_bytes_estimate_after": 0,
            },
            "memory": {
                "active_memory_after_generation_bytes": 1_000,
                "drift_from_measurement_start_bytes": 0,
                "watermark_after_generation": "GREEN",
            },
        },
        {
            "schema_version": "b1c2.v1",
            "phase": "swap",
            "sample_index": 2,
            "elapsed_s": 2.0,
            "session_cache": {"counter_delta": {}},
            "swap": {
                "unload_ok": True,
                "settle_barrier_state": "clean",
                "load_ok": True,
            },
        },
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 3,
            "prompt_id": "medium",
            "elapsed_s": 3.0,
            "sample_verdict": "passed",
            "model": {"id": "model-b"},
            "session_cache": {
                "counter_delta": {},
                "resident_bytes_estimate_after": 0,
            },
            "memory": {
                "active_memory_after_generation_bytes": 50_000,
                "drift_from_measurement_start_bytes": 49_000,
                "watermark_after_generation": "GREEN",
            },
        },
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 4,
            "prompt_id": "long",
            "elapsed_s": 4.0,
            "sample_verdict": "passed",
            "model": {"id": "model-b"},
            "session_cache": {
                "counter_delta": {},
                "resident_bytes_estimate_after": 250,
                "resident_bytes_estimate_mode": "cache_object_nbytes",
            },
            "memory": {
                "active_memory_after_generation_bytes": 50_200,
                "drift_from_measurement_start_bytes": 49_200,
                "watermark_after_generation": "GREEN",
            },
        },
    )

    result = session_kv_soak_audit.audit_b1c2_ledger(ledger)

    assert result["max_measurement_drift_bytes"] == 49_200
    assert result["max_same_model_load_epoch_drift_bytes"] == 200
    assert (
        result["max_same_model_load_epoch_unaccounted_session_kv_drift_bytes"]
        == 0
    )
    assert result["session_cache_resident_bytes_estimate_modes"] == [
        "cache_object_nbytes"
    ]
    assert result["same_model_load_epoch_drift_accounting"]["epoch_count"] == 2


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
    assert "unsafe_claim:passed_without_axis_verdicts" in result["errors"]
    assert "unsafe_claim:passed_without_swap_requirement" in result["errors"]


def test_b1c2_segment_rollup_audit_distinguishes_local_from_canonical_pass(tmp_path):
    rollup = tmp_path / "local-threshold-rollup.jsonl"
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=3,
            swap_count=3,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed(),
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 3,
                "canonical_switch_requirement_met": False,
                "soak_plus_swap_graduation_eligible": False,
            },
            graduates={
                "soak_plus_swap_stability": False,
                "session_kv_supported": False,
            },
        ),
    )

    local_result = session_kv_soak_audit.audit_b1c2_segment_rollup(rollup)
    canonical_result = session_kv_soak_audit.audit_b1c2_segment_rollup(
        rollup,
        require_canonical=True,
    )

    assert local_result["errors"] == []
    assert local_result["canonical_acceptance_status"] == "not_canonical"
    assert "canonical_gate:canonical_switch_requirement_not_met" in (
        canonical_result["errors"]
    )
    assert "canonical_gate:graduation_not_eligible" in canonical_result["errors"]
    assert "canonical_gate:graduate_flag_not_true" in canonical_result["errors"]


def test_b1c2_segment_rollup_audit_accepts_canonical_pass(tmp_path):
    rollup = tmp_path / "canonical-rollup.jsonl"
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=24,
            swap_count=24,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed(),
            interrupted_soak_plus_swap={
                "interrupted": False,
                "observed_record_count": 72,
                "observed_measurement_count": 48,
                "observed_swap_count": 24,
                "graduation_eligible": True,
            },
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 24,
                "canonical_switch_requirement_met": True,
                "soak_plus_swap_graduation_eligible": True,
            },
            graduates={
                "soak_plus_swap_stability": True,
                "session_kv_supported": False,
            },
        ),
    )

    result = session_kv_soak_audit.audit_b1c2_segment_rollup(
        rollup,
        require_canonical=True,
    )

    assert result["errors"] == []
    assert result["canonical_acceptance_status"] == "canonical_passed"


def test_b1c2_segment_rollup_audit_can_require_cache_eviction(tmp_path):
    rollup = tmp_path / "canonical-rollup.jsonl"
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=24,
            swap_count=24,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed(),
            interrupted_soak_plus_swap={
                "interrupted": False,
                "observed_record_count": 72,
                "observed_measurement_count": 48,
                "observed_swap_count": 24,
                "graduation_eligible": True,
            },
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 24,
                "canonical_switch_requirement_met": True,
                "soak_plus_swap_graduation_eligible": True,
            },
            graduates={
                "soak_plus_swap_stability": True,
                "session_kv_supported": False,
            },
        ),
    )

    result = session_kv_soak_audit.audit_b1c2_segment_rollup(
        rollup,
        require_canonical=True,
        require_cache_eviction=True,
    )

    assert result["canonical_acceptance_status"] == "not_canonical"
    assert "cache_eviction:requirement_flag_not_true" in result["errors"]
    assert "cache_eviction:not_observed" in result["errors"]

    evicting_rollup = tmp_path / "canonical-evicting-rollup.jsonl"
    _write_jsonl(
        evicting_rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=24,
            swap_count=24,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed_with_eviction(),
            interrupted_soak_plus_swap={
                "interrupted": False,
                "observed_record_count": 72,
                "observed_measurement_count": 48,
                "observed_swap_count": 24,
                "graduation_eligible": True,
            },
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 24,
                "canonical_switch_requirement_met": True,
                "soak_plus_swap_graduation_eligible": True,
            },
            graduates={
                "soak_plus_swap_stability": True,
                "session_kv_supported": False,
            },
        ),
    )

    evicting_result = session_kv_soak_audit.audit_b1c2_segment_rollup(
        evicting_rollup,
        require_canonical=True,
        require_cache_eviction=True,
    )

    assert evicting_result["errors"] == []
    assert evicting_result["canonical_acceptance_status"] == "canonical_passed"


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


def test_b1c2_aggregate_rollup_audit_accepts_canonical_axes(tmp_path):
    aggregate = tmp_path / "aggregate-rollup.jsonl"
    _write_jsonl(
        aggregate,
        {
            "schema_version": "b1c2.aggregate.v1",
            "run_id": "aggregate",
            "conclusion": "passed",
            "soak_plus_swap_stability": "passed",
            "interrupted_soak_plus_swap": {
                "all_segments_ok_for_rehearsal": True,
                "prerequisite_satisfied": True,
                "duration_requirement_met": False,
                "swap_requirement_met": True,
                "allocator_truth_claimable": True,
                "axis_verdicts": _b1c2_all_axes_passed(),
            },
            "canonical_gate": {
                "required_swap_count": 24,
                "observed_swap_count": 24,
                "canonical_switch_requirement_met": True,
                "soak_plus_swap_graduation_eligible": True,
            },
            "graduates": {
                "soak_plus_swap_stability": True,
                "session_kv_supported": False,
            },
        },
    )

    result = session_kv_soak_audit.audit_b1c2_aggregate_rollup(
        aggregate,
        require_canonical=True,
    )

    assert result["errors"] == []
    assert result["canonical_acceptance_status"] == "canonical_passed"


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


def test_session_kv_soak_audit_cli_requires_rollup_for_ledger(tmp_path, capsys):
    ledger = tmp_path / "20260602T100243Z-b1c2-fast-count-soak-swap.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 1,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {}},
            "memory": {"watermark_after_generation": "GREEN"},
        },
    )

    code = session_kv_soak_audit.main(
        ["--ledger", str(ledger), "--require-rollup"]
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "diagnostic_partial_no_rollup" in captured.out
    assert "missing_segment_rollup" in captured.out


def test_session_kv_soak_audit_cli_can_require_canonical_rollup(tmp_path, capsys):
    rollup = tmp_path / "local-threshold-rollup.jsonl"
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=3,
            swap_count=3,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed(),
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 3,
                "canonical_switch_requirement_met": False,
                "soak_plus_swap_graduation_eligible": False,
            },
            graduates={
                "soak_plus_swap_stability": False,
                "session_kv_supported": False,
            },
        ),
    )

    code = session_kv_soak_audit.main(
        ["--segment-rollup", str(rollup), "--require-canonical"]
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "canonical_gate:canonical_switch_requirement_not_met" in captured.out


def test_session_kv_soak_audit_cli_can_require_canonical_from_ledger(
    tmp_path,
    capsys,
):
    ledger = tmp_path / "20260602T095334Z-b1c2-threshold-soak-swap.jsonl"
    rollup = tmp_path / "20260602T095334Z-b1c2-threshold-soak-swap-rollup.jsonl"
    _write_jsonl(
        ledger,
        {
            "schema_version": "b1c2.v1",
            "phase": "measurement",
            "sample_index": 1,
            "sample_verdict": "passed",
            "session_cache": {"counter_delta": {}},
            "memory": {"watermark_after_generation": "GREEN"},
        },
    )
    _write_jsonl(
        rollup,
        _clean_blocked_b1c2_rollup(
            conclusion="passed",
            soak_plus_swap_stability="passed",
            required_swap_count=3,
            swap_count=3,
            swap_requirement_met=True,
            axis_verdicts=_b1c2_all_axes_passed(),
            canonical_gate={
                "required_swap_count": 24,
                "observed_swap_count": 3,
                "canonical_switch_requirement_met": False,
                "soak_plus_swap_graduation_eligible": False,
            },
            graduates={
                "soak_plus_swap_stability": False,
                "session_kv_supported": False,
            },
        ),
    )

    code = session_kv_soak_audit.main(
        ["--ledger", str(ledger), "--require-canonical"]
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "expected_rollup_canonical_acceptance=not_canonical" in captured.out
    assert "expected_rollup:canonical_gate:canonical_switch_requirement_not_met" in (
        captured.out
    )
