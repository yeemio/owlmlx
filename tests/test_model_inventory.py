"""Tests for owlmlx.model_inventory.

The inventory layer is the pure input registry between platform probes and
owlmlx derivation engines. It must not probe anything itself.
"""

from __future__ import annotations

from owlmlx.abort_recovery import SubstrateState
from owlmlx.memory_budget import BudgetVerdict, MachineMemoryProfile
from owlmlx.model_inventory import (
    LoadedModelEntry,
    ModelInventorySnapshot,
    inventory_budget_check,
    inventory_currently_loaded_gb,
    inventory_entry_for_model,
    inventory_health_snapshot,
    inventory_load_state_for_model,
    inventory_model_ids,
    inventory_to_dict,
    inventory_truth_level_for_model,
    normalize_inventory_entry,
    normalize_inventory_snapshot,
)
from owlmlx.runtime_health import InferenceHealth, LoadState, TruthLevel


def test_empty_inventory_defaults_to_unknown_and_zero_memory():
    snapshot = ModelInventorySnapshot(entries=())

    assert inventory_model_ids(snapshot) == ()
    assert inventory_currently_loaded_gb(snapshot) == 0.0
    assert inventory_entry_for_model(snapshot, "missing") is None
    assert inventory_load_state_for_model(snapshot, "missing") == LoadState.unknown
    assert inventory_truth_level_for_model(snapshot, "missing") == TruthLevel.unavailable


def test_single_true_loaded_model_counts_memory():
    snapshot = ModelInventorySnapshot(
        entries=(
            LoadedModelEntry(
                model_id="gemma",
                memory_gb=58.0,
                load_state=LoadState.true_loaded,
                truth_level=TruthLevel.true,
                backend="omlx",
            ),
        )
    )

    assert inventory_model_ids(snapshot) == ("gemma",)
    assert inventory_currently_loaded_gb(snapshot) == 58.0
    assert inventory_load_state_for_model(snapshot, "gemma") == LoadState.true_loaded
    assert inventory_truth_level_for_model(snapshot, "gemma") == TruthLevel.true


def test_inferred_loaded_model_counts_memory():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "qwen",
                    "memory_gb": 19,
                    "load_state": "inferred_loaded",
                    "truth_level": "inferred",
                }
            ]
        }
    )

    assert inventory_currently_loaded_gb(snapshot) == 19.0
    assert inventory_load_state_for_model(snapshot, "qwen") == LoadState.inferred_loaded
    assert inventory_truth_level_for_model(snapshot, "qwen") == TruthLevel.inferred


def test_cold_model_does_not_count_as_loaded_memory():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "cold-model",
                    "memory_gb": 62,
                    "load_state": "cold",
                    "truth_level": "true",
                }
            ]
        }
    )

    assert inventory_currently_loaded_gb(snapshot) == 0.0
    assert inventory_load_state_for_model(snapshot, "cold-model") == LoadState.cold


def test_unavailable_and_unknown_do_not_count_as_loaded_memory():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {"model_id": "down", "memory_gb": 62, "load_state": "unavailable"},
                {"model_id": "unknown", "memory_gb": 20, "load_state": "unknown"},
            ]
        }
    )

    assert inventory_currently_loaded_gb(snapshot) == 0.0


def test_duplicate_model_id_uses_last_wins_for_lookup_and_aggregation():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "same",
                    "memory_gb": 10,
                    "load_state": "true_loaded",
                    "truth_level": "true",
                },
                {
                    "model_id": "same",
                    "memory_gb": 20,
                    "load_state": "cold",
                    "truth_level": "true",
                },
            ]
        }
    )

    assert inventory_model_ids(snapshot) == ("same",)
    assert inventory_entry_for_model(snapshot, "same").memory_gb == 20.0
    assert inventory_load_state_for_model(snapshot, "same") == LoadState.cold
    assert inventory_currently_loaded_gb(snapshot) == 0.0


def test_negative_memory_is_clamped_to_zero():
    entry = normalize_inventory_entry(
        {
            "model_id": "bad-memory",
            "memory_gb": -12,
            "load_state": "true_loaded",
            "truth_level": "true",
        }
    )

    assert entry.memory_gb == 0.0


def test_invalid_states_normalize_to_safe_defaults():
    entry = normalize_inventory_entry(
        {
            "model_id": "bad-state",
            "memory_gb": 12,
            "load_state": "loaded",
            "truth_level": "maybe",
        }
    )

    assert entry.load_state == LoadState.unknown
    assert entry.truth_level == TruthLevel.unavailable


def test_normalize_entry_passes_through_existing_entry():
    entry = LoadedModelEntry(
        model_id="existing",
        memory_gb=1,
        load_state=LoadState.true_loaded,
        truth_level=TruthLevel.true,
    )

    assert normalize_inventory_entry(entry) is entry


def test_normalize_snapshot_passes_through_existing_snapshot():
    snapshot = ModelInventorySnapshot(entries=())

    assert normalize_inventory_snapshot(snapshot) is snapshot


def test_budget_check_uses_inventory_loaded_memory():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "loaded",
                    "memory_gb": 84,
                    "load_state": "true_loaded",
                    "truth_level": "true",
                }
            ]
        }
    )
    profile = MachineMemoryProfile(
        system_memory_gb=128,
        system_reserve_gb=12,
        serving_budget_gb=116,
        warning_threshold_gb=100,
    )

    evaluation = inventory_budget_check(snapshot, requested_model_gb=40, profile=profile)

    assert evaluation.verdict == BudgetVerdict.exceeds
    assert evaluation.currently_loaded_gb == 84.0
    assert evaluation.projected_gb == 124.0


def test_budget_check_allows_fit_with_warning_threshold():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "loaded",
                    "memory_gb": 58,
                    "load_state": "inferred_loaded",
                    "truth_level": "inferred",
                }
            ]
        }
    )
    profile = MachineMemoryProfile(
        system_memory_gb=128,
        system_reserve_gb=12,
        serving_budget_gb=116,
        warning_threshold_gb=100,
    )

    evaluation = inventory_budget_check(snapshot, requested_model_gb=45, profile=profile)

    assert evaluation.verdict == BudgetVerdict.fits_warning
    assert evaluation.currently_loaded_gb == 58.0


def test_inventory_health_snapshot_for_loaded_model():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "ready",
                    "memory_gb": 15,
                    "load_state": "true_loaded",
                    "truth_level": "true",
                }
            ]
        }
    )

    health = inventory_health_snapshot(snapshot, "ready", InferenceHealth.serving)

    assert health["load_state"] == "true_loaded"
    assert health["truth_level"] == "true"
    assert health["readiness"] == "ready"
    assert health["wait_tier"] == "ready_now"
    assert health["is_ready"] is True


def test_inventory_health_snapshot_for_missing_model_is_unknown():
    health = inventory_health_snapshot(
        ModelInventorySnapshot(entries=()),
        "missing",
        InferenceHealth.serving,
    )

    assert health["load_state"] == "unknown"
    assert health["truth_level"] == "unavailable"
    assert health["readiness"] == "unknown"
    assert health["is_ready"] is False


def test_inventory_health_snapshot_respects_substrate_contamination():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "loaded",
                    "memory_gb": 15,
                    "load_state": "true_loaded",
                    "truth_level": "true",
                }
            ]
        }
    )

    health = inventory_health_snapshot(
        snapshot,
        "loaded",
        "serving",
        substrate_state=SubstrateState.contaminated,
    )

    assert health["readiness"] == "blocked"
    assert health["block_reason"] == "substrate contaminated after high-context abort"


def test_inventory_health_snapshot_respects_lab_flag():
    snapshot = normalize_inventory_snapshot(
        {
            "entries": [
                {
                    "model_id": "lab",
                    "memory_gb": 15,
                    "load_state": "true_loaded",
                    "truth_level": "true",
                }
            ]
        }
    )

    health = inventory_health_snapshot(snapshot, "lab", "serving", is_lab=True)

    assert health["wait_tier"] == "background_only"


def test_inventory_to_dict_includes_derived_counts():
    snapshot = normalize_inventory_snapshot(
        {
            "timestamp": 123.0,
            "entries": [
                {
                    "model_id": "a",
                    "memory_gb": 10,
                    "load_state": "true_loaded",
                    "truth_level": "true",
                },
                {
                    "model_id": "b",
                    "memory_gb": 20,
                    "load_state": "cold",
                    "truth_level": "true",
                },
            ],
        }
    )

    data = inventory_to_dict(snapshot)

    assert data["total_loaded_gb"] == 10.0
    assert data["model_count"] == 2
    assert data["loaded_count"] == 1
    assert data["timestamp"] == 123.0
    assert data["entries"][0]["model_id"] == "a"


def test_module_has_no_platform_or_transport_dependencies():
    import owlmlx.model_inventory as module

    forbidden = ("ops_dashboard", "llm_router", "httpx", "asyncio", "subprocess", "socket")

    for token in forbidden:
        assert token not in module.__dict__
