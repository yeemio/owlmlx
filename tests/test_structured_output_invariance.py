from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.bench.structured_output_invariance import (
    F4_ROLLUP_SCHEMA_VERSION,
    F4_VALIDATOR_FIXTURE_SCHEMA_VERSION,
    build_smoke_plan,
    load_fixture_rows,
    load_smoke_cases,
    record_for_fixture,
    record_for_smoke_output,
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
CASES_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "structured_output_invariance"
    / "f4_cases.jsonl"
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


def test_thinking_validator_handles_closed_tag_with_leading_prose() -> None:
    result = validate_structured_output(
        family="thinking_tag_closed",
        output=(
            "Here is the answer. "
            '<thinking>brief check</thinking>{"final":"ok","confidence":"high"}'
        ),
    )

    assert result.parse_ok is True
    assert result.schema_ok is True
    assert result.hard_break is True
    assert result.failure_codes == ("extra_prose_outside_envelope",)


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


def test_smoke_cases_cover_required_families() -> None:
    rows = load_smoke_cases(CASES_PATH)

    assert {row["family"] for row in rows} == {
        "json_schema_flat",
        "function_call_arguments",
        "nested_object",
        "enum_constrained",
        "thinking_tag_closed",
    }
    assert all(row["case_id"].startswith("f4-") for row in rows)
    assert all(row["prompt"] for row in rows)


def test_smoke_plan_builds_minimum_f4_1_matrix() -> None:
    cases = load_smoke_cases(CASES_PATH)
    plan = build_smoke_plan(
        cases=cases,
        models=("m1", "m2", "m3"),
        chunks=(2048,),
        temperatures=(0.0, 0.3),
        samples_per_family=2,
    )

    assert len(plan) == 60
    assert {cell["family"] for cell in plan} == {
        "json_schema_flat",
        "function_call_arguments",
        "nested_object",
        "enum_constrained",
        "thinking_tag_closed",
    }
    assert {cell["model_id"] for cell in plan} == {"m1", "m2", "m3"}
    assert {cell["temperature"] for cell in plan} == {0.0, 0.3}
    assert {cell["chunk_tokens"] for cell in plan} == {2048}
    assert {cell["run_idx"] for cell in plan} == {1, 2}


def test_smoke_record_uses_validator_contract_fields() -> None:
    case = next(
        row
        for row in load_smoke_cases(CASES_PATH)
        if row["family"] == "json_schema_flat"
    )
    cell = {
        **case,
        "model_id": "m1",
        "chunk_tokens": 2048,
        "temperature": 0.0,
        "run_idx": 1,
    }

    row = record_for_smoke_output(
        cell,
        run_id="smoke",
        created_at_utc=None,
        output=(
            '{"task_id":"F4-JSON-001","category":"bugfix",'
            '"priority":1,"requires_review":false}'
        ),
        metrics={"ttft_ms": 12.5},
    )

    assert row["schema_version"] == "f4.structured_output_invariance.cell.v1"
    assert row["phase"] == "smoke"
    assert row["status"] == "ok"
    assert row["model_id"] == "m1"
    assert row["chunk_tokens"] == 2048
    assert row["temperature"] == 0.0
    assert row["parse_ok"] is True
    assert row["schema_ok"] is True
    assert row["hard_break"] is False
    assert row["failure_codes"] == []
    assert row["diagnostic_codes"] == []
    assert row["metrics"]["ttft_ms"] == 12.5


def test_smoke_rollup_reports_matrix_break_rates() -> None:
    cases = load_smoke_cases(CASES_PATH)
    plan = build_smoke_plan(
        cases=cases,
        models=("m1", "m2", "m3"),
        chunks=(2048,),
        temperatures=(0.0, 0.3),
        samples_per_family=2,
    )
    rows = [
        record_for_smoke_output(
            cell,
            run_id="smoke",
            created_at_utc=None,
            output="{not json}",
            metrics={},
        )
        for cell in plan
    ]

    rollup = rollup_records(
        rows,
        run_id="smoke",
        phase="smoke",
        expected_sample_count=60,
    )

    assert rollup["schema_version"] == F4_ROLLUP_SCHEMA_VERSION
    assert rollup["sample_count"] == 60
    assert rollup["expected_sample_count"] == 60
    assert rollup["hard_break_count"] == 60
    assert rollup["generation_error_count"] == 0
    assert set(rollup["by_model"]) == {"m1", "m2", "m3"}
    assert set(rollup["by_family"]) == {
        "json_schema_flat",
        "function_call_arguments",
        "nested_object",
        "enum_constrained",
        "thinking_tag_closed",
    }
    assert set(rollup["by_temperature"]) == {"0", "0.3"}
    assert set(rollup["by_chunk_tokens"]) == {"2048"}
    assert rollup["graduates"] == {
        "validator_contract": True,
        "measurement_harness": True,
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


# --- F-4.2b grammar matrix helpers ------------------------------------------


def test_f4_family_grammar_json_schema_families() -> None:
    from scripts.bench.structured_output_invariance import f4_family_grammar

    for family in (
        "json_schema_flat",
        "function_call_arguments",
        "nested_object",
        "enum_constrained",
    ):
        spec = f4_family_grammar(family)
        assert spec is not None
        assert spec["kind"] == "json_schema"
        assert spec["schema"]["type"] == "object"


def test_f4_family_grammar_thinking_tag_is_prompt_only() -> None:
    from scripts.bench.structured_output_invariance import f4_family_grammar

    # The f4_thinking_tag_diagnose probe showed the structural tag BACKFIRES:
    # the trigger does not fire on the model's native <think> channel and the
    # constraint sends generation into a runaway. thinking_tag is therefore run
    # prompt-only (no grammar); a tolerant validator handles the native channel.
    assert f4_family_grammar("thinking_tag_closed") is None


def test_run_generation_cell_passes_grammar_when_enabled() -> None:
    from scripts.bench.structured_output_invariance import _run_generation_cell

    captured: dict = {}

    class _FakeEvent:
        event = "done"
        text = ""
        prompt_tokens = 1
        completion_tokens = 1
        finish_reason = "stop"
        detail: dict = {}

    class _FakeBackend:
        def stream_generate(self, model_id, prompt, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = kwargs
            return iter([_FakeEvent()])

    cell = {
        "model_id": "m",
        "prompt": "p",
        "family": "json_schema_flat",
        "temperature": 0.0,
        "chunk_tokens": 2048,
    }
    _run_generation_cell(
        backend=_FakeBackend(),
        cell=cell,
        max_tokens=8,
        grammar={"kind": "json_schema", "schema": {"type": "object"}},
    )
    assert captured["kwargs"]["grammar"] == {
        "kind": "json_schema",
        "schema": {"type": "object"},
    }


def test_run_generation_cell_omits_grammar_when_none() -> None:
    from scripts.bench.structured_output_invariance import _run_generation_cell

    captured: dict = {}

    class _FakeEvent:
        event = "done"
        text = ""
        prompt_tokens = 1
        completion_tokens = 1
        finish_reason = "stop"
        detail: dict = {}

    class _FakeBackend:
        def stream_generate(self, model_id, prompt, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = kwargs
            return iter([_FakeEvent()])

    cell = {
        "model_id": "m",
        "prompt": "p",
        "family": "json_schema_flat",
        "temperature": 0.0,
        "chunk_tokens": 2048,
    }
    _run_generation_cell(backend=_FakeBackend(), cell=cell, max_tokens=8)
    assert "grammar" not in captured["kwargs"]


# --- F-4.3 narrow-lane family filter ----------------------------------------


def test_filter_cases_by_family_keeps_only_requested() -> None:
    from scripts.bench.structured_output_invariance import _filter_cases_by_family

    cases = [
        {"case_id": "a", "family": "json_schema_flat", "prompt": "p"},
        {"case_id": "b", "family": "enum_constrained", "prompt": "p"},
        {"case_id": "c", "family": "thinking_tag_closed", "prompt": "p"},
    ]
    kept = _filter_cases_by_family(cases, ("json_schema_flat", "enum_constrained"))
    assert [c["case_id"] for c in kept] == ["a", "b"]


def test_filter_cases_by_family_none_keeps_all() -> None:
    from scripts.bench.structured_output_invariance import _filter_cases_by_family

    cases = [
        {"case_id": "a", "family": "json_schema_flat", "prompt": "p"},
        {"case_id": "c", "family": "thinking_tag_closed", "prompt": "p"},
    ]
    assert _filter_cases_by_family(cases, None) == cases


def test_filter_cases_by_family_unknown_family_raises() -> None:
    import pytest as _pytest

    from scripts.bench.structured_output_invariance import _filter_cases_by_family

    with _pytest.raises(ValueError):
        _filter_cases_by_family(
            [{"case_id": "a", "family": "json_schema_flat", "prompt": "p"}],
            ("does_not_exist",),
        )


# --- F-4 residual #2: thinking_tag validator tolerates native reasoning -------


def test_thinking_validator_accepts_native_think_prefix_then_envelope() -> None:
    from scripts.bench.structured_output_invariance import validate_structured_output

    # Reasoning model emits its native <think></think> first, then the requested
    # <thinking>...</thinking>{json}. This is the real Qwen control-arm shape.
    out = (
        "<think>\n\n</think>\n\n"
        '<thinking>processed</thinking>{"final": "ok", "confidence": "high"}'
    )
    result = validate_structured_output(family="thinking_tag_closed", output=out)
    assert result.hard_break is False, result.failure_codes


def test_thinking_validator_accepts_native_think_envelope_then_json() -> None:
    from scripts.bench.structured_output_invariance import validate_structured_output

    # Native closed reasoning envelope IS a closed thinking envelope; trailing
    # JSON should validate without requiring a literal <thinking> tag.
    out = '<think>reasoning here</think>{"final": "done", "confidence": "low"}'
    result = validate_structured_output(family="thinking_tag_closed", output=out)
    assert result.hard_break is False, result.failure_codes


def test_thinking_validator_still_breaks_on_unclosed_reasoning() -> None:
    from scripts.bench.structured_output_invariance import validate_structured_output

    out = '<think>rambling with no close and no json'
    result = validate_structured_output(family="thinking_tag_closed", output=out)
    assert result.hard_break is True


def test_thinking_validator_still_breaks_on_bad_enum_after_envelope() -> None:
    from scripts.bench.structured_output_invariance import validate_structured_output

    out = '<think></think>{"final": "x", "confidence": "certain"}'
    result = validate_structured_output(family="thinking_tag_closed", output=out)
    assert result.hard_break is True


# --- F-4 residual #3: bound gemma in-string / whitespace degeneracy ----------


def _iter_string_props(schema):
    """Yield every {"type":"string"} property subschema (recursive)."""
    if isinstance(schema, dict):
        if schema.get("type") == "string":
            yield schema
        for v in schema.values():
            yield from _iter_string_props(v)
    elif isinstance(schema, list):
        for v in schema:
            yield from _iter_string_props(v)


def test_function_call_and_nested_grammars_bound_string_length() -> None:
    from scripts.bench.structured_output_invariance import f4_family_grammar

    for family in ("function_call_arguments", "nested_object"):
        spec = f4_family_grammar(family)
        # every free-text string field carries a maxLength bound (enum strings
        # are already bounded by their enum, so they are exempt)
        for prop in _iter_string_props(spec["schema"]):
            if "enum" in prop:
                continue
            assert "maxLength" in prop, f"{family} string prop lacks maxLength: {prop}"


def test_nested_grammar_tightens_whitespace_cap() -> None:
    from scripts.bench.structured_output_invariance import f4_family_grammar

    spec = f4_family_grammar("nested_object")
    assert spec.get("max_whitespace_cnt", 16) <= 4
