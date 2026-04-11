from __future__ import annotations

import asyncio
import sys

from owlmlx.runtime import MlxLmBackend, RuntimeErrorCode, RuntimeKernel
from owlmlx.runtime.mlx_lm_backend import probe_mlx_lm_import


class FakeMlxLmModule:
    def __init__(self) -> None:
        self.load_calls: list[str] = []
        self.generate_calls: list[dict[str, object]] = []

    def load(self, model_id: str):
        self.load_calls.append(model_id)
        return f"model:{model_id}", f"tokenizer:{model_id}"

    def generate(self, model, tokenizer, *, prompt: str, **kwargs):
        self.generate_calls.append(
            {
                "model": model,
                "tokenizer": tokenizer,
                "prompt": prompt,
                "kwargs": kwargs,
            }
        )
        return f"{prompt} :: mlx-lm"


def test_mlx_lm_backend_load_calls_mlx_lm_load() -> None:
    module = FakeMlxLmModule()
    backend = MlxLmBackend(module=module)

    result = backend.load("model-a", memory_gb=2.5)

    assert result.ok is True
    assert module.load_calls == ["model-a"]
    assert result.model is not None
    assert result.model.backend == "mlx-lm"
    assert result.model.memory_gb == 2.5


def test_mlx_lm_backend_generate_calls_mlx_lm_generate() -> None:
    module = FakeMlxLmModule()
    backend = MlxLmBackend(module=module)
    backend.load("model-a", memory_gb=2.5)

    result = backend.generate("model-a", "hello", max_tokens=8)

    assert result.ok is True
    assert result.text == "hello :: mlx-lm"
    assert module.generate_calls == [
        {
            "model": "model:model-a",
            "tokenizer": "tokenizer:model-a",
            "prompt": "hello",
            "kwargs": {"max_tokens": 8},
        }
    ]


def test_mlx_lm_backend_generate_requires_loaded_model() -> None:
    backend = MlxLmBackend(module=FakeMlxLmModule())

    result = backend.generate("missing", "hello")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded


def test_mlx_lm_backend_status_reports_loaded_models() -> None:
    backend = MlxLmBackend(module=FakeMlxLmModule())
    backend.load("model-a", memory_gb=2.5)

    status = backend.status()

    assert status.backend_name == "mlx-lm"
    assert status.healthy is True
    assert len(status.loaded_models) == 1
    assert status.loaded_models[0].model_id == "model-a"


def test_mlx_lm_backend_unload_removes_model() -> None:
    backend = MlxLmBackend(module=FakeMlxLmModule())
    backend.load("model-a", memory_gb=2.5)

    result = backend.unload("model-a")

    assert result.ok is True
    assert result.freed_gb == 2.5
    assert backend.status().loaded_models == ()


def test_runtime_kernel_can_use_mlx_lm_backend_with_mock_module() -> None:
    backend = MlxLmBackend(module=FakeMlxLmModule())
    kernel = RuntimeKernel(backend)

    loaded = kernel.load_model("model-a", memory_gb=2.5)
    generated = asyncio.run(kernel.generate("hello", max_tokens=4))

    assert loaded.ok is True
    assert generated.ok is True
    assert generated.text == "hello :: mlx-lm"
    assert kernel.status_dict()["backend"]["backend_name"] == "mlx-lm"


def test_runtime_kernel_requires_memory_for_mlx_lm_backend() -> None:
    backend = MlxLmBackend(module=FakeMlxLmModule())
    kernel = RuntimeKernel(backend)

    result = kernel.load_model("model-a")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.invalid_request
    assert backend.status().loaded_models == ()


def test_mlx_lm_backend_reports_import_or_load_error() -> None:
    class BrokenModule:
        def load(self, model_id):
            raise RuntimeError("boom")

    backend = MlxLmBackend(module=BrokenModule())

    result = backend.load("model-a")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error
    assert backend.status().healthy is False


def test_probe_mlx_lm_import_uses_subprocess_without_parent_import() -> None:
    result = probe_mlx_lm_import(
        python_executable=sys.executable,
        timeout_s=5.0,
    )

    # The test environment may or may not have mlx_lm installed. The contract
    # is that probing returns a structured result instead of importing mlx_lm
    # in the parent process.
    assert isinstance(result.ok, bool)
    assert isinstance(result.returncode, int)
    assert isinstance(result.stdout, str)
    assert isinstance(result.stderr, str)
    assert "probe" in result.message


def test_mlx_lm_backend_preflight_failure_does_not_import_in_parent() -> None:
    backend = MlxLmBackend(
        python_executable="/path/that/does/not/exist",
        preflight_import=True,
    )

    result = backend.load("model-a", memory_gb=1.0)

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error
    assert "probe" in result.message
    assert backend.status().loaded_models == ()
    assert backend.status().detail["last_import_probe"]["ok"] is False
