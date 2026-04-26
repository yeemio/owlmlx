"""Runtime-owned harness for child-exchange aggregated dispatch visibility."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CacheChildExchangeAggregatedDispatchHarnessResult:
    """Observed child-exchange aggregated-dispatch behavior on the active path."""

    aggregated_dispatch_visible: bool
    child_exchange_mode: str
    exchange_count: int
    batch_size: int
    aggregated_request_count: int
    max_aggregated_batch_size: int
    pid: int | None
    stream_secondary_status: str
    texts: tuple[str, ...]


def _write_runner(tmpdir: Path) -> str:
    module = tmpdir / "cache_child_exchange_probe_runner.py"
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
                "    elif action == 'generate_batch':",
                "        requests = list(req.get('requests', []))",
                "        count += 1",
                "        results = [",
                "            {'ok': True, 'text': item.get('prompt', '') + ' :: child', 'finish_reason': 'stop'}",
                "            for item in requests",
                "        ]",
                "        print(json.dumps({'ok': True, 'action': 'generate_batch', 'results': results, 'batch_size': len(results), 'pid': os.getpid(), 'generation_count': count}), flush=True)",
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


def run_cache_child_exchange_aggregated_dispatch_harness(
    *,
    prompts: tuple[str, ...] = ("child-a", "child-b"),
) -> CacheChildExchangeAggregatedDispatchHarnessResult:
    """Run a narrow harness proving whether one child exchange can carry a cohort."""

    from .runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend

    with tempfile.TemporaryDirectory(prefix="owlmlx-cache-child-exchange-") as tmp:
        tmpdir = Path(tmp)
        runner = _write_runner(tmpdir)
        backend = MlxLmSubprocessBackend(
            runner_module=runner,
            extra_pythonpath=(str(tmpdir),),
        )
        loaded = backend.load("child-exchange-probe")
        if not loaded.ok:
            raise RuntimeError(f"child-exchange harness load failed: {loaded.message}")

        try:
            batch = backend.generate_cohort("child-exchange-probe", list(prompts))
            if not batch.ok:
                raise RuntimeError(
                    f"child-exchange harness batch dispatch failed: {batch.message}"
                )
            status = backend.status()
            observations = dict(status.detail.get("cache_runtime_observations", {}))
            return CacheChildExchangeAggregatedDispatchHarnessResult(
                aggregated_dispatch_visible=bool(
                    observations.get("aggregated_child_exchange_visible")
                ),
                child_exchange_mode=str(
                    observations.get("child_exchange_mode")
                    or "single_request_per_child_exchange"
                ),
                exchange_count=int(batch.detail.get("exchange_count", 0) or 0),
                batch_size=int(batch.detail.get("batch_size", 0) or 0),
                aggregated_request_count=int(
                    observations.get("aggregated_child_exchange_request_count", 0) or 0
                ),
                max_aggregated_batch_size=int(
                    observations.get("max_aggregated_child_batch_size", 0) or 0
                ),
                pid=(
                    None
                    if batch.detail.get("pid") is None
                    else int(batch.detail.get("pid"))
                ),
                stream_secondary_status="stream_session_holds_gate_until_completion",
                texts=tuple(item.text for item in batch.results),
            )
        finally:
            backend.unload("child-exchange-probe")
