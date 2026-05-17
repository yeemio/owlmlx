from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.bench import deepseek_v4_d1_repeatability as d1


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


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
        elif action == "generate":
            self.generation_count += 1
            response = {
                "ok": True,
                "action": "generate",
                "model_id": payload["model_id"],
                "text": f"completion-{self.generation_count}",
                "finish_reason": "stop",
                "pid": self.pid,
                "generation_count": self.generation_count,
            }
        elif action == "stream_generate":
            self.generation_count += 1
            text = f"completion-{self.generation_count}"
            token = {
                "ok": True,
                "action": "stream_event",
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
                "action": "stream_done",
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
                "terminal_action": "stream_done",
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
        "generate",
        "unload",
        "ping",
        "shutdown",
    ]
    assert created[0].stdin.writes[0]["tokenizer_config"] == d1.D1_TOKENIZER_CONFIG
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
    assert record["prompt_results"][0]["completion_preview"].startswith("completion-")
    assert record["prompt_results"][0]["completion_tail"].startswith("completion-")
    assert record["prompt_shape"]["surface"] == "raw_text"
    assert record["prompt_shape"]["prompt_chars"] > 0
    assert len(record["prompt_shape"]["prompt_sha256"]) == 64
    assert record["prompt_results"][0]["generation_surface"] == "generate"
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


def test_real_run_coverage_reports_failed_and_missing_ladder(monkeypatch, tmp_path):
    class _FailingSecondGenerationProcess(_FakeProcess):
        def handle(self, payload: dict) -> None:
            if payload["action"] == "generate" and self.generation_count >= 1:
                self.generation_count += 1
                self.stdout.lines.append(
                    json.dumps(
                        {
                            "ok": False,
                            "action": "generate",
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
    assert record["verdict"] == "passed"


def test_repetition_diagnostics_report_repeated_window() -> None:
    repeated = "0123456789012345678901234567890123456789" * 5

    payload = d1._repetition_diagnostics(repeated)

    assert payload["repetition_flag"] is True
    assert payload["method"] == "fixed_window_repeat_v1"
    assert payload["max_repeated_window_count"] == 5
    assert len(payload["repeated_window_sha256"]) == 64
    assert payload["repeated_window_preview"].startswith("0123456789")


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
