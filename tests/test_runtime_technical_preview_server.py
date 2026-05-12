from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.model_release_candidate_history import ModelReleaseCandidateLedger
from owlmlx.model_release_candidate_record import build_dry_run_model_release_candidate_records
from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend
from owlmlx.runtime.technical_preview import (
    create_technical_preview_app,
    model_path_resolver,
)


def _write_path_echo_runner(tmp_path: Path) -> str:
    module = tmp_path / "fake_preview_runner.py"
    module.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "loaded = None",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        loaded = req['model_id']",
                "        print(json.dumps({'ok': True, 'action': 'load', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "    elif action == 'generate':",
                "        print(json.dumps({'ok': True, 'action': 'generate', 'text': 'loaded=' + str(loaded), 'pid': os.getpid(), 'generation_count': 1}), flush=True)",
                "    elif action == 'ping':",
                "        print(json.dumps({'ok': True, 'action': 'ping', 'model_id': loaded, 'pid': os.getpid(), 'generation_count': 0}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    return module.stem


def test_model_path_resolver_maps_visible_id_to_local_model_dir(tmp_path: Path) -> None:
    local_model_dir = tmp_path / "gemma-4-31B-it"
    local_model_dir.mkdir()

    resolve = model_path_resolver(tmp_path)

    assert resolve("gemma-4-31B-it") == str(local_model_dir)
    assert resolve("missing-model") == "missing-model"


def test_subprocess_backend_preserves_public_model_id_while_loading_local_path(
    tmp_path: Path,
) -> None:
    models_root = tmp_path / "models"
    local_model_dir = models_root / "demo-model"
    local_model_dir.mkdir(parents=True)
    runner = _write_path_echo_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        python_executable=sys.executable,
        runner_module=runner,
        model_path_resolver=model_path_resolver(models_root),
        extra_pythonpath=(str(tmp_path),),
    )

    loaded = backend.load("demo-model", memory_gb=1.0)
    generated = backend.generate("demo-model", "hello")

    assert loaded.ok is True
    assert loaded.model is not None
    assert loaded.model.model_id == "demo-model"
    assert loaded.detail["runner_model_id"] == str(local_model_dir)
    assert generated.ok is True
    assert generated.model_id == "demo-model"
    assert generated.text == f"loaded={local_model_dir}"
    assert backend.status().loaded_models[0].model_id == "demo-model"
    backend.unload("demo-model")


def test_technical_preview_factory_exposes_real_backend_and_visibility(
    tmp_path: Path,
    monkeypatch,
) -> None:
    model_dir = tmp_path / "gemma-4-31B-it"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("OWLMLX_MODELS_ROOT", str(tmp_path))
    monkeypatch.setenv("OWLMLX_RUNTIME_PYTHON", sys.executable)

    client = TestClient(create_technical_preview_app())

    health = client.get("/healthz")
    visibility = client.get("/v1/runtime/model-visibility")

    assert health.status_code == 200
    assert health.json()["backend_name"] == "mlx-lm-subprocess"
    assert visibility.status_code == 200
    assert "gemma-4-31B-it" in visibility.json()["visible_model_ids"]


def test_technical_preview_factory_mounts_model_rc_ledger_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ledger_path = tmp_path / "model-rc-ledger.jsonl"
    ModelReleaseCandidateLedger(ledger_path).append_many(
        list(
            build_dry_run_model_release_candidate_records(
                created_at="2026-05-05T00:00:00Z",
            )
        )
    )
    monkeypatch.setenv("OWLMLX_MODELS_ROOT", str(tmp_path))
    monkeypatch.setenv("OWLMLX_RUNTIME_PYTHON", sys.executable)
    monkeypatch.setenv("OWLMLX_MODEL_RELEASE_CANDIDATE_LEDGER_PATH", str(ledger_path))

    client = TestClient(create_technical_preview_app())

    latest = client.get("/v1/runtime/model-release-candidates")
    history = client.get("/v1/runtime/model-release-candidates/history")

    assert latest.status_code == 200
    assert latest.json()["model_id"] == "DeepSeek-V4-Flash-2bit-DQ"
    assert history.status_code == 200
    assert len(history.json()["records"]) == 4
