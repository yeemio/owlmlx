#!/usr/bin/env python3
"""Operator probe for F-3.1 Gemma4 resident MTP feasibility.

This script is intentionally an operator/bench entry, not an owlmlx runtime
module.  It answers the F-3 prerequisite question: can the local mlx-vlm stack
load Gemma4 target + assistant drafter once and serve multiple speculative
requests from one resident Python process?
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TARGET_PATH = "/Users/yeemio/AI/Agent/models/gemma-4-31B-it"
DEFAULT_DRAFT_PATH = (
    "/Users/yeemio/AI/Agent/model-candidates/mlx-community/"
    "gemma-4-31B-it-assistant-bf16"
)
DEFAULT_PYTHON = (
    "/Users/yeemio/AI/gitrep/runtime-probes/"
    "mlx-vlm-mtp-probe-py311/.venv/bin/python"
)
DEFAULT_OUTPUT_DIR = "files/evidence/owlmlx/bench/f3-resident-mtp"

VERDICT_RESIDENT_APPEND_ONLY = "resident_viable_append_only"
VERDICT_RESIDENT_WITH_TRIM = "resident_viable_with_trim"
VERDICT_BLOCKED_LOCAL_RUNTIME = "blocked_on_local_runtime"
VERDICT_BLOCKED_980 = "blocked_on_980"
VERDICT_FAILED = "failed"


@dataclass(frozen=True)
class ProbeConfig:
    python_executable: str
    target_path: str
    draft_path: str
    output_dir: Path
    max_tokens: int
    request_count: int
    draft_block_size: int
    timeout_s: float


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_python_json(
    *,
    python_executable: str,
    code: str,
    args: list[str] | None = None,
    timeout_s: float = 30.0,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [python_executable, "-c", code, *(args or [])],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "returncode": None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "stdout": "",
            "stderr": "",
        }
    payload: dict[str, Any]
    try:
        payload = json.loads(completed.stdout.strip() or "{}")
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "error": "child_stdout_not_json",
            "stdout": completed.stdout[-4000:],
        }
    payload.setdefault("ok", completed.returncode == 0)
    payload["returncode"] = completed.returncode
    payload["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
    payload["stderr"] = completed.stderr[-4000:]
    return payload


def inspect_api(*, python_executable: str) -> dict[str, Any]:
    code = r'''
import importlib
import importlib.metadata as metadata
import inspect
import json

payload = {
    "schema_version": "f3.resident_api_inspection.v1",
    "python_executable": __import__("sys").executable,
    "ok": False,
    "versions": {},
    "surfaces": {},
    "errors": [],
}
for name in ("mlx-vlm", "mlx-lm", "mlx"):
    try:
        payload["versions"][name] = metadata.version(name)
    except Exception as exc:
        payload["versions"][name] = None
        payload["errors"].append(f"{name}: {type(exc).__name__}: {exc}")
try:
    import mlx.core as mx
    payload["surfaces"]["mlx_core_import"] = True
except Exception as exc:
    payload["surfaces"]["mlx_core_import"] = False
    payload["errors"].append(f"mlx.core: {type(exc).__name__}: {exc}")
try:
    gen = importlib.import_module("mlx_vlm.generate")
    drafters = importlib.import_module("mlx_vlm.speculative.drafters")
    for attr in ("load", "generate", "stream_generate", "PromptCacheState"):
        obj = getattr(gen, attr, None)
        payload["surfaces"][f"mlx_vlm.generate.{attr}"] = obj is not None
        if obj is not None:
            try:
                payload["surfaces"][f"signature.{attr}"] = str(inspect.signature(obj))
            except Exception:
                pass
    payload["surfaces"]["mlx_vlm.speculative.drafters.load_drafter"] = (
        getattr(drafters, "load_drafter", None) is not None
    )
except Exception as exc:
    payload["errors"].append(f"mlx_vlm: {type(exc).__name__}: {exc}")
required = (
    "mlx_core_import",
    "mlx_vlm.generate.load",
    "mlx_vlm.generate.stream_generate",
    "mlx_vlm.generate.PromptCacheState",
    "mlx_vlm.speculative.drafters.load_drafter",
)
payload["resident_api_candidate"] = all(payload["surfaces"].get(item) for item in required)
payload["ok"] = payload["resident_api_candidate"]
print(json.dumps(payload, sort_keys=True))
'''
    return _run_python_json(
        python_executable=python_executable,
        code=code,
        timeout_s=30.0,
    )


def _resident_probe_child_code() -> str:
    return r'''
import json
import sys
import time
import traceback
import importlib.metadata as metadata

target_path = sys.argv[1]
draft_path = sys.argv[2]
max_tokens = int(sys.argv[3])
request_count = int(sys.argv[4])
draft_block_size = int(sys.argv[5])

trim_calls = []

def _patch_trim_counter():
    from mlx_vlm.models import cache as vlm_cache
    for cls_name in ("KVCache", "RotatingKVCache", "CacheList", "SimpleKVCache", "SlidingWindowCache", "StaticKVCache"):
        cls = getattr(vlm_cache, cls_name, None)
        if cls is None or not hasattr(cls, "trim"):
            continue
        original = getattr(cls, "trim")
        if getattr(original, "_owlmlx_f3_wrapped", False):
            continue
        def _make_wrapper(name, fn):
            def wrapper(self, n, *args, **kwargs):
                trim_calls.append({"class": name, "n": int(n) if isinstance(n, int) else str(n)})
                return fn(self, n, *args, **kwargs)
            wrapper._owlmlx_f3_wrapped = True
            return wrapper
        setattr(cls, "trim", _make_wrapper(cls_name, original))

payload = {
    "ok": False,
    "versions": {},
    "requests": [],
    "target_load_count": 0,
    "draft_load_count": 0,
    "trim_calls": trim_calls,
}
for name in ("mlx-vlm", "mlx-lm", "mlx"):
    try:
        payload["versions"][name] = metadata.version(name)
    except Exception:
        payload["versions"][name] = None
try:
    from mlx_vlm.generate import PromptCacheState, load, stream_generate
    from mlx_vlm.speculative.drafters import load_drafter

    _patch_trim_counter()

    load_start = time.perf_counter()
    model, processor = load(target_path)
    payload["target_load_count"] = 1
    draft_model = load_drafter(draft_path, kind="mtp")
    payload["draft_load_count"] = 1
    payload["load_elapsed_ms"] = round((time.perf_counter() - load_start) * 1000, 3)

    prompt_cache_state = PromptCacheState()
    prompt = "user: Define local AI in one sentence.\nassistant:"
    previous_lens_len = 0
    for index in range(request_count):
        started = time.perf_counter()
        chunks = []
        chunk_error = None
        try:
            for chunk in stream_generate(
                model,
                processor,
                prompt,
                max_tokens=max_tokens,
                temperature=0.0,
                draft_model=draft_model,
                draft_kind="mtp",
                draft_block_size=draft_block_size,
                prompt_cache_state=prompt_cache_state,
            ):
                chunks.append(
                    {
                        "text": getattr(chunk, "text", ""),
                        "token": int(getattr(chunk, "token", 0) or 0),
                        "prompt_tokens": int(getattr(chunk, "prompt_tokens", 0) or 0),
                        "generation_tokens": int(getattr(chunk, "generation_tokens", 0) or 0),
                    }
                )
        except Exception as exc:
            chunk_error = f"{type(exc).__name__}: {exc}"

        text = "".join(item["text"] for item in chunks)
        lens = list(getattr(draft_model, "accept_lens", None) or [])
        new_lens = lens[previous_lens_len:]
        previous_lens_len = len(lens)
        mean_accepted = (sum(new_lens) / len(new_lens)) if new_lens else 0.0
        request = {
            "index": index,
            "ok": chunk_error is None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "text": text,
            "chunk_count": len(chunks),
            "error": chunk_error,
            "speculative_summary": {
                "mean_accepted_tokens": round(mean_accepted, 6),
                "rounds": len(new_lens),
            },
            "prompt_tokens": chunks[-1]["prompt_tokens"] if chunks else 0,
            "generation_tokens": chunks[-1]["generation_tokens"] if chunks else 0,
        }
        payload["requests"].append(request)
        if chunk_error:
            break
        prompt = prompt + text + "\nuser: Continue with one more short clause.\nassistant:"

    payload["ok"] = (
        payload["target_load_count"] == 1
        and payload["draft_load_count"] == 1
        and len(payload["requests"]) == request_count
        and all(item.get("ok") for item in payload["requests"])
    )
except Exception as exc:
    payload["ok"] = False
    payload["error"] = f"{type(exc).__name__}: {exc}"
    payload["traceback"] = traceback.format_exc()[-4000:]

print(json.dumps(payload, sort_keys=True))
'''


def run_resident_probe(config: ProbeConfig) -> dict[str, Any]:
    return _run_python_json(
        python_executable=config.python_executable,
        code=_resident_probe_child_code(),
        args=[
            config.target_path,
            config.draft_path,
            str(config.max_tokens),
            str(config.request_count),
            str(config.draft_block_size),
        ],
        timeout_s=config.timeout_s,
    )


def classify_verdict(
    *,
    api_inspection: dict[str, Any],
    probe_payload: dict[str, Any] | None,
    request_count: int,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not api_inspection.get("ok"):
        reasons.append("resident_api_surface_unavailable")
        return VERDICT_BLOCKED_LOCAL_RUNTIME, reasons
    if probe_payload is None:
        reasons.append("probe_not_run")
        return VERDICT_BLOCKED_LOCAL_RUNTIME, reasons
    if not probe_payload.get("ok"):
        text = json.dumps(probe_payload, sort_keys=True)
        if "RotatingKVCache" in text or "trim" in text or "is_trimmable" in text:
            reasons.append("hybrid_cache_or_trim_failure")
            return VERDICT_BLOCKED_980, reasons
        reasons.append("resident_probe_failed")
        return VERDICT_FAILED, reasons
    requests = list(probe_payload.get("requests") or [])
    if len(requests) < request_count:
        reasons.append("too_few_requests")
        return VERDICT_FAILED, reasons
    if int(probe_payload.get("target_load_count") or 0) != 1:
        reasons.append("target_reload_observed")
        return VERDICT_FAILED, reasons
    if int(probe_payload.get("draft_load_count") or 0) != 1:
        reasons.append("draft_reload_observed")
        return VERDICT_FAILED, reasons
    summaries = [dict(item.get("speculative_summary") or {}) for item in requests[1:]]
    if not summaries or not all(float(item.get("mean_accepted_tokens") or 0.0) > 0 for item in summaries):
        reasons.append("non_trivial_speculative_summary_missing_after_first_request")
        return VERDICT_FAILED, reasons
    if probe_payload.get("trim_calls"):
        reasons.append("trim_calls_observed")
        return VERDICT_RESIDENT_WITH_TRIM, reasons
    reasons.append("no_trim_calls_observed")
    return VERDICT_RESIDENT_APPEND_ONLY, reasons


def build_verdict_row(
    *,
    config: ProbeConfig,
    api_inspection: dict[str, Any],
    probe_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    verdict, reasons = classify_verdict(
        api_inspection=api_inspection,
        probe_payload=probe_payload,
        request_count=config.request_count,
    )
    trim_calls = list((probe_payload or {}).get("trim_calls") or [])
    cache_regime = "trim" if trim_calls else "append_only"
    requests = list((probe_payload or {}).get("requests") or [])
    summaries = [dict(item.get("speculative_summary") or {}) for item in requests]
    mean_values = [float(item.get("mean_accepted_tokens") or 0.0) for item in summaries]
    return {
        "schema_version": "f3.resident_feasibility.v1",
        "record_type": "resident_mtp_feasibility_probe",
        "timestamp_utc": _now_iso(),
        "gate": "F-3",
        "target": config.target_path,
        "drafter": config.draft_path,
        "python_executable": config.python_executable,
        "api_inspection": api_inspection,
        "versions": (probe_payload or {}).get("versions") or api_inspection.get("versions") or {},
        "reloads_observed": max(0, int((probe_payload or {}).get("target_load_count") or 0) - 1),
        "requests_served": len(requests),
        "mean_accepted_tokens": round(sum(mean_values[1:]) / len(mean_values[1:]), 6)
        if len(mean_values) > 1
        else 0.0,
        "trim_attempted": bool(trim_calls),
        "trim_reason_code": "trim_calls_observed" if trim_calls else None,
        "trim_calls": trim_calls,
        "cache_regime": cache_regime,
        "health_clean_pre_post": None,
        "verdict": verdict,
        "failure_reasons": reasons,
        "probe_payload": probe_payload,
        "used_for_promotion_gate": False,
        "capability_label": "experimental",
    }


def _write_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")


def _default_output_path(output_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return output_dir / f"{stamp}-f3-1-resident-feasibility.jsonl"


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect-api")
    inspect_parser.add_argument("--python-executable", default=DEFAULT_PYTHON)

    run_parser = subparsers.add_parser("run-probe")
    run_parser.add_argument("--python-executable", default=DEFAULT_PYTHON)
    run_parser.add_argument("--target-path", default=DEFAULT_TARGET_PATH)
    run_parser.add_argument("--draft-path", default=DEFAULT_DRAFT_PATH)
    run_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    run_parser.add_argument("--output-path", default=None)
    run_parser.add_argument("--max-tokens", type=int, default=8)
    run_parser.add_argument("--request-count", type=int, default=3)
    run_parser.add_argument("--draft-block-size", type=int, default=6)
    run_parser.add_argument("--timeout-s", type=float, default=1800.0)
    run_parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Write a blocked_on_local_runtime row after API inspection only.",
    )

    args = parser.parse_args()

    if args.command == "inspect-api":
        _print_json(inspect_api(python_executable=args.python_executable))
        return 0

    if args.command == "run-probe":
        config = ProbeConfig(
            python_executable=args.python_executable,
            target_path=args.target_path,
            draft_path=args.draft_path,
            output_dir=Path(args.output_dir),
            max_tokens=args.max_tokens,
            request_count=args.request_count,
            draft_block_size=args.draft_block_size,
            timeout_s=args.timeout_s,
        )
        api = inspect_api(python_executable=config.python_executable)
        probe_payload = None if args.inspect_only or not api.get("ok") else run_resident_probe(config)
        row = build_verdict_row(
            config=config,
            api_inspection=api,
            probe_payload=probe_payload,
        )
        output_path = Path(args.output_path) if args.output_path else _default_output_path(config.output_dir)
        _write_jsonl(output_path, row)
        _print_json({"output_path": str(output_path), "row": row})
        return 0 if row["verdict"].startswith("resident_viable_") else 2

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
