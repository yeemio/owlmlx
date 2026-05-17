from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.bench import deepseek_v4_d1_repeatability as d1


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_checkpoint_model(
    path: Path,
    *,
    num_hidden_layers: int = 2,
    num_nextn_predict_layers: int = 1,
    weight_keys: tuple[str, ...] = (),
) -> None:
    path.mkdir()
    (path / "config.json").write_text(
        json.dumps(
            {
                "model_type": d1.MODEL_TYPE,
                "architectures": ["DeepseekV4ForCausalLM"],
                "num_hidden_layers": num_hidden_layers,
                "num_nextn_predict_layers": num_nextn_predict_layers,
                "max_position_embeddings": 1048576,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    weight_map = {key: "model-00001-of-00001.safetensors" for key in weight_keys}
    (path / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "metadata": {
                    "total_size": 1234,
                    "total_parameters": 5678,
                },
                "weight_map": weight_map,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


class _FakeStdout:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def readline(self) -> str:
        if not self.lines:
            return ""
        return self.lines.pop(0)


class _FakeStdin:
    def __init__(self, proc: "_FakeProcess") -> None:
        self.proc = proc
        self.writes: list[dict] = []

    def write(self, text: str) -> int:
        payload = json.loads(text)
        self.writes.append(payload)
        self.proc.handle(payload)
        return len(text)

    def flush(self) -> None:
        return None


class _FakeProcess:
    def __init__(self, cmd: list[str], **kwargs: object) -> None:
        self.cmd = cmd
        self.kwargs = kwargs
        self.returncode: int | None = None
        self.stdout = _FakeStdout()
        self.stdin = _FakeStdin(self)
        self.stderr = None
        self.pid = 4242
        self.generation_count = 0

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.returncode = -15

    def handle(self, payload: dict) -> None:
        action = payload["action"]
        if action == "load":
            response = {
                "ok": True,
                "action": "load",
                "model_id": payload["model_id"],
                "pid": self.pid,
            }
        elif action in {"generate", "generate_messages"}:
            self.generation_count += 1
            text_prefix = "messages-completion" if action == "generate_messages" else "completion"
            response = {
                "ok": True,
                "action": action,
                "model_id": payload["model_id"],
                "text": f"{text_prefix}-{self.generation_count}",
                "finish_reason": "stop",
                "pid": self.pid,
                "generation_count": self.generation_count,
            }
            if action == "generate_messages":
                response["message_count"] = len(payload.get("messages") or [])
        elif action in {"stream_generate", "stream_generate_messages"}:
            self.generation_count += 1
            text_prefix = (
                "messages-stream-completion"
                if action == "stream_generate_messages"
                else "completion"
            )
            event_action = (
                "stream_message_event"
                if action == "stream_generate_messages"
                else "stream_event"
            )
            done_action = (
                "stream_message_done"
                if action == "stream_generate_messages"
                else "stream_done"
            )
            terminal_action = (
                "stream_message_done"
                if action == "stream_generate_messages"
                else "stream_done"
            )
            text = f"{text_prefix}-{self.generation_count}"
            token = {
                "ok": True,
                "action": event_action,
                "event": "token",
                "model_id": payload["model_id"],
                "text": text,
                "finish_reason": "length",
                "pid": self.pid,
                "prompt_tokens": 7,
                "completion_tokens": payload["params"]["max_tokens"],
                "timing": {
                    "first_visible_token_ms": 12.5,
                    "stream_wall_ms": 25.0,
                },
            }
            done = {
                "ok": True,
                "action": done_action,
                "event": "done",
                "model_id": payload["model_id"],
                "finish_reason": "length",
                "pid": self.pid,
                "generation_count": self.generation_count,
                "prompt_tokens": 7,
                "completion_tokens": payload["params"]["max_tokens"],
                "timing": {
                    "first_visible_token_ms": 12.5,
                    "stream_wall_ms": 25.0,
                },
            }
            diagnostic = {
                "ok": True,
                "action": "stream_runtime_owned_terminal_boundary",
                "terminal_action": terminal_action,
                "model_id": payload["model_id"],
                "pid": self.pid,
                "sequence": 1,
            }
            self.stdout.lines.append(json.dumps(token) + "\n")
            self.stdout.lines.append(json.dumps(diagnostic) + "\n")
            self.stdout.lines.append(json.dumps(done) + "\n")
            return
        elif action == "unload":
            response = {
                "ok": True,
                "action": "unload",
                "model_id": payload["model_id"],
                "pid": self.pid,
            }
        elif action == "ping":
            response = {
                "ok": True,
                "action": "ping",
                "model_id": None,
                "pid": self.pid,
                "generation_count": 0,
            }
        elif action == "shutdown":
            response = {
                "ok": True,
                "action": "shutdown",
                "model_id": None,
                "pid": self.pid,
            }
            self.returncode = 0
        else:
            response = {"ok": False, "error": f"bad action: {action}"}
        self.stdout.lines.append(json.dumps(response) + "\n")


def test_preflight_reports_missing_deepseek_v4_import_as_blocked(monkeypatch, tmp_path):
    fake_python = tmp_path / "python"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    model_path = tmp_path / "DeepSeek-V4-Flash-2bit-DQ"
    model_path.mkdir()

    def fake_imports(python_path: Path, timeout_s: float = 20.0) -> dict:
        assert python_path == fake_python
        assert timeout_s == 20.0
        return {
            "ok": False,
            "returncode": 0,
            "imports": {
                "mlx_lm": True,
                d1.DEEPSEEK_V4_MODULE: False,
            },
            "stderr": "",
        }

    monkeypatch.setattr(d1, "_check_isolated_imports", fake_imports)

    payload = d1.run_preflight(
        isolated_python=fake_python,
        model_path=model_path,
        isolated_runtime_path=tmp_path / ".runtime-deepseek-v4-mlx",
    )

    assert payload["verdict"] == "blocked"
    assert payload["preflight"] == "blocked"
    assert payload["isolation"]["stock_runtime_untouched"] is True
    assert payload["isolation"]["default_model_surface_unchanged"] is True
    assert payload["isolation"]["ds4_c_adopted"] is False
    assert "deepseek_v4_import_missing" in payload["blocked_reasons"]


def test_preflight_reports_isolated_runtime_source(monkeypatch, tmp_path):
    fake_python = tmp_path / "python"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    model_path = tmp_path / "DeepSeek-V4-Flash-2bit-DQ"
    model_path.mkdir()
    runtime_source = {
        "mlx_lm": {
            "module": "mlx_lm",
            "origin": "/tmp/mlx-lm-dsv4/mlx_lm/__init__.py",
            "package_version": "0.0.test",
            "git_root": "/tmp/mlx-lm-dsv4",
            "git_commit": "abc123",
            "git_branch": "pc/add-deepseekv4flash-model",
            "git_remote": "https://example.invalid/mlx-lm.git",
        },
        "deepseek_v4": {
            "module": d1.DEEPSEEK_V4_MODULE,
            "origin": "/tmp/mlx-lm-dsv4/mlx_lm/models/deepseek_v4.py",
            "git_root": "/tmp/mlx-lm-dsv4",
            "git_commit": "abc123",
            "git_branch": "pc/add-deepseekv4flash-model",
            "git_remote": "https://example.invalid/mlx-lm.git",
        },
    }

    monkeypatch.setattr(
        d1,
        "_check_isolated_imports",
        lambda python_path, timeout_s=20.0: {
            "ok": True,
            "returncode": 0,
            "imports": {"mlx_lm": True, d1.DEEPSEEK_V4_MODULE: True},
            "module_origins": {
                "mlx_lm": runtime_source["mlx_lm"]["origin"],
                d1.DEEPSEEK_V4_MODULE: runtime_source["deepseek_v4"]["origin"],
            },
            "package_versions": {"mlx-lm": "0.0.test"},
            "runtime_source": runtime_source,
            "stderr": "",
        },
    )

    payload = d1.run_preflight(
        isolated_python=fake_python,
        model_path=model_path,
        isolated_runtime_path=tmp_path / ".runtime-deepseek-v4-mlx",
    )

    assert payload["verdict"] == "passed"
    assert payload["runtime_source"] == runtime_source
    assert payload["mlx_lm_source"] == runtime_source["mlx_lm"]
    assert payload["import_check"]["module_origins"][d1.DEEPSEEK_V4_MODULE].endswith(
        "deepseek_v4.py"
    )


def test_dry_run_writes_15_d1_rows_with_honest_synthetic_labels(tmp_path):
    summary = d1.run_dry_run(output_dir=tmp_path, run_id="d1-test")

    assert summary["rows_written"] == 15
    assert summary["verdict"] == "passed"
    assert summary["evidence_strength"] == d1.EVIDENCE_STRENGTH

    output_path = tmp_path / "d1-test.jsonl"
    assert summary["output_path"] == str(output_path)
    records = _records(output_path)
    assert len(records) == 15
    assert {record["prompt_index"] for record in records} == {1, 2, 3, 4, 5}
    assert {record["max_tokens"] for record in records} == {128, 512, 1024}
    assert {record["gate"] for record in records} == {"D1"}
    assert {record["model_id"] for record in records} == {d1.MODEL_ID}
    assert {record["evidence_strength"] for record in records} == {
        "synthetic_dry_run_no_model_claim"
    }
    assert {record["capability_label"] for record in records} == {
        "experimental_only"
    }
    assert {record["verdict"] for record in records} == {"passed"}
    assert all(record["isolation"]["stock_runtime_untouched"] for record in records)
    assert all(record["isolation"]["default_model_surface_unchanged"] for record in records)
    assert all(record["isolation"]["ds4_c_adopted"] is False for record in records)
    assert all(
        record["child_restart_detection"]["method"]
        == "placeholder_not_measured_in_dry_run"
        for record in records
    )
    assert all(record["prompt_results"][0]["restart_observed"] is False for record in records)


def test_cli_preflight_exits_nonzero_for_impossible_isolated_runtime(tmp_path):
    code = d1.main(
        [
            "preflight",
            "--isolated-python",
            str(tmp_path / "missing-python"),
            "--model-path",
            str(tmp_path / "missing-model"),
        ]
    )

    assert code == 1


def test_real_runner_command_uses_isolated_python_and_repo_pythonpath():
    isolated_python = Path("/tmp/deepseek-venv/bin/python")

    assert d1._runner_command(isolated_python) == [
        str(isolated_python),
        "-m",
        "owlmlx.runtime.mlx_lm_runner",
    ]
    env = d1._runner_env(base_env={"PYTHONPATH": "/already-there", "X": "1"})
    assert env["PYTHONPATH"].split(":")[:2] == [str(d1.REPO_ROOT), "/already-there"]
    assert env["X"] == "1"


def test_read_json_payload_times_out_on_partial_line_without_blocking():
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import sys, time; sys.stdout.write('{'); sys.stdout.flush(); time.sleep(2)",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        try:
            d1._read_json_payload(proc, timeout_s=0.2)
        except TimeoutError as exc:
            assert "timed out waiting for child response" in str(exc)
        else:
            raise AssertionError("partial stdout line should time out")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_real_run_uses_persistent_child_protocol_with_fake_process(monkeypatch, tmp_path):
    fake_python = tmp_path / ".runtime-deepseek-v4-mlx" / "bin" / "python"
    fake_python.parent.mkdir(parents=True)
    fake_python.write_text("#!/bin/sh\n", encoding="utf-8")
    model_path = tmp_path / "DeepSeek-V4-Flash-2bit-DQ"
    model_path.mkdir()
    created: list[_FakeProcess] = []

    def passed_preflight(**kwargs: object) -> dict:
        return {
            "schema_version": "d1.preflight.v1",
            "gate": "D1",
            "runtime": "owlmlx",
            "model_id": d1.MODEL_ID,
            "preflight": "passed",
            "verdict": "passed",
            "blocked_reasons": [],
            "isolation": {},
        }

    def fake_popen(cmd: list[str], **kwargs: object) -> _FakeProcess:
        proc = _FakeProcess(cmd, **kwargs)
        created.append(proc)
        return proc

    monkeypatch.setattr(d1, "run_preflight", passed_preflight)

    summary = d1.run_real(
        output_dir=tmp_path,
        isolated_runtime_path=fake_python.parents[2],
        isolated_python=fake_python,
        model_path=model_path,
        run_id="real-fake",
        max_prompts=1,
        max_tokens_ladder=(128,),
        timeout_s=1.0,
        popen_factory=fake_popen,
    )

    assert summary["verdict"] == "passed"
    assert summary["rows_written"] == 1
    assert summary["coverage"]["expected_generation_count"] == 1
    assert summary["coverage"]["completed_generation_count"] == 1
    assert summary["coverage"]["passed_generation_count"] == 1
    assert summary["coverage"]["full_ladder_completed"] is True
    assert summary["coverage"]["prompt_token_matrix"] == {
        "p1_short_cn": {"128": "passed"}
    }
    assert summary["coverage"]["failed_pairs"] == []
    assert summary["coverage"]["missing_pairs"] == []
    assert created[0].cmd == [str(fake_python), "-m", "owlmlx.runtime.mlx_lm_runner"]
    assert created[0].kwargs["cwd"] == str(d1.REPO_ROOT)
    assert str(d1.REPO_ROOT) in created[0].kwargs["env"]["PYTHONPATH"].split(":")
    assert [item["action"] for item in created[0].stdin.writes] == [
        "load",
        "generate_messages",
        "unload",
        "ping",
        "shutdown",
    ]
    assert created[0].stdin.writes[0]["tokenizer_config"] == d1.D1_TOKENIZER_CONFIG
    assert created[0].stdin.writes[1]["messages"] == [
        {"role": "user", "content": dict(d1.PROMPTS)["p1_short_cn"]}
    ]
    assert created[0].stdin.writes[1]["params"] == {
        **d1.D1_GENERATION_DEFAULTS,
        "max_tokens": 128,
    }


def test_real_run_writes_jsonl_shape_from_fake_process(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="shape-fake",
        max_prompts=1,
        max_tokens_ladder=(128,),
        timeout_s=1.0,
        popen_factory=lambda cmd, **kwargs: _FakeProcess(cmd, **kwargs),
    )

    records = _records(tmp_path / "shape-fake.jsonl")
    assert summary["evidence_strength"] == d1.REAL_EVIDENCE_STRENGTH
    assert len(records) == 1
    record = records[0]
    assert record["schema_version"] == "d1.v1"
    assert record["record_type"] == "prompt_result"
    assert record["evidence_strength"] == d1.REAL_EVIDENCE_STRENGTH
    assert record["generation_params"] == {
        **d1.D1_GENERATION_DEFAULTS,
        "max_tokens": 128,
    }
    assert record["lifecycle"]["load_ok"] is True
    assert record["lifecycle"]["unload_ok"] is True
    assert record["lifecycle"]["clean_health_after_unload"] is True
    assert record["child_restart_detection"]["method"] == (
        "pid_stability_across_persistent_child_session"
    )
    assert record["prompt_results"][0]["restart_observed"] is False
    assert record["prompt_results"][0]["completion_chars"] > 0
    assert len(record["prompt_results"][0]["completion_sha256"]) == 64
    assert record["prompt_results"][0]["completion_preview"].startswith(
        "messages-completion-"
    )
    assert record["prompt_results"][0]["completion_tail"].startswith(
        "messages-completion-"
    )
    assert record["prompt_shape"]["surface"] == "chat_messages"
    assert record["prompt_surface"] == "messages"
    assert record["prompt_shape"]["content_chars"] > 0
    assert len(record["prompt_shape"]["messages_sha256"]) == 64
    assert record["prompt_results"][0]["generation_surface"] == "generate_messages"
    assert record["prompt_results"][0]["stop_reason"] == "unknown_non_stream_text_only"
    assert record["prompt_results"][0]["stop_reason_source"] == (
        "non_stream_generate_text_only"
    )
    assert record["prompt_results"][0]["prompt_tokens"] is None
    assert record["prompt_results"][0]["completion_tokens"] is None
    assert record["prompt_results"][0]["stop_strings"] == []
    assert record["prompt_results"][0]["stop_string_count"] == 0
    assert record["prompt_results"][0]["timing"] == {}
    assert record["metrics"]["ttft_ms_by_prompt"] == {}
    assert record["metrics"]["stream_wall_ms_by_prompt"] == {}
    assert record["verdict"] == "passed"


def test_real_run_messages_surface_uses_runner_chat_template_path(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()
    created: list[_FakeProcess] = []

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    def fake_popen(cmd: list[str], **kwargs: object) -> _FakeProcess:
        proc = _FakeProcess(cmd, **kwargs)
        created.append(proc)
        return proc

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="messages-fake",
        max_prompts=1,
        max_tokens_ladder=(128,),
        prompt_surface="messages",
        timeout_s=1.0,
        popen_factory=fake_popen,
    )

    records = _records(tmp_path / "messages-fake.jsonl")
    assert summary["prompt_surface"] == "messages"
    assert summary["verdict"] == "passed"
    assert created[0].stdin.writes[1]["action"] == "generate_messages"
    assert created[0].stdin.writes[1]["messages"] == [
        {"role": "user", "content": dict(d1.PROMPTS)["p1_short_cn"]}
    ]
    record = records[0]
    assert record["prompt_surface"] == "messages"
    assert record["prompt_shape"]["surface"] == "chat_messages"
    assert record["prompt_shape"]["message_count"] == 1
    assert record["prompt_shape"]["roles"] == ["user"]
    assert record["prompt_results"][0]["generation_surface"] == "generate_messages"
    assert record["prompt_results"][0]["completion_preview"].startswith(
        "messages-completion-"
    )


def test_real_run_coverage_reports_failed_and_missing_ladder(monkeypatch, tmp_path):
    class _FailingSecondGenerationProcess(_FakeProcess):
        def handle(self, payload: dict) -> None:
            if (
                payload["action"] in {"generate", "generate_messages"}
                and self.generation_count >= 1
            ):
                self.generation_count += 1
                self.stdout.lines.append(
                    json.dumps(
                        {
                            "ok": False,
                            "action": payload["action"],
                            "model_id": payload["model_id"],
                            "error": "synthetic generation failure",
                            "pid": self.pid,
                            "generation_count": self.generation_count,
                        }
                    )
                    + "\n"
                )
                return
            super().handle(payload)

    model_path = tmp_path / "model"
    model_path.mkdir()

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="coverage-fake",
        max_prompts=1,
        max_tokens_ladder=(128, 512, 1024),
        timeout_s=1.0,
        popen_factory=lambda cmd, **kwargs: _FailingSecondGenerationProcess(
            cmd,
            **kwargs,
        ),
    )

    assert summary["verdict"] == "failed"
    assert summary["failure_policy"] == "stop_on_first_failure"
    assert summary["coverage"]["expected_generation_count"] == 3
    assert summary["coverage"]["completed_generation_count"] == 2
    assert summary["coverage"]["passed_generation_count"] == 1
    assert summary["coverage"]["full_ladder_completed"] is False
    assert summary["coverage"]["prompt_token_matrix"] == {
        "p1_short_cn": {
            "128": "passed",
            "512": "failed",
            "1024": "not_run",
        }
    }
    assert summary["coverage"]["failed_pairs"] == [
        {"prompt_id": "p1_short_cn", "max_tokens": 512, "verdict": "failed"}
    ]
    assert summary["coverage"]["missing_pairs"] == [
        {"prompt_id": "p1_short_cn", "max_tokens": 1024}
    ]


def test_real_run_continue_on_failure_fills_diagnostic_matrix(monkeypatch, tmp_path):
    class _FailingAfterFirstGenerationProcess(_FakeProcess):
        def handle(self, payload: dict) -> None:
            if (
                payload["action"] in {"generate", "generate_messages"}
                and self.generation_count >= 1
            ):
                self.generation_count += 1
                self.stdout.lines.append(
                    json.dumps(
                        {
                            "ok": False,
                            "action": payload["action"],
                            "model_id": payload["model_id"],
                            "error": "synthetic generation failure",
                            "pid": self.pid,
                            "generation_count": self.generation_count,
                        }
                    )
                    + "\n"
                )
                return
            super().handle(payload)

    model_path = tmp_path / "model"
    model_path.mkdir()

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="coverage-continue-fake",
        max_prompts=1,
        max_tokens_ladder=(128, 512, 1024),
        continue_on_failure=True,
        timeout_s=1.0,
        popen_factory=lambda cmd, **kwargs: _FailingAfterFirstGenerationProcess(
            cmd,
            **kwargs,
        ),
    )

    records = _records(tmp_path / "coverage-continue-fake.jsonl")
    assert len(records) == 3
    assert summary["verdict"] == "failed"
    assert summary["failure_policy"] == "continue_on_failure"
    assert summary["coverage"]["expected_generation_count"] == 3
    assert summary["coverage"]["completed_generation_count"] == 3
    assert summary["coverage"]["passed_generation_count"] == 1
    assert summary["coverage"]["full_ladder_completed"] is False
    assert summary["coverage"]["prompt_token_matrix"] == {
        "p1_short_cn": {
            "128": "passed",
            "512": "failed",
            "1024": "failed",
        }
    }
    assert summary["coverage"]["missing_pairs"] == []


def test_real_run_stream_surface_records_timing_from_fake_process(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="stream-fake",
        max_prompts=1,
        max_tokens_ladder=(128,),
        generation_surface="stream",
        prompt_surface="raw",
        timeout_s=1.0,
        popen_factory=lambda cmd, **kwargs: _FakeProcess(cmd, **kwargs),
    )

    records = _records(tmp_path / "stream-fake.jsonl")
    assert summary["generation_surface"] == "stream"
    assert summary["verdict"] == "passed"
    assert len(records) == 1
    record = records[0]
    assert record["prompt_results"][0]["generation_surface"] == "stream_generate"
    assert record["prompt_results"][0]["stop_reason"] == "length"
    assert record["prompt_results"][0]["stop_reason_source"] == "stream_done"
    assert record["prompt_results"][0]["prompt_tokens"] == 7
    assert record["prompt_results"][0]["completion_tokens"] == 128
    assert record["prompt_results"][0]["stream_event_count"] == 1
    assert record["prompt_results"][0]["stream_diagnostic_count"] == 1
    assert record["prompt_results"][0]["stream_diagnostics"][0]["terminal_action"] == (
        "stream_done"
    )
    assert record["prompt_results"][0]["timing"]["stream_wall_ms"] == 25.0
    assert record["metrics"]["ttft_ms_by_prompt"] == {"p1_short_cn": 12.5}
    assert record["metrics"]["stream_wall_ms_by_prompt"] == {"p1_short_cn": 25.0}
    assert record["metrics"]["decode_tps_by_prompt"] == {"p1_short_cn": 10160.0}
    assert record["metrics"]["wall_tps_by_prompt"] == {"p1_short_cn": 5120.0}
    assert record["verdict"] == "passed"


def test_real_run_stream_messages_surface_records_rss_and_decode_metrics(
    monkeypatch,
    tmp_path,
):
    model_path = tmp_path / "model"
    model_path.mkdir()
    created: list[_FakeProcess] = []

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    def fake_popen(cmd: list[str], **kwargs: object) -> _FakeProcess:
        proc = _FakeProcess(cmd, **kwargs)
        created.append(proc)
        return proc

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="stream-messages-fake",
        max_prompts=1,
        max_tokens_ladder=(128,),
        generation_surface="stream",
        prompt_surface="messages",
        timeout_s=1.0,
        popen_factory=fake_popen,
        rss_sampler=lambda pid: 1.25,
    )

    records = _records(tmp_path / "stream-messages-fake.jsonl")
    assert summary["verdict"] == "passed"
    assert created[0].stdin.writes[1]["action"] == "stream_generate_messages"
    record = records[0]
    assert record["prompt_surface"] == "messages"
    assert record["prompt_shape"]["surface"] == "chat_messages"
    assert record["prompt_results"][0]["generation_surface"] == "stream_generate_messages"
    assert record["prompt_results"][0]["completion_preview"].startswith(
        "messages-stream-completion-"
    )
    assert record["metrics"]["ttft_ms_by_prompt"] == {"p1_short_cn": 12.5}
    assert record["metrics"]["stream_wall_ms_by_prompt"] == {"p1_short_cn": 25.0}
    assert record["metrics"]["decode_tps_by_prompt"] == {"p1_short_cn": 10160.0}
    assert record["metrics"]["wall_tps_by_prompt"] == {"p1_short_cn": 5120.0}
    assert record["metrics"]["child_rss_gb"] == 1.25
    assert record["metrics"]["rss_sample_scope"] == "child_process"
    assert record["metrics"]["rss_sample_source"] == "ps_rss_kb"
    assert record["metrics"]["rss_sample_timing"] == "after_generation_before_unload"
    assert record["metrics"]["peak_rss_gb"] == 1.25


def test_run_metrics_writes_d2_ledger_from_fake_stream(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    summary = d1.run_metrics(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="metrics-fake",
        prompt_ids=("p1_short_cn",),
        max_tokens_ladder=(128,),
        timeout_s=1.0,
        popen_factory=lambda cmd, **kwargs: _FakeProcess(cmd, **kwargs),
        rss_sampler=lambda pid: 1.5,
    )

    records = _records(tmp_path / "metrics-fake.jsonl")
    source_records = _records(
        tmp_path / "source-d1-stream" / "metrics-fake-source-d1-stream.jsonl"
    )
    assert summary["schema_version"] == "d2.metrics.run.v2"
    assert summary["verdict"] == "passed"
    assert summary["rows_written"] == 1
    assert summary["passed_rows"] == 1
    assert summary["missing_metrics"] == []
    assert summary["summary_output_path"] == str(tmp_path / "metrics-fake.summary.json")
    assert summary["metric_summary"] == {
        "ttft_ms": {"count": 1, "min": 12.5, "p50": 12.5, "max": 12.5},
        "decode_tps_after_first_token": {
            "count": 1,
            "min": 10160.0,
            "p50": 10160.0,
            "max": 10160.0,
        },
        "child_rss_gb": {"count": 1, "min": 1.5, "p50": 1.5, "max": 1.5},
    }
    assert len(source_records) == 1
    summary_record = json.loads((tmp_path / "metrics-fake.summary.json").read_text())
    assert summary_record == summary
    record = records[0]
    assert record["schema_version"] == "d2.metrics.v2"
    assert record["gate"] == "D2"
    assert record["source"]["gate"] == "D1"
    assert record["prompt_surface"] == "messages"
    assert record["generation_surface"] == "stream_generate_messages"
    assert record["metrics"]["ttft_ms"] == 12.5
    assert record["metrics"]["stream_wall_ms"] == 25.0
    assert record["metrics"]["decode_tps_after_first_token"] == 10160.0
    assert record["metrics"]["wall_tps"] == 5120.0
    assert record["metrics"]["child_rss_gb"] == 1.5
    assert record["metrics"]["rss_sample_scope"] == "child_process"
    assert record["metrics"]["rss_sample_source"] == "ps_rss_kb"
    assert record["metrics"]["rss_sample_timing"] == "after_generation_before_unload"
    assert record["metrics"]["peak_rss_gb"] == 1.5
    assert record["backend_health"]["clean_health_after_unload"] is True
    assert record["verdict"] == "passed"


def test_d2_metric_summary_reports_min_p50_max() -> None:
    rows = [
        {
            "metrics": {
                "ttft_ms": 30.0,
                "decode_tps_after_first_token": 10.0,
                "child_rss_gb": 3.0,
            }
        },
        {
            "metrics": {
                "ttft_ms": 10.0,
                "decode_tps_after_first_token": 30.0,
                "child_rss_gb": 1.0,
            }
        },
        {
            "metrics": {
                "ttft_ms": 20.0,
                "decode_tps_after_first_token": 20.0,
                "child_rss_gb": 2.0,
            }
        },
        {
            "metrics": {
                "ttft_ms": 40.0,
                "decode_tps_after_first_token": 40.0,
                "child_rss_gb": 4.0,
            }
        },
    ]

    assert d1._d2_metric_summary(rows) == {
        "ttft_ms": {"count": 4, "min": 10.0, "p50": 25.0, "max": 40.0},
        "decode_tps_after_first_token": {
            "count": 4,
            "min": 10.0,
            "p50": 25.0,
            "max": 40.0,
        },
        "child_rss_gb": {"count": 4, "min": 1.0, "p50": 2.5, "max": 4.0},
    }


def test_d2_record_falls_back_from_legacy_peak_rss_field(tmp_path):
    row = {
        "schema_version": "d1.v1",
        "record_type": "prompt_result",
        "run_id": "legacy-source",
        "prompt_index": 1,
        "prompt_id": "p1_short_cn",
        "prompt_surface": "messages",
        "max_tokens": 128,
        "generation_params": {"max_tokens": 128},
        "prompt_shape": {"surface": "chat_messages"},
        "prompt_results": [
            {
                "ok": True,
                "generation_surface": "stream_generate_messages",
                "prompt_tokens": 7,
                "completion_tokens": 128,
                "stream_event_count": 1,
                "stream_diagnostic_count": 0,
            }
        ],
        "metrics": {
            "load_time_s": 1.0,
            "ttft_ms_by_prompt": {"p1_short_cn": 2.0},
            "stream_wall_ms_by_prompt": {"p1_short_cn": 12.0},
            "decode_tps_by_prompt": {"p1_short_cn": 12.7},
            "wall_tps_by_prompt": {"p1_short_cn": 10.6},
            "peak_rss_gb": 0.75,
        },
        "lifecycle": {
            "load_ok": True,
            "generate_ok": True,
            "unload_ok": True,
            "clean_health_after_unload": True,
        },
        "child_restart_detection": {"restart_observed": False},
        "verdict": "passed",
    }

    record = d1._d2_record_from_d1_row(
        run_id="d2-legacy",
        output_path=tmp_path / "d2-legacy.jsonl",
        source_run_id="legacy-source",
        source_output_path=str(tmp_path / "legacy-source.jsonl"),
        row=row,
    )

    assert record["schema_version"] == "d2.metrics.v2"
    assert record["verdict"] == "passed"
    assert record["missing_metrics"] == []
    assert record["metrics"]["child_rss_gb"] == 0.75
    assert record["metrics"]["peak_rss_gb"] == 0.75
    assert record["metrics"]["rss_sample_scope"] == "child_process"
    assert record["metrics"]["rss_sample_source"] == "ps_rss_kb"
    assert record["metrics"]["rss_sample_timing"] == "after_generation_before_unload"


def test_d3_checkpoint_inspection_records_missing_mtp_reason(tmp_path):
    model_path = tmp_path / "model"
    _write_checkpoint_model(
        model_path,
        num_hidden_layers=2,
        num_nextn_predict_layers=1,
        weight_keys=(
            "model.layers.0.attn.wq.weight",
            "model.layers.1.attn.wq.weight",
            "lm_head.weight",
        ),
    )

    summary = d1.run_mtp_checkpoint_inspection(
        output_dir=tmp_path,
        model_path=model_path,
        adapter_path=tmp_path / "missing-adapter",
        run_id="d3-missing",
    )

    records = _records(tmp_path / "d3-missing.jsonl")
    assert summary["schema_version"] == "d3.checkpoint_inspection.run.v1"
    assert summary["verdict"] == "passed"
    assert summary["mtp_weight_status"] == "absent_or_stripped"
    assert summary["missingReason"] == d1.D3_MTP_MISSING_REASON
    record = records[0]
    assert record["schema_version"] == "d3.checkpoint_inspection.v1"
    assert record["gate"] == "D3"
    assert record["inspection"]["config_declares_nextn_predict_layers"] is True
    assert record["inspection"]["has_mtp_weight_candidates"] is False
    assert record["inspection"]["missingReason"] == d1.D3_MTP_MISSING_REASON
    assert record["capability_conclusion"] == "mtp_checkpoint_not_available"
    assert record["weight_index_summary"]["weight_key_count"] == 3
    assert record["read_errors"] == []


def test_d3_checkpoint_inspection_detects_mtp_candidate_keys(tmp_path):
    model_path = tmp_path / "model"
    _write_checkpoint_model(
        model_path,
        num_hidden_layers=2,
        num_nextn_predict_layers=1,
        weight_keys=(
            "model.layers.0.attn.wq.weight",
            "model.layers.2.attn.wq.weight",
            "mtp.fc.weight",
        ),
    )

    summary = d1.run_mtp_checkpoint_inspection(
        output_dir=tmp_path,
        model_path=model_path,
        adapter_path=tmp_path / "missing-adapter",
        run_id="d3-present",
    )

    record = _records(tmp_path / "d3-present.jsonl")[0]
    assert summary["verdict"] == "passed"
    assert summary["mtp_weight_status"] == "present"
    assert summary["missingReason"] is None
    assert record["inspection"]["has_mtp_weight_candidates"] is True
    assert record["weight_index_summary"]["matched_mtp_weight_key_count"] == 1
    assert record["weight_index_summary"]["extra_layer_key_count"] == 1
    assert record["capability_conclusion"] == "mtp_checkpoint_candidate_present"


def test_real_run_stream_timeout_writes_failed_row_and_skips_unload(
    monkeypatch,
    tmp_path,
):
    model_path = tmp_path / "model"
    model_path.mkdir()
    created: list[_FakeProcess] = []

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    def fake_popen(cmd: list[str], **kwargs: object) -> _FakeProcess:
        proc = _FakeProcess(cmd, **kwargs)
        created.append(proc)
        return proc

    def fake_stream(proc: _FakeProcess, request: dict, *, timeout_s: float) -> dict:
        return {
            "ok": False,
            "action": request["action"],
            "text": "",
            "error": "timed out waiting for child response",
            "pid": proc.pid,
            "finish_reason": "stream_timeout",
            "stream_timeout": True,
            "timeout_s": timeout_s,
            "stream_event_count": 0,
            "stream_diagnostic_count": 0,
            "stream_diagnostics": [],
        }

    monkeypatch.setattr(d1, "_child_stream_generate", fake_stream)

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="stream-timeout-fake",
        max_prompts=1,
        max_tokens_ladder=(128,),
        generation_surface="stream",
        prompt_surface="messages",
        timeout_s=1.0,
        popen_factory=fake_popen,
    )

    records = _records(tmp_path / "stream-timeout-fake.jsonl")
    assert summary["verdict"] == "failed"
    assert summary["error"] == "stream generation timed out before terminal payload"
    assert [item["action"] for item in created[0].stdin.writes] == [
        "load",
    ]
    assert created[0].returncode == -15
    record = records[0]
    assert record["prompt_results"][0]["generation_surface"] == (
        "stream_generate_messages"
    )
    assert record["prompt_results"][0]["error"] == (
        "timed out waiting for child response"
    )
    assert record["prompt_results"][0]["stream_timeout"] is True
    assert record["prompt_results"][0]["timeout_s"] == 1.0
    assert record["lifecycle"]["unload_ok"] is False
    assert record["lifecycle"]["clean_health_after_unload"] is False
    assert record["verdict"] == "failed"


def test_repetition_diagnostics_report_repeated_window() -> None:
    repeated = "0123456789012345678901234567890123456789" * 5

    payload = d1._repetition_diagnostics(repeated)

    assert payload["repetition_flag"] is True
    assert payload["method"] == "fixed_window_repeat_v1"
    assert payload["max_repeated_window_count"] == 5
    assert len(payload["repeated_window_sha256"]) == 64
    assert payload["repeated_window_preview"].startswith("0123456789")


def _passed_preflight() -> dict:
    return {
        "schema_version": "d1.preflight.v1",
        "gate": "D1",
        "runtime": "owlmlx",
        "model_id": d1.MODEL_ID,
        "preflight": "passed",
        "verdict": "passed",
        "blocked_reasons": [],
        "isolation": {},
    }


def _direct_result(text: str) -> dict:
    return {
        "ok": True,
        "action": "direct_generate",
        "surface": "direct_mlx_lm_generate",
        "text": text,
        "finish_reason": "stop",
        "pid": 111,
        "load_time_s": 0.1,
        "generate_time_s": 0.2,
    }


def _runner_func_for_text(text: str):
    def fake_runner(**kwargs: object) -> dict:
        output_dir = Path(kwargs["output_dir"])
        run_id = str(kwargs["run_id"])
        prompt_id = str(kwargs["prompt_ids"][0])
        max_tokens = int(kwargs["max_tokens_ladder"][0])
        path = output_dir / f"{run_id}.jsonl"
        repetition = d1._repetition_diagnostics(text)
        row = {
            "schema_version": "d1.v1",
            "record_type": "prompt_result",
            "run_id": run_id,
            "prompt_id": prompt_id,
            "max_tokens": max_tokens,
            "prompt_results": [
                {
                    "ok": True,
                    "completion_chars": len(text),
                    **d1._completion_observation(text),
                    "stop_reason": "unknown_non_stream_text_only",
                    "repetition_flag": repetition["repetition_flag"],
                    "repetition_diagnostics": repetition,
                    "child_pid": 222,
                    "timing": {},
                }
            ],
            "lifecycle": {
                "load_ok": True,
                "unload_ok": True,
                "clean_health_after_unload": True,
            },
            "verdict": "failed" if repetition["repetition_flag"] else "passed",
        }
        d1._append_jsonl(path, [row])
        return {
            "schema_version": "d1.run.v1",
            "run_id": run_id,
            "output_path": str(path),
            "rows_written": 1,
            "verdict": row["verdict"],
            "lifecycle": row["lifecycle"],
            "coverage": {},
        }

    return fake_runner


def test_direct_vs_runner_compare_classifies_shared_repetition(monkeypatch, tmp_path):
    repeated = "0123456789012345678901234567890123456789" * 5
    monkeypatch.setattr(d1, "run_preflight", lambda **kwargs: _passed_preflight())

    summary = d1.run_direct_vs_runner(
        output_dir=tmp_path,
        run_id="compare-shared",
        prompt_id="p1_short_cn",
        max_tokens=1024,
        direct_func=lambda **kwargs: _direct_result(repeated),
        runner_func=_runner_func_for_text(repeated),
    )

    records = _records(tmp_path / "compare-shared.jsonl")
    assert len(records) == 1
    assert summary["schema_version"] == "d1.compare.v1"
    assert summary["classification"] == "adapter_or_artifact_likely"
    assert summary["verdict"] == "diagnostic_failed"
    assert summary["surfaces"]["direct_mlx_lm_generate"]["repetition_flag"] is True
    assert summary["surfaces"]["owlmlx_runner_generate"]["repetition_flag"] is True
    assert Path(summary["runner_output_path"]).name == "compare-shared-runner.jsonl"


def test_direct_vs_runner_compare_flags_runner_call_path(monkeypatch, tmp_path):
    repeated = "abcdefghijabcdefghijabcdefghijabcdefghij" * 5
    monkeypatch.setattr(d1, "run_preflight", lambda **kwargs: _passed_preflight())

    summary = d1.run_direct_vs_runner(
        output_dir=tmp_path,
        run_id="compare-runner-suspect",
        prompt_id="p1_short_cn",
        max_tokens=1024,
        direct_func=lambda **kwargs: _direct_result("short clean completion"),
        runner_func=_runner_func_for_text(repeated),
    )

    assert summary["classification"] == "runner_call_path_suspect"
    assert summary["surfaces"]["direct_mlx_lm_generate"]["repetition_flag"] is False
    assert summary["surfaces"]["owlmlx_runner_generate"]["repetition_flag"] is True


def test_direct_vs_runner_compare_flags_runner_masking(monkeypatch, tmp_path):
    repeated = "zyxwvutsrqponmlkjihgfedcba98765432101234" * 5
    monkeypatch.setattr(d1, "run_preflight", lambda **kwargs: _passed_preflight())

    summary = d1.run_direct_vs_runner(
        output_dir=tmp_path,
        run_id="compare-runner-masks",
        prompt_id="p1_short_cn",
        max_tokens=1024,
        direct_func=lambda **kwargs: _direct_result(repeated),
        runner_func=_runner_func_for_text("short clean completion"),
    )

    assert summary["classification"] == "runner_masks_direct_repetition"
    assert summary["surfaces"]["direct_mlx_lm_generate"]["repetition_flag"] is True
    assert summary["surfaces"]["owlmlx_runner_generate"]["repetition_flag"] is False


def test_real_run_prompt_id_and_stop_strings_pass_through(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()
    created: list[_FakeProcess] = []

    monkeypatch.setattr(
        d1,
        "run_preflight",
        lambda **kwargs: {"verdict": "passed", "preflight": "passed"},
    )

    def fake_popen(cmd: list[str], **kwargs: object) -> _FakeProcess:
        proc = _FakeProcess(cmd, **kwargs)
        created.append(proc)
        return proc

    summary = d1.run_real(
        output_dir=tmp_path,
        model_path=model_path,
        run_id="prompt-stop-fake",
        prompt_ids=("p5_stop_marker",),
        max_tokens_ladder=(1024,),
        generation_overrides={"stop": ["<END>"]},
        prompt_surface="raw",
        timeout_s=1.0,
        popen_factory=fake_popen,
    )

    records = _records(tmp_path / "prompt-stop-fake.jsonl")
    assert summary["verdict"] == "passed"
    assert summary["prompt_count"] == 1
    assert records[0]["prompt_id"] == "p5_stop_marker"
    assert records[0]["max_tokens"] == 1024
    assert records[0]["generation_params"]["stop"] == ["<END>"]
    assert records[0]["prompt_results"][0]["stop_strings"] == ["<END>"]
    assert records[0]["prompt_results"][0]["stop_string_count"] == 1
    assert created[0].stdin.writes[1]["prompt"] == dict(d1.PROMPTS)["p5_stop_marker"]
    assert created[0].stdin.writes[1]["params"]["stop"] == ["<END>"]


def test_cli_run_sampler_overrides_are_forwarded(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_real(**kwargs: object) -> dict:
        captured.update(kwargs)
        return {
            "schema_version": "d1.run.v1",
            "gate": "D1",
            "runtime": "owlmlx",
            "model_id": d1.MODEL_ID,
            "verdict": "failed",
        }

    monkeypatch.setattr(d1, "run_real", fake_run_real)

    code = d1.main(
        [
            "run",
            "--output-dir",
            str(tmp_path),
            "--prompt-id",
            "p1_short_cn",
            "--max-tokens",
            "1024",
            "--temp",
            "0.2",
            "--top-p",
            "0.9",
            "--min-p",
            "0.05",
            "--top-k",
            "40",
            "--prompt-surface",
            "messages",
        ]
    )

    assert code == 1
    assert captured["prompt_surface"] == "messages"
    assert captured["generation_overrides"] == {
        "max_kv_size": d1.D1_GENERATION_DEFAULTS["max_kv_size"],
        "kv_bits": None,
        "kv_group_size": None,
        "temperature": 0.2,
        "top_p": 0.9,
        "min_p": 0.05,
        "top_k": 40,
        "stop": None,
    }


def test_cli_compare_sampler_overrides_are_forwarded(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_compare(**kwargs: object) -> dict:
        captured.update(kwargs)
        return {
            "schema_version": "d1.compare.v1",
            "gate": "D1",
            "runtime": "owlmlx",
            "model_id": d1.MODEL_ID,
            "verdict": "diagnostic_failed",
        }

    monkeypatch.setattr(d1, "run_direct_vs_runner", fake_compare)

    code = d1.main(
        [
            "compare",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "compare-cli",
            "--prompt-id",
            "p1_short_cn",
            "--max-tokens",
            "1024",
            "--max-kv-size",
            "2048",
            "--temp",
            "0.2",
            "--top-p",
            "0.9",
            "--top-k",
            "40",
            "--stop",
            "<END>",
        ]
    )

    assert code == 1
    assert captured["run_id"] == "compare-cli"
    assert captured["prompt_id"] == "p1_short_cn"
    assert captured["max_tokens"] == 1024
    assert captured["generation_overrides"] == {
        "max_kv_size": 2048,
        "kv_bits": None,
        "kv_group_size": None,
        "temperature": 0.2,
        "top_p": 0.9,
        "min_p": None,
        "top_k": 40,
        "stop": ["<END>"],
    }


def test_cli_metrics_sampler_overrides_are_forwarded(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_metrics(**kwargs: object) -> dict:
        captured.update(kwargs)
        return {
            "schema_version": "d2.metrics.run.v2",
            "gate": "D2",
            "runtime": "owlmlx",
            "model_id": d1.MODEL_ID,
            "verdict": "passed",
        }

    monkeypatch.setattr(d1, "run_metrics", fake_metrics)

    code = d1.main(
        [
            "metrics",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "metrics-cli",
            "--prompt-id",
            "p1_short_cn",
            "--max-tokens",
            "128",
            "512",
            "--max-tokens",
            "1024",
            "--max-kv-size",
            "2048",
            "--temp",
            "0.1",
            "--top-p",
            "0.8",
            "--top-k",
            "20",
        ]
    )

    assert code == 0
    assert captured["run_id"] == "metrics-cli"
    assert captured["prompt_ids"] == ("p1_short_cn",)
    assert captured["max_tokens_ladder"] == (128, 512, 1024)
    assert captured["prompt_surface"] == "messages"
    assert captured["generation_overrides"] == {
        "max_kv_size": 2048,
        "kv_bits": None,
        "kv_group_size": None,
        "temperature": 0.1,
        "top_p": 0.8,
        "min_p": None,
        "top_k": 20,
        "stop": None,
    }


def test_cli_checkpoint_inspect_forwards_paths(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_inspect(**kwargs: object) -> dict:
        captured.update(kwargs)
        return {
            "schema_version": "d3.checkpoint_inspection.run.v1",
            "gate": "D3",
            "runtime": "owlmlx",
            "model_id": d1.MODEL_ID,
            "verdict": "passed",
        }

    monkeypatch.setattr(d1, "run_mtp_checkpoint_inspection", fake_inspect)

    code = d1.main(
        [
            "checkpoint-inspect",
            "--output-dir",
            str(tmp_path / "out"),
            "--model-path",
            str(tmp_path / "model"),
            "--adapter-path",
            str(tmp_path / "adapter"),
            "--run-id",
            "d3-cli",
        ]
    )

    assert code == 0
    assert captured["run_id"] == "d3-cli"
    assert captured["output_dir"] == tmp_path / "out"
    assert captured["model_path"] == tmp_path / "model"
    assert captured["adapter_path"] == tmp_path / "adapter"


def test_cli_dry_run_exits_zero_and_writes_jsonl(tmp_path):
    code = d1.main(["dry-run", "--output-dir", str(tmp_path), "--run-id", "cli-dry"])

    assert code == 0
    records = _records(tmp_path / "cli-dry.jsonl")
    assert len(records) == 15


def test_subprocess_cli_preflight_nonzero_and_dry_run_zero(tmp_path):
    script = Path(d1.__file__)
    missing = tmp_path / "missing-python"
    preflight = subprocess.run(
        [
            sys.executable,
            str(script),
            "preflight",
            "--isolated-python",
            str(missing),
            "--model-path",
            str(tmp_path / "missing-model"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert preflight.returncode == 1
    assert json.loads(preflight.stdout)["verdict"] == "blocked"

    dry = subprocess.run(
        [
            sys.executable,
            str(script),
            "fake-run",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "subprocess-dry",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert dry.returncode == 0
    assert json.loads(dry.stdout)["rows_written"] == 15
