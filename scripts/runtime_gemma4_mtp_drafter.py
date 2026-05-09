#!/usr/bin/env python3
"""Operator entry for Gemma4 MTP drafter readiness and command construction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx.gemma4_mtp_drafter import (
    build_mlx_vlm_generate_argv,
    build_mlx_vlm_mtp_generate_argv,
    parse_mlx_vlm_generate_output,
    readiness_payload,
    run_mlx_vlm_generate,
    run_mlx_vlm_mtp_generate,
)


DEFAULT_TARGET_PATH = "/Users/yeemio/AI/Agent/models/gemma-4-31B-it"
DEFAULT_DRAFT_PATH = (
    "/Users/yeemio/AI/Agent/model-candidates/mlx-community/"
    "gemma-4-31B-it-assistant-bf16"
)
DEFAULT_PYTHON = (
    "/Users/yeemio/AI/gitrep/runtime-probes/"
    "mlx-vlm-mtp-probe/.venv/bin/python"
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--target-path", default=DEFAULT_TARGET_PATH)
    inspect_parser.add_argument("--draft-path", default=DEFAULT_DRAFT_PATH)
    inspect_parser.add_argument("--python-executable", default=DEFAULT_PYTHON)

    command_parser = subparsers.add_parser("command")
    command_parser.add_argument("--target-path", default=DEFAULT_TARGET_PATH)
    command_parser.add_argument("--draft-path", default=DEFAULT_DRAFT_PATH)
    command_parser.add_argument("--python-executable", default=DEFAULT_PYTHON)
    command_parser.add_argument("--prompt", required=True)
    command_parser.add_argument("--max-tokens", type=int, default=64)
    command_parser.add_argument("--temperature", type=float, default=0.0)
    command_parser.add_argument("--draft-block-size", type=int, default=6)
    command_parser.add_argument("--without-drafter", action="store_true")

    parse_parser = subparsers.add_parser("parse-log")
    parse_parser.add_argument("log_path")

    run_parser = subparsers.add_parser("run-smoke")
    run_parser.add_argument("--target-path", default=DEFAULT_TARGET_PATH)
    run_parser.add_argument("--draft-path", default=DEFAULT_DRAFT_PATH)
    run_parser.add_argument("--python-executable", default=DEFAULT_PYTHON)
    run_parser.add_argument("--prompt", required=True)
    run_parser.add_argument("--max-tokens", type=int, default=64)
    run_parser.add_argument("--temperature", type=float, default=0.0)
    run_parser.add_argument("--draft-block-size", type=int, default=6)
    run_parser.add_argument("--timeout-s", type=float, default=900.0)
    run_parser.add_argument("--without-drafter", action="store_true")

    args = parser.parse_args()

    if args.command == "inspect":
        _print_json(
            readiness_payload(
                target_path=args.target_path,
                draft_path=args.draft_path,
                python_executable=args.python_executable,
            )
        )
        return 0

    if args.command == "command":
        _print_json(
            {
                "argv": list(
                    build_mlx_vlm_generate_argv(
                        python_executable=args.python_executable,
                        target_path=args.target_path,
                        draft_path=None if args.without_drafter else args.draft_path,
                        prompt=args.prompt,
                        max_tokens=args.max_tokens,
                        temperature=args.temperature,
                        draft_block_size=args.draft_block_size,
                    )
                )
            }
        )
        return 0

    if args.command == "parse-log":
        text = Path(args.log_path).read_text(encoding="utf-8")
        _print_json(parse_mlx_vlm_generate_output(stdout_text=text))
        return 0

    if args.command == "run-smoke":
        if args.without_drafter:
            payload = run_mlx_vlm_generate(
                python_executable=args.python_executable,
                target_path=args.target_path,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                timeout_s=args.timeout_s,
            )
        else:
            payload = run_mlx_vlm_mtp_generate(
                python_executable=args.python_executable,
                target_path=args.target_path,
                draft_path=args.draft_path,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                draft_block_size=args.draft_block_size,
                timeout_s=args.timeout_s,
            )
        _print_json(payload)
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
