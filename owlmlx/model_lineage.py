"""owlmlx model lineage schema and truth inheritance rules.

This module owns the runtime truth schema for served model provenance:
what weights are being served, how they were converted, what runtime
validated them, and whether prior verification truth carries over after
a change.

The platform owns catalog storage and endpoint transport. owlmlx owns the
schema, normalization, validation, and pure inheritance derivation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


LINEAGE_REQUIRED_FIELDS: tuple[str, ...] = (
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

RELAXED_LINEAGE_FIELDS: tuple[str, ...] = (
    "conversion_patches",
    "sha256",
    "known_caveats",
)

STRICT_LINEAGE_STATES: tuple[str, ...] = ("stable", "backup")


class LineageChangeType(str, Enum):
    """Change categories that determine verification truth inheritance."""

    same_model_same_runtime_same_quant = "same_model_same_runtime_same_quant"
    runtime_version_bump = "runtime_version_bump"
    different_quant = "different_quant"
    different_conversion_path = "different_conversion_path"
    different_base_model = "different_base_model"
    different_runtime = "different_runtime"


class TruthInheritanceLevel(str, Enum):
    """How much prior verification truth carries over."""

    full = "full"
    most = "most"
    none = "none"


@dataclass(frozen=True, slots=True)
class ModelLineage:
    """Canonical served-model lineage.

    This describes the actual served weights, not just a marketing model
    name. If served weights are converted or quantized, conversion_path and
    quant_method must make that explicit.
    """

    base_model: str
    base_format: str
    quantizer: str
    quant_method: str
    served_format: str
    conversion_path: str
    conversion_patches: tuple[str, ...]
    local_path: str
    file_size_gb: float
    sha256: str | None
    runtime: str
    runtime_version: str
    verified_date: str
    verified_context: int
    known_caveats: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "file_size_gb", max(float(self.file_size_gb or 0.0), 0.0))
        object.__setattr__(self, "verified_context", max(int(self.verified_context or 0), 0))
        object.__setattr__(self, "conversion_patches", _tuple_of_strings(self.conversion_patches))
        object.__setattr__(self, "known_caveats", _tuple_of_strings(self.known_caveats))
        if self.sha256 == "":
            object.__setattr__(self, "sha256", None)


@dataclass(frozen=True, slots=True)
class LineageValidationResult:
    """Pure validation result for a lineage record."""

    valid: bool
    missing_fields: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TruthInheritance:
    """Result of comparing two lineage records."""

    change_type: LineageChangeType
    inheritance_level: TruthInheritanceLevel
    inherited: bool
    must_reverify: tuple[str, ...]


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def normalize_model_lineage(raw: Mapping[str, Any] | ModelLineage) -> ModelLineage:
    """Normalize a raw catalog lineage object into ModelLineage."""
    if isinstance(raw, ModelLineage):
        return raw

    return ModelLineage(
        base_model=str(raw.get("base_model", "")),
        base_format=str(raw.get("base_format", "")),
        quantizer=str(raw.get("quantizer", "")),
        quant_method=str(raw.get("quant_method", "")),
        served_format=str(raw.get("served_format", "")),
        conversion_path=str(raw.get("conversion_path", "")),
        conversion_patches=_tuple_of_strings(raw.get("conversion_patches")),
        local_path=str(raw.get("local_path", "")),
        file_size_gb=float(raw.get("file_size_gb", 0.0) or 0.0),
        sha256=str(raw.get("sha256", "")) or None,
        runtime=str(raw.get("runtime", "")),
        runtime_version=str(raw.get("runtime_version", "")),
        verified_date=str(raw.get("verified_date", "")),
        verified_context=int(raw.get("verified_context", 0) or 0),
        known_caveats=_tuple_of_strings(raw.get("known_caveats")),
    )


def model_lineage_to_dict(lineage: ModelLineage) -> dict[str, Any]:
    """Serialize ModelLineage to a plain dict for platform payloads."""
    return {
        "base_model": lineage.base_model,
        "base_format": lineage.base_format,
        "quantizer": lineage.quantizer,
        "quant_method": lineage.quant_method,
        "served_format": lineage.served_format,
        "conversion_path": lineage.conversion_path,
        "conversion_patches": list(lineage.conversion_patches),
        "local_path": lineage.local_path,
        "file_size_gb": lineage.file_size_gb,
        "sha256": lineage.sha256,
        "runtime": lineage.runtime,
        "runtime_version": lineage.runtime_version,
        "verified_date": lineage.verified_date,
        "verified_context": lineage.verified_context,
        "known_caveats": list(lineage.known_caveats),
    }


def validate_model_lineage(
    raw: Mapping[str, Any] | ModelLineage | None,
    *,
    lifecycle_state: str = "stable",
) -> LineageValidationResult:
    """Validate lineage completeness for a model lifecycle state.

    Stable and backup models require the full schema. Candidate and lower
    states may omit conversion_patches, sha256, and known_caveats.
    """
    if raw is None:
        return LineageValidationResult(
            valid=False,
            missing_fields=LINEAGE_REQUIRED_FIELDS,
            warnings=(),
        )

    data = model_lineage_to_dict(raw) if isinstance(raw, ModelLineage) else dict(raw)
    required = list(LINEAGE_REQUIRED_FIELDS)
    if lifecycle_state not in STRICT_LINEAGE_STATES:
        required = [field for field in required if field not in RELAXED_LINEAGE_FIELDS]

    missing = tuple(field for field in required if field not in data or data.get(field) in (None, ""))
    warnings: list[str] = []

    lineage = normalize_model_lineage(data)
    if lineage.verified_context <= 0:
        warnings.append("verified_context is not positive")
    if lineage.file_size_gb <= 0:
        warnings.append("file_size_gb is not positive")
    if "direct" not in lineage.conversion_path.lower() and not lineage.conversion_path:
        warnings.append("conversion_path is empty")

    return LineageValidationResult(
        valid=not missing,
        missing_fields=missing,
        warnings=tuple(warnings),
    )


def derive_lineage_change_type(
    previous: Mapping[str, Any] | ModelLineage,
    current: Mapping[str, Any] | ModelLineage,
) -> LineageChangeType:
    """Classify lineage change type for truth inheritance."""
    prev = normalize_model_lineage(previous)
    curr = normalize_model_lineage(current)

    if prev.base_model != curr.base_model:
        return LineageChangeType.different_base_model
    if prev.runtime != curr.runtime:
        return LineageChangeType.different_runtime
    if prev.quant_method != curr.quant_method or prev.served_format != curr.served_format:
        return LineageChangeType.different_quant
    if prev.conversion_path != curr.conversion_path or prev.conversion_patches != curr.conversion_patches:
        return LineageChangeType.different_conversion_path
    if prev.runtime_version != curr.runtime_version:
        return LineageChangeType.runtime_version_bump
    return LineageChangeType.same_model_same_runtime_same_quant


def truth_inheritance_for_change(change_type: LineageChangeType | str) -> TruthInheritance:
    """Return inheritance rule for a lineage change type."""
    ct = LineageChangeType(change_type) if isinstance(change_type, str) else change_type

    if ct == LineageChangeType.same_model_same_runtime_same_quant:
        return TruthInheritance(
            change_type=ct,
            inheritance_level=TruthInheritanceLevel.full,
            inherited=True,
            must_reverify=(),
        )
    if ct == LineageChangeType.runtime_version_bump:
        return TruthInheritance(
            change_type=ct,
            inheritance_level=TruthInheritanceLevel.most,
            inherited=True,
            must_reverify=("R1", "R3"),
        )
    if ct == LineageChangeType.different_quant:
        return TruthInheritance(
            change_type=ct,
            inheritance_level=TruthInheritanceLevel.none,
            inherited=False,
            must_reverify=("Q1", "Q2", "Q3"),
        )
    if ct == LineageChangeType.different_runtime:
        return TruthInheritance(
            change_type=ct,
            inheritance_level=TruthInheritanceLevel.none,
            inherited=False,
            must_reverify=("B1", "B2", "B3", "B4"),
        )

    return TruthInheritance(
        change_type=ct,
        inheritance_level=TruthInheritanceLevel.none,
        inherited=False,
        must_reverify=("G1", "G2", "G3", "G4", "G5", "G6", "G7"),
    )


def derive_truth_inheritance(
    previous: Mapping[str, Any] | ModelLineage,
    current: Mapping[str, Any] | ModelLineage,
) -> TruthInheritance:
    """Compare lineage records and return the verification inheritance rule."""
    return truth_inheritance_for_change(derive_lineage_change_type(previous, current))


def lineage_from_artifact_metadata(
    metadata: Mapping[str, Any],
    *,
    runtime: str,
    runtime_version: str,
    local_path: str,
    file_size_gb: float = 0.0,
    verified_context: int = 0,
    verified_date: str = "",
) -> ModelLineage:
    """Build served-model lineage from owlmlx training artifact metadata.

    This is a bridge from training artifacts to serving provenance. LoRA
    and adapter methods retain base_model as the artifact model_id and
    express the adapter transformation in conversion_path.
    """
    method = str(metadata.get("method", ""))
    model_id = str(metadata.get("model_id", ""))
    training_stack = str(metadata.get("training_stack", ""))
    training_stack_version = str(metadata.get("training_stack_version", ""))
    run_id = str(metadata.get("run_id", ""))

    return ModelLineage(
        base_model=model_id,
        base_format=str(metadata.get("base_format", "unknown")),
        quantizer=training_stack,
        quant_method=method,
        served_format=f"{runtime}+{method}" if method else runtime,
        conversion_path=f"training artifact {run_id} via {training_stack} {training_stack_version}".strip(),
        conversion_patches=_tuple_of_strings(metadata.get("conversion_patches")),
        local_path=local_path,
        file_size_gb=file_size_gb,
        sha256=str(metadata.get("sha256", "")) or None,
        runtime=runtime,
        runtime_version=runtime_version,
        verified_date=verified_date,
        verified_context=verified_context,
        known_caveats=_tuple_of_strings(metadata.get("known_caveats")),
    )
