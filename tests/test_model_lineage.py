"""Tests for owlmlx.model_lineage."""

from __future__ import annotations

from owlmlx.model_lineage import (
    LINEAGE_REQUIRED_FIELDS,
    LineageChangeType,
    ModelLineage,
    TruthInheritanceLevel,
    derive_lineage_change_type,
    derive_truth_inheritance,
    lineage_from_artifact_metadata,
    model_lineage_to_dict,
    normalize_model_lineage,
    truth_inheritance_for_change,
    validate_model_lineage,
)
from owlmlx.training import build_artifact_metadata


def _lineage(**overrides):
    data = {
        "base_model": "mlx-community/Qwen3.5-35B-A3B-4bit",
        "base_format": "bf16",
        "quantizer": "mlx-community",
        "quant_method": "mlx-4bit",
        "served_format": "mlx-4bit",
        "conversion_path": "direct download from mlx-community",
        "conversion_patches": [],
        "local_path": "models/Qwen3.5-35B-A3B-4bit",
        "file_size_gb": 19,
        "sha256": "abc123",
        "runtime": "omlx",
        "runtime_version": "omlx 0.3.2",
        "verified_date": "2026-03-20",
        "verified_context": 131072,
        "known_caveats": [],
    }
    data.update(overrides)
    return data


def test_required_fields_match_platform_contract():
    assert LINEAGE_REQUIRED_FIELDS == (
        "base_model",
        "base_format",
        "quantizer",
        "quant_method",
        "served_format",
        "conversion_path",
        "conversion_patches",
        "local_path",
        "file_size_gb",
        "sha256",
        "runtime",
        "runtime_version",
        "verified_date",
        "verified_context",
        "known_caveats",
    )


def test_normalize_model_lineage_from_raw_dict():
    lineage = normalize_model_lineage(_lineage(conversion_patches=["patch"], known_caveats=["slow"]))

    assert isinstance(lineage, ModelLineage)
    assert lineage.base_model == "mlx-community/Qwen3.5-35B-A3B-4bit"
    assert lineage.file_size_gb == 19.0
    assert lineage.verified_context == 131072
    assert lineage.conversion_patches == ("patch",)
    assert lineage.known_caveats == ("slow",)


def test_normalize_model_lineage_passes_through_instance():
    lineage = normalize_model_lineage(_lineage())

    assert normalize_model_lineage(lineage) is lineage


def test_negative_size_and_context_clamp_to_zero():
    lineage = normalize_model_lineage(_lineage(file_size_gb=-10, verified_context=-1))

    assert lineage.file_size_gb == 0.0
    assert lineage.verified_context == 0


def test_empty_sha_becomes_none():
    lineage = normalize_model_lineage(_lineage(sha256=""))

    assert lineage.sha256 is None


def test_model_lineage_to_dict_serializes_tuples_to_lists():
    lineage = normalize_model_lineage(_lineage(conversion_patches=["p"], known_caveats=["c"]))

    data = model_lineage_to_dict(lineage)

    assert data["conversion_patches"] == ["p"]
    assert data["known_caveats"] == ["c"]


def test_validate_stable_requires_full_schema():
    raw = _lineage()
    raw.pop("sha256")

    result = validate_model_lineage(raw, lifecycle_state="stable")

    assert result.valid is False
    assert result.missing_fields == ("sha256",)


def test_validate_candidate_relaxes_patch_sha_caveat_fields():
    raw = _lineage()
    raw.pop("sha256")
    raw.pop("conversion_patches")
    raw.pop("known_caveats")

    result = validate_model_lineage(raw, lifecycle_state="candidate")

    assert result.valid is True
    assert result.missing_fields == ()


def test_validate_none_fails_with_all_required_fields():
    result = validate_model_lineage(None, lifecycle_state="stable")

    assert result.valid is False
    assert result.missing_fields == LINEAGE_REQUIRED_FIELDS


def test_validate_warns_on_non_positive_verified_context():
    result = validate_model_lineage(_lineage(verified_context=0), lifecycle_state="stable")

    assert result.valid is True
    assert "verified_context is not positive" in result.warnings


def test_same_lineage_inherits_all_truth():
    result = derive_truth_inheritance(_lineage(), _lineage())

    assert result.change_type == LineageChangeType.same_model_same_runtime_same_quant
    assert result.inheritance_level == TruthInheritanceLevel.full
    assert result.inherited is True
    assert result.must_reverify == ()


def test_runtime_version_bump_inherits_most_truth():
    result = derive_truth_inheritance(
        _lineage(runtime_version="omlx 0.3.2"),
        _lineage(runtime_version="omlx 0.3.3"),
    )

    assert result.change_type == LineageChangeType.runtime_version_bump
    assert result.inheritance_level == TruthInheritanceLevel.most
    assert result.inherited is True
    assert result.must_reverify == ("R1", "R3")


def test_different_quant_requires_quant_gate():
    result = derive_truth_inheritance(
        _lineage(quant_method="mlx-4bit", served_format="mlx-4bit"),
        _lineage(quant_method="mlx-8bit", served_format="mlx-8bit"),
    )

    assert result.change_type == LineageChangeType.different_quant
    assert result.inheritance_level == TruthInheritanceLevel.none
    assert result.must_reverify == ("Q1", "Q2", "Q3")


def test_same_quant_different_conversion_path_requires_full_gate():
    result = derive_truth_inheritance(
        _lineage(conversion_path="direct download"),
        _lineage(conversion_path="mlx_4bit -> fp16 -> gguf"),
    )

    assert result.change_type == LineageChangeType.different_conversion_path
    assert result.inherited is False
    assert result.must_reverify == ("G1", "G2", "G3", "G4", "G5", "G6", "G7")


def test_different_base_model_requires_full_gate():
    result = derive_truth_inheritance(
        _lineage(base_model="a"),
        _lineage(base_model="b"),
    )

    assert result.change_type == LineageChangeType.different_base_model
    assert result.must_reverify == ("G1", "G2", "G3", "G4", "G5", "G6", "G7")


def test_different_runtime_requires_backup_gate():
    result = derive_truth_inheritance(
        _lineage(runtime="omlx"),
        _lineage(runtime="llama.cpp"),
    )

    assert result.change_type == LineageChangeType.different_runtime
    assert result.must_reverify == ("B1", "B2", "B3", "B4")


def test_truth_inheritance_accepts_raw_change_type_string():
    result = truth_inheritance_for_change("runtime_version_bump")

    assert result.inheritance_level == TruthInheritanceLevel.most


def test_quant_change_takes_precedence_over_conversion_path_change():
    result = derive_lineage_change_type(
        _lineage(quant_method="mlx-4bit", conversion_path="a"),
        _lineage(quant_method="mlx-8bit", conversion_path="b"),
    )

    assert result == LineageChangeType.different_quant


def test_lineage_from_artifact_metadata_bridges_training_to_serving():
    metadata = build_artifact_metadata(
        model_id="gemma-4-31B-it",
        run_id="pilot-lora-20260410-01",
        method="lora",
        training_stack="mlx-lm",
        training_stack_version="0.31.2",
    )

    lineage = lineage_from_artifact_metadata(
        metadata,
        runtime="omlx",
        runtime_version="omlx 0.3.2",
        local_path="models/gemma-4-31B-it/tuned/pilot-lora-20260410-01",
        file_size_gb=0.016,
        verified_context=8192,
        verified_date="2026-04-10",
    )

    assert lineage.base_model == "gemma-4-31B-it"
    assert lineage.quantizer == "mlx-lm"
    assert lineage.quant_method == "lora"
    assert lineage.served_format == "omlx+lora"
    assert "pilot-lora-20260410-01" in lineage.conversion_path


def test_module_has_no_platform_or_transport_dependencies():
    import owlmlx.model_lineage as module

    forbidden = ("ops_dashboard", "llm_router", "httpx", "asyncio", "subprocess", "socket")

    for token in forbidden:
        assert token not in module.__dict__
