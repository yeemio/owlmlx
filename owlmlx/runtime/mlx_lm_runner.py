"""Child-process runner for mlx-lm load+generate.

This module is executed in an isolated Python process. It is the only place in
Runtime-1 where ``mlx_lm`` is imported for real execution. The parent runtime
communicates through stdin/stdout JSON so Metal/Objective-C crashes cannot
terminate the parent process.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def _read_request() -> dict[str, Any]:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception as exc:
        return {"_parse_error": str(exc)}


def main() -> int:
    request = _read_request()
    if "_parse_error" in request:
        print(json.dumps({"ok": False, "error": request["_parse_error"]}))
        return 2

    model_id = request.get("model_id")
    prompt = request.get("prompt", "")
    params = dict(request.get("params") or {})
    if not model_id:
        print(json.dumps({"ok": False, "error": "model_id is required"}))
        return 2

    try:
        import mlx_lm  # noqa: PLC0415

        model, tokenizer = mlx_lm.load(str(model_id))
        text = mlx_lm.generate(model, tokenizer, prompt=str(prompt), **params)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        )
        return 2

    print(
        json.dumps(
            {
                "ok": True,
                "text": str(text),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
