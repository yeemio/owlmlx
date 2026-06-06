import importlib.util
from pathlib import Path

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "replacement" / "r4_phaseb_b1_flip_readiness.py"
_spec = importlib.util.spec_from_file_location("r4_phaseb_b1_flip_readiness", _MOD)
b1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b1)


def _conf(*, owlcoda_gap=False, owlcc_gap=True):
    contracts = [
        {"contract": "owlcoda_gate_openai_models", "status": "gap" if owlcoda_gap else "pass"},
        {"contract": "owlcoda_gate_model_visibility", "status": "pass"},
        {"contract": "owlcc_preflight_v1_models", "status": "gap" if owlcc_gap else "pass"},
    ]
    has_gap = any(c["status"] == "gap" for c in contracts)
    return {"verdict": "contract_gap_found" if has_gap else "passed", "contracts": contracts}


def test_go_when_owlcoda_clean_and_ready_even_with_owlcc_gap():
    v = b1.evaluate_flip_readiness(_conf(owlcoda_gap=False, owlcc_gap=True),
                                   {"ready": True, "failures": [], "verdict": "readiness_passed"})
    assert v["verdict"] == "go", v["blocking"]
    assert v["blocking"] == []


def test_no_go_when_owlcoda_contract_gaps():
    v = b1.evaluate_flip_readiness(_conf(owlcoda_gap=True),
                                   {"ready": True, "failures": [], "verdict": "readiness_passed"})
    assert v["verdict"] == "no_go"
    assert any("owlcoda_gate_openai_models" in b for b in v["blocking"])


def test_no_go_when_readiness_not_ready():
    v = b1.evaluate_flip_readiness(_conf(owlcoda_gap=False),
                                   {"ready": False, "failures": ["model_visible"], "verdict": "pilot_readiness_failed"})
    assert v["verdict"] == "no_go"
    assert any("readiness:model_visible" in b for b in v["blocking"])


def test_build_flip_readiness_artifact_shape():
    verdict = {"round": "R4-phaseB-B1", "tier": "flip-readiness", "verdict": "go", "blocking": []}
    art = b1.build_flip_readiness_artifact(verdict=verdict, base_url="http://x", model_id="m",
                                           owlmlx_commit="abc", recorded_at="2026-01-01T00:00:00Z")
    assert art["kind"] == "flip_readiness"
    assert art["verdict"] == "go"
    assert art["promotes"] == "nothing"
    assert art["reproduction"]["model_id"] == "m"
