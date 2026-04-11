"""owlmlx model inventory registry.

Defines immutable data structures and pure derivation helpers for
loaded-model inventory snapshots. This is the fifth module in the
substrate truth family:

1. memory_budget.py        — can this model fit?
2. context_concurrency.py  — how many concurrent requests are safe?
3. abort_recovery.py       — after an abort, is the substrate clean?
4. runtime_health.py       — overall, is the runtime ready to serve?
5. model_inventory.py (this) — what models are loaded and where?

This module closes the dependency gap where owlmlx's derivation engines
(memory_budget, runtime_health) required platform-provided raw inputs
(load_state, currently_loaded_gb, truth_level). With this module, the
platform fills a ModelInventorySnapshot; owlmlx derives everything
downstream.

What this module owns:

- LoadedModelEntry and ModelInventorySnapshot immutable data structures
- Inventory-level memory aggregation (currently_loaded_gb)
- Per-model lookup (load state, truth level, entry)
- Composition with memory_budget.evaluate_model_fit()
- Composition with runtime_health.runtime_health_snapshot()
- Serialization to plain dicts

What this module does NOT own (stays in platform):

- Backend probing (HTTP, socket, tmux, subprocess)
- Backend-specific model ID normalization (vLLM path stripping, etc.)
- Memory heuristic matching (oMLX partial loading combinatorics)
- Router model list discovery
- Catalog reading and management

This module is self-contained. It imports only owlmlx substrate modules
and Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from owlmlx.abort_recovery import SubstrateState
from owlmlx.memory_budget import (
    BudgetEvaluation,
    MachineMemoryProfile,
    default_machine_profile,
    evaluate_model_fit,
)
from owlmlx.runtime_health import (
    InferenceHealth,
    LoadState,
    TruthLevel,
    normalize_inference_health,
    normalize_load_state,
    normalize_truth_level,
    runtime_health_snapshot,
)


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class LoadedModelEntry:
    """A single model's inventory record.

    Immutable snapshot of one model's presence in the runtime.

    Attributes:
        model_id: Canonical model identifier (e.g., "Qwen2.5-72B-4bit").
        memory_gb: Memory footprint of this model in GB.
        load_state: Current load state (true_loaded, inferred_loaded, etc.).
        truth_level: Confidence of the load state assessment.
        backend: Backend serving this model (e.g., "omlx", "vllm").
            None if unknown.
        loaded_at: Timestamp when the model was loaded. None if unknown.
    """

    model_id: str
    memory_gb: float
    load_state: LoadState
    truth_level: TruthLevel
    backend: str | None = None
    loaded_at: float | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must be non-empty")
        object.__setattr__(self, "memory_gb", max(float(self.memory_gb or 0.0), 0.0))
        if isinstance(self.load_state, str):
            object.__setattr__(self, "load_state", normalize_load_state(self.load_state))
        if isinstance(self.truth_level, str):
            object.__setattr__(self, "truth_level", normalize_truth_level(self.truth_level))


@dataclass(frozen=True, slots=True)
class ModelInventorySnapshot:
    """Immutable snapshot of all known model inventory at a point in time.

    The platform fills this from probe results. owlmlx derives budget,
    readiness, and wait-tier truth from it.

    Attributes:
        entries: All model entries in the inventory. Order is preserved
            but has no semantic meaning.
        timestamp: When this snapshot was taken. None if unknown.
    """

    entries: tuple[LoadedModelEntry, ...]
    timestamp: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", _dedupe_last_wins(self.entries))


def _dedupe_last_wins(entries: tuple[LoadedModelEntry, ...]) -> tuple[LoadedModelEntry, ...]:
    """Return entries with duplicate model IDs resolved by last-wins."""
    by_id: dict[str, LoadedModelEntry] = {}
    for entry in entries:
        by_id[entry.model_id] = entry
    return tuple(by_id.values())


# ── Query helpers ─────────────────────────────────────────────────────────────


def inventory_model_ids(snapshot: ModelInventorySnapshot) -> tuple[str, ...]:
    """Return model IDs in the inventory after last-wins de-duplication."""
    return tuple(e.model_id for e in snapshot.entries)


def inventory_entry_for_model(
    snapshot: ModelInventorySnapshot,
    model_id: str,
) -> LoadedModelEntry | None:
    """Look up a model entry by ID. Returns None if not found.

    If duplicate model IDs existed in raw input, ModelInventorySnapshot
    de-duplicates them using last-wins semantics.
    """
    for entry in snapshot.entries:
        if entry.model_id == model_id:
            return entry
    return None


# ── Memory aggregation ────────────────────────────────────────────────────────


def inventory_currently_loaded_gb(snapshot: ModelInventorySnapshot) -> float:
    """Total memory consumed by models in a loaded state.

    Only counts models with load_state in (true_loaded, inferred_loaded).
    Cold, unavailable, and unknown models are excluded.

    Returns:
        Total loaded memory in GB, rounded to 2 decimal places.
    """
    total = 0.0
    for entry in snapshot.entries:
        if entry.load_state in (LoadState.true_loaded, LoadState.inferred_loaded):
            total += entry.memory_gb
    return round(total, 2)


# ── Per-model state lookup ────────────────────────────────────────────────────


def inventory_load_state_for_model(
    snapshot: ModelInventorySnapshot,
    model_id: str,
) -> LoadState:
    """Look up the load state for a specific model.

    Returns LoadState.unknown if the model is not in the inventory.
    """
    entry = inventory_entry_for_model(snapshot, model_id)
    if entry is None:
        return LoadState.unknown
    return entry.load_state


def inventory_truth_level_for_model(
    snapshot: ModelInventorySnapshot,
    model_id: str,
) -> TruthLevel:
    """Look up the truth level for a specific model.

    Returns TruthLevel.unavailable if the model is not in the inventory.
    """
    entry = inventory_entry_for_model(snapshot, model_id)
    if entry is None:
        return TruthLevel.unavailable
    return entry.truth_level


# ── Budget integration ────────────────────────────────────────────────────────


def inventory_budget_check(
    snapshot: ModelInventorySnapshot,
    requested_model_gb: float,
    profile: MachineMemoryProfile | None = None,
) -> BudgetEvaluation:
    """Check whether a new model fits in the memory budget.

    Uses the inventory's currently loaded memory and delegates to
    memory_budget.evaluate_model_fit().

    Args:
        snapshot: Current inventory state.
        requested_model_gb: Memory required by the model to load.
        profile: Machine memory profile. Uses default if None.

    Returns:
        BudgetEvaluation with verdict and projected memory.
    """
    loaded_gb = inventory_currently_loaded_gb(snapshot)
    p = profile if profile is not None else default_machine_profile()
    return evaluate_model_fit(
        requested_gb=requested_model_gb,
        currently_loaded_gb=loaded_gb,
        profile=p,
    )


# ── Runtime health integration ────────────────────────────────────────────────


def inventory_health_snapshot(
    snapshot: ModelInventorySnapshot,
    model_id: str,
    inference_health: InferenceHealth | str,
    substrate_state: SubstrateState | str | None = None,
    is_lab: bool = False,
    budget_feasible: bool | None = None,
) -> dict[str, Any]:
    """Build a runtime health snapshot for a specific model from inventory.

    Looks up the model's load state and truth level from the inventory,
    then delegates to runtime_health.runtime_health_snapshot().

    Args:
        snapshot: Current inventory state.
        model_id: Model to assess.
        inference_health: Backend inference health status.
        substrate_state: Abort recovery substrate state (optional).
        is_lab: Whether the model is lab/background-only.
        budget_feasible: Whether the model fits in memory budget.

    Returns:
        Dict with canonical health fields from runtime_health_snapshot().
        If model is not in inventory, uses LoadState.unknown and
        TruthLevel.unavailable.
    """
    entry = inventory_entry_for_model(snapshot, model_id)
    if entry is not None:
        load_state = entry.load_state
        truth_level = entry.truth_level
        memory_gb = entry.memory_gb
    else:
        load_state = LoadState.unknown
        truth_level = TruthLevel.unavailable
        memory_gb = 0.0

    ih = normalize_inference_health(inference_health) if isinstance(inference_health, str) else inference_health

    return runtime_health_snapshot(
        load_state=load_state,
        inference_health=ih,
        truth_level=truth_level,
        substrate_state=substrate_state,
        memory_gb=memory_gb,
        is_lab=is_lab,
        budget_feasible=budget_feasible,
    )


# ── Serialization ─────────────────────────────────────────────────────────────


def inventory_entry_to_dict(entry: LoadedModelEntry) -> dict[str, Any]:
    """Serialize a LoadedModelEntry to a plain dict."""
    return {
        "model_id": entry.model_id,
        "memory_gb": entry.memory_gb,
        "load_state": entry.load_state.value,
        "truth_level": entry.truth_level.value,
        "backend": entry.backend,
        "loaded_at": entry.loaded_at,
    }


def inventory_to_dict(snapshot: ModelInventorySnapshot) -> dict[str, Any]:
    """Serialize a ModelInventorySnapshot to a plain dict.

    Includes derived fields (total loaded memory, model count).
    """
    return {
        "entries": [inventory_entry_to_dict(e) for e in snapshot.entries],
        "total_loaded_gb": inventory_currently_loaded_gb(snapshot),
        "model_count": len(snapshot.entries),
        "loaded_count": sum(
            1 for e in snapshot.entries
            if e.load_state in (LoadState.true_loaded, LoadState.inferred_loaded)
        ),
        "timestamp": snapshot.timestamp,
    }


# ── Normalization ─────────────────────────────────────────────────────────────


def normalize_inventory_entry(raw: Mapping[str, Any] | LoadedModelEntry) -> LoadedModelEntry:
    """Build a LoadedModelEntry from a raw dict.

    Normalizes load_state and truth_level strings via owlmlx canonical
    normalizers. Missing or invalid values get safe defaults.

    Args:
        raw: Dict with at minimum "model_id" or an existing
            LoadedModelEntry.

    Returns:
        Immutable LoadedModelEntry.

    Raises:
        KeyError: If "model_id" is missing.
    """
    if isinstance(raw, LoadedModelEntry):
        return raw

    model_id = str(raw["model_id"])
    memory_gb = max(float(raw.get("memory_gb", 0.0) or 0.0), 0.0)

    ls_raw = raw.get("load_state", "unknown")
    ls = normalize_load_state(ls_raw) if isinstance(ls_raw, str) else ls_raw

    tl_raw = raw.get("truth_level", "unavailable")
    tl = normalize_truth_level(tl_raw) if isinstance(tl_raw, str) else tl_raw

    return LoadedModelEntry(
        model_id=model_id,
        memory_gb=memory_gb,
        load_state=ls,
        truth_level=tl,
        backend=raw.get("backend"),
        loaded_at=raw.get("loaded_at"),
    )


def normalize_inventory_snapshot(
    raw: Mapping[str, Any] | ModelInventorySnapshot,
) -> ModelInventorySnapshot:
    """Build a ModelInventorySnapshot from a raw dict or pass through.

    If already a ModelInventorySnapshot, returns it unchanged.

    Args:
        raw: Dict with "entries" list of raw entry dicts, or an existing
            ModelInventorySnapshot.

    Returns:
        Immutable ModelInventorySnapshot.
    """
    if isinstance(raw, ModelInventorySnapshot):
        return raw
    entries = tuple(normalize_inventory_entry(e) for e in raw.get("entries", []))
    return ModelInventorySnapshot(
        entries=entries,
        timestamp=raw.get("timestamp"),
    )
