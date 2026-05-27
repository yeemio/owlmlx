"""D1 DeepSeek V4 isolated repeatability runner.

This script is intentionally isolated from the stock owlmlx runtime. Preflight
checks the caller-selected DeepSeek V4 Python environment and model path; dry-run
only writes synthetic schema smoke rows to an explicit output directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ISOLATED_RUNTIME_PATH = REPO_ROOT / ".runtime-deepseek-v4-mlx"
DEFAULT_ISOLATED_PYTHON = DEFAULT_ISOLATED_RUNTIME_PATH / "bin" / "python"
DEFAULT_MODEL_PATH = Path(
    "/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ"
)
MODEL_ID = "DeepSeek-V4-Flash-2bit-DQ"
MODEL_TYPE = "deepseek_v4"
DEEPSEEK_V4_MODULE = "mlx_lm.models.deepseek_v4"
TOKEN_LADDER = (128, 512, 1024)
EVIDENCE_STRENGTH = "synthetic_dry_run_no_model_claim"
REAL_EVIDENCE_STRENGTH = "isolated_real_child_process"
COMPARE_EVIDENCE_STRENGTH = "diagnostic_direct_vs_runner_compare"
D1_TOKENIZER_CONFIG = {
    "pretrained_config": {
        "max_position_embeddings": 1048576,
        "model_type": MODEL_TYPE,
    }
}
D1_GENERATION_DEFAULTS = {
    "max_kv_size": 512,
    "temperature": 0.0,
}
D1_PROMPT_SURFACE_DEFAULT = "messages"
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "files" / "evidence" / "owlmlx" / "deepseek-v4" / "d1-isolated-repeatability"
)
D2_EVIDENCE_STRENGTH = "isolated_real_stream_metrics"
D2_DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "files" / "evidence" / "owlmlx" / "deepseek-v4" / "d2-metrics-ledger"
)
D3_EVIDENCE_STRENGTH = "local_checkpoint_metadata_inspection"
D3_DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "files"
    / "evidence"
    / "owlmlx"
    / "deepseek-v4"
    / "d3-checkpoint-inspection"
)
D3_MTP_MISSING_REASON = "mtp_weights_absent_or_stripped"
D4_EVIDENCE_STRENGTH = "clean_preload_reject_with_health_probe"
D4_DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "files"
    / "evidence"
    / "owlmlx"
    / "deepseek-v4"
    / "d4-preload-reject"
)
DEFAULT_RUNTIME_HEALTH_URL = "http://127.0.0.1:8066/healthz"
RSS_SAMPLE_SCOPE = "child_process"
RSS_SAMPLE_SOURCE = "ps_rss_kb"
RSS_SAMPLE_TIMING = "after_generation_before_unload"
RUNNER_MODULE = "owlmlx.runtime.mlx_lm_runner"
DEFAULT_DEEPSEEK_ADAPTER_PATH = Path("/tmp/mlx-lm-dsv4")
D6_EVIDENCE_STRENGTH = "mainline_backend_lifecycle"
D6_DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "files"
    / "evidence"
    / "owlmlx"
    / "deepseek-v4"
    / "d6-mainline-backend-integration"
)
D6_DEFAULT_BASELINE_PATH = (
    REPO_ROOT
    / "files"
    / "evidence"
    / "owlmlx"
    / "deepseek-v4"
    / "d2-metrics-ledger"
    / "20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl"
)
D6_DEFAULT_BACKEND_PYTHON = (
    REPO_ROOT / ".runtime-deepseek-experimental" / "bin" / "python"
)
D6_EXPECTED_MLX_LM_GIT_COMMIT = "5c10538136b9038b9626c134612b08afc18d697a"
D6_TTFT_DRIFT_REL_THRESHOLD = 0.20
D6_DECODE_TPS_DRIFT_REL_THRESHOLD = 0.15
D6_CHILD_RSS_DRIFT_ABS_THRESHOLD = 1.0
D6_FREED_GB_LOWER_BOUND = 80.0
D6_DEFAULT_PROMPT_IDS: tuple[str, ...] = (
    "p1_short_cn",
    "p2_short_en",
    "p4_long_context",
)
D6_DEFAULT_MAX_TOKENS_LADDER: tuple[int, ...] = (128, 512)
MTP_WEIGHT_TERMS = (
    "mtp",
    "draft",
    "eagle",
    "medusa",
    "nextn",
    "next_n",
    "next-token",
    "next_token",
    "speculative",
)

PROMPTS = (
    ("p1_short_cn", "用两句话说明 owlmlx 的运行时边界。"),
    ("p2_short_en", "Answer in two concise English sentences about runtime isolation."),
    ("p3_code", "Return a tiny Python function named add_one."),
    ("p4_long_context", "Summarize why repeatability needs lifecycle evidence. " * 48),
    ("p5_stop_marker", "Reply with one short paragraph and stop before <END>."),
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compact_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _token_ladder_from_cli(
    values: list[int] | list[list[int]] | None,
    *,
    default: tuple[int, ...],
) -> tuple[int, ...]:
    if values is None:
        return default
    tokens: list[int] = []
    for value in values:
        if isinstance(value, list):
            tokens.extend(int(item) for item in value)
        else:
            tokens.append(int(value))
    return tuple(tokens)


def _append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True))
            stream.write("\n")


def _runner_command(isolated_python: Path) -> list[str]:
    return [str(isolated_python), "-m", RUNNER_MODULE]


def _runner_env(*, base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), *([existing] if existing else [])]
    )
    return env


def _prompt_by_id(prompt_id: str) -> tuple[int, str, str]:
    for index, (known_id, prompt) in enumerate(PROMPTS, start=1):
        if known_id == prompt_id:
            return index, known_id, prompt
    known = ", ".join(prompt_id for prompt_id, _prompt in PROMPTS)
    raise ValueError(f"unknown prompt_id {prompt_id!r}; known values: {known}")


def _relative_runtime_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _check_isolated_imports(python_path: Path, timeout_s: float = 20.0) -> dict[str, Any]:
    code = f"""
import importlib.metadata
import importlib.util
import json
import pathlib
import subprocess

mods = {json.dumps(["mlx_lm", DEEPSEEK_V4_MODULE])}
imports = {{}}
module_origins = {{}}
git_sources = {{}}


def _git(cwd, args):
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
    except Exception:
        return None
    value = proc.stdout.strip()
    return value or None


def _git_source(origin):
    if not origin:
        return {{}}
    path = pathlib.Path(origin)
    cwd = path.parent if path.suffix else path
    root = _git(cwd, ["rev-parse", "--show-toplevel"])
    if not root:
        return {{}}
    return {{
        "git_root": root,
        "git_commit": _git(root, ["rev-parse", "HEAD"]),
        "git_branch": _git(root, ["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_remote": _git(root, ["config", "--get", "remote.origin.url"]),
    }}


for mod in mods:
    try:
        spec = importlib.util.find_spec(mod)
    except ModuleNotFoundError:
        spec = None
    imports[mod] = spec is not None
    origin = getattr(spec, "origin", None) if spec is not None else None
    module_origins[mod] = origin
    git_sources[mod] = _git_source(origin)

try:
    mlx_lm_version = importlib.metadata.version("mlx-lm")
except importlib.metadata.PackageNotFoundError:
    mlx_lm_version = None

runtime_source = {{
    "mlx_lm": {{
        "module": "mlx_lm",
        "origin": module_origins.get("mlx_lm"),
        "package_version": mlx_lm_version,
        **git_sources.get("mlx_lm", {{}}),
    }},
    "deepseek_v4": {{
        "module": {json.dumps(DEEPSEEK_V4_MODULE)},
        "origin": module_origins.get({json.dumps(DEEPSEEK_V4_MODULE)}),
        **git_sources.get({json.dumps(DEEPSEEK_V4_MODULE)}, {{}}),
    }},
}}

print(json.dumps({{
    "imports": imports,
    "module_origins": module_origins,
    "package_versions": {{"mlx-lm": mlx_lm_version}},
    "runtime_source": runtime_source,
}}, sort_keys=True))
"""
    try:
        proc = subprocess.run(
            [str(python_path), "-c", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except OSError as exc:
        return {
            "ok": False,
            "returncode": None,
            "imports": {},
            "module_origins": {},
            "package_versions": {},
            "runtime_source": {},
            "stderr": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "imports": {},
            "module_origins": {},
            "package_versions": {},
            "runtime_source": {},
            "stderr": f"import preflight timed out after {exc.timeout}s",
        }

    imports: dict[str, bool] = {}
    module_origins: dict[str, str | None] = {}
    package_versions: dict[str, str | None] = {}
    runtime_source: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout.strip().splitlines()[-1])
            if isinstance(parsed, dict) and "imports" in parsed:
                imports = {
                    str(key): bool(value)
                    for key, value in dict(parsed.get("imports", {})).items()
                }
                module_origins = {
                    str(key): value
                    for key, value in dict(parsed.get("module_origins", {})).items()
                }
                package_versions = {
                    str(key): value
                    for key, value in dict(parsed.get("package_versions", {})).items()
                }
                runtime_source = dict(parsed.get("runtime_source", {}))
            else:
                imports = {str(key): bool(value) for key, value in parsed.items()}
        except json.JSONDecodeError:
            imports = {}
    return {
        "ok": proc.returncode == 0 and all(imports.get(name) for name in (
            "mlx_lm",
            DEEPSEEK_V4_MODULE,
        )),
        "returncode": proc.returncode,
        "imports": imports,
        "module_origins": module_origins,
        "package_versions": package_versions,
        "runtime_source": runtime_source,
        "stderr": proc.stderr.strip(),
    }


def run_preflight(
    *,
    isolated_python: Path = DEFAULT_ISOLATED_PYTHON,
    model_path: Path = DEFAULT_MODEL_PATH,
    isolated_runtime_path: Path = DEFAULT_ISOLATED_RUNTIME_PATH,
) -> dict[str, Any]:
    isolated_python = Path(isolated_python)
    model_path = Path(model_path)
    isolated_runtime_path = Path(isolated_runtime_path)

    checks = {
        "isolated_python_exists": isolated_python.exists(),
        "isolated_python_is_file": isolated_python.is_file(),
        "model_path_exists": model_path.exists(),
        "model_path_is_dir": model_path.is_dir(),
    }
    import_check: dict[str, Any] = {
        "ok": False,
        "returncode": None,
        "imports": {},
        "stderr": "isolated python path is not available",
    }
    if checks["isolated_python_exists"] and checks["isolated_python_is_file"]:
        import_check = _check_isolated_imports(isolated_python)

    blocked_reasons: list[str] = []
    if not checks["isolated_python_exists"]:
        blocked_reasons.append("isolated_python_missing")
    elif not checks["isolated_python_is_file"]:
        blocked_reasons.append("isolated_python_not_file")
    if not checks["model_path_exists"]:
        blocked_reasons.append("model_path_missing")
    elif not checks["model_path_is_dir"]:
        blocked_reasons.append("model_path_not_directory")
    if not import_check["imports"].get("mlx_lm"):
        blocked_reasons.append("mlx_lm_import_missing")
    if not import_check["imports"].get(DEEPSEEK_V4_MODULE):
        blocked_reasons.append("deepseek_v4_import_missing")

    verdict = "passed" if not blocked_reasons and import_check["ok"] else "blocked"
    runtime_source = dict(import_check.get("runtime_source", {}))
    return {
        "schema_version": "d1.preflight.v1",
        "gate": "D1",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "model_type": MODEL_TYPE,
        "preflight": verdict,
        "verdict": verdict,
        "blocked_reasons": blocked_reasons,
        "checks": checks,
        "import_check": import_check,
        "runtime_source": runtime_source,
        "mlx_lm_source": dict(runtime_source.get("mlx_lm", {})),
        "isolation": {
            "isolated_runtime_path": _relative_runtime_path(isolated_runtime_path),
            "isolated_python": str(isolated_python),
            "model_path": str(model_path),
            "stock_runtime_untouched": True,
            "default_model_surface_unchanged": True,
            "ds4_c_adopted": False,
        },
    }


def _base_record(
    *,
    run_id: str,
    output_path: Path,
    isolated_runtime_path: Path,
    isolated_python: Path,
    model_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "d1.v1",
        "run_id": run_id,
        "created_at": _now_utc(),
        "gate": "D1",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "model_type": MODEL_TYPE,
        "capability_label": "experimental_only",
        "evidence_strength": EVIDENCE_STRENGTH,
        "output_path": str(output_path),
        "isolation": {
            "isolated_runtime_path": _relative_runtime_path(isolated_runtime_path),
            "isolated_python": str(isolated_python),
            "model_path": str(model_path),
            "stock_runtime_untouched": True,
            "default_model_surface_unchanged": True,
            "ds4_c_adopted": False,
        },
        "token_ladder": list(TOKEN_LADDER),
        "lifecycle": {
            "preflight": "synthetic_skipped",
            "load_ok": True,
            "generate_ok": True,
            "unload_ok": True,
            "clean_health_after_unload": True,
            "health_after_unload": "synthetic_clean",
        },
        "child_restart_detection": {
            "method": "placeholder_not_measured_in_dry_run",
            "restart_observed": False,
        },
        "metrics": {
            "load_time_s": None,
            "ttft_ms_by_prompt": {},
            "decode_tps_by_prompt": {},
            "child_rss_gb": None,
            "rss_sample_scope": RSS_SAMPLE_SCOPE,
            "rss_sample_source": RSS_SAMPLE_SOURCE,
            "rss_sample_timing": RSS_SAMPLE_TIMING,
            "peak_rss_gb": None,
        },
    }


def run_dry_run(
    *,
    output_dir: Path,
    isolated_runtime_path: Path = DEFAULT_ISOLATED_RUNTIME_PATH,
    isolated_python: Path = DEFAULT_ISOLATED_PYTHON,
    model_path: Path = DEFAULT_MODEL_PATH,
    run_id: str | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    run_id = run_id or f"{_compact_stamp()}-d1-deepseek-v4-synthetic-dry-run"
    output_path = output_dir / f"{run_id}.jsonl"
    rows: list[dict[str, Any]] = []
    for prompt_index, (prompt_id, prompt) in enumerate(PROMPTS, start=1):
        for max_tokens in TOKEN_LADDER:
            record = _base_record(
                run_id=run_id,
                output_path=output_path,
                isolated_runtime_path=isolated_runtime_path,
                isolated_python=isolated_python,
                model_path=model_path,
            )
            record.update(
                {
                    "record_type": "prompt_result",
                    "prompt_index": prompt_index,
                    "prompt_id": prompt_id,
                    "prompt_sha_hint": f"synthetic-{prompt_id}",
                    "max_tokens": max_tokens,
                    "prompt_results": [
                        {
                            "prompt_index": prompt_index,
                            "prompt_id": prompt_id,
                            "max_tokens": max_tokens,
                            "ok": True,
                            "completion_chars": len(prompt_id) + max_tokens // 64,
                            "stop_reason": "synthetic_stop",
                            "restart_observed": False,
                            "repetition_flag": False,
                        }
                    ],
                    "verdict": "passed",
                }
            )
            _ = prompt
            rows.append(record)

    _append_jsonl(output_path, rows)
    return {
        "schema_version": "d1.v1",
        "run_id": run_id,
        "gate": "D1",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "evidence_strength": EVIDENCE_STRENGTH,
        "output_path": str(output_path),
        "rows_written": len(rows),
        "prompt_count": len(PROMPTS),
        "token_ladder": list(TOKEN_LADDER),
        "verdict": "passed",
    }


def _read_json_payload(proc: subprocess.Popen[str], *, timeout_s: float) -> dict[str, Any]:
    stdout = proc.stdout
    if stdout is None:
        raise RuntimeError("child stdout pipe is unavailable")

    deadline = time.monotonic() + timeout_s
    discarded: list[str] = []
    try:
        stdout_fd = stdout.fileno()
    except (AttributeError, OSError, ValueError):
        stdout_fd = None

    if stdout_fd is not None:
        buffered = getattr(proc, "_owlmlx_stdout_buffer", "")
        while True:
            if "\n" in buffered:
                line, buffered = buffered.split("\n", 1)
                setattr(proc, "_owlmlx_stdout_buffer", buffered)
                text = line.strip()
                if not text:
                    continue
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    discarded.append(text)
                    continue
                if isinstance(payload, dict):
                    if discarded:
                        payload["_discarded_stdout"] = discarded[-5:]
                    return payload

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                setattr(proc, "_owlmlx_stdout_buffer", buffered)
                raise TimeoutError("timed out waiting for child response")

            ready, _, _ = select.select([stdout_fd], [], [], remaining)
            if not ready:
                setattr(proc, "_owlmlx_stdout_buffer", buffered)
                raise TimeoutError("timed out waiting for child response")

            chunk = os.read(stdout_fd, 4096)
            if not chunk:
                setattr(proc, "_owlmlx_stdout_buffer", buffered)
                raise RuntimeError("child process produced no output")
            buffered += chunk.decode("utf-8", errors="replace")

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("timed out waiting for child response")

        try:
            ready, _, _ = select.select([stdout], [], [], remaining)
        except (OSError, ValueError, TypeError):
            ready = [stdout]
        if not ready:
            raise TimeoutError("timed out waiting for child response")

        line = stdout.readline()
        if not line:
            raise RuntimeError("child process produced no output")
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            discarded.append(text)
            continue
        if isinstance(payload, dict):
            if discarded:
                payload["_discarded_stdout"] = discarded[-5:]
            return payload


def _write_child_request(
    proc: subprocess.Popen[str],
    request: dict[str, Any],
) -> None:
    if proc.poll() is not None:
        raise RuntimeError(f"child process exited before request: {proc.returncode}")
    if proc.stdin is None:
        raise RuntimeError("child stdin pipe is unavailable")
    proc.stdin.write(json.dumps(request, sort_keys=True) + "\n")
    proc.stdin.flush()


def _child_exchange(
    proc: subprocess.Popen[str],
    request: dict[str, Any],
    *,
    timeout_s: float,
) -> dict[str, Any]:
    _write_child_request(proc, request)
    return _read_json_payload(proc, timeout_s=timeout_s)


def _child_stream_generate(
    proc: subprocess.Popen[str],
    request: dict[str, Any],
    *,
    timeout_s: float,
) -> dict[str, Any]:
    request_action = str(request.get("action") or "stream_generate")
    _write_child_request(proc, request)
    text_parts: list[str] = []
    token_event_count = 0
    stream_diagnostics: list[dict[str, Any]] = []
    last_token: dict[str, Any] | None = None
    while True:
        try:
            payload = _read_json_payload(proc, timeout_s=timeout_s)
        except TimeoutError as exc:
            return {
                "ok": False,
                "action": request_action,
                "text": "".join(text_parts),
                "error": str(exc),
                "pid": proc.pid,
                "finish_reason": "stream_timeout",
                "stream_timeout": True,
                "timeout_s": timeout_s,
                "stream_event_count": token_event_count,
                "stream_diagnostic_count": len(stream_diagnostics),
                "stream_diagnostics": stream_diagnostics,
            }
        if not payload.get("ok", False):
            return {
                "ok": False,
                "action": request_action,
                "text": "".join(text_parts),
                "error": payload.get("error") or payload.get("message"),
                "pid": payload.get("pid"),
                "finish_reason": payload.get("finish_reason"),
                "stream_event_count": token_event_count,
                "stream_diagnostic_count": len(stream_diagnostics),
                "stream_diagnostics": stream_diagnostics,
            }

        action = str(payload.get("action") or "")
        event = str(payload.get("event") or "")
        if action in {"stream_event", "stream_message_event"} and event == "token":
            text_parts.append(str(payload.get("text") or ""))
            token_event_count += 1
            last_token = payload
            continue
        if action in {"stream_done", "stream_message_done"} and event == "done":
            timing = payload.get("timing") if isinstance(payload.get("timing"), dict) else {}
            return {
                "ok": True,
                "action": request_action,
                "text": "".join(text_parts),
                "finish_reason": payload.get("finish_reason")
                or (last_token or {}).get("finish_reason"),
                "pid": payload.get("pid") or (last_token or {}).get("pid"),
                "generation_count": payload.get("generation_count"),
                "prompt_tokens": payload.get("prompt_tokens")
                if payload.get("prompt_tokens") is not None
                else (last_token or {}).get("prompt_tokens"),
                "completion_tokens": payload.get("completion_tokens")
                if payload.get("completion_tokens") is not None
                else (last_token or {}).get("completion_tokens"),
                "timing": timing,
                "stream_event_count": token_event_count,
                "stream_diagnostic_count": len(stream_diagnostics),
                "stream_diagnostics": stream_diagnostics,
            }
        diagnostic = {
            key: payload.get(key)
            for key in (
                "action",
                "event",
                "terminal_action",
                "model_id",
                "pid",
                "sequence",
            )
            if payload.get(key) is not None
        }
        if diagnostic and len(stream_diagnostics) < 16:
            stream_diagnostics.append(diagnostic)


def _repetition_diagnostics(text: str) -> dict[str, Any]:
    normalized = " ".join(text.split())
    method = "fixed_window_repeat_v1"
    window_size = 40
    minimum_repeat_count = 4
    if len(normalized) < 120:
        return {
            "method": method,
            "repetition_flag": False,
            "normalized_length": len(normalized),
            "window_size": window_size,
            "minimum_repeat_count": minimum_repeat_count,
            "max_repeated_window_count": 0,
            "repeated_window_sha256": None,
            "repeated_window_preview": None,
        }
    windows = [
        normalized[index : index + window_size]
        for index in range(0, len(normalized), window_size)
    ]
    counts = {window: windows.count(window) for window in windows if window}
    repeated_window = max(counts, key=lambda item: counts[item]) if counts else None
    max_count = counts.get(repeated_window, 0) if repeated_window is not None else 0
    return {
        "method": method,
        "repetition_flag": max_count >= minimum_repeat_count,
        "normalized_length": len(normalized),
        "window_size": window_size,
        "minimum_repeat_count": minimum_repeat_count,
        "max_repeated_window_count": max_count,
        "repeated_window_sha256": (
            hashlib.sha256(repeated_window.encode("utf-8")).hexdigest()
            if repeated_window is not None
            else None
        ),
        "repeated_window_preview": repeated_window[:80] if repeated_window else None,
    }


def _completion_observation(text: str) -> dict[str, Any]:
    preview_chars = 240
    return {
        "completion_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "completion_preview": text[:preview_chars],
        "completion_tail": text[-preview_chars:] if len(text) > preview_chars else text,
    }


def _prompt_shape(prompt: str) -> dict[str, Any]:
    preview_chars = 160
    return {
        "surface": "raw_text",
        "prompt_chars": len(prompt),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_preview": prompt[:preview_chars],
    }


def _messages_for_prompt(prompt: str) -> list[dict[str, str]]:
    return [{"role": "user", "content": prompt}]


def _prompt_shape_for_surface(
    *,
    prompt: str,
    prompt_surface: str,
) -> dict[str, Any]:
    if prompt_surface == "raw":
        return _prompt_shape(prompt)
    messages = _messages_for_prompt(prompt)
    encoded = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return {
        "surface": "chat_messages",
        "message_count": len(messages),
        "roles": [message["role"] for message in messages],
        "content_chars": sum(len(message["content"]) for message in messages),
        "messages_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "first_user_content_preview": prompt[:160],
    }


def _generation_params(*, max_tokens: int, overrides: dict[str, Any]) -> dict[str, Any]:
    params = {**D1_GENERATION_DEFAULTS}
    params.update(
        {key: value for key, value in overrides.items() if value is not None}
    )
    params["max_tokens"] = int(max_tokens)
    return params


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _decode_tps_after_first_token(
    *,
    completion_tokens: Any,
    first_visible_token_ms: Any,
    stream_wall_ms: Any,
) -> float | None:
    tokens = _as_float(completion_tokens)
    ttft_ms = _as_float(first_visible_token_ms)
    wall_ms = _as_float(stream_wall_ms)
    if tokens is None or wall_ms is None or tokens <= 1:
        return None
    decode_ms = wall_ms - (ttft_ms or 0.0)
    if decode_ms <= 0:
        return None
    return round((tokens - 1.0) / (decode_ms / 1000.0), 4)


def _wall_tps(
    *,
    completion_tokens: Any,
    stream_wall_ms: Any,
) -> float | None:
    tokens = _as_float(completion_tokens)
    wall_ms = _as_float(stream_wall_ms)
    if tokens is None or wall_ms is None or tokens <= 0 or wall_ms <= 0:
        return None
    return round(tokens / (wall_ms / 1000.0), 4)


def _process_rss_gb(pid: Any, *, run_factory: Any = subprocess.run) -> float | None:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return None
    if pid_int <= 0:
        return None
    try:
        proc = run_factory(
            ["ps", "-o", "rss=", "-p", str(pid_int)],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.0,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    lines = str(proc.stdout or "").strip().splitlines()
    if not lines:
        return None
    try:
        rss_kb = float(lines[-1].strip())
    except ValueError:
        return None
    return round(rss_kb / 1024.0 / 1024.0, 6)


def _real_record(
    *,
    run_id: str,
    output_path: Path,
    isolated_runtime_path: Path,
    isolated_python: Path,
    model_path: Path,
    prompt_index: int,
    prompt_id: str,
    prompt: str,
    prompt_surface: str,
    max_tokens: int,
    generation_params: dict[str, Any],
    load_ok: bool,
    unload_ok: bool,
    clean_health_after_unload: bool,
    load_time_s: float | None,
    child_rss_gb: float | None,
    result: dict[str, Any],
    load_pid: Any,
) -> dict[str, Any]:
    text = str(result.get("text") or "")
    result_pid = result.get("pid")
    generation_surface = str(result.get("action") or "generate")
    timing = result.get("timing") if isinstance(result.get("timing"), dict) else {}
    first_visible_token_ms = timing.get("first_visible_token_ms")
    stream_wall_ms = timing.get("stream_wall_ms")
    completion_tokens = result.get("completion_tokens")
    decode_tps = _decode_tps_after_first_token(
        completion_tokens=completion_tokens,
        first_visible_token_ms=first_visible_token_ms,
        stream_wall_ms=stream_wall_ms,
    )
    wall_tps = _wall_tps(
        completion_tokens=completion_tokens,
        stream_wall_ms=stream_wall_ms,
    )
    if generation_surface in {"stream_generate", "stream_generate_messages"}:
        stop_reason = str(result.get("finish_reason") or "unknown")
        stop_reason_source = "stream_done"
    else:
        stop_reason = "unknown_non_stream_text_only"
        stop_reason_source = "non_stream_generate_text_only"
    restart_observed = (
        load_pid is not None
        and result_pid is not None
        and str(result_pid) != str(load_pid)
    )
    ok = bool(result.get("ok")) and bool(text) and not restart_observed
    repetition_diagnostics = _repetition_diagnostics(text)
    repetition_flag = bool(repetition_diagnostics["repetition_flag"])
    completion_observation = _completion_observation(text)
    stop_strings = generation_params.get("stop")
    stop_string_count = len(stop_strings) if isinstance(stop_strings, list) else 0

    record = _base_record(
        run_id=run_id,
        output_path=output_path,
        isolated_runtime_path=isolated_runtime_path,
        isolated_python=isolated_python,
        model_path=model_path,
    )
    record.update(
        {
            "record_type": "prompt_result",
            "capability_label": "experimental_only",
            "evidence_strength": REAL_EVIDENCE_STRENGTH,
            "prompt_index": prompt_index,
            "prompt_id": prompt_id,
            "prompt_surface": prompt_surface,
            "prompt_shape": _prompt_shape_for_surface(
                prompt=prompt,
                prompt_surface=prompt_surface,
            ),
            "prompt_sha_hint": None,
            "max_tokens": max_tokens,
            "generation_params": generation_params,
            "prompt_results": [
                {
                    "prompt_index": prompt_index,
                    "prompt_id": prompt_id,
                    "max_tokens": max_tokens,
                    "ok": ok,
                    "completion_chars": len(text),
                    **completion_observation,
                    "stop_reason": stop_reason,
                    "stop_reason_source": stop_reason_source,
                    "generation_surface": generation_surface,
                    "prompt_tokens": result.get("prompt_tokens"),
                    "completion_tokens": completion_tokens,
                    "stream_event_count": result.get("stream_event_count"),
                    "stream_diagnostic_count": result.get("stream_diagnostic_count"),
                    "stream_diagnostics": result.get("stream_diagnostics", []),
                    "error": result.get("error"),
                    "timeout_s": result.get("timeout_s"),
                    "stream_timeout": bool(result.get("stream_timeout")),
                    "stop_strings": stop_strings if isinstance(stop_strings, list) else [],
                    "stop_string_count": stop_string_count,
                    "timing": timing,
                    "restart_observed": restart_observed,
                    "repetition_flag": repetition_flag,
                    "repetition_diagnostics": repetition_diagnostics,
                    "child_pid": result_pid,
                    "generation_count": result.get("generation_count"),
                }
            ],
            "lifecycle": {
                "preflight": "passed",
                "load_ok": load_ok,
                "generate_ok": bool(result.get("ok")),
                "unload_ok": unload_ok,
                "clean_health_after_unload": clean_health_after_unload,
                "health_after_unload": (
                    "clean" if clean_health_after_unload else "not_observed"
                ),
            },
            "child_restart_detection": {
                "method": "pid_stability_across_persistent_child_session",
                "load_pid": load_pid,
                "restart_observed": restart_observed,
            },
            "metrics": {
                "load_time_s": load_time_s,
                "ttft_ms_by_prompt": {
                    prompt_id: first_visible_token_ms
                }
                if first_visible_token_ms is not None
                else {},
                "decode_tps_by_prompt": {prompt_id: decode_tps}
                if decode_tps is not None
                else {},
                "wall_tps_by_prompt": {prompt_id: wall_tps}
                if wall_tps is not None
                else {},
                "stream_wall_ms_by_prompt": {
                    prompt_id: stream_wall_ms
                }
                if stream_wall_ms is not None
                else {},
                "child_rss_gb": child_rss_gb,
                "rss_sample_scope": RSS_SAMPLE_SCOPE,
                "rss_sample_source": RSS_SAMPLE_SOURCE,
                "rss_sample_timing": RSS_SAMPLE_TIMING,
                # Compatibility field for earlier D2 smoke rows. The value is
                # a child-process RSS sample, not an aggregate or true peak.
                "peak_rss_gb": child_rss_gb,
            },
            "verdict": "failed" if repetition_flag or not ok else "passed",
        }
    )
    return record


def _coverage_summary(
    *,
    rows: list[dict[str, Any]],
    prompt_slice: tuple[tuple[str, str], ...],
    token_ladder: tuple[int, ...],
) -> dict[str, Any]:
    requested_prompt_ids = [prompt_id for prompt_id, _prompt in prompt_slice]
    requested_token_ladder = [int(value) for value in token_ladder]
    matrix: dict[str, dict[str, str]] = {
        prompt_id: {str(max_tokens): "not_run" for max_tokens in requested_token_ladder}
        for prompt_id in requested_prompt_ids
    }
    for row in rows:
        prompt_id = str(row.get("prompt_id") or "")
        max_tokens = str(row.get("max_tokens"))
        if prompt_id in matrix and max_tokens in matrix[prompt_id]:
            matrix[prompt_id][max_tokens] = str(row.get("verdict") or "unknown")

    completed_prompt_ids = [
        prompt_id
        for prompt_id in requested_prompt_ids
        if any(value != "not_run" for value in matrix[prompt_id].values())
    ]
    passed_pairs = sum(
        1
        for prompt_results in matrix.values()
        for verdict in prompt_results.values()
        if verdict == "passed"
    )
    expected_generation_count = len(requested_prompt_ids) * len(requested_token_ladder)
    failed_pairs = [
        {"prompt_id": prompt_id, "max_tokens": int(max_tokens), "verdict": verdict}
        for prompt_id, prompt_results in matrix.items()
        for max_tokens, verdict in prompt_results.items()
        if verdict not in {"passed", "not_run"}
    ]
    missing_pairs = [
        {"prompt_id": prompt_id, "max_tokens": int(max_tokens)}
        for prompt_id, prompt_results in matrix.items()
        for max_tokens, verdict in prompt_results.items()
        if verdict == "not_run"
    ]

    return {
        "requested_prompt_ids": requested_prompt_ids,
        "requested_token_ladder": requested_token_ladder,
        "expected_generation_count": expected_generation_count,
        "completed_generation_count": len(rows),
        "passed_generation_count": passed_pairs,
        "completed_prompt_ids": completed_prompt_ids,
        "full_ladder_completed": (
            expected_generation_count > 0 and passed_pairs == expected_generation_count
        ),
        "prompt_token_matrix": matrix,
        "failed_pairs": failed_pairs,
        "missing_pairs": missing_pairs,
    }


def run_real(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    isolated_runtime_path: Path = DEFAULT_ISOLATED_RUNTIME_PATH,
    isolated_python: Path = DEFAULT_ISOLATED_PYTHON,
    model_path: Path = DEFAULT_MODEL_PATH,
    run_id: str | None = None,
    max_prompts: int | None = None,
    prompt_ids: tuple[str, ...] | None = None,
    max_tokens_ladder: tuple[int, ...] = TOKEN_LADDER,
    generation_overrides: dict[str, Any] | None = None,
    generation_surface: str = "generate",
    prompt_surface: str = D1_PROMPT_SURFACE_DEFAULT,
    continue_on_failure: bool = False,
    timeout_s: float = 600.0,
    popen_factory: Any = subprocess.Popen,
    rss_sampler: Any = _process_rss_gb,
) -> dict[str, Any]:
    preflight = run_preflight(
        isolated_python=isolated_python,
        model_path=model_path,
        isolated_runtime_path=isolated_runtime_path,
    )
    if preflight["verdict"] != "passed":
        return {
            "schema_version": "d1.run.v1",
            "gate": "D1",
            "runtime": "owlmlx",
            "model_id": MODEL_ID,
            "preflight": preflight,
            "verdict": "blocked",
            "rows_written": 0,
            "message": (
                "real D1 execution is blocked by preflight; this runner does "
                "not repair venvs, install dependencies, or fall back to stock .venv"
            ),
        }

    output_dir = Path(output_dir)
    run_id = run_id or f"{_compact_stamp()}-d1-deepseek-v4-real-run"
    output_path = output_dir / f"{run_id}.jsonl"
    prompt_slice = PROMPTS
    if prompt_ids:
        selected = set(prompt_ids)
        known = {prompt_id for prompt_id, _prompt in PROMPTS}
        unknown = sorted(selected - known)
        if unknown:
            raise ValueError(f"unknown --prompt-id value(s): {', '.join(unknown)}")
        prompt_slice = tuple(
            (prompt_id, prompt)
            for prompt_id, prompt in PROMPTS
            if prompt_id in selected
        )
    if max_prompts is not None:
        prompt_slice = prompt_slice[:max_prompts]
    token_ladder = tuple(int(value) for value in max_tokens_ladder)
    generation_overrides = dict(generation_overrides or {})
    if generation_surface not in {"generate", "stream"}:
        raise ValueError("--generation-surface must be 'generate' or 'stream'")
    if prompt_surface not in {"raw", "messages"}:
        raise ValueError("--prompt-surface must be 'raw' or 'messages'")
    rows: list[dict[str, Any]] = []
    load_ok = False
    unload_ok = False
    clean_health_after_unload = False
    load_time_s: float | None = None
    load_pid: Any = None
    run_error: str | None = None
    stream_timeout_observed = False
    proc: subprocess.Popen[str] | None = None

    try:
        proc = popen_factory(
            _runner_command(Path(isolated_python)),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(REPO_ROOT),
            env=_runner_env(),
        )
        load_started = time.monotonic()
        load_result = _child_exchange(
            proc,
            {
                "action": "load",
                "model_id": str(model_path),
                "tokenizer_config": D1_TOKENIZER_CONFIG,
            },
            timeout_s=timeout_s,
        )
        load_time_s = round(time.monotonic() - load_started, 4)
        load_ok = bool(load_result.get("ok"))
        load_pid = load_result.get("pid")
        if not load_ok:
            raise RuntimeError(str(load_result.get("error") or "load failed"))

        for prompt_index, (prompt_id, prompt) in enumerate(prompt_slice, start=1):
            for max_tokens in token_ladder:
                generation_params = _generation_params(
                    max_tokens=max_tokens,
                    overrides=generation_overrides,
                )
                if prompt_surface == "messages":
                    request = {
                        "action": "stream_generate_messages"
                        if generation_surface == "stream"
                        else "generate_messages",
                        "model_id": str(model_path),
                        "messages": _messages_for_prompt(prompt),
                        "params": generation_params,
                    }
                else:
                    request = {
                        "action": "stream_generate"
                        if generation_surface == "stream"
                        else "generate",
                        "model_id": str(model_path),
                        "prompt": prompt,
                        "params": generation_params,
                    }
                if generation_surface == "stream":
                    result = _child_stream_generate(
                        proc,
                        request,
                        timeout_s=timeout_s,
                    )
                else:
                    result = _child_exchange(proc, request, timeout_s=timeout_s)
                if result.get("stream_timeout"):
                    stream_timeout_observed = True
                child_rss_gb = rss_sampler(result.get("pid"))
                rows.append(
                    _real_record(
                        run_id=run_id,
                        output_path=output_path,
                        isolated_runtime_path=isolated_runtime_path,
                        isolated_python=isolated_python,
                        model_path=model_path,
                        prompt_index=prompt_index,
                        prompt_id=prompt_id,
                        prompt=prompt,
                        prompt_surface=prompt_surface,
                        max_tokens=max_tokens,
                        generation_params=generation_params,
                        load_ok=load_ok,
                        unload_ok=False,
                        clean_health_after_unload=False,
                        load_time_s=load_time_s,
                        child_rss_gb=child_rss_gb,
                        result=result,
                        load_pid=load_pid,
                    )
                )
                if rows[-1]["verdict"] != "passed" and not continue_on_failure:
                    break
            if rows and rows[-1]["verdict"] != "passed" and not continue_on_failure:
                break

        if stream_timeout_observed:
            run_error = "stream generation timed out before terminal payload"
        else:
            unload_result = _child_exchange(
                proc,
                {"action": "unload", "model_id": str(model_path)},
                timeout_s=timeout_s,
            )
            unload_ok = bool(unload_result.get("ok"))
            ping_result = _child_exchange(proc, {"action": "ping"}, timeout_s=timeout_s)
            clean_health_after_unload = bool(ping_result.get("ok")) and (
                ping_result.get("model_id") is None
            )
    except Exception as exc:
        run_error = str(exc)
        if proc is not None and proc.poll() is None and load_ok:
            try:
                unload_result = _child_exchange(
                    proc,
                    {"action": "unload", "model_id": str(model_path)},
                    timeout_s=min(timeout_s, 30.0),
                )
                unload_ok = bool(unload_result.get("ok"))
                ping_result = _child_exchange(
                    proc,
                    {"action": "ping"},
                    timeout_s=min(timeout_s, 30.0),
                )
                clean_health_after_unload = bool(ping_result.get("ok")) and (
                    ping_result.get("model_id") is None
                )
            except Exception as unload_exc:
                run_error = f"{run_error}; unload_after_error={unload_exc}"
    finally:
        if proc is not None and proc.poll() is None and not stream_timeout_observed:
            try:
                _child_exchange(proc, {"action": "shutdown"}, timeout_s=5.0)
            except Exception:
                pass
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                proc.wait(timeout=5.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    for row in rows:
        row["lifecycle"]["unload_ok"] = unload_ok
        row["lifecycle"]["clean_health_after_unload"] = clean_health_after_unload
        row["lifecycle"]["health_after_unload"] = (
            "clean" if clean_health_after_unload else "not_observed"
        )
        if not unload_ok or not clean_health_after_unload:
            row["verdict"] = "failed"

    _append_jsonl(output_path, rows)
    coverage = _coverage_summary(
        rows=rows,
        prompt_slice=prompt_slice,
        token_ladder=token_ladder,
    )
    verdict = (
        "passed"
        if rows
        and all(row["verdict"] == "passed" for row in rows)
        and coverage["full_ladder_completed"]
        else "failed"
    )
    return {
        "schema_version": "d1.run.v1",
        "run_id": run_id,
        "gate": "D1",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "evidence_strength": REAL_EVIDENCE_STRENGTH,
        "output_path": str(output_path),
        "rows_written": len(rows),
        "prompt_count": len(prompt_slice),
        "coverage": coverage,
        "token_ladder": list(token_ladder),
        "tokenizer_config": D1_TOKENIZER_CONFIG,
        "generation_defaults": D1_GENERATION_DEFAULTS,
        "generation_overrides": generation_overrides,
        "generation_surface": generation_surface,
        "prompt_surface": prompt_surface,
        "failure_policy": (
            "continue_on_failure" if continue_on_failure else "stop_on_first_failure"
        ),
        "preflight": preflight,
        "lifecycle": {
            "load_ok": load_ok,
            "unload_ok": unload_ok,
            "clean_health_after_unload": clean_health_after_unload,
        },
        "verdict": verdict,
        **({"error": run_error} if run_error else {}),
    }


def _read_jsonl_rows(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    candidate = Path(path)
    if not candidate.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in candidate.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _git_reference(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    try:
        branch = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        revision = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return {"path": str(path), "exists": True, "git": "unavailable"}
    return {"path": str(path), "exists": True, "branch": branch, "revision": revision}


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_mtp_candidate_key(key: str) -> bool:
    lowered = key.lower()
    return any(term in lowered for term in MTP_WEIGHT_TERMS)


def _layer_index_from_key(key: str) -> int | None:
    parts = key.split(".")
    for index, part in enumerate(parts[:-1]):
        if part == "layers":
            return _int_or_none(parts[index + 1])
    return None


def _sample(values: list[str], *, limit: int = 12) -> list[str]:
    return values[:limit]


def _health_probe(url: str | None, *, timeout_s: float = 2.0) -> dict[str, Any]:
    if not url:
        return {"url": None, "observed": False, "reason": "not_configured"}
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:
            raw = response.read(65536).decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            return {
                "url": url,
                "observed": True,
                "ok": 200 <= int(response.status) < 300,
                "status_code": int(response.status),
                "body": payload if isinstance(payload, dict) else raw,
            }
    except (OSError, urllib.error.URLError) as exc:
        return {
            "url": url,
            "observed": False,
            "ok": False,
            "error": str(exc),
        }


def _health_fingerprint(probe: dict[str, Any]) -> dict[str, Any]:
    body = probe.get("body") if isinstance(probe.get("body"), dict) else {}
    return {
        "observed": bool(probe.get("observed")),
        "ok": probe.get("ok"),
        "status_code": probe.get("status_code"),
        "readiness": body.get("readiness"),
        "active_model_id": body.get("active_model_id"),
        "model_count": body.get("model_count"),
        "backend_error": body.get("backend_error"),
        "persistent_child": body.get("persistent_child"),
    }


def _metric_from_prompt_map(
    metrics: dict[str, Any],
    key: str,
    prompt_id: str,
) -> Any:
    value = metrics.get(key)
    if isinstance(value, dict):
        return value.get(prompt_id)
    return None


def _metric_distribution(rows: list[dict[str, Any]], metric_key: str) -> dict[str, Any]:
    values = sorted(
        value
        for row in rows
        if isinstance(row.get("metrics"), dict)
        for value in [_as_float(row["metrics"].get(metric_key))]
        if value is not None
    )
    if not values:
        return {"count": 0, "min": None, "p50": None, "max": None}
    midpoint = len(values) // 2
    if len(values) % 2:
        p50 = values[midpoint]
    else:
        p50 = (values[midpoint - 1] + values[midpoint]) / 2.0
    return {
        "count": len(values),
        "min": round(values[0], 6),
        "p50": round(p50, 6),
        "max": round(values[-1], 6),
    }


def _d2_metric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ttft_ms": _metric_distribution(rows, "ttft_ms"),
        "decode_tps_after_first_token": _metric_distribution(
            rows,
            "decode_tps_after_first_token",
        ),
        "child_rss_gb": _metric_distribution(rows, "child_rss_gb"),
    }


def _d2_record_from_d1_row(
    *,
    run_id: str,
    output_path: Path,
    source_run_id: str,
    source_output_path: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    prompt_results = row.get("prompt_results")
    first = dict(prompt_results[0]) if isinstance(prompt_results, list) and prompt_results else {}
    prompt_id = str(row.get("prompt_id") or first.get("prompt_id") or "")
    metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
    lifecycle = row.get("lifecycle") if isinstance(row.get("lifecycle"), dict) else {}

    load_time_s = _as_float(metrics.get("load_time_s"))
    ttft_ms = _as_float(_metric_from_prompt_map(metrics, "ttft_ms_by_prompt", prompt_id))
    stream_wall_ms = _as_float(
        _metric_from_prompt_map(metrics, "stream_wall_ms_by_prompt", prompt_id)
    )
    decode_tps = _as_float(
        _metric_from_prompt_map(metrics, "decode_tps_by_prompt", prompt_id)
    )
    wall_tps = _as_float(_metric_from_prompt_map(metrics, "wall_tps_by_prompt", prompt_id))
    child_rss_gb = _as_float(metrics.get("child_rss_gb"))
    if child_rss_gb is None:
        child_rss_gb = _as_float(metrics.get("peak_rss_gb"))
    rss_sample_scope = metrics.get("rss_sample_scope") or RSS_SAMPLE_SCOPE
    rss_sample_source = metrics.get("rss_sample_source") or RSS_SAMPLE_SOURCE
    rss_sample_timing = metrics.get("rss_sample_timing") or RSS_SAMPLE_TIMING
    completion_tokens = first.get("completion_tokens")
    prompt_tokens = first.get("prompt_tokens")

    required = {
        "load_time_s": load_time_s,
        "ttft_ms": ttft_ms,
        "stream_wall_ms": stream_wall_ms,
        "completion_tokens": completion_tokens,
        "decode_tps_after_first_token": decode_tps,
        "child_rss_gb": child_rss_gb,
    }
    missing_metrics = [key for key, value in required.items() if value is None]
    backend_health = {
        "load_ok": bool(lifecycle.get("load_ok")),
        "generate_ok": bool(lifecycle.get("generate_ok")),
        "unload_ok": bool(lifecycle.get("unload_ok")),
        "clean_health_after_unload": bool(lifecycle.get("clean_health_after_unload")),
        "child_restart_observed": bool(
            row.get("child_restart_detection", {}).get("restart_observed")
        )
        if isinstance(row.get("child_restart_detection"), dict)
        else None,
    }
    verdict = (
        "passed"
        if row.get("verdict") == "passed"
        and not missing_metrics
        and all(
            backend_health[key]
            for key in (
                "load_ok",
                "generate_ok",
                "unload_ok",
                "clean_health_after_unload",
            )
        )
        and backend_health["child_restart_observed"] is False
        else "failed"
    )
    return {
        "schema_version": "d2.metrics.v2",
        "record_type": "metrics_result",
        "run_id": run_id,
        "created_at": _now_utc(),
        "gate": "D2",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "model_type": MODEL_TYPE,
        "capability_label": "experimental_only",
        "evidence_strength": D2_EVIDENCE_STRENGTH,
        "output_path": str(output_path),
        "source": {
            "gate": "D1",
            "schema_version": row.get("schema_version"),
            "run_id": source_run_id,
            "output_path": source_output_path,
            "record_type": row.get("record_type"),
        },
        "prompt_index": row.get("prompt_index"),
        "prompt_id": prompt_id,
        "prompt_surface": row.get("prompt_surface"),
        "generation_surface": first.get("generation_surface"),
        "prompt_shape": row.get("prompt_shape"),
        "max_tokens": row.get("max_tokens"),
        "generation_params": row.get("generation_params"),
        "metrics": {
            "load_time_s": load_time_s,
            "ttft_ms": ttft_ms,
            "stream_wall_ms": stream_wall_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "decode_tps_after_first_token": decode_tps,
            "wall_tps": wall_tps,
            "child_rss_gb": child_rss_gb,
            "rss_sample_scope": rss_sample_scope,
            "rss_sample_source": rss_sample_source,
            "rss_sample_timing": rss_sample_timing,
            # Compatibility field for older readers. This is the same
            # child-process sample, not an aggregate or true peak.
            "peak_rss_gb": child_rss_gb,
            "stream_event_count": first.get("stream_event_count"),
            "stream_diagnostic_count": first.get("stream_diagnostic_count"),
        },
        "backend_health": backend_health,
        "missing_metrics": missing_metrics,
        "verdict": verdict,
    }


def run_metrics(
    *,
    output_dir: Path = D2_DEFAULT_OUTPUT_DIR,
    isolated_runtime_path: Path = DEFAULT_ISOLATED_RUNTIME_PATH,
    isolated_python: Path = DEFAULT_ISOLATED_PYTHON,
    model_path: Path = DEFAULT_MODEL_PATH,
    run_id: str | None = None,
    max_prompts: int | None = None,
    prompt_ids: tuple[str, ...] | None = None,
    max_tokens_ladder: tuple[int, ...] = (128,),
    generation_overrides: dict[str, Any] | None = None,
    prompt_surface: str = D1_PROMPT_SURFACE_DEFAULT,
    timeout_s: float = 900.0,
    popen_factory: Any = subprocess.Popen,
    rss_sampler: Any = _process_rss_gb,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    run_id = run_id or f"{_compact_stamp()}-d2-deepseek-v4-metrics"
    output_path = output_dir / f"{run_id}.jsonl"
    summary_path = output_dir / f"{run_id}.summary.json"
    source_output_dir = output_dir / "source-d1-stream"
    source_run_id = f"{run_id}-source-d1-stream"
    generation_overrides = dict(generation_overrides or {})
    source_summary = run_real(
        output_dir=source_output_dir,
        isolated_runtime_path=isolated_runtime_path,
        isolated_python=isolated_python,
        model_path=model_path,
        run_id=source_run_id,
        max_prompts=max_prompts,
        prompt_ids=prompt_ids,
        max_tokens_ladder=max_tokens_ladder,
        generation_overrides=generation_overrides,
        generation_surface="stream",
        prompt_surface=prompt_surface,
        continue_on_failure=True,
        timeout_s=timeout_s,
        popen_factory=popen_factory,
        rss_sampler=rss_sampler,
    )
    source_output_path = str(source_summary.get("output_path") or "")
    source_rows = _read_jsonl_rows(source_output_path)
    rows = [
        _d2_record_from_d1_row(
            run_id=run_id,
            output_path=output_path,
            source_run_id=source_run_id,
            source_output_path=source_output_path,
            row=row,
        )
        for row in source_rows
    ]
    _append_jsonl(output_path, rows)
    passed_rows = sum(1 for row in rows if row.get("verdict") == "passed")
    missing_metrics = sorted(
        {
            metric
            for row in rows
            for metric in list(row.get("missing_metrics") or [])
        }
    )
    verdict = (
        "passed"
        if rows
        and source_summary.get("verdict") == "passed"
        and passed_rows == len(rows)
        else "failed"
    )
    summary = {
        "schema_version": "d2.metrics.run.v2",
        "run_id": run_id,
        "gate": "D2",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "evidence_strength": D2_EVIDENCE_STRENGTH,
        "output_path": str(output_path),
        "summary_output_path": str(summary_path),
        "source_output_path": source_output_path,
        "rows_written": len(rows),
        "passed_rows": passed_rows,
        "missing_metrics": missing_metrics,
        "metric_summary": _d2_metric_summary(rows),
        "prompt_surface": prompt_surface,
        "generation_surface": "stream",
        "token_ladder": list(max_tokens_ladder),
        "source_summary": {
            "schema_version": source_summary.get("schema_version"),
            "run_id": source_summary.get("run_id"),
            "verdict": source_summary.get("verdict"),
            "rows_written": source_summary.get("rows_written"),
            "coverage": source_summary.get("coverage"),
            "lifecycle": source_summary.get("lifecycle"),
        },
        "verdict": verdict,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def run_mtp_checkpoint_inspection(
    *,
    output_dir: Path = D3_DEFAULT_OUTPUT_DIR,
    model_path: Path = DEFAULT_MODEL_PATH,
    adapter_path: Path = DEFAULT_DEEPSEEK_ADAPTER_PATH,
    run_id: str | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    model_path = Path(model_path)
    adapter_path = Path(adapter_path)
    run_id = run_id or f"{_compact_stamp()}-d3-deepseek-v4-mtp-checkpoint"
    output_path = output_dir / f"{run_id}.jsonl"

    config_path = model_path / "config.json"
    index_path = model_path / "model.safetensors.index.json"
    config = _read_json_object(config_path)
    index = _read_json_object(index_path)
    weight_map = index.get("weight_map") if isinstance(index.get("weight_map"), dict) else {}
    weight_keys = sorted(str(key) for key in weight_map)
    num_hidden_layers = _int_or_none(config.get("num_hidden_layers"))
    declared_nextn_layers = _int_or_none(config.get("num_nextn_predict_layers")) or 0

    matched_weight_keys = [key for key in weight_keys if _is_mtp_candidate_key(key)]
    extra_layer_keys = []
    if num_hidden_layers is not None:
        extra_layer_keys = [
            key
            for key in weight_keys
            if (layer_index := _layer_index_from_key(key)) is not None
            and layer_index >= num_hidden_layers
        ]
    candidate_files = sorted(
        path.name
        for path in model_path.iterdir()
        if path.is_file() and _is_mtp_candidate_key(path.name)
    ) if model_path.exists() else []
    has_mtp_weight_candidates = bool(matched_weight_keys or extra_layer_keys or candidate_files)
    config_declares_nextn = declared_nextn_layers > 0

    if has_mtp_weight_candidates:
        mtp_weight_status = "present"
        missing_reason = None
    elif config_declares_nextn:
        mtp_weight_status = "absent_or_stripped"
        missing_reason = D3_MTP_MISSING_REASON
    else:
        mtp_weight_status = "not_configured"
        missing_reason = "num_nextn_predict_layers_not_declared"

    read_errors = []
    if not model_path.exists():
        read_errors.append("model_path_missing")
    if not config:
        read_errors.append("config_json_missing_or_unreadable")
    if not index:
        read_errors.append("safetensors_index_missing_or_unreadable")
    verdict = "passed" if not read_errors else "blocked"

    payload = {
        "schema_version": "d3.checkpoint_inspection.v1",
        "record_type": "mtp_checkpoint_inspection",
        "run_id": run_id,
        "gate": "D3",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "model_type": MODEL_TYPE,
        "capability_label": "experimental_only",
        "evidence_strength": D3_EVIDENCE_STRENGTH,
        "created_at": _now_utc(),
        "output_path": str(output_path),
        "model_path": str(model_path),
        "adapter_reference": _git_reference(adapter_path),
        "config_summary": {
            "model_type": config.get("model_type"),
            "architectures": config.get("architectures"),
            "num_hidden_layers": num_hidden_layers,
            "num_nextn_predict_layers": declared_nextn_layers,
            "max_position_embeddings": config.get("max_position_embeddings"),
        },
        "weight_index_summary": {
            "metadata": index.get("metadata"),
            "weight_key_count": len(weight_keys),
            "safetensors_shard_count": len(
                {
                    str(value)
                    for value in weight_map.values()
                    if str(value).endswith(".safetensors")
                }
            ),
            "matched_mtp_weight_key_count": len(matched_weight_keys),
            "matched_mtp_weight_key_samples": _sample(matched_weight_keys),
            "extra_layer_key_count": len(extra_layer_keys),
            "extra_layer_key_samples": _sample(extra_layer_keys),
            "candidate_file_names": candidate_files,
        },
        "inspection": {
            "config_declares_nextn_predict_layers": config_declares_nextn,
            "has_mtp_weight_candidates": has_mtp_weight_candidates,
            "mtp_weight_status": mtp_weight_status,
            "missingReason": missing_reason,
            "expected_strip_patterns": [
                "mtp.*",
                "model.layers.<index >= num_hidden_layers>.*",
                "layers.<index >= num_hidden_layers>.*",
            ],
        },
        "read_errors": read_errors,
        "verdict": verdict,
        "capability_conclusion": (
            "mtp_checkpoint_not_available"
            if missing_reason == D3_MTP_MISSING_REASON
            else "mtp_checkpoint_candidate_present"
            if has_mtp_weight_candidates
            else "mtp_not_configured"
        ),
    }
    _append_jsonl(output_path, [payload])
    return {
        "schema_version": "d3.checkpoint_inspection.run.v1",
        "run_id": run_id,
        "gate": "D3",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "evidence_strength": D3_EVIDENCE_STRENGTH,
        "output_path": str(output_path),
        "mtp_weight_status": mtp_weight_status,
        "missingReason": missing_reason,
        "capability_conclusion": payload["capability_conclusion"],
        "verdict": verdict,
    }


def _inspection_from_path(path: str | Path | None) -> dict[str, Any] | None:
    row = _read_first_jsonl_row(path)
    return row if isinstance(row, dict) else None


def _inspection_missing_reason(inspection: dict[str, Any]) -> str | None:
    nested = inspection.get("inspection")
    if isinstance(nested, dict) and nested.get("missingReason"):
        return str(nested["missingReason"])
    if inspection.get("missingReason"):
        return str(inspection["missingReason"])
    return None


def run_mtp_preload_reject(
    *,
    output_dir: Path = D4_DEFAULT_OUTPUT_DIR,
    model_path: Path = DEFAULT_MODEL_PATH,
    adapter_path: Path = DEFAULT_DEEPSEEK_ADAPTER_PATH,
    run_id: str | None = None,
    inspection_path: Path | None = None,
    runtime_health_url: str | None = DEFAULT_RUNTIME_HEALTH_URL,
    inspection_func: Any = run_mtp_checkpoint_inspection,
    health_probe: Any = _health_probe,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    run_id = run_id or f"{_compact_stamp()}-d4-deepseek-v4-mtp-preload-reject"
    output_path = output_dir / f"{run_id}.jsonl"

    health_before = health_probe(runtime_health_url)
    source_inspection = _inspection_from_path(inspection_path)
    source_output_path = str(inspection_path) if inspection_path else None
    if source_inspection is None:
        source_summary = inspection_func(
            output_dir=output_dir / "source-d3-inspection",
            model_path=model_path,
            adapter_path=adapter_path,
            run_id=f"{run_id}-source-d3-inspection",
        )
        source_output_path = str(source_summary.get("output_path") or "")
        source_inspection = _inspection_from_path(source_output_path) or {}
    health_after = health_probe(runtime_health_url)

    missing_reason = _inspection_missing_reason(source_inspection)
    inspection_conclusion = source_inspection.get("capability_conclusion")
    should_reject = (
        missing_reason == D3_MTP_MISSING_REASON
        or inspection_conclusion == "mtp_checkpoint_not_available"
    )
    decision = "rejected_pre_load" if should_reject else "not_rejected"
    reason_code = missing_reason if should_reject else None
    before_fingerprint = _health_fingerprint(health_before)
    after_fingerprint = _health_fingerprint(health_after)
    health_stable = before_fingerprint == after_fingerprint
    health_required = runtime_health_url is not None
    health_ok = (not health_required) or (
        bool(health_before.get("observed"))
        and bool(health_after.get("observed"))
        and health_stable
    )
    reject_ok = decision == "rejected_pre_load" and reason_code == D3_MTP_MISSING_REASON
    verdict = "passed" if reject_ok and health_ok else "failed"

    payload = {
        "schema_version": "d4.preload_reject.v1",
        "record_type": "mtp_preload_reject",
        "run_id": run_id,
        "gate": "D4",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "model_type": MODEL_TYPE,
        "capability_label": "experimental_only",
        "evidence_strength": D4_EVIDENCE_STRENGTH,
        "created_at": _now_utc(),
        "output_path": str(output_path),
        "requested_capability": "deepseek_v4_mtp",
        "source_inspection": {
            "schema_version": source_inspection.get("schema_version"),
            "run_id": source_inspection.get("run_id"),
            "output_path": source_output_path,
            "capability_conclusion": inspection_conclusion,
            "missingReason": missing_reason,
            "verdict": source_inspection.get("verdict"),
        },
        "decision": decision,
        "reason_code": reason_code,
        "load_attempted": False,
        "child_process_started": False,
        "default_model_surface_changed": False,
        "runtime_health": {
            "url": runtime_health_url,
            "before": health_before,
            "after": health_after,
            "before_fingerprint": before_fingerprint,
            "after_fingerprint": after_fingerprint,
            "stable": health_stable,
            "required": health_required,
        },
        "verdict": verdict,
    }
    _append_jsonl(output_path, [payload])
    return {
        "schema_version": "d4.preload_reject.run.v1",
        "run_id": run_id,
        "gate": "D4",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "evidence_strength": D4_EVIDENCE_STRENGTH,
        "output_path": str(output_path),
        "decision": decision,
        "reason_code": reason_code,
        "load_attempted": False,
        "child_process_started": False,
        "runtime_health_stable": health_stable,
        "verdict": verdict,
    }


_DIRECT_GENERATE_CODE = r"""
import gc
import json
import os
import sys
import time
from contextlib import redirect_stdout


def _emit(payload):
    sys.__stdout__.write(json.dumps(payload, sort_keys=True) + "\n")
    sys.__stdout__.flush()


request = json.loads(sys.stdin.read() or "{}")
model = None
tokenizer = None
try:
    import mlx_lm
    from owlmlx.runtime.mlx_lm_runner import (
        _prepare_generation_params,
        _prepare_tokenizer_config,
        _stop_strings_from_params,
        _truncate_at_stop_strings,
    )

    model_path = str(request["model_path"])
    params = dict(request.get("params") or {})
    tokenizer_config = _prepare_tokenizer_config(
        dict(request.get("tokenizer_config") or {})
    )
    stop_strings = _stop_strings_from_params(params)

    load_started = time.perf_counter()
    with redirect_stdout(sys.stderr):
        model, tokenizer = mlx_lm.load(
            model_path,
            tokenizer_config=tokenizer_config or None,
        )
    load_time_s = round(time.perf_counter() - load_started, 4)

    generate_started = time.perf_counter()
    with redirect_stdout(sys.stderr):
        text = mlx_lm.generate(
            model,
            tokenizer,
            prompt=str(request.get("prompt") or ""),
            **_prepare_generation_params(params),
        )
    generate_time_s = round(time.perf_counter() - generate_started, 4)
    text, stop_hit = _truncate_at_stop_strings(str(text), stop_strings)
    _emit(
        {
            "ok": True,
            "action": "direct_generate",
            "surface": "direct_mlx_lm_generate",
            "model_id": model_path,
            "text": text,
            "finish_reason": "stop" if stop_hit else "stop",
            "pid": os.getpid(),
            "load_time_s": load_time_s,
            "generate_time_s": generate_time_s,
        }
    )
except Exception as exc:
    _emit(
        {
            "ok": False,
            "action": "direct_generate",
            "surface": "direct_mlx_lm_generate",
            "model_id": str(request.get("model_path") or ""),
            "text": "",
            "error": str(exc),
            "pid": os.getpid(),
        }
    )
finally:
    model = None
    tokenizer = None
    try:
        gc.collect()
    except Exception:
        pass
    try:
        import mlx.core as mx

        mx.clear_cache()
    except Exception:
        pass
"""


def _run_direct_generate(
    *,
    isolated_python: Path,
    model_path: Path,
    prompt: str,
    generation_params: dict[str, Any],
    timeout_s: float,
    run_factory: Any = subprocess.run,
) -> dict[str, Any]:
    request = {
        "model_path": str(model_path),
        "prompt": prompt,
        "params": generation_params,
        "tokenizer_config": D1_TOKENIZER_CONFIG,
    }
    try:
        proc = run_factory(
            [str(isolated_python), "-c", _DIRECT_GENERATE_CODE],
            input=json.dumps(request, sort_keys=True),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout_s,
            cwd=str(REPO_ROOT),
            env=_runner_env(),
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "action": "direct_generate",
            "surface": "direct_mlx_lm_generate",
            "text": "",
            "error": f"direct generate timed out after {exc.timeout}s",
            "timeout_s": exc.timeout,
        }
    except OSError as exc:
        return {
            "ok": False,
            "action": "direct_generate",
            "surface": "direct_mlx_lm_generate",
            "text": "",
            "error": str(exc),
        }

    stdout = str(proc.stdout or "").strip()
    payload: dict[str, Any] | None = None
    if stdout:
        for line in reversed(stdout.splitlines()):
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                payload = parsed
                break
    if payload is None:
        return {
            "ok": False,
            "action": "direct_generate",
            "surface": "direct_mlx_lm_generate",
            "text": "",
            "error": "direct generate produced no JSON payload",
            "returncode": proc.returncode,
            "stdout_tail": stdout[-1000:],
        }
    payload["returncode"] = proc.returncode
    if proc.returncode != 0:
        payload["ok"] = False
        payload.setdefault("error", f"direct generate exited {proc.returncode}")
    return payload


def _compare_surface_observation(
    *,
    surface: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    text = str(result.get("text") or "")
    repetition = _repetition_diagnostics(text)
    observation = {
        "surface": surface,
        "ok": bool(result.get("ok")) and bool(text),
        "completion_chars": len(text),
        **_completion_observation(text),
        "repetition_flag": bool(repetition["repetition_flag"]),
        "repetition_diagnostics": repetition,
        "pid": result.get("pid"),
        "finish_reason": result.get("finish_reason"),
        "timing": {
            key: result.get(key)
            for key in ("load_time_s", "generate_time_s")
            if result.get(key) is not None
        },
    }
    if result.get("error"):
        observation["error"] = result.get("error")
    if result.get("returncode") is not None:
        observation["returncode"] = result.get("returncode")
    return observation


def _runner_compare_observation(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return _compare_surface_observation(
            surface="owlmlx_runner_generate",
            result={"ok": False, "text": "", "error": "runner produced no row"},
        )
    prompt_results = row.get("prompt_results")
    if isinstance(prompt_results, list) and prompt_results:
        first = dict(prompt_results[0])
    else:
        first = {}
    timing = first.get("timing") if isinstance(first.get("timing"), dict) else {}
    return {
        "surface": "owlmlx_runner_generate",
        "ok": bool(first.get("ok")),
        "completion_chars": int(first.get("completion_chars") or 0),
        "completion_sha256": first.get("completion_sha256"),
        "completion_preview": first.get("completion_preview"),
        "completion_tail": first.get("completion_tail"),
        "repetition_flag": bool(first.get("repetition_flag")),
        "repetition_diagnostics": first.get("repetition_diagnostics", {}),
        "pid": first.get("child_pid"),
        "finish_reason": first.get("stop_reason"),
        "timing": timing,
        "row_verdict": row.get("verdict"),
        "lifecycle": row.get("lifecycle", {}),
    }


def _compare_classification(
    *,
    direct: dict[str, Any],
    runner: dict[str, Any],
) -> str:
    if not direct.get("ok") and not runner.get("ok"):
        return "both_surfaces_failed"
    if not direct.get("ok") and runner.get("ok"):
        return "direct_surface_failed_runner_passed"
    if direct.get("ok") and not runner.get("ok"):
        return "runner_surface_failed_direct_passed"

    direct_repeats = bool(direct.get("repetition_flag"))
    runner_repeats = bool(runner.get("repetition_flag"))
    if direct_repeats and runner_repeats:
        return "adapter_or_artifact_likely"
    if not direct_repeats and runner_repeats:
        return "runner_call_path_suspect"
    if direct_repeats and not runner_repeats:
        return "runner_masks_direct_repetition"
    return "no_repetition_observed"


def _read_first_jsonl_row(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    for line in candidate.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        return parsed if isinstance(parsed, dict) else None
    return None


def run_direct_vs_runner(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    isolated_runtime_path: Path = DEFAULT_ISOLATED_RUNTIME_PATH,
    isolated_python: Path = DEFAULT_ISOLATED_PYTHON,
    model_path: Path = DEFAULT_MODEL_PATH,
    run_id: str | None = None,
    prompt_id: str = "p1_short_cn",
    max_tokens: int = 1024,
    generation_overrides: dict[str, Any] | None = None,
    timeout_s: float = 900.0,
    direct_func: Any = _run_direct_generate,
    runner_func: Any = run_real,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    run_id = run_id or f"{_compact_stamp()}-d1-direct-vs-runner"
    output_path = output_dir / f"{run_id}.jsonl"
    prompt_index, prompt_id, prompt = _prompt_by_id(prompt_id)
    generation_overrides = dict(generation_overrides or {})
    generation_params = _generation_params(
        max_tokens=max_tokens,
        overrides=generation_overrides,
    )
    preflight = run_preflight(
        isolated_python=isolated_python,
        model_path=model_path,
        isolated_runtime_path=isolated_runtime_path,
    )
    if preflight["verdict"] != "passed":
        payload = {
            "schema_version": "d1.compare.v1",
            "record_type": "direct_vs_runner_compare",
            "run_id": run_id,
            "gate": "D1",
            "runtime": "owlmlx",
            "model_id": MODEL_ID,
            "prompt_id": prompt_id,
            "max_tokens": int(max_tokens),
            "evidence_strength": COMPARE_EVIDENCE_STRENGTH,
            "preflight": preflight,
            "classification": "blocked_by_preflight",
            "verdict": "blocked",
            "output_path": str(output_path),
        }
        _append_jsonl(output_path, [payload])
        return payload

    direct_raw = direct_func(
        isolated_python=Path(isolated_python),
        model_path=Path(model_path),
        prompt=prompt,
        generation_params=generation_params,
        timeout_s=timeout_s,
    )
    direct = _compare_surface_observation(
        surface="direct_mlx_lm_generate",
        result=dict(direct_raw),
    )

    runner_run_id = f"{run_id}-runner"
    runner_summary = runner_func(
        output_dir=output_dir,
        isolated_runtime_path=isolated_runtime_path,
        isolated_python=isolated_python,
        model_path=model_path,
        run_id=runner_run_id,
        prompt_ids=(prompt_id,),
        max_tokens_ladder=(int(max_tokens),),
        generation_overrides=generation_overrides,
        timeout_s=timeout_s,
    )
    runner_row = _read_first_jsonl_row(runner_summary.get("output_path"))
    runner = _runner_compare_observation(runner_row)
    classification = _compare_classification(direct=direct, runner=runner)
    verdict = (
        "diagnostic_passed"
        if classification == "no_repetition_observed"
        else "diagnostic_failed"
    )
    payload = {
        "schema_version": "d1.compare.v1",
        "record_type": "direct_vs_runner_compare",
        "run_id": run_id,
        "gate": "D1",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "model_type": MODEL_TYPE,
        "capability_label": "experimental_only",
        "evidence_strength": COMPARE_EVIDENCE_STRENGTH,
        "created_at": _now_utc(),
        "output_path": str(output_path),
        "runner_output_path": runner_summary.get("output_path"),
        "prompt_index": prompt_index,
        "prompt_id": prompt_id,
        "prompt_shape": _prompt_shape(prompt),
        "max_tokens": int(max_tokens),
        "generation_params": generation_params,
        "preflight": preflight,
        "surfaces": {
            "direct_mlx_lm_generate": direct,
            "owlmlx_runner_generate": runner,
        },
        "runner_summary": {
            "schema_version": runner_summary.get("schema_version"),
            "run_id": runner_summary.get("run_id"),
            "verdict": runner_summary.get("verdict"),
            "rows_written": runner_summary.get("rows_written"),
            "lifecycle": runner_summary.get("lifecycle"),
            "coverage": runner_summary.get("coverage"),
        },
        "classification": classification,
        "verdict": verdict,
        "diagnostic_scope": (
            "Localizes whether p1/max_tokens repetition is visible in direct "
            "mlx_lm.generate or only through owlmlx.runtime.mlx_lm_runner."
        ),
    }
    _append_jsonl(output_path, [payload])
    return payload


# ---------------------------------------------------------------------------
# D6 · mainline backend integration (DSV4-Flash 2bit-DQ through
# MlxLmSubprocessBackend with the `deepseek-experimental` extras venv).
# Spec: docs/architect/design/D6-mainline-backend-integration-spec.md
# ---------------------------------------------------------------------------


def _d6_read_model_type_from_config(model_path: Path) -> str | None:
    config_path = Path(model_path) / "config.json"
    if not config_path.is_file():
        return None
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    model_type = payload.get("model_type")
    if isinstance(model_type, str) and model_type.strip():
        return model_type.strip()
    return None


def _d6_probe_model_type_support(
    python_executable: Path,
    model_type: str,
    *,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    """Run ``importlib.util.find_spec`` in the given python venv."""

    module_name = f"mlx_lm.models.{model_type}"
    code = (
        "import importlib.util, json, sys\n"
        "module = sys.argv[1]\n"
        "try:\n"
        "    spec = importlib.util.find_spec(module)\n"
        "except ModuleNotFoundError as exc:\n"
        "    print(json.dumps({'probe_error': str(exc), 'module_name': module}))\n"
        "    raise SystemExit(1)\n"
        "print(json.dumps({'supported': spec is not None, 'module_name': module}))\n"
    )
    try:
        completed = subprocess.run(
            [str(python_executable), "-c", code, module_name],
            cwd=None,
            env=os.environ.copy(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "supported": False,
            "module_name": module_name,
            "returncode": -1,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }
    parsed: dict[str, Any] = {}
    try:
        parsed = json.loads(completed.stdout.strip() or "{}")
    except json.JSONDecodeError:
        parsed = {}
    supported = (
        completed.returncode == 0
        and bool(parsed.get("supported"))
        and not parsed.get("probe_error")
    )
    return {
        "supported": supported,
        "module_name": module_name,
        "returncode": int(completed.returncode),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _d6_runtime_provenance(
    python_executable: Path,
    *,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    code = (
        "import importlib, importlib.metadata, json, os.path, pathlib, subprocess\n"
        "result = {'origin': None, 'package_version': None, 'git_commit': None, 'source_url': None}\n"
        "try:\n"
        "    module = importlib.import_module('mlx_lm')\n"
        "    result['origin'] = getattr(module, '__file__', None)\n"
        "except Exception as exc:\n"
        "    result['origin_error'] = str(exc)\n"
        "dist_path = None\n"
        "try:\n"
        "    dist = importlib.metadata.distribution('mlx-lm')\n"
        "    result['package_version'] = dist.version\n"
        "    dist_path = pathlib.Path(str(getattr(dist, '_path', '') or ''))\n"
        "    direct_url_text = dist.read_text('direct_url.json')\n"
        "    if direct_url_text:\n"
        "        direct_url = json.loads(direct_url_text)\n"
        "        result['source_url'] = direct_url.get('url')\n"
        "        vcs_info = direct_url.get('vcs_info') or {}\n"
        "        result['git_commit'] = vcs_info.get('commit_id')\n"
        "except Exception:\n"
        "    pass\n"
        "checkout = result.get('origin')\n"
        "site_root = str(dist_path.parent) if dist_path else None\n"
        "while result.get('git_commit') is None and checkout and not os.path.isdir(os.path.join(checkout, '.git')):\n"
        "    if site_root and os.path.abspath(checkout) == os.path.abspath(site_root):\n"
        "        checkout = None\n"
        "        break\n"
        "    parent = os.path.dirname(checkout)\n"
        "    if parent == checkout:\n"
        "        checkout = None\n"
        "        break\n"
        "    checkout = parent\n"
        "if result.get('git_commit') is None and checkout:\n"
        "    try:\n"
        "        commit = subprocess.run(['git', '-C', checkout, 'rev-parse', 'HEAD'],\n"
        "                                capture_output=True, text=True, timeout=5)\n"
        "        if commit.returncode == 0:\n"
        "            result['git_commit'] = commit.stdout.strip()\n"
        "    except Exception:\n"
        "        pass\n"
        "print(json.dumps(result))\n"
    )
    try:
        completed = subprocess.run(
            [str(python_executable), "-c", code],
            cwd=None,
            env=os.environ.copy(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"origin": None, "package_version": None, "git_commit": None}
    try:
        return json.loads(completed.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return {"origin": None, "package_version": None, "git_commit": None}


def _d6_load_baseline(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in _read_jsonl_rows(path):
        prompt_id = str(row.get("prompt_id") or "")
        max_tokens = row.get("max_tokens")
        if not prompt_id or max_tokens is None:
            continue
        try:
            key = (prompt_id, int(max_tokens))
        except (TypeError, ValueError):
            continue
        rows[key] = row
    return rows


def _d6_cross_validation(
    *,
    actual_metrics: dict[str, Any],
    baseline_row: dict[str, Any] | None,
    ttft_drift_rel_threshold: float,
    decode_tps_drift_rel_threshold: float,
    child_rss_drift_abs_threshold: float,
) -> dict[str, Any]:
    if baseline_row is None:
        return {
            "d2_baseline_row_present": False,
            "ttft_ms_diff_rel": None,
            "decode_tps_diff_rel": None,
            "child_rss_gb_diff_abs": None,
            "drift_within_threshold": False,
            "reason": "baseline_row_missing",
        }
    baseline_metrics = (
        baseline_row.get("metrics") if isinstance(baseline_row.get("metrics"), dict) else {}
    )

    def _diff_rel(key: str) -> float | None:
        actual = _as_float(actual_metrics.get(key))
        baseline = _as_float(baseline_metrics.get(key))
        if actual is None or baseline is None or baseline == 0.0:
            return None
        return round((actual - baseline) / baseline, 6)

    def _diff_abs(key: str) -> float | None:
        actual = _as_float(actual_metrics.get(key))
        baseline = _as_float(baseline_metrics.get(key))
        if actual is None or baseline is None:
            return None
        return round(actual - baseline, 6)

    ttft_diff = _diff_rel("ttft_ms")
    decode_diff = _diff_rel("decode_tps_after_first_token")
    rss_diff = _diff_abs("child_rss_gb")

    reasons: list[str] = []

    def _check_rel(diff: float | None, threshold: float, name: str) -> bool:
        if diff is None:
            reasons.append(f"{name}_unavailable")
            return False
        if abs(diff) > threshold:
            reasons.append(f"{name}_diff_rel={diff} exceeds {threshold}")
            return False
        return True

    def _check_abs(diff: float | None, threshold: float, name: str) -> bool:
        if diff is None:
            reasons.append(f"{name}_unavailable")
            return False
        if abs(diff) > threshold:
            reasons.append(f"{name}_diff_abs={diff} exceeds {threshold}")
            return False
        return True

    ok_ttft = _check_rel(ttft_diff, ttft_drift_rel_threshold, "ttft_ms")
    ok_decode = _check_rel(
        decode_diff, decode_tps_drift_rel_threshold, "decode_tps_after_first_token"
    )
    ok_rss = _check_abs(rss_diff, child_rss_drift_abs_threshold, "child_rss_gb")

    return {
        "d2_baseline_row_present": True,
        "ttft_ms_diff_rel": ttft_diff,
        "decode_tps_diff_rel": decode_diff,
        "child_rss_gb_diff_abs": rss_diff,
        "drift_within_threshold": ok_ttft and ok_decode and ok_rss,
        "reason": "; ".join(reasons) if reasons else None,
    }


def _d6_status_snapshot(backend: Any) -> dict[str, Any]:
    try:
        status = backend.status()
    except Exception as exc:  # noqa: BLE001
        return {
            "healthy": None,
            "loaded_model_count": None,
            "backend_name": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "healthy": bool(status.healthy),
        "loaded_model_count": len(status.loaded_models),
        "backend_name": status.backend_name,
    }


def run_mainline(
    *,
    output_dir: Path,
    backend_python: Path,
    model_path: Path,
    run_id: str | None = None,
    d2_baseline_path: Path = D6_DEFAULT_BASELINE_PATH,
    prompt_ids: tuple[str, ...] = D6_DEFAULT_PROMPT_IDS,
    max_tokens_ladder: tuple[int, ...] = D6_DEFAULT_MAX_TOKENS_LADDER,
    timeout_s: float = 900.0,
    expected_mlx_lm_git_commit: str = D6_EXPECTED_MLX_LM_GIT_COMMIT,
    ttft_drift_rel_threshold: float = D6_TTFT_DRIFT_REL_THRESHOLD,
    decode_tps_drift_rel_threshold: float = D6_DECODE_TPS_DRIFT_REL_THRESHOLD,
    child_rss_drift_abs_threshold: float = D6_CHILD_RSS_DRIFT_ABS_THRESHOLD,
    expected_freed_gb_lower_bound: float = D6_FREED_GB_LOWER_BOUND,
    backend_factory: Any = None,
) -> dict[str, Any]:
    """Drive D6 mainline-backend lifecycle and write D6 evidence ledger.

    Spec: ``docs/architect/design/D6-mainline-backend-integration-spec.md``.
    Constructs ``MlxLmSubprocessBackend`` (or the injected ``backend_factory``)
    against ``backend_python``; runs preflight; on pass loads the model, runs
    the cartesian ``prompt_ids × max_tokens_ladder`` matrix in one session,
    cross-validates each row against the D2 baseline, then unloads. Writes
    one JSONL ledger plus one summary JSON.
    """

    run_id = run_id or f"{_compact_stamp()}-d6-mainline-backend-lifecycle"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    lifecycle_path = output_dir / f"{run_id}.jsonl"
    summary_path = output_dir / f"{run_id}.summary.json"

    backend_python = Path(backend_python)
    model_path = Path(model_path)
    d2_baseline_path = Path(d2_baseline_path)

    # ---------- Preflight ----------
    model_type = _d6_read_model_type_from_config(model_path)
    probe = _d6_probe_model_type_support(backend_python, model_type or MODEL_TYPE)
    provenance = _d6_runtime_provenance(backend_python)
    baseline_rows = _d6_load_baseline(d2_baseline_path) if d2_baseline_path.exists() else {}

    if backend_python.parent.name == "bin":
        mainline_runtime_path_str = str(backend_python.parent.parent)
    else:
        mainline_runtime_path_str = str(backend_python.parent)

    preflight_detail: dict[str, Any] = {
        "mainline_runtime_path": mainline_runtime_path_str,
        "deepseek_experimental_extras_installed": bool(probe.get("supported")),
        "mlx_lm_source": {
            "origin": provenance.get("origin"),
            "package_version": provenance.get("package_version"),
            "git_commit": provenance.get("git_commit"),
            "git_commit_matches_expected": (
                provenance.get("git_commit") == expected_mlx_lm_git_commit
            ),
        },
        "backend_class": "MlxLmSubprocessBackend",
        "python_executable": str(backend_python),
        "model_artifact_path": str(model_path),
        "model_type_in_config": model_type,
        "model_type_support_probe": {
            "module_name": probe.get("module_name"),
            "supported": bool(probe.get("supported")),
            "returncode": probe.get("returncode"),
        },
        "d2_baseline_evidence_path": str(d2_baseline_path),
        "d2_baseline_rows_present": len(baseline_rows),
        "stock_runtime_untouched": True,
        "default_model_surface_unchanged": True,
    }

    blocked_reasons: list[str] = []
    if not model_type:
        blocked_reasons.append("model_type_missing_from_config")
    if not probe.get("supported"):
        blocked_reasons.append("model_type_support_probe_unsupported")
    expected_baseline_rows = len(prompt_ids) * len(max_tokens_ladder)
    if len(baseline_rows) < expected_baseline_rows:
        blocked_reasons.append(
            f"d2_baseline_rows_insufficient ({len(baseline_rows)} < {expected_baseline_rows})"
        )

    if blocked_reasons:
        summary = {
            "schema_version": "d6.mainline-backend.run.v1",
            "run_id": run_id,
            "created_at": _now_utc(),
            "gate": "D6",
            "evidence_strength": D6_EVIDENCE_STRENGTH,
            "preflight": "blocked",
            "preflight_detail": preflight_detail,
            "blocked_reasons": blocked_reasons,
            "rows_written": 0,
            "passed_rows": 0,
            "drift_within_threshold_rows": 0,
            "backend_class": "MlxLmSubprocessBackend",
            "mlx_lm_git_commit": provenance.get("git_commit"),
            "metric_summary": {
                "ttft_ms": {"count": 0, "min": None, "p50": None, "max": None},
                "decode_tps_after_first_token": {
                    "count": 0,
                    "min": None,
                    "p50": None,
                    "max": None,
                },
                "child_rss_gb": {"count": 0, "min": None, "p50": None, "max": None},
            },
            "cross_validation_summary": {
                "ttft_ms_diff_rel_max": None,
                "decode_tps_diff_rel_max": None,
                "child_rss_gb_diff_abs_max": None,
            },
            "backend_health_summary": {
                "child_restart_observed": False,
                "clean_health_after_unload": False,
                "unload_freed_gb": None,
                "unload_time_s": None,
            },
            "overall_conclusion": "blocked",
            "verdict": "blocked",
            "lifecycle_path": str(lifecycle_path),
            "summary_path": str(summary_path),
        }
        _append_jsonl(lifecycle_path, [])
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
        )
        return summary

    # ---------- Backend lifecycle ----------
    if backend_factory is None:
        def _default_backend_factory(**kwargs: Any) -> Any:
            from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend

            return MlxLmSubprocessBackend(**kwargs)

        backend_factory = _default_backend_factory

    backend = backend_factory(
        python_executable=str(backend_python),
        timeout_s=timeout_s,
        auto_restart_dead_session=False,
        max_restart_attempts=0,
    )

    health_before_load = _d6_status_snapshot(backend)

    from owlmlx.runtime.types import ChatTurn  # local: keep script importable without owlmlx

    load_started = time.monotonic()
    load_result = backend.load(str(model_path), memory_gb=100.0)
    load_time_s = round(time.monotonic() - load_started, 4)

    if not load_result.ok:
        summary = {
            "schema_version": "d6.mainline-backend.run.v1",
            "run_id": run_id,
            "created_at": _now_utc(),
            "gate": "D6",
            "evidence_strength": D6_EVIDENCE_STRENGTH,
            "preflight": "passed",
            "preflight_detail": preflight_detail,
            "rows_written": 0,
            "passed_rows": 0,
            "drift_within_threshold_rows": 0,
            "backend_class": "MlxLmSubprocessBackend",
            "mlx_lm_git_commit": provenance.get("git_commit"),
            "load_error": {
                "message": load_result.message,
                "error_code": (
                    load_result.error_code.value if load_result.error_code else None
                ),
                "detail": load_result.detail,
            },
            "metric_summary": {
                "ttft_ms": {"count": 0, "min": None, "p50": None, "max": None},
                "decode_tps_after_first_token": {
                    "count": 0,
                    "min": None,
                    "p50": None,
                    "max": None,
                },
                "child_rss_gb": {"count": 0, "min": None, "p50": None, "max": None},
            },
            "cross_validation_summary": {
                "ttft_ms_diff_rel_max": None,
                "decode_tps_diff_rel_max": None,
                "child_rss_gb_diff_abs_max": None,
            },
            "backend_health_summary": {
                "child_restart_observed": False,
                "clean_health_after_unload": False,
                "unload_freed_gb": None,
                "unload_time_s": None,
            },
            "overall_conclusion": "failed",
            "verdict": "failed",
            "lifecycle_path": str(lifecycle_path),
            "summary_path": str(summary_path),
        }
        _append_jsonl(lifecycle_path, [])
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
        )
        return summary

    health_after_load = _d6_status_snapshot(backend)
    pid = load_result.detail.get("pid") if isinstance(load_result.detail, dict) else None

    rows: list[dict[str, Any]] = []
    overall_failed = False

    for prompt_id in prompt_ids:
        try:
            _index, _, prompt_text = _prompt_by_id(prompt_id)
        except ValueError:
            overall_failed = True
            rows.append(
                {
                    "schema_version": "d6.mainline-backend.v1",
                    "record_type": "mainline_backend_lifecycle_row",
                    "gate": "D6",
                    "run_id": run_id,
                    "created_at_utc": _now_utc(),
                    "prompt_id": prompt_id,
                    "max_tokens": None,
                    "metrics": {},
                    "cross_validation": {
                        "drift_within_threshold": False,
                        "reason": "unknown_prompt_id",
                    },
                    "verdict": "failed",
                    "verdict_reason": "unknown_prompt_id",
                }
            )
            continue
        messages_dicts = _messages_for_prompt(prompt_text)
        messages = [
            ChatTurn(role=msg["role"], content=msg["content"])
            for msg in messages_dicts
        ]

        for max_tokens in max_tokens_ladder:
            request_started = time.monotonic()
            first_token_at: float | None = None
            done_event = None
            stream_exception: BaseException | None = None
            try:
                for event in backend.stream_generate_messages(
                    str(model_path),
                    messages,
                    max_tokens=int(max_tokens),
                ):
                    if event.event == "token" and first_token_at is None:
                        first_token_at = time.monotonic()
                    if event.event == "done":
                        done_event = event
                    if event.event == "error":
                        stream_exception = RuntimeError(
                            f"stream error: {event.detail}"
                        )
                        break
            except BaseException as exc:  # noqa: BLE001
                stream_exception = exc
            stream_done_at = time.monotonic()

            if stream_exception is not None:
                overall_failed = True
                rows.append(
                    {
                        "schema_version": "d6.mainline-backend.v1",
                        "record_type": "mainline_backend_lifecycle_row",
                        "gate": "D6",
                        "run_id": run_id,
                        "created_at_utc": _now_utc(),
                        "model_id": MODEL_ID,
                        "backend_class": "MlxLmSubprocessBackend",
                        "prompt_id": prompt_id,
                        "max_tokens": int(max_tokens),
                        "metrics": {},
                        "stream_error": (
                            f"{type(stream_exception).__name__}: {stream_exception}"
                        ),
                        "cross_validation": {
                            "drift_within_threshold": False,
                            "reason": "stream_exception",
                        },
                        "verdict": "failed",
                        "verdict_reason": "stream_exception",
                    }
                )
                continue

            if first_token_at is None:
                first_token_at = stream_done_at
            ttft_ms = round((first_token_at - request_started) * 1000.0, 4)
            stream_wall_ms = round((stream_done_at - request_started) * 1000.0, 4)
            completion_tokens = done_event.completion_tokens if done_event else None
            prompt_tokens = done_event.prompt_tokens if done_event else None
            stop_reason = (
                done_event.finish_reason
                if done_event and done_event.finish_reason
                else "stop"
            )
            decode_tps = _decode_tps_after_first_token(
                completion_tokens=completion_tokens,
                first_visible_token_ms=ttft_ms,
                stream_wall_ms=stream_wall_ms,
            )
            wall_tps = _wall_tps(
                completion_tokens=completion_tokens,
                stream_wall_ms=stream_wall_ms,
            )
            child_rss_gb = _process_rss_gb(pid) if pid is not None else None

            actual_metrics = {
                "load_time_s": load_time_s,
                "ttft_ms": ttft_ms,
                "stream_wall_ms": stream_wall_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "decode_tps_after_first_token": decode_tps,
                "wall_tps": wall_tps,
                "child_rss_gb": child_rss_gb,
                "rss_sample_scope": RSS_SAMPLE_SCOPE,
                "rss_sample_source": RSS_SAMPLE_SOURCE,
                "rss_sample_timing": RSS_SAMPLE_TIMING,
            }
            baseline_row = baseline_rows.get((prompt_id, int(max_tokens)))
            cross = _d6_cross_validation(
                actual_metrics=actual_metrics,
                baseline_row=baseline_row,
                ttft_drift_rel_threshold=ttft_drift_rel_threshold,
                decode_tps_drift_rel_threshold=decode_tps_drift_rel_threshold,
                child_rss_drift_abs_threshold=child_rss_drift_abs_threshold,
            )
            row_health = _d6_status_snapshot(backend)

            verdict = "passed"
            verdict_reason: str | None = None
            if not cross["drift_within_threshold"]:
                verdict = "failed"
                verdict_reason = "cross_validation_drift"
                overall_failed = True
            if done_event is None:
                verdict = "failed"
                verdict_reason = verdict_reason or "no_done_event"
                overall_failed = True

            rows.append(
                {
                    "schema_version": "d6.mainline-backend.v1",
                    "record_type": "mainline_backend_lifecycle_row",
                    "gate": "D6",
                    "run_id": run_id,
                    "created_at_utc": _now_utc(),
                    "model_id": MODEL_ID,
                    "backend_class": "MlxLmSubprocessBackend",
                    "backend_path": {
                        "python_executable": str(backend_python),
                        "runner_module": RUNNER_MODULE,
                        "deepseek_experimental_extras_active": True,
                        "mlx_lm_source": {
                            "git_commit": provenance.get("git_commit"),
                            "package_version": provenance.get("package_version"),
                        },
                    },
                    "prompt_surface": D1_PROMPT_SURFACE_DEFAULT,
                    "generation_surface": "stream_generate_messages",
                    "prompt_id": prompt_id,
                    "max_tokens": int(max_tokens),
                    "stop_reason": stop_reason,
                    "metrics": actual_metrics,
                    "backend_health_snapshot": {
                        "before_load": health_before_load,
                        "after_load": health_after_load,
                        "after_this_row": row_health,
                    },
                    "cross_validation": cross,
                    "host_state": {
                        "unified_memory_gb_capacity": 128,
                    },
                    "verdict": verdict,
                    "verdict_reason": verdict_reason,
                }
            )

    # ---------- Unload ----------
    unload_started = time.monotonic()
    unload_result = backend.unload(str(model_path))
    unload_time_s = round(time.monotonic() - unload_started, 4)
    health_after_unload = _d6_status_snapshot(backend)
    freed_gb: float | None = (
        float(unload_result.freed_gb) if unload_result.ok else None
    )
    if not unload_result.ok:
        overall_failed = True
    elif freed_gb is not None and freed_gb < expected_freed_gb_lower_bound:
        overall_failed = True

    clean_health_after_unload = (
        health_after_unload.get("healthy") is True
        and health_after_unload.get("loaded_model_count") == 0
    )
    if not clean_health_after_unload:
        overall_failed = True

    if rows:
        rows[-1].setdefault("backend_health_snapshot", {})[
            "after_unload"
        ] = health_after_unload

    _append_jsonl(lifecycle_path, rows)

    passed_rows = sum(1 for row in rows if row.get("verdict") == "passed")
    drift_within_rows = sum(
        1
        for row in rows
        if isinstance(row.get("cross_validation"), dict)
        and row["cross_validation"].get("drift_within_threshold") is True
    )

    ttft_diffs = [
        abs(row["cross_validation"]["ttft_ms_diff_rel"])
        for row in rows
        if isinstance(row.get("cross_validation"), dict)
        and row["cross_validation"].get("ttft_ms_diff_rel") is not None
    ]
    decode_diffs = [
        abs(row["cross_validation"]["decode_tps_diff_rel"])
        for row in rows
        if isinstance(row.get("cross_validation"), dict)
        and row["cross_validation"].get("decode_tps_diff_rel") is not None
    ]
    rss_diffs = [
        abs(row["cross_validation"]["child_rss_gb_diff_abs"])
        for row in rows
        if isinstance(row.get("cross_validation"), dict)
        and row["cross_validation"].get("child_rss_gb_diff_abs") is not None
    ]

    expected_rows = len(prompt_ids) * len(max_tokens_ladder)
    if len(rows) != expected_rows:
        overall_failed = True

    overall = "failed" if overall_failed or passed_rows != len(rows) else "passed"

    summary = {
        "schema_version": "d6.mainline-backend.run.v1",
        "run_id": run_id,
        "created_at": _now_utc(),
        "gate": "D6",
        "evidence_strength": D6_EVIDENCE_STRENGTH,
        "preflight": "passed",
        "preflight_detail": preflight_detail,
        "rows_written": len(rows),
        "passed_rows": passed_rows,
        "drift_within_threshold_rows": drift_within_rows,
        "backend_class": "MlxLmSubprocessBackend",
        "mlx_lm_git_commit": provenance.get("git_commit"),
        "metric_summary": {
            "ttft_ms": _metric_distribution(rows, "ttft_ms"),
            "decode_tps_after_first_token": _metric_distribution(
                rows, "decode_tps_after_first_token"
            ),
            "child_rss_gb": _metric_distribution(rows, "child_rss_gb"),
        },
        "cross_validation_summary": {
            "ttft_ms_diff_rel_max": max(ttft_diffs) if ttft_diffs else None,
            "decode_tps_diff_rel_max": max(decode_diffs) if decode_diffs else None,
            "child_rss_gb_diff_abs_max": max(rss_diffs) if rss_diffs else None,
        },
        "backend_health_summary": {
            "child_restart_observed": False,
            "clean_health_after_unload": clean_health_after_unload,
            "unload_freed_gb": freed_gb,
            "unload_time_s": unload_time_s,
        },
        "overall_conclusion": overall,
        "verdict": overall,
        "lifecycle_path": str(lifecycle_path),
        "summary_path": str(summary_path),
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary


def _cmd_mainline(args: argparse.Namespace) -> int:
    payload = run_mainline(
        output_dir=args.output_dir,
        run_id=args.run_id,
        backend_python=args.backend_python,
        model_path=args.model_path,
        d2_baseline_path=args.d2_baseline,
        prompt_ids=tuple(args.prompt_id) if args.prompt_id else D6_DEFAULT_PROMPT_IDS,
        max_tokens_ladder=_token_ladder_from_cli(
            args.max_tokens, default=D6_DEFAULT_MAX_TOKENS_LADDER
        ),
        timeout_s=args.timeout_s,
        expected_mlx_lm_git_commit=args.expected_mlx_lm_git_commit,
        ttft_drift_rel_threshold=args.ttft_drift_rel_threshold,
        decode_tps_drift_rel_threshold=args.decode_tps_drift_rel_threshold,
        child_rss_drift_abs_threshold=args.child_rss_drift_abs_threshold,
        expected_freed_gb_lower_bound=args.expected_freed_gb_lower_bound,
    )
    _json_print(payload)
    return 0 if payload.get("overall_conclusion") == "passed" else 1


def _cmd_preflight(args: argparse.Namespace) -> int:
    payload = run_preflight(
        isolated_python=args.isolated_python,
        model_path=args.model_path,
        isolated_runtime_path=args.isolated_runtime_path,
    )
    _json_print(payload)
    return 0 if payload["verdict"] == "passed" else 1


def _cmd_dry_run(args: argparse.Namespace) -> int:
    payload = run_dry_run(
        output_dir=args.output_dir,
        isolated_runtime_path=args.isolated_runtime_path,
        isolated_python=args.isolated_python,
        model_path=args.model_path,
        run_id=args.run_id,
    )
    _json_print(payload)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    payload = run_real(
        output_dir=args.output_dir,
        isolated_runtime_path=args.isolated_runtime_path,
        isolated_python=args.isolated_python,
        model_path=args.model_path,
        run_id=args.run_id,
        max_prompts=args.max_prompts,
        prompt_ids=tuple(args.prompt_id or ()),
        max_tokens_ladder=_token_ladder_from_cli(
            args.max_tokens,
            default=TOKEN_LADDER,
        ),
        generation_surface=args.generation_surface,
        prompt_surface=args.prompt_surface,
        continue_on_failure=args.continue_on_failure,
        generation_overrides={
            "max_kv_size": args.max_kv_size,
            "kv_bits": args.kv_bits,
            "kv_group_size": args.kv_group_size,
            "temperature": args.temp,
            "top_p": args.top_p,
            "min_p": args.min_p,
            "top_k": args.top_k,
            "stop": args.stop,
        },
        timeout_s=args.timeout_s,
    )
    _json_print(payload)
    return 0 if payload["verdict"] == "passed" else 1


def _cmd_compare(args: argparse.Namespace) -> int:
    payload = run_direct_vs_runner(
        output_dir=args.output_dir,
        isolated_runtime_path=args.isolated_runtime_path,
        isolated_python=args.isolated_python,
        model_path=args.model_path,
        run_id=args.run_id,
        prompt_id=args.prompt_id,
        max_tokens=args.max_tokens,
        generation_overrides={
            "max_kv_size": args.max_kv_size,
            "kv_bits": args.kv_bits,
            "kv_group_size": args.kv_group_size,
            "temperature": args.temp,
            "top_p": args.top_p,
            "min_p": args.min_p,
            "top_k": args.top_k,
            "stop": args.stop,
        },
        timeout_s=args.timeout_s,
    )
    _json_print(payload)
    return 0 if payload["verdict"] == "diagnostic_passed" else 1


def _cmd_metrics(args: argparse.Namespace) -> int:
    payload = run_metrics(
        output_dir=args.output_dir,
        isolated_runtime_path=args.isolated_runtime_path,
        isolated_python=args.isolated_python,
        model_path=args.model_path,
        run_id=args.run_id,
        max_prompts=args.max_prompts,
        prompt_ids=tuple(args.prompt_id or ()),
        max_tokens_ladder=_token_ladder_from_cli(
            args.max_tokens,
            default=(128,),
        ),
        generation_overrides={
            "max_kv_size": args.max_kv_size,
            "kv_bits": args.kv_bits,
            "kv_group_size": args.kv_group_size,
            "temperature": args.temp,
            "top_p": args.top_p,
            "min_p": args.min_p,
            "top_k": args.top_k,
            "stop": args.stop,
        },
        prompt_surface=args.prompt_surface,
        timeout_s=args.timeout_s,
    )
    _json_print(payload)
    return 0 if payload["verdict"] == "passed" else 1


def _cmd_checkpoint_inspect(args: argparse.Namespace) -> int:
    payload = run_mtp_checkpoint_inspection(
        output_dir=args.output_dir,
        model_path=args.model_path,
        adapter_path=args.adapter_path,
        run_id=args.run_id,
    )
    _json_print(payload)
    return 0 if payload["verdict"] == "passed" else 1


def _cmd_mtp_preload_reject(args: argparse.Namespace) -> int:
    runtime_health_url = None if args.no_runtime_health else args.runtime_health_url
    payload = run_mtp_preload_reject(
        output_dir=args.output_dir,
        model_path=args.model_path,
        adapter_path=args.adapter_path,
        run_id=args.run_id,
        inspection_path=args.inspection_path,
        runtime_health_url=runtime_health_url,
    )
    _json_print(payload)
    return 0 if payload["verdict"] == "passed" else 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--isolated-runtime-path",
            type=Path,
            default=DEFAULT_ISOLATED_RUNTIME_PATH,
        )
        p.add_argument("--isolated-python", type=Path, default=DEFAULT_ISOLATED_PYTHON)
        p.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)

    preflight = sub.add_parser("preflight", help="Check isolated D1 runtime readiness")
    add_common(preflight)
    preflight.set_defaults(func=_cmd_preflight)

    dry = sub.add_parser("dry-run", help="Write synthetic D1 JSONL rows")
    add_common(dry)
    dry.add_argument("--output-dir", type=Path, required=True)
    dry.add_argument("--run-id", default=None)
    dry.set_defaults(func=_cmd_dry_run)

    fake = sub.add_parser("fake-run", help="Alias for dry-run")
    add_common(fake)
    fake.add_argument("--output-dir", type=Path, required=True)
    fake.add_argument("--run-id", default=None)
    fake.set_defaults(func=_cmd_dry_run)

    run = sub.add_parser("run", help="Run real isolated D1 load/generate/unload")
    add_common(run)
    run.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    run.add_argument("--run-id", default=None)
    run.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        help="Optional smoke limiter; omit for the full D1 prompt set.",
    )
    run.add_argument(
        "--prompt-id",
        action="append",
        default=None,
        help="Run only the selected D1 prompt id; repeat for multiple prompts.",
    )
    run.add_argument(
        "--max-tokens",
        type=int,
        nargs="+",
        action="append",
        default=None,
        help="Token ladder to execute; defaults to the full D1 ladder.",
    )
    run.add_argument("--timeout-s", type=float, default=600.0)
    run.add_argument(
        "--generation-surface",
        choices=("generate", "stream"),
        default="generate",
        help="Use non-stream generate for lifecycle runs; stream for timing diagnostics.",
    )
    run.add_argument(
        "--prompt-surface",
        choices=("raw", "messages"),
        default=D1_PROMPT_SURFACE_DEFAULT,
        help="Use runner chat-template messages by default; raw is diagnostic.",
    )
    run.add_argument(
        "--continue-on-failure",
        action="store_true",
        help=(
            "Diagnostic mode: keep running the requested prompt/token matrix after "
            "a failed row. The run verdict still fails unless the full matrix passes."
        ),
    )
    run.add_argument("--max-kv-size", type=int, default=D1_GENERATION_DEFAULTS["max_kv_size"])
    run.add_argument("--kv-bits", type=int, default=None)
    run.add_argument(
        "--kv-group-size",
        type=int,
        default=None,
    )
    run.add_argument("--temp", type=float, default=D1_GENERATION_DEFAULTS["temperature"])
    run.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="Optional sampler top_p forwarded to the isolated runner.",
    )
    run.add_argument(
        "--min-p",
        type=float,
        default=None,
        help="Optional sampler min_p forwarded to the isolated runner.",
    )
    run.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Optional sampler top_k forwarded to the isolated runner.",
    )
    run.add_argument(
        "--stop",
        action="append",
        default=None,
        help="Experimental stop string passed through to the isolated runner.",
    )
    run.set_defaults(func=_cmd_run)

    compare = sub.add_parser(
        "compare",
        help="Run direct mlx_lm.generate versus owlmlx runner for one D1 row",
    )
    add_common(compare)
    compare.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    compare.add_argument("--run-id", default=None)
    compare.add_argument(
        "--prompt-id",
        default="p1_short_cn",
        help="Run a single D1 prompt id through both surfaces.",
    )
    compare.add_argument("--max-tokens", type=int, default=1024)
    compare.add_argument("--timeout-s", type=float, default=900.0)
    compare.add_argument(
        "--max-kv-size",
        type=int,
        default=D1_GENERATION_DEFAULTS["max_kv_size"],
    )
    compare.add_argument("--kv-bits", type=int, default=None)
    compare.add_argument("--kv-group-size", type=int, default=None)
    compare.add_argument("--temp", type=float, default=D1_GENERATION_DEFAULTS["temperature"])
    compare.add_argument("--top-p", type=float, default=None)
    compare.add_argument("--min-p", type=float, default=None)
    compare.add_argument("--top-k", type=int, default=None)
    compare.add_argument(
        "--stop",
        action="append",
        default=None,
        help="Experimental stop string passed through to both surfaces.",
    )
    compare.set_defaults(func=_cmd_compare)

    metrics = sub.add_parser(
        "metrics",
        help="Run isolated D2 stream metrics ledger for DeepSeek V4",
    )
    add_common(metrics)
    metrics.add_argument("--output-dir", type=Path, default=D2_DEFAULT_OUTPUT_DIR)
    metrics.add_argument("--run-id", default=None)
    metrics.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        help="Optional smoke limiter; omit to run the selected prompt set.",
    )
    metrics.add_argument(
        "--prompt-id",
        action="append",
        default=None,
        help="Run only the selected D1 prompt id; repeat for multiple prompts.",
    )
    metrics.add_argument(
        "--max-tokens",
        type=int,
        nargs="+",
        action="append",
        default=None,
        help=(
            "Metric token ladder; defaults to 128 for a light D2 smoke. "
            "Accepts either '--max-tokens 128 512' or repeated flags."
        ),
    )
    metrics.add_argument("--timeout-s", type=float, default=900.0)
    metrics.add_argument(
        "--prompt-surface",
        choices=("raw", "messages"),
        default=D1_PROMPT_SURFACE_DEFAULT,
        help="Use adopted messages/chat-template prompt surface by default.",
    )
    metrics.add_argument(
        "--max-kv-size",
        type=int,
        default=D1_GENERATION_DEFAULTS["max_kv_size"],
    )
    metrics.add_argument("--kv-bits", type=int, default=None)
    metrics.add_argument("--kv-group-size", type=int, default=None)
    metrics.add_argument("--temp", type=float, default=D1_GENERATION_DEFAULTS["temperature"])
    metrics.add_argument("--top-p", type=float, default=None)
    metrics.add_argument("--min-p", type=float, default=None)
    metrics.add_argument("--top-k", type=int, default=None)
    metrics.add_argument(
        "--stop",
        action="append",
        default=None,
        help="Experimental stop string passed through to the isolated runner.",
    )
    metrics.set_defaults(func=_cmd_metrics)

    mainline = sub.add_parser(
        "mainline",
        help=(
            "Run D6 mainline backend lifecycle via MlxLmSubprocessBackend "
            "against the deepseek-experimental extras venv"
        ),
    )
    mainline.add_argument(
        "--backend-python",
        type=Path,
        default=D6_DEFAULT_BACKEND_PYTHON,
        help=(
            "Path to the python executable inside a venv populated with the "
            "deepseek-experimental extras group."
        ),
    )
    mainline.add_argument(
        "--model-path",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help="DSV4-Flash 2bit-DQ artifact directory.",
    )
    mainline.add_argument(
        "--output-dir",
        type=Path,
        default=D6_DEFAULT_OUTPUT_DIR,
        help="Where to write the D6 lifecycle JSONL and summary JSON.",
    )
    mainline.add_argument(
        "--d2-baseline",
        type=Path,
        default=D6_DEFAULT_BASELINE_PATH,
        help="D2 metrics ledger JSONL used as cross-validation baseline.",
    )
    mainline.add_argument("--run-id", default=None)
    mainline.add_argument(
        "--prompt-id",
        action="append",
        default=None,
        help=(
            "Restrict the prompt set; repeatable. Defaults to "
            f"{','.join(D6_DEFAULT_PROMPT_IDS)} per design spec."
        ),
    )
    mainline.add_argument(
        "--max-tokens",
        type=int,
        nargs="+",
        action="append",
        default=None,
        help=(
            "Token ladder; defaults to "
            f"{','.join(str(v) for v in D6_DEFAULT_MAX_TOKENS_LADDER)}."
        ),
    )
    mainline.add_argument("--timeout-s", type=float, default=900.0)
    mainline.add_argument(
        "--expected-mlx-lm-git-commit",
        default=D6_EXPECTED_MLX_LM_GIT_COMMIT,
        help=(
            "Expected mlx-lm git commit pinned by the deepseek-experimental "
            "extras group; mismatch is logged but does not fail preflight."
        ),
    )
    mainline.add_argument(
        "--ttft-drift-rel-threshold",
        type=float,
        default=D6_TTFT_DRIFT_REL_THRESHOLD,
    )
    mainline.add_argument(
        "--decode-tps-drift-rel-threshold",
        type=float,
        default=D6_DECODE_TPS_DRIFT_REL_THRESHOLD,
    )
    mainline.add_argument(
        "--child-rss-drift-abs-threshold",
        type=float,
        default=D6_CHILD_RSS_DRIFT_ABS_THRESHOLD,
    )
    mainline.add_argument(
        "--expected-freed-gb-lower-bound",
        type=float,
        default=D6_FREED_GB_LOWER_BOUND,
    )
    mainline.set_defaults(func=_cmd_mainline)

    inspect = sub.add_parser(
        "checkpoint-inspect",
        help="Inspect isolated DeepSeek V4 checkpoint metadata for D3 MTP weights",
    )
    add_common(inspect)
    inspect.add_argument("--output-dir", type=Path, default=D3_DEFAULT_OUTPUT_DIR)
    inspect.add_argument("--run-id", default=None)
    inspect.add_argument(
        "--adapter-path",
        type=Path,
        default=DEFAULT_DEEPSEEK_ADAPTER_PATH,
        help="DeepSeek V4 adapter fork used for D1/D2 evidence.",
    )
    inspect.set_defaults(func=_cmd_checkpoint_inspect)

    reject = sub.add_parser(
        "mtp-preload-reject",
        help="Record D4 clean pre-load rejection for unavailable DeepSeek MTP",
    )
    add_common(reject)
    reject.add_argument("--output-dir", type=Path, default=D4_DEFAULT_OUTPUT_DIR)
    reject.add_argument("--run-id", default=None)
    reject.add_argument(
        "--adapter-path",
        type=Path,
        default=DEFAULT_DEEPSEEK_ADAPTER_PATH,
        help="DeepSeek V4 adapter fork used for D1/D2/D3 evidence.",
    )
    reject.add_argument(
        "--inspection-path",
        type=Path,
        default=None,
        help="Existing D3 checkpoint-inspection JSONL row to consume.",
    )
    reject.add_argument(
        "--runtime-health-url",
        default=DEFAULT_RUNTIME_HEALTH_URL,
        help="Optional runtime health URL to probe before and after rejection.",
    )
    reject.add_argument(
        "--no-runtime-health",
        action="store_true",
        help="Skip runtime health probing; use only for offline shape tests.",
    )
    reject.set_defaults(func=_cmd_mtp_preload_reject)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
