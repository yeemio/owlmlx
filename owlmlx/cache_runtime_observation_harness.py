"""Runtime-owned active-path cache observation harness for owlmlx."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache_closure_rung import CacheClosureRung, build_cache_closure_rung
from .cache_repeatability_evidence import (
    CacheRepeatabilityEvidence,
    build_cache_repeatability_evidence,
)
from .runtime import MlxLmSubprocessBackend
from .turboquant_readiness import TurboQuantReadiness, build_turboquant_readiness


@dataclass(frozen=True, slots=True)
class CacheRuntimeObservationHarnessResult:
    """Active runtime-path cache observation result."""

    backend_observations: dict[str, Any]
    repeatability: CacheRepeatabilityEvidence
    turboquant: TurboQuantReadiness
    closure: CacheClosureRung


def _write_runner(tmpdir: Path) -> str:
    module = tmpdir / "cache_runtime_probe_runner.py"
    module.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "loaded = None",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        loaded = req['model_id']",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'generate', 'text': req['prompt'], 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                "    elif action == 'ping':",
                "        print(json.dumps({'ok': True, 'action': 'ping', 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    return module.stem


def run_cache_runtime_observation_harness() -> CacheRuntimeObservationHarnessResult:
    """Run the active runtime-path cache observation harness."""

    with tempfile.TemporaryDirectory(prefix="owlmlx-cache-runtime-") as tmp:
        tmpdir = Path(tmp)
        runner = _write_runner(tmpdir)
        backend = MlxLmSubprocessBackend(
            runner_module=runner,
            extra_pythonpath=(str(tmpdir),),
        )
        load = backend.load("cache-runtime-probe")
        if not load.ok:
            raise RuntimeError(f"cache runtime harness load failed: {load.message}")

        try:
            backend.generate("cache-runtime-probe", "warm-1")
            backend.generate("cache-runtime-probe", "warm-2")
            backend_status = backend.status()
            backend_observations = dict(
                backend_status.detail.get("cache_runtime_observations", {})
            )
            repeatability = build_cache_repeatability_evidence(
                [],
                backend_status=backend_status,
            )
            turboquant = build_turboquant_readiness(repeatability=repeatability)
            closure = build_cache_closure_rung(
                repeatability=repeatability,
                turboquant=turboquant,
            )
            return CacheRuntimeObservationHarnessResult(
                backend_observations=backend_observations,
                repeatability=repeatability,
                turboquant=turboquant,
                closure=closure,
            )
        finally:
            backend.unload("cache-runtime-probe")
