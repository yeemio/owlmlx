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
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "files" / "evidence" / "owlmlx" / "deepseek-v4" / "d1-isolated-repeatability"
)
RUNNER_MODULE = "owlmlx.runtime.mlx_lm_runner"

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
    _write_child_request(proc, request)
    text_parts: list[str] = []
    token_event_count = 0
    stream_diagnostics: list[dict[str, Any]] = []
    last_token: dict[str, Any] | None = None
    while True:
        payload = _read_json_payload(proc, timeout_s=timeout_s)
        if not payload.get("ok", False):
            return {
                "ok": False,
                "action": "stream_generate",
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
        if action == "stream_event" and event == "token":
            text_parts.append(str(payload.get("text") or ""))
            token_event_count += 1
            last_token = payload
            continue
        if action == "stream_done" and event == "done":
            timing = payload.get("timing") if isinstance(payload.get("timing"), dict) else {}
            return {
                "ok": True,
                "action": "stream_generate",
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


def _generation_params(*, max_tokens: int, overrides: dict[str, Any]) -> dict[str, Any]:
    params = {**D1_GENERATION_DEFAULTS}
    params.update(
        {key: value for key, value in overrides.items() if value is not None}
    )
    params["max_tokens"] = int(max_tokens)
    return params


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
    max_tokens: int,
    generation_params: dict[str, Any],
    load_ok: bool,
    unload_ok: bool,
    clean_health_after_unload: bool,
    load_time_s: float | None,
    result: dict[str, Any],
    load_pid: Any,
) -> dict[str, Any]:
    text = str(result.get("text") or "")
    result_pid = result.get("pid")
    generation_surface = str(result.get("action") or "generate")
    if generation_surface == "stream_generate":
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
            "prompt_shape": _prompt_shape(prompt),
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
                    "completion_tokens": result.get("completion_tokens"),
                    "stream_event_count": result.get("stream_event_count"),
                    "stream_diagnostic_count": result.get("stream_diagnostic_count"),
                    "stream_diagnostics": result.get("stream_diagnostics", []),
                    "stop_strings": stop_strings if isinstance(stop_strings, list) else [],
                    "stop_string_count": stop_string_count,
                    "timing": result.get("timing") if isinstance(result.get("timing"), dict) else {},
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
                    prompt_id: result.get("timing", {}).get("first_visible_token_ms")
                }
                if isinstance(result.get("timing"), dict)
                and result.get("timing", {}).get("first_visible_token_ms") is not None
                else {},
                "decode_tps_by_prompt": {},
                "stream_wall_ms_by_prompt": {
                    prompt_id: result.get("timing", {}).get("stream_wall_ms")
                }
                if isinstance(result.get("timing"), dict)
                and result.get("timing", {}).get("stream_wall_ms") is not None
                else {},
                "peak_rss_gb": None,
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
    continue_on_failure: bool = False,
    timeout_s: float = 600.0,
    popen_factory: Any = subprocess.Popen,
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
    rows: list[dict[str, Any]] = []
    load_ok = False
    unload_ok = False
    clean_health_after_unload = False
    load_time_s: float | None = None
    load_pid: Any = None
    run_error: str | None = None
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
                        max_tokens=max_tokens,
                        generation_params=generation_params,
                        load_ok=load_ok,
                        unload_ok=False,
                        clean_health_after_unload=False,
                        load_time_s=load_time_s,
                        result=result,
                        load_pid=load_pid,
                    )
                )
                if rows[-1]["verdict"] != "passed" and not continue_on_failure:
                    break
            if rows and rows[-1]["verdict"] != "passed" and not continue_on_failure:
                break

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
        if proc is not None and proc.poll() is None:
            try:
                _child_exchange(proc, {"action": "shutdown"}, timeout_s=5.0)
            except Exception:
                pass
            if proc.poll() is None:
                try:
                    proc.terminate()
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
        max_tokens_ladder=tuple(args.max_tokens),
        generation_surface=args.generation_surface,
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
        default=list(TOKEN_LADDER),
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

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
