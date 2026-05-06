from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from owlmlx.model_release_candidate_ledger import (
    ModelReleaseCandidateLedger,
    model_release_candidate_history_envelope,
    model_release_candidate_still_blocked_payload,
)
from owlmlx.model_release_candidate_record import (
    build_dry_run_model_release_candidate_records,
    build_model_release_candidate_record,
    model_release_candidate_record_to_dict,
)
from owlmlx.model_release_candidate_schema import (
    BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY,
    MODEL_RELEASE_CANDIDATE_LANES,
    MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE,
    MODEL_RELEASE_CANDIDATE_RECORD_SURFACE,
    MODEL_RELEASE_CANDIDATE_RECORD_VERSION,
    MODEL_RELEASE_CANDIDATE_VERDICTS,
    MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES,
    ModelReleaseCandidateSchemaError,
    validate_model_release_candidate_record,
)
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app
from scripts.runtime_model_release_candidate import (
    GEMMA_FINAL_ANSWER_ONLY_INSTRUCTION,
    _chat_messages_for_prompt,
    _classify_output_sanity,
    _effective_generation_policy,
)


def _records():
    return build_dry_run_model_release_candidate_records(
        created_at="2026-05-05T00:00:00Z",
    )


def _record_dicts() -> list[dict[str, object]]:
    return [model_release_candidate_record_to_dict(record) for record in _records()]


def _policy_args(
    *,
    model_id: str,
    apply_model_profile_defaults: bool = False,
    request_mode: str | None = None,
    prompt_template_id: str | None = None,
) -> object:
    return type(
        "Args",
        (),
        {
            "model_id": model_id,
            "apply_model_profile_defaults": apply_model_profile_defaults,
            "request_mode": request_mode,
            "prompt_template_id": prompt_template_id,
        },
    )()


def test_schema_constants_are_frozen() -> None:
    assert MODEL_RELEASE_CANDIDATE_RECORD_SURFACE == "owlmlx.model_release_candidate_record"
    assert MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE == (
        "owlmlx.model_release_candidate_record_history"
    )
    assert MODEL_RELEASE_CANDIDATE_RECORD_VERSION == "v1"
    assert set(MODEL_RELEASE_CANDIDATE_LANES) == {
        "mainline",
        "flagship_experimental",
    }
    assert set(MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES) == {
        "visible",
        "blocked",
        "not_registered",
        "unknown",
    }
    assert set(MODEL_RELEASE_CANDIDATE_VERDICTS) == {
        "pass",
        "needs_optimization",
        "blocked",
        "experimental_only",
    }


def test_banned_vocabulary_is_not_available_as_verdict() -> None:
    assert {
        "parity",
        "replacement",
        "equivalent",
        "production_ready",
        "beats",
        "wins",
    } <= set(BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY)
    for banned in BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY:
        assert banned not in MODEL_RELEASE_CANDIDATE_VERDICTS


def test_profile_policy_default_behavior_unchanged_without_opt_in() -> None:
    policy = _effective_generation_policy(
        _policy_args(model_id="Qwen3.6-27B")
    )

    assert policy["profile_applied"] is False
    assert policy["request_mode"] == "raw_generate_stream"
    assert policy["prompt_template_id"] == "operator_prompt_raw"
    assert policy["quality_caveats"] == []


def test_profile_policy_qwen_uses_chat_template_when_opted_in() -> None:
    policy = _effective_generation_policy(
        _policy_args(
            model_id="Qwen3.6-27B",
            apply_model_profile_defaults=True,
        )
    )

    assert policy["profile_applied"] is True
    assert policy["profile_id"] == "qwen3_6_text"
    assert policy["request_mode"] == "openai_chat_stream"
    assert policy["prompt_template_id"] == "openai_chat_completions_apply_chat_template"
    assert policy["chat_template_kwargs"] == {"enable_thinking": False}
    assert policy["stop_token_strings_applied"] is True
    assert policy["stop_token_application"]["target"] == "http_generation_params.stop"
    assert "model_profile:profile_stop_tokens_applied_experimental" in policy["quality_caveats"]


def test_profile_policy_gemma_records_channel_reasoning_caveats_when_opted_in() -> None:
    policy = _effective_generation_policy(
        _policy_args(
            model_id="gemma-4-31B-it",
            apply_model_profile_defaults=True,
        )
    )

    assert policy["profile_id"] == "gemma4_text"
    assert policy["request_mode"] == "openai_chat_stream"
    assert policy["chat_template_kwargs"] == {"enable_thinking": False}
    assert any(
        "channel-cleanup caveats" in caveat for caveat in policy["quality_caveats"]
    )
    assert policy["stop_token_strings_applied"] is True
    assert policy["stop_token_strings"] == ["<eos>", "<turn|>"]
    assert policy["stop_token_application"]["target"] == "http_generation_params.stop"
    assert "model_profile:profile_stop_tokens_applied_experimental" in policy["quality_caveats"]
    assert "model_profile:gemma_final_answer_only_prompt_control" in policy[
        "quality_caveats"
    ]
    assert policy["prompt_control"]["mode"] == "final_answer_only_user_prefix"


def test_gemma_profile_prompt_control_wraps_user_message_only_when_opted_in() -> None:
    legacy_policy = _effective_generation_policy(
        _policy_args(model_id="gemma-4-31B-it")
    )
    assert _chat_messages_for_prompt(
        prompt="Define local AI.",
        effective_policy=legacy_policy,
    ) == [{"role": "user", "content": "Define local AI."}]

    profile_policy = _effective_generation_policy(
        _policy_args(
            model_id="gemma-4-31B-it",
            apply_model_profile_defaults=True,
        )
    )
    messages = _chat_messages_for_prompt(
        prompt="Define local AI.",
        effective_policy=profile_policy,
    )

    assert messages[0]["role"] == "user"
    assert GEMMA_FINAL_ANSWER_ONLY_INSTRUCTION in messages[0]["content"]
    assert "User request:\nDefine local AI." in messages[0]["content"]


def test_profile_policy_preserves_explicit_cli_overrides() -> None:
    policy = _effective_generation_policy(
        _policy_args(
            model_id="Qwen3.6-27B",
            apply_model_profile_defaults=True,
            request_mode="raw_generate_stream",
            prompt_template_id="operator_prompt_raw_custom",
        )
    )

    assert policy["request_mode"] == "raw_generate_stream"
    assert policy["request_mode_source"] == "explicit_cli"
    assert policy["prompt_template_id"] == "operator_prompt_raw_custom"
    assert policy["prompt_template_id_source"] == "explicit_cli"
    assert "model_profile:explicit_prompt_template_id_preserved" in policy["quality_caveats"]


def test_profile_policy_unknown_model_stays_conservative_when_opted_in() -> None:
    policy = _effective_generation_policy(
        _policy_args(
            model_id="future-local-model-9b",
            apply_model_profile_defaults=True,
        )
    )

    assert policy["profile_id"] == "unknown"
    assert policy["request_mode"] == "raw_generate_stream"
    assert policy["prompt_template_id"] == "operator_prompt_raw"
    assert policy["unknown_model_conservative"] is True
    assert "model_profile:unknown_model_conservative_defaults" in policy["quality_caveats"]


def test_dry_run_matrix_contains_mainline_and_deepseek_without_pass_claims() -> None:
    payload = _record_dicts()
    assert len(payload) == 4
    by_model = {entry["model_id"]: entry for entry in payload}

    assert by_model["Qwen3.6-27B"]["lane"] == "mainline"
    assert by_model["Qwen3.6-35B-A3B"]["visibility_status"] == "visible"
    assert by_model["gemma-4-31B-it"]["verdict"] == "needs_optimization"
    assert "gpt-oss-120b-MXFP4-Q4" not in by_model

    deepseek = by_model["DeepSeek-V4-Flash-2bit-DQ"]
    assert deepseek["lane"] == "flagship_experimental"
    assert deepseek["visibility_status"] == "not_registered"
    assert deepseek["verdict"] == "experimental_only"
    assert "DeepSeek-V4-Flash-2bit-DQ" in deepseek["artifact_path"]

    assert all(entry["verdict"] != "pass" for entry in payload)
    assert all(entry["repeat_count"] == 0 for entry in payload)
    assert all(entry["load_result"]["status"] == "not_run" for entry in payload)


def test_validate_rejects_flagship_experimental_pass() -> None:
    payload = _record_dicts()[-1]
    payload["verdict"] = "pass"
    with pytest.raises(ModelReleaseCandidateSchemaError):
        validate_model_release_candidate_record(payload)


def test_validate_rejects_banned_verdict_vocabulary() -> None:
    payload = _record_dicts()[0]
    payload["verdict"] = "parity"
    with pytest.raises(ModelReleaseCandidateSchemaError):
        validate_model_release_candidate_record(payload)


def test_build_rejects_missing_required_result_shape() -> None:
    record = _record_dicts()[0]
    record["load_result"] = {"status": "not_run"}
    with pytest.raises(ModelReleaseCandidateSchemaError):
        validate_model_release_candidate_record(record)


def test_build_model_release_candidate_record_accepts_live_like_metrics() -> None:
    record = build_model_release_candidate_record(
        created_at="2026-05-05T00:00:00Z",
        model_id="Qwen3.6-27B",
        lane="mainline",
        runtime_url="http://127.0.0.1:8066",
        host_class="Mac17,6-arm64-macOS-26.4.1-128GB",
        artifact_path="/Users/yeemio/AI/Agent/models/Qwen3.6-27B",
        visibility_status="visible",
        load_result={"status": "pass", "detail": "loaded"},
        generation_result={"status": "pass", "detail": "generated"},
        unload_result={"status": "pass", "detail": "unloaded"},
        reload_result={"status": "pass", "detail": "reloaded"},
        repeat_count=2,
        failure_count=0,
        first_token_latency_ms=1200.0,
        tokens_per_second=25.0,
        wall_clock_ms=4000.0,
        peak_resident_set_bytes=50_000_000_000,
        memory_headroom_bytes=20_000_000_000,
        output_sanity_label="valid_text",
        owlops_observation_path="files/evidence/owlops/model-rc/qwen.json",
        verdict="pass",
        blockers=(),
        load_time_ms=100.0,
        reload_time_ms=90.0,
        unload_time_ms=50.0,
        queue_wait_ms=12.0,
        ttft_ms=1200.0,
        decode_tokens_per_second=40.0,
        end_to_end_tokens_per_second=25.0,
        resident_mode="load_unload_per_repeat",
        prompt_template_id="operator_prompt_raw",
        quality_caveats=[],
        memory_peak_source="process_tree_rss",
        runtime_stream_wall_ms=13.0,
        runtime_first_response_ms=11.0,
        runtime_first_visible_token_ms=12.0,
        runtime_prompt_render_ms=2.0,
        runtime_timing_repeat_count=2,
        runtime_timing_gate_status="supported",
    )
    payload = model_release_candidate_record_to_dict(record)
    assert payload["verdict"] == "pass"
    assert payload["repeat_count"] == 2
    assert payload["ttft_ms"] == 1200.0
    assert payload["decode_tokens_per_second"] == 40.0
    assert payload["end_to_end_tokens_per_second"] == 25.0
    assert payload["memory_peak_source"] == "process_tree_rss"
    assert payload["runtime_first_response_ms"] == 11.0
    assert payload["runtime_timing_repeat_count"] == 2
    assert payload["runtime_timing_gate_status"] == "supported"


def test_validate_accepts_legacy_v1_record_without_observability_v2_fields() -> None:
    payload = _record_dicts()[0]
    for field in (
        "load_time_ms",
        "reload_time_ms",
        "unload_time_ms",
        "queue_wait_ms",
        "ttft_ms",
        "decode_tokens_per_second",
        "end_to_end_tokens_per_second",
        "resident_mode",
        "prompt_template_id",
        "quality_caveats",
        "memory_peak_source",
        "runtime_stream_wall_ms",
        "runtime_first_response_ms",
        "runtime_first_visible_token_ms",
        "runtime_prompt_render_ms",
        "runtime_timing_repeat_count",
        "runtime_timing_gate_status",
    ):
        payload.pop(field, None)

    validate_model_release_candidate_record(payload)


def test_validate_rejects_invalid_observability_v2_fields() -> None:
    payload = _record_dicts()[0]
    payload["decode_tokens_per_second"] = -1.0
    with pytest.raises(ModelReleaseCandidateSchemaError):
        validate_model_release_candidate_record(payload)

    payload = _record_dicts()[0]
    payload["quality_caveats"] = ["ok", ""]
    with pytest.raises(ModelReleaseCandidateSchemaError):
        validate_model_release_candidate_record(payload)


def test_ledger_missing_latest_history_and_append_many(tmp_path) -> None:
    ledger = ModelReleaseCandidateLedger(tmp_path / "ledger.jsonl")
    assert ledger.exists() is False
    assert ledger.latest() is None
    assert ledger.history() == []

    appended = ledger.append_many(list(_records()))
    assert len(appended) == 4
    assert ledger.exists() is True
    assert ledger.latest()["model_id"] == "DeepSeek-V4-Flash-2bit-DQ"
    assert len(ledger.history()) == 4


def test_still_blocked_and_history_envelopes_are_stable() -> None:
    blocked = model_release_candidate_still_blocked_payload(
        missing_signal="missing",
        ledger_path="/tmp/ledger.jsonl",
    )
    assert blocked["surface"] == MODEL_RELEASE_CANDIDATE_RECORD_SURFACE
    assert blocked["status"] == "still_blocked"

    envelope = model_release_candidate_history_envelope(
        records=[],
        ledger_status="empty",
    )
    assert envelope["surface"] == MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE
    assert envelope["ledger_status"] == "empty"


def test_operator_dry_run_matrix_outputs_valid_records(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/runtime_model_release_candidate.py",
            "--ledger-path",
            str(tmp_path / "ledger.jsonl"),
            "dry-run-matrix",
            "--created-at",
            "2026-05-05T00:00:00Z",
        ],
        check=True,
        cwd=str(Path(__file__).parents[1]),
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert len(payload) == 4
    for record in payload:
        validate_model_release_candidate_record(record)


def test_operator_append_latest_history_round_trip(tmp_path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    root = str(Path(__file__).parents[1])
    subprocess.run(
        [
            sys.executable,
            "scripts/runtime_model_release_candidate.py",
            "--ledger-path",
            str(ledger),
            "append-dry-run-matrix",
            "--created-at",
            "2026-05-05T00:00:00Z",
        ],
        check=True,
        cwd=root,
        capture_output=True,
        text=True,
    )
    latest = subprocess.run(
        [
            sys.executable,
            "scripts/runtime_model_release_candidate.py",
            "--ledger-path",
            str(ledger),
            "latest",
        ],
        check=True,
        cwd=root,
        capture_output=True,
        text=True,
    )
    history = subprocess.run(
        [
            sys.executable,
            "scripts/runtime_model_release_candidate.py",
            "--ledger-path",
            str(ledger),
            "history",
        ],
        check=True,
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert json.loads(latest.stdout)["model_id"] == "DeepSeek-V4-Flash-2bit-DQ"
    assert len(json.loads(history.stdout)["records"]) == 4


def test_operator_append_record_file_and_merge_ledgers(tmp_path) -> None:
    root = str(Path(__file__).parents[1])
    source_a = tmp_path / "source-a.jsonl"
    source_b = tmp_path / "source-b.jsonl"
    out = tmp_path / "combined.jsonl"
    records = _record_dicts()
    source_a.write_text(json.dumps(records[0]) + "\n", encoding="utf-8")
    source_b.write_text(json.dumps(records[1]) + "\n", encoding="utf-8")
    record_file = tmp_path / "record-c.json"
    record_file.write_text(json.dumps(records[2]), encoding="utf-8")

    merge = subprocess.run(
        [
            sys.executable,
            "scripts/runtime_model_release_candidate.py",
            "--ledger-path",
            str(out),
            "merge-ledgers",
            str(source_a),
            str(source_b),
            str(record_file),
            str(source_a),
            "--replace",
        ],
        check=True,
        cwd=root,
        capture_output=True,
        text=True,
    )
    merged = json.loads(merge.stdout)
    assert [record["model_id"] for record in merged] == [
        "Qwen3.6-27B",
        "Qwen3.6-35B-A3B",
        "gemma-4-31B-it",
    ]
    assert len(ModelReleaseCandidateLedger(out).history()) == 3

    append = subprocess.run(
        [
            sys.executable,
            "scripts/runtime_model_release_candidate.py",
            "--ledger-path",
            str(out),
            "append-record-file",
            str(tmp_path / "record-c.json"),
        ],
        check=True,
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert json.loads(append.stdout)["model_id"] == "gemma-4-31B-it"
    assert len(ModelReleaseCandidateLedger(out).history()) == 4


def test_operator_live_http_mainline_appends_valid_record(tmp_path) -> None:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:  # pragma: no cover - quiet test server
            return

        def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802 - stdlib hook
            if self.path == "/healthz":
                self._send_json({"ok": True, "readiness": "degraded"})
                return
            if self.path == "/v1/runtime/status":
                self._send_json(
                    {
                        "summary": {
                            "backend_healthy": True,
                            "active_model_id": None,
                        }
                    }
                )
                return
            if self.path == "/v1/openai/models":
                self._send_json(
                    {
                        "object": "list",
                        "data": [{"id": "Qwen3.6-27B", "object": "model"}],
                    }
                )
                return
            if self.path.startswith("/v1/runtime/model-load-admission"):
                self._send_json(
                    {
                        "surface": "owlmlx.model_load_admission",
                        "version": "v1",
                        "summary": {"ledger_status": "fixture"},
                        "entries": [
                            {
                                "model_id": "Qwen3.6-27B",
                                "admission_decision": "admit",
                                "reason_code": "fixture_admit",
                            }
                        ],
                    }
                )
                return
            self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802 - stdlib hook
            length = int(self.headers.get("Content-Length") or 0)
            _payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/v1/runtime/host-pressure-sample":
                self._send_json(
                    {
                        "surface": "owlmlx.host_pressure_sample",
                        "version": "v1",
                        "snapshot": {
                            "available": True,
                            "classification": "normal",
                            "reason_code": "fixture_normal",
                        },
                    }
                )
                return
            if self.path == "/v1/load":
                self._send_json({"ok": True, "message": "loaded"})
                return
            if self.path == "/v1/unload":
                self._send_json({"ok": True, "message": "unloaded"})
                return
            if self.path == "/v1/generate/stream":
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                time.sleep(0.08)
                for text in ("O", "K", "."):
                    self.wfile.write(
                        json.dumps(
                            {
                                "event": "token",
                                "model_id": "Qwen3.6-27B",
                                "text": text,
                            }
                        ).encode("utf-8")
                        + b"\n"
                    )
                    self.wfile.flush()
                    time.sleep(0.01)
                self.wfile.write(
                    json.dumps(
                        {
                            "event": "done",
                            "model_id": "Qwen3.6-27B",
                            "completion_tokens": 3,
                            "finish_reason": "stop",
                            "wait_time_s": 0.012,
                            "detail": {
                                "timing": {
                                    "surface": "owlmlx.child_stream_timing",
                                    "version": "v1",
                                    "prompt_render_ms": 2.0,
                                    "first_response_ms": 11.0,
                                    "first_visible_token_ms": 12.0,
                                    "stream_wall_ms": 13.0,
                                }
                            },
                        }
                    ).encode("utf-8")
                    + b"\n"
                )
                self.wfile.flush()
                return
            self._send_json({"error": "not found"}, status=404)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        ledger = tmp_path / "ledger.jsonl"
        evidence_dir = tmp_path / "evidence"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/runtime_model_release_candidate.py",
                "--ledger-path",
                str(ledger),
                "run-live-http-mainline",
                "--runtime-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model-id",
                "Qwen3.6-27B",
                "--artifact-path",
                "/Users/yeemio/AI/Agent/models/Qwen3.6-27B",
                "--prompt",
                "hello",
                "--max-tokens",
                "2",
                "--repeats",
                "2",
                "--evidence-dir",
                str(evidence_dir),
                "--http-timeout-s",
                "5",
                "--rss-root-pid",
                str(os.getpid()),
                "--rss-sample-interval-s",
                "0.05",
                "--timing-gate-resident-repeat",
            ],
            check=True,
            cwd=str(Path(__file__).parents[1]),
            capture_output=True,
            text=True,
        )
    finally:
        server.shutdown()
        server.server_close()

    payload = json.loads(result.stdout)
    validate_model_release_candidate_record(payload)
    assert payload["model_id"] == "Qwen3.6-27B"
    assert payload["repeat_count"] == 2
    assert payload["failure_count"] == 0
    assert payload["load_result"]["status"] == "pass"
    assert payload["generation_result"]["status"] == "pass"
    assert payload["unload_result"]["status"] == "pass"
    assert payload["reload_result"]["status"] == "pass"
    assert payload["verdict"] == "needs_optimization"
    assert payload["first_token_latency_ms"] is not None
    assert payload["tokens_per_second"] is not None
    assert payload["ttft_ms"] == payload["first_token_latency_ms"]
    assert payload["end_to_end_tokens_per_second"] == payload["tokens_per_second"]
    assert payload["decode_tokens_per_second"] is not None
    assert payload["decode_tokens_per_second"] > payload["end_to_end_tokens_per_second"]
    assert payload["load_time_ms"] is not None
    assert payload["reload_time_ms"] is not None
    assert payload["unload_time_ms"] is not None
    assert payload["queue_wait_ms"] == 12.0
    assert payload["resident_mode"] == "load_unload_per_repeat"
    assert payload["prompt_template_id"] == "operator_prompt_raw"
    assert payload["quality_caveats"] == [
        "blocker:owlops_observation_pending",
        "blocker:reference_runtime_comparison_missing",
    ]
    assert payload["memory_peak_source"] == "process_tree_rss"
    assert payload["runtime_stream_wall_ms"] == 13.0
    assert payload["runtime_first_response_ms"] == 11.0
    assert payload["runtime_first_visible_token_ms"] == 12.0
    assert payload["runtime_prompt_render_ms"] == 2.0
    assert payload["runtime_timing_repeat_count"] == 4
    assert payload["runtime_timing_gate_status"] == "supported"
    assert payload["peak_resident_set_bytes"] is not None
    runner_config = json.loads((evidence_dir / "runner-config.json").read_text())
    assert runner_config["model_profile"]["profile_id"] == "qwen3_6_text"
    assert "effective_generation_policy" not in runner_config
    assert (evidence_dir / "repeat-01-host-pressure-sample.json").exists()
    assert (evidence_dir / "repeat-01-model-load-admission-before.json").exists()
    first_generation = json.loads(
        (evidence_dir / "repeat-01-generation.json").read_text(encoding="utf-8")
    )
    assert first_generation["request_payload"] == {
        "model_id": "Qwen3.6-27B",
        "prompt": "hello",
        "params": {"max_tokens": 2, "temperature": 0.0},
    }
    first_timing = first_generation["timing_breakdown"]
    assert first_timing["load_elapsed_ms"] is not None
    assert first_timing["stream_request_wall_ms"] == first_generation["elapsed_ms"]
    assert first_timing["first_token_latency_ms"] == first_generation["first_token_latency_ms"]
    assert first_timing["queue_wait_ms"] == 12.0
    assert first_timing["completion_tokens"] == 3
    assert first_timing["post_first_token_decode_tokens"] == 2
    assert first_timing["post_first_token_decode_wall_ms"] is not None
    assert first_timing["post_first_token_decode_wall_ms"] > 0
    assert first_generation["runtime_stream_timing"]["stream_wall_ms"] == 13.0
    assert first_timing["runtime_first_response_ms"] == 11.0
    assert abs(
        first_timing["stream_request_wall_ms"]
        - (
            first_timing["first_token_latency_ms"]
            + first_timing["post_first_token_decode_wall_ms"]
        )
    ) <= 0.002
    assert first_generation["reasoning_trace_policy"]["visible_reasoning_trace"] is False
    assert first_generation["reasoning_trace_policy"]["final_text"] == "OK."
    resident_generation = json.loads(
        (evidence_dir / "repeat-01-resident-generation.json").read_text(
            encoding="utf-8"
        )
    )
    assert resident_generation["runtime_stream_timing"]["first_visible_token_ms"] == 12.0
    timing_gate = json.loads(
        (evidence_dir / "timing-gate-summary.json").read_text(encoding="utf-8")
    )
    assert timing_gate["status"] == "supported"
    assert timing_gate["runtime_timing_repeat_count"] == 4
    assert timing_gate["classification"] == "measured_without_cold_dominance"
    assert (evidence_dir / "post-run-healthz.json").exists()
    assert (evidence_dir / "post-run-runtime-status.json").exists()
    assert (evidence_dir / "record.json").exists()
    assert ModelReleaseCandidateLedger(ledger).latest()["model_id"] == "Qwen3.6-27B"


def test_operator_live_http_mainline_can_use_openai_chat_stream(tmp_path) -> None:
    seen_payloads: list[dict[str, object]] = []
    seen_load_payloads: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:  # pragma: no cover - quiet test server
            return

        def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802 - stdlib hook
            if self.path == "/healthz":
                self._send_json({"ok": True, "readiness": "degraded"})
                return
            if self.path == "/v1/runtime/status":
                self._send_json(
                    {
                        "summary": {
                            "backend_healthy": True,
                            "active_model_id": None,
                        }
                    }
                )
                return
            if self.path == "/v1/openai/models":
                self._send_json(
                    {
                        "object": "list",
                        "data": [{"id": "gemma-4-31B-it", "object": "model"}],
                    }
                )
                return
            if self.path.startswith("/v1/runtime/model-load-admission"):
                self._send_json(
                    {
                        "surface": "owlmlx.model_load_admission",
                        "version": "v1",
                        "summary": {"ledger_status": "fixture"},
                        "entries": [
                            {
                                "model_id": "gemma-4-31B-it",
                                "admission_decision": "admit",
                                "reason_code": "fixture_admit",
                                "known_peak_resident_set_bytes": 4 * 1024**3,
                            }
                        ],
                    }
                )
                return
            self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802 - stdlib hook
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/v1/runtime/host-pressure-sample":
                self._send_json(
                    {
                        "surface": "owlmlx.host_pressure_sample",
                        "version": "v1",
                        "snapshot": {
                            "available": True,
                            "classification": "normal",
                            "reason_code": "fixture_normal",
                        },
                    }
                )
                return
            if self.path == "/v1/load":
                seen_load_payloads.append(payload)
                self._send_json({"ok": True, "message": "loaded"})
                return
            if self.path == "/v1/unload":
                self._send_json({"ok": True, "message": "unloaded"})
                return
            if self.path == "/v1/chat/completions":
                seen_payloads.append(payload)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for text in ("Local", " AI", " stays", " on-device."):
                    chunk = {
                        "choices": [
                            {
                                "delta": {"content": text},
                                "finish_reason": None,
                                "index": 0,
                            }
                        ]
                    }
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(0.01)
                done = {
                    "choices": [
                        {
                            "delta": {},
                            "finish_reason": "stop",
                            "index": 0,
                        }
                    ]
                }
                self.wfile.write(f"data: {json.dumps(done)}\n\n".encode("utf-8"))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
                return
            self._send_json({"error": "not found"}, status=404)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        ledger = tmp_path / "ledger.jsonl"
        evidence_dir = tmp_path / "evidence"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/runtime_model_release_candidate.py",
                "--ledger-path",
                str(ledger),
                "run-live-http-mainline",
                "--runtime-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model-id",
                "gemma-4-31B-it",
                "--artifact-path",
                "/Users/yeemio/AI/Agent/models/gemma-4-31B-it",
                "--prompt",
                "In one short sentence, define local AI.",
                "--max-tokens",
                "8",
                "--request-mode",
                "openai_chat_stream",
                "--apply-model-profile-defaults",
                "--repeats",
                "2",
                "--evidence-dir",
                str(evidence_dir),
                "--http-timeout-s",
                "5",
                "--rss-root-pid",
                str(os.getpid()),
                "--rss-sample-interval-s",
                "0.05",
            ],
            check=True,
            cwd=str(Path(__file__).parents[1]),
            capture_output=True,
            text=True,
        )
    finally:
        server.shutdown()
        server.server_close()

    payload = json.loads(result.stdout)
    validate_model_release_candidate_record(payload)
    assert len(seen_payloads) == 2
    assert seen_load_payloads[0]["memory_gb"] == 4.0
    assert seen_payloads[0]["stream"] is True
    assert seen_payloads[0]["stop"] == ["<eos>", "<turn|>"]
    assert seen_payloads[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert seen_payloads[0]["messages"][0]["role"] == "user"
    assert GEMMA_FINAL_ANSWER_ONLY_INSTRUCTION in seen_payloads[0]["messages"][0]["content"]
    assert "User request:\nIn one short sentence, define local AI." in seen_payloads[0]["messages"][0]["content"]
    assert payload["model_id"] == "gemma-4-31B-it"
    assert payload["prompt_template_id"] == "openai_chat_completions_apply_chat_template"
    assert payload["output_sanity_label"] == "valid_text"
    assert payload["queue_wait_ms"] is None
    assert payload["decode_tokens_per_second"] is not None
    assert "model_profile:profile_stop_tokens_applied_experimental" in payload["quality_caveats"]
    assert "blocker:owlops_observation_pending" in payload["quality_caveats"]
    assert "blocker:reference_runtime_comparison_missing" in payload["quality_caveats"]
    stream_events = [
        json.loads(line)
        for line in (evidence_dir / "repeat-01-stream.ndjson").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert stream_events[-1]["event"] == "done"
    assert stream_events[-1]["completion_tokens"] == 4
    first_generation = json.loads(
        (evidence_dir / "repeat-01-generation.json").read_text(encoding="utf-8")
    )
    assert first_generation["request_payload"]["model"] == "gemma-4-31B-it"
    assert first_generation["request_payload"]["stream"] is True
    assert first_generation["request_payload"]["stop"] == ["<eos>", "<turn|>"]
    assert first_generation["request_payload"]["chat_template_kwargs"] == {
        "enable_thinking": False
    }
    assert first_generation["request_payload"]["messages"] == seen_payloads[0]["messages"]
    first_timing = first_generation["timing_breakdown"]
    assert first_timing["load_elapsed_ms"] is not None
    assert first_timing["stream_request_wall_ms"] == first_generation["elapsed_ms"]
    assert first_timing["first_token_latency_ms"] == first_generation["first_token_latency_ms"]
    assert first_timing["queue_wait_ms"] is None
    assert first_timing["completion_tokens"] == 4
    assert first_timing["post_first_token_decode_tokens"] == 3
    assert first_timing["post_first_token_decode_wall_ms"] is not None
    assert abs(
        first_timing["stream_request_wall_ms"]
        - (
            first_timing["first_token_latency_ms"]
            + first_timing["post_first_token_decode_wall_ms"]
        )
    ) <= 0.002
    trace_policy = first_generation["reasoning_trace_policy"]
    assert trace_policy["visible_reasoning_trace"] is False
    assert trace_policy["final_text"] == "Local AI stays on-device."
    runner_config = json.loads((evidence_dir / "runner-config.json").read_text())
    assert runner_config["model_profile"]["profile_id"] == "gemma4_text"
    assert (evidence_dir / "repeat-01-host-pressure-sample.json").exists()
    assert (evidence_dir / "repeat-01-model-load-admission-before.json").exists()
    assert (evidence_dir / "post-run-healthz.json").exists()
    assert (evidence_dir / "post-run-runtime-status.json").exists()
    effective_policy = runner_config["effective_generation_policy"]
    assert effective_policy["profile_applied"] is True
    assert effective_policy["request_mode"] == "openai_chat_stream"
    assert effective_policy["request_mode_source"] == "explicit_cli"
    assert effective_policy["prompt_control"]["mode"] == "final_answer_only_user_prefix"
    assert effective_policy["stop_token_strings_applied"] is True
    assert effective_policy["chat_template_kwargs"] == {"enable_thinking": False}


def test_operator_live_http_mainline_blocks_dirty_post_run_backend_health(tmp_path) -> None:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:  # pragma: no cover - quiet test server
            return

        def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802 - stdlib hook
            if self.path == "/healthz":
                self._send_json(
                    {
                        "ok": False,
                        "readiness": "blocked",
                        "backend_error": "fixture backend parse error",
                    }
                )
                return
            if self.path == "/v1/runtime/status":
                self._send_json(
                    {
                        "summary": {
                            "backend_healthy": False,
                            "active_model_id": None,
                        },
                        "backend": {
                            "detail": {
                                "last_error": "fixture backend parse error",
                            }
                        },
                    }
                )
                return
            if self.path == "/v1/openai/models":
                self._send_json(
                    {
                        "object": "list",
                        "data": [{"id": "Qwen3.6-27B", "object": "model"}],
                    }
                )
                return
            if self.path.startswith("/v1/runtime/model-load-admission"):
                self._send_json(
                    {
                        "surface": "owlmlx.model_load_admission",
                        "version": "v1",
                        "summary": {"ledger_status": "fixture"},
                        "entries": [
                            {
                                "model_id": "Qwen3.6-27B",
                                "admission_decision": "admit",
                                "reason_code": "fixture_admit",
                            }
                        ],
                    }
                )
                return
            self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802 - stdlib hook
            length = int(self.headers.get("Content-Length") or 0)
            _payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/v1/runtime/host-pressure-sample":
                self._send_json(
                    {
                        "surface": "owlmlx.host_pressure_sample",
                        "version": "v1",
                        "snapshot": {
                            "available": True,
                            "classification": "normal",
                            "reason_code": "fixture_normal",
                        },
                    }
                )
                return
            if self.path == "/v1/load":
                self._send_json({"ok": True, "message": "loaded"})
                return
            if self.path == "/v1/unload":
                self._send_json({"ok": True, "message": "unloaded"})
                return
            if self.path == "/v1/generate/stream":
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "event": "token",
                            "model_id": "Qwen3.6-27B",
                            "text": "OK",
                        }
                    ).encode("utf-8")
                    + b"\n"
                )
                self.wfile.write(
                    json.dumps(
                        {
                            "event": "done",
                            "model_id": "Qwen3.6-27B",
                            "completion_tokens": 1,
                            "finish_reason": "stop",
                        }
                    ).encode("utf-8")
                    + b"\n"
                )
                self.wfile.flush()
                return
            self._send_json({"error": "not found"}, status=404)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        ledger = tmp_path / "ledger.jsonl"
        evidence_dir = tmp_path / "evidence"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/runtime_model_release_candidate.py",
                "--ledger-path",
                str(ledger),
                "run-live-http-mainline",
                "--runtime-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model-id",
                "Qwen3.6-27B",
                "--artifact-path",
                "/Users/yeemio/AI/Agent/models/Qwen3.6-27B",
                "--prompt",
                "hello",
                "--max-tokens",
                "2",
                "--repeats",
                "1",
                "--evidence-dir",
                str(evidence_dir),
                "--http-timeout-s",
                "5",
                "--rss-root-pid",
                str(os.getpid()),
                "--rss-sample-interval-s",
                "0.05",
            ],
            check=True,
            cwd=str(Path(__file__).parents[1]),
            capture_output=True,
            text=True,
        )
    finally:
        server.shutdown()
        server.server_close()

    payload = json.loads(result.stdout)
    validate_model_release_candidate_record(payload)
    first_generation = json.loads(
        (evidence_dir / "repeat-01-generation.json").read_text(encoding="utf-8")
    )
    assert first_generation["reasoning_trace_policy"]["trace_status"] == "none"
    assert payload["failure_count"] == 1
    assert payload["verdict"] == "blocked"
    assert "post_run_backend_unhealthy" in payload["blockers"]
    assert "blocker:post_run_backend_unhealthy" in payload["quality_caveats"]
    post_health = json.loads((evidence_dir / "post-run-healthz.json").read_text())
    assert post_health["payload"]["backend_error"] == "fixture backend parse error"


def test_live_runner_classifies_length_truncated_reasoning_trace() -> None:
    label = _classify_output_sanity(
        generated_texts=["\n\n<think>\nThinking Process:"],
        generation_results=[
            {
                "done": {
                    "finish_reason": "length",
                }
            }
        ],
    )

    assert label == "reasoning_trace_truncated"


def test_live_runner_classifies_channel_thought_truncation_as_reasoning_trace() -> None:
    label = _classify_output_sanity(
        generated_texts=[
            (
                "<|channel>thought\n"
                "* Topic: Local AI.\n"
                "* Constraint: One short sentence."
            )
        ],
        generation_results=[
            {
                "done": {
                    "finish_reason": "length",
                }
            }
        ],
    )

    assert label == "reasoning_trace_truncated"


def test_live_runner_classifies_visible_reasoning_trace() -> None:
    label = _classify_output_sanity(
        generated_texts=[
            "<think>short plan</think>\nFinal answer."
        ],
        generation_results=[
            {
                "done": {
                    "finish_reason": "stop",
                }
            }
        ],
    )

    assert label == "reasoning_trace_visible"


def test_live_runner_keeps_plain_nonempty_text_valid() -> None:
    label = _classify_output_sanity(
        generated_texts=[" OK."],
        generation_results=[
            {
                "done": {
                    "finish_reason": "stop",
                }
            }
        ],
    )

    assert label == "valid_text"


def test_live_runner_classifies_repeated_la_sequence() -> None:
    label = _classify_output_sanity(
        generated_texts=["la la la la la la la la la"],
        generation_results=[{"done": {"finish_reason": "length"}}],
    )

    assert label == "repeated_la_sequence"


def test_live_runner_classifies_repeated_prompt_echo() -> None:
    label = _classify_output_sanity(
        generated_texts=[
            (
                "In one short sentence, define local AI. "
                "In one short sentence, define local AI. "
                "In one short sentence, define local AI."
            )
        ],
        generation_results=[{"done": {"finish_reason": "length"}}],
    )

    assert label == "repetitive_output"


def test_http_surface_still_blocked_when_ledger_not_connected() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend())))
    latest = client.get("/v1/runtime/model-release-candidates")
    history = client.get("/v1/runtime/model-release-candidates/history")

    assert latest.status_code == 503
    assert latest.json()["missing_signal"] == "model_release_candidate_ledger_not_connected"
    assert history.status_code == 503
    assert history.json()["missing_signal"] == "model_release_candidate_ledger_not_connected"


def test_http_surface_returns_latest_and_history_when_seeded(tmp_path) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    ModelReleaseCandidateLedger(ledger_path).append_many(list(_records()))
    client = TestClient(
        create_app(
            RuntimeKernel(FakeBackend()),
            model_release_candidate_ledger_path=str(ledger_path),
        )
    )

    latest = client.get("/v1/runtime/model-release-candidates")
    history = client.get("/v1/runtime/model-release-candidates/history")

    assert latest.status_code == 200
    assert latest.json()["surface"] == MODEL_RELEASE_CANDIDATE_RECORD_SURFACE
    assert latest.json()["model_id"] == "DeepSeek-V4-Flash-2bit-DQ"
    assert history.status_code == 200
    assert history.json()["surface"] == MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE
    assert len(history.json()["records"]) == 4
