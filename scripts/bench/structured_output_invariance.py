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
import time
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
DEFAULT_CASES_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "structured_output_invariance"
    / "f4_cases.jsonl"
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
DEFAULT_SMOKE_MODELS = (
    "qwen3.6-27b-4bit",
    "qwen3.6-35b-a3b-4bit",
    "gemma-4-31b-it-4bit",
)
DEFAULT_SMOKE_CHUNKS = (2048,)
DEFAULT_SMOKE_TEMPERATURES = (0.0, 0.3)
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


def _dimension_key(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


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
        parse_ok, value, extra_prose = _parse_json_envelope(stripped)
        return parse_ok, value, extra_prose, failures

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


def load_smoke_cases(path: str | Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    cases_path = Path(path)
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(cases_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("family") not in ALLOWED_FAMILIES:
            raise ValueError(f"{cases_path}:{line_number} has unsupported family")
        if not row.get("case_id") or not row.get("prompt"):
            raise ValueError(f"{cases_path}:{line_number} must include case_id and prompt")
        cases.append(row)
    return cases


def _filter_cases_by_family(
    cases: list[dict[str, Any]],
    families: tuple[str, ...] | None,
) -> list[dict[str, Any]]:
    """Keep only cases whose family is in ``families`` (None = keep all).

    Used by the F-4.3 narrow reliability lane to restrict the matrix to the
    clean families. Raises on an unknown family so a typo cannot silently
    produce an empty plan.
    """
    if not families:
        return cases
    unknown = [f for f in families if f not in ALLOWED_FAMILIES]
    if unknown:
        raise ValueError(f"unknown F-4 families requested: {unknown}")
    wanted = set(families)
    return [case for case in cases if case.get("family") in wanted]


def build_smoke_plan(
    *,
    cases: list[Mapping[str, Any]],
    models: tuple[str, ...],
    chunks: tuple[int, ...],
    temperatures: tuple[float, ...],
    samples_per_family: int,
) -> list[dict[str, Any]]:
    if samples_per_family < 1:
        raise ValueError("samples_per_family must be >= 1")
    plan: list[dict[str, Any]] = []
    for model_id in models:
        for chunk_tokens in chunks:
            for temperature in temperatures:
                for run_idx in range(1, samples_per_family + 1):
                    for case in cases:
                        plan.append(
                            {
                                "case_id": case["case_id"],
                                "family": case["family"],
                                "prompt": case["prompt"],
                                "model_id": model_id,
                                "chunk_tokens": int(chunk_tokens),
                                "temperature": float(temperature),
                                "run_idx": run_idx,
                            }
                        )
    return plan


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


def record_for_smoke_output(
    cell: Mapping[str, Any],
    *,
    run_id: str,
    created_at_utc: str | None,
    output: str,
    metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result = validate_structured_output(
        family=str(cell["family"]),
        output=output,
    )
    actual = _result_to_payload(result)
    payload: dict[str, Any] = {
        "schema_version": F4_CELL_SCHEMA_VERSION,
        "run_id": run_id,
        "phase": "smoke",
        "created_at_utc": created_at_utc,
        "case_id": cell["case_id"],
        "family": cell["family"],
        "model_id": cell["model_id"],
        "chunk_tokens": cell["chunk_tokens"],
        "temperature": cell["temperature"],
        "run_idx": cell["run_idx"],
        "status": "ok",
        "prompt_hash": _json_hash(str(cell["prompt"])),
        "output_hash": _json_hash(output),
        "output_text": output,
        "parse_ok": actual["parse_ok"],
        "schema_ok": actual["schema_ok"],
        "hard_break": actual["hard_break"],
        "failure_codes": actual["failure_codes"],
        "diagnostic_codes": actual["diagnostic_codes"],
        "metrics": dict(metrics or {}),
    }
    if actual["extracted_json"] is not None:
        payload["extracted_json"] = actual["extracted_json"]
    return payload


def record_for_generation_error(
    cell: Mapping[str, Any],
    *,
    run_id: str,
    created_at_utc: str | None,
    message: str,
    metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": F4_CELL_SCHEMA_VERSION,
        "run_id": run_id,
        "phase": "smoke",
        "created_at_utc": created_at_utc,
        "case_id": cell["case_id"],
        "family": cell["family"],
        "model_id": cell["model_id"],
        "chunk_tokens": cell["chunk_tokens"],
        "temperature": cell["temperature"],
        "run_idx": cell["run_idx"],
        "status": "generation_error",
        "prompt_hash": _json_hash(str(cell["prompt"])),
        "output_hash": None,
        "parse_ok": False,
        "schema_ok": False,
        "hard_break": False,
        "failure_codes": [],
        "diagnostic_codes": [],
        "metrics": dict(metrics or {}),
        "error_message": message,
    }


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _bump_bucket(bucket: dict[str, int], row: Mapping[str, Any]) -> None:
    bucket["sample_count"] += 1
    if row.get("hard_break") is True:
        bucket["hard_break_count"] += 1
    if row.get("status") != "ok":
        bucket["generation_error_count"] += 1


def _finalize_bucket(bucket: dict[str, int]) -> dict[str, Any]:
    sample_count = bucket["sample_count"]
    return {
        "sample_count": sample_count,
        "hard_break_count": bucket["hard_break_count"],
        "hard_break_rate": (
            bucket["hard_break_count"] / sample_count if sample_count else 0.0
        ),
        "generation_error_count": bucket["generation_error_count"],
    }


def rollup_records(
    rows: list[Mapping[str, Any]],
    *,
    run_id: str,
    phase: str,
    created_at_utc: str | None = None,
    expected_sample_count: int | None = None,
) -> dict[str, Any]:
    sample_count = len(rows)
    hard_break_count = sum(1 for row in rows if row.get("hard_break") is True)
    fixture_mismatch_count = sum(
        1 for row in rows if row.get("fixture_expected_match") is False
    )
    generation_error_count = sum(1 for row in rows if row.get("status") != "ok")
    diagnostic_variant_count = sum(1 for row in rows if row.get("diagnostic_codes"))
    failure_counts: Counter[str] = Counter()
    diagnostic_counts: Counter[str] = Counter()
    by_family: dict[str, dict[str, int]] = {}
    by_model: dict[str, dict[str, int]] = {}
    by_temperature: dict[str, dict[str, int]] = {}
    by_chunk_tokens: dict[str, dict[str, int]] = {}
    for row in rows:
        family = str(row.get("family", "unknown"))
        model = str(row.get("model_id", "unknown"))
        temperature = _dimension_key(row.get("temperature", "unknown"))
        chunk_tokens = _dimension_key(row.get("chunk_tokens", "unknown"))
        for buckets, key in (
            (by_family, family),
            (by_model, model),
            (by_temperature, temperature),
            (by_chunk_tokens, chunk_tokens),
        ):
            bucket = buckets.setdefault(
                key,
                {"sample_count": 0, "hard_break_count": 0, "generation_error_count": 0},
            )
            _bump_bucket(bucket, row)
        for code in row.get("failure_codes", []):
            failure_counts[str(code)] += 1
        for code in row.get("diagnostic_codes", []):
            diagnostic_counts[str(code)] += 1

    validator_contract = sample_count > 0 and fixture_mismatch_count == 0
    expected_ok = expected_sample_count is None or sample_count >= expected_sample_count
    measurement_harness = (
        phase != "validator-fixtures"
        and validator_contract
        and expected_ok
        and generation_error_count == 0
    )
    payload: dict[str, Any] = {
        "schema_version": (
            F4_VALIDATOR_FIXTURE_SCHEMA_VERSION
            if phase == "validator-fixtures"
            else F4_ROLLUP_SCHEMA_VERSION
        ),
        "run_id": run_id,
        "phase": phase,
        "created_at_utc": created_at_utc,
        "sample_count": sample_count,
        "expected_sample_count": expected_sample_count,
        "hard_break_count": hard_break_count,
        "hard_break_rate": hard_break_count / sample_count if sample_count else 0.0,
        "generation_error_count": generation_error_count,
        "diagnostic_variant_count": diagnostic_variant_count,
        "diagnostic_variant_rate": (
            diagnostic_variant_count / sample_count if sample_count else 0.0
        ),
        "fixture_mismatch_count": fixture_mismatch_count,
        "failure_code_counts": _counter_to_dict(failure_counts),
        "diagnostic_code_counts": _counter_to_dict(diagnostic_counts),
        "by_family": {
            key: _finalize_bucket(by_family[key]) for key in sorted(by_family)
        },
        "graduates": {
            "validator_contract": validator_contract,
            "measurement_harness": measurement_harness,
            "structured_output_invariance_promotion_candidate": False,
        },
    }
    if phase != "validator-fixtures":
        payload["by_model"] = {
            key: _finalize_bucket(by_model[key]) for key in sorted(by_model)
        }
        payload["by_temperature"] = {
            key: _finalize_bucket(by_temperature[key]) for key in sorted(by_temperature)
        }
        payload["by_chunk_tokens"] = {
            key: _finalize_bucket(by_chunk_tokens[key])
            for key in sorted(by_chunk_tokens)
        }
    return payload


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            handle.write("\n")


def append_jsonl_row(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
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


def _model_path_resolver(model_id: str) -> str:
    from scripts.bench.long_context_ladder import MODEL_PATHS

    return MODEL_PATHS[model_id]


# F-4.2b per-family grammar specs. These are the schemas verified model-free in
# scripts/probe/f4_grammar_per_family_verify.py (evidence
# 20260529T024253Z-f4-2-per-family-grammar-verify.json, all_families_pass=true):
# four families use a plain JSON-schema grammar; thinking_tag_closed uses an
# xgrammar structural tag triggered on the closing </thinking> tag so the
# reasoning envelope stays free text and only the trailing JSON is constrained.
F4_FAMILY_GRAMMARS: dict[str, dict[str, Any]] = {
    "json_schema_flat": {
        "kind": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["bugfix", "feature", "docs", "test"],
                },
                "priority": {"type": "integer"},
                "requires_review": {"type": "boolean"},
            },
            "required": ["task_id", "category", "priority", "requires_review"],
            "additionalProperties": False,
        },
    },
    "function_call_arguments": {
        "kind": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "enum": ["apply_patch", "run_tests", "inspect_logs"],
                },
                "arguments": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "risk_level": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                    "required": ["target", "risk_level"],
                    "additionalProperties": False,
                },
            },
            "required": ["tool_name", "arguments"],
            "additionalProperties": False,
        },
    },
    "nested_object": {
        "kind": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "diagnosis": {
                    "type": "object",
                    "properties": {
                        "root_cause": {"type": "string"},
                        "evidence": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "summary": {"type": "string"},
                                },
                                "required": ["source", "summary"],
                                "additionalProperties": False,
                            },
                        },
                        "next_action": {
                            "type": "object",
                            "properties": {
                                "kind": {
                                    "type": "string",
                                    "enum": ["retry", "fix", "escalate"],
                                },
                                "owner": {
                                    "type": "string",
                                    "enum": ["runtime", "operator"],
                                },
                            },
                            "required": ["kind", "owner"],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["root_cause", "evidence", "next_action"],
                    "additionalProperties": False,
                }
            },
            "required": ["diagnosis"],
            "additionalProperties": False,
        },
    },
    "enum_constrained": {
        "kind": "json_schema",
        # "supported" below is a fixture ENUM VALUE, not a capability claim.
        "schema": {
            "type": "object",
            "properties": {
                "capability_label": {
                    "type": "string",
                    "enum": ["supported", "partial", "experimental", "not_in_scope"],
                },
                "reason_code": {"type": "string"},
            },
            "required": ["capability_label", "reason_code"],
            "additionalProperties": False,
        },
    },
    "thinking_tag_closed": {
        "kind": "structural_tag",
        "begin": "</thinking>",
        "end": "",
        "schema": {
            "type": "object",
            "properties": {
                "final": {"type": "string"},
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
            },
            "required": ["final", "confidence"],
            "additionalProperties": False,
        },
    },
}


def f4_family_grammar(family: str) -> dict[str, Any] | None:
    """Return the grammar spec for an F-4 family, or None if unknown."""
    return F4_FAMILY_GRAMMARS.get(family)


def _run_generation_cell(
    *,
    backend: Any,
    cell: Mapping[str, Any],
    max_tokens: int,
    grammar: Mapping[str, Any] | None = None,
) -> tuple[str | None, dict[str, Any], str | None]:
    t_start = time.perf_counter()
    t_first_token: float | None = None
    output_parts: list[str] = []
    prefill_progress_events = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None
    error_message: str | None = None

    stream_kwargs: dict[str, Any] = {
        "max_tokens": max_tokens,
        "temperature": float(cell["temperature"]),
        "prefill_chunk_tokens": int(cell["chunk_tokens"]),
    }
    if grammar is not None:
        stream_kwargs["grammar"] = dict(grammar)

    for event in backend.stream_generate(
        str(cell["model_id"]),
        str(cell["prompt"]),
        **stream_kwargs,
    ):
        if event.event == "prefill_progress":
            prefill_progress_events += 1
            continue
        if event.event == "token":
            if t_first_token is None:
                t_first_token = time.perf_counter()
            output_parts.append(str(event.text or ""))
            if event.prompt_tokens is not None:
                prompt_tokens = int(event.prompt_tokens)
            if event.completion_tokens is not None:
                completion_tokens = int(event.completion_tokens)
            continue
        if event.event == "done":
            if event.prompt_tokens is not None:
                prompt_tokens = int(event.prompt_tokens)
            if event.completion_tokens is not None:
                completion_tokens = int(event.completion_tokens)
            if event.finish_reason is not None:
                finish_reason = str(event.finish_reason)
            break
        if event.event == "error":
            detail = event.detail if isinstance(event.detail, Mapping) else {}
            error_message = str(detail.get("message") or event.error_code or "stream error")
            break

    finished = time.perf_counter()
    metrics: dict[str, Any] = {
        "elapsed_ms": round((finished - t_start) * 1000, 3),
        "ttft_ms": (
            round((t_first_token - t_start) * 1000, 3)
            if t_first_token is not None
            else None
        ),
        "prefill_progress_event_count": prefill_progress_events,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "finish_reason": finish_reason,
    }
    if error_message:
        return None, metrics, error_message
    return "".join(output_parts), metrics, None


def run_smoke_matrix(
    *,
    cases: Path,
    output_dir: Path,
    run_id: str,
    models: tuple[str, ...],
    chunks: tuple[int, ...],
    temperatures: tuple[float, ...],
    samples_per_family: int,
    max_tokens: int,
    timeout_s: float,
    python_executable: str | None = None,
    grammar_enabled: bool = False,
    families: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend

    created_at = _now_iso_utc()
    smoke_cases = _filter_cases_by_family(load_smoke_cases(cases), families)
    plan = build_smoke_plan(
        cases=smoke_cases,
        models=models,
        chunks=chunks,
        temperatures=temperatures,
        samples_per_family=samples_per_family,
    )
    rows_path = output_dir / f"{run_id}.jsonl"
    rollup_path = output_dir / f"{run_id}-rollup.jsonl"
    if rows_path.exists():
        rows_path.unlink()
    if rollup_path.exists():
        rollup_path.unlink()

    backend = MlxLmSubprocessBackend(
        python_executable=python_executable,
        model_path_resolver=_model_path_resolver,
        timeout_s=timeout_s,
        extra_pythonpath=(str(REPO_ROOT),),
    )
    rows: list[dict[str, Any]] = []
    loaded_model: str | None = None
    try:
        for cell in plan:
            model_id = str(cell["model_id"])
            if loaded_model != model_id:
                if loaded_model is not None:
                    backend.unload(loaded_model)
                load_result = backend.load(model_id)
                loaded_model = model_id if load_result.ok else None
                if not load_result.ok:
                    row = record_for_generation_error(
                        cell,
                        run_id=run_id,
                        created_at_utc=created_at,
                        message=load_result.message,
                        metrics={"load_error_code": str(load_result.error_code)},
                    )
                    rows.append(row)
                    append_jsonl_row(rows_path, row)
                    continue

            cell_grammar = (
                f4_family_grammar(str(cell["family"])) if grammar_enabled else None
            )
            output, metrics, error_message = _run_generation_cell(
                backend=backend,
                cell=cell,
                max_tokens=max_tokens,
                grammar=cell_grammar,
            )
            if error_message is not None or output is None:
                row = record_for_generation_error(
                    cell,
                    run_id=run_id,
                    created_at_utc=created_at,
                    message=error_message or "missing generation output",
                    metrics=metrics,
                )
            else:
                row = record_for_smoke_output(
                    cell,
                    run_id=run_id,
                    created_at_utc=created_at,
                    output=output,
                    metrics=metrics,
                )
            rows.append(row)
            append_jsonl_row(rows_path, row)
    finally:
        if loaded_model is not None:
            backend.unload(loaded_model)

    rollup = rollup_records(
        rows,
        run_id=run_id,
        phase="smoke",
        created_at_utc=created_at,
        expected_sample_count=len(plan),
    )
    write_jsonl(rollup_path, [rollup])
    return {
        "phase": "smoke",
        "run_id": run_id,
        "grammar_enabled": grammar_enabled,
        "rows_path": str(rows_path),
        "rollup_path": str(rollup_path),
        "sample_count": rollup["sample_count"],
        "hard_break_count": rollup["hard_break_count"],
        "hard_break_rate": rollup["hard_break_rate"],
        "generation_error_count": rollup["generation_error_count"],
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
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--models", nargs="*", default=DEFAULT_SMOKE_MODELS)
    parser.add_argument("--chunks", nargs="*", type=int, default=DEFAULT_SMOKE_CHUNKS)
    parser.add_argument("--temperatures", nargs="*", type=float, default=DEFAULT_SMOKE_TEMPERATURES)
    parser.add_argument("--samples-per-family", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--timeout-s", type=float, default=600.0)
    parser.add_argument("--python-executable", default=None)
    parser.add_argument(
        "--grammar",
        action="store_true",
        help="F-4.2b: constrain each cell with its per-family grammar spec",
    )
    parser.add_argument(
        "--families",
        nargs="*",
        default=None,
        help="F-4.3: restrict the matrix to these families (default: all)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    smoke_label = "f4-2-grammar-matrix" if args.grammar else "f4-smoke-matrix"
    run_id = args.run_id or (
        f"{_now_compact_utc()}-{smoke_label}"
        if args.phase == "smoke"
        else f"{_now_compact_utc()}-f4-validator-fixtures"
    )
    if args.phase == "smoke":
        result = run_smoke_matrix(
            cases=args.cases,
            output_dir=args.output_dir,
            run_id=run_id,
            models=tuple(args.models),
            chunks=tuple(args.chunks),
            temperatures=tuple(args.temperatures),
            samples_per_family=args.samples_per_family,
            max_tokens=args.max_tokens,
            timeout_s=args.timeout_s,
            python_executable=args.python_executable,
            grammar_enabled=args.grammar,
            families=tuple(args.families) if args.families else None,
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if result["graduates"]["measurement_harness"] else 1

    result = run_validator_fixtures(
        fixtures=args.fixtures,
        output_dir=args.output_dir,
        run_id=run_id,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["fixture_mismatch_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
