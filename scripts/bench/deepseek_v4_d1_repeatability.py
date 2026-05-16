"""D1 DeepSeek V4 isolated repeatability runner skeleton.

This script is intentionally isolated from the stock owlmlx runtime. Preflight
checks the caller-selected DeepSeek V4 Python environment and model path; dry-run
only writes synthetic schema smoke rows to an explicit output directory.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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
    preflight = run_preflight(
        isolated_python=args.isolated_python,
        model_path=args.model_path,
        isolated_runtime_path=args.isolated_runtime_path,
    )
    if preflight["verdict"] != "passed":
        payload = {
            "schema_version": "d1.run.v1",
            "gate": "D1",
            "runtime": "owlmlx",
            "model_id": MODEL_ID,
            "preflight": preflight,
            "verdict": "blocked",
            "message": (
                "real D1 execution is blocked by preflight; this skeleton does "
                "not repair venvs, install dependencies, or fall back to stock .venv"
            ),
        }
        _json_print(payload)
        return 1
    payload = {
        "schema_version": "d1.run.v1",
        "gate": "D1",
        "runtime": "owlmlx",
        "model_id": MODEL_ID,
        "preflight": preflight,
        "verdict": "blocked",
        "message": "real D1 generation is intentionally not implemented in this skeleton",
    }
    _json_print(payload)
    return 1


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

    run = sub.add_parser("run", help="Real D1 entrypoint placeholder")
    add_common(run)
    run.set_defaults(func=_cmd_run)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
