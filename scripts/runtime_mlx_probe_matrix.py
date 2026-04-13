#!/usr/bin/env python3
"""Emit a structured MLX probe matrix for one interpreter and launch mode."""

from __future__ import annotations

import argparse
import json

from owlmlx.runtime.mlx_lm_backend import probe_python_snippet


PROBE_CASES: tuple[tuple[str, str], ...] = (
    (
        "mlx_core_import",
        "import mlx.core as mx; a = mx.array([1.0, 2.0]); print(a.shape[0])",
    ),
    (
        "mlx_lm_import",
        "import mlx_lm; print(getattr(mlx_lm, '__version__', 'unknown'))",
    ),
    (
        "mlx_lm_load_symbol",
        "from mlx_lm import load; print('load-ok')",
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit a structured MLX probe matrix for one Python baseline."
    )
    parser.add_argument("--python", required=True, help="Python executable to probe.")
    parser.add_argument(
        "--execution-mode",
        choices=("default_metal", "force_cpu"),
        default="default_metal",
        help="Execution mode to probe.",
    )
    parser.add_argument(
        "--launch-mode",
        choices=("direct_exec", "env_wrapper"),
        default="direct_exec",
        help="Child launch mode to compare against shell behavior.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=20.0,
        help="Probe timeout in seconds.",
    )
    args = parser.parse_args()

    probes: list[dict[str, object]] = []
    for probe_id, code in PROBE_CASES:
        result = probe_python_snippet(
            code=code,
            python_executable=args.python,
            timeout_s=args.timeout_s,
            execution_mode=args.execution_mode,
            launch_mode=args.launch_mode,
        )
        probes.append(
            {
                "probe_id": probe_id,
                "ok": result.ok,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": result.message,
            }
        )

    print(
        json.dumps(
            {
                "contract": {
                    "surface": "owlmlx.mlx_probe_matrix",
                    "version": "stabilization2",
                },
                "python_executable": args.python,
                "execution_mode": args.execution_mode,
                "launch_mode": args.launch_mode,
                "probes": probes,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
