#!/usr/bin/env python3
"""Runtime-2 steady-state benchmark.

Measures persistent-child MLX runtime behavior after the Runtime-2 transition.
The benchmark separates:

- environment selection
- load time
- warm generate latencies
- simple summary statistics
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
from statistics import mean, median
from typing import Any

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


async def _run_generations(
    kernel: RuntimeKernel,
    *,
    prompt: str,
    max_tokens: int,
    repeat: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index in range(repeat):
        generated = await kernel.generate(prompt, max_tokens=max_tokens)
        row = asdict(generated)
        row["iteration"] = index + 1
        results.append(row)
        if not generated.ok:
            break
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--memory-gb", type=float, required=True)
    parser.add_argument("--prompt", default="Reply with exactly OK.")
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--python", default=None)
    parser.add_argument("--python-candidate", action="append", default=[])
    parser.add_argument("--include-known-venvs", action="store_true")
    args = parser.parse_args()

    selection = select_mlx_environment(tuple(_build_candidates(args)))
    print(json.dumps({"environment_selection": selection_to_dict(selection)}, indent=2))
    if not selection.ok or selection.selected is None:
        return 2

    backend = MlxLmSubprocessBackend(
        python_executable=selection.selected.candidate.python_executable
    )
    kernel = RuntimeKernel(backend)

    load_result = kernel.load_model(args.model, memory_gb=args.memory_gb)
    print(json.dumps({"load": asdict(load_result)}, indent=2, default=str))
    if not load_result.ok:
        return 2

    generations = asyncio.run(
        _run_generations(
            kernel,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            repeat=args.repeat,
        )
    )
    print(json.dumps({"generations": generations}, indent=2, default=str))

    unload_result = kernel.unload_model(args.model)
    print(json.dumps({"unload": asdict(unload_result)}, indent=2, default=str))

    if not unload_result.ok or not generations or not all(row["ok"] for row in generations):
        return 2

    latencies = [float(row["execution_time_s"] or 0.0) for row in generations]
    summary = {
        "model": args.model,
        "repeat": args.repeat,
        "load_time_s": load_result.detail.get("load_time_s"),
        "warm_generate_mean_s": round(mean(latencies), 4),
        "warm_generate_median_s": round(median(latencies), 4),
        "warm_generate_min_s": round(min(latencies), 4),
        "warm_generate_max_s": round(max(latencies), 4),
    }
    print(json.dumps({"summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
