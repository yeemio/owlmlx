"""Persistent child-process runner for mlx-lm execution.

This module is executed in an isolated Python process. It is the only place in
owlmlx runtime where ``mlx_lm`` is imported for real execution. The parent
runtime communicates through stdin/stdout JSON lines so Metal/Objective-C
crashes cannot terminate the parent process.
"""

from __future__ import annotations

import json
import gc
import os
import sys
from contextlib import redirect_stdout
from typing import Any


def _parse_request(line: str) -> dict[str, Any]:
    try:
        return json.loads(line or "{}")
    except Exception as exc:
        return {"_parse_error": str(exc)}


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload), flush=True)


def main() -> int:
    current_model_id: str | None = None
    model: Any | None = None
    tokenizer: Any | None = None
    generation_count = 0

    for line in sys.stdin:
        request = _parse_request(line.strip())
        if "_parse_error" in request:
            _emit({"ok": False, "error": request["_parse_error"]})
            continue

        action = str(request.get("action") or "").strip().lower()
        model_id = request.get("model_id")
        prompt = request.get("prompt", "")
        params = dict(request.get("params") or {})

        try:
            if action == "load":
                if not model_id:
                    _emit({"ok": False, "error": "model_id is required"})
                    continue
                if current_model_id and current_model_id != model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                "runner already loaded a different model: "
                                f"{current_model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                with redirect_stdout(sys.stderr):
                    model, tokenizer = mlx_lm.load(str(model_id))
                current_model_id = str(model_id)
                generation_count = 0
                _emit(
                    {
                        "ok": True,
                        "action": "load",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                    }
                )
                continue

            if action == "generate":
                if not current_model_id or model is None or tokenizer is None:
                    _emit({"ok": False, "error": "no model loaded"})
                    continue
                if model_id and str(model_id) != current_model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                f"loaded model is {current_model_id}, "
                                f"not {model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                with redirect_stdout(sys.stderr):
                    text = mlx_lm.generate(
                        model,
                        tokenizer,
                        prompt=str(prompt),
                        **params,
                    )
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate",
                        "model_id": current_model_id,
                        "text": str(text),
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                    }
                )
                continue

            if action == "unload":
                unloaded_model = current_model_id
                current_model_id = None
                model = None
                tokenizer = None
                generation_count = 0
                gc.collect()
                _emit(
                    {
                        "ok": True,
                        "action": "unload",
                        "model_id": unloaded_model,
                        "pid": os.getpid(),
                    }
                )
                continue

            if action == "ping":
                _emit(
                    {
                        "ok": True,
                        "action": "ping",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                    }
                )
                continue

            if action == "shutdown":
                _emit(
                    {
                        "ok": True,
                        "action": "shutdown",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                    }
                )
                return 0

            _emit({"ok": False, "error": f"unsupported action: {action or '<empty>'}"})
        except Exception as exc:
            _emit(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
