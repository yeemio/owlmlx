"""Tests for the measured comparative-evidence runner (release floor 3.5B).

Unit tests use deterministic fake commands (``python3 -c "..."``) so the
runner is exercised without requiring 58G live model weights. The live
same-host measured run is left to a downstream Codex review lane.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from owlmlx.comparative_evidence_ledger import ComparativeEvidenceLedger
from owlmlx.comparative_evidence_runner import (
    RuntimeRunnerConfig,
    WorkloadInputs,
    aggregate_runtime,
    aggregate_to_record_runtime,
    compute_verdict,
    execute_attempt,
    load_runner_config_file,
)
from owlmlx.comparative_evidence_schema import (
    BANNED_VERDICT_VOCABULARY,
    SchemaValidationError,
    validate_comparative_evidence_record,
)
from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "runtime_comparative_evidence.py"


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def _workload(prompt: str = "Reply with exactly OK.") -> WorkloadInputs:
    return WorkloadInputs(
        prompt=prompt,
        decode_max_tokens=2,
        decode_temperature=0.0,
        model_id="qwen3-0.6b",
        model_path="/tmp/fake-model-path",
        model_quantization="q4",
        prompt_set_hash="sha256:test",
        serving_budget_bytes=6 * 1024 * 1024 * 1024,
        workload_class="single_prompt_short",
    )


def _fake_success_command(stdout_token: str = "OK") -> tuple[str, ...]:
    """A deterministic fake command that emits one stdout chunk and exits 0."""

    program = textwrap.dedent(
        f"""
        import sys, time
        # tiny pause so first-token latency is observably non-zero
        time.sleep(0.02)
        sys.stdout.write({stdout_token!r} + "\\n")
        sys.stdout.flush()
        sys.exit(0)
        """
    )
    return (sys.executable, "-c", program)


def _fake_failure_command(message: str = "boom") -> tuple[str, ...]:
    program = textwrap.dedent(
        f"""
        import sys
        sys.stderr.write({message!r} + "\\n")
        sys.exit(2)
        """
    )
    return (sys.executable, "-c", program)


def _fake_silent_command() -> tuple[str, ...]:
    """A command that exits 0 but never emits stdout (first-token unobservable)."""

    program = "import sys; sys.exit(0)"
    return (sys.executable, "-c", program)


def _runner_cfg(
    *,
    runtime_id: str,
    runtime_version: str,
    argv: tuple[str, ...],
    timeout_s: float = 30.0,
) -> RuntimeRunnerConfig:
    return RuntimeRunnerConfig(
        runtime_id=runtime_id,
        runtime_version=runtime_version,
        argv=argv,
        timeout_s=timeout_s,
        tokens_method="max_tokens",
    )


# ---------------------------------------------------------------------------
# CLI shape
# ---------------------------------------------------------------------------


def test_cli_exposes_run_measured_short_prompt_subcommand() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "run-measured-short-prompt" in completed.stdout


def test_cli_run_measured_short_prompt_help_exposes_required_flags() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "run-measured-short-prompt",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    for flag in (
        "--evidence-dir",
        "--runner-config",
        "--host-class",
        "--model-id",
        "--model-path",
        "--prompt",
        "--prompt-set-hash",
        "--decode-max-tokens",
        "--decode-temperature",
        "--serving-budget-bytes",
        "--repeats",
    ):
        assert flag in completed.stdout, f"missing CLI flag {flag}"


# ---------------------------------------------------------------------------
# execute_attempt + aggregate_runtime + compute_verdict
# ---------------------------------------------------------------------------


def test_execute_attempt_records_first_token_latency_for_fake_success(tmp_path) -> None:
    cfg = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_success_command(),
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is True
    assert result.failure_cause is None
    assert result.first_token_latency_ms is not None
    assert result.first_token_latency_ms > 0.0
    assert result.wall_clock_ms >= result.first_token_latency_ms
    assert result.generated_token_count == 2  # decode_max_tokens
    assert result.throughput_tokens_per_second is not None
    assert result.throughput_tokens_per_second > 0.0
    assert Path(result.stdout_path).read_text(encoding="utf-8").strip() == "OK"
    assert Path(result.rss_samples_path).exists()


def test_execute_attempt_marks_silent_command_first_token_unobservable(tmp_path) -> None:
    cfg = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_silent_command(),
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is False
    assert result.failure_cause == "first_token_latency_unobservable"
    assert result.first_token_latency_ms is None


def test_execute_attempt_marks_non_zero_exit_as_failure(tmp_path) -> None:
    cfg = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_failure_command(),
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is False
    assert result.failure_cause == "harness_runtime_invocation_error_non_zero_exit"
    assert result.return_code == 2


def test_execute_attempt_handles_spawn_failure(tmp_path) -> None:
    cfg = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=("/no/such/binary/owlmlx-fake-runner",),
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is False
    assert result.failure_cause == "harness_runtime_invocation_error_spawn_failed"


def test_aggregate_runtime_aggregates_two_successes(tmp_path) -> None:
    cfg = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_success_command(),
    )
    attempts = [
        execute_attempt(
            runtime_config=cfg,
            workload=_workload(),
            attempt_index=i + 1,
            artifact_dir=tmp_path,
        )
        for i in range(2)
    ]
    aggregate = aggregate_runtime(runtime_config=cfg, attempts=attempts)
    assert aggregate.completed_request_count == 2
    assert aggregate.failure_count == 0
    assert aggregate.failure_causes == ()
    assert aggregate.wall_clock_ms > 0.0
    assert aggregate.first_token_latency_ms > 0.0
    assert aggregate.throughput_tokens_per_second > 0.0


def test_compute_verdict_emits_measured_when_all_attempts_succeed(tmp_path) -> None:
    cfg_owl = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_success_command("OWL"),
    )
    cfg_ref = _runner_cfg(
        runtime_id="omlx",
        runtime_version="0.3.5",
        argv=_fake_success_command("REF"),
    )
    aggs = []
    for cfg in (cfg_owl, cfg_ref):
        attempts = [
            execute_attempt(
                runtime_config=cfg,
                workload=_workload(),
                attempt_index=i + 1,
                artifact_dir=tmp_path,
            )
            for i in range(2)
        ]
        aggs.append(aggregate_runtime(runtime_config=cfg, attempts=attempts))
    grade, text = compute_verdict(
        aggregates=aggs,
        expected_repeats=2,
        workload=_workload(),
        host_class="darwin-arm64-test-host",
    )
    assert grade == "measured"
    assert text.startswith("measured: owlmlx tokens_per_second")
    assert "vs omlx tokens_per_second" in text


def test_compute_verdict_emits_inconclusive_when_one_attempt_fails(tmp_path) -> None:
    cfg_owl = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_success_command("OWL"),
    )
    cfg_ref = _runner_cfg(
        runtime_id="omlx",
        runtime_version="0.3.5",
        argv=_fake_success_command("REF"),
    )
    fake_failure = _runner_cfg(
        runtime_id="omlx",
        runtime_version="0.3.5",
        argv=_fake_failure_command(),
    )
    owl_attempts = [
        execute_attempt(
            runtime_config=cfg_owl,
            workload=_workload(),
            attempt_index=i + 1,
            artifact_dir=tmp_path,
        )
        for i in range(2)
    ]
    ref_attempts = [
        execute_attempt(
            runtime_config=cfg_ref,
            workload=_workload(),
            attempt_index=1,
            artifact_dir=tmp_path,
        ),
        execute_attempt(
            runtime_config=fake_failure,
            workload=_workload(),
            attempt_index=2,
            artifact_dir=tmp_path,
        ),
    ]
    aggs = [
        aggregate_runtime(runtime_config=cfg_owl, attempts=owl_attempts),
        aggregate_runtime(runtime_config=cfg_ref, attempts=ref_attempts),
    ]
    grade, text = compute_verdict(
        aggregates=aggs,
        expected_repeats=2,
        workload=_workload(),
        host_class="darwin-arm64-test-host",
    )
    assert grade == "inconclusive"
    assert text.startswith("inconclusive:")


def test_compute_verdict_emits_rejected_when_runtime_has_zero_successes(tmp_path) -> None:
    cfg_owl = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_success_command("OWL"),
    )
    cfg_ref = _runner_cfg(
        runtime_id="omlx",
        runtime_version="0.3.5",
        argv=_fake_failure_command("ref-fail"),
    )
    owl_attempts = [
        execute_attempt(
            runtime_config=cfg_owl,
            workload=_workload(),
            attempt_index=i + 1,
            artifact_dir=tmp_path,
        )
        for i in range(2)
    ]
    ref_attempts = [
        execute_attempt(
            runtime_config=cfg_ref,
            workload=_workload(),
            attempt_index=i + 1,
            artifact_dir=tmp_path,
        )
        for i in range(2)
    ]
    aggs = [
        aggregate_runtime(runtime_config=cfg_owl, attempts=owl_attempts),
        aggregate_runtime(runtime_config=cfg_ref, attempts=ref_attempts),
    ]
    grade, text = compute_verdict(
        aggregates=aggs,
        expected_repeats=2,
        workload=_workload(),
        host_class="darwin-arm64-test-host",
    )
    assert grade == "rejected"
    assert text.startswith("rejected: omlx_runtime_invocation_failed")


# ---------------------------------------------------------------------------
# Banned vocabulary stays rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("banned_word", BANNED_VERDICT_VOCABULARY)
def test_banned_verdict_vocabulary_remains_rejected(banned_word: str) -> None:
    record = {
        "surface": "owlmlx.comparative_evidence_record",
        "version": "v1",
        "recorded_at": "2026-04-27T00:00:00Z",
        "evidence_pointer": "files/evidence/test/manifest.json",
        "host_class": "darwin-arm64-test-host",
        "workload_class": "single_prompt_short",
        "workload_invariants": {
            "model_id": "qwen3-0.6b",
            "model_quantization": "q4",
            "decode_max_tokens": 2,
            "decode_temperature": 0.0,
            "prompt_set_hash": "sha256:test",
            "serving_budget_bytes": 1,
        },
        "runtimes": [
            {
                "runtime_id": "owlmlx",
                "runtime_version": "0.0.0-runtime7",
                "measurement": {
                    "throughput_tokens_per_second": 1.0,
                    "first_token_latency_ms": 1.0,
                    "peak_resident_set_bytes": 1,
                    "wall_clock_ms": 1.0,
                    "completed_request_count": 1,
                    "failure_count": 0,
                },
            },
            {
                "runtime_id": "omlx",
                "runtime_version": "0.3.5",
                "measurement": {
                    "throughput_tokens_per_second": 1.0,
                    "first_token_latency_ms": 1.0,
                    "peak_resident_set_bytes": 1,
                    "wall_clock_ms": 1.0,
                    "completed_request_count": 1,
                    "failure_count": 0,
                },
            },
        ],
        "verdict_text": f"measured: owlmlx {banned_word} omlx",
        "verdict_grade": "measured",
    }
    with pytest.raises(SchemaValidationError):
        validate_comparative_evidence_record(record)


# ---------------------------------------------------------------------------
# Runner config loading
# ---------------------------------------------------------------------------


def test_load_runner_config_file_round_trip(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    config_path.write_text(
        json.dumps(
            {
                "owlmlx": {
                    "runtime_version": "0.0.0-runtime7",
                    "argv": ["python3", "-c", "print('owl')"],
                    "tokens_method": "max_tokens",
                    "timeout_s": 10.0,
                },
                "reference": {
                    "runtime_id": "omlx",
                    "runtime_version": "0.3.5",
                    "argv": ["python3", "-c", "print('ref')"],
                    "tokens_method": "max_tokens",
                    "timeout_s": 10.0,
                },
            }
        ),
        encoding="utf-8",
    )
    owl, ref = load_runner_config_file(config_path)
    assert owl.runtime_id == "owlmlx"
    assert owl.runtime_version == "0.0.0-runtime7"
    assert ref.runtime_id == "omlx"
    assert ref.runtime_version == "0.3.5"


def test_load_runner_config_file_rejects_missing_argv(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    config_path.write_text(
        json.dumps(
            {
                "owlmlx": {
                    "runtime_version": "x",
                    "argv": [],
                },
                "reference": {
                    "runtime_id": "omlx",
                    "runtime_version": "0.3.5",
                    "argv": ["python3"],
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_runner_config_file(config_path)


# ---------------------------------------------------------------------------
# End-to-end CLI invocation: measured + inconclusive
# ---------------------------------------------------------------------------


def _write_runner_config(
    config_path: Path,
    *,
    owlmlx_argv: tuple[str, ...],
    reference_argv: tuple[str, ...],
    reference_id: str = "omlx",
) -> None:
    config_path.write_text(
        json.dumps(
            {
                "owlmlx": {
                    "runtime_version": "0.0.0-runtime7-test",
                    "argv": list(owlmlx_argv),
                    "tokens_method": "max_tokens",
                    "timeout_s": 30.0,
                },
                "reference": {
                    "runtime_id": reference_id,
                    "runtime_version": "0.3.5-test",
                    "argv": list(reference_argv),
                    "tokens_method": "max_tokens",
                    "timeout_s": 30.0,
                },
            }
        ),
        encoding="utf-8",
    )


def _common_cli_args(
    *,
    ledger_path: Path,
    config_path: Path,
    evidence_dir: Path,
    repeats: int = 2,
) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT_PATH),
        "--ledger-path",
        str(ledger_path),
        "run-measured-short-prompt",
        "--evidence-dir",
        str(evidence_dir),
        "--runner-config",
        str(config_path),
        "--host-class",
        "darwin-arm64-test-host",
        "--workload-class",
        "single_prompt_short",
        "--model-id",
        "qwen3-0.6b",
        "--model-path",
        "/tmp/fake-model-path",
        "--model-quantization",
        "q4",
        "--prompt",
        "Reply with exactly OK.",
        "--prompt-set-hash",
        "sha256:test",
        "--decode-max-tokens",
        "2",
        "--decode-temperature",
        "0.0",
        "--serving-budget-bytes",
        "6442450944",
        "--repeats",
        str(repeats),
    ]


def test_cli_run_measured_short_prompt_emits_measured_record_with_fake_commands(
    tmp_path,
) -> None:
    config_path = tmp_path / "runner.json"
    _write_runner_config(
        config_path,
        owlmlx_argv=_fake_success_command("OWL"),
        reference_argv=_fake_success_command("REF"),
    )
    ledger_path = tmp_path / "ledger.jsonl"
    evidence_dir = tmp_path / "evidence"

    completed = subprocess.run(
        _common_cli_args(
            ledger_path=ledger_path,
            config_path=config_path,
            evidence_dir=evidence_dir,
        ),
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["verdict_grade"] == "measured"
    assert payload["verdict_text"].startswith("measured: owlmlx tokens_per_second")
    runtime_ids = [r["runtime_id"] for r in payload["runtimes"]]
    assert runtime_ids == ["owlmlx", "omlx"]
    for runtime in payload["runtimes"]:
        m = runtime["measurement"]
        assert m["completed_request_count"] == 2
        assert m["failure_count"] == 0
        assert m["throughput_tokens_per_second"] > 0.0
        assert m["first_token_latency_ms"] > 0.0
        assert m["wall_clock_ms"] > 0.0
        assert m["peak_resident_set_bytes"] >= 0
    assert (evidence_dir / "manifest.json").exists()
    assert (evidence_dir / "commands.json").exists()
    assert (evidence_dir / "summary.md").exists()
    # per-attempt artifacts
    assert (evidence_dir / "owlmlx_attempt1.stdout.txt").read_text(encoding="utf-8").strip() == "OWL"
    assert (evidence_dir / "owlmlx_attempt2.stdout.txt").exists()
    assert (evidence_dir / "omlx_attempt1.stdout.txt").exists()
    assert (evidence_dir / "omlx_attempt2.stdout.txt").exists()
    # ledger contains exactly one record matching the printed payload
    ledger = ComparativeEvidenceLedger(ledger_path)
    assert len(ledger.history()) == 1
    assert ledger.latest()["verdict_grade"] == "measured"


def test_cli_run_measured_short_prompt_emits_inconclusive_when_reference_partially_fails(
    tmp_path,
) -> None:
    """When one runtime succeeds twice and the other has at least one success
    plus at least one failure, verdict_grade must be inconclusive — never a fake
    measured record. The ledger must still receive the validated v1 record.
    """

    # Use a flaky reference: succeeds attempt 1 (writes a marker file) and fails
    # subsequently (because the marker file already exists). This isolates a
    # cause without invoking external network state.
    marker_path = tmp_path / "ref_marker"
    flaky_program = textwrap.dedent(
        f"""
        import os, sys, time
        marker = {str(marker_path)!r}
        if os.path.exists(marker):
            sys.stderr.write('flaky_failure\\n')
            sys.exit(3)
        with open(marker, 'w') as f:
            f.write('1')
        time.sleep(0.02)
        sys.stdout.write('REF\\n')
        sys.stdout.flush()
        sys.exit(0)
        """
    )
    config_path = tmp_path / "runner.json"
    _write_runner_config(
        config_path,
        owlmlx_argv=_fake_success_command("OWL"),
        reference_argv=(sys.executable, "-c", flaky_program),
    )
    ledger_path = tmp_path / "ledger.jsonl"
    evidence_dir = tmp_path / "evidence"

    completed = subprocess.run(
        _common_cli_args(
            ledger_path=ledger_path,
            config_path=config_path,
            evidence_dir=evidence_dir,
        ),
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["verdict_grade"] == "inconclusive"
    assert payload["verdict_text"].startswith("inconclusive:")
    # owlmlx still succeeded, so it must report 2 completions and zero failures
    owl = payload["runtimes"][0]
    assert owl["runtime_id"] == "owlmlx"
    assert owl["measurement"]["completed_request_count"] == 2
    assert owl["measurement"]["failure_count"] == 0
    # reference partially failed
    ref = payload["runtimes"][1]
    assert ref["runtime_id"] == "omlx"
    assert ref["measurement"]["failure_count"] >= 1
    assert ref["measurement"]["completed_request_count"] >= 1
    assert "failure_causes" in ref["measurement"]


def test_cli_run_measured_short_prompt_emits_rejected_when_reference_zero_success(
    tmp_path,
) -> None:
    config_path = tmp_path / "runner.json"
    _write_runner_config(
        config_path,
        owlmlx_argv=_fake_success_command("OWL"),
        reference_argv=_fake_failure_command(),
    )
    ledger_path = tmp_path / "ledger.jsonl"
    evidence_dir = tmp_path / "evidence"

    completed = subprocess.run(
        _common_cli_args(
            ledger_path=ledger_path,
            config_path=config_path,
            evidence_dir=evidence_dir,
        ),
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["verdict_grade"] == "rejected"
    assert payload["verdict_text"].startswith("rejected: omlx_runtime_invocation_failed")


# ---------------------------------------------------------------------------
# HTTP serves the appended measured record
# ---------------------------------------------------------------------------


def test_http_surface_serves_measured_record_from_isolated_ledger(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_runner_config(
        config_path,
        owlmlx_argv=_fake_success_command("OWL"),
        reference_argv=_fake_success_command("REF"),
    )
    ledger_path = tmp_path / "ledger.jsonl"
    evidence_dir = tmp_path / "evidence"

    subprocess.run(
        _common_cli_args(
            ledger_path=ledger_path,
            config_path=config_path,
            evidence_dir=evidence_dir,
        ),
        capture_output=True,
        text=True,
        check=True,
    )

    client = TestClient(
        create_app(
            RuntimeKernel(FakeBackend(), profile=_profile()),
            comparative_evidence_ledger_path=str(ledger_path),
        )
    )

    latest = client.get("/v1/runtime/comparative-evidence")
    assert latest.status_code == 200
    body = latest.json()
    assert body["surface"] == "owlmlx.comparative_evidence_record"
    assert body["version"] == "v1"
    assert body["verdict_grade"] == "measured"
    assert body["host_class"] == "darwin-arm64-test-host"

    history = client.get("/v1/runtime/comparative-evidence/history")
    assert history.status_code == 200
    history_body = history.json()
    assert history_body["ledger_status"] == "available"
    assert len(history_body["records"]) == 1


# ---------------------------------------------------------------------------
# Module hygiene
# ---------------------------------------------------------------------------


def test_runner_module_does_not_import_forbidden_paths() -> None:
    """The measured runner must not pull OwlOps / OwlCoda / Agent code.

    Inspects the module AST so disclaimer strings inside the docstring do not
    register as imports. Only real ``import`` and ``from ... import`` statements
    are checked.
    """

    import ast

    source = (
        Path(__file__).resolve().parents[1]
        / "owlmlx"
        / "comparative_evidence_runner.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = ("owlops", "owlcoda")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                lower = alias.name.lower()
                for needle in forbidden:
                    assert needle not in lower, f"forbidden import {alias.name!r}"
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").lower()
            for needle in forbidden:
                assert needle not in module, f"forbidden import-from {node.module!r}"


def _fake_wrapper_with_child_command() -> tuple[str, ...]:
    """Wrapper that spawns a child with a measurable RSS footprint.

    The child allocates ~20MB and stays alive long enough for the sampler to
    observe it. The wrapper prints ``STARTED`` first (so first-token timing
    fires) and ``DONE`` after the child exits, then exits zero.
    """

    program = textwrap.dedent(
        """
        import subprocess, sys, time
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; arr=bytearray(20_000_000); time.sleep(0.4)"]
        )
        sys.stdout.write('STARTED\\n')
        sys.stdout.flush()
        child.wait()
        sys.stdout.write('DONE\\n')
        sys.stdout.flush()
        sys.exit(0)
        """
    )
    return (sys.executable, "-c", program)


def _fake_diagnostic_then_token_command() -> tuple[str, ...]:
    """Command that emits diagnostic JSON first, then a generated-token line.

    The diagnostic line arrives quickly; the token line arrives after a small
    pause. ``first_nonempty_chunk`` would mistakenly time the diagnostic line;
    ``after_marker:`` and ``regex:`` should time the token line instead.
    """

    program = textwrap.dedent(
        """
        import sys, time
        sys.stdout.write('{"smoke_ready": true, "stage": "gate"}\\n')
        sys.stdout.flush()
        time.sleep(0.15)
        sys.stdout.write('GENERATED OK\\n')
        sys.stdout.flush()
        sys.exit(0)
        """
    )
    return (sys.executable, "-c", program)


def test_rss_sampler_observes_child_process_in_wrapper_tree(tmp_path) -> None:
    """The runner must sample the wrapper PID *plus its descendants*.

    Codex's 3.5C live review showed sampling only the wrapper PID misses the
    real owlmlx MLX child workers and the real omlx server process.
    """

    cfg = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_wrapper_with_child_command(),
        timeout_s=10.0,
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is True
    rss_path = Path(result.rss_samples_path)
    assert rss_path.exists()

    samples = [
        json.loads(line)
        for line in rss_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert samples, "expected at least one rss sample"
    multi_pid_samples = [s for s in samples if len(s["per_pid_rss_bytes"]) > 1]
    assert multi_pid_samples, (
        f"expected at least one sample with multiple tracked PIDs; "
        f"got {samples!r}"
    )
    # Peak must reflect the child allocation (~20MB) on top of the wrapper.
    assert result.peak_resident_set_bytes >= 15_000_000, (
        f"peak {result.peak_resident_set_bytes} should include ~20MB child allocation"
    )


def test_rss_sampler_includes_external_pid(tmp_path) -> None:
    """external_pids must be sampled alongside the wrapper tree."""

    # Spawn a long-lived "external server" that allocates ~25MB.
    server_program = textwrap.dedent(
        """
        import sys, time
        arr = bytearray(25_000_000)
        time.sleep(2.0)
        """
    )
    server = subprocess.Popen([sys.executable, "-c", server_program])
    try:
        cfg = RuntimeRunnerConfig(
            runtime_id="omlx",
            runtime_version="0.3.5",
            argv=_fake_success_command("OK"),
            timeout_s=10.0,
            tokens_method="max_tokens",
            external_pids=(server.pid,),
        )
        result = execute_attempt(
            runtime_config=cfg,
            workload=_workload(),
            attempt_index=1,
            artifact_dir=tmp_path,
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

    assert result.ok is True
    samples = [
        json.loads(line)
        for line in Path(result.rss_samples_path)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert samples
    # The external server PID must appear in at least one sample.
    sampled_pids: set[str] = set()
    for sample in samples:
        sampled_pids.update(sample["per_pid_rss_bytes"].keys())
    assert str(server.pid) in sampled_pids, (
        f"external server PID {server.pid} not observed; sampled {sampled_pids}"
    )


def test_external_pid_file_resolves_pids(tmp_path) -> None:
    """external_pid_file must be read at attempt start, line by line."""

    server = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(2.0)"]
    )
    pid_file = tmp_path / "pids.txt"
    pid_file.write_text(
        f"# server PID\n{server.pid}\n\n", encoding="utf-8"
    )
    try:
        cfg = RuntimeRunnerConfig(
            runtime_id="omlx",
            runtime_version="0.3.5",
            argv=_fake_success_command("OK"),
            timeout_s=10.0,
            tokens_method="max_tokens",
            external_pid_file=str(pid_file),
        )
        result = execute_attempt(
            runtime_config=cfg,
            workload=_workload(),
            attempt_index=1,
            artifact_dir=tmp_path,
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

    assert result.ok is True
    samples = [
        json.loads(line)
        for line in Path(result.rss_samples_path)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    sampled_pids: set[str] = set()
    for sample in samples:
        sampled_pids.update(sample["per_pid_rss_bytes"].keys())
    assert str(server.pid) in sampled_pids


def test_after_marker_first_token_strategy_skips_diagnostic_lines(tmp_path) -> None:
    """``after_marker:`` must defer first-token until the marker line is seen."""

    cfg = RuntimeRunnerConfig(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_diagnostic_then_token_command(),
        timeout_s=10.0,
        tokens_method="max_tokens",
        first_token_strategy="after_marker:smoke_ready",
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is True
    # The diagnostic line arrives at ~0ms; the token line at ~150ms.
    # Without the marker fix, first_token_latency_ms would be near 0.
    assert result.first_token_latency_ms is not None
    assert result.first_token_latency_ms >= 100.0, (
        f"after_marker should observe the post-marker line (~150ms), "
        f"got {result.first_token_latency_ms}ms"
    )


def test_regex_first_token_strategy_matches_generation_pattern(tmp_path) -> None:
    cfg = RuntimeRunnerConfig(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_diagnostic_then_token_command(),
        timeout_s=10.0,
        tokens_method="max_tokens",
        first_token_strategy=r"regex:^GENERATED",
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is True
    assert result.first_token_latency_ms is not None
    assert result.first_token_latency_ms >= 100.0


def test_first_nonempty_chunk_back_compat_still_observes_first_line(tmp_path) -> None:
    """The default strategy must still time the first non-empty stdout line."""

    cfg = RuntimeRunnerConfig(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_diagnostic_then_token_command(),
        timeout_s=10.0,
        tokens_method="max_tokens",
        first_token_strategy="first_nonempty_chunk",
    )
    result = execute_attempt(
        runtime_config=cfg,
        workload=_workload(),
        attempt_index=1,
        artifact_dir=tmp_path,
    )
    assert result.ok is True
    # Default strategy times the diagnostic JSON line; latency must be < 100ms.
    assert result.first_token_latency_ms is not None
    assert result.first_token_latency_ms < 100.0


def test_load_runner_config_rejects_unsupported_first_token_strategy(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    config_path.write_text(
        json.dumps(
            {
                "owlmlx": {
                    "runtime_version": "x",
                    "argv": ["python3", "-c", "print('hi')"],
                    "first_token_strategy": "definitely-not-supported",
                },
                "reference": {
                    "runtime_id": "omlx",
                    "runtime_version": "0.3.5",
                    "argv": ["python3", "-c", "print('hi')"],
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_runner_config_file(config_path)


def test_load_runner_config_rejects_invalid_regex_strategy(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    config_path.write_text(
        json.dumps(
            {
                "owlmlx": {
                    "runtime_version": "x",
                    "argv": ["python3", "-c", "print('hi')"],
                    "first_token_strategy": "regex:[unterminated",
                },
                "reference": {
                    "runtime_id": "omlx",
                    "runtime_version": "0.3.5",
                    "argv": ["python3", "-c", "print('hi')"],
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_runner_config_file(config_path)


def test_load_runner_config_accepts_external_pids_and_pid_file(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    pid_file = tmp_path / "pids.txt"
    pid_file.write_text("12345\n", encoding="utf-8")
    config_path.write_text(
        json.dumps(
            {
                "owlmlx": {
                    "runtime_version": "x",
                    "argv": ["python3", "-c", "print('hi')"],
                    "external_pids": [777, 888],
                },
                "reference": {
                    "runtime_id": "omlx",
                    "runtime_version": "0.3.5",
                    "argv": ["python3", "-c", "print('hi')"],
                    "external_pid_file": str(pid_file),
                },
            }
        ),
        encoding="utf-8",
    )
    owl, ref = load_runner_config_file(config_path)
    assert owl.external_pids == (777, 888)
    assert owl.external_pid_file is None
    assert ref.external_pids == ()
    assert ref.external_pid_file == str(pid_file)


def test_aggregate_to_record_runtime_is_validatable_under_schema(tmp_path) -> None:
    cfg = _runner_cfg(
        runtime_id="owlmlx",
        runtime_version="0.0.0-runtime7",
        argv=_fake_success_command(),
    )
    attempts = [
        execute_attempt(
            runtime_config=cfg,
            workload=_workload(),
            attempt_index=i + 1,
            artifact_dir=tmp_path,
        )
        for i in range(2)
    ]
    aggregate = aggregate_runtime(runtime_config=cfg, attempts=attempts)
    runtime_payload = aggregate_to_record_runtime(aggregate)
    # Must contain all required measurement fields per the schema
    for field_name in (
        "throughput_tokens_per_second",
        "first_token_latency_ms",
        "peak_resident_set_bytes",
        "wall_clock_ms",
        "completed_request_count",
        "failure_count",
    ):
        assert field_name in runtime_payload["measurement"]
