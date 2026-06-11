"""Tests for the runtime-owned model visibility contract."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime_model_visibility import (
    DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS,
    RUNTIME_MODEL_VISIBILITY_CONTRACT_VERSION,
    RUNTIME_MODEL_VISIBILITY_RULE,
    RegisteredRuntimeVisibleModel,
    build_runtime_model_visibility,
    derive_runtime_model_visibility_contract,
)


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def _registry(*model_ids: str) -> tuple[RegisteredRuntimeVisibleModel, ...]:
    return tuple(RegisteredRuntimeVisibleModel(model_id=model_id) for model_id in model_ids)


def _write_base_config(models_root: Path, model_id: str) -> None:
    model_dir = models_root / model_id
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text("{}")


def _client(
    models_root: Path,
    *,
    registry: tuple[RegisteredRuntimeVisibleModel, ...],
) -> TestClient:
    return TestClient(
        create_app(
            RuntimeKernel(FakeBackend(), profile=_profile()),
            visibility_models_root=str(models_root),
            visibility_registry=registry,
        )
    )


def test_default_registry_excludes_retired_gpt_oss_120b() -> None:
    model_ids = {entry.model_id for entry in DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS}

    assert "gpt-oss-120b-MXFP4-Q4" not in model_ids
    assert "gemma-4-12B-it" in model_ids


def test_registered_models_require_base_dir_and_config(tmp_path: Path) -> None:
    _write_base_config(tmp_path, "visible-a")
    (tmp_path / "missing-config").mkdir()

    gate = build_runtime_model_visibility(
        models_root=tmp_path,
        registry=_registry("visible-a", "missing-config", "missing-dir"),
    )

    assert gate.rule == RUNTIME_MODEL_VISIBILITY_RULE
    assert gate.contract_version == RUNTIME_MODEL_VISIBILITY_CONTRACT_VERSION
    assert gate.visible_model_ids == ("visible-a",)
    assert gate.technical_preview_visible_model_ids == ()

    by_id = {entry.model_id: entry for entry in gate.entries}
    assert by_id["visible-a"].visible is True
    assert by_id["visible-a"].tier == "default"
    assert by_id["visible-a"].block_reason is None
    assert by_id["missing-config"].visible is False
    assert by_id["missing-config"].block_reason == "base_model_config_missing"
    assert by_id["missing-dir"].visible is False
    assert by_id["missing-dir"].block_reason == "base_model_directory_missing"


def test_contract_declares_formal_surface_and_loaded_inventory_distinction(
    tmp_path: Path,
) -> None:
    _write_base_config(tmp_path, "visible-a")

    contract = derive_runtime_model_visibility_contract(
        models_root=tmp_path,
        registry=_registry("visible-a"),
    )

    assert contract["rule"] == RUNTIME_MODEL_VISIBILITY_RULE
    assert contract["rule"] == "runtime_gate_required_before_visible"
    assert contract["surface"] == "owlmlx.runtime.model_visibility"
    assert contract["formal_surface"]["endpoint"] == "/v1/openai/models"
    assert contract["diagnostic_surface"]["endpoint"] == "/v1/runtime/model-visibility"
    assert contract["loaded_inventory_surface"]["endpoint"] == "/v1/models"
    assert contract["gate"]["kind"] == "registered_base_model_config_present"
    assert contract["visible_model_ids"] == ["visible-a"]
    assert contract["technical_preview_visible_model_ids"] == []
    assert contract["blocked_model_ids"] == []


def test_runtime_model_visibility_endpoint_tracks_registered_models_not_loaded_inventory(
    tmp_path: Path,
) -> None:
    _write_base_config(tmp_path, "visible-a")
    client = _client(tmp_path, registry=_registry("visible-a"))

    initial = client.get("/v1/runtime/model-visibility")
    assert initial.status_code == 200
    payload = initial.json()
    assert payload["visible_model_ids"] == ["visible-a"]
    assert payload["distinct_from_loaded_inventory"]["loaded_model_ids"] == []

    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 1.0})

    after = client.get("/v1/runtime/model-visibility").json()
    assert after["visible_model_ids"] == ["visible-a"]
    assert after["distinct_from_loaded_inventory"]["loaded_model_ids"] == ["fake-a"]
    assert after["model_count"] == 1
    assert after["distinct_from_platform_rule"]["platform_rule"] == (
        "gate_required_before_visible"
    )


def test_v1_models_embeds_visibility_contract_without_overwriting_inventory(
    tmp_path: Path,
) -> None:
    _write_base_config(tmp_path, "visible-a")
    client = _client(tmp_path, registry=_registry("visible-a"))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 1.0})

    payload = client.get("/v1/models").json()
    assert payload["inventory"]["model_count"] == 1
    assert payload["inventory"]["entries"][0]["model_id"] == "fake-a"
    assert "visibility_contract" in payload

    contract = payload["visibility_contract"]
    assert contract["visible_model_ids"] == ["visible-a"]
    assert "technical_preview_visible_model_ids" not in contract
    assert contract["loaded_inventory_surface"]["semantic_role"] == (
        "currently_loaded_inventory_only"
    )
    assert contract["distinct_from_loaded_inventory"]["loaded_model_ids"] == ["fake-a"]


def test_technical_preview_tier_is_diagnostic_only(tmp_path: Path) -> None:
    _write_base_config(tmp_path, "default-a")
    _write_base_config(tmp_path, "preview-a")
    registry = (
        RegisteredRuntimeVisibleModel("default-a"),
        RegisteredRuntimeVisibleModel("preview-a", tier="technical_preview"),
    )

    gate = build_runtime_model_visibility(models_root=tmp_path, registry=registry)

    assert gate.visible_model_ids == ("default-a",)
    assert gate.technical_preview_visible_model_ids == ("preview-a",)
    by_id = {entry.model_id: entry for entry in gate.entries}
    assert by_id["default-a"].tier == "default"
    assert by_id["preview-a"].tier == "technical_preview"

    contract = derive_runtime_model_visibility_contract(
        models_root=tmp_path,
        registry=registry,
    )
    assert contract["visible_model_ids"] == ["default-a"]
    assert contract["technical_preview_visible_model_ids"] == ["preview-a"]
    assert contract["entries"][0]["tier"] == "default"
    assert contract["entries"][1]["tier"] == "technical_preview"


def test_dict_registry_preserves_technical_preview_tier(tmp_path: Path) -> None:
    _write_base_config(tmp_path, "preview-dict")

    gate = build_runtime_model_visibility(
        models_root=tmp_path,
        registry=(
            {
                "model_id": "preview-dict",
                "tier": "technical_preview",
            },
        ),
    )

    assert gate.visible_model_ids == ()
    assert gate.technical_preview_visible_model_ids == ("preview-dict",)


def test_default_registry_contains_dsv4_as_technical_preview_only() -> None:
    by_id = {
        entry.model_id: entry
        for entry in DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS
    }

    assert by_id["gemma-4-12B-it"].tier == "default"

    deepseek = by_id["DeepSeek-V4-Flash-2bit-DQ"]
    assert deepseek.tier == "technical_preview"


def test_v1_models_scrubs_technical_preview_tier_from_default_surface(
    tmp_path: Path,
) -> None:
    _write_base_config(tmp_path, "visible-a")
    _write_base_config(tmp_path, "DeepSeek-V4-Flash-2bit-DQ")
    registry = (
        RegisteredRuntimeVisibleModel("visible-a"),
        RegisteredRuntimeVisibleModel(
            "DeepSeek-V4-Flash-2bit-DQ",
            tier="technical_preview",
        ),
    )
    client = _client(tmp_path, registry=registry)

    models_payload = client.get("/v1/models").json()
    default_contract = models_payload["visibility_contract"]
    assert "technical_preview_visible_model_ids" not in default_contract
    assert default_contract["visible_model_ids"] == ["visible-a"]
    assert "DeepSeek-V4-Flash-2bit-DQ" not in str(default_contract)

    diagnostic = client.get("/v1/runtime/model-visibility").json()
    assert diagnostic["visible_model_ids"] == ["visible-a"]
    assert diagnostic["technical_preview_visible_model_ids"] == [
        "DeepSeek-V4-Flash-2bit-DQ"
    ]
