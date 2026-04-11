from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from owlmlx.runtime import MlxLmSubprocessBackend, RuntimeErrorCode, RuntimeKernel


def _write_runner(tmp_path: Path, *, ok: bool = True) -> str:
    module = tmp_path / "fake_runner.py"
    if ok:
        module.write_text(
            "\n".join(
                [
                    "import json, sys",
                    "req=json.loads(sys.stdin.read())",
                    "print(json.dumps({'ok': True, 'text': req['prompt'] + ' :: child'}))",
                ]
            ),
            encoding="utf-8",
        )
    else:
        module.write_text(
            "\n".join(
                [
                    "import json",
                    "print(json.dumps({'ok': False, 'error': 'child boom'}))",
                    "raise SystemExit(2)",
                ]
            ),
            encoding="utf-8",
        )
    return module.stem


def test_subprocess_backend_registers_loaded_model(tmp_path: Path, monkeypatch) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )

    result = backend.load("model-a", memory_gb=2.0)

    assert result.ok is True
    assert result.model is not None
    assert result.model.backend == "mlx-lm-subprocess"
    assert backend.status().loaded_models[0].model_id == "model-a"


def test_subprocess_backend_generate_runs_child(tmp_path: Path, monkeypatch) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    result = backend.generate("model-a", "hello", max_tokens=4)

    assert result.ok is True
    assert result.text == "hello :: child"
    assert backend.status().healthy is True


def test_subprocess_backend_generate_requires_loaded_model(tmp_path: Path, monkeypatch) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )

    result = backend.generate("missing", "hello")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded


def test_subprocess_backend_reports_child_failure(tmp_path: Path, monkeypatch) -> None:
    runner = _write_runner(tmp_path, ok=False)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    result = backend.generate("model-a", "hello")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error
    assert "child boom" in result.message
    assert backend.status().healthy is False
    assert backend.status().detail["last_subprocess"]["returncode"] == 2


def test_subprocess_backend_unload_unregisters_model(tmp_path: Path, monkeypatch) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    result = backend.unload("model-a")

    assert result.ok is True
    assert result.freed_gb == 2.0
    assert backend.status().loaded_models == ()


def test_runtime_kernel_can_use_subprocess_backend(tmp_path: Path, monkeypatch) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    kernel = RuntimeKernel(backend)

    loaded = kernel.load_model("model-a", memory_gb=2.0)
    generated = asyncio.run(kernel.generate("hello", max_tokens=4))

    assert loaded.ok is True
    assert generated.ok is True
    assert generated.text == "hello :: child"
    assert kernel.status_dict()["backend"]["backend_name"] == "mlx-lm-subprocess"


def test_real_runner_missing_mlx_lm_returns_structured_failure() -> None:
    backend = MlxLmSubprocessBackend(
        python_executable=sys.executable,
        runner_module="owlmlx.runtime.mlx_lm_runner",
        timeout_s=20.0,
    )
    backend.load("model-a", memory_gb=1.0)

    result = backend.generate("model-a", "hello")

    # In dev/test environments without mlx_lm, this must be a structured
    # backend error, not a parent-process crash.
    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error
    assert "subprocess generate failed" in result.message
