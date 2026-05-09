"""Experimental child runner for Gemma4 MTP via mlx-vlm CLI.

This runner speaks the same JSONL protocol as ``mlx_lm_runner`` but keeps the
MTP path behind an explicit runner-module opt-in. It shells out to
``python -m mlx_vlm generate`` per request because the current upstream MTP
programmatic surface is not stable enough to bind directly.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from owlmlx.gemma4_mtp_drafter import (
    MlxVlmToolchainInspection,
    inspect_gemma4_mtp_pair,
    inspect_mlx_vlm_toolchain,
    run_mlx_vlm_mtp_generate,
)


GenerateFunc = Callable[..., dict[str, Any]]
ToolchainInspector = Callable[..., MlxVlmToolchainInspection]


def _parse_request(line: str) -> dict[str, Any]:
    try:
        return json.loads(line or "{}")
    except Exception as exc:
        return {"_parse_error": str(exc)}


def _emit(payload: dict[str, Any]) -> None:
    sys.__stdout__.write(json.dumps(payload) + "\n")
    sys.__stdout__.flush()


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


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


def _prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for message in messages:
        role = str(message.get("role") or "user").strip() or "user"
        content = str(message.get("content") or "")
        lines.append(f"{role}: {content}")
    lines.append("assistant:")
    return "\n".join(lines)


def _int_param(params: dict[str, Any], name: str, default: int) -> int:
    try:
        return int(params.get(name, default))
    except (TypeError, ValueError):
        return default


def _float_param(params: dict[str, Any], name: str, default: float) -> float:
    try:
        return float(params.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class MlxVlmMtpChildRunner:
    env: dict[str, str] = field(default_factory=lambda: dict(os.environ))
    python_executable: str = field(default_factory=lambda: sys.executable)
    generate_func: GenerateFunc = run_mlx_vlm_mtp_generate
    toolchain_inspector: ToolchainInspector = inspect_mlx_vlm_toolchain
    current_model_id: str | None = None
    draft_model_path: str | None = None
    draft_block_size: int = 6
    generation_count: int = 0

    def handle(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        action = str(request.get("action") or "").strip().lower()
        if "_parse_error" in request:
            return [{"ok": False, "error": request["_parse_error"]}]
        if action == "load":
            return [self._load(request)]
        if action == "generate":
            return [self._generate(request, messages=None, stream=False)]
        if action == "generate_messages":
            return [self._generate(request, messages=list(request.get("messages") or []), stream=False)]
        if action == "stream_generate":
            return self._stream_generate(request, messages=None)
        if action == "stream_generate_messages":
            return self._stream_generate(request, messages=list(request.get("messages") or []))
        if action == "unload":
            unloaded_model = self.current_model_id
            self.current_model_id = None
            self.generation_count = 0
            return [
                {
                    "ok": True,
                    "action": "unload",
                    "model_id": unloaded_model,
                    "pid": os.getpid(),
                }
            ]
        if action == "ping":
            return [
                {
                    "ok": True,
                    "action": "ping",
                    "model_id": self.current_model_id,
                    "pid": os.getpid(),
                    "generation_count": self.generation_count,
                    "runtime_family": "mlx-vlm-mtp",
                    "capability_label": "experimental",
                }
            ]
        if action == "shutdown":
            return [
                {
                    "ok": True,
                    "action": "shutdown",
                    "model_id": self.current_model_id,
                    "pid": os.getpid(),
                }
            ]
        return [{"ok": False, "error": f"unsupported action: {action or '<empty>'}"}]

    def _load(self, request: dict[str, Any]) -> dict[str, Any]:
        model_id = str(request.get("model_id") or "")
        if not model_id:
            return {"ok": False, "error": "model_id is required"}
        if self.current_model_id and self.current_model_id != model_id:
            return {
                "ok": False,
                "error": f"runner already loaded a different model: {self.current_model_id}",
            }

        draft_model_path = self.env.get("OWLMLX_GEMMA4_MTP_DRAFT_MODEL", "").strip()
        if not draft_model_path:
            return {
                "ok": False,
                "error": "OWLMLX_GEMMA4_MTP_DRAFT_MODEL is required",
                "capability_label": "experimental",
            }
        if (self.env.get("OWLMLX_GEMMA4_MTP_DRAFT_KIND", "mtp").strip() or "mtp") != "mtp":
            return {
                "ok": False,
                "error": "only OWLMLX_GEMMA4_MTP_DRAFT_KIND=mtp is supported",
                "capability_label": "experimental",
            }
        pair = inspect_gemma4_mtp_pair(target_path=model_id, draft_path=draft_model_path)
        if not pair.ok:
            return {
                "ok": False,
                "error": "Gemma4 MTP target/draft pair is blocked",
                "capability_label": "experimental",
                "pair": pair.to_dict(),
            }
        toolchain = self.toolchain_inspector(python_executable=self.python_executable)
        if not toolchain.ok:
            return {
                "ok": False,
                "error": "mlx-vlm toolchain does not expose required MTP flags",
                "capability_label": "experimental",
                "toolchain": toolchain.to_dict(),
            }

        self.current_model_id = model_id
        self.draft_model_path = draft_model_path
        self.draft_block_size = _int_param(
            {"draft_block_size": self.env.get("OWLMLX_GEMMA4_MTP_DRAFT_BLOCK_SIZE", "6")},
            "draft_block_size",
            6,
        )
        self.generation_count = 0
        return {
            "ok": True,
            "action": "load",
            "model_id": self.current_model_id,
            "pid": os.getpid(),
            "runtime_family": "mlx-vlm-mtp",
            "capability_label": "experimental",
            "load_mode": "deferred_cli_per_request",
            "draft_model_path": self.draft_model_path,
            "draft_block_size": self.draft_block_size,
            "pair": pair.to_dict(),
            "toolchain": toolchain.to_dict(),
        }

    def _generate(
        self,
        request: dict[str, Any],
        *,
        messages: list[dict[str, Any]] | None,
        stream: bool,
    ) -> dict[str, Any]:
        if not self.current_model_id or not self.draft_model_path:
            return {"ok": False, "error": "no model loaded"}
        requested_model = request.get("model_id")
        if requested_model and str(requested_model) != self.current_model_id:
            return {
                "ok": False,
                "error": f"loaded model is {self.current_model_id}, not {requested_model}",
            }

        params = dict(request.get("params") or {})
        prompt = _prompt_from_messages(messages) if messages is not None else str(request.get("prompt", ""))
        stop_strings = _stop_strings_from_params(params)
        start = time.perf_counter()
        result = self.generate_func(
            python_executable=self.python_executable,
            target_path=self.current_model_id,
            draft_path=self.draft_model_path,
            prompt=prompt,
            max_tokens=_int_param(params, "max_tokens", 64),
            temperature=_float_param(params, "temperature", 0.0),
            draft_block_size=self.draft_block_size,
            timeout_s=_float_param(
                {"timeout_s": self.env.get("OWLMLX_GEMMA4_MTP_TIMEOUT_S", "900")},
                "timeout_s",
                900.0,
            ),
        )
        parsed = dict(result.get("parsed") or {})
        text, stop_hit = _truncate_at_stop_strings(
            str(parsed.get("generated_text") or ""),
            stop_strings,
        )
        self.generation_count += 1
        return {
            "ok": bool(result.get("ok")),
            "action": "stream_message_event" if stream and messages is not None else request.get("action"),
            "event": "token" if stream else None,
            "model_id": self.current_model_id,
            "text": text,
            "finish_reason": "stop",
            "pid": os.getpid(),
            "generation_count": self.generation_count,
            "message_count": len(messages) if messages is not None else None,
            "capability_label": "experimental",
            "runtime_family": "mlx-vlm-mtp",
            "stop_hit": stop_hit,
            "speculative_summary": parsed.get("speculative_summary"),
            "loaded_drafter": parsed.get("loaded_drafter"),
            "returncode": result.get("returncode"),
            "timing": {
                "surface": "owlmlx.child_stream_timing",
                "version": "v1",
                "first_response_ms": _elapsed_ms(start),
                "first_visible_token_ms": _elapsed_ms(start) if text else None,
                "stream_wall_ms": _elapsed_ms(start),
                "wrapper_elapsed_ms": result.get("elapsed_ms"),
                "streaming_mode": "single_event_after_cli_completion",
            },
            "stderr_excerpt": str(result.get("stderr") or "")[-2000:],
        }

    def _stream_generate(
        self,
        request: dict[str, Any],
        *,
        messages: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        event = self._generate(request, messages=messages, stream=True)
        if not event.get("ok"):
            return [event]
        action_done = "stream_message_done" if messages is not None else "stream_done"
        sequence = 1 if event.get("text") else 0
        terminal_common = {
            "ok": True,
            "model_id": self.current_model_id,
            "pid": os.getpid(),
            "sequence": sequence,
            "message_count": len(messages) if messages is not None else None,
            "capability_label": "experimental",
            "runtime_family": "mlx-vlm-mtp",
        }
        done = {
            **terminal_common,
            "action": action_done,
            "event": "done",
            "generation_count": self.generation_count,
            "finish_reason": "stop",
            "completion_tokens": sequence,
            "timing": event.get("timing"),
            "speculative_summary": event.get("speculative_summary"),
        }
        return [
            {**event, "sequence": sequence},
            {
                **terminal_common,
                "runtime_owned_terminal_boundary": True,
                "action": "stream_runtime_owned_terminal_boundary",
                "terminal_action": action_done,
            },
            {
                **terminal_common,
                "terminal_notice": True,
                "action": "stream_terminal_notice",
                "terminal_action": action_done,
            },
            done,
        ]


def main() -> int:
    runner = MlxVlmMtpChildRunner()
    for line in sys.stdin:
        request = _parse_request(line.strip())
        try:
            payloads = runner.handle(request)
        except Exception as exc:
            payloads = [{"ok": False, "error": f"{type(exc).__name__}: {exc}"}]
        for payload in payloads:
            _emit({key: value for key, value in payload.items() if value is not None})
        if any(payload.get("action") == "shutdown" and payload.get("ok") for payload in payloads):
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
