"""F-4 structured-output invariance bench harness.

F-4.0 is intentionally validator-only: it proves that known-good and
known-bad structured outputs are classified deterministically before any
long-running model matrix is allowed to start.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "structured_output_invariance"
    / "f4_validator_fixtures.jsonl"
)
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "structured-output-invariance"
)

F4_VALIDATOR_FIXTURE_SCHEMA_VERSION = (
    "f4.structured_output_invariance.validator_fixtures.v1"
)
F4_CELL_SCHEMA_VERSION = "f4.structured_output_invariance.cell.v1"
F4_ROLLUP_SCHEMA_VERSION = "f4.structured_output_invariance.rollup.v1"

ALLOWED_FAMILIES = (
    "json_schema_flat",
    "function_call_arguments",
    "nested_object",
    "enum_constrained",
    "thinking_tag_closed",
)
HARD_FAILURE_CODES = (
    "json_parse_failed",
    "schema_required_missing",
    "schema_type_mismatch",
    "enum_value_invalid",
    "tool_arguments_invalid",
    "thinking_tag_unclosed",
    "extra_prose_outside_envelope",
    "semantic_value_mismatch",
    "refusal_or_safety_text",
)
DIAGNOSTIC_CODES = (
    "format_variant",
    "extra_optional_key",
    "case_insensitive_enum_match",
)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    parse_ok: bool
    schema_ok: bool
    hard_break: bool
    failure_codes: tuple[str, ...]
    diagnostic_codes: tuple[str, ...]
    extracted_json: Any | None = None


def _now_compact_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _append_unique(values: list[str], code: str) -> None:
    if code not in values:
        values.append(code)


def _is_int(value: Any) -> bool:
    return type(value) is int


def _parse_json_envelope(output: str) -> tuple[bool, Any | None, bool]:
    stripped = output.strip()
    if not stripped:
        return False, None, False

    try:
        return True, json.loads(stripped), False
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            value, end = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        trailing = stripped[index + end :].strip()
        extra_prose = index != 0 or bool(trailing)
        return True, value, extra_prose
    return False, None, False


def _parse_thinking_envelope(output: str) -> tuple[bool, Any | None, bool, list[str]]:
    failures: list[str] = []
    stripped = output.strip()
    open_count = stripped.count("<thinking>")
    close_count = stripped.count("</thinking>")
    if open_count != close_count or open_count == 0:
        _append_unique(failures, "thinking_tag_unclosed")
        return False, None, False, failures
    if not stripped.startswith("<thinking>"):
        return _parse_json_envelope(stripped)

    close_marker = "</thinking>"
    _, after = stripped.split(close_marker, 1)
    parse_ok, value, extra_prose = _parse_json_envelope(after)
    return parse_ok, value, extra_prose, failures


def _require_fields(
    obj: Mapping[str, Any],
    required: Mapping[str, type | tuple[type, ...]],
    failures: list[str],
) -> None:
    for field, expected_type in required.items():
        if field not in obj:
            _append_unique(failures, "schema_required_missing")
            continue
        value = obj[field]
        if expected_type is int:
            if not _is_int(value):
                _append_unique(failures, "schema_type_mismatch")
            continue
        if expected_type is bool:
            if type(value) is not bool:
                _append_unique(failures, "schema_type_mismatch")
            continue
        if not isinstance(value, expected_type):
            _append_unique(failures, "schema_type_mismatch")


def _check_enum(
    value: Any,
    allowed: tuple[str, ...],
    failures: list[str],
    diagnostics: list[str],
) -> None:
    if not isinstance(value, str):
        _append_unique(failures, "schema_type_mismatch")
        return
    if value in allowed:
        return
    if value.lower() in allowed:
        _append_unique(diagnostics, "case_insensitive_enum_match")
    _append_unique(failures, "enum_value_invalid")


def _check_extra_keys(
    obj: Mapping[str, Any],
    allowed: tuple[str, ...],
    diagnostics: list[str],
) -> None:
    if any(key not in allowed for key in obj):
        _append_unique(diagnostics, "extra_optional_key")


def _validate_json_schema_flat(
    value: Any,
    failures: list[str],
    diagnostics: list[str],
) -> None:
    if not isinstance(value, Mapping):
        _append_unique(failures, "schema_type_mismatch")
        return
    required = {
        "task_id": str,
        "category": str,
        "priority": int,
        "requires_review": bool,
    }
    _require_fields(value, required, failures)
    if "category" in value:
        _check_enum(value["category"], ("bugfix", "feature", "docs", "test"), failures, diagnostics)
    _check_extra_keys(value, tuple(required), diagnostics)


def _validate_function_call_arguments(
    value: Any,
    failures: list[str],
    diagnostics: list[str],
) -> None:
    if not isinstance(value, Mapping):
        _append_unique(failures, "schema_type_mismatch")
        return
    _require_fields(value, {"tool_name": str}, failures)
    if "arguments" not in value:
        _append_unique(failures, "schema_required_missing")
        _append_unique(failures, "tool_arguments_invalid")
    if "tool_name" in value:
        _check_enum(
            value["tool_name"],
            ("apply_patch", "run_tests", "inspect_logs"),
            failures,
            diagnostics,
        )
    arguments = value.get("arguments")
    if not isinstance(arguments, Mapping):
        _append_unique(failures, "tool_arguments_invalid")
        return
    before = tuple(failures)
    _require_fields(arguments, {"target": str, "risk_level": str}, failures)
    if tuple(failures) != before:
        _append_unique(failures, "tool_arguments_invalid")
    if "risk_level" in arguments:
        _check_enum(arguments["risk_level"], ("low", "medium", "high"), failures, diagnostics)
    _check_extra_keys(value, ("tool_name", "arguments"), diagnostics)
    _check_extra_keys(arguments, ("target", "risk_level"), diagnostics)


def _validate_nested_object(
    value: Any,
    failures: list[str],
    diagnostics: list[str],
) -> None:
    if not isinstance(value, Mapping):
        _append_unique(failures, "schema_type_mismatch")
        return
    diagnosis = value.get("diagnosis")
    if "diagnosis" not in value:
        _append_unique(failures, "schema_required_missing")
        return
    if not isinstance(diagnosis, Mapping):
        _append_unique(failures, "schema_type_mismatch")
        return
    _require_fields(
        diagnosis,
        {"root_cause": str, "evidence": list, "next_action": dict},
        failures,
    )
    evidence = diagnosis.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, Mapping):
                _append_unique(failures, "schema_type_mismatch")
                continue
            _require_fields(item, {"source": str, "summary": str}, failures)
            _check_extra_keys(item, ("source", "summary"), diagnostics)
    next_action = diagnosis.get("next_action")
    if isinstance(next_action, Mapping):
        _require_fields(next_action, {"kind": str, "owner": str}, failures)
        if "kind" in next_action:
            _check_enum(next_action["kind"], ("retry", "fix", "escalate"), failures, diagnostics)
        if "owner" in next_action:
            _check_enum(next_action["owner"], ("runtime", "operator"), failures, diagnostics)
        _check_extra_keys(next_action, ("kind", "owner"), diagnostics)
    _check_extra_keys(value, ("diagnosis",), diagnostics)
    _check_extra_keys(diagnosis, ("root_cause", "evidence", "next_action"), diagnostics)


def _validate_enum_constrained(
    value: Any,
    failures: list[str],
    diagnostics: list[str],
) -> None:
    if not isinstance(value, Mapping):
        _append_unique(failures, "schema_type_mismatch")
        return
    _require_fields(value, {"capability_label": str, "reason_code": str}, failures)
    if "capability_label" in value:
        _check_enum(
            value["capability_label"],
            ("supported", "partial", "experimental", "not_in_scope"),
            failures,
            diagnostics,
        )
    _check_extra_keys(value, ("capability_label", "reason_code"), diagnostics)


def _validate_thinking_tag_closed(
    value: Any,
    failures: list[str],
    diagnostics: list[str],
) -> None:
    if not isinstance(value, Mapping):
        _append_unique(failures, "schema_type_mismatch")
        return
    _require_fields(value, {"final": str, "confidence": str}, failures)
    if "confidence" in value:
        _check_enum(value["confidence"], ("low", "medium", "high"), failures, diagnostics)
    _check_extra_keys(value, ("final", "confidence"), diagnostics)


FAMILY_VALIDATORS = {
    "json_schema_flat": _validate_json_schema_flat,
    "function_call_arguments": _validate_function_call_arguments,
    "nested_object": _validate_nested_object,
    "enum_constrained": _validate_enum_constrained,
    "thinking_tag_closed": _validate_thinking_tag_closed,
}


def validate_structured_output(*, family: str, output: str) -> ValidationResult:
    if family not in FAMILY_VALIDATORS:
        raise ValueError(f"unsupported F-4 family: {family}")

    failure_codes: list[str] = []
    diagnostic_codes: list[str] = []
    if family == "thinking_tag_closed":
        parsed, extracted_json, extra_prose, tag_failures = _parse_thinking_envelope(output)
        for code in tag_failures:
            _append_unique(failure_codes, code)
    else:
        parsed, extracted_json, extra_prose = _parse_json_envelope(output)

    if extra_prose:
        _append_unique(failure_codes, "extra_prose_outside_envelope")
    if not parsed:
        if "thinking_tag_unclosed" not in failure_codes:
            _append_unique(failure_codes, "json_parse_failed")
        return ValidationResult(
            parse_ok=False,
            schema_ok=False,
            hard_break=True,
            failure_codes=tuple(failure_codes),
            diagnostic_codes=tuple(diagnostic_codes),
            extracted_json=None,
        )

    FAMILY_VALIDATORS[family](extracted_json, failure_codes, diagnostic_codes)
    schema_failures = [
        code
        for code in failure_codes
        if code not in ("extra_prose_outside_envelope",)
    ]
    schema_ok = not schema_failures
    hard_break = any(code in HARD_FAILURE_CODES for code in failure_codes)
    return ValidationResult(
        parse_ok=True,
        schema_ok=schema_ok,
        hard_break=hard_break,
        failure_codes=tuple(failure_codes),
        diagnostic_codes=tuple(diagnostic_codes),
        extracted_json=extracted_json,
    )


def load_fixture_rows(path: str | Path = DEFAULT_FIXTURE_PATH) -> list[dict[str, Any]]:
    fixture_path = Path(path)
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(fixture_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("family") not in ALLOWED_FAMILIES:
            raise ValueError(f"{fixture_path}:{line_number} has unsupported family")
        rows.append(row)
    return rows


def _result_to_payload(result: ValidationResult) -> dict[str, Any]:
    return {
        "parse_ok": result.parse_ok,
        "schema_ok": result.schema_ok,
        "hard_break": result.hard_break,
        "failure_codes": list(result.failure_codes),
        "diagnostic_codes": list(result.diagnostic_codes),
        "extracted_json": result.extracted_json,
    }


def record_for_fixture(
    fixture: Mapping[str, Any],
    *,
    run_id: str,
    created_at_utc: str | None,
) -> dict[str, Any]:
    result = validate_structured_output(
        family=str(fixture["family"]),
        output=str(fixture["output"]),
    )
    expected = fixture.get("expected", {})
    actual = _result_to_payload(result)
    comparable_actual = {
        "parse_ok": actual["parse_ok"],
        "schema_ok": actual["schema_ok"],
        "hard_break": actual["hard_break"],
        "failure_codes": actual["failure_codes"],
        "diagnostic_codes": actual["diagnostic_codes"],
    }
    fixture_expected_match = comparable_actual == expected
    payload: dict[str, Any] = {
        "schema_version": F4_CELL_SCHEMA_VERSION,
        "run_id": run_id,
        "phase": "validator-fixtures",
        "created_at_utc": created_at_utc,
        "case_id": fixture["case_id"],
        "family": fixture["family"],
        "description": fixture.get("description", ""),
        "output_hash": _json_hash(str(fixture["output"])),
        "parse_ok": actual["parse_ok"],
        "schema_ok": actual["schema_ok"],
        "hard_break": actual["hard_break"],
        "failure_codes": actual["failure_codes"],
        "diagnostic_codes": actual["diagnostic_codes"],
        "expected": expected,
        "fixture_expected_match": fixture_expected_match,
    }
    if actual["extracted_json"] is not None:
        payload["extracted_json"] = actual["extracted_json"]
    return payload


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def rollup_records(
    rows: list[Mapping[str, Any]],
    *,
    run_id: str,
    phase: str,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    sample_count = len(rows)
    hard_break_count = sum(1 for row in rows if row.get("hard_break") is True)
    fixture_mismatch_count = sum(
        1 for row in rows if row.get("fixture_expected_match") is False
    )
    failure_counts: Counter[str] = Counter()
    diagnostic_counts: Counter[str] = Counter()
    by_family: dict[str, dict[str, int]] = {}
    for row in rows:
        family = str(row.get("family", "unknown"))
        bucket = by_family.setdefault(family, {"sample_count": 0, "hard_break_count": 0})
        bucket["sample_count"] += 1
        if row.get("hard_break") is True:
            bucket["hard_break_count"] += 1
        for code in row.get("failure_codes", []):
            failure_counts[str(code)] += 1
        for code in row.get("diagnostic_codes", []):
            diagnostic_counts[str(code)] += 1

    for bucket in by_family.values():
        bucket["hard_break_rate"] = (
            bucket["hard_break_count"] / bucket["sample_count"]
            if bucket["sample_count"]
            else 0.0
        )

    validator_contract = sample_count > 0 and fixture_mismatch_count == 0
    return {
        "schema_version": F4_VALIDATOR_FIXTURE_SCHEMA_VERSION,
        "run_id": run_id,
        "phase": phase,
        "created_at_utc": created_at_utc,
        "sample_count": sample_count,
        "hard_break_count": hard_break_count,
        "hard_break_rate": hard_break_count / sample_count if sample_count else 0.0,
        "fixture_mismatch_count": fixture_mismatch_count,
        "failure_code_counts": _counter_to_dict(failure_counts),
        "diagnostic_code_counts": _counter_to_dict(diagnostic_counts),
        "by_family": {key: by_family[key] for key in sorted(by_family)},
        "graduates": {
            "validator_contract": validator_contract,
            "measurement_harness": phase != "validator-fixtures" and validator_contract,
            "structured_output_invariance_promotion_candidate": False,
        },
    }


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            handle.write("\n")


def run_validator_fixtures(
    *,
    fixtures: Path,
    output_dir: Path,
    run_id: str,
) -> dict[str, Any]:
    created_at = _now_iso_utc()
    fixture_rows = load_fixture_rows(fixtures)
    records = [
        record_for_fixture(row, run_id=run_id, created_at_utc=created_at)
        for row in fixture_rows
    ]
    rollup = rollup_records(
        records,
        run_id=run_id,
        phase="validator-fixtures",
        created_at_utc=created_at,
    )
    rows_path = output_dir / f"{run_id}.jsonl"
    rollup_path = output_dir / f"{run_id}-rollup.jsonl"
    write_jsonl(rows_path, records)
    write_jsonl(rollup_path, [rollup])
    return {
        "phase": "validator-fixtures",
        "run_id": run_id,
        "rows_path": str(rows_path),
        "rollup_path": str(rollup_path),
        "sample_count": rollup["sample_count"],
        "hard_break_count": rollup["hard_break_count"],
        "fixture_mismatch_count": rollup["fixture_mismatch_count"],
        "graduates": rollup["graduates"],
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="F-4 structured-output invariance validator and smoke harness"
    )
    parser.add_argument(
        "--phase",
        choices=("validator-fixtures", "smoke"),
        default="validator-fixtures",
    )
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--models", nargs="*", default=())
    parser.add_argument("--chunks", nargs="*", type=int, default=(2048,))
    parser.add_argument("--temperatures", nargs="*", type=float, default=(0.0, 0.3))
    parser.add_argument("--samples-per-family", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    run_id = args.run_id or f"{_now_compact_utc()}-f4-validator-fixtures"
    if args.phase == "smoke":
        raise SystemExit(
            "F-4.1 smoke generation is scaffolded in CLI arguments but not "
            "executed in F-4.0; run validator-fixtures first."
        )

    result = run_validator_fixtures(
        fixtures=args.fixtures,
        output_dir=args.output_dir,
        run_id=run_id,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["fixture_mismatch_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
