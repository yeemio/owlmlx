from __future__ import annotations

from pathlib import Path

from owlmlx.nonresident_loadability_lineage import (
    NONRESIDENT_LOADABILITY_LINEAGE_DECISIONS,
    NONRESIDENT_LOADABILITY_LINEAGE_SURFACE,
    build_nonresident_loadability_lineage,
    nonresident_loadability_lineage_to_dict,
)
from owlmlx.runtime_model_visibility import (
    RuntimeModelVisibilityGate,
    RuntimeVisibleModelState,
)


def _gate(
    *,
    entries: tuple[RuntimeVisibleModelState, ...],
    models_root: str = "/runtime-owned/models",
) -> RuntimeModelVisibilityGate:
    visible_ids = tuple(entry.model_id for entry in entries if entry.visible)
    return RuntimeModelVisibilityGate(
        rule="runtime_gate_required_before_visible",
        contract_version="runtime-owned-2",
        models_root=models_root,
        entries=entries,
        visible_model_ids=visible_ids,
        loaded_model_ids=(),
    )


def _visible_state(
    model_id: str = "fake-b",
    *,
    visible: bool = True,
    block_reason: str | None = None,
    models_root: str = "/runtime-owned/models",
) -> RuntimeVisibleModelState:
    local_dir = f"{models_root}/{model_id}"
    return RuntimeVisibleModelState(
        model_id=model_id,
        local_model_dir=local_dir,
        config_path=f"{local_dir}/config.json",
        local_model_dir_present=visible,
        config_present=visible,
        visible=visible,
        block_reason=block_reason,
    )


def _valid_lineage_record(local_path: str) -> dict[str, object]:
    return {
        "base_model": "fake-b",
        "base_format": "safetensors",
        "quantizer": "owlmlx",
        "quant_method": "q4",
        "served_format": "mlx",
        "conversion_path": "direct",
        "conversion_patches": ["patch-a"],
        "local_path": local_path,
        "file_size_gb": 4.5,
        "sha256": "deadbeef",
        "runtime": "mlx_lm",
        "runtime_version": "1.0",
        "verified_date": "2026-04-25",
        "verified_context": 4096,
        "known_caveats": [],
    }


def test_known_loadable_when_visible_and_lineage_valid_and_aligned() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=gate,
            lineage_records={
                "fake-b": _valid_lineage_record("/runtime-owned/models/fake-b"),
            },
        )
    )

    assert payload["contract"]["surface"] == NONRESIDENT_LOADABILITY_LINEAGE_SURFACE
    assert payload["summary"]["decision"] == "known_loadable"
    assert payload["summary"]["target_model_id"] == "fake-b"
    assert (
        payload["reason"]["code"]
        == "target_visible_lineage_valid_and_aligned_with_local_artifact"
    )
    assert payload["visibility"]["registered"] is True
    assert payload["visibility"]["visible"] is True
    assert payload["lineage"]["target_alignment"] == "aligned"
    assert payload["lineage"]["validation_valid"] is True
    assert payload["blocking_signals"] == []
    assert payload["missing_signals"] == []
    assert payload["inputs"]["visibility_truth_status"] == "runtime_owned_connected"
    assert (
        payload["inputs"]["loadability_lineage_truth_status"]
        == "runtime_owned_connected"
    )


def test_unknown_when_visibility_registry_not_connected() -> None:
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=None,
            lineage_records={"fake-b": _valid_lineage_record("/x")},
        )
    )

    assert payload["summary"]["decision"] == "unknown"
    assert payload["reason"]["code"] == "visibility_registry_not_connected"
    assert any(
        item["layer"] == "visibility" for item in payload["blocking_signals"]
    )
    layers = {item["layer"] for item in payload["missing_signals"]}
    assert "visibility" in layers


def test_unknown_when_loadability_lineage_source_not_connected() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=gate,
            lineage_records=None,
        )
    )

    assert payload["summary"]["decision"] == "unknown"
    assert payload["reason"]["code"] == "loadability_lineage_source_not_connected"
    layers = {item["layer"] for item in payload["missing_signals"]}
    assert "loadability_lineage_source" in layers
    assert (
        payload["inputs"]["loadability_lineage_truth_status"] == "missing"
    )


def test_not_loadable_when_target_missing_from_visibility_registry() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-c",
            runtime_visibility_gate=gate,
            lineage_records={"fake-c": _valid_lineage_record("/x")},
        )
    )

    assert payload["summary"]["decision"] == "not_loadable"
    assert payload["reason"]["code"] == "target_missing_from_runtime_visibility_registry"
    assert payload["visibility"]["registered"] is False
    assert any(
        item["layer"] == "visibility_registry"
        for item in payload["blocking_signals"]
    )


def test_not_loadable_when_required_local_artifact_or_config_absent() -> None:
    gate = _gate(
        entries=(
            _visible_state(
                "fake-b",
                visible=False,
                block_reason="base_model_config_missing",
            ),
        )
    )
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=gate,
            lineage_records={"fake-b": _valid_lineage_record("/x")},
        )
    )

    assert payload["summary"]["decision"] == "not_loadable"
    assert payload["reason"]["code"] == "required_local_artifact_or_config_truth_absent"
    assert payload["visibility"]["block_reason"] == "base_model_config_missing"


def test_not_loadable_when_lineage_record_missing_for_visible_target() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=gate,
            lineage_records={"fake-other": _valid_lineage_record("/x")},
        )
    )

    assert payload["summary"]["decision"] == "not_loadable"
    assert payload["reason"]["code"] == "lineage_record_missing_for_visible_target"


def test_not_loadable_when_lineage_record_invalid() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    invalid_record = {
        "base_model": "fake-b",
        # missing required fields like base_format, quantizer, etc.
    }
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=gate,
            lineage_records={"fake-b": invalid_record},
        )
    )

    assert payload["summary"]["decision"] == "not_loadable"
    assert payload["reason"]["code"] == "lineage_record_invalid_for_lifecycle_state"
    assert payload["lineage"]["validation_valid"] is False
    assert payload["lineage"]["validation_missing_fields"]


def test_not_loadable_when_lineage_local_path_mismatches_visibility() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=gate,
            lineage_records={
                "fake-b": _valid_lineage_record("/different/runtime/path/fake-b"),
            },
        )
    )

    assert payload["summary"]["decision"] == "not_loadable"
    assert payload["reason"]["code"] == "lineage_target_mismatch_with_local_artifact"
    assert payload["lineage"]["target_alignment"] == "mismatch"
    assert any(
        item["layer"] == "lineage_alignment"
        for item in payload["blocking_signals"]
    )


def test_unknown_when_no_target_model_id() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id=None,
            runtime_visibility_gate=gate,
            lineage_records={"fake-b": _valid_lineage_record("/x")},
        )
    )

    assert payload["summary"]["decision"] == "unknown"
    assert payload["reason"]["code"] == "no_target_model_requested"


def test_decision_vocabulary_is_stable() -> None:
    gate = _gate(entries=(_visible_state("fake-b"),))
    payload = nonresident_loadability_lineage_to_dict(
        build_nonresident_loadability_lineage(
            model_id="fake-b",
            runtime_visibility_gate=gate,
            lineage_records={
                "fake-b": _valid_lineage_record("/runtime-owned/models/fake-b"),
            },
        )
    )

    assert payload["summary"]["supported_decisions"] == list(
        NONRESIDENT_LOADABILITY_LINEAGE_DECISIONS
    )
    assert set(payload["decision_support"].keys()) == set(
        NONRESIDENT_LOADABILITY_LINEAGE_DECISIONS
    )


def test_runtime_endpoint_returns_known_loadable_and_admits_without_operator_hint(
    tmp_path: Path,
) -> None:
    from fastapi.testclient import TestClient

    from owlmlx.memory_budget import MachineMemoryProfile
    from owlmlx.runtime import FakeBackend, RuntimeKernel
    from owlmlx.runtime.server import create_app
    from owlmlx.runtime_model_visibility import RegisteredRuntimeVisibleModel

    target_id = "fake-target"
    target_dir = tmp_path / target_id
    target_dir.mkdir()
    (target_dir / "config.json").write_text("{}")

    expected_local_path = str(target_dir)
    lineage_record = _valid_lineage_record(local_path=expected_local_path)
    lineage_record["base_model"] = target_id

    profile = MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )
    client = TestClient(
        create_app(
            RuntimeKernel(FakeBackend(), profile=profile),
            visibility_models_root=str(tmp_path),
            visibility_registry=[RegisteredRuntimeVisibleModel(target_id)],
            loadability_lineage_records={target_id: lineage_record},
        )
    )

    lineage_response = client.get(
        "/v1/runtime/nonresident-loadability-lineage",
        params={"model_id": target_id},
    )
    assert lineage_response.status_code == 200
    lineage_payload = lineage_response.json()
    assert lineage_payload["contract"]["surface"] == NONRESIDENT_LOADABILITY_LINEAGE_SURFACE
    assert lineage_payload["summary"]["decision"] == "known_loadable"
    assert lineage_payload["lineage"]["target_alignment"] == "aligned"

    admission_response = client.get(
        "/v1/runtime/nonresident-model-admission-policy",
        params={"model_id": target_id},
    )
    assert admission_response.status_code == 200
    admission_payload = admission_response.json()
    assert admission_payload["summary"]["decision"] == "admit_and_load"
    assert (
        admission_payload["reason"]["code"]
        == "non_resident_target_runtime_owned_loadability_lineage_admit"
    )
    assert (
        admission_payload["inputs"]["loadability_lineage"]["decision"]
        == "known_loadable"
    )
    assert admission_payload["inputs"]["known_loadable_model_ids"] == []
    layers = {
        item["layer"] for item in admission_payload["missing_signals"]
    }
    assert "loadability" not in layers


def test_nonresident_loadability_lineage_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__)
        .parents[1]
        .joinpath("owlmlx", "nonresident_loadability_lineage.py")
        .read_text()
    )
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
