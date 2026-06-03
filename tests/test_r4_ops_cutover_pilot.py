from __future__ import annotations

from scripts.replacement import r4_ops_cutover_pilot as pilot


def test_module_imports_and_exposes_constants() -> None:
    assert pilot.DEFAULT_BASE_URL == "http://127.0.0.1:8066"
    assert pilot.EVIDENCE_SURFACE == "owlmlx.replacement.r4_ops_cutover_pilot"
    assert pilot.TOOL_LANE_SUBGATES == (
        "tool_call_emitted",
        "tool_call_executed",
        "tool_result_roundtrip",
        "final_answer_after_tool",
    )


def _all_pass_probes(model_id: str = "Qwen3.6-27B") -> dict:
    return {
        "healthz": {"status": 200, "body": {"ok": True, "readiness": "ready"}},
        "model_visibility": {
            "status": 200,
            "body": {"visible_model_ids": [model_id], "blocked_model_ids": []},
        },
        "openai_models": {
            "status": 200,
            "body": {"object": "list", "data": [{"id": model_id}]},
        },
        "tool_lane": {
            "status": 200,
            "body": {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {"id": "call_1", "type": "function",
                                 "function": {"name": "get_weather", "arguments": "{}"}}
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
        },
        "monitor": {
            "status": 200,
            "body": {"resources": {"host_pressure": {"classification": "green"}}},
        },
    }


def test_evaluate_readiness_all_pass() -> None:
    verdict = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    assert verdict.ready is True
    assert verdict.verdict == "readiness_passed"
    assert verdict.failures == ()
    assert {c.name for c in verdict.checks} == {
        "healthz_ok",
        "model_visible",
        "model_in_openai_models",
        "tool_lane_live",
        "monitor_reachable",
    }


def test_evaluate_readiness_model_not_visible_fails_with_artifact_verdict() -> None:
    probes = _all_pass_probes()
    probes["model_visibility"]["body"]["visible_model_ids"] = ["some-other-model"]
    verdict = pilot.evaluate_readiness(probes, model_id="Qwen3.6-27B")
    assert verdict.ready is False
    assert verdict.verdict == "pilot_readiness_failed"
    assert "model_visible" in verdict.failures


def test_evaluate_readiness_tool_lane_empty_fails() -> None:
    probes = _all_pass_probes()
    probes["tool_lane"]["body"]["choices"][0]["message"]["tool_calls"] = []
    verdict = pilot.evaluate_readiness(probes, model_id="Qwen3.6-27B")
    assert verdict.ready is False
    assert "tool_lane_live" in verdict.failures


def test_evaluate_tool_lane_all_true_passes() -> None:
    verdict = pilot.evaluate_tool_lane(
        {
            "tool_call_emitted": True,
            "tool_call_executed": True,
            "tool_result_roundtrip": True,
            "final_answer_after_tool": True,
        }
    )
    assert verdict.passed is True
    assert verdict.failing == ()
    assert verdict.subgates == {
        "tool_call_emitted": True,
        "tool_call_executed": True,
        "tool_result_roundtrip": True,
        "final_answer_after_tool": True,
    }


def test_evaluate_tool_lane_one_false_fails_and_records_all_four() -> None:
    verdict = pilot.evaluate_tool_lane(
        {
            "tool_call_emitted": True,
            "tool_call_executed": True,
            "tool_result_roundtrip": False,
            "final_answer_after_tool": True,
        }
    )
    assert verdict.passed is False
    assert verdict.failing == ("tool_result_roundtrip",)
    assert set(verdict.subgates) == set(pilot.TOOL_LANE_SUBGATES)


def test_evaluate_tool_lane_missing_subgate_is_treated_false() -> None:
    verdict = pilot.evaluate_tool_lane({"tool_call_emitted": True})
    assert verdict.passed is False
    assert "tool_call_executed" in verdict.failing
    assert verdict.subgates["final_answer_after_tool"] is False


def _proof_inputs():
    return dict(
        config_snapshot={
            "base_url": "http://127.0.0.1:8066",
            "provider": "owlmlx",
            "fallback_enabled": False,
        },
        consumer_outbound={
            "fallback_count": 0,
            "outbound_hosts": ["127.0.0.1:8066"],
        },
        owlmlx_inbound={"served_request_ids": ["req_a", "req_b", "req_c"]},
        pilot_request_ids=["req_a", "req_b"],
        pilot_base_url="http://127.0.0.1:8066",
    )


def test_evaluate_fallback_proof_all_legs_pass() -> None:
    proof = pilot.evaluate_fallback_proof(**_proof_inputs())
    assert proof.proven is True
    assert proof.config_ok is True
    assert proof.consumer_outbound_ok is True
    assert proof.owlmlx_inbound_ok is True
    assert proof.reasons == ()


def test_evaluate_fallback_proof_config_points_at_8009_fails() -> None:
    args = _proof_inputs()
    args["config_snapshot"]["base_url"] = "http://127.0.0.1:8009"
    proof = pilot.evaluate_fallback_proof(**args)
    assert proof.proven is False
    assert proof.config_ok is False
    assert any("8009" in r or "base_url" in r for r in proof.reasons)


def test_evaluate_fallback_proof_outbound_fallback_count_nonzero_fails() -> None:
    args = _proof_inputs()
    args["consumer_outbound"]["fallback_count"] = 2
    proof = pilot.evaluate_fallback_proof(**args)
    assert proof.proven is False
    assert proof.consumer_outbound_ok is False


def test_evaluate_fallback_proof_inbound_coverage_gap_fails() -> None:
    args = _proof_inputs()
    args["owlmlx_inbound"]["served_request_ids"] = ["req_a"]  # missing req_b
    proof = pilot.evaluate_fallback_proof(**args)
    assert proof.proven is False
    assert proof.owlmlx_inbound_ok is False
