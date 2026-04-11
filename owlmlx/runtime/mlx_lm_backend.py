"""mlx-lm backend adapter for owlmlx Runtime-0.

This adapter proves that RuntimeKernel has a real MLX-family backend seam.
It lazily imports ``mlx_lm`` so truth-only installs and core fake-backend tests
do not require runtime extras.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any

from .types import (
    BackendStatus,
    GenerateResult,
    LoadResult,
    LoadedModelInfo,
    RuntimeErrorCode,
    UnloadResult,
)


@dataclass(frozen=True, slots=True)
class MlxLmImportProbeResult:
    """Result of probing mlx-lm import in an isolated subprocess."""

    ok: bool
    returncode: int
    stdout: str
    stderr: str
    message: str


def probe_mlx_lm_import(
    *,
    python_executable: str | None = None,
    timeout_s: float = 20.0,
) -> MlxLmImportProbeResult:
    """Probe mlx-lm import without risking the parent runtime process.

    Importing ``mlx_lm`` initializes MLX/Metal in some environments. When
    Metal initialization crashes through Objective-C, Python cannot catch it.
    Running the import in a subprocess lets RuntimeKernel report a backend
    error instead of crashing the owlmlx process.
    """

    executable = python_executable or sys.executable
    code = (
        "import mlx_lm; "
        "print(getattr(mlx_lm, '__version__', 'unknown'))"
    )
    try:
        proc = subprocess.run(
            [executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except Exception as exc:
        return MlxLmImportProbeResult(
            ok=False,
            returncode=-1,
            stdout="",
            stderr=str(exc),
            message=f"mlx-lm import probe failed to run: {exc}",
        )

    ok = proc.returncode == 0
    return MlxLmImportProbeResult(
        ok=ok,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
        message=(
            "mlx-lm import probe passed"
            if ok
            else f"mlx-lm import probe failed with return code {proc.returncode}"
        ),
    )


class MlxLmBackend:
    """RuntimeBackend adapter backed by mlx-lm."""

    name = "mlx-lm"

    def __init__(
        self,
        *,
        module: Any | None = None,
        preflight_import: bool = True,
        python_executable: str | None = None,
    ) -> None:
        self._module = module
        self.preflight_import = preflight_import
        self.python_executable = python_executable
        self._loaded: dict[str, tuple[Any, Any, LoadedModelInfo]] = {}
        self._last_error: str | None = None
        self._last_probe: MlxLmImportProbeResult | None = None

    def _mlx_lm(self) -> Any:
        if self._module is None:
            self._module = importlib.import_module("mlx_lm")
        return self._module

    def load(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        if model_id in self._loaded:
            return LoadResult(
                ok=False,
                message=f"model already loaded: {model_id}",
                error_code=RuntimeErrorCode.model_already_loaded,
                model=self._loaded[model_id][2],
            )
        if self._module is None and self.preflight_import:
            probe = probe_mlx_lm_import(python_executable=self.python_executable)
            self._last_probe = probe
            if not probe.ok:
                self._last_error = probe.message
                return LoadResult(
                    ok=False,
                    message=probe.message,
                    error_code=RuntimeErrorCode.backend_error,
                    detail={
                        "probe_returncode": probe.returncode,
                        "probe_stdout": probe.stdout,
                        "probe_stderr": probe.stderr[-2000:],
                    },
                )
        try:
            module = self._mlx_lm()
            model, tokenizer = module.load(model_id)
        except Exception as exc:
            self._last_error = str(exc)
            return LoadResult(
                ok=False,
                message=f"mlx-lm load failed: {exc}",
                error_code=RuntimeErrorCode.backend_error,
            )

        info = LoadedModelInfo(
            model_id=model_id,
            memory_gb=memory_gb if memory_gb is not None else 0.0,
            backend=self.name,
            loaded_at=time.time(),
        )
        self._loaded[model_id] = (model, tokenizer, info)
        self._last_error = None
        return LoadResult(ok=True, message=f"loaded {model_id}", model=info)

    def generate(self, model_id: str, prompt: str, **kwargs: object) -> GenerateResult:
        loaded = self._loaded.get(model_id)
        if loaded is None:
            return GenerateResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )

        model, tokenizer, _info = loaded
        try:
            module = self._mlx_lm()
            text = module.generate(model, tokenizer, prompt=prompt, **kwargs)
        except Exception as exc:
            self._last_error = str(exc)
            return GenerateResult(
                ok=False,
                message=f"mlx-lm generate failed: {exc}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
            )

        self._last_error = None
        return GenerateResult(
            ok=True,
            message="generated",
            model_id=model_id,
            text=str(text),
        )

    def unload(self, model_id: str) -> UnloadResult:
        loaded = self._loaded.pop(model_id, None)
        if loaded is None:
            return UnloadResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        info = loaded[2]
        return UnloadResult(
            ok=True,
            message=f"unloaded {model_id}",
            model_id=model_id,
            freed_gb=info.memory_gb,
        )

    def status(self) -> BackendStatus:
        return BackendStatus(
            backend_name=self.name,
            healthy=self._last_error is None,
            loaded_models=tuple(info for _model, _tokenizer, info in self._loaded.values()),
            detail={
                "model_count": len(self._loaded),
                "last_error": self._last_error,
                "last_import_probe": (
                    {
                        "ok": self._last_probe.ok,
                        "returncode": self._last_probe.returncode,
                        "stdout": self._last_probe.stdout,
                        "stderr": self._last_probe.stderr[-2000:],
                        "message": self._last_probe.message,
                    }
                    if self._last_probe is not None
                    else None
                ),
            },
        )
