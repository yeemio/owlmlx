#!/usr/bin/env python3
"""Run the first validated large-weight smoke flow through the specimen gate."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from owlmlx.runtime import (
    MlxLmSubprocessBackend,
    RuntimeKernel,
    build_large_weight_specimen_gate,
    specimen_gate_to_dict,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the first owlmlx large-weight smoke behind the specimen gate."
    )
    parser.add_argument("--specimen-path", required=True, help="Local model path to validate.")
    parser.add_argument("--memory-gb", type=float, required=True)
    parser.add_argument("--prompt", default="Reply with exactly OK.")
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument(
        "--include-known-venvs",
        action="store_true",
        help="Expand diagnostics to broader known local environments.",
    )
    parser.add_argument(
        "--execution-mode",
        choices=("default_metal", "force_cpu"),
        default="default_metal",
        help="Execution mode to use for the first smoke.",
    )
    args = parser.parse_args()

    gate = build_large_weight_specimen_gate(
        specimen_path=args.specimen_path,
        include_known_candidates=args.include_known_venvs,
        preferred_execution_mode=args.execution_mode,
    )
    gate_payload = specimen_gate_to_dict(gate)
    print(json.dumps({"gate": gate_payload}, indent=2, sort_keys=True))
    if not gate.smoke_ready:
        return 2

    selected = gate.mlx_environment.selection.selected
    if selected is None:
        return 2

    kernel = RuntimeKernel(
        MlxLmSubprocessBackend(
            python_executable=selected.candidate.python_executable,
            env_overrides=(
                {"MLX_FORCE_CPU": "1"}
                if selected.candidate.execution_mode == "force_cpu"
                else None
            ),
        )
    )
    specimen = str(Path(args.specimen_path).expanduser())
    loaded = kernel.load_model(specimen, memory_gb=args.memory_gb)
    print(json.dumps({"load": asdict(loaded)}, indent=2, default=str))
    if not loaded.ok:
        return 2

    generated = asyncio.run(
        kernel.generate(args.prompt, max_tokens=args.max_tokens)
    )
    print(json.dumps({"generate": asdict(generated)}, indent=2, default=str))

    unloaded = kernel.unload_model(specimen)
    print(json.dumps({"unload": asdict(unloaded)}, indent=2, default=str))
    return 0 if generated.ok and unloaded.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
