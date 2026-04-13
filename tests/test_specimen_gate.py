from __future__ import annotations

from pathlib import Path

from owlmlx.runtime.specimen_gate import (
    assess_specimen_path,
    build_large_weight_specimen_gate,
    specimen_gate_to_dict,
)


def test_assess_specimen_path_reports_missing() -> None:
    result = assess_specimen_path("/tmp/does-not-exist-owlmlx-specimen")

    assert result.exists is False
    assert result.kind == "missing"
    assert result.has_config_json is False
    assert result.has_index_json is False
    assert result.shard_count == 0
    assert result.blocked_reason == "specimen path does not exist"


def test_assess_specimen_path_reports_directory_size(tmp_path: Path) -> None:
    specimen = tmp_path / "specimen"
    specimen.mkdir()
    (specimen / "a.bin").write_bytes(b"abcd")
    nested = specimen / "nested"
    nested.mkdir()
    (nested / "b.bin").write_bytes(b"ef")

    result = assess_specimen_path(str(specimen))

    assert result.exists is True
    assert result.kind == "directory"
    assert result.file_count == 2
    assert result.total_size_bytes == 6
    assert result.has_config_json is False
    assert result.has_index_json is False
    assert result.blocked_reason == "specimen directory is missing config.json"


def test_assess_specimen_path_detects_incomplete_download(tmp_path: Path) -> None:
    specimen = tmp_path / "specimen"
    specimen.mkdir()
    (specimen / "config.json").write_text("{}", encoding="utf-8")
    (specimen / "model.safetensors.index.json").write_text(
        '{"weight_map": {"a": "model-00000-of-00130.safetensors", "b": "model-00001-of-00130.safetensors", "c": "model-00002-of-00130.safetensors"}}',
        encoding="utf-8",
    )
    (specimen / "model-00000-of-00130.safetensors").write_bytes(b"a")
    (specimen / "model-00001-of-00130.safetensors").write_bytes(b"b")
    (specimen / "download.aria2").write_text("", encoding="utf-8")

    result = assess_specimen_path(str(specimen))

    assert result.has_config_json is True
    assert result.has_index_json is True
    assert result.shard_count == 2
    assert result.expected_shard_count == 3
    assert result.aria2_in_progress is True
    assert result.blocked_reason == "specimen download still in progress"


def test_assess_specimen_path_allows_complete_shards_even_with_stale_aria2(tmp_path: Path) -> None:
    specimen = tmp_path / "specimen"
    specimen.mkdir()
    (specimen / "config.json").write_text("{}", encoding="utf-8")
    (specimen / "model.safetensors.index.json").write_text(
        '{"weight_map": {"a": "model-00000-of-00002.safetensors", "b": "model-00001-of-00002.safetensors"}}',
        encoding="utf-8",
    )
    (specimen / "model-00000-of-00002.safetensors").write_bytes(b"a")
    (specimen / "model-00001-of-00002.safetensors").write_bytes(b"b")
    (specimen / "download.aria2").write_text("", encoding="utf-8")

    result = assess_specimen_path(str(specimen))

    assert result.aria2_in_progress is True
    assert result.expected_shard_count == 2
    assert result.shard_count == 2
    assert result.blocked_reason is None


def test_assess_specimen_path_detects_missing_shards_without_aria2(tmp_path: Path) -> None:
    specimen = tmp_path / "specimen"
    specimen.mkdir()
    (specimen / "config.json").write_text("{}", encoding="utf-8")
    (specimen / "model.safetensors.index.json").write_text(
        '{"weight_map": {"a": "model-00000-of-00003.safetensors", "b": "model-00001-of-00003.safetensors", "c": "model-00002-of-00003.safetensors"}}',
        encoding="utf-8",
    )
    (specimen / "model-00000-of-00003.safetensors").write_bytes(b"a")
    (specimen / "model-00001-of-00003.safetensors").write_bytes(b"b")

    result = assess_specimen_path(str(specimen))

    assert result.aria2_in_progress is False
    assert result.shard_count == 2
    assert result.expected_shard_count == 3
    assert result.blocked_reason == "specimen shard set is incomplete"


def test_build_large_weight_specimen_gate_blocks_on_missing_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.specimen_gate.build_mlx_environment_readiness",
        lambda **_: type(
            "Readiness",
            (),
            {
                "ok": True,
                "blocked_reason": None,
                "selection": type("Selection", (), {"message": "selected", "selected": None, "probes": ()})(),
                "include_known_candidates": False,
                "preferred_execution_mode": "default_metal",
                "quarantine_count": 0,
            },
        )(),
    )

    gate = build_large_weight_specimen_gate(
        specimen_path=str(tmp_path / "missing-model"),
    )
    payload = specimen_gate_to_dict(gate)

    assert gate.smoke_ready is False
    assert payload["contract"]["surface"] == "owlmlx.large_weight_specimen_gate"
    assert payload["summary"]["blocked_reason"] == "specimen path does not exist"


def test_build_large_weight_specimen_gate_blocks_on_environment(
    monkeypatch,
    tmp_path: Path,
) -> None:
    specimen = tmp_path / "model"
    specimen.mkdir()
    (specimen / "config.json").write_text("{}", encoding="utf-8")
    (specimen / "model-00000-of-00001.safetensors").write_bytes(b"abc")

    monkeypatch.setattr(
        "owlmlx.runtime.specimen_gate.build_mlx_environment_readiness",
        lambda **_: type(
            "Readiness",
            (),
            {
                "ok": False,
                "blocked_reason": "no usable mlx-lm python environment found",
                "selection": type("Selection", (), {"message": "blocked", "selected": None, "probes": ()})(),
                "include_known_candidates": False,
                "preferred_execution_mode": "default_metal",
                "quarantine_count": 0,
            },
        )(),
    )

    gate = build_large_weight_specimen_gate(specimen_path=str(specimen))
    payload = specimen_gate_to_dict(gate)

    assert gate.smoke_ready is False
    assert payload["specimen_path"]["file_count"] == 2
    assert (
        payload["summary"]["blocked_reason"]
        == "no usable mlx-lm python environment found"
    )


def test_build_large_weight_specimen_gate_ready_when_path_and_env_ok(
    monkeypatch,
    tmp_path: Path,
) -> None:
    specimen = tmp_path / "model"
    specimen.mkdir()
    (specimen / "config.json").write_text("{}", encoding="utf-8")
    (specimen / "model-00000-of-00001.safetensors").write_bytes(b"abc")

    selected = type(
        "SelectedProbe",
        (),
        {
            "candidate": type(
                "Candidate",
                (),
                {
                    "label": "runtime1-mlx",
                    "python_executable": "/tmp/python",
                    "execution_mode": "force_cpu",
                },
            )()
        },
    )()
    selection = type(
        "Selection",
        (),
        {"message": "selected mlx environment", "selected": selected, "probes": ()},
    )()
    monkeypatch.setattr(
        "owlmlx.runtime.specimen_gate.build_mlx_environment_readiness",
        lambda **_: type(
            "Readiness",
            (),
            {
                "ok": True,
                "blocked_reason": None,
                "selection": selection,
                "include_known_candidates": False,
                "preferred_execution_mode": "force_cpu",
                "quarantine_count": 2,
            },
        )(),
    )

    gate = build_large_weight_specimen_gate(specimen_path=str(specimen))
    payload = specimen_gate_to_dict(gate)

    assert gate.smoke_ready is True
    assert payload["summary"]["smoke_ready"] is True
    assert payload["specimen_path"]["has_config_json"] is True
    assert payload["specimen_path"]["has_index_json"] is False
    assert payload["mlx_environment"]["selection"]["selected_label"] == "runtime1-mlx"
    assert payload["mlx_environment"]["selection"]["execution_mode"] == "force_cpu"
    assert payload["mlx_environment"]["quarantine"]["count"] == 2
