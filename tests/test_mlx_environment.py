from __future__ import annotations

from owlmlx.runtime.mlx_environment import (
    MlxEnvironmentCandidate,
    default_environment_candidates,
    known_environment_candidates,
    probe_to_dict,
    select_mlx_environment,
    selection_to_dict,
)


def test_default_environment_candidates_include_current_python() -> None:
    candidates = default_environment_candidates()

    assert candidates
    assert candidates[0].label == "current"
    assert len(candidates) == 1


def test_default_environment_candidates_are_unique() -> None:
    candidates = default_environment_candidates()

    executables = [candidate.python_executable for candidate in candidates]
    assert len(executables) == len(set(executables))


def test_known_environment_candidates_include_current_python() -> None:
    candidates = known_environment_candidates()

    assert candidates
    assert candidates[0].label == "current"
    assert len(candidates) >= 1


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
