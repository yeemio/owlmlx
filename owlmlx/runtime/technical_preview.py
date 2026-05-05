"""Technical-preview app factory for the real owlmlx MLX runtime path."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from owlmlx.runtime_model_visibility import default_models_root

from .kernel import RuntimeKernel
from .mlx_lm_subprocess_backend import MlxLmSubprocessBackend
from .server import create_app


DEFAULT_TECHNICAL_PREVIEW_PORT = 8066
TECHNICAL_PREVIEW_SURFACE = "owlmlx.technical_preview_server"


def repo_root() -> Path:
    """Return the source checkout root for subprocess import stability."""

    return Path(__file__).resolve().parents[2]


def default_runtime_python() -> str:
    """Return the preferred Python executable for technical-preview serving."""

    configured = os.environ.get("OWLMLX_RUNTIME_PYTHON", "").strip()
    if configured:
        return str(Path(configured).expanduser())
    repo_venv_python = repo_root() / ".venv" / "bin" / "python"
    if repo_venv_python.is_file():
        return str(repo_venv_python)
    return sys.executable


def model_path_resolver(models_root: str | Path):
    """Build a resolver from public model id to local mlx-lm load path."""

    root = Path(models_root).expanduser()

    def resolve(model_id: str) -> str:
        raw = Path(model_id).expanduser()
        if raw.is_absolute() or raw.exists():
            return str(raw)
        local_model_dir = root / model_id
        if local_model_dir.exists():
            return str(local_model_dir)
        return model_id

    return resolve


def create_technical_preview_app():
    """Create the real-backend technical-preview HTTP app.

    Environment knobs:

    - ``OWLMLX_RUNTIME_PYTHON``: Python used by child ``mlx_lm`` runners.
    - ``OWLMLX_MODELS_ROOT``: local model root; defaults to the runtime
      visibility contract root.
    - ``OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH``: optional comparative
      evidence JSONL ledger for the read-only evidence routes.
    - ``OWLMLX_BACKEND_TIMEOUT_S``: child request timeout in seconds.
    - ``OWLMLX_BACKEND_RUNNER_MODULE``: child runner module override.
    - ``OWLMLX_FORCE_CPU``: when ``1``, propagated to child processes.
    """

    models_root = Path(
        os.environ.get("OWLMLX_MODELS_ROOT", "").strip()
        or str(default_models_root())
    ).expanduser()
    timeout_s = float(os.environ.get("OWLMLX_BACKEND_TIMEOUT_S", "600"))
    runner_module = os.environ.get(
        "OWLMLX_BACKEND_RUNNER_MODULE",
        "owlmlx.runtime.mlx_lm_runner",
    )
    env_overrides: dict[str, str] = {}
    if os.environ.get("OWLMLX_FORCE_CPU", "").strip() == "1":
        env_overrides["MLX_FORCE_CPU"] = "1"

    backend = MlxLmSubprocessBackend(
        python_executable=default_runtime_python(),
        env_overrides=env_overrides or None,
        runner_module=runner_module,
        model_path_resolver=model_path_resolver(models_root),
        timeout_s=timeout_s,
        extra_pythonpath=(str(repo_root()),),
    )
    return create_app(
        RuntimeKernel(backend),
        visibility_models_root=str(models_root),
        comparative_evidence_ledger_path=os.environ.get(
            "OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH"
        ),
    )
