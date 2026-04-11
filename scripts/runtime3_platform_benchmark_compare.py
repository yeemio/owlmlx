#!/usr/bin/env python3
"""Runtime-3 same-model benchmark comparison against old platform truth.

This script replays the old platform's dedicated benchmark prompts through the
Runtime-3 streaming kernel so we can compare:

- TTFT
- total latency
- approximate tokens/s from streamed completion counts
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean

from owlmlx.runtime import (
    MlxEnvironmentCandidate,
    MlxLmSubprocessBackend,
    RuntimeKernel,
    default_environment_candidates,
    known_environment_candidates,
    select_mlx_environment,
    selection_to_dict,
)

CASES: dict[str, dict[str, object]] = {
    "short_qa": {
        "prompt": "请用三句话解释 MoE 和 dense 模型的主要区别。",
        "max_tokens": 512,
    },
    "structured_json": {
        "prompt": "请输出一个 JSON，对比 Apple Silicon 本地推理栈中的 vLLM-MLX、oMLX、Router，字段必须为 name、role、risk。",
        "max_tokens": 512,
    },
    "coding": {
        "prompt": "写一个 Python 函数，读取目录下所有 Markdown 文件，提取一级标题并返回字典。",
        "max_tokens": 2048,
    },
}


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


async def _run_case(
    kernel: RuntimeKernel,
    *,
    case_name: str,
    prompt: str,
    max_tokens: int,
) -> dict[str, object]:
    started = time.monotonic()
    first_token_at: float | None = None
    last_done: dict[str, object] | None = None
    token_events = 0
    output_text = ""
    async for event in kernel.generate_stream(prompt, max_tokens=max_tokens):
        if event.event == "token":
            token_events += 1
            output_text = event.text
            if first_token_at is None:
                first_token_at = time.monotonic()
        elif event.event == "done":
            last_done = asdict(event)
        elif event.event == "error":
            return {
                "case": case_name,
                "ok": False,
                "error": event.detail.get("message"),
            }
    finished = time.monotonic()
    ttft_s = (first_token_at - started) if first_token_at is not None else None
    total_s = finished - started
    completion_tokens = int((last_done or {}).get("completion_tokens") or token_events or 0)
    decode_window_s = max(total_s - (ttft_s or 0.0), 0.0001)
    return {
        "case": case_name,
        "ok": True,
        "ttft_s": round(ttft_s, 4) if ttft_s is not None else None,
        "total_s": round(total_s, 4),
        "completion_tokens": completion_tokens,
        "tokens_per_sec": round(completion_tokens / decode_window_s, 1),
        "response_preview": output_text[:240],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--memory-gb", type=float, required=True)
    parser.add_argument("--gate-file", default="/Users/yeemio/AI/Agent/model_fleet/benchmark_gate.json")
    parser.add_argument("--python", default=None)
    parser.add_argument("--python-candidate", action="append", default=[])
    parser.add_argument("--include-known-venvs", action="store_true")
    args = parser.parse_args()

    gate_path = Path(args.gate_file)
    model_path = Path(args.model)
    if not gate_path.exists():
        print(json.dumps({"error": f"gate file does not exist: {gate_path}"}, indent=2))
        return 2
    if not model_path.exists():
        print(json.dumps({"error": f"model path does not exist: {model_path}"}, indent=2))
        return 2

    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    platform_record = gate["models"].get(model_path.name)
    if platform_record is None:
        print(json.dumps({"error": f"no old-platform benchmark record for {model_path.name}"}, indent=2))
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
    load_result = kernel.load_model(str(model_path), memory_gb=args.memory_gb)
    print(json.dumps({"load": asdict(load_result)}, indent=2, default=str))
    if not load_result.ok:
        return 2

    case_results = []
    for case_name, config in CASES.items():
        case_results.append(
            asyncio.run(
                _run_case(
                    kernel,
                    case_name=case_name,
                    prompt=str(config["prompt"]),
                    max_tokens=int(config["max_tokens"]),
                )
            )
        )

    unload_result = kernel.unload_model(str(model_path))
    print(json.dumps({"cases": case_results}, indent=2, default=str))
    print(json.dumps({"unload": asdict(unload_result)}, indent=2, default=str))
    if not unload_result.ok or not all(row["ok"] for row in case_results):
        return 2

    owl_ttft = [float(row["ttft_s"]) for row in case_results if row["ttft_s"] is not None]
    owl_total = [float(row["total_s"]) for row in case_results]
    owl_tps = [float(row["tokens_per_sec"]) for row in case_results]
    summary = {
        "model": model_path.name,
        "owlmlx_runtime3": {
            "avg_ttft_seconds": round(mean(owl_ttft), 3) if owl_ttft else None,
            "avg_total_seconds": round(mean(owl_total), 3),
            "avg_tokens_per_sec": round(mean(owl_tps), 1),
        },
        "old_platform": {
            "avg_ttft_seconds": platform_record.get("avg_ttft_seconds"),
            "avg_total_seconds": platform_record.get("avg_total_seconds"),
            "avg_tokens_per_sec": platform_record.get("avg_tokens_per_sec"),
            "gate_verdict": platform_record.get("gate_verdict"),
        },
        "delta": {
            "ttft_seconds": (
                round(mean(owl_ttft) - float(platform_record["avg_ttft_seconds"]), 3)
                if owl_ttft and platform_record.get("avg_ttft_seconds") is not None
                else None
            ),
            "total_seconds": round(mean(owl_total) - float(platform_record["avg_total_seconds"]), 3),
            "tokens_per_sec": (
                round(mean(owl_tps) - float(platform_record["avg_tokens_per_sec"]), 1)
                if platform_record.get("avg_tokens_per_sec") is not None
                else None
            ),
        },
    }
    print(json.dumps({"summary": summary}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
