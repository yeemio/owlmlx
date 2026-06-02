"""Native-backend technical-preview app factory."""

from __future__ import annotations

import os
from pathlib import Path

from owlmlx.runtime_model_visibility import default_models_root

from .kernel import RuntimeKernel
from .mlx_native_backend import MlxNativeBackend
from .model_path_resolving_backend import ModelPathResolvingBackend
from .server import create_app
from .technical_preview import DEFAULT_TECHNICAL_PREVIEW_PORT, model_path_resolver


NATIVE_PREVIEW_SURFACE = "owlmlx.native_preview_server"


def create_native_preview_app():
    """Create the real native-backend HTTP app for opt-in cache validation.

    Environment knobs:

    - ``OWLMLX_MODELS_ROOT``: local model root; defaults to the runtime
      visibility contract root.
    - ``OWLMLX_SESSION_CACHE_ENABLED``: enables explicit session KV cache reuse.
    - ``OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED``: enables opt-in no-header
      automatic prefix reuse.
    - ``OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES``: optional resident cache cap.
    - ledger and monitor env vars accepted by ``create_app`` as in the
      subprocess technical-preview server.
    """

    models_root = Path(
        os.environ.get("OWLMLX_MODELS_ROOT", "").strip()
        or str(default_models_root())
    ).expanduser()
    backend = ModelPathResolvingBackend(
        MlxNativeBackend(),
        model_path_resolver=model_path_resolver(models_root),
    )
    return create_app(
        RuntimeKernel(backend),
        visibility_models_root=str(models_root),
        comparative_evidence_ledger_path=os.environ.get(
            "OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH"
        ),
        model_release_candidate_ledger_path=os.environ.get(
            "OWLMLX_MODEL_RELEASE_CANDIDATE_LEDGER_PATH"
        ),
        runtime_test_run_ledger_path=os.environ.get(
            "OWLMLX_RUNTIME_TEST_RUN_LEDGER_PATH"
        ),
        runtime_monitor_trend_ledger_path=os.environ.get(
            "OWLMLX_RUNTIME_MONITOR_TREND_LEDGER_PATH"
        ),
        runtime_monitor_sample_interval_s=float(
            os.environ.get("OWLMLX_RUNTIME_MONITOR_SAMPLE_INTERVAL_S", "0") or "0"
        ),
        runtime_monitor_url=os.environ.get("OWLMLX_RUNTIME_URL", "http://127.0.0.1:8066"),
    )


__all__ = [
    "DEFAULT_TECHNICAL_PREVIEW_PORT",
    "NATIVE_PREVIEW_SURFACE",
    "create_native_preview_app",
]
