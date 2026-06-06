# tests/test_r2_control_plane_operability.py
import importlib.util
from pathlib import Path

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "replacement" / "r2_control_plane_operability.py"
_spec = importlib.util.spec_from_file_location("r2_control_plane_operability", _MOD)
r2o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r2o)


def test_load_step_pass():
    healthz = {"active_model_id": "m", "readiness": "ready"}
    status = {"summary": {"active_model_id": "m"}}
    v = r2o.evaluate_load_step("m", healthz, status)
    assert v["status"] == r2o.PASS, v["reasons"]


def test_load_step_fail_when_wrong_active():
    healthz = {"active_model_id": "other", "readiness": "ready"}
    status = {"summary": {"active_model_id": "other"}}
    v = r2o.evaluate_load_step("m", healthz, status)
    assert v["status"] == r2o.FAIL
    assert any("active_model_id" in r for r in v["reasons"])


def test_switch_step_pass():
    v = r2o.evaluate_switch_step("m2", {"summary": {"active_model_id": "m2"}})
    assert v["status"] == r2o.PASS


def test_evict_step_pass():
    v = r2o.evaluate_evict_step("victim", {"selected_victim": "victim"}, {"summary": {"active_model_id": "keep"}})
    assert v["status"] == r2o.PASS


def test_evict_step_fail_when_no_victim():
    v = r2o.evaluate_evict_step("victim", {}, {"summary": {"active_model_id": "keep"}})
    assert v["status"] == r2o.FAIL


def test_restart_step_pass():
    v = r2o.evaluate_restart_step({"recovery": "ok"}, {"summary": {"readiness": "ready"}})
    assert v["status"] == r2o.PASS


def test_watermark_step_pass():
    v = r2o.evaluate_watermark_step({"level": "GREEN", "recommended_action": "none"})
    assert v["status"] == r2o.PASS


def test_watermark_step_fail_on_unknown():
    v = r2o.evaluate_watermark_step({"level": "UNKNOWN"})
    assert v["status"] == r2o.FAIL


def test_aggregate_lifecycle_passed():
    steps = [{"status": r2o.PASS}, {"status": r2o.PASS}]
    agg = r2o.aggregate_lifecycle(steps)
    assert agg["verdict"] == "passed"


def test_aggregate_lifecycle_failed():
    steps = [{"status": r2o.PASS}, {"status": r2o.FAIL}]
    agg = r2o.aggregate_lifecycle(steps)
    assert agg["verdict"] == "rehearsal_failed"
