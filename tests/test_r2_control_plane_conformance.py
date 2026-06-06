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
