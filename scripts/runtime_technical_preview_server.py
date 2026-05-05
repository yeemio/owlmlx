#!/usr/bin/env python3
"""Run the owlmlx technical-preview server with the real MLX subprocess backend."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn

from owlmlx.runtime.technical_preview import DEFAULT_TECHNICAL_PREVIEW_PORT


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Start owlmlx technical-preview serving side-by-side with legacy "
            "oMLX/router services. This does not stop old services."
        )
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_TECHNICAL_PREVIEW_PORT)
    parser.add_argument(
        "--models-root",
        default=os.environ.get("OWLMLX_MODELS_ROOT", "/Users/yeemio/AI/Agent/models"),
        help="Local model root used for model visibility and model-id resolution.",
    )
    parser.add_argument(
        "--runtime-python",
        default=os.environ.get("OWLMLX_RUNTIME_PYTHON", ""),
        help="Python executable used by child mlx-lm runners; defaults to repo .venv/bin/python.",
    )
    parser.add_argument(
        "--comparative-evidence-ledger-path",
        default=os.environ.get("OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH", ""),
        help="Optional JSONL ledger path for comparative-evidence HTTP routes.",
    )
    parser.add_argument(
        "--backend-timeout-s",
        type=float,
        default=float(os.environ.get("OWLMLX_BACKEND_TIMEOUT_S", "600")),
    )
    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Propagate MLX_FORCE_CPU=1 to child runner processes.",
    )
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    os.environ["OWLMLX_MODELS_ROOT"] = str(Path(args.models_root).expanduser())
    os.environ["OWLMLX_BACKEND_TIMEOUT_S"] = str(args.backend_timeout_s)
    if args.runtime_python:
        os.environ["OWLMLX_RUNTIME_PYTHON"] = str(Path(args.runtime_python).expanduser())
    if args.comparative_evidence_ledger_path:
        os.environ["OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH"] = str(
            Path(args.comparative_evidence_ledger_path).expanduser()
        )
    if args.force_cpu:
        os.environ["OWLMLX_FORCE_CPU"] = "1"

    uvicorn.run(
        "owlmlx.runtime.technical_preview:create_technical_preview_app",
        factory=True,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
