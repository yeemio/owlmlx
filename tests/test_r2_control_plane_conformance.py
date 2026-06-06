import importlib.util
from pathlib import Path

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "replacement" / "r2_control_plane_conformance.py"
_spec = importlib.util.spec_from_file_location("r2_control_plane_conformance", _MOD)
r2c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r2c)


def test_dot_present_nested_scalar():
    assert r2c._dot_present({"a": {"b": 1}}, "a.b") is True
    assert r2c._dot_present({"a": {"b": 1}}, "a.c") is False
    assert r2c._dot_present({"a": 1}, "a.b") is False


def test_owlcc_healthz_pass():
    v = r2c.evaluate_owlcc_healthz({"ok": True, "readiness": "ready", "model_count": 1})
    assert v["status"] == r2c.PASS
    assert v["missing"] == []


def test_owlcc_healthz_gap_when_missing_readiness():
    v = r2c.evaluate_owlcc_healthz({"ok": True})
    assert v["status"] == r2c.GAP
    assert "readiness" in v["missing"]


def test_owlcc_v1_models_gap_on_statusdict():
    # owlmlx /v1/models is a status-dict with NO data[] -> gap vs OwlCC preflight data[].id
    payload = {"active_model_id": "m", "inventory": {"entries": [{"model_id": "m"}], "model_count": 1}}
    v = r2c.evaluate_owlcc_v1_models(payload)
    assert v["status"] == r2c.GAP
    assert any("data[].id" in m for m in v["missing"])


def test_owlcc_v1_models_pass_on_openai_list():
    v = r2c.evaluate_owlcc_v1_models({"object": "list", "data": [{"id": "m"}]})
    assert v["status"] == r2c.PASS


def test_owlcc_openai_models_resolution_pass():
    v = r2c.evaluate_owlcc_openai_models_resolution({"object": "list", "data": [{"id": "m"}]})
    assert v["status"] == r2c.PASS
    assert v["endpoint"] == "/v1/openai/models"


def _owlmlx_model_visibility_sample():
    return {
        "surface": "/v1/runtime/model-visibility",
        "contract_version": "runtime-owned-2",
        "rule": "registered_base_model_config_present",
        "formal_surface": {"endpoint": "/v1/openai/models"},
        "diagnostic_surface": {"endpoint": "/v1/runtime/model-visibility"},
        "loaded_inventory_surface": {"endpoint": "/v1/models", "semantic_role": "loaded_inventory_only"},
        "gate": {"owner": "owlmlx", "kind": "registry", "models_root": "/m"},
        "visible_model_ids": ["m"],
        "blocked_model_ids": [],
        "entries": [{"model_id": "m", "visible": True, "block_reason": None}],
    }


def test_owlcoda_model_visibility_pass():
    v = r2c.evaluate_owlcoda_model_visibility(_owlmlx_model_visibility_sample())
    assert v["status"] == r2c.PASS, v["missing"]


def test_owlcoda_model_visibility_gap_when_entry_field_missing():
    s = _owlmlx_model_visibility_sample()
    del s["entries"][0]["block_reason"]
    v = r2c.evaluate_owlcoda_model_visibility(s)
    assert v["status"] == r2c.GAP
    assert "entries[].block_reason" in v["missing"]


def test_owlcoda_loaded_inventory_pass():
    payload = {
        "inventory": {"entries": [{"model_id": "m"}], "model_count": 1},
        "visibility_contract": {"loaded_inventory_surface": {"semantic_role": "loaded_inventory_only"}},
    }
    v = r2c.evaluate_owlcoda_loaded_inventory(payload)
    assert v["status"] == r2c.PASS, v["missing"]


def test_owlcoda_runtime_status_reports_missing_fields():
    # Probe the truth: a status-dict missing health.readiness must surface a gap.
    payload = {"backend": {"healthy": True, "loaded_models": [{"model_id": "m"}]},
               "inventory": {"entries": [{"model_id": "m"}], "model_count": 1}}
    v = r2c.evaluate_owlcoda_runtime_status(payload)
    assert v["status"] == r2c.GAP
    assert "health.readiness" in v["missing"]


def test_owlcoda_openai_models_pass():
    v = r2c.evaluate_owlcoda_openai_models({"object": "list", "data": [{"id": "m"}]})
    assert v["status"] == r2c.PASS
