from __future__ import annotations

import pytest

from owlmlx.comparative_evidence_record import (
    ComparativeEvidenceMeasurement,
    ComparativeEvidenceRecord,
    ComparativeEvidenceRuntime,
    build_comparative_evidence_record,
    comparative_evidence_record_to_dict,
)
from owlmlx.comparative_evidence_schema import (
    COMPARATIVE_EVIDENCE_RECORD_SURFACE,
    COMPARATIVE_EVIDENCE_RECORD_VERSION,
    SchemaValidationError,
)


def _measurement_kwargs(*, failed: bool) -> dict[str, object]:
    base: dict[str, object] = {
        "throughput_tokens_per_second": 0.0,
        "first_token_latency_ms": 0.0,
        "peak_resident_set_bytes": 0,
        "wall_clock_ms": 0.0,
        "completed_request_count": 0,
        "failure_count": 1 if failed else 0,
    }
    if failed:
        base["failure_causes"] = ["reference_runtime_unavailable"]
    return base


def _runtime(runtime_id: str, *, failed: bool = True) -> ComparativeEvidenceRuntime:
    return ComparativeEvidenceRuntime(
        runtime_id=runtime_id,
        runtime_version="0.0.0-runtime7",
        measurement=ComparativeEvidenceMeasurement(**_measurement_kwargs(failed=failed)),
    )


def _build_kwargs() -> dict[str, object]:
    return {
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
        "runtimes": (_runtime("owlmlx"), _runtime("omlx")),
        "verdict_text": "rejected: reference_runtime_unavailable on host_class=darwin-arm64-m2-16gb",
        "verdict_grade": "rejected",
    }


def test_build_record_returns_validated_dataclass() -> None:
    record = build_comparative_evidence_record(**_build_kwargs())
    assert isinstance(record, ComparativeEvidenceRecord)
    assert record.surface == COMPARATIVE_EVIDENCE_RECORD_SURFACE
    assert record.version == COMPARATIVE_EVIDENCE_RECORD_VERSION
    assert record.workload_class == "single_prompt_short"
    assert record.verdict_grade == "rejected"


def test_to_dict_round_trips_required_fields() -> None:
    record = build_comparative_evidence_record(**_build_kwargs())
    payload = comparative_evidence_record_to_dict(record)
    for required in (
        "surface",
        "version",
        "recorded_at",
        "evidence_pointer",
        "host_class",
        "workload_class",
        "workload_invariants",
        "runtimes",
        "verdict_text",
        "verdict_grade",
    ):
        assert required in payload
    assert payload["surface"] == COMPARATIVE_EVIDENCE_RECORD_SURFACE
    assert payload["version"] == COMPARATIVE_EVIDENCE_RECORD_VERSION
    assert isinstance(payload["runtimes"], list)
    assert payload["runtimes"][0]["runtime_id"] == "owlmlx"
    assert (
        payload["runtimes"][0]["measurement"]["failure_causes"]
        == ["reference_runtime_unavailable"]
    )


def test_build_rejects_invalid_workload_class() -> None:
    kwargs = _build_kwargs()
    kwargs["workload_class"] = "unknown_workload"
    with pytest.raises(SchemaValidationError):
        build_comparative_evidence_record(**kwargs)


def test_build_rejects_invalid_runtime_id() -> None:
    kwargs = _build_kwargs()
    kwargs["runtimes"] = (_runtime("tinyllm"),)  # type: ignore[arg-type]
    with pytest.raises(SchemaValidationError):
        build_comparative_evidence_record(**kwargs)


def test_build_rejects_invalid_verdict_grade() -> None:
    kwargs = _build_kwargs()
    kwargs["verdict_grade"] = "parity"
    with pytest.raises(SchemaValidationError):
        build_comparative_evidence_record(**kwargs)


def test_build_rejects_banned_verdict_vocabulary() -> None:
    kwargs = _build_kwargs()
    kwargs["verdict_text"] = "measured: parity reached"
    kwargs["verdict_grade"] = "measured"
    with pytest.raises(SchemaValidationError):
        build_comparative_evidence_record(**kwargs)


def test_build_rejects_missing_workload_invariant() -> None:
    kwargs = _build_kwargs()
    invariants = dict(kwargs["workload_invariants"])  # type: ignore[arg-type]
    invariants.pop("prompt_set_hash")
    kwargs["workload_invariants"] = invariants
    with pytest.raises(SchemaValidationError):
        build_comparative_evidence_record(**kwargs)


def test_record_module_has_no_owlops_or_platform_imports() -> None:
    from pathlib import Path

    source = (
        Path(__file__).parents[1] / "owlmlx" / "comparative_evidence_record.py"
    ).read_text()
    for forbidden in ("owlops", "owlcoda", "AI/Agent", "llm_router"):
        assert forbidden not in source
