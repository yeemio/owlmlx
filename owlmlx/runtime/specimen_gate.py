"""Runtime-owned large-weight specimen validation gate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re

from .mlx_environment import (
    MlxEnvironmentReadiness,
    build_mlx_environment_readiness,
    readiness_to_dict,
)


@dataclass(frozen=True, slots=True)
class SpecimenPathAssessment:
    """Filesystem truth for a candidate local specimen path."""

    exists: bool
    path: str
    kind: str
    file_count: int
    total_size_bytes: int
    has_config_json: bool
    has_index_json: bool
    shard_count: int
    expected_shard_count: int | None
    aria2_in_progress: bool
    blocked_reason: str | None


@dataclass(frozen=True, slots=True)
class LargeWeightSpecimenGate:
    """Stable readiness gate before large-weight smoke or validation."""

    specimen_path: SpecimenPathAssessment
    mlx_environment: MlxEnvironmentReadiness
    smoke_ready: bool
    blocked_reason: str | None


def assess_specimen_path(path: str) -> SpecimenPathAssessment:
    """Assess whether a local model path is present enough for validation."""

    target = Path(path).expanduser()
    if not target.exists():
        return SpecimenPathAssessment(
            exists=False,
            path=str(target),
            kind="missing",
            file_count=0,
            total_size_bytes=0,
            has_config_json=False,
            has_index_json=False,
            shard_count=0,
            expected_shard_count=None,
            aria2_in_progress=False,
            blocked_reason="specimen path does not exist",
        )

    if target.is_file():
        return SpecimenPathAssessment(
            exists=True,
            path=str(target),
            kind="file",
            file_count=1,
            total_size_bytes=target.stat().st_size,
            has_config_json=target.name == "config.json",
            has_index_json=target.name == "model.safetensors.index.json",
            shard_count=1 if target.suffix == ".safetensors" else 0,
            expected_shard_count=1 if target.suffix == ".safetensors" else None,
            aria2_in_progress=False,
            blocked_reason=None,
        )

    files = [child for child in target.rglob("*") if child.is_file()]
    total_size = sum(child.stat().st_size for child in files)
    has_config_json = (target / "config.json").exists()
    index_json = target / "model.safetensors.index.json"
    has_index_json = index_json.exists()
    shard_files = sorted(target.glob("model-*-of-*.safetensors"))
    expected_shard_count: int | None = None
    if has_index_json:
        try:
            payload = json.loads(index_json.read_text(encoding="utf-8"))
            weight_map = payload.get("weight_map", {})
            if isinstance(weight_map, dict):
                expected_shard_count = len(
                    {value for value in weight_map.values() if isinstance(value, str)}
                )
        except Exception:
            expected_shard_count = None
    if expected_shard_count is None:
        shard_pattern = re.compile(r"model-(\d+)-of-(\d+)\.safetensors$")
        for shard in shard_files:
            match = shard_pattern.match(shard.name)
            if not match:
                continue
            expected_shard_count = int(match.group(2))
            break
    aria2_in_progress = any(child.suffix == ".aria2" for child in files)
    shard_set_complete = (
        expected_shard_count is not None and len(shard_files) >= expected_shard_count
    )
    blocked_reason = None
    if not files:
        blocked_reason = "specimen directory contains no files"
    elif not has_config_json:
        blocked_reason = "specimen directory is missing config.json"
    elif aria2_in_progress and not shard_set_complete:
        blocked_reason = "specimen download still in progress"
    elif expected_shard_count is not None and len(shard_files) < expected_shard_count:
        blocked_reason = "specimen shard set is incomplete"
    return SpecimenPathAssessment(
        exists=True,
        path=str(target),
        kind="directory",
        file_count=len(files),
        total_size_bytes=total_size,
        has_config_json=has_config_json,
        has_index_json=has_index_json,
        shard_count=len(shard_files),
        expected_shard_count=expected_shard_count,
        aria2_in_progress=aria2_in_progress,
        blocked_reason=blocked_reason,
    )


def build_large_weight_specimen_gate(
    *,
    specimen_path: str,
    include_known_candidates: bool = False,
    preferred_execution_mode: str = "default_metal",
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
) -> LargeWeightSpecimenGate:
    """Build the stable pre-smoke gate for a large-weight specimen."""

    path_assessment = assess_specimen_path(specimen_path)
    readiness = build_mlx_environment_readiness(
        include_known_candidates=include_known_candidates,
        preferred_execution_mode=preferred_execution_mode,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    blocked_reason = path_assessment.blocked_reason or readiness.blocked_reason
    return LargeWeightSpecimenGate(
        specimen_path=path_assessment,
        mlx_environment=readiness,
        smoke_ready=blocked_reason is None,
        blocked_reason=blocked_reason,
    )


def specimen_gate_to_dict(gate: LargeWeightSpecimenGate) -> dict[str, object]:
    """Serialize the large-weight specimen gate."""

    return {
        "contract": {
            "surface": "owlmlx.large_weight_specimen_gate",
            "version": "stabilization2",
            "stable_sections": [
                "summary",
                "specimen_path",
                "mlx_environment",
            ],
        },
        "summary": {
            "smoke_ready": gate.smoke_ready,
            "blocked_reason": gate.blocked_reason,
        },
        "specimen_path": {
            "exists": gate.specimen_path.exists,
            "path": gate.specimen_path.path,
            "kind": gate.specimen_path.kind,
            "file_count": gate.specimen_path.file_count,
            "total_size_bytes": gate.specimen_path.total_size_bytes,
            "has_config_json": gate.specimen_path.has_config_json,
            "has_index_json": gate.specimen_path.has_index_json,
            "shard_count": gate.specimen_path.shard_count,
            "expected_shard_count": gate.specimen_path.expected_shard_count,
            "aria2_in_progress": gate.specimen_path.aria2_in_progress,
            "blocked_reason": gate.specimen_path.blocked_reason,
        },
        "mlx_environment": readiness_to_dict(gate.mlx_environment),
    }
