"""Read-only audits for session KV soak evidence.

This helper intentionally does not run models or mutate evidence. It exists to
check completed B-1c section 2 segment/aggregate rollups, and to give a cheap
live-ledger health snapshot while a long native run is still in progress.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.bench import eviction_soak


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [], [f"missing_file:{path}"]

    for line_number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_json:{path}:{line_number}:{exc.msg}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"non_object_json:{path}:{line_number}")
            continue
        records.append(payload)
    return records, errors


def _read_first_record(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    records, errors = _read_jsonl(path)
    if not records:
        errors.append(f"empty_jsonl:{path}")
        return None, errors
    if len(records) > 1:
        errors.append(f"multiple_rollup_records:{path}:{len(records)}")
    return records[0], errors


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _counter_delta_total(records: list[dict[str, Any]], key: str) -> int:
    total = 0
    for record in records:
        delta = record.get("session_cache", {}).get("counter_delta", {})
        if isinstance(delta, dict):
            total += _as_int(delta.get(key), 0)
    return total


def _sample_indices(records: list[dict[str, Any]]) -> list[int]:
    indices: list[int] = []
    for record in records:
        if "sample_index" not in record:
            continue
        indices.append(_as_int(record.get("sample_index"), -1))
    return indices


def _expected_b1c2_rollup_path(ledger_path: Path) -> Path:
    name = ledger_path.name
    suffix = "-soak-swap.jsonl"
    if name.endswith(suffix):
        return ledger_path.with_name(f"{name[:-len(suffix)]}-soak-swap-rollup.jsonl")
    return ledger_path.with_name(f"{ledger_path.stem}-rollup.jsonl")


def _segment_blockers(record: dict[str, Any]) -> list[str]:
    checks = {
        "hard_failure_false": record.get("hard_failure") is False,
        "ledger_gap_free": record.get("ledger_gap_free") is True,
        "measurement_wall_clock_gap_free": record.get("measurement_wall_clock_gap_free")
        is True,
        "session_mix_complete": record.get("session_mix_complete") is True,
        "session_mix_balanced": record.get("session_mix_balanced") is True,
        "max_drift_within_budget": record.get("max_drift_within_budget") is True,
        "swap_boundaries_clean": record.get("swap_boundaries_clean") is True,
        "fatal_watermark_count_zero": _as_int(record.get("fatal_watermark_count")) == 0,
        "session_cache_drops_total_zero": _as_int(
            record.get("session_cache_drops_total")
        )
        == 0,
        "session_cache_expirations_total_zero": _as_int(
            record.get("session_cache_expirations_total")
        )
        == 0,
        "session_cache_rejects_total_zero": _as_int(
            record.get("session_cache_rejects_total")
        )
        == 0,
        "failure_measurement_count_zero": _as_int(
            record.get("failure_measurement_count")
        )
        == 0,
        "unresolved_reclaim_barrier_events_zero": _as_int(
            record.get("unresolved_reclaim_barrier_events")
        )
        == 0,
        "positive_measurement_duration": _as_float(
            record.get("measurement_duration_s")
        )
        > 0.0,
    }
    return [name for name, ok in checks.items() if not ok]


def _claim_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    graduates = record.get("graduates", {})
    if not isinstance(graduates, dict):
        graduates = {}

    if graduates.get("session_kv_supported") is True:
        errors.append("unsafe_claim:session_kv_supported=true")

    duration_met = record.get("duration_requirement_met") is True
    swap_met = record.get("swap_requirement_met") is True
    axis_verdicts = record.get("axis_verdicts", {})
    if not isinstance(axis_verdicts, dict):
        axis_verdicts = {}
    required_axes = (
        "load_stability",
        "throughput_stability",
        "switch_stability",
        "concurrency_stability",
    )
    axes_met = all(
        axis_verdicts.get(axis, {}).get("status") == "passed"
        for axis in required_axes
    )
    prerequisite_met = record.get("prerequisite_satisfied") is True
    allocator_truth = record.get("allocator_truth_claimable") is True
    clean_segment = eviction_soak._b1c2_segment_ok_for_rehearsal(record)
    passed_claim = (
        record.get("conclusion") == "passed"
        or record.get("soak_plus_swap_stability") == "passed"
        or graduates.get("soak_plus_swap_stability") is True
    )
    if passed_claim and not (
        axes_met and swap_met and prerequisite_met and allocator_truth and clean_segment
    ):
        errors.append("unsafe_claim:soak_plus_swap_passed_without_all_gates")
    if record.get("conclusion") == "passed" and not axes_met:
        errors.append("unsafe_claim:passed_without_axis_verdicts")
    if not swap_met and record.get("conclusion") == "passed":
        errors.append("unsafe_claim:passed_without_swap_requirement")
    canonical_gate = record.get("canonical_gate", {})
    if not isinstance(canonical_gate, dict):
        canonical_gate = {}
    canonical_eligible = (
        canonical_gate.get("canonical_switch_requirement_met") is True
        and canonical_gate.get("soak_plus_swap_graduation_eligible") is True
    )
    if graduates.get("soak_plus_swap_stability") is True and not canonical_eligible:
        errors.append("unsafe_claim:graduates_soak_plus_swap_without_canonical_gate")
    return errors


def _required_axis_statuses(record: dict[str, Any]) -> dict[str, str | None]:
    axis_verdicts = record.get("axis_verdicts", {})
    if not isinstance(axis_verdicts, dict) or not axis_verdicts:
        aggregate = record.get("interrupted_soak_plus_swap", {})
        if isinstance(aggregate, dict):
            axis_verdicts = aggregate.get("axis_verdicts", {})
    if not isinstance(axis_verdicts, dict):
        axis_verdicts = {}
    required_axes = (
        "load_stability",
        "throughput_stability",
        "switch_stability",
        "concurrency_stability",
    )
    return {
        axis: (
            axis_verdicts.get(axis, {}).get("status")
            if isinstance(axis_verdicts.get(axis), dict)
            else None
        )
        for axis in required_axes
    }


def _concurrency_axis(record: dict[str, Any]) -> dict[str, Any]:
    axis_verdicts = record.get("axis_verdicts", {})
    if not isinstance(axis_verdicts, dict) or not axis_verdicts:
        aggregate = record.get("interrupted_soak_plus_swap", {})
        if isinstance(aggregate, dict):
            axis_verdicts = aggregate.get("axis_verdicts", {})
    if not isinstance(axis_verdicts, dict):
        return {}
    concurrency = axis_verdicts.get("concurrency_stability", {})
    return concurrency if isinstance(concurrency, dict) else {}


def _cache_eviction_acceptance_errors(record: dict[str, Any]) -> list[str]:
    concurrency = _concurrency_axis(record)
    errors: list[str] = []
    if not concurrency:
        return ["cache_eviction:concurrency_axis_missing"]
    if concurrency.get("cache_eviction_required") is not True:
        errors.append("cache_eviction:requirement_flag_not_true")
    if concurrency.get("cache_eviction_observed") is not True:
        errors.append("cache_eviction:not_observed")
    return errors


def _canonical_acceptance_errors(
    record: dict[str, Any],
    *,
    require_cache_eviction: bool = False,
) -> list[str]:
    errors: list[str] = []
    canonical_gate = record.get("canonical_gate", {})
    if not isinstance(canonical_gate, dict):
        canonical_gate = {}
    graduates = record.get("graduates", {})
    if not isinstance(graduates, dict):
        graduates = {}
    interrupted = record.get("interrupted_soak_plus_swap", {})
    if not isinstance(interrupted, dict):
        interrupted = {}
    axis_statuses = _required_axis_statuses(record)
    if any(status != "passed" for status in axis_statuses.values()):
        errors.append("canonical_gate:axis_verdicts_not_all_passed")
    if record.get("conclusion") != "passed":
        errors.append("canonical_gate:conclusion_not_passed")
    if record.get("soak_plus_swap_stability") != "passed":
        errors.append("canonical_gate:stability_not_passed")
    if canonical_gate.get("canonical_switch_requirement_met") is not True:
        errors.append("canonical_gate:canonical_switch_requirement_not_met")
    if canonical_gate.get("soak_plus_swap_graduation_eligible") is not True:
        errors.append("canonical_gate:graduation_not_eligible")
    if graduates.get("soak_plus_swap_stability") is not True:
        errors.append("canonical_gate:graduate_flag_not_true")
    if graduates.get("session_kv_supported") is True:
        errors.append("unsafe_claim:session_kv_supported=true")
    if interrupted.get("interrupted") is True:
        errors.append("canonical_gate:interrupted_segment")
    if require_cache_eviction:
        errors.extend(_cache_eviction_acceptance_errors(record))
    return errors


def _canonical_acceptance_status(
    record: dict[str, Any],
    *,
    require_cache_eviction: bool = False,
) -> str:
    return (
        "canonical_passed"
        if not _canonical_acceptance_errors(
            record,
            require_cache_eviction=require_cache_eviction,
        )
        else "not_canonical"
    )


def audit_b1c2_ledger(
    path: Path,
    *,
    require_rollup: bool = False,
    require_canonical: bool = False,
    require_cache_eviction: bool = False,
) -> dict[str, Any]:
    records, errors = _read_jsonl(path)
    expected_rollup_path = _expected_b1c2_rollup_path(path)
    expected_rollup_exists = expected_rollup_path.exists()
    if (
        require_rollup
        or require_canonical
        or require_cache_eviction
    ) and not expected_rollup_exists:
        errors.append(f"missing_segment_rollup:{expected_rollup_path}")
    expected_rollup_canonical_acceptance_status = None
    expected_rollup_canonical_errors: list[str] = []
    if (require_canonical or require_cache_eviction) and expected_rollup_exists:
        rollup_audit = audit_b1c2_segment_rollup(
            expected_rollup_path,
            require_canonical=True,
            require_cache_eviction=require_cache_eviction,
        )
        expected_rollup_canonical_acceptance_status = rollup_audit.get(
            "canonical_acceptance_status"
        )
        canonical_errors = rollup_audit.get("canonical_acceptance_errors")
        if isinstance(canonical_errors, list):
            expected_rollup_canonical_errors = [str(error) for error in canonical_errors]
        for error in rollup_audit.get("errors", []):
            errors.append(f"expected_rollup:{error}")
    indices = _sample_indices(records)
    expected_indices = list(range(1, len(indices) + 1))
    phases = Counter(str(record.get("phase", "missing")) for record in records)
    last_record = records[-1] if records else {}
    failed_samples = sum(
        1 for record in records if record.get("sample_verdict") == "failed"
    )
    fatal_watermarks = sum(
        1
        for record in records
        if record.get("memory", {}).get("watermark_after_generation") == "FATAL"
    )
    swap_records = [record for record in records if record.get("phase") == "swap"]
    drop_records = [
        record
        for record in records
        if _as_int(
            record.get("session_cache", {}).get("counter_delta", {}).get("drops"),
            0,
        )
        > 0
    ]
    bypass_records = [
        record
        for record in records
        if _as_int(
            record.get("session_cache", {})
            .get("counter_delta", {})
            .get("trim_bypasses"),
            0,
        )
        > 0
    ]
    dirty_swaps = [
        record.get("sample_index")
        for record in swap_records
        if not (
            record.get("swap", {}).get("unload_ok") is True
            and record.get("swap", {}).get("settle_barrier_state") == "clean"
            and record.get("swap", {}).get("load_ok") is True
        )
    ]
    max_drift_values = [
        _as_int(record.get("memory", {}).get("drift_from_measurement_start_bytes"))
        for record in records
        if record.get("memory", {}).get("drift_from_measurement_start_bytes") is not None
    ]
    resident_estimate_values = [
        _as_int(record.get("session_cache", {}).get("resident_bytes_estimate_after"))
        for record in records
        if record.get("session_cache", {}).get("resident_bytes_estimate_after")
        is not None
    ]
    resident_estimate_modes = {
        str(record.get("session_cache", {}).get("resident_bytes_estimate_mode"))
        for record in records
        if record.get("session_cache", {}).get("resident_bytes_estimate_mode")
        is not None
    }
    unaccounted_drift_values = []
    for record in records:
        drift = record.get("memory", {}).get("drift_from_measurement_start_bytes")
        resident_estimate = record.get("session_cache", {}).get(
            "resident_bytes_estimate_after"
        )
        if drift is None or resident_estimate is None:
            continue
        unaccounted_drift_values.append(max(_as_int(drift) - _as_int(resident_estimate), 0))
    same_model_epoch_drift = eviction_soak._b1c2_same_model_load_epoch_drift(records)

    return {
        "kind": "b1c2_ledger",
        "path": str(path),
        "expected_rollup_path": str(expected_rollup_path),
        "expected_rollup_exists": expected_rollup_exists,
        "expected_rollup_canonical_acceptance_status": (
            expected_rollup_canonical_acceptance_status
        ),
        "expected_rollup_canonical_errors": expected_rollup_canonical_errors,
        "ledger_acceptance_status": (
            "rollup_available"
            if expected_rollup_exists
            else "diagnostic_partial_no_rollup"
        ),
        "record_count": len(records),
        "schema_versions": sorted(
            {str(record.get("schema_version", "missing")) for record in records}
        ),
        "phases": dict(sorted(phases.items())),
        "ledger_gap_free": bool(indices) and indices == expected_indices,
        "last_sample_index": last_record.get("sample_index"),
        "last_phase": last_record.get("phase"),
        "last_prompt_id": last_record.get("prompt_id"),
        "last_elapsed_s": last_record.get("elapsed_s"),
        "swap_count": len(swap_records),
        "drop_sample_indices": [
            record.get("sample_index") for record in drop_records
        ],
        "drop_samples": [
            {
                "sample_index": record.get("sample_index"),
                "elapsed_s": record.get("elapsed_s"),
                "phase": record.get("phase"),
                "prompt_id": record.get("prompt_id"),
                "model_id": record.get("model", {}).get("id"),
                "prompt_chars_before_generation": record.get("config", {}).get(
                    "prompt_chars_before_generation"
                ),
                "prompt_chars_after_generation": record.get("config", {}).get(
                    "prompt_chars_after_generation"
                ),
                "counter_delta": record.get("session_cache", {}).get("counter_delta", {}),
                "drop_reason_code": record.get("session_cache", {}).get(
                    "drop_reason_code"
                ),
                "last_drop_event_after": record.get("session_cache", {}).get(
                    "last_drop_event_after"
                ),
            }
            for record in drop_records
        ],
        "trim_bypass_sample_indices": [
            record.get("sample_index") for record in bypass_records
        ],
        "trim_bypass_samples": [
            {
                "sample_index": record.get("sample_index"),
                "elapsed_s": record.get("elapsed_s"),
                "phase": record.get("phase"),
                "prompt_id": record.get("prompt_id"),
                "model_id": record.get("model", {}).get("id"),
                "prompt_chars_before_generation": record.get("config", {}).get(
                    "prompt_chars_before_generation"
                ),
                "prompt_chars_after_generation": record.get("config", {}).get(
                    "prompt_chars_after_generation"
                ),
                "counter_delta": record.get("session_cache", {}).get("counter_delta", {}),
                "bypass_reason_code": record.get("session_cache", {}).get(
                    "bypass_reason_code"
                ),
                "last_bypass_event_after": record.get("session_cache", {}).get(
                    "last_bypass_event_after"
                ),
            }
            for record in bypass_records
        ],
        "dirty_swap_sample_indices": dirty_swaps,
        "session_cache_drops_total": _counter_delta_total(records, "drops"),
        "session_cache_expirations_total": _counter_delta_total(records, "expirations"),
        "session_cache_rejects_total": _counter_delta_total(records, "rejects"),
        "session_cache_trim_bypasses_total": _counter_delta_total(
            records,
            "trim_bypasses",
        ),
        "session_cache_trim_evictions_total": _counter_delta_total(
            records,
            "trim_evictions",
        ),
        "session_cache_window_bypasses_total": _counter_delta_total(
            records,
            "window_bypasses",
        ),
        "session_cache_window_evictions_total": _counter_delta_total(
            records,
            "window_evictions",
        ),
        "fatal_watermark_count": fatal_watermarks,
        "failed_sample_count": failed_samples,
        "max_measurement_drift_bytes": (
            max(max_drift_values) if max_drift_values else None
        ),
        "max_session_cache_resident_bytes": (
            max(resident_estimate_values) if resident_estimate_values else None
        ),
        "session_cache_resident_bytes_estimate_modes": sorted(
            resident_estimate_modes
        ),
        "max_unaccounted_session_kv_drift_bytes": (
            max(unaccounted_drift_values) if unaccounted_drift_values else None
        ),
        "same_model_load_epoch_drift_accounting": same_model_epoch_drift,
        "max_same_model_load_epoch_drift_bytes": same_model_epoch_drift[
            "max_same_model_load_epoch_drift_bytes"
        ],
        "max_same_model_load_epoch_unaccounted_session_kv_drift_bytes": (
            same_model_epoch_drift[
                "max_same_model_load_epoch_unaccounted_session_kv_drift_bytes"
            ]
        ),
        "errors": errors,
    }


def audit_b1c2_segment_rollup(
    path: Path,
    *,
    require_canonical: bool = False,
    require_cache_eviction: bool = False,
) -> dict[str, Any]:
    record, errors = _read_first_record(path)
    if record is None:
        return {
            "kind": "b1c2_segment_rollup",
            "path": str(path),
            "errors": errors,
        }
    if record.get("schema_version") != "b1c2.rollup.v1":
        errors.append(
            f"wrong_schema:{record.get('schema_version')}:expected_b1c2.rollup.v1"
        )
    if record.get("gate") != "B-1c section 2":
        errors.append(f"wrong_gate:{record.get('gate')}")
    errors.extend(_claim_errors(record))
    canonical_errors = _canonical_acceptance_errors(
        record,
        require_cache_eviction=require_cache_eviction,
    )
    if require_canonical or require_cache_eviction:
        errors.extend(canonical_errors)
    blockers = _segment_blockers(record)
    return {
        "kind": "b1c2_segment_rollup",
        "path": str(path),
        "run_id": record.get("run_id"),
        "conclusion": record.get("conclusion"),
        "soak_plus_swap_stability": record.get("soak_plus_swap_stability"),
        "hard_failure": record.get("hard_failure"),
        "measurement_duration_s": record.get("measurement_duration_s"),
        "required_duration_s": record.get("required_duration_s"),
        "duration_requirement_met": record.get("duration_requirement_met"),
        "swap_count": record.get("swap_count"),
        "required_swap_count": record.get("required_swap_count"),
        "swap_requirement_met": record.get("swap_requirement_met"),
        "canonical_gate": record.get("canonical_gate", {}),
        "canonical_acceptance_status": _canonical_acceptance_status(
            record,
            require_cache_eviction=require_cache_eviction,
        ),
        "canonical_acceptance_errors": canonical_errors,
        "clean_for_interrupted_aggregate": eviction_soak._b1c2_segment_ok_for_rehearsal(
            record
        ),
        "session_cache_drops_total": record.get("session_cache_drops_total"),
        "session_cache_evictions_total": record.get("session_cache_evictions_total"),
        "session_cache_window_bypasses_total": record.get(
            "session_cache_window_bypasses_total"
        ),
        "session_cache_window_evictions_total": record.get(
            "session_cache_window_evictions_total"
        ),
        "session_cache_trim_bypasses_total": record.get(
            "session_cache_trim_bypasses_total"
        ),
        "session_cache_trim_evictions_total": record.get(
            "session_cache_trim_evictions_total"
        ),
        "max_drift_bytes": record.get("max_drift_bytes"),
        "max_drift_within_budget": record.get("max_drift_within_budget"),
        "drift_gate": record.get("drift_gate"),
        "session_kv_drift_accounting": record.get("session_kv_drift_accounting"),
        "swap_boundaries_clean": record.get("swap_boundaries_clean"),
        "graduates": record.get("graduates", {}),
        "blockers": blockers,
        "errors": errors,
    }


def audit_b1c2_aggregate_rollup(
    path: Path,
    *,
    require_canonical: bool = False,
    require_cache_eviction: bool = False,
) -> dict[str, Any]:
    record, errors = _read_first_record(path)
    if record is None:
        return {
            "kind": "b1c2_aggregate_rollup",
            "path": str(path),
            "errors": errors,
        }
    if record.get("schema_version") != "b1c2.aggregate.v1":
        errors.append(
            f"wrong_schema:{record.get('schema_version')}:expected_b1c2.aggregate.v1"
        )
    graduates = record.get("graduates", {})
    if not isinstance(graduates, dict):
        graduates = {}
    if graduates.get("session_kv_supported") is True:
        errors.append("unsafe_claim:session_kv_supported=true")
    aggregate = record.get("interrupted_soak_plus_swap", {})
    if not isinstance(aggregate, dict):
        aggregate = {}
    axis_verdicts = aggregate.get("axis_verdicts", {})
    if not isinstance(axis_verdicts, dict):
        axis_verdicts = {}
    required_axes = (
        "load_stability",
        "throughput_stability",
        "switch_stability",
        "concurrency_stability",
    )
    axes_met = all(
        axis_verdicts.get(axis, {}).get("status") == "passed"
        for axis in required_axes
    )
    passed_claim = (
        record.get("conclusion") == "passed"
        or record.get("soak_plus_swap_stability") == "passed"
        or graduates.get("soak_plus_swap_stability") is True
    )
    aggregate_gates_met = (
        aggregate.get("all_segments_ok_for_rehearsal") is True
        and aggregate.get("prerequisite_satisfied") is True
        and aggregate.get("swap_requirement_met") is True
        and aggregate.get("allocator_truth_claimable") is True
        and axes_met
    )
    if passed_claim and not aggregate_gates_met:
        errors.append("unsafe_claim:aggregate_passed_without_all_gates")
    canonical_errors = _canonical_acceptance_errors(
        record,
        require_cache_eviction=require_cache_eviction,
    )
    if require_canonical or require_cache_eviction:
        errors.extend(canonical_errors)

    return {
        "kind": "b1c2_aggregate_rollup",
        "path": str(path),
        "run_id": record.get("run_id"),
        "conclusion": record.get("conclusion"),
        "soak_plus_swap_stability": record.get("soak_plus_swap_stability"),
        "aggregate": aggregate,
        "canonical_gate": record.get("canonical_gate", {}),
        "canonical_acceptance_status": _canonical_acceptance_status(
            record,
            require_cache_eviction=require_cache_eviction,
        ),
        "canonical_acceptance_errors": canonical_errors,
        "graduates": graduates,
        "errors": errors,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, action="append", default=[])
    parser.add_argument("--segment-rollup", type=Path, action="append", default=[])
    parser.add_argument("--aggregate-rollup", type=Path, action="append", default=[])
    parser.add_argument("--require-rollup", action="store_true")
    parser.add_argument("--require-canonical", action="store_true")
    parser.add_argument("--require-cache-eviction", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _render_text(results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for result in results:
        lines.append(f"{result['kind']}: {result['path']}")
        if result["kind"] == "b1c2_ledger":
            lines.append(
                "  records={record_count} last={last_sample_index}/{last_phase} "
                "swaps={swap_count} drops={session_cache_drops_total} "
                "fatal={fatal_watermark_count} gap_free={ledger_gap_free} "
                "acceptance={ledger_acceptance_status}".format(
                    **result
                )
            )
            if result.get("errors"):
                lines.append(f"  errors={result['errors']}")
            if result.get("expected_rollup_canonical_acceptance_status"):
                lines.append(
                    "  expected_rollup_canonical_acceptance="
                    "{expected_rollup_canonical_acceptance_status}".format(**result)
                )
            if result.get("drop_sample_indices"):
                lines.append(f"  drop_samples={result['drop_sample_indices']}")
        else:
            lines.append(
                "  conclusion={conclusion} stability={soak_plus_swap_stability} "
                "errors={errors}".format(**result)
            )
            if result.get("canonical_acceptance_status"):
                lines.append(
                    "  canonical_acceptance={canonical_acceptance_status}".format(
                        **result
                    )
                )
        blockers = result.get("blockers") or []
        if blockers:
            lines.append(f"  blockers={','.join(blockers)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    results: list[dict[str, Any]] = []
    for path in args.ledger:
        results.append(
            audit_b1c2_ledger(
                path,
                require_rollup=args.require_rollup,
                require_canonical=args.require_canonical,
                require_cache_eviction=args.require_cache_eviction,
            )
        )
    for path in args.segment_rollup:
        results.append(
            audit_b1c2_segment_rollup(
                path,
                require_canonical=args.require_canonical,
                require_cache_eviction=args.require_cache_eviction,
            )
        )
    for path in args.aggregate_rollup:
        results.append(
            audit_b1c2_aggregate_rollup(
                path,
                require_canonical=args.require_canonical,
                require_cache_eviction=args.require_cache_eviction,
            )
        )
    if not results:
        print("no audit inputs supplied", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"results": results}, indent=2, sort_keys=True))
    else:
        print(_render_text(results))
    has_errors = any(result.get("errors") for result in results)
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
