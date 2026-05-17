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


def _relative_runtime_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _check_isolated_imports(python_path: Path, timeout_s: float = 20.0) -> dict[str, Any]:
    code = (
        "import importlib.util, json\n"
        "mods = ['mlx_lm', 'mlx_lm.models.deepseek_v4']\n"
        "results = {}\n"
        "for mod in mods:\n"
        "    try:\n"
        "        results[mod] = importlib.util.find_spec(mod) is not None\n"
        "    except ModuleNotFoundError:\n"
        "        results[mod] = False\n"
        "print(json.dumps(results, sort_keys=True))\n"
    )
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
            "stderr": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "imports": {},
            "stderr": f"import preflight timed out after {exc.timeout}s",
        }

    imports: dict[str, bool] = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout.strip().splitlines()[-1])
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
            }


def _looks_repetitive(text: str) -> bool:
    normalized = " ".join(text.split())
    if len(normalized) < 120:
        return False
    windows = [normalized[index : index + 40] for index in range(0, len(normalized), 40)]
    counts = {window: windows.count(window) for window in windows if window}
    return any(count >= 4 for count in counts.values())


def _completion_observation(text: str) -> dict[str, Any]:
    preview_chars = 240
    return {
        "completion_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "completion_preview": text[:preview_chars],
        "completion_tail": text[-preview_chars:] if len(text) > preview_chars else text,
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
    repetition_flag = _looks_repetitive(text)
    completion_observation = _completion_observation(text)

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
                    "timing": result.get("timing") if isinstance(result.get("timing"), dict) else {},
                    "restart_observed": restart_observed,
                    "repetition_flag": repetition_flag,
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


def run_real(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    isolated_runtime_path: Path = DEFAULT_ISOLATED_RUNTIME_PATH,
    isolated_python: Path = DEFAULT_ISOLATED_PYTHON,
    model_path: Path = DEFAULT_MODEL_PATH,
    run_id: str | None = None,
    max_prompts: int | None = None,
    max_tokens_ladder: tuple[int, ...] = TOKEN_LADDER,
    generation_overrides: dict[str, Any] | None = None,
    generation_surface: str = "generate",
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
    prompt_slice = PROMPTS if max_prompts is None else PROMPTS[:max_prompts]
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
                if rows[-1]["verdict"] != "passed":
                    break
            if rows and rows[-1]["verdict"] != "passed":
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
    verdict = (
        "passed"
        if rows and all(row["verdict"] == "passed" for row in rows)
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
        "token_ladder": list(token_ladder),
        "tokenizer_config": D1_TOKENIZER_CONFIG,
        "generation_defaults": D1_GENERATION_DEFAULTS,
        "generation_overrides": generation_overrides,
        "generation_surface": generation_surface,
        "preflight": preflight,
        "lifecycle": {
            "load_ok": load_ok,
            "unload_ok": unload_ok,
            "clean_health_after_unload": clean_health_after_unload,
        },
        "verdict": verdict,
        **({"error": run_error} if run_error else {}),
    }


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
        max_tokens_ladder=tuple(args.max_tokens),
        generation_surface=args.generation_surface,
        generation_overrides={
            "max_kv_size": args.max_kv_size,
            "kv_bits": args.kv_bits,
            "kv_group_size": args.kv_group_size,
            "temperature": args.temp,
        },
        timeout_s=args.timeout_s,
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
    run.add_argument("--max-kv-size", type=int, default=D1_GENERATION_DEFAULTS["max_kv_size"])
    run.add_argument("--kv-bits", type=int, default=None)
    run.add_argument(
        "--kv-group-size",
        type=int,
        default=None,
    )
    run.add_argument("--temp", type=float, default=D1_GENERATION_DEFAULTS["temperature"])
    run.set_defaults(func=_cmd_run)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
