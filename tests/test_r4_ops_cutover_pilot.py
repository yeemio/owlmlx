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
