from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.bench import deepseek_v4_d1_repeatability as d1


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


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
