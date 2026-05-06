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


_SAMPLER_PARAM_NAMES = (
    "temp",
    "top_p",
    "min_p",
    "min_tokens_to_keep",
    "top_k",
    "xtc_probability",
    "xtc_threshold",
    "xtc_special_tokens",
)


def _stop_strings_from_params(params: dict[str, Any]) -> tuple[str, ...]:
    raw_stop = params.get("stop")
    if raw_stop is None:
        return ()
    if isinstance(raw_stop, str):
        candidates = (raw_stop,)
    elif isinstance(raw_stop, list):
        candidates = tuple(item for item in raw_stop if isinstance(item, str))
    else:
        return ()
    return tuple(dict.fromkeys(item for item in candidates if item))


def _truncate_at_stop_strings(
    text: str,
    stop_strings: tuple[str, ...],
) -> tuple[str, bool]:
    if not stop_strings:
        return text, False
    earliest: int | None = None
    for marker in stop_strings:
        index = text.find(marker)
        if index >= 0:
            earliest = index if earliest is None else min(earliest, index)
    if earliest is None:
        return text, False
    return text[:earliest], True


class _StopStringStreamFilter:
    def __init__(self, stop_strings: tuple[str, ...]) -> None:
        self.stop_strings = stop_strings
        self.max_marker_len = max((len(marker) for marker in stop_strings), default=0)
        self.buffer = ""
        self.stopped = False

    def feed(self, text: str) -> tuple[str, bool]:
        if self.stopped or not text:
            return "", self.stopped
        if not self.stop_strings:
            return text, False

        self.buffer += text
        truncated, found = _truncate_at_stop_strings(self.buffer, self.stop_strings)
        if found:
            self.stopped = True
            self.buffer = ""
            return truncated, True

        retain = max(self.max_marker_len - 1, 0)
        if retain == 0 or len(self.buffer) <= retain:
            return "", False
        emit = self.buffer[:-retain]
        self.buffer = self.buffer[-retain:]
        return emit, False

    def flush(self) -> str:
        if self.stopped or not self.buffer:
            return ""
        text = self.buffer
        self.buffer = ""
        return text


def _prepare_generation_params(params: dict[str, Any]) -> dict[str, Any]:
    """Adapt API-facing sampling params to the installed ``mlx_lm`` API.

    Current ``mlx_lm.generate`` forwards unknown keyword arguments to
    ``generate_step``. OpenAI-compatible callers send ``temperature`` and
    ``top_p``, while this mlx-lm version expects those to be wrapped in a
    sampler callable.
    """

    prepared = dict(params)
    prepared.pop("stop", None)
    sampler_kwargs: dict[str, Any] = {}

    if "temperature" in prepared:
        sampler_kwargs["temp"] = prepared.pop("temperature")
    if "temp" in prepared:
        sampler_kwargs["temp"] = prepared.pop("temp")

    for name in _SAMPLER_PARAM_NAMES:
        if name in prepared:
            sampler_kwargs[name] = prepared.pop(name)

    if sampler_kwargs:
        from mlx_lm.sample_utils import make_sampler  # noqa: PLC0415

        prepared["sampler"] = make_sampler(**sampler_kwargs)

    return prepared


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

                stop_strings = _stop_strings_from_params(params)
                with redirect_stdout(sys.stderr):
                    text = mlx_lm.generate(
                        model,
                        tokenizer,
                        prompt=str(prompt),
                        **_prepare_generation_params(params),
                    )
                text, stop_hit = _truncate_at_stop_strings(str(text), stop_strings)
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate",
                        "model_id": current_model_id,
                        "text": text,
                        "finish_reason": "stop" if stop_hit else "stop",
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                    }
                )
                continue

            if action == "generate_batch":
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

                requests = list(request.get("requests") or [])
                results: list[dict[str, Any]] = []
                with redirect_stdout(sys.stderr):
                    for item in requests:
                        payload = item if isinstance(item, dict) else {}
                        payload_params = dict(payload.get("params") or {})
                        stop_strings = _stop_strings_from_params(payload_params)
                        text = mlx_lm.generate(
                            model,
                            tokenizer,
                            prompt=str(payload.get("prompt", "")),
                            **_prepare_generation_params(
                                payload_params
                            ),
                        )
                        text, stop_hit = _truncate_at_stop_strings(
                            str(text),
                            stop_strings,
                        )
                        results.append(
                            {
                                "ok": True,
                                "text": text,
                                "finish_reason": "stop" if stop_hit else "stop",
                            }
                        )
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate_batch",
                        "model_id": current_model_id,
                        "results": results,
                        "batch_size": len(results),
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
                stop_strings = _stop_strings_from_params(params)
                with redirect_stdout(sys.stderr):
                    text = mlx_lm.generate(
                        model,
                        tokenizer,
                        prompt=rendered_prompt,
                        **_prepare_generation_params(params),
                    )
                text, stop_hit = _truncate_at_stop_strings(str(text), stop_strings)
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate_messages",
                        "model_id": current_model_id,
                        "text": text,
                        "finish_reason": "stop" if stop_hit else "stop",
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
                stop_strings = _stop_strings_from_params(params)
                stop_filter = _StopStringStreamFilter(stop_strings)
                with redirect_stdout(sys.stderr):
                    for response in mlx_lm.stream_generate(
                        model,
                        tokenizer,
                        prompt=str(prompt),
                        **_prepare_generation_params(params),
                    ):
                        prompt_tokens = getattr(response, "prompt_tokens", prompt_tokens)
                        completion_tokens = int(
                            getattr(response, "generation_tokens", completion_tokens) or 0
                        )
                        finish_reason = str(
                            getattr(response, "finish_reason", finish_reason) or finish_reason
                        )
                        text, stop_hit = stop_filter.feed(
                            str(getattr(response, "text", "") or "")
                        )
                        if stop_hit:
                            finish_reason = "stop"
                        if not text and not stop_hit:
                            continue
                        if text:
                            sequence += 1
                            _emit(
                                {
                                    "ok": True,
                                    "action": "stream_event",
                                    "event": "token",
                                    "model_id": current_model_id,
                                    "text": text,
                                    "pid": os.getpid(),
                                    "sequence": sequence,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "finish_reason": finish_reason,
                                }
                            )
                        if stop_hit:
                            break
                    tail = stop_filter.flush()
                    if tail:
                        sequence += 1
                        _emit(
                            {
                                "ok": True,
                                "action": "stream_event",
                                "event": "token",
                                "model_id": current_model_id,
                                "text": tail,
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
                        "runtime_owned_terminal_boundary": True,
                        "action": "stream_runtime_owned_terminal_boundary",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_leading_discriminator": True,
                        "action": "stream_runtime_owned_terminal_leading_discriminator",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_notice_discriminator": True,
                        "action": "stream_runtime_owned_terminal_notice_discriminator",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice_lead": True,
                        "action": "stream_terminal_notice_lead",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice": True,
                        "action": "stream_terminal_notice",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
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
                stop_strings = _stop_strings_from_params(params)
                stop_filter = _StopStringStreamFilter(stop_strings)
                with redirect_stdout(sys.stderr):
                    for response in mlx_lm.stream_generate(
                        model,
                        tokenizer,
                        prompt=rendered_prompt,
                        **_prepare_generation_params(params),
                    ):
                        prompt_tokens = getattr(response, "prompt_tokens", prompt_tokens)
                        completion_tokens = int(
                            getattr(response, "generation_tokens", completion_tokens) or 0
                        )
                        finish_reason = str(
                            getattr(response, "finish_reason", finish_reason) or finish_reason
                        )
                        text, stop_hit = stop_filter.feed(
                            str(getattr(response, "text", "") or "")
                        )
                        if stop_hit:
                            finish_reason = "stop"
                        if not text and not stop_hit:
                            continue
                        if text:
                            sequence += 1
                            _emit(
                                {
                                    "ok": True,
                                    "action": "stream_message_event",
                                    "event": "token",
                                    "model_id": current_model_id,
                                    "text": text,
                                    "pid": os.getpid(),
                                    "sequence": sequence,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "finish_reason": finish_reason,
                                    "message_count": len(messages),
                                }
                            )
                        if stop_hit:
                            break
                    tail = stop_filter.flush()
                    if tail:
                        sequence += 1
                        _emit(
                            {
                                "ok": True,
                                "action": "stream_message_event",
                                "event": "token",
                                "model_id": current_model_id,
                                "text": tail,
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
                        "runtime_owned_terminal_boundary": True,
                        "action": "stream_runtime_owned_terminal_boundary",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_leading_discriminator": True,
                        "action": "stream_runtime_owned_terminal_leading_discriminator",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_notice_discriminator": True,
                        "action": "stream_runtime_owned_terminal_notice_discriminator",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice_lead": True,
                        "action": "stream_terminal_notice_lead",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice": True,
                        "action": "stream_terminal_notice",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
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
