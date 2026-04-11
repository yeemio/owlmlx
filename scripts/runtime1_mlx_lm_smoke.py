#!/usr/bin/env python3
"""Runtime-1/2 mlx-lm smoke probe.

This script is intentionally not part of pytest. It may initialize MLX/Metal
and can crash the child Python process on misconfigured hosts. Use it only as
an explicit operator smoke:

    python scripts/runtime1_mlx_lm_smoke.py --model /path/to/small-mlx-model

Without --model it only runs the isolated import probe.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Local mlx-lm compatible model path")
    parser.add_argument("--memory-gb", type=float, default=1.0)
    parser.add_argument("--prompt", default="Hello")
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--python", default=None)
    parser.add_argument(
        "--python-candidate",
        action="append",
        default=[],
        help="Additional python executable candidates to probe in order",
    )
    parser.add_argument(
        "--include-known-venvs",
        action="store_true",
        help="Also probe known local MLX virtualenvs; may trigger child-process aborts",
    )
    args = parser.parse_args()

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

    selection = select_mlx_environment(tuple(candidates))
    print(json.dumps({"environment_selection": selection_to_dict(selection)}, indent=2))
    if not selection.ok or selection.selected is None:
        return 2
    selected_python = selection.selected.candidate.python_executable

    if not args.model:
        return 0

    model = Path(args.model)
    if not model.exists():
        print(json.dumps({"error": f"model path does not exist: {model}"}, indent=2))
        return 2

    kernel = RuntimeKernel(MlxLmSubprocessBackend(python_executable=selected_python))
    loaded = kernel.load_model(str(model), memory_gb=args.memory_gb)
    print(json.dumps({"load": asdict(loaded)}, indent=2, default=str))
    if not loaded.ok:
        return 2

    ok = True
    for index in range(args.repeat):
        generated = asyncio.run(
            kernel.generate(args.prompt, max_tokens=args.max_tokens)
        )
        print(
            json.dumps(
                {"generate": index + 1, "result": asdict(generated)},
                indent=2,
                default=str,
            )
        )
        ok = ok and generated.ok

    unloaded = kernel.unload_model(str(model))
    print(json.dumps({"unload": asdict(unloaded)}, indent=2, default=str))
    return 0 if ok and unloaded.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
