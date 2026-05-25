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
    prerequisite_met = record.get("prerequisite_satisfied") is True
    allocator_truth = record.get("allocator_truth_claimable") is True
    clean_segment = eviction_soak._b1c2_segment_ok_for_rehearsal(record)
    passed_claim = (
        record.get("conclusion") == "passed"
        or record.get("soak_plus_swap_stability") == "passed"
        or graduates.get("soak_plus_swap_stability") is True
    )
    if passed_claim and not (
        duration_met and swap_met and prerequisite_met and allocator_truth and clean_segment
    ):
        errors.append("unsafe_claim:soak_plus_swap_passed_without_all_gates")
    if not duration_met and record.get("conclusion") == "passed":
        errors.append("unsafe_claim:passed_without_duration_requirement")
    if not swap_met and record.get("conclusion") == "passed":
        errors.append("unsafe_claim:passed_without_swap_requirement")
    return errors


def audit_b1c2_ledger(path: Path) -> dict[str, Any]:
    records, errors = _read_jsonl(path)
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
    unaccounted_drift_values = []
    for record in records:
        drift = record.get("memory", {}).get("drift_from_measurement_start_bytes")
        resident_estimate = record.get("session_cache", {}).get(
            "resident_bytes_estimate_after"
        )
        if drift is None or resident_estimate is None:
            continue
        unaccounted_drift_values.append(max(_as_int(drift) - _as_int(resident_estimate), 0))

    return {
        "kind": "b1c2_ledger",
        "path": str(path),
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
            }
            for record in drop_records
        ],
        "dirty_swap_sample_indices": dirty_swaps,
        "session_cache_drops_total": _counter_delta_total(records, "drops"),
        "session_cache_expirations_total": _counter_delta_total(records, "expirations"),
        "session_cache_rejects_total": _counter_delta_total(records, "rejects"),
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
        "max_unaccounted_session_kv_drift_bytes": (
            max(unaccounted_drift_values) if unaccounted_drift_values else None
        ),
        "errors": errors,
    }


def audit_b1c2_segment_rollup(path: Path) -> dict[str, Any]:
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
        "clean_for_interrupted_aggregate": eviction_soak._b1c2_segment_ok_for_rehearsal(
            record
        ),
        "session_cache_drops_total": record.get("session_cache_drops_total"),
        "session_cache_window_bypasses_total": record.get(
            "session_cache_window_bypasses_total"
        ),
        "session_cache_window_evictions_total": record.get(
            "session_cache_window_evictions_total"
        ),
        "max_drift_bytes": record.get("max_drift_bytes"),
        "max_drift_within_budget": record.get("max_drift_within_budget"),
        "session_kv_drift_accounting": record.get("session_kv_drift_accounting"),
        "swap_boundaries_clean": record.get("swap_boundaries_clean"),
        "graduates": record.get("graduates", {}),
        "blockers": blockers,
        "errors": errors,
    }


def audit_b1c2_aggregate_rollup(path: Path) -> dict[str, Any]:
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
    passed_claim = (
        record.get("conclusion") == "passed"
        or record.get("soak_plus_swap_stability") == "passed"
        or graduates.get("soak_plus_swap_stability") is True
    )
    aggregate_gates_met = (
        aggregate.get("all_segments_ok_for_rehearsal") is True
        and aggregate.get("prerequisite_satisfied") is True
        and aggregate.get("duration_requirement_met") is True
        and aggregate.get("swap_requirement_met") is True
        and aggregate.get("allocator_truth_claimable") is True
    )
    if passed_claim and not aggregate_gates_met:
        errors.append("unsafe_claim:aggregate_passed_without_all_gates")

    return {
        "kind": "b1c2_aggregate_rollup",
        "path": str(path),
        "run_id": record.get("run_id"),
        "conclusion": record.get("conclusion"),
        "soak_plus_swap_stability": record.get("soak_plus_swap_stability"),
        "aggregate": aggregate,
        "graduates": graduates,
        "errors": errors,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, action="append", default=[])
    parser.add_argument("--segment-rollup", type=Path, action="append", default=[])
    parser.add_argument("--aggregate-rollup", type=Path, action="append", default=[])
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
                "fatal={fatal_watermark_count} gap_free={ledger_gap_free}".format(
                    **result
                )
            )
            if result.get("drop_sample_indices"):
                lines.append(f"  drop_samples={result['drop_sample_indices']}")
        else:
            lines.append(
                "  conclusion={conclusion} stability={soak_plus_swap_stability} "
                "errors={errors}".format(**result)
            )
        blockers = result.get("blockers") or []
        if blockers:
            lines.append(f"  blockers={','.join(blockers)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    results: list[dict[str, Any]] = []
    for path in args.ledger:
        results.append(audit_b1c2_ledger(path))
    for path in args.segment_rollup:
        results.append(audit_b1c2_segment_rollup(path))
    for path in args.aggregate_rollup:
        results.append(audit_b1c2_aggregate_rollup(path))
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
