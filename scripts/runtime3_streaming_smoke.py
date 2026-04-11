#!/usr/bin/env python3
"""Runtime-3 real streaming smoke.

Verifies the RuntimeKernel streaming path end-to-end:

- environment selection
- persistent-child MLX load
- first token timing
- streamed token/done events
- explicit unload
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import asdict
from pathlib import Path

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


async def _run_stream(
    kernel: RuntimeKernel,
    *,
    prompt: str,
    max_tokens: int,
) -> dict[str, object]:
    started = time.monotonic()
    first_token_at: float | None = None
    events: list[dict[str, object]] = []
    async for event in kernel.generate_stream(prompt, max_tokens=max_tokens):
        if event.event == "token" and first_token_at is None:
            first_token_at = time.monotonic()
        events.append(asdict(event))
    finished = time.monotonic()
    return {
        "ttft_s": round((first_token_at - started), 4) if first_token_at else None,
        "total_s": round(finished - started, 4),
        "events": events,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--memory-gb", type=float, required=True)
    parser.add_argument("--prompt", default="Reply with exactly OK.")
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--python", default=None)
    parser.add_argument("--python-candidate", action="append", default=[])
    parser.add_argument("--include-known-venvs", action="store_true")
    args = parser.parse_args()

    model = Path(args.model)
    if not model.exists():
        print(json.dumps({"error": f"model path does not exist: {model}"}, indent=2))
        return 2

    selection = select_mlx_environment(tuple(_build_candidates(args)))
    print(json.dumps({"environment_selection": selection_to_dict(selection)}, indent=2))
    if not selection.ok or selection.selected is None:
        return 2

    kernel = RuntimeKernel(
        MlxLmSubprocessBackend(
            python_executable=selection.selected.candidate.python_executable
        )
    )
    load_result = kernel.load_model(str(model), memory_gb=args.memory_gb)
    print(json.dumps({"load": asdict(load_result)}, indent=2, default=str))
    if not load_result.ok:
        return 2

    stream_result = asyncio.run(
        _run_stream(kernel, prompt=args.prompt, max_tokens=args.max_tokens)
    )
    print(json.dumps({"stream": stream_result}, indent=2, default=str))

    unload_result = kernel.unload_model(str(model))
    print(json.dumps({"unload": asdict(unload_result)}, indent=2, default=str))
    return 0 if unload_result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
