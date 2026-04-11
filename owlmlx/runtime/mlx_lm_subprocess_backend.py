"""Subprocess-isolated mlx-lm backend.

This backend keeps the owlmlx parent process safe by never importing mlx-lm
in-process. ``generate`` launches a child runner that performs
``mlx_lm.load`` + ``mlx_lm.generate`` and returns JSON.

This is intentionally one-shot per generation. It is not production efficient,
but it is the correct Runtime-1 safety boundary after local MLX/Metal import
proved capable of aborting the Python process.
"""

from __future__ import annotations

import json
import os
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
class MlxLmSubprocessResult:
    """Raw child-process execution result."""

    ok: bool
    returncode: int
    stdout: str
    stderr: str
    payload: dict[str, Any]


class MlxLmSubprocessBackend:
    """RuntimeBackend that isolates mlx-lm execution in child processes."""

    name = "mlx-lm-subprocess"

    def __init__(
        self,
        *,
        python_executable: str | None = None,
        runner_module: str = "owlmlx.runtime.mlx_lm_runner",
        timeout_s: float = 600.0,
        extra_pythonpath: tuple[str, ...] = (),
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.runner_module = runner_module
        self.timeout_s = timeout_s
        self.extra_pythonpath = extra_pythonpath
        self._loaded: dict[str, LoadedModelInfo] = {}
        self._last_error: str | None = None
        self._last_result: MlxLmSubprocessResult | None = None

    def load(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        if model_id in self._loaded:
            return LoadResult(
                ok=False,
                message=f"model already loaded: {model_id}",
                error_code=RuntimeErrorCode.model_already_loaded,
                model=self._loaded[model_id],
            )
        info = LoadedModelInfo(
            model_id=model_id,
            memory_gb=memory_gb if memory_gb is not None else 0.0,
            backend=self.name,
            loaded_at=time.time(),
        )
        self._loaded[model_id] = info
        self._last_error = None
        return LoadResult(
            ok=True,
            message=(
                f"registered {model_id}; mlx-lm load executes in subprocess "
                "during generation"
            ),
            model=info,
        )

    def _run_child(
        self,
        *,
        model_id: str,
        prompt: str,
        params: dict[str, Any],
    ) -> MlxLmSubprocessResult:
        request = {
            "model_id": model_id,
            "prompt": prompt,
            "params": params,
        }
        try:
            env = os.environ.copy()
            if self.extra_pythonpath:
                existing = env.get("PYTHONPATH")
                env["PYTHONPATH"] = os.pathsep.join(
                    [*self.extra_pythonpath, *([existing] if existing else [])]
                )
            proc = subprocess.run(
                [self.python_executable, "-m", self.runner_module],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                env=env,
            )
        except Exception as exc:
            return MlxLmSubprocessResult(
                ok=False,
                returncode=-1,
                stdout="",
                stderr=str(exc),
                payload={"ok": False, "error": str(exc)},
            )

        payload: dict[str, Any]
        try:
            stdout = proc.stdout.strip()
            if not stdout:
                raise ValueError("child process produced no output")
            payload = json.loads(stdout.splitlines()[-1])
        except Exception as exc:
            payload = {
                "ok": False,
                "error": f"invalid runner JSON: {exc}",
            }
        return MlxLmSubprocessResult(
            ok=proc.returncode == 0 and bool(payload.get("ok")),
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            payload=payload,
        )

    def generate(self, model_id: str, prompt: str, **kwargs: object) -> GenerateResult:
        if model_id not in self._loaded:
            return GenerateResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )

        result = self._run_child(
            model_id=model_id,
            prompt=prompt,
            params=dict(kwargs),
        )
        self._last_result = result
        if not result.ok:
            error = str(result.payload.get("error") or result.stderr or result.returncode)
            self._last_error = error
            return GenerateResult(
                ok=False,
                message=f"mlx-lm subprocess generate failed: {error}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
                detail={
                    "returncode": result.returncode,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                    "payload": result.payload,
                },
            )

        self._last_error = None
        return GenerateResult(
            ok=True,
            message="generated",
            model_id=model_id,
            text=str(result.payload.get("text", "")),
            detail={
                "returncode": result.returncode,
            },
        )

    def unload(self, model_id: str) -> UnloadResult:
        info = self._loaded.pop(model_id, None)
        if info is None:
            return UnloadResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        return UnloadResult(
            ok=True,
            message=f"unregistered {model_id}",
            model_id=model_id,
            freed_gb=info.memory_gb,
        )

    def status(self) -> BackendStatus:
        return BackendStatus(
            backend_name=self.name,
            healthy=self._last_error is None,
            loaded_models=tuple(self._loaded.values()),
            detail={
                "model_count": len(self._loaded),
                "last_error": self._last_error,
                "last_subprocess": (
                    {
                        "ok": self._last_result.ok,
                        "returncode": self._last_result.returncode,
                        "stdout": self._last_result.stdout[-2000:],
                        "stderr": self._last_result.stderr[-2000:],
                        "payload": self._last_result.payload,
                    }
                    if self._last_result is not None
                    else None
                ),
            },
        )
