"""owlmlx training artifact registration.

Provides helpers to create, validate, and discover trained model artifacts
following the artifact-layout-contract.md and training-to-serving-contract.md.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# Artifact metadata schema version
ARTIFACT_METADATA_VERSION = "1"

# Valid artifact status values (lifecycle order)
ARTIFACT_STATUSES = (
    "training",
    "completed",
    "verified",
    "serving",
    "superseded",
    "failed",
)

# Valid training methods
TRAINING_METHODS = ("lora", "dora", "qlora", "full")

# Valid serving feasibility values
SERVING_FEASIBILITY_VALUES = ("pending", "pass", "fail")


def build_artifact_metadata(
    model_id: str,
    run_id: str,
    method: str,
    training_stack: str = "mlx-lm",
    training_stack_version: str = "",
    status: str = "completed",
    trainable_params: int = 0,
    total_params: int = 0,
    peak_memory_gb: float = 0.0,
    training_tokens_per_sec: float = 0.0,
    final_loss: float = 0.0,
    training_steps: int = 0,
    lora_config: Optional[dict[str, Any]] = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build artifact metadata dict per artifact-layout-contract.md section 6.

    Returns a dict suitable for writing as metadata.json.
    """
    if method not in TRAINING_METHODS:
        raise ValueError(
            f"Invalid training method '{method}'. Must be one of: {TRAINING_METHODS}"
        )
    if status not in ARTIFACT_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {ARTIFACT_STATUSES}"
        )

    adapter_path = "adapters.safetensors" if method != "full" else None

    metadata: dict[str, Any] = {
        "owlmlx_artifact_version": ARTIFACT_METADATA_VERSION,
        "model_id": model_id,
        "run_id": run_id,
        "method": method,
        "base_model_path": "../..",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_stack": training_stack,
        "training_stack_version": training_stack_version,
        "status": status,
        "trainable_params": trainable_params,
        "total_params": total_params,
        "peak_memory_gb": peak_memory_gb,
        "training_tokens_per_sec": training_tokens_per_sec,
        "final_loss": final_loss,
        "training_steps": training_steps,
    }

    if adapter_path:
        metadata["adapter_path"] = adapter_path

    if lora_config:
        metadata["lora_config"] = lora_config

    # Defaults for optional fields
    metadata["serving_feasibility"] = "pending"
    metadata["serving_feasibility_note"] = ""
    metadata["inference_delta_verified"] = False

    # Merge any extra fields
    for key, value in extra.items():
        if key not in metadata:
            metadata[key] = value

    return metadata


def write_artifact_metadata(
    models_root: str | Path,
    model_id: str,
    run_id: str,
    metadata: dict[str, Any],
) -> Path:
    """Write metadata.json to the correct artifact directory.

    Creates the directory structure if it doesn't exist.
    Returns the path to the written metadata.json.
    """
    artifact_dir = Path(models_root) / model_id / "tuned" / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = artifact_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return metadata_path


def read_artifact_metadata(
    models_root: str | Path,
    model_id: str,
    run_id: str,
) -> Optional[dict[str, Any]]:
    """Read metadata.json for a specific artifact.

    Returns None if the file doesn't exist.
    """
    metadata_path = Path(models_root) / model_id / "tuned" / run_id / "metadata.json"
    if not metadata_path.exists():
        return None

    with open(metadata_path) as f:
        return json.load(f)


def discover_artifacts(
    models_root: str | Path,
    model_id: str,
    status_filter: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Discover all registered artifacts for a model.

    Scans $MODELS_ROOT/{model_id}/tuned/*/metadata.json.
    Optionally filters by status.
    Returns list of metadata dicts, sorted by created_at descending.
    """
    tuned_dir = Path(models_root) / model_id / "tuned"
    if not tuned_dir.exists():
        return []

    artifacts = []
    for run_dir in tuned_dir.iterdir():
        if not run_dir.is_dir():
            continue
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
            if status_filter and metadata.get("status") != status_filter:
                continue
            artifacts.append(metadata)
        except (json.JSONDecodeError, OSError):
            continue

    artifacts.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return artifacts


def validate_artifact_for_serving(
    models_root: str | Path,
    model_id: str,
    run_id: str,
) -> tuple[bool, str]:
    """Check if an artifact passes the serving feasibility checklist.

    Returns (feasible, reason).
    Per training-to-serving-contract.md section 4.1.
    """
    metadata = read_artifact_metadata(models_root, model_id, run_id)

    if metadata is None:
        return False, "metadata.json not found"

    status = metadata.get("status", "")
    if status not in ("completed", "verified", "serving"):
        return False, f"artifact status is '{status}', must be >= completed"

    # Check adapter/model files exist
    artifact_dir = Path(models_root) / model_id / "tuned" / run_id
    method = metadata.get("method", "")

    if method in ("lora", "dora", "qlora"):
        adapter_path = artifact_dir / metadata.get("adapter_path", "adapters.safetensors")
        if not adapter_path.exists():
            return False, f"adapter file not found: {adapter_path}"
    elif method == "full":
        # Full fine-tune needs config.json at minimum
        if not (artifact_dir / "config.json").exists():
            return False, "full fine-tune config.json not found"

    # Check base model exists (for LoRA methods)
    if method in ("lora", "dora", "qlora"):
        base_model_dir = Path(models_root) / model_id
        if not (base_model_dir / "config.json").exists():
            return False, f"base model config.json not found at {base_model_dir}"

    return True, "all checks passed"
