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


def _fallback_prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{str(message.get('role') or 'user')}: {str(message.get('content') or '')}"
        for message in messages
    )


def _prompt_from_messages(tokenizer: Any, messages: list[dict[str, Any]]) -> str:
    if hasattr(tokenizer, "apply_chat_template"):
        return str(
            tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        )
    return _fallback_prompt_from_messages(messages)


def _parse_request(line: str) -> dict[str, Any]:
    try:
        return json.loads(line or "{}")
    except Exception as exc:
        return {"_parse_error": str(exc)}


def _emit(payload: dict[str, Any]) -> None:
    sys.__stdout__.write(json.dumps(payload) + "\n")
    sys.__stdout__.flush()


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
        messages = list(request.get("messages") or [])
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

            if action == "generate_messages":
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

                rendered_prompt = _prompt_from_messages(tokenizer, messages)
                with redirect_stdout(sys.stderr):
                    text = mlx_lm.generate(
                        model,
                        tokenizer,
                        prompt=rendered_prompt,
                        **params,
                    )
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate_messages",
                        "model_id": current_model_id,
                        "text": str(text),
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                        "message_count": len(messages),
                    }
                )
                continue

            if action == "stream_generate":
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

                sequence = 0
                prompt_tokens = None
                completion_tokens = 0
                finish_reason = "stop"
                with redirect_stdout(sys.stderr):
                    for response in mlx_lm.stream_generate(
                        model,
                        tokenizer,
                        prompt=str(prompt),
                        **params,
                    ):
                        sequence += 1
                        prompt_tokens = getattr(response, "prompt_tokens", prompt_tokens)
                        completion_tokens = int(
                            getattr(response, "generation_tokens", completion_tokens) or 0
                        )
                        finish_reason = str(
                            getattr(response, "finish_reason", finish_reason) or finish_reason
                        )
                        _emit(
                            {
                                "ok": True,
                                "action": "stream_event",
                                "event": "token",
                                "model_id": current_model_id,
                                "text": str(getattr(response, "text", "") or ""),
                                "pid": os.getpid(),
                                "sequence": sequence,
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "finish_reason": finish_reason,
                            }
                        )
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "stream_done",
                        "event": "done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                        "sequence": sequence,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "finish_reason": finish_reason,
                    }
                )
                continue

            if action == "stream_generate_messages":
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

                rendered_prompt = _prompt_from_messages(tokenizer, messages)
                sequence = 0
                prompt_tokens = None
                completion_tokens = 0
                finish_reason = "stop"
                with redirect_stdout(sys.stderr):
                    for response in mlx_lm.stream_generate(
                        model,
                        tokenizer,
                        prompt=rendered_prompt,
                        **params,
                    ):
                        sequence += 1
                        prompt_tokens = getattr(response, "prompt_tokens", prompt_tokens)
                        completion_tokens = int(
                            getattr(response, "generation_tokens", completion_tokens) or 0
                        )
                        finish_reason = str(
                            getattr(response, "finish_reason", finish_reason) or finish_reason
                        )
                        _emit(
                            {
                                "ok": True,
                                "action": "stream_message_event",
                                "event": "token",
                                "model_id": current_model_id,
                                "text": str(getattr(response, "text", "") or ""),
                                "pid": os.getpid(),
                                "sequence": sequence,
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "finish_reason": finish_reason,
                                "message_count": len(messages),
                            }
                        )
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "stream_message_done",
                        "event": "done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                        "sequence": sequence,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "finish_reason": finish_reason,
                        "message_count": len(messages),
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
