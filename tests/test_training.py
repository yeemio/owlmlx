"""Tests for owlmlx training artifact registration."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from owlmlx.training import (
    ARTIFACT_METADATA_VERSION,
    ARTIFACT_STATUSES,
    SERVING_FEASIBILITY_VALUES,
    TRAINING_METHODS,
    build_artifact_metadata,
    discover_artifacts,
    read_artifact_metadata,
    validate_artifact_for_serving,
    write_artifact_metadata,
)


@pytest.fixture
def models_root(tmp_path):
    """Create a temporary models root with a fake base model."""
    model_dir = tmp_path / "gemma-4-31B-it"
    model_dir.mkdir()
    (model_dir / "config.json").write_text('{"model_type": "gemma4"}')
    return tmp_path


class TestBuildArtifactMetadata:
    def test_basic_lora_metadata(self):
        meta = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="premise-lora-20260410-01",
            method="lora",
            training_stack_version="0.31.2",
            trainable_params=4090000,
            total_params=30697000000,
            final_loss=6.1,
            training_steps=5,
        )
        assert meta["owlmlx_artifact_version"] == ARTIFACT_METADATA_VERSION
        assert meta["model_id"] == "gemma-4-31B-it"
        assert meta["run_id"] == "premise-lora-20260410-01"
        assert meta["method"] == "lora"
        assert meta["adapter_path"] == "adapters.safetensors"
        assert meta["status"] == "completed"
        assert meta["serving_feasibility"] == "pending"
        assert meta["inference_delta_verified"] is False

    def test_full_finetune_has_no_adapter_path(self):
        meta = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="general-full-20260410-01",
            method="full",
        )
        assert "adapter_path" not in meta

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Invalid training method"):
            build_artifact_metadata(
                model_id="test", run_id="test", method="invalid"
            )

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            build_artifact_metadata(
                model_id="test", run_id="test", method="lora", status="bogus"
            )

    def test_lora_config_included(self):
        lora_cfg = {"rank": 8, "alpha": 16, "num_layers": 4}
        meta = build_artifact_metadata(
            model_id="test",
            run_id="test-lora-20260410-01",
            method="lora",
            lora_config=lora_cfg,
        )
        assert meta["lora_config"] == lora_cfg

    def test_extra_fields_merged(self):
        meta = build_artifact_metadata(
            model_id="test",
            run_id="test-lora-20260410-01",
            method="lora",
            task_head="premise",
            dataset_description="test data",
        )
        assert meta["task_head"] == "premise"
        assert meta["dataset_description"] == "test data"

    def test_created_at_is_iso_timestamp(self):
        meta = build_artifact_metadata(
            model_id="test", run_id="test", method="lora"
        )
        assert "T" in meta["created_at"]
        assert "+" in meta["created_at"] or "Z" in meta["created_at"]


class TestWriteAndReadMetadata:
    def test_write_creates_directory_structure(self, models_root):
        meta = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="test-lora-20260410-01",
            method="lora",
        )
        path = write_artifact_metadata(
            models_root, "gemma-4-31B-it", "test-lora-20260410-01", meta
        )
        assert path.exists()
        assert path.name == "metadata.json"
        assert "tuned" in str(path)

    def test_read_returns_written_metadata(self, models_root):
        meta = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="test-lora-20260410-01",
            method="lora",
            final_loss=6.1,
        )
        write_artifact_metadata(
            models_root, "gemma-4-31B-it", "test-lora-20260410-01", meta
        )
        read_back = read_artifact_metadata(
            models_root, "gemma-4-31B-it", "test-lora-20260410-01"
        )
        assert read_back["final_loss"] == 6.1
        assert read_back["method"] == "lora"

    def test_read_nonexistent_returns_none(self, models_root):
        result = read_artifact_metadata(
            models_root, "gemma-4-31B-it", "nonexistent-run"
        )
        assert result is None


class TestDiscoverArtifacts:
    def test_discover_empty(self, models_root):
        artifacts = discover_artifacts(models_root, "gemma-4-31B-it")
        assert artifacts == []

    def test_discover_finds_artifacts(self, models_root):
        for i in range(3):
            meta = build_artifact_metadata(
                model_id="gemma-4-31B-it",
                run_id=f"test-lora-20260410-0{i+1}",
                method="lora",
            )
            write_artifact_metadata(
                models_root, "gemma-4-31B-it", f"test-lora-20260410-0{i+1}", meta
            )
        artifacts = discover_artifacts(models_root, "gemma-4-31B-it")
        assert len(artifacts) == 3

    def test_discover_filters_by_status(self, models_root):
        meta1 = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="run-01",
            method="lora",
            status="completed",
        )
        meta2 = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="run-02",
            method="lora",
            status="failed",
        )
        write_artifact_metadata(models_root, "gemma-4-31B-it", "run-01", meta1)
        write_artifact_metadata(models_root, "gemma-4-31B-it", "run-02", meta2)

        completed = discover_artifacts(
            models_root, "gemma-4-31B-it", status_filter="completed"
        )
        assert len(completed) == 1
        assert completed[0]["run_id"] == "run-01"


class TestValidateForServing:
    def test_no_metadata_fails(self, models_root):
        ok, reason = validate_artifact_for_serving(
            models_root, "gemma-4-31B-it", "nonexistent"
        )
        assert not ok
        assert "not found" in reason

    def test_training_status_fails(self, models_root):
        meta = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="run-01",
            method="lora",
            status="training",
        )
        write_artifact_metadata(models_root, "gemma-4-31B-it", "run-01", meta)
        ok, reason = validate_artifact_for_serving(
            models_root, "gemma-4-31B-it", "run-01"
        )
        assert not ok
        assert "training" in reason

    def test_missing_adapter_file_fails(self, models_root):
        meta = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="run-01",
            method="lora",
            status="completed",
        )
        write_artifact_metadata(models_root, "gemma-4-31B-it", "run-01", meta)
        ok, reason = validate_artifact_for_serving(
            models_root, "gemma-4-31B-it", "run-01"
        )
        assert not ok
        assert "adapter" in reason

    def test_valid_artifact_passes(self, models_root):
        meta = build_artifact_metadata(
            model_id="gemma-4-31B-it",
            run_id="run-01",
            method="lora",
            status="completed",
        )
        write_artifact_metadata(models_root, "gemma-4-31B-it", "run-01", meta)
        # Create fake adapter file
        artifact_dir = models_root / "gemma-4-31B-it" / "tuned" / "run-01"
        (artifact_dir / "adapters.safetensors").write_bytes(b"fake")

        ok, reason = validate_artifact_for_serving(
            models_root, "gemma-4-31B-it", "run-01"
        )
        assert ok
        assert "passed" in reason
