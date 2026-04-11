#!/usr/bin/env python3
"""Runtime-3 serialized concurrency validation.

Validates that persistent-child serving remains queue-based and serialized under
concurrent requests. The script measures per-request wait and execution timing
through RuntimeKernel + GenerationGate.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json

from owlmlx.runtime import (
    MlxEnvironmentCandidate,
    MlxLmSubprocessBackend,
    RuntimeKernel,
    default_environment_candidates,
    known_environment_candidates,
    select_mlx_environment,
    selection_to_dict,
)


def _build_candidates(args: argparse.Namespace) -> list[MlxEnvironmentCandidate]:
    candidates: list[MlxEnvironmentCandidate] = []
    if args.python:
        candidates.append(MlxEnvironmentCandidate(args.python, "explicit"))
    for index, executable in enumerate(args.python_candidate):
        candidates.append(MlxEnvironmentCandidate(executable, f"candidate-{index + 1}"))
    if not candidates:
        candidates.extend(default_environment_candidates())
        if args.include_known_venvs:
            current = {candidate.python_executable for candidate in candidates}
            for candidate in known_environment_candidates():
                if candidate.python_executable not in current:
                    candidates.append(candidate)
    return candidates


async def _run_request(kernel: RuntimeKernel, prompt: str, max_tokens: int) -> dict:
    result = await kernel.generate(prompt, max_tokens=max_tokens)
    return asdict(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--memory-gb", type=float, required=True)
    parser.add_argument("--prompt", default="Reply with exactly OK.")
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--python", default=None)
    parser.add_argument("--python-candidate", action="append", default=[])
    parser.add_argument("--include-known-venvs", action="store_true")
    args = parser.parse_args()

    selection = select_mlx_environment(tuple(_build_candidates(args)))
    print(json.dumps({"environment_selection": selection_to_dict(selection)}, indent=2))
    if not selection.ok or selection.selected is None:
        return 2

    kernel = RuntimeKernel(
        MlxLmSubprocessBackend(
            python_executable=selection.selected.candidate.python_executable
        )
    )
    loaded = kernel.load_model(args.model, memory_gb=args.memory_gb)
    print(json.dumps({"load": asdict(loaded)}, indent=2, default=str))
    if not loaded.ok:
        return 2

    async def run_all() -> list[dict]:
        tasks = [
            _run_request(kernel, f"{args.prompt} [{index + 1}]", args.max_tokens)
            for index in range(args.concurrency)
        ]
        return await asyncio.gather(*tasks)

    results = asyncio.run(run_all())
    print(json.dumps({"results": results}, indent=2, default=str))
    unload = kernel.unload_model(args.model)
    print(json.dumps({"unload": asdict(unload)}, indent=2, default=str))

    if not unload.ok or not all(result["ok"] for result in results):
        return 2

    status = kernel.status_dict()
    gate = status["generation_gate"]
    pids = {
        result.get("detail", {}).get("pid")
        for result in results
        if result.get("detail", {}).get("pid") is not None
    }
    queued = sum(1 for result in results if result["was_queued"])
    summary = {
        "model": args.model,
        "concurrency": args.concurrency,
        "queued_requests": queued,
        "same_child_pid": len(pids) == 1,
        "all_serialized": (
            gate["max_concurrent"] == 1
            and gate["queue_discipline"] == "serial"
            and gate["total_served"] == args.concurrency
            and gate["total_queued"] == args.concurrency
            and len(pids) == 1
        ),
        "wait_times_s": [result["wait_time_s"] for result in results],
        "execution_times_s": [result["execution_time_s"] for result in results],
        "generation_gate": gate,
    }
    print(json.dumps({"summary": summary}, indent=2, default=str))
    return 0 if summary["all_serialized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
