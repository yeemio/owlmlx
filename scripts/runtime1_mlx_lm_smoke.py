#!/usr/bin/env python3
"""Runtime-1 mlx-lm smoke probe.

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
import sys

from owlmlx.runtime import MlxLmBackend, RuntimeKernel
from owlmlx.runtime.mlx_lm_backend import probe_mlx_lm_import


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Local mlx-lm compatible model path")
    parser.add_argument("--memory-gb", type=float, default=1.0)
    parser.add_argument("--prompt", default="Hello")
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    probe = probe_mlx_lm_import(python_executable=args.python)
    print(json.dumps({"import_probe": asdict(probe)}, indent=2))
    if not probe.ok:
        return 2

    if not args.model:
        return 0

    model = Path(args.model)
    if not model.exists():
        print(json.dumps({"error": f"model path does not exist: {model}"}, indent=2))
        return 2

    kernel = RuntimeKernel(MlxLmBackend(python_executable=args.python))
    loaded = kernel.load_model(str(model), memory_gb=args.memory_gb)
    print(json.dumps({"load": asdict(loaded)}, indent=2, default=str))
    if not loaded.ok:
        return 2

    generated = asyncio.run(
        kernel.generate(args.prompt, max_tokens=args.max_tokens)
    )
    print(json.dumps({"generate": asdict(generated)}, indent=2, default=str))
    return 0 if generated.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
