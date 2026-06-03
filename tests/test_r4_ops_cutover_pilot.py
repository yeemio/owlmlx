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


def test_evaluate_watermark_health_no_red() -> None:
    health = pilot.evaluate_watermark_health(["green", "green", "yellow"])
    assert health.watermark_red_observed is False
    assert health.classifications_seen == ("green", "yellow")
    assert "not" in health.interpretation.lower()
    assert "stability" in health.interpretation.lower()


def test_evaluate_watermark_health_red_trips_gate() -> None:
    health = pilot.evaluate_watermark_health(["green", "red"])
    assert health.watermark_red_observed is True
    assert "red" in health.classifications_seen


def test_evaluate_watermark_health_fatal_counts_as_red() -> None:
    health = pilot.evaluate_watermark_health(["fatal"])
    assert health.watermark_red_observed is True


def _passing_components():
    readiness = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    tool_lane = pilot.evaluate_tool_lane(
        {k: True for k in pilot.TOOL_LANE_SUBGATES}
    )
    fallback = pilot.evaluate_fallback_proof(**_proof_inputs())
    watermark = pilot.evaluate_watermark_health(["green", "green"])
    return readiness, tool_lane, fallback, watermark


def test_build_pilot_verdict_passed() -> None:
    readiness, tool_lane, fallback, watermark = _passing_components()
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "passed"
    assert verdict.reasons == ()


def test_build_pilot_verdict_readiness_failure_dominates() -> None:
    probes = _all_pass_probes()
    probes["healthz"]["body"]["ok"] = False
    readiness = pilot.evaluate_readiness(probes, model_id="Qwen3.6-27B")
    _, tool_lane, fallback, watermark = _passing_components()
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "pilot_readiness_failed"


def test_build_pilot_verdict_tool_lane_fail_is_loop_failed() -> None:
    readiness, _, fallback, watermark = _passing_components()
    tool_lane = pilot.evaluate_tool_lane(
        {**{k: True for k in pilot.TOOL_LANE_SUBGATES}, "final_answer_after_tool": False}
    )
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "loop_failed"
    assert any("final_answer_after_tool" in r for r in verdict.reasons)


def test_build_pilot_verdict_watermark_red_is_loop_failed() -> None:
    readiness, tool_lane, fallback, _ = _passing_components()
    watermark = pilot.evaluate_watermark_health(["green", "red"])
    verdict = pilot.build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=True,
    )
    assert verdict.verdict == "loop_failed"
    assert any("watermark" in r.lower() for r in verdict.reasons)


def test_build_readiness_artifact_shape() -> None:
    readiness = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    artifact = pilot.build_readiness_artifact(
        verdict=readiness,
        base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B",
        owlmlx_commit="abc1234",
        recorded_at="2026-06-03T00:00:00Z",
    )
    assert artifact["surface"] == pilot.EVIDENCE_SURFACE
    assert artifact["version"] == pilot.EVIDENCE_VERSION
    assert artifact["kind"] == "readiness"
    assert artifact["verdict"] == "readiness_passed"
    assert artifact["reproduction"]["owlmlx_commit"] == "abc1234"
    assert artifact["promotes"] == "nothing"


def test_build_pilot_artifact_shape_records_all_subgates() -> None:
    readiness, tool_lane, fallback, watermark = _passing_components()
    verdict = pilot.build_pilot_verdict(
        readiness=readiness, tool_lane=tool_lane, fallback=fallback,
        watermark=watermark, loop_completed=True,
    )
    reproduction = {
        "launch_command": "uv run python -m owlmlx.runtime.server ...",
        "env": {"OWLMLX_PILOT_BASE_URL": "http://127.0.0.1:8066"},
        "owlmlx_commit": "abc1234",
        "base_url": "http://127.0.0.1:8066",
        "model_id": "Qwen3.6-27B",
        "session_id": "pilot-001",
        "request_ids": ["req_a", "req_b"],
    }
    artifact = pilot.build_pilot_artifact(
        pilot_verdict=verdict,
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        reproduction=reproduction,
        recorded_at="2026-06-03T00:00:00Z",
    )
    assert artifact["kind"] == "pilot"
    assert artifact["verdict"] == "passed"
    assert set(artifact["tool_lane"]["subgates"]) == set(pilot.TOOL_LANE_SUBGATES)
    assert artifact["fallback"]["fallback_used"] is False
    assert artifact["watermark"]["watermark_red_observed"] is False
    assert artifact["reproduction"]["request_ids"] == ["req_a", "req_b"]
    assert "replacement complete" in artifact["honesty_note"].lower()


import json as _json


def _install_fake_http(monkeypatch, model_id: str, *, tool_calls: bool = True):
    def fake_http_json(*, method, url, payload=None, timeout_s):
        if url.endswith("/healthz"):
            return 200, {"ok": True, "readiness": "ready"}
        if url.endswith("/v1/runtime/model-visibility"):
            return 200, {"visible_model_ids": [model_id], "blocked_model_ids": []}
        if url.endswith("/v1/openai/models"):
            return 200, {"object": "list", "data": [{"id": model_id}]}
        if url.endswith("/v1/chat/completions"):
            calls = [{"id": "c1", "type": "function",
                      "function": {"name": "t", "arguments": "{}"}}] if tool_calls else []
            return 200, {"choices": [{"message": {"tool_calls": calls},
                                      "finish_reason": "tool_calls"}]}
        if url.endswith("/v1/runtime/monitor/snapshot"):
            return 200, {"resources": {"host_pressure": {"classification": "green"}}}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(pilot, "_http_json", fake_http_json)


def test_run_probe_readiness_writes_passed_artifact(tmp_path, monkeypatch) -> None:
    _install_fake_http(monkeypatch, "Qwen3.6-27B")
    result = pilot.run_probe_readiness(
        base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B",
        owlmlx_commit="abc1234",
        evidence_dir=tmp_path,
        timeout_s=5.0,
    )
    assert result["verdict"] == "readiness_passed"
    artifact_path = tmp_path / result["artifact_filename"]
    assert artifact_path.exists()
    written = _json.loads(artifact_path.read_text())
    assert written["kind"] == "readiness"
    assert written["verdict"] == "readiness_passed"


def test_run_probe_readiness_failure_still_writes_artifact(tmp_path, monkeypatch) -> None:
    _install_fake_http(monkeypatch, "Qwen3.6-27B", tool_calls=False)
    result = pilot.run_probe_readiness(
        base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B",
        owlmlx_commit="abc1234",
        evidence_dir=tmp_path,
        timeout_s=5.0,
    )
    assert result["verdict"] == "pilot_readiness_failed"
    assert "tool_lane_live" in result["failures"]
    artifact_path = tmp_path / result["artifact_filename"]
    assert artifact_path.exists()  # constraint #5: failure ALWAYS yields an artifact


def _write_capture(tmp_path, *, override=None):
    capture = {
        "loop_completed": True,
        "tool_lane_subgates": {k: True for k in pilot.TOOL_LANE_SUBGATES},
        "fallback": {
            "config_snapshot": {"base_url": "http://127.0.0.1:8066",
                                 "provider": "owlmlx", "fallback_enabled": False},
            "consumer_outbound": {"fallback_count": 0, "outbound_hosts": ["127.0.0.1:8066"]},
            "owlmlx_inbound": {"served_request_ids": ["req_a", "req_b"]},
        },
        "watermark_classifications": ["green", "green"],
        "reproduction": {
            "launch_command": "uv run python -m owlmlx.runtime.server",
            "env": {"OWLMLX_PILOT_BASE_URL": "http://127.0.0.1:8066"},
            "owlmlx_commit": "abc1234",
            "base_url": "http://127.0.0.1:8066",
            "model_id": "Qwen3.6-27B",
            "session_id": "pilot-001",
            "request_ids": ["req_a", "req_b"],
        },
    }
    if override:
        override(capture)
    path = tmp_path / "capture.json"
    path.write_text(_json.dumps(capture))
    return path


def _write_passing_readiness_artifact(tmp_path):
    readiness = pilot.evaluate_readiness(_all_pass_probes(), model_id="Qwen3.6-27B")
    artifact = pilot.build_readiness_artifact(
        verdict=readiness, base_url="http://127.0.0.1:8066",
        model_id="Qwen3.6-27B", owlmlx_commit="abc1234",
        recorded_at="2026-06-03T00:00:00Z",
    )
    path = tmp_path / "readiness.json"
    path.write_text(_json.dumps(artifact))
    return path


def test_run_assemble_evidence_passed(tmp_path) -> None:
    capture = _write_capture(tmp_path)
    readiness = _write_passing_readiness_artifact(tmp_path)
    result = pilot.run_assemble_evidence(
        capture_path=capture,
        readiness_artifact_path=readiness,
        pilot_base_url="http://127.0.0.1:8066",
        evidence_dir=tmp_path,
    )
    assert result["verdict"] == "passed"
    artifact = _json.loads((tmp_path / result["artifact_filename"]).read_text())
    assert artifact["fallback"]["fallback_used"] is False
    assert set(artifact["tool_lane"]["subgates"]) == set(pilot.TOOL_LANE_SUBGATES)
    ledger_rows = [
        _json.loads(line)
        for line in (tmp_path / "pilot-ledger.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert ledger_rows[-1]["verdict"] == "passed"


def test_run_assemble_evidence_subgate_false_is_loop_failed(tmp_path) -> None:
    def _break(cap):
        cap["tool_lane_subgates"]["tool_result_roundtrip"] = False
    capture = _write_capture(tmp_path, override=_break)
    readiness = _write_passing_readiness_artifact(tmp_path)
    result = pilot.run_assemble_evidence(
        capture_path=capture,
        readiness_artifact_path=readiness,
        pilot_base_url="http://127.0.0.1:8066",
        evidence_dir=tmp_path,
    )
    assert result["verdict"] == "loop_failed"
    assert any("tool_result_roundtrip" in r for r in result["reasons"])
