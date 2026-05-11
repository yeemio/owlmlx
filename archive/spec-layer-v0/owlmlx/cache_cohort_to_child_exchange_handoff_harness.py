"""Runtime-owned harness for cohort-to-child handoff visibility."""

from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CacheCohortToChildExchangeHandoffHarnessResult:
    """Observed main-path handoff behavior from cohort window to child exchange."""

    cohort_handoff_visible: bool
    handoff_status: str
    child_exchange_mode: str
    aggregated_batch_count: int
    aggregated_request_count: int
    max_aggregated_batch_size: int
    gate_total_served: int
    gate_total_queued: int
    max_concurrent: int
    queue_discipline: str
    handoff_request_count: int
    stream_secondary_status: str
    texts: tuple[str, ...]


def _write_runner(tmpdir: Path) -> str:
    module = tmpdir / "cache_cohort_handoff_probe_runner.py"
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
                "        prompt = req.get('prompt', '')",
                "        print(json.dumps({'ok': True, 'action': 'generate', 'text': prompt + ' :: child', 'finish_reason': 'stop', 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                "    elif action == 'generate_batch':",
                "        requests = list(req.get('requests', []))",
                "        count += 1",
                "        results = [",
                "            {'ok': True, 'text': item.get('prompt', '') + ' :: child', 'finish_reason': 'stop'}",
                "            for item in requests",
                "        ]",
                "        print(json.dumps({'ok': True, 'action': 'generate_batch', 'results': results, 'batch_size': len(results), 'pid': os.getpid(), 'generation_count': count}), flush=True)",
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


def run_cache_cohort_to_child_exchange_handoff_harness(
    *,
    prompts: tuple[str, ...] = ("handoff-a", "handoff-b"),
) -> CacheCohortToChildExchangeHandoffHarnessResult:
    """Run the main serving path through a bounded cohort handoff."""

    from .runtime import MlxLmSubprocessBackend, RuntimeKernel

    with tempfile.TemporaryDirectory(prefix="owlmlx-cache-cohort-handoff-") as tmp:
        tmpdir = Path(tmp)
        runner = _write_runner(tmpdir)
        backend = MlxLmSubprocessBackend(
            runner_module=runner,
            extra_pythonpath=(str(tmpdir),),
        )
        kernel = RuntimeKernel(backend)
        loaded = kernel.load_model("cohort-handoff-probe", memory_gb=1.0)
        if not loaded.ok:
            raise RuntimeError(f"cohort handoff harness load failed: {loaded.message}")

        async def run_pair() -> tuple[object, ...]:
            return await asyncio.gather(
                *(kernel.generate(prompt) for prompt in prompts)
            )

        try:
            results = asyncio.run(run_pair())
            if not all(getattr(result, "ok", False) for result in results):
                raise RuntimeError("cohort handoff harness generate failed")
            status = kernel.status_dict()
            observations = dict(status["backend"]["detail"].get("cache_runtime_observations", {}))
            gate = dict(status["generation_gate"])
            pre_gate = dict(gate.get("pre_gate_admission", {}))
            handoff_request_count = max(
                int(pre_gate.get("active_handoff_request_count", 0) or 0),
                int(pre_gate.get("last_handoff_request_count", 0) or 0),
            )
            visible = (
                bool(observations.get("aggregated_child_exchange_visible"))
                and int(observations.get("aggregated_child_exchange_batch_count", 0) or 0)
                >= 1
                and int(
                    observations.get("aggregated_child_exchange_request_count", 0) or 0
                )
                >= len(prompts)
                and int(gate.get("max_concurrent", 0) or 0) == 1
                and str(gate.get("queue_discipline")) == "serial"
                and int(gate.get("total_served", 0) or 0) == len(prompts)
                and handoff_request_count >= len(prompts)
            )
            handoff_status = (
                "cohort_handed_off_to_aggregated_child_exchange_visible"
                if visible
                else "pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange"
            )
            return CacheCohortToChildExchangeHandoffHarnessResult(
                cohort_handoff_visible=visible,
                handoff_status=handoff_status,
                child_exchange_mode=str(
                    observations.get("child_exchange_mode")
                    or "single_request_per_child_exchange"
                ),
                aggregated_batch_count=int(
                    observations.get("aggregated_child_exchange_batch_count", 0) or 0
                ),
                aggregated_request_count=int(
                    observations.get("aggregated_child_exchange_request_count", 0) or 0
                ),
                max_aggregated_batch_size=int(
                    observations.get("max_aggregated_child_batch_size", 0) or 0
                ),
                gate_total_served=int(gate.get("total_served", 0) or 0),
                gate_total_queued=int(gate.get("total_queued", 0) or 0),
                max_concurrent=int(gate.get("max_concurrent", 0) or 0),
                queue_discipline=str(gate.get("queue_discipline") or "unknown"),
                handoff_request_count=handoff_request_count,
                stream_secondary_status="stream_session_holds_gate_until_completion",
                texts=tuple(str(getattr(result, "text", "")) for result in results),
            )
        finally:
            backend.unload("cohort-handoff-probe")
