from owlmlx.runtime_status import (
    BLOCKED,
    PARTIAL,
    SUPPORTED,
    normalize_core_runtime_status,
    normalize_large_weight_runtime_status,
    validate_runtime_status,
)


def test_validate_core_runtime_status_passes() -> None:
    result = validate_runtime_status(
        {
            "runtime": "owlmlx-core",
            "status": "ok",
            "load_state": "loaded",
            "memory_active": "24.0GB",
            "memory_budget_gb": 64,
            "model_memory_utilization": 0.37,
            "queue_state": {"active": 0, "waiting": 0},
            "truth_level": "direct",
            "capability_labels": {"runtime_truth": SUPPORTED, "cache_truth": PARTIAL},
        }
    )
    assert result.valid is True
    assert result.errors == []
    assert result.inferred_kind == "core"


def test_validate_missing_required_field_fails() -> None:
    result = validate_runtime_status(
        {
            "runtime": "owlmlx-core",
            "status": "ok",
            "memory_active": "24.0GB",
            "memory_budget_gb": 64,
            "model_memory_utilization": 0.37,
            "queue_state": {"active": 0, "waiting": 0},
            "truth_level": "direct",
        }
    )
    assert result.valid is False
    assert any("load_state" in error for error in result.errors)


def test_invalid_capability_label_fails() -> None:
    result = validate_runtime_status(
        {
            "runtime": "owlmlx-core",
            "status": "ok",
            "load_state": "loaded",
            "memory_active": "24.0GB",
            "memory_budget_gb": 64,
            "model_memory_utilization": 0.37,
            "queue_state": {"active": 0, "waiting": 0},
            "truth_level": "direct",
            "capability_label": "ready-ish",
        }
    )
    assert result.valid is False
    assert any("invalid capability_label" in error for error in result.errors)


def test_large_weight_runtime_status_passes() -> None:
    result = validate_runtime_status(
        {
            "runtime": "kimi-sharded",
            "path_variant": "expert-sharded",
            "status": "ok",
            "model": "Kimi-K2.5-3bit",
            "tier": "background",
            "interactive_status": "background_only",
            "lifecycle_mode": "manual_start",
            "memory_active": "52.3GB",
            "memory_budget_gb": 55,
            "capability_labels": {"resume": BLOCKED, "path_status": SUPPORTED},
        }
    )
    assert result.valid is True
    assert result.inferred_kind == "large_weight"


def test_normalize_core_runtime_status_adds_required_fields() -> None:
    normalized = normalize_core_runtime_status(
        {
            "models_loaded": 2,
            "active_requests": 0,
            "waiting_requests": 1,
            "model_memory_used_formatted": "34.74GB",
            "model_memory_max_formatted": "108.00GB",
            "model_memory_utilization": 0.322,
        }
    )
    result = validate_runtime_status(normalized, kind="core")
    assert result.valid is True
    assert normalized["runtime"] == "omlx"
    assert normalized["load_state"] == "loaded"
    assert normalized["memory_budget_gb"] == 108
    assert normalized["model_memory_utilization"] == 0.322


def test_normalize_large_weight_runtime_status_adds_required_fields() -> None:
    normalized = normalize_large_weight_runtime_status(
        {
            "model": "Kimi-K2.5-3bit",
            "memory_active": "52.3GB",
            "memory_budget_gb": 55,
        }
    )
    result = validate_runtime_status(normalized, kind="large_weight")
    assert result.valid is True
    assert normalized["runtime"] == "kimi-sharded"
    assert normalized["interactive_status"] == "background_only"
