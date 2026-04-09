"""Runtime status schema validation for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

SUPPORTED = "supported"
PARTIAL = "partial"
BEST_EFFORT = "best_effort"
MANUAL_ONLY = "manual_only"
BLOCKED = "blocked"
UNSUPPORTED = "unsupported"

ALLOWED_CAPABILITY_LABELS = {
    SUPPORTED,
    PARTIAL,
    BEST_EFFORT,
    MANUAL_ONLY,
    BLOCKED,
    UNSUPPORTED,
}

CORE_REQUIRED_FIELDS = {
    "runtime",
    "status",
    "load_state",
    "memory_active",
    "memory_budget_gb",
    "model_memory_utilization",
    "queue_state",
    "truth_level",
}

LARGE_WEIGHT_REQUIRED_FIELDS = {
    "runtime",
    "path_variant",
    "status",
    "model",
    "tier",
    "interactive_status",
    "lifecycle_mode",
    "memory_active",
    "memory_budget_gb",
}


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    inferred_kind: str = "core"


def _missing_fields(data: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in data)


def _validate_capability_labels(data: dict[str, Any], errors: list[str]) -> None:
    label = data.get("capability_label")
    if label is not None and label not in ALLOWED_CAPABILITY_LABELS:
        errors.append(f"invalid capability_label: {label}")

    labels = data.get("capability_labels")
    if labels is None:
        return
    if not isinstance(labels, dict):
        errors.append("capability_labels must be a dict")
        return
    for key, value in labels.items():
        if value not in ALLOWED_CAPABILITY_LABELS:
            errors.append(f"invalid capability_labels[{key!r}]: {value}")


def _detect_kind(data: dict[str, Any], kind: str | None) -> str:
    if kind in {"core", "large_weight"}:
        return kind
    if "path_variant" in data or "interactive_status" in data or data.get("tier") == "background":
        return "large_weight"
    return "core"


def normalize_core_runtime_status(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a shell-hosted core runtime payload into owlmlx field language."""
    queue_state = data.get("queue_state")
    if not isinstance(queue_state, dict):
        queue_state = {
            "active": data.get("active_requests", 0),
            "waiting": data.get("waiting_requests", 0),
        }

    normalized = dict(data)
    normalized.setdefault("runtime", "omlx")
    normalized.setdefault("status", "ok")
    normalized.setdefault("load_state", "loaded" if data.get("models_loaded", 0) else "idle")
    normalized.setdefault("memory_active", data.get("model_memory_used_formatted"))
    normalized.setdefault("memory_budget_gb", _parse_gb_value(data.get("model_memory_max_formatted")))
    normalized.setdefault("model_memory_utilization", _infer_model_memory_utilization(data, normalized))
    normalized.setdefault("queue_state", queue_state)
    normalized.setdefault("truth_level", "direct")
    return normalized


def normalize_large_weight_runtime_status(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a shell-hosted large-weight path payload into owlmlx field language."""
    normalized = dict(data)
    normalized.setdefault("runtime", "kimi-sharded")
    normalized.setdefault("path_variant", "expert-sharded")
    normalized.setdefault("status", "ok")
    normalized.setdefault("tier", "background")
    normalized.setdefault("interactive_status", "background_only")
    normalized.setdefault("lifecycle_mode", "manual_start")
    return normalized


def _parse_gb_value(value: Any) -> int | None:
    if not isinstance(value, str) or not value.endswith("GB"):
        return None
    try:
        return int(round(float(value[:-2])))
    except ValueError:
        return None


def _infer_model_memory_utilization(data: dict[str, Any], normalized: dict[str, Any]) -> float | None:
    existing = data.get("model_memory_utilization")
    if isinstance(existing, (int, float)):
        return round(float(existing), 3)
    used = data.get("model_memory_used")
    max_mem = data.get("model_memory_max")
    if isinstance(used, (int, float)) and isinstance(max_mem, (int, float)) and max_mem:
        return round(float(used) / float(max_mem), 3)
    used_gb = _parse_gb_value(data.get("model_memory_used_formatted")) or _parse_gb_value(normalized.get("memory_active"))
    max_gb = _parse_gb_value(data.get("model_memory_max_formatted"))
    if isinstance(used_gb, int) and isinstance(max_gb, int) and max_gb:
        return round(used_gb / max_gb, 3)
    return None


def default_owlmlx_repo() -> Path:
    env = os.environ.get("OWLMLX_REPO")
    if env:
        return Path(env).expanduser()
    return Path.home() / "AI" / "gitrep" / "owlmlx"


def validate_runtime_status(data: dict[str, Any], kind: str | None = None) -> ValidationResult:
    """Validate a runtime status payload against owlmlx schema expectations."""
    if not isinstance(data, dict):
        return ValidationResult(valid=False, errors=["status payload must be a dict"])

    inferred_kind = _detect_kind(data, kind)
    required = LARGE_WEIGHT_REQUIRED_FIELDS if inferred_kind == "large_weight" else CORE_REQUIRED_FIELDS
    errors: list[str] = []

    missing = _missing_fields(data, required)
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))

    _validate_capability_labels(data, errors)

    if inferred_kind == "large_weight":
        if "load_state" in data:
            errors.append("large_weight status should use lifecycle/interactive posture instead of core load_state")
    else:
        if "path_variant" in data:
            errors.append("core status must not include path_variant without large_weight kind")

    return ValidationResult(valid=not errors, errors=errors, inferred_kind=inferred_kind)
