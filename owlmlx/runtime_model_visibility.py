"""owlmlx runtime-owned model visibility contract.

This module defines the owlmlx-owned answer to one narrow question:

    Which local models should appear in owlmlx's stable visibility list for
    downstream consumers such as the old router or OwlCoda?

This contract is intentionally distinct from ``model_inventory.py``:

- ``model_inventory.py`` answers "what is loaded right now?"
- this module answers "what models are registered and visibility-ready?"

The visibility gate is machine-checkable and owlmlx-owned:

1. the model is registered in owlmlx's visibility registry
2. the base model directory exists under ``$MODELS_ROOT/{model_id}/``
3. ``config.json`` exists in that base model directory

This lets owlmlx expose a stable visibility list without pretending that
"currently loaded" and "should be visible" are the same contract.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from owlmlx.model_inventory import ModelInventorySnapshot


RUNTIME_MODEL_VISIBILITY_RULE = "runtime_gate_required_before_visible"
RUNTIME_MODEL_VISIBILITY_CONTRACT_VERSION = "runtime-owned-2"
RUNTIME_MODEL_VISIBILITY_SURFACE = "/v1/openai/models"
RUNTIME_MODEL_VISIBILITY_DETAIL_SURFACE = "/v1/runtime/model-visibility"
RUNTIME_LOADED_INVENTORY_SURFACE = "/v1/models"
RUNTIME_MODEL_VISIBILITY_GATE_KIND = "registered_base_model_config_present"
DEFAULT_MODELS_ROOT = Path("/Users/yeemio/AI/Agent/models")


@dataclass(frozen=True, slots=True)
class RegisteredRuntimeVisibleModel:
    """A model that owlmlx may expose through its visibility contract."""

    model_id: str
    local_dir_name: str | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must be non-empty")

    @property
    def effective_local_dir_name(self) -> str:
        return self.local_dir_name or self.model_id

    def local_model_dir(self, models_root: str | Path) -> Path:
        return Path(models_root) / self.effective_local_dir_name

    def config_path(self, models_root: str | Path) -> Path:
        return self.local_model_dir(models_root) / "config.json"


@dataclass(frozen=True, slots=True)
class RuntimeVisibleModelState:
    """Visibility state for one registered model."""

    model_id: str
    local_model_dir: str
    config_path: str
    local_model_dir_present: bool
    config_present: bool
    visible: bool
    block_reason: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeModelVisibilityGate:
    """Immutable result of the runtime-owned visibility derivation."""

    rule: str
    contract_version: str
    models_root: str
    entries: tuple[RuntimeVisibleModelState, ...]
    visible_model_ids: tuple[str, ...]
    loaded_model_ids: tuple[str, ...]


DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS: tuple[RegisteredRuntimeVisibleModel, ...] = (
    RegisteredRuntimeVisibleModel("Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit"),
    RegisteredRuntimeVisibleModel("Qwen3.5-35B-A3B-4bit"),
    RegisteredRuntimeVisibleModel("Qwen3.6-27B"),
    RegisteredRuntimeVisibleModel("Qwen3.6-35B-A3B"),
    RegisteredRuntimeVisibleModel("gemma-4-31B-it"),
    RegisteredRuntimeVisibleModel("gpt-oss-120b-MXFP4-Q4"),
    RegisteredRuntimeVisibleModel("gpt-oss-20b-MXFP4-Q4"),
    RegisteredRuntimeVisibleModel("Qwen3-Embedding-8B-4bit-DWQ"),
)


def default_models_root() -> Path:
    """Return the canonical models root for owlmlx visibility checks."""

    raw = os.environ.get("OWLMLX_MODELS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser()
    return DEFAULT_MODELS_ROOT


def normalize_registered_runtime_visible_models(
    registry: Iterable[RegisteredRuntimeVisibleModel | dict[str, Any]] | None = None,
) -> tuple[RegisteredRuntimeVisibleModel, ...]:
    """Normalize the registry to stable dataclass entries."""

    raw_registry = (
        DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS
        if registry is None
        else tuple(registry)
    )
    normalized: list[RegisteredRuntimeVisibleModel] = []
    for item in raw_registry:
        if isinstance(item, RegisteredRuntimeVisibleModel):
            normalized.append(item)
            continue
        normalized.append(
            RegisteredRuntimeVisibleModel(
                model_id=str(item.get("model_id", "")),
                local_dir_name=str(item.get("local_dir_name", "") or "") or None,
            )
        )
    return tuple(normalized)


def _loaded_model_ids(snapshot: ModelInventorySnapshot | None) -> tuple[str, ...]:
    if snapshot is None:
        return ()
    return tuple(entry.model_id for entry in snapshot.entries if entry.model_id)


def build_runtime_model_visibility(
    snapshot: ModelInventorySnapshot | None = None,
    *,
    models_root: str | Path | None = None,
    registry: Iterable[RegisteredRuntimeVisibleModel | dict[str, Any]] | None = None,
) -> RuntimeModelVisibilityGate:
    """Derive the owlmlx-owned visibility gate.

    The derivation is independent from loaded inventory. The optional
    snapshot is used only to expose a comparison against the currently
    loaded inventory so consumers do not confuse the two semantics.
    """

    root = Path(models_root) if models_root is not None else default_models_root()
    entries: list[RuntimeVisibleModelState] = []
    visible_model_ids: list[str] = []
    for entry in normalize_registered_runtime_visible_models(registry):
        local_model_dir = entry.local_model_dir(root)
        config_path = entry.config_path(root)
        local_model_dir_present = local_model_dir.is_dir()
        config_present = config_path.is_file()
        visible = local_model_dir_present and config_present
        block_reason = None
        if not local_model_dir_present:
            block_reason = "base_model_directory_missing"
        elif not config_present:
            block_reason = "base_model_config_missing"
        state = RuntimeVisibleModelState(
            model_id=entry.model_id,
            local_model_dir=str(local_model_dir),
            config_path=str(config_path),
            local_model_dir_present=local_model_dir_present,
            config_present=config_present,
            visible=visible,
            block_reason=block_reason,
        )
        entries.append(state)
        if visible:
            visible_model_ids.append(entry.model_id)
    return RuntimeModelVisibilityGate(
        rule=RUNTIME_MODEL_VISIBILITY_RULE,
        contract_version=RUNTIME_MODEL_VISIBILITY_CONTRACT_VERSION,
        models_root=str(root),
        entries=tuple(entries),
        visible_model_ids=tuple(visible_model_ids),
        loaded_model_ids=_loaded_model_ids(snapshot),
    )


def runtime_model_visibility_contract(
    gate: RuntimeModelVisibilityGate,
) -> dict[str, Any]:
    """Return the machine-readable runtime-owned visibility contract."""

    visible_model_ids = list(gate.visible_model_ids)
    blocked_model_ids = [entry.model_id for entry in gate.entries if not entry.visible]
    return {
        "surface": "owlmlx.runtime.model_visibility",
        "contract_version": gate.contract_version,
        "rule": gate.rule,
        "formal_surface": {
            "component": "owlmlx",
            "endpoint": RUNTIME_MODEL_VISIBILITY_SURFACE,
            "shape": "openai.model.list",
            "role": "authoritative",
        },
        "diagnostic_surface": {
            "component": "owlmlx",
            "endpoint": RUNTIME_MODEL_VISIBILITY_DETAIL_SURFACE,
            "shape": "owlmlx.runtime.model_visibility",
            "role": "diagnostic",
        },
        "loaded_inventory_surface": {
            "component": "owlmlx",
            "endpoint": RUNTIME_LOADED_INVENTORY_SURFACE,
            "shape": "owlmlx.runtime.inventory",
            "semantic_role": "currently_loaded_inventory_only",
        },
        "gate": {
            "owner": "owlmlx",
            "kind": RUNTIME_MODEL_VISIBILITY_GATE_KIND,
            "models_root": gate.models_root,
            "required_artifact": "{model-id}/config.json",
        },
        "visible_when": {
            "registered_in_owlmlx_visibility_registry": True,
            "base_model_directory_present": True,
            "base_model_config_present": True,
        },
        "distinct_from_loaded_inventory": {
            "loaded_model_ids": list(gate.loaded_model_ids),
            "reason": (
                "loaded inventory tracks active backend state; visibility tracks "
                "owlmlx-registered local models that are loadable on demand."
            ),
        },
        "distinct_from_platform_rule": {
            "platform_rule": "gate_required_before_visible",
            "platform_surface": {
                "component": "llm_router",
                "endpoint": "/v1/models",
            },
            "reason": (
                "owlmlx visibility no longer depends on router-owned lifecycle "
                "curation or platform gate files; it is derived from owlmlx "
                "registration plus base-model artifact presence."
            ),
        },
        "visible_model_ids": visible_model_ids,
        "blocked_model_ids": blocked_model_ids,
        "model_count": len(visible_model_ids),
        "registered_model_count": len(gate.entries),
        "entries": [
            {
                "model_id": entry.model_id,
                "registered": True,
                "visible": entry.visible,
                "block_reason": entry.block_reason,
                "local_model_dir": entry.local_model_dir,
                "config_path": entry.config_path,
                "local_model_dir_present": entry.local_model_dir_present,
                "config_present": entry.config_present,
            }
            for entry in gate.entries
        ],
    }


def derive_runtime_model_visibility_contract(
    snapshot: ModelInventorySnapshot | None = None,
    *,
    models_root: str | Path | None = None,
    registry: Iterable[RegisteredRuntimeVisibleModel | dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Single-call helper: derive the gate and render the contract."""

    return runtime_model_visibility_contract(
        build_runtime_model_visibility(
            snapshot,
            models_root=models_root,
            registry=registry,
        )
    )

