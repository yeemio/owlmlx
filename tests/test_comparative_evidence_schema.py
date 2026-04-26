from __future__ import annotations

import pytest

from owlmlx.comparative_evidence_schema import (
    BANNED_VERDICT_VOCABULARY,
    COMPARATIVE_EVIDENCE_RECORD_HISTORY_SURFACE,
    COMPARATIVE_EVIDENCE_RECORD_SURFACE,
    COMPARATIVE_EVIDENCE_RECORD_VERSION,
    REQUIRED_MEASUREMENT_FIELDS,
    REQUIRED_RECORD_FIELDS,
    REQUIRED_RUNTIME_FIELDS,
    REQUIRED_WORKLOAD_INVARIANT_KEYS,
    RUNTIME_IDS,
    VERDICT_GRADES,
    WORKLOAD_CLASSES,
    SchemaValidationError,
    validate_comparative_evidence_record,
    verdict_text_uses_banned_vocabulary,
)


def _good_record() -> dict[str, object]:
    return {
        "surface": COMPARATIVE_EVIDENCE_RECORD_SURFACE,
        "version": COMPARATIVE_EVIDENCE_RECORD_VERSION,
        "recorded_at": "2026-04-26T00:00:00Z",
        "evidence_pointer": "docs/source-of-truth/comparative-evidence-ledger.md#row-1",
        "host_class": "darwin-arm64-m2-16gb",
        "workload_class": "single_prompt_short",
        "workload_invariants": {
            "model_id": "qwen3-0.6b",
            "model_quantization": "q4",
            "decode_max_tokens": 16,
            "decode_temperature": 0.0,
            "prompt_set_hash": "sha256:abc",
            "serving_budget_bytes": 6 * 1024 * 1024 * 1024,
        },
        "runtimes": [
            {
                "runtime_id": "owlmlx",
                "runtime_version": "0.0.0-runtime7",
                "measurement": {
                    "throughput_tokens_per_second": 0.0,
                    "first_token_latency_ms": 0.0,
                    "peak_resident_set_bytes": 0,
                    "wall_clock_ms": 0.0,
                    "completed_request_count": 0,
                    "failure_count": 1,
                    "failure_causes": ["reference_runtime_unavailable"],
                },
            },
        ],
        "verdict_text": "rejected: reference_runtime_unavailable on host_class=darwin-arm64-m2-16gb",
        "verdict_grade": "rejected",
    }


def test_surface_and_version_are_frozen() -> None:
    assert COMPARATIVE_EVIDENCE_RECORD_SURFACE == "owlmlx.comparative_evidence_record"
    assert COMPARATIVE_EVIDENCE_RECORD_HISTORY_SURFACE == (
        "owlmlx.comparative_evidence_record_history"
    )
    assert COMPARATIVE_EVIDENCE_RECORD_VERSION == "v1"


def test_workload_class_enum_matches_schema_stub() -> None:
    assert set(WORKLOAD_CLASSES) == {
        "single_prompt_short",
        "single_prompt_long",
        "multi_prompt_serial",
        "multi_prompt_aggregated",
    }


def test_runtime_id_enum_matches_schema_stub() -> None:
    assert set(RUNTIME_IDS) == {"owlmlx", "omlx", "vmlx"}


def test_verdict_grade_enum_is_exactly_three_values() -> None:
    assert set(VERDICT_GRADES) == {"measured", "inconclusive", "rejected"}


def test_required_workload_invariant_keys_match_schema_stub() -> None:
    assert set(REQUIRED_WORKLOAD_INVARIANT_KEYS) == {
        "model_id",
        "model_quantization",
        "decode_max_tokens",
        "decode_temperature",
        "prompt_set_hash",
        "serving_budget_bytes",
    }


def test_required_measurement_fields_match_schema_stub() -> None:
    assert set(REQUIRED_MEASUREMENT_FIELDS) == {
        "throughput_tokens_per_second",
        "first_token_latency_ms",
        "peak_resident_set_bytes",
        "wall_clock_ms",
        "completed_request_count",
        "failure_count",
    }


def test_banned_verdict_vocabulary_includes_all_phrases() -> None:
    assert {
        "parity",
        "equivalent",
        "replaces",
        "replacement",
        "production-ready",
        "production_ready",
        "superior",
        "wins",
        "beats",
        "matches",
    } <= set(BANNED_VERDICT_VOCABULARY)


def test_validate_accepts_good_record() -> None:
    validate_comparative_evidence_record(_good_record())


def test_validate_rejects_unknown_workload_class() -> None:
    record = _good_record()
    record["workload_class"] = "unknown_workload"
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "workload_class" in str(exc_info.value)


def test_validate_rejects_unknown_runtime_id() -> None:
    record = _good_record()
    record["runtimes"][0]["runtime_id"] = "tinyllm"
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "runtime_id" in str(exc_info.value)


def test_validate_rejects_invalid_verdict_grade() -> None:
    record = _good_record()
    record["verdict_grade"] = "parity"
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "verdict_grade" in str(exc_info.value)


def test_validate_rejects_missing_required_top_level_field() -> None:
    record = _good_record()
    del record["host_class"]
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "host_class" in str(exc_info.value)


def test_validate_rejects_missing_required_workload_invariant_key() -> None:
    record = _good_record()
    del record["workload_invariants"]["prompt_set_hash"]
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "prompt_set_hash" in str(exc_info.value)


def test_validate_rejects_missing_required_measurement_field() -> None:
    record = _good_record()
    del record["runtimes"][0]["measurement"]["wall_clock_ms"]
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "wall_clock_ms" in str(exc_info.value)


def test_validate_rejects_failure_causes_missing_when_failure_count_positive() -> None:
    record = _good_record()
    del record["runtimes"][0]["measurement"]["failure_causes"]
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "failure_causes" in str(exc_info.value)


def test_verdict_text_banned_vocabulary_detector() -> None:
    assert verdict_text_uses_banned_vocabulary("rejected: ok") is False
    assert verdict_text_uses_banned_vocabulary("measured: parity reached") is True
    assert verdict_text_uses_banned_vocabulary("measured: equivalent on hostX") is True
    assert verdict_text_uses_banned_vocabulary("rejected: production-ready missing") is True


def test_validate_rejects_record_with_banned_verdict_vocabulary() -> None:
    record = _good_record()
    record["verdict_text"] = "measured: parity reached on host_class=foo"
    record["verdict_grade"] = "measured"
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "banned" in str(exc_info.value).lower()


def test_validate_rejects_runtimes_list_empty() -> None:
    record = _good_record()
    record["runtimes"] = []
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_comparative_evidence_record(record)
    assert "runtimes" in str(exc_info.value)


def test_required_field_sets_have_no_owlops_or_platform_imports_in_schema() -> None:
    from pathlib import Path

    source = (
        Path(__file__).parents[1] / "owlmlx" / "comparative_evidence_schema.py"
    ).read_text()
    for forbidden in ("owlops", "owlcoda", "AI/Agent", "llm_router"):
        assert forbidden not in source
    assert REQUIRED_RECORD_FIELDS  # non-empty
    assert REQUIRED_RUNTIME_FIELDS  # non-empty
