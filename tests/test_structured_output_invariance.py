from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.bench.structured_output_invariance import (
    F4_VALIDATOR_FIXTURE_SCHEMA_VERSION,
    load_fixture_rows,
    record_for_fixture,
    rollup_records,
    validate_structured_output,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "structured_output_invariance"
    / "f4_validator_fixtures.jsonl"
)


def test_fixture_file_has_required_families_and_failure_cases() -> None:
    rows = load_fixture_rows(FIXTURE_PATH)

    assert {row["family"] for row in rows} == {
        "json_schema_flat",
        "function_call_arguments",
        "nested_object",
        "enum_constrained",
        "thinking_tag_closed",
    }

    expected_failure_codes = {
        code
        for row in rows
        for code in row["expected"]["failure_codes"]
    }
    assert {
        "json_parse_failed",
        "schema_required_missing",
        "schema_type_mismatch",
        "enum_value_invalid",
        "tool_arguments_invalid",
        "thinking_tag_unclosed",
        "extra_prose_outside_envelope",
    } <= expected_failure_codes


@pytest.mark.parametrize("fixture", load_fixture_rows(FIXTURE_PATH))
def test_validator_matches_f4_fixture_expectations(fixture: dict[str, object]) -> None:
    result = validate_structured_output(
        family=str(fixture["family"]),
        output=str(fixture["output"]),
    )
    expected = fixture["expected"]

    assert result.parse_ok is expected["parse_ok"]
    assert result.schema_ok is expected["schema_ok"]
    assert result.hard_break is expected["hard_break"]
    assert result.failure_codes == tuple(expected["failure_codes"])
    assert result.diagnostic_codes == tuple(expected["diagnostic_codes"])


def test_validator_classification_is_deterministic() -> None:
    rows = load_fixture_rows(FIXTURE_PATH)

    first = [
        record_for_fixture(row, run_id="deterministic", created_at_utc=None)
        for row in rows
    ]
    second = [
        record_for_fixture(row, run_id="deterministic", created_at_utc=None)
        for row in rows
    ]

    assert first == second


def test_fixture_rollup_reports_break_rate_and_graduation() -> None:
    rows = [
        record_for_fixture(row, run_id="rollup", created_at_utc=None)
        for row in load_fixture_rows(FIXTURE_PATH)
    ]

    rollup = rollup_records(rows, run_id="rollup", phase="validator-fixtures")

    assert rollup["schema_version"] == F4_VALIDATOR_FIXTURE_SCHEMA_VERSION
    assert rollup["sample_count"] == len(rows)
    assert rollup["hard_break_count"] == 7
    assert rollup["hard_break_rate"] == pytest.approx(0.7)
    assert rollup["fixture_mismatch_count"] == 0
    assert rollup["failure_code_counts"]["json_parse_failed"] == 1
    assert rollup["failure_code_counts"]["schema_required_missing"] == 1
    assert rollup["failure_code_counts"]["extra_prose_outside_envelope"] == 1
    assert rollup["diagnostic_code_counts"]["extra_optional_key"] == 1
    assert rollup["graduates"] == {
        "validator_contract": True,
        "measurement_harness": False,
        "structured_output_invariance_promotion_candidate": False,
    }


def test_cli_writes_validator_fixture_evidence(tmp_path: Path) -> None:
    run_id = "pytest-f4-validator"
    output_dir = tmp_path / "evidence"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/bench/structured_output_invariance.py",
            "--phase",
            "validator-fixtures",
            "--fixtures",
            str(FIXTURE_PATH),
            "--output-dir",
            str(output_dir),
            "--run-id",
            run_id,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    stdout = json.loads(completed.stdout)
    rows_path = Path(stdout["rows_path"])
    rollup_path = Path(stdout["rollup_path"])
    assert rows_path.exists()
    assert rollup_path.exists()

    rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
    assert rows[0]["case_id"] == "f4-json-flat-valid-001"
    assert rows[0]["parse_ok"] is True
    assert rows[0]["schema_ok"] is True
    assert rows[0]["hard_break"] is False

    rollup = json.loads(rollup_path.read_text().strip())
    assert rollup["run_id"] == run_id
    assert rollup["graduates"]["validator_contract"] is True
