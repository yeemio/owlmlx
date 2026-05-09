from __future__ import annotations

import sys
from pathlib import Path

from owlmlx.runtime.mlx_environment import (
    MlxEnvironmentCandidate,
    blocker_report_to_dict,
    build_mlx_import_blocker_report,
    build_mlx_environment_readiness,
    default_environment_candidates,
    is_known_unsafe_python,
    is_known_unsafe_python_with_path,
    load_quarantined_pythons,
    known_environment_candidates,
    load_verified_baselines,
    probe_to_dict,
    probe_mlx_environments,
    quarantine_file_path,
    readiness_to_dict,
    remember_quarantined_python,
    remember_verified_baseline,
    select_mlx_environment,
    selection_to_dict,
    verified_baseline_file_path,
)
from owlmlx.runtime.mlx_lm_backend import MlxLmImportProbeResult, probe_python_snippet


def test_default_environment_candidates_include_current_python() -> None:
    candidates = default_environment_candidates()

    if candidates:
        assert len(candidates) >= 1
        if is_known_unsafe_python(sys.executable) is False:
            assert any(candidate.label == "current" for candidate in candidates)
    else:
        assert is_known_unsafe_python(sys.executable) is True


def test_default_environment_candidates_are_unique() -> None:
    candidates = default_environment_candidates()

    executables = [candidate.python_executable for candidate in candidates]
    assert len(executables) == len(set(executables))


def test_known_environment_candidates_include_current_python() -> None:
    candidates = known_environment_candidates()

    assert candidates
    assert any(candidate.label == "current" for candidate in candidates)
    assert len(candidates) >= 1


def test_default_environment_candidates_respect_preferred_execution_mode() -> None:
    candidates = default_environment_candidates(preferred_execution_mode="force_cpu")

    if candidates:
        assert all(candidate.execution_mode == "force_cpu" for candidate in candidates)


def test_known_environment_candidates_include_runtime1_mlx_when_present() -> None:
    candidates = known_environment_candidates(preferred_execution_mode="force_cpu")

    labels = [candidate.label for candidate in candidates]
    if any("AI/gitrep/owlmlx/.runtime1-mlx/bin/python" in candidate.python_executable for candidate in candidates):
        assert "runtime1-mlx" in labels
        runtime1 = next(candidate for candidate in candidates if candidate.label == "runtime1-mlx")
        assert runtime1.execution_mode == "force_cpu"


def test_known_unsafe_python_matches_runtime_docs_paths() -> None:
    assert is_known_unsafe_python("/Users/yeemio/AI/llm-infra/.venv/bin/python") is True
    assert is_known_unsafe_python("/Users/yeemio/AI/gitrep/owlmlx/.venv/bin/python") is True
    assert (
        is_known_unsafe_python_with_path(
            "/Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python",
            quarantine_path=Path("/tmp/nonexistent-quarantine.json"),
        )
        is False
    )


def test_probe_mlx_environments_skips_known_unsafe_candidates() -> None:
    probes = probe_mlx_environments(
        (MlxEnvironmentCandidate("/Users/yeemio/AI/llm-infra/.venv/bin/python", "unsafe"),)
    )

    assert len(probes) == 1
    assert probes[0].usable is False
    assert probes[0].result.returncode == -6
    assert "skipped known unsafe" in probes[0].result.message


def test_quarantine_file_path_respects_env_override(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "quarantine.json"
    monkeypatch.setenv("OWLMX_MLX_QUARANTINE_PATH", str(target))

    assert quarantine_file_path() == target


def test_verified_baseline_file_path_respects_env_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "verified.json"
    monkeypatch.setenv("OWLMX_MLX_VERIFIED_BASELINES_PATH", str(target))

    assert verified_baseline_file_path() == target


def test_remember_quarantined_python_persists_entries(tmp_path: Path) -> None:
    target = tmp_path / "quarantine.json"

    remember_quarantined_python(
        "/tmp/python-a",
        reason="aborted during import",
        path=target,
    )
    remember_quarantined_python(
        "/tmp/python-b",
        reason="second failure",
        path=target,
    )

    payload = load_quarantined_pythons(path=target)
    assert payload[f"{Path('/tmp/python-a')}::default_metal"] == "aborted during import"
    assert payload[f"{Path('/tmp/python-b')}::default_metal"] == "second failure"


def test_remember_verified_baseline_persists_entries(tmp_path: Path) -> None:
    target = tmp_path / "verified.json"

    remember_verified_baseline("/tmp/python-a", label="a", path=target)
    remember_verified_baseline(
        "/tmp/python-b",
        label="b",
        execution_mode="force_cpu",
        path=target,
    )

    payload = load_verified_baselines(path=target)
    assert payload[0].python_executable == str(Path("/tmp/python-b"))
    assert payload[0].label == "b"
    assert payload[0].execution_mode == "force_cpu"
    assert payload[1].python_executable == str(Path("/tmp/python-a"))


def test_probe_mlx_environments_quarantines_abort_returncode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    aborting_python = tmp_path / "aborting_python.py"

    def fake_probe(
        *,
        python_executable: str,
        timeout_s: float = 20.0,
        execution_mode: str = "default_metal",
    ) -> MlxLmImportProbeResult:
        assert python_executable == str(aborting_python)
        assert execution_mode == "default_metal"
        return MlxLmImportProbeResult(
            ok=False,
            returncode=-6,
            stdout="",
            stderr="simulated abort during Metal initialization",
            message="mlx-lm import probe failed with return code -6",
        )

    monkeypatch.setattr("owlmlx.runtime.mlx_environment.probe_mlx_lm_import", fake_probe)
    quarantine = tmp_path / "quarantine.json"
    probes = probe_mlx_environments(
        (MlxEnvironmentCandidate(str(aborting_python), "abort"),),
        quarantine_path=quarantine,
    )

    assert probes[0].result.returncode == -6
    payload = load_quarantined_pythons(path=quarantine)
    assert f"{aborting_python}::default_metal" in payload


def test_select_mlx_environment_skips_previously_quarantined_python(tmp_path: Path) -> None:
    quarantine = tmp_path / "quarantine.json"
    remember_quarantined_python(
        "/tmp/unsafe-python",
        reason="import probe aborted during Metal initialization",
        path=quarantine,
    )

    selection = select_mlx_environment(
        (MlxEnvironmentCandidate("/tmp/unsafe-python", "unsafe"),),
        quarantine_path=quarantine,
    )

    assert selection.ok is False
    assert is_known_unsafe_python_with_path("/tmp/unsafe-python", quarantine_path=quarantine) is True
    assert selection.probes[0].result.returncode == -6
    assert "skipped known unsafe" in selection.probes[0].result.message


def test_force_cpu_mode_is_not_blocked_by_default_metal_quarantine(tmp_path: Path) -> None:
    quarantine = tmp_path / "quarantine.json"
    remember_quarantined_python(
        "/tmp/unsafe-python",
        execution_mode="default_metal",
        reason="import probe aborted during Metal initialization",
        path=quarantine,
    )

    assert (
        is_known_unsafe_python_with_path(
            "/tmp/unsafe-python",
            execution_mode="force_cpu",
            quarantine_path=quarantine,
        )
        is False
    )


def test_default_environment_candidates_use_verified_baseline_registry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline-python"
    baseline.write_text("", encoding="utf-8")
    verified = tmp_path / "verified.json"
    remember_verified_baseline(str(baseline), label="verified", path=verified)
    monkeypatch.setenv("OWLMX_MLX_VERIFIED_BASELINES_PATH", str(verified))

    candidates = default_environment_candidates()

    assert candidates
    assert candidates[0].label == "verified"
    assert candidates[0].python_executable == str(baseline)
    assert candidates[0].execution_mode == "default_metal"


def test_select_mlx_environment_picks_first_success(tmp_path) -> None:
    ok_python = tmp_path / "ok_python.py"
    ok_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "if sys.argv[1] == '-c':",
                "    print('0.31.2')",
                "    raise SystemExit(0)",
                "raise SystemExit(2)",
            ]
        ),
        encoding="utf-8",
    )
    ok_python.chmod(0o755)

    bad_python = tmp_path / "bad_python.py"
    bad_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "print('boom', file=sys.stderr)",
                "raise SystemExit(1)",
            ]
        ),
        encoding="utf-8",
    )
    bad_python.chmod(0o755)

    selection = select_mlx_environment(
        (
            MlxEnvironmentCandidate(str(bad_python), "bad"),
            MlxEnvironmentCandidate(str(ok_python), "ok"),
        )
    )

    assert selection.ok is True
    assert selection.selected is not None
    assert selection.selected.candidate.label == "ok"
    assert len(selection.probes) == 2


def test_select_mlx_environment_reports_total_failure(tmp_path) -> None:
    bad_python = tmp_path / "bad_python.py"
    bad_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "print('missing mlx_lm', file=sys.stderr)",
                "raise SystemExit(1)",
            ]
        ),
        encoding="utf-8",
    )
    bad_python.chmod(0o755)

    selection = select_mlx_environment(
        (MlxEnvironmentCandidate(str(bad_python), "bad"),)
    )

    assert selection.ok is False
    assert selection.selected is None
    assert selection.probes[0].candidate.label == "bad"
    assert "no usable mlx-lm python environment found" in selection.message


def test_selection_to_dict_includes_probe_details(tmp_path) -> None:
    ok_python = tmp_path / "ok_python.py"
    ok_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "if sys.argv[1] == '-c':",
                "    print('0.31.2')",
                "    raise SystemExit(0)",
                "raise SystemExit(2)",
            ]
        ),
        encoding="utf-8",
    )
    ok_python.chmod(0o755)

    selection = select_mlx_environment(
        (MlxEnvironmentCandidate(str(ok_python), "ok"),)
    )
    payload = selection_to_dict(selection)

    assert payload["ok"] is True
    assert payload["selected"] is not None
    assert payload["probes"][0]["label"] == "ok"
    assert payload["probes"][0]["usable"] is True
    assert probe_to_dict(selection.probes[0])["python_executable"] == str(ok_python)
    assert probe_to_dict(selection.probes[0])["execution_mode"] == "default_metal"


def test_build_mlx_environment_readiness_blocks_without_candidates(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.mlx_environment.default_environment_candidates",
        lambda **_: (),
    )

    readiness = build_mlx_environment_readiness(quarantine_path=tmp_path / "q.json")
    payload = readiness_to_dict(readiness)

    assert readiness.ok is False
    assert payload["contract"]["surface"] == "owlmlx.mlx_environment"
    assert payload["contract"]["version"] == "stabilization2"
    assert payload["summary"]["readiness"] == "blocked"
    assert payload["summary"]["blocked_reason"] == "no safe default mlx-lm python candidates available"
    assert payload["selection"]["python_executable"] is None
    assert payload["selection"]["execution_mode"] is None
    assert payload["quarantine"]["count"] == 0


def test_build_mlx_environment_readiness_exposes_selected_python(
    monkeypatch,
    tmp_path: Path,
) -> None:
    ok_python = tmp_path / "ok_python.py"
    ok_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "if sys.argv[1] == '-c':",
                "    print('0.31.2')",
                "    raise SystemExit(0)",
                "raise SystemExit(2)",
            ]
        ),
        encoding="utf-8",
    )
    ok_python.chmod(0o755)

    monkeypatch.setattr(
        "owlmlx.runtime.mlx_environment.default_environment_candidates",
        lambda **kwargs: (
            MlxEnvironmentCandidate(
                str(ok_python),
                "ok",
                kwargs.get("preferred_execution_mode", "default_metal"),
            ),
        ),
    )

    readiness = build_mlx_environment_readiness(
        preferred_execution_mode="force_cpu",
        quarantine_path=tmp_path / "q.json",
    )
    payload = readiness_to_dict(readiness)

    assert readiness.ok is True
    assert payload["summary"]["readiness"] == "ready"
    assert payload["summary"]["preferred_execution_mode"] == "force_cpu"
    assert payload["selection"]["selected_label"] == "ok"
    assert payload["selection"]["execution_mode"] == "force_cpu"
    assert payload["selection"]["python_executable"] == str(ok_python)
    assert payload["contract"]["diagnostic_sections"] == ["probes"]


def test_readiness_to_dict_reflects_quarantine_count(tmp_path: Path) -> None:
    quarantine = tmp_path / "quarantine.json"
    remember_quarantined_python(
        "/tmp/unsafe-python-a",
        reason="import probe aborted during Metal initialization",
        path=quarantine,
    )
    remember_quarantined_python(
        "/tmp/unsafe-python-b",
        reason="second abort",
        path=quarantine,
    )

    original = default_environment_candidates
    try:
        from owlmlx.runtime import mlx_environment as mlx_environment_module

        mlx_environment_module.default_environment_candidates = lambda **_: ()
        readiness = build_mlx_environment_readiness(
            quarantine_path=quarantine,
        )
    finally:
        mlx_environment_module.default_environment_candidates = original
    payload = readiness_to_dict(readiness)

    assert payload["quarantine"]["count"] == 2


def test_build_mlx_import_blocker_report_serializes_blocked_machine_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.mlx_environment.default_environment_candidates",
        lambda **_: (),
    )

    quarantine = tmp_path / "quarantine.json"
    report = build_mlx_import_blocker_report(
        include_known_candidates=False,
        quarantine_path=quarantine,
    )
    payload = blocker_report_to_dict(report)

    assert report.blocked is True
    assert payload["contract"]["surface"] == "owlmlx.mlx_blocker_report"
    assert payload["contract"]["version"] == "stabilization2"
    assert payload["summary"]["blocked"] is True
    assert payload["summary"]["blocked_reason"] == "no safe default mlx-lm python candidates available"
    assert payload["readiness"]["contract"]["surface"] == "owlmlx.mlx_environment"
    assert payload["quarantine"]["file"] == str(quarantine)


def test_build_mlx_import_blocker_report_preserves_known_candidate_mode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    ok_python = tmp_path / "ok_python.py"
    ok_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "if sys.argv[1] == '-c':",
                "    print('0.31.2')",
                "    raise SystemExit(0)",
                "raise SystemExit(2)",
            ]
        ),
        encoding="utf-8",
    )
    ok_python.chmod(0o755)

    monkeypatch.setattr(
        "owlmlx.runtime.mlx_environment.known_environment_candidates",
        lambda **_: (MlxEnvironmentCandidate(str(ok_python), "known-ok"),),
    )

    report = build_mlx_import_blocker_report(
        include_known_candidates=True,
        quarantine_path=tmp_path / "q.json",
    )
    payload = blocker_report_to_dict(report)

    assert report.blocked is False
    assert payload["summary"]["blocked"] is False
    assert payload["readiness"]["summary"]["include_known_candidates"] is True
    assert payload["readiness"]["selection"]["selected_label"] == "known-ok"


def test_build_mlx_environment_readiness_uses_force_cpu_mode_when_requested(
    monkeypatch,
    tmp_path: Path,
) -> None:
    ok_python = tmp_path / "ok_python.py"
    ok_python.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "owlmlx.runtime.mlx_environment.default_environment_candidates",
        lambda *, preferred_execution_mode="default_metal": (
            MlxEnvironmentCandidate(str(ok_python), "ok", preferred_execution_mode),
        ),
    )

    def fake_probe(
        *,
        python_executable: str,
        timeout_s: float = 20.0,
        execution_mode: str = "default_metal",
    ) -> MlxLmImportProbeResult:
        assert python_executable == str(ok_python)
        assert execution_mode == "force_cpu"
        return MlxLmImportProbeResult(
            ok=True,
            returncode=0,
            stdout="0.31.2",
            stderr="",
            message="mlx-lm import probe passed",
        )

    monkeypatch.setattr("owlmlx.runtime.mlx_environment.probe_mlx_lm_import", fake_probe)
    readiness = build_mlx_environment_readiness(
        preferred_execution_mode="force_cpu",
        quarantine_path=tmp_path / "q.json",
    )

    assert readiness.ok is True
    assert readiness.selection.selected is not None
    assert readiness.selection.selected.candidate.execution_mode == "force_cpu"


def test_probe_python_snippet_supports_env_wrapper_force_cpu(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeCompleted:
        returncode = 0
        stdout = "ok\n"
        stderr = ""

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs.get("env")
        return FakeCompleted()

    monkeypatch.setattr("owlmlx.runtime.mlx_lm_backend.subprocess.run", fake_run)
    result = probe_python_snippet(
        code="print('ok')",
        python_executable="/tmp/python",
        execution_mode="force_cpu",
        launch_mode="env_wrapper",
    )

    assert result.ok is True
    assert captured["argv"] == [
        "/usr/bin/env",
        "MLX_FORCE_CPU=1",
        "/tmp/python",
        "-c",
        "print('ok')",
    ]
    assert captured["env"] is None


def test_probe_python_snippet_uses_env_for_direct_exec(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeCompleted:
        returncode = 0
        stdout = "ok\n"
        stderr = ""

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs.get("env")
        return FakeCompleted()

    monkeypatch.setattr("owlmlx.runtime.mlx_lm_backend.subprocess.run", fake_run)
    result = probe_python_snippet(
        code="print('ok')",
        python_executable="/tmp/python",
        execution_mode="force_cpu",
        launch_mode="direct_exec",
    )

    assert result.ok is True
    assert captured["argv"] == ["/tmp/python", "-c", "print('ok')"]
    assert isinstance(captured["env"], dict)
    assert captured["env"]["MLX_FORCE_CPU"] == "1"
