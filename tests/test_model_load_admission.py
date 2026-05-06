from __future__ import annotations

from owlmlx.model_load_admission import (
    build_model_load_admission,
    model_load_admission_to_dict,
)


def _runtime_status(
    *,
    available_gb: float = 80.0,
    host_pressure_classification: str = "normal",
    cooldown_active: bool = False,
    loaded_model_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "budget": {
            "available_gb": available_gb,
            "serving_budget_gb": 116.0,
            "currently_loaded_gb": 36.0,
        },
        "backend": {
            "loaded_models": [
                {"model_id": model_id, "memory_gb": 36.0, "backend": "fake"}
                for model_id in (loaded_model_ids or [])
            ],
            "detail": {
                "dead_registered_models": [],
            },
        },
        "active_model_id": (loaded_model_ids or [None])[0],
        "host_pressure": {
            "available": host_pressure_classification != "unknown",
            "classification": host_pressure_classification,
            "reason_code": "fixture",
        },
        "memory_pressure_cooldown": {
            "active": cooldown_active,
        },
    }


def _visibility_contract(*, visible: bool = True) -> dict[str, object]:
    return {
        "visible_model_ids": ["Qwen3.6-35B-A3B"] if visible else [],
        "entries": [
            {
                "model_id": "Qwen3.6-35B-A3B",
                "visible": visible,
                "block_reason": None if visible else "base_model_config_missing",
            }
        ],
    }


def _record(*, peak_bytes: int | None = 64 * 1024**3) -> dict[str, object]:
    return {
        "model_id": "Qwen3.6-35B-A3B",
        "created_at": "2026-05-05T00:00:00Z",
        "verdict": "needs_optimization",
        "failure_count": 0,
        "peak_resident_set_bytes": peak_bytes,
        "memory_peak_source": "process_tree_rss",
        "owlops_observation_path": "files/evidence/owlmlx/model-release-candidates/test",
    }


def _payload(**kwargs):
    return model_load_admission_to_dict(build_model_load_admission(**kwargs))


def test_model_load_admission_admits_when_visible_peak_fits_and_host_pressure_normal() -> None:
    payload = _payload(
        runtime_status=_runtime_status(available_gb=80.0),
        visibility_contract=_visibility_contract(),
        model_release_candidate_records=[_record(peak_bytes=64 * 1024**3)],
        target_model_id="Qwen3.6-35B-A3B",
        ledger_status="available",
    )

    entry = payload["entries"][0]
    assert payload["surface"] == "owlmlx.model_load_admission"
    assert entry["profile_id"] == "qwen3_6_moe"
    assert entry["admission_decision"] == "admit"
    assert entry["budget_projection"] == "fits"
    assert entry["reason_code"] == "known_peak_fits_current_budget"


def test_model_load_admission_blocks_when_known_peak_exceeds_budget() -> None:
    payload = _payload(
        runtime_status=_runtime_status(available_gb=40.0),
        visibility_contract=_visibility_contract(),
        model_release_candidate_records=[_record(peak_bytes=64 * 1024**3)],
        target_model_id="Qwen3.6-35B-A3B",
    )

    entry = payload["entries"][0]
    assert entry["admission_decision"] == "blocked"
    assert entry["budget_projection"] == "exceeds"
    assert entry["reason_code"] == "known_peak_exceeds_available_budget"


def test_model_load_admission_is_unknown_without_host_pressure_sample() -> None:
    payload = _payload(
        runtime_status=_runtime_status(
            available_gb=80.0,
            host_pressure_classification="unknown",
        ),
        visibility_contract=_visibility_contract(),
        model_release_candidate_records=[_record(peak_bytes=64 * 1024**3)],
        target_model_id="Qwen3.6-35B-A3B",
    )

    entry = payload["entries"][0]
    assert entry["admission_decision"] == "unknown"
    assert entry["budget_projection"] == "fits"
    assert entry["reason_code"] == "host_pressure_sample_missing"


def test_model_load_admission_blocks_on_host_pressure_barrier() -> None:
    payload = _payload(
        runtime_status=_runtime_status(
            available_gb=80.0,
            host_pressure_classification="host_pressure_block",
        ),
        visibility_contract=_visibility_contract(),
        model_release_candidate_records=[_record(peak_bytes=64 * 1024**3)],
        target_model_id="Qwen3.6-35B-A3B",
    )

    entry = payload["entries"][0]
    assert entry["admission_decision"] == "blocked"
    assert entry["reason_code"] == "host_pressure_admission_barrier_active"


def test_model_load_admission_marks_already_loaded_without_new_load() -> None:
    payload = _payload(
        runtime_status=_runtime_status(
            available_gb=10.0,
            loaded_model_ids=["Qwen3.6-35B-A3B"],
        ),
        visibility_contract=_visibility_contract(),
        model_release_candidate_records=[_record(peak_bytes=64 * 1024**3)],
        target_model_id="Qwen3.6-35B-A3B",
    )

    entry = payload["entries"][0]
    assert entry["admission_decision"] == "already_loaded"
    assert entry["budget_projection"] == "already_loaded"


def test_model_load_admission_blocks_invisible_models_before_budget_projection() -> None:
    payload = _payload(
        runtime_status=_runtime_status(available_gb=80.0),
        visibility_contract=_visibility_contract(visible=False),
        model_release_candidate_records=[_record(peak_bytes=64 * 1024**3)],
        target_model_id="Qwen3.6-35B-A3B",
    )

    entry = payload["entries"][0]
    assert entry["admission_decision"] == "blocked"
    assert entry["visibility_status"] == "blocked"
    assert entry["reason_code"] == "model_not_visible"
