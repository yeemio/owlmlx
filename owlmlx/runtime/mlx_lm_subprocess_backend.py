"""Subprocess-isolated persistent mlx-lm backend.

This backend keeps the owlmlx parent process safe by never importing mlx-lm
in-process. Each loaded model owns a persistent child runner process. The
child performs ``mlx_lm.load`` once, serves multiple ``generate`` commands,
then exits on explicit ``unload`` or forced termination.
"""

from __future__ import annotations

import json
import os
import queue
import select
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .types import (
    BackendStatus,
    ChatTurn,
    GenerateCohortResult,
    GenerateResult,
    LoadResult,
    LoadedModelInfo,
    RuntimeErrorCode,
    StreamEvent,
    UnloadResult,
)


@dataclass(frozen=True, slots=True)
class MlxLmSubprocessResult:
    """Raw child-process execution result."""

    ok: bool
    returncode: int
    stdout: str
    stderr: str
    payload: dict[str, Any]


@dataclass(slots=True)
class _ChildSession:
    """Persistent child process bound to one loaded model."""

    proc: subprocess.Popen[str]
    model: LoadedModelInfo
    stderr_lines: deque[str] = field(default_factory=lambda: deque(maxlen=200))
    generation_count: int = 0
    aggregated_dispatch_count: int = 0
    aggregated_dispatch_request_count: int = 0
    max_aggregated_dispatch_batch_size: int = 0
    last_payload: dict[str, Any] | None = None
    last_error: str | None = None
    stderr_thread: threading.Thread | None = None
    stream_stdout_lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def pid(self) -> int | None:
        return self.proc.pid


@dataclass(frozen=True, slots=True)
class _ModelTypeSupportProbe:
    """Child-runtime probe for whether mlx-lm exposes a model_type module."""

    model_path: str
    model_type: str
    supported: bool
    module_name: str
    returncode: int
    stdout: str = ""
    stderr: str = ""


def _drain_stderr(pipe: Any, buffer: deque[str]) -> None:
    """Continuously drain child stderr so the pipe never blocks."""

    if pipe is None:
        return
    try:
        for line in pipe:
            text = line.rstrip()
            if text:
                buffer.append(text)
    except Exception:
        return


def _stream_payload_detail(
    payload: dict[str, Any],
    *,
    include_message_count: bool = False,
    include_generation_count: bool = False,
) -> dict[str, Any]:
    detail: dict[str, Any] = {"pid": payload.get("pid")}
    if include_generation_count:
        detail["generation_count"] = payload.get("generation_count")
    if include_message_count:
        detail["message_count"] = payload.get("message_count")
    timing = payload.get("timing")
    if isinstance(timing, dict):
        detail["timing"] = timing
    return detail


def _classify_failure_text(text: str) -> str | None:
    lowered = text.lower()
    if (
        "[metal]" in lowered
        and (
            "insufficient memory" in lowered
            or "outofmemory" in lowered
            or "out of memory" in lowered
        )
    ):
        return "metal_oom"
    if "broken pipe" in lowered:
        return "broken_pipe_child_lost"
    if "child process produced no output" in lowered:
        return "child_lost_no_output"
    if "child process exited unexpectedly" in lowered:
        return "child_lost"
    return None


def _classify_last_subprocess_failure(
    *,
    last_error: str | None,
    last_result: MlxLmSubprocessResult | None,
) -> str | None:
    parts: list[str] = []
    if last_error:
        parts.append(last_error)
    if last_result is not None:
        parts.extend(
            [
                last_result.stderr,
                last_result.stdout,
                json.dumps(last_result.payload, sort_keys=True),
            ]
        )
    for part in parts:
        if _classify_failure_text(part) == "metal_oom":
            return "metal_oom"
    for part in parts:
        classified = _classify_failure_text(part)
        if classified is not None:
            return classified
    if last_error:
        return "backend_error"
    if last_result is not None and not last_result.ok:
        return "backend_error"
    return None


def _read_model_type_from_config(model_path: str) -> str | None:
    """Return a local Hugging Face/MLX config model_type, if cheaply readable."""

    path = Path(model_path).expanduser()
    config_path = path / "config.json" if path.is_dir() else None
    if config_path is None or not config_path.is_file():
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


_STREAM_TERMINAL_RECORD_PREFIXES = (
    '{"ok": true, "action": "stream_done"',
    '{"ok":true,"action":"stream_done"',
    '{"ok": true, "action": "stream_message_done"',
    '{"ok":true,"action":"stream_message_done"',
    '{"ok": false',
    '{"ok":false',
)

_STREAM_TRANSPORT_DIAGNOSTIC_LIMIT = 32
_STREAM_TRANSPORT_DIAGNOSTIC_PREVIEW_CHARS = 1000


def _stream_transport_preview(text: str) -> str:
    """Return a bounded diagnostic preview for malformed child stdout."""

    if len(text) <= _STREAM_TRANSPORT_DIAGNOSTIC_PREVIEW_CHARS:
        return text
    return text[:_STREAM_TRANSPORT_DIAGNOSTIC_PREVIEW_CHARS] + "...<truncated>"


def _recover_embedded_terminal_stream_payload(text: str) -> dict[str, Any] | None:
    """Recover a complete terminal payload after a malformed JSON prefix."""

    decoder = json.JSONDecoder()
    for prefix in _STREAM_TERMINAL_RECORD_PREFIXES:
        start = text.find(prefix, 1)
        if start < 0:
            continue
        try:
            payload, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if text[start + end :].strip():
            continue
        if isinstance(payload, dict) and (
            payload.get("event") == "done" or not payload.get("ok")
        ):
            return payload
    return None


def _classify_non_json_stream_transport_line(text: str) -> str:
    """Classify malformed child stdout without silently masking transport corruption."""

    stripped = text.lstrip()
    if (
        stripped.startswith("{")
        or stripped.startswith("[")
        or '"action":' in stripped
        or "stream_done" in stripped
        or "stream_message_done" in stripped
        or "runtime_owned_terminal" in stripped
        or "terminal_notice" in stripped
    ):
        return "corrupt_json_transport_record"
    return "benign_child_stdout_noise"


_STREAM_TERMINAL_RECORD_ACTION_DISCRIMINANTS = (
    '{"ok": true, "action": "stream_d',
    '{"ok":true,"action":"stream_d',
    '{"ok": true, "action": "stream_message_d',
    '{"ok":true,"action":"stream_message_d',
    '{"ok": false',
    '{"ok":false',
)

_STREAM_TERMINAL_NOTICE_PREFIXES = (
    '{"ok": true, "action": "stream_terminal_notice"',
    '{"ok":true,"action":"stream_terminal_notice"',
    '{"ok": true, "terminal_notice": true, "action": "stream_terminal_notice"',
    '{"ok":true,"terminal_notice":true,"action":"stream_terminal_notice"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_EARLIER_BOUNDARIES = (
    '{"ok": true, "runtime_owned_terminal_earlier_earlier_boundary": true, "action": "stream_runtime_owned_terminal_earlier_earlier_boundary"',
    '{"ok":true,"runtime_owned_terminal_earlier_earlier_boundary":true,"action":"stream_runtime_owned_terminal_earlier_earlier_boundary"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_EARLIER_BOUNDARY_STEMS = (
    '{"ok": true, "runtime_owned_terminal_earlier_e',
    '{"ok":true,"runtime_owned_terminal_earlier_e',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_BOUNDARIES = (
    '{"ok": true, "runtime_owned_terminal_earlier_boundary": true, "action": "stream_runtime_owned_terminal_earlier_boundary"',
    '{"ok":true,"runtime_owned_terminal_earlier_boundary":true,"action":"stream_runtime_owned_terminal_earlier_boundary"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_BOUNDARY_STEMS = (
    '{"ok": true, "runtime_owned_terminal_earlier_b',
    '{"ok":true,"runtime_owned_terminal_earlier_b',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_BOUNDARIES = (
    '{"ok": true, "runtime_owned_terminal_boundary": true, "action": "stream_runtime_owned_terminal_boundary"',
    '{"ok":true,"runtime_owned_terminal_boundary":true,"action":"stream_runtime_owned_terminal_boundary"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_BOUNDARY_PREFIXES = (
    '{"ok": true, "runtime_owned_terminal_boundary"',
    '{"ok":true,"runtime_owned_terminal_boundary"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_BOUNDARY_STEMS = (
    '{"ok": true, "runtime_owned_terminal_b',
    '{"ok":true,"runtime_owned_terminal_b',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATORS = (
    '{"ok": true, "runtime_owned_terminal_leading_discriminator": true, "action": "stream_runtime_owned_terminal_leading_discriminator"',
    '{"ok":true,"runtime_owned_terminal_leading_discriminator":true,"action":"stream_runtime_owned_terminal_leading_discriminator"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATOR_PREFIXES = (
    '{"ok": true, "runtime_owned_terminal_leading_discriminator"',
    '{"ok":true,"runtime_owned_terminal_leading_discriminator"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATOR_STEMS = (
    '{"ok": true, "runtime_owned_terminal_leading_d',
    '{"ok":true,"runtime_owned_terminal_leading_d',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATOR_DISCRIMINANTS = (
    '{"ok": true, "runtime_owned_terminal_leading_',
    '{"ok":true,"runtime_owned_terminal_leading_',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATORS = (
    '{"ok": true, "runtime_owned_terminal_notice_discriminator": true, "action": "stream_runtime_owned_terminal_notice_discriminator"',
    '{"ok":true,"runtime_owned_terminal_notice_discriminator":true,"action":"stream_runtime_owned_terminal_notice_discriminator"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATOR_PREFIXES = (
    '{"ok": true, "runtime_owned_terminal_notice_discriminator"',
    '{"ok":true,"runtime_owned_terminal_notice_discriminator"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATOR_STEMS = (
    '{"ok": true, "runtime_owned_terminal_notice_d',
    '{"ok":true,"runtime_owned_terminal_notice_d',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATOR_DISCRIMINANTS = (
    '{"ok": true, "runtime_owned_terminal_notice_',
    '{"ok":true,"runtime_owned_terminal_notice_',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKERS = (
    '{"ok": true, "terminal_notice_lead": true',
    '{"ok":true,"terminal_notice_lead":true',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_PREFIXES = (
    '{"ok": true, "terminal_notice_lead"',
    '{"ok":true,"terminal_notice_lead"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_STEMS = (
    '{"ok": true, "terminal_notice_l',
    '{"ok":true,"terminal_notice_l',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_DISCRIMINANTS = (
    '{"ok": true, "terminal_notice_',
    '{"ok":true,"terminal_notice_',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_PREFIXES = (
    '{"ok": true, "terminal_notice_lead": true, "action": "stream_terminal_notice_lead"',
    '{"ok":true,"terminal_notice_lead":true,"action":"stream_terminal_notice_lead"',
    '{"ok": true, "action": "stream_terminal_notice_lead"',
    '{"ok":true,"action":"stream_terminal_notice_lead"',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_PREFIX_BOUNDARIES = (
    '{"ok": true, "terminal_notice_lead": true, "action": "stream_terminal_notice_lead',
    '{"ok":true,"terminal_notice_lead":true,"action":"stream_terminal_notice_lead',
    '{"ok": true, "action": "stream_terminal_notice_lead',
    '{"ok":true,"action":"stream_terminal_notice_lead',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_STEMS = (
    '{"ok": true, "terminal_notice_lead": true, "action": "stream_terminal_notice_l',
    '{"ok":true,"terminal_notice_lead":true,"action":"stream_terminal_notice_l',
    '{"ok": true, "action": "stream_terminal_notice_l',
    '{"ok":true,"action":"stream_terminal_notice_l',
)

_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_DISCRIMINANTS = (
    '{"ok": true, "terminal_notice_lead": true, "action": "stream_terminal_notice_',
    '{"ok":true,"terminal_notice_lead":true,"action":"stream_terminal_notice_',
    '{"ok": true, "action": "stream_terminal_notice_',
    '{"ok":true,"action":"stream_terminal_notice_',
)

_STREAM_TERMINAL_NOTICE_MARKERS = (
    '{"ok": true, "terminal_notice": true',
    '{"ok":true,"terminal_notice":true',
)

_STREAM_TERMINAL_NOTICE_MARKER_PREFIXES = (
    '{"ok": true, "terminal_notice"',
    '{"ok":true,"terminal_notice"',
)

_STREAM_TERMINAL_NOTICE_MARKER_KEY_LEADS = (
    '{"ok": true, "t',
    '{"ok":true,"t',
)

_STREAM_TERMINAL_NOTICE_MARKER_DISCRIMINANTS = (
    '{"ok": true, "terminal_',
    '{"ok":true,"terminal_',
)

_STREAM_TERMINAL_NOTICE_MARKER_STEMS = (
    '{"ok": true, "terminal_n',
    '{"ok":true,"terminal_n',
)

_STREAM_TERMINAL_NOTICE_ACTION_DISCRIMINANTS = (
    '{"ok": true, "action": "stream_terminal_n',
    '{"ok":true,"action":"stream_terminal_n',
    '{"ok": true, "terminal_notice": true, "action": "stream_terminal_n',
    '{"ok":true,"terminal_notice":true,"action":"stream_terminal_n',
)

_STREAM_TERMINAL_NOTICE_ACTION_STEMS = (
    '{"ok": true, "action": "stream_t',
    '{"ok":true,"action":"stream_t',
    '{"ok": true, "terminal_notice": true, "action": "stream_t',
    '{"ok":true,"terminal_notice":true,"action":"stream_t',
)


def _is_terminal_stream_record(text: str) -> bool:
    """Return whether a stream transport record is terminal before payload decode."""

    return text.startswith(_STREAM_TERMINAL_RECORD_PREFIXES)


def _has_terminal_stream_record_action_discriminant(buffer: str) -> bool:
    """Return whether a partial buffer already proves the terminal action family."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_RECORD_ACTION_DISCRIMINANTS
    )


def _has_terminal_stream_record_prefix(buffer: str) -> bool:
    """Return whether a partial transport buffer already proves a terminal record."""

    return any(buffer.startswith(prefix) for prefix in _STREAM_TERMINAL_RECORD_PREFIXES)


def _is_terminal_notice_record(text: str) -> bool:
    """Return whether a transport record is an internal terminal notice."""

    return text.startswith(_STREAM_TERMINAL_NOTICE_PREFIXES)


def _is_terminal_notice_leading_discriminator_record(text: str) -> bool:
    """Return whether a transport record is the runtime-owned leading discriminator."""

    return text.startswith(_STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_PREFIXES)


def _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_record(
    text: str,
) -> bool:
    """Return whether a transport record is the earlier runtime-owned discriminator."""

    return text.startswith(
        _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATORS
    )


def _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_earlier_boundary_record(
    text: str,
) -> bool:
    """Return whether a transport record is the earlier runtime-owned earlier-earlier-boundary."""

    return text.startswith(
        _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_EARLIER_BOUNDARIES
    )


def _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_boundary_record(
    text: str,
) -> bool:
    """Return whether a transport record is the earlier runtime-owned earlier-boundary."""

    return text.startswith(
        _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_BOUNDARIES
    )


def _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_record(
    text: str,
) -> bool:
    """Return whether a transport record is the earlier runtime-owned boundary."""

    return text.startswith(
        _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_BOUNDARIES
    )


def _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_record(
    text: str,
) -> bool:
    """Return whether a transport record is the earlier runtime-owned leading discriminator."""

    return text.startswith(
        _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATORS
    )


def _has_terminal_notice_prefix(buffer: str) -> bool:
    """Return whether a partial buffer already proves a terminal notice record."""

    return any(buffer.startswith(prefix) for prefix in _STREAM_TERMINAL_NOTICE_PREFIXES)


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already proves the earlier runtime-owned leading discriminator."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATORS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_earlier_boundary_stem(
    buffer: str,
) -> bool:
    """Return whether a partial buffer reaches the earlier runtime-owned earlier-earlier-boundary stem."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_EARLIER_BOUNDARY_STEMS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_boundary_stem(
    buffer: str,
) -> bool:
    """Return whether a partial buffer reaches the earlier runtime-owned earlier-boundary stem."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_EARLIER_BOUNDARY_STEMS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already proves the earlier runtime-owned boundary."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_BOUNDARIES
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned boundary prefix."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_BOUNDARY_PREFIXES
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned boundary stem."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_BOUNDARY_STEMS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned leading-discriminator prefix."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATOR_PREFIXES
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned leading-discriminator stem."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATOR_STEMS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned leading-discriminator discriminant."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_LEADING_DISCRIMINATOR_DISCRIMINANTS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already proves the earlier runtime-owned discriminator."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATORS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned discriminator prefix."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATOR_PREFIXES
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned discriminator stem."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATOR_STEMS
    )


def _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the earlier runtime-owned discriminator discriminant."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_EARLIER_RUNTIME_OWNED_DISCRIMINATOR_DISCRIMINANTS
    )


def _has_terminal_notice_leading_discriminator(buffer: str) -> bool:
    """Return whether a partial buffer already proves the leading-discriminator record."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_PREFIXES
    )


def _has_terminal_notice_leading_discriminator_marker(buffer: str) -> bool:
    """Return whether a partial buffer already proves the leading-discriminator marker."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKERS
    )


def _has_terminal_notice_leading_discriminator_marker_prefix(buffer: str) -> bool:
    """Return whether a partial buffer already reaches the leading-discriminator marker prefix."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_PREFIXES
    )


def _has_terminal_notice_leading_discriminator_marker_stem(buffer: str) -> bool:
    """Return whether a partial buffer already reaches the leading-discriminator marker stem."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_STEMS
    )


def _has_terminal_notice_leading_discriminator_marker_discriminant(
    buffer: str,
) -> bool:
    """Return whether a partial buffer already reaches the leading-discriminator marker discriminant."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_MARKER_DISCRIMINANTS
    )


def _has_terminal_notice_leading_discriminator_prefix(buffer: str) -> bool:
    """Return whether a partial buffer already reaches the leading-discriminator prefix."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_PREFIX_BOUNDARIES
    )


def _has_terminal_notice_leading_discriminator_stem(buffer: str) -> bool:
    """Return whether a partial buffer already reaches the leading-discriminator stem."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_STEMS
    )


def _has_terminal_notice_leading_discriminator_discriminant(buffer: str) -> bool:
    """Return whether a partial buffer already reaches the leading-discriminator discriminant."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_LEADING_DISCRIMINATOR_DISCRIMINANTS
    )


def _has_terminal_notice_action_discriminant(buffer: str) -> bool:
    """Return whether a partial buffer already proves the terminal-notice action family."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_ACTION_DISCRIMINANTS
    )


def _has_terminal_notice_action_stem(buffer: str) -> bool:
    """Return whether a partial buffer already reaches the first unique notice-action stem."""

    return any(buffer.startswith(prefix) for prefix in _STREAM_TERMINAL_NOTICE_ACTION_STEMS)


def _has_terminal_notice_marker(buffer: str) -> bool:
    """Return whether a partial buffer already proves the explicit notice marker field."""

    return any(buffer.startswith(prefix) for prefix in _STREAM_TERMINAL_NOTICE_MARKERS)


def _has_terminal_notice_marker_prefix(buffer: str) -> bool:
    """Return whether a partial buffer already proves the terminal-notice marker key."""

    return any(
        buffer.startswith(prefix) for prefix in _STREAM_TERMINAL_NOTICE_MARKER_PREFIXES
    )


def _has_terminal_notice_marker_key_lead(buffer: str) -> bool:
    """Return whether a partial buffer already reaches the first marker-key lead."""

    return any(
        buffer.startswith(prefix) for prefix in _STREAM_TERMINAL_NOTICE_MARKER_KEY_LEADS
    )


def _has_terminal_notice_marker_discriminant(buffer: str) -> bool:
    """Return whether a partial buffer already proves the marker-key family lead-in."""

    return any(
        buffer.startswith(prefix)
        for prefix in _STREAM_TERMINAL_NOTICE_MARKER_DISCRIMINANTS
    )


def _has_terminal_notice_marker_stem(buffer: str) -> bool:
    """Return whether a partial buffer already proves the terminal-notice marker family."""

    return any(buffer.startswith(prefix) for prefix in _STREAM_TERMINAL_NOTICE_MARKER_STEMS)


class MlxLmSubprocessBackend:
    """RuntimeBackend that isolates mlx-lm execution in persistent child processes."""

    name = "mlx-lm-subprocess"

    def __init__(
        self,
        *,
        python_executable: str | None = None,
        env_overrides: dict[str, str] | None = None,
        runner_module: str = "owlmlx.runtime.mlx_lm_runner",
        model_path_resolver: Callable[[str], str] | None = None,
        timeout_s: float = 600.0,
        health_probe_timeout_s: float = 2.0,
        auto_restart_dead_session: bool = True,
        max_restart_attempts: int = 1,
        extra_pythonpath: tuple[str, ...] = (),
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.env_overrides = dict(env_overrides or {})
        self.runner_module = runner_module
        self.model_path_resolver = model_path_resolver
        self.timeout_s = timeout_s
        self.health_probe_timeout_s = health_probe_timeout_s
        self.auto_restart_dead_session = auto_restart_dead_session
        self.max_restart_attempts = max_restart_attempts
        self.extra_pythonpath = extra_pythonpath
        self._registrations: dict[str, LoadedModelInfo] = {}
        self._sessions: dict[str, _ChildSession] = {}
        self._restart_counts: dict[str, int] = {}
        self._last_error: str | None = None
        self._last_result: MlxLmSubprocessResult | None = None
        self._io_lock = threading.Lock()
        self._stream_transport_non_json_lines: deque[str] = deque(
            maxlen=_STREAM_TRANSPORT_DIAGNOSTIC_LIMIT
        )
        self._stream_transport_non_json_diagnostics: deque[dict[str, Any]] = deque(
            maxlen=_STREAM_TRANSPORT_DIAGNOSTIC_LIMIT
        )
        self._stream_debug_after_request_write: (
            Callable[[dict[str, Any]], None] | None
        ) = None
        self._stream_debug_before_terminal_action_discriminant: (
            Callable[[dict[str, Any]], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_discriminant_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_stem_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_marker_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_discriminant_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_stem_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_leading_discriminator_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_marker_key_lead_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_marker_discriminant_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_marker_stem_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_marker_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_marker_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_action_stem: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_action_discriminant: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_notice_capture: (
            Callable[[dict[str, Any]], None] | None
        ) = None
        self._stream_debug_before_terminal_record_prefix_detection: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_record_capture: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_payload_capture: (
            Callable[[str], None] | None
        ) = None
        self._stream_debug_before_terminal_payload_commit: (
            Callable[[dict[str, Any]], None] | None
        ) = None

    def _runner_model_id(self, model_id: str) -> str:
        """Return the model identifier sent to the child runner.

        The public runtime API keeps stable logical model ids, while the
        technical-preview launcher may need to resolve those ids to local
        filesystem paths for ``mlx_lm.load``.
        """

        if self.model_path_resolver is None:
            return model_id
        return str(self.model_path_resolver(model_id))

    def _probe_model_type_support(
        self,
        *,
        runner_model_id: str,
        model_type: str,
    ) -> _ModelTypeSupportProbe | None:
        """Probe model-family support in the child runtime without importing it here."""

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
                [self.python_executable, "-c", code, module_name],
                cwd=None,
                env=self._build_env(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=min(max(float(self.health_probe_timeout_s), 1.0), 10.0),
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        supported = False
        try:
            payload = json.loads(completed.stdout.strip() or "{}")
            supported = bool(payload.get("supported"))
        except json.JSONDecodeError:
            return None
        if completed.returncode != 0 or payload.get("probe_error"):
            return None
        return _ModelTypeSupportProbe(
            model_path=runner_model_id,
            model_type=model_type,
            supported=supported,
            module_name=module_name,
            returncode=int(completed.returncode),
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def _read_stream_transport_line(
        self,
        stdout: Any,
        *,
        release_serial_boundary: Callable[[], None] | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_discriminant_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_stem_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_prefix_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_marker_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_discriminant_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_stem_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_prefix_detection: Callable[
            [str], None
        ]
        | None = None,
        before_terminal_notice_leading_discriminator_detection: Callable[[str], None]
        | None = None,
        before_terminal_notice_marker_key_lead_detection: Callable[[str], None] | None = None,
        before_terminal_notice_marker_discriminant_detection: Callable[[str], None] | None = None,
        before_terminal_notice_marker_stem_detection: Callable[[str], None] | None = None,
        before_terminal_notice_marker_prefix_detection: Callable[[str], None] | None = None,
        before_terminal_notice_marker_detection: Callable[[str], None] | None = None,
        before_terminal_notice_action_stem: Callable[[str], None] | None = None,
        before_terminal_notice_action_discriminant: Callable[[str], None] | None = None,
        before_terminal_notice_prefix_detection: Callable[[str], None] | None = None,
        before_terminal_record_prefix_detection: Callable[[str], None] | None = None,
        before_terminal_record_capture: Callable[[str], None] | None = None,
    ) -> tuple[str, bool]:
        """Read one stream transport line and optionally release the serial boundary early."""

        raw_chars: list[str] = []
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected = False
        terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected = False
        terminal_notice_leading_discriminator_marker_discriminant_detected = False
        terminal_notice_leading_discriminator_marker_stem_detected = False
        terminal_notice_leading_discriminator_marker_prefix_detected = False
        terminal_notice_leading_discriminator_marker_detected = False
        terminal_notice_leading_discriminator_discriminant_detected = False
        terminal_notice_leading_discriminator_stem_detected = False
        terminal_notice_leading_discriminator_prefix_detected = False
        terminal_notice_leading_discriminator_detected = False
        terminal_notice_marker_key_lead_detected = False
        terminal_action_discriminant_detected = False
        terminal_notice_marker_discriminant_detected = False
        terminal_notice_marker_stem_detected = False
        terminal_notice_marker_prefix_detected = False
        terminal_notice_marker_detected = False
        terminal_notice_action_stem_detected = False
        terminal_notice_action_discriminant_detected = False
        terminal_notice_prefix_detected = False
        terminal_prefix_detected = False
        while True:
            ch = stdout.read(1)
            if not ch:
                raise ValueError("child process produced no output")
            if ch == "\n":
                return "".join(raw_chars).strip(), terminal_prefix_detected
            raw_chars.append(ch)
            if terminal_prefix_detected:
                continue
            buffer = "".join(raw_chars)
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_earlier_boundary_stem(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_boundary_stem(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection = None
            if not terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected and (
                _has_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator(
                    buffer
                )
            ):
                terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection = None
            if not terminal_notice_leading_discriminator_marker_discriminant_detected and (
                _has_terminal_notice_leading_discriminator_marker_discriminant(buffer)
            ):
                terminal_notice_leading_discriminator_marker_discriminant_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_discriminant_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_discriminant_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_discriminant_detection = None
            if not terminal_notice_leading_discriminator_marker_stem_detected and (
                _has_terminal_notice_leading_discriminator_marker_stem(buffer)
            ):
                terminal_notice_leading_discriminator_marker_stem_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_stem_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_stem_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_stem_detection = None
            if not terminal_notice_leading_discriminator_marker_prefix_detected and (
                _has_terminal_notice_leading_discriminator_marker_prefix(buffer)
            ):
                terminal_notice_leading_discriminator_marker_prefix_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_marker_prefix_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_marker_prefix_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_prefix_detection = None
            if not terminal_notice_leading_discriminator_marker_detected and (
                _has_terminal_notice_leading_discriminator_marker(buffer)
            ):
                terminal_notice_leading_discriminator_marker_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_leading_discriminator_marker_detection is not None:
                    before_terminal_notice_leading_discriminator_marker_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_marker_detection = None
            if not terminal_notice_leading_discriminator_discriminant_detected and (
                _has_terminal_notice_leading_discriminator_discriminant(buffer)
            ):
                terminal_notice_leading_discriminator_discriminant_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_discriminant_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_discriminant_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_discriminant_detection = None
            if not terminal_notice_leading_discriminator_stem_detected and (
                _has_terminal_notice_leading_discriminator_stem(buffer)
            ):
                terminal_notice_leading_discriminator_stem_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_leading_discriminator_stem_detection is not None:
                    before_terminal_notice_leading_discriminator_stem_detection(buffer)
                    before_terminal_notice_leading_discriminator_stem_detection = None
            if not terminal_notice_leading_discriminator_prefix_detected and (
                _has_terminal_notice_leading_discriminator_prefix(buffer)
            ):
                terminal_notice_leading_discriminator_prefix_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if (
                    before_terminal_notice_leading_discriminator_prefix_detection
                    is not None
                ):
                    before_terminal_notice_leading_discriminator_prefix_detection(
                        buffer
                    )
                    before_terminal_notice_leading_discriminator_prefix_detection = None
            if not terminal_notice_leading_discriminator_detected and (
                _has_terminal_notice_leading_discriminator(buffer)
            ):
                terminal_notice_leading_discriminator_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_leading_discriminator_detection is not None:
                    before_terminal_notice_leading_discriminator_detection(buffer)
                    before_terminal_notice_leading_discriminator_detection = None
            if not terminal_notice_marker_key_lead_detected and (
                _has_terminal_notice_marker_key_lead(buffer)
            ):
                terminal_notice_marker_key_lead_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_marker_key_lead_detection is not None:
                    before_terminal_notice_marker_key_lead_detection(buffer)
                    before_terminal_notice_marker_key_lead_detection = None
            if not terminal_notice_marker_discriminant_detected and (
                _has_terminal_notice_marker_discriminant(buffer)
            ):
                terminal_notice_marker_discriminant_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_marker_discriminant_detection is not None:
                    before_terminal_notice_marker_discriminant_detection(buffer)
                    before_terminal_notice_marker_discriminant_detection = None
            if not terminal_notice_marker_stem_detected and _has_terminal_notice_marker_stem(
                buffer
            ):
                terminal_notice_marker_stem_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_marker_stem_detection is not None:
                    before_terminal_notice_marker_stem_detection(buffer)
                    before_terminal_notice_marker_stem_detection = None
            if not terminal_notice_marker_prefix_detected and _has_terminal_notice_marker_prefix(
                buffer
            ):
                terminal_notice_marker_prefix_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_marker_prefix_detection is not None:
                    before_terminal_notice_marker_prefix_detection(buffer)
                    before_terminal_notice_marker_prefix_detection = None
            if not terminal_notice_marker_detected and _has_terminal_notice_marker(buffer):
                terminal_notice_marker_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_marker_detection is not None:
                    before_terminal_notice_marker_detection(buffer)
                    before_terminal_notice_marker_detection = None
            if not terminal_notice_action_stem_detected and _has_terminal_notice_action_stem(
                buffer
            ):
                terminal_notice_action_stem_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_action_stem is not None:
                    before_terminal_notice_action_stem(buffer)
                    before_terminal_notice_action_stem = None
            if not terminal_notice_action_discriminant_detected and (
                _has_terminal_notice_action_discriminant(buffer)
            ):
                terminal_notice_action_discriminant_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_action_discriminant is not None:
                    before_terminal_notice_action_discriminant(buffer)
                    before_terminal_notice_action_discriminant = None
            if not terminal_notice_prefix_detected and _has_terminal_notice_prefix(buffer):
                terminal_notice_prefix_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_notice_prefix_detection is not None:
                    before_terminal_notice_prefix_detection(buffer)
                    before_terminal_notice_prefix_detection = None
            if not terminal_action_discriminant_detected and (
                _has_terminal_stream_record_action_discriminant(buffer)
            ):
                terminal_action_discriminant_detected = True
                if release_serial_boundary is not None:
                    release_serial_boundary()
                    release_serial_boundary = None
                if before_terminal_record_prefix_detection is not None:
                    before_terminal_record_prefix_detection(buffer)
                    before_terminal_record_prefix_detection = None
            if _has_terminal_stream_record_prefix(buffer):
                terminal_prefix_detected = True
                if before_terminal_record_capture is not None:
                    before_terminal_record_capture(buffer)
                    before_terminal_record_capture = None

    def load(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        if model_id in self._registrations:
            return LoadResult(
                ok=False,
                message=f"model already loaded: {model_id}",
                error_code=RuntimeErrorCode.model_already_loaded,
                model=self._registrations[model_id],
            )
        runner_model_id = self._runner_model_id(model_id)
        model_type = _read_model_type_from_config(runner_model_id)
        support_probe = (
            self._probe_model_type_support(
                runner_model_id=runner_model_id,
                model_type=model_type,
            )
            if model_type
            else None
        )
        if support_probe is not None and not support_probe.supported:
            return LoadResult(
                ok=False,
                message=(
                    "unsupported model family: "
                    f"model_type={model_type} has no {support_probe.module_name} "
                    "loader in the configured mlx-lm runtime"
                ),
                error_code=RuntimeErrorCode.unsupported_model_family,
                detail={
                    "preflight": {
                        "stage": "model_type_loader_support",
                        "model_path": support_probe.model_path,
                        "model_type": support_probe.model_type,
                        "module_name": support_probe.module_name,
                        "supported": support_probe.supported,
                        "returncode": support_probe.returncode,
                        "stderr": support_probe.stderr[-2000:],
                    },
                    "does_not_start_child": True,
                    "does_not_dirty_backend_health": True,
                },
            )
        info = LoadedModelInfo(
            model_id=model_id,
            memory_gb=memory_gb if memory_gb is not None else 0.0,
            backend=self.name,
            loaded_at=time.time(),
        )
        session = self._start_session(info)
        load_started = time.monotonic()
        result = self._exchange(
            session,
            {
                "action": "load",
                "model_id": runner_model_id,
            },
        )
        self._last_result = result
        if not result.ok:
            self._last_error = str(result.payload.get("error") or result.stderr or result.returncode)
            self._terminate_session(session)
            return LoadResult(
                ok=False,
                message=f"mlx-lm subprocess load failed: {self._last_error}",
                error_code=RuntimeErrorCode.backend_error,
                detail={
                    "pid": session.pid,
                    "load_time_s": round(time.monotonic() - load_started, 4),
                    "returncode": result.returncode,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                    "payload": result.payload,
                },
            )

        session.last_payload = result.payload
        self._registrations[model_id] = info
        self._sessions[model_id] = session
        self._restart_counts[model_id] = 0
        self._last_error = None
        return LoadResult(
            ok=True,
            message=f"loaded {model_id} in persistent child pid={session.pid}",
            detail={
                "pid": session.pid,
                "load_time_s": round(time.monotonic() - load_started, 4),
                "runner_model_id": result.payload.get("model_id"),
            },
            model=info,
        )

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(self.env_overrides)
        if self.extra_pythonpath:
            existing = env.get("PYTHONPATH")
            env["PYTHONPATH"] = os.pathsep.join(
                [*self.extra_pythonpath, *([existing] if existing else [])]
            )
        return env

    def _start_session(self, model: LoadedModelInfo) -> _ChildSession:
        proc = subprocess.Popen(
            [self.python_executable, "-m", self.runner_module],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self._build_env(),
        )
        session = _ChildSession(proc=proc, model=model)
        if proc.stderr is not None:
            session.stderr_thread = threading.Thread(
                target=_drain_stderr,
                args=(proc.stderr, session.stderr_lines),
                daemon=True,
            )
            session.stderr_thread.start()
        return session

    def _collect_stderr(self, session: _ChildSession) -> str:
        return "\n".join(session.stderr_lines)

    def _read_payload_line(
        self,
        session: _ChildSession,
        *,
        timeout_s: float | None = None,
    ) -> tuple[dict[str, Any], str]:
        proc = session.proc
        stdout = proc.stdout
        if stdout is None:
            raise ValueError("child stdout pipe is unavailable")
        deadline = time.monotonic() + (timeout_s if timeout_s is not None else self.timeout_s)
        discarded: list[str] = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timed out waiting for child response")
            ready, _, _ = select.select([stdout], [], [], remaining)
            if not ready:
                raise TimeoutError("timed out waiting for child response")
            line = stdout.readline()
            if not line:
                raise ValueError("child process produced no output")
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
                if isinstance(payload, dict):
                    return payload, "\n".join(discarded)
            except Exception:
                discarded.append(text)

    def _record_stream_transport_non_json_line(
        self,
        text: str,
        *,
        classification: str,
        recovered_terminal_payload: bool = False,
    ) -> None:
        preview = _stream_transport_preview(text)
        self._stream_transport_non_json_lines.append(preview)
        self._stream_transport_non_json_diagnostics.append(
            {
                "classification": classification,
                "preview": preview,
                "raw_length": len(text),
                "recovered_terminal_payload": recovered_terminal_payload,
            }
        )

    def _exchange(
        self,
        session: _ChildSession,
        request: dict[str, Any],
        *,
        timeout_s: float | None = None,
    ) -> MlxLmSubprocessResult:
        proc = session.proc
        if proc.poll() is not None:
            return MlxLmSubprocessResult(
                ok=False,
                returncode=int(proc.returncode or 0),
                stdout="",
                stderr=self._collect_stderr(session),
                payload={"ok": False, "error": "child process is not running"},
            )
        try:
            stdout_lock_held = False
            with self._io_lock:
                if proc.stdin is None:
                    raise ValueError("child stdin pipe is unavailable")
                if proc.stdout is None:
                    raise ValueError("child stdout pipe is unavailable")
                session.stream_stdout_lock.acquire()
                stdout_lock_held = True
                proc.stdin.write(json.dumps(request) + "\n")
                proc.stdin.flush()
                payload, discarded = self._read_payload_line(session, timeout_s=timeout_s)
                session.stream_stdout_lock.release()
                stdout_lock_held = False
        except Exception as exc:
            if stdout_lock_held:
                session.stream_stdout_lock.release()
            return MlxLmSubprocessResult(
                ok=False,
                returncode=int(proc.returncode or -1),
                stdout="",
                stderr=self._collect_stderr(session),
                payload={"ok": False, "error": str(exc)},
            )
        return MlxLmSubprocessResult(
            ok=bool(payload.get("ok")),
            returncode=0 if proc.poll() is None else int(proc.returncode or 0),
            stdout=discarded,
            stderr=self._collect_stderr(session),
            payload=payload,
        )

    def _stream_exchange(
        self,
        session: _ChildSession,
        request: dict[str, Any],
        *,
        timeout_s: float | None = None,
    ) -> Iterator[dict[str, Any]]:
        proc = session.proc
        if proc.poll() is not None:
            raise RuntimeError("child process is not running")
        messages: queue.Queue[tuple[str, dict[str, Any] | None]] = queue.Queue()

        def worker() -> None:
            gate_lock_held = False
            stdout_lock_held = False

            def release_gate_lock() -> None:
                nonlocal gate_lock_held
                if gate_lock_held:
                    self._io_lock.release()
                    gate_lock_held = False

            try:
                terminal_payload: dict[str, Any] | None = None
                terminal_record: str | None = None
                self._io_lock.acquire()
                gate_lock_held = True
                try:
                    if proc.stdin is None:
                        raise ValueError("child stdin pipe is unavailable")
                    if proc.stdout is None:
                        raise ValueError("child stdout pipe is unavailable")
                    proc.stdin.write(json.dumps(request) + "\n")
                    proc.stdin.flush()
                    write_hook = self._stream_debug_after_request_write
                    if write_hook is not None:
                        write_hook(request)
                    session.stream_stdout_lock.acquire()
                    stdout_lock_held = True
                    while True:
                        text, terminal_prefix_detected = self._read_stream_transport_line(
                            proc.stdout,
                            release_serial_boundary=(
                                release_gate_lock if gate_lock_held else None
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_discriminant_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_discriminant_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_stem_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_stem_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_prefix_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_prefix_detection
                            ),
                            before_terminal_notice_leading_discriminator_marker_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_marker_detection
                            ),
                            before_terminal_notice_leading_discriminator_discriminant_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_discriminant_detection
                            ),
                            before_terminal_notice_leading_discriminator_stem_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_stem_detection
                            ),
                            before_terminal_notice_leading_discriminator_prefix_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_prefix_detection
                            ),
                            before_terminal_notice_leading_discriminator_detection=(
                                self._stream_debug_before_terminal_notice_leading_discriminator_detection
                            ),
                            before_terminal_notice_marker_key_lead_detection=(
                                self._stream_debug_before_terminal_notice_marker_key_lead_detection
                            ),
                            before_terminal_notice_marker_discriminant_detection=(
                                self._stream_debug_before_terminal_notice_marker_discriminant_detection
                            ),
                            before_terminal_notice_marker_stem_detection=(
                                self._stream_debug_before_terminal_notice_marker_stem_detection
                            ),
                            before_terminal_notice_marker_prefix_detection=(
                                self._stream_debug_before_terminal_notice_marker_prefix_detection
                            ),
                            before_terminal_notice_marker_detection=(
                                self._stream_debug_before_terminal_notice_marker_detection
                            ),
                            before_terminal_notice_action_stem=(
                                self._stream_debug_before_terminal_notice_action_stem
                            ),
                            before_terminal_notice_action_discriminant=(
                                self._stream_debug_before_terminal_notice_action_discriminant
                            ),
                            before_terminal_notice_prefix_detection=(
                                self._stream_debug_before_terminal_notice_prefix_detection
                            ),
                            before_terminal_record_prefix_detection=(
                                self._stream_debug_before_terminal_record_prefix_detection
                            ),
                            before_terminal_record_capture=(
                                self._stream_debug_before_terminal_record_capture
                            ),
                        )
                        if not text:
                            continue
                        if _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_earlier_boundary_record(
                            text
                        ):
                            if gate_lock_held:
                                release_gate_lock()
                            continue
                        if _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_boundary_record(
                            text
                        ):
                            if gate_lock_held:
                                release_gate_lock()
                            continue
                        if _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_record(
                            text
                        ):
                            if gate_lock_held:
                                release_gate_lock()
                            continue
                        if _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_record(
                            text
                        ):
                            if gate_lock_held:
                                release_gate_lock()
                            continue
                        if _is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_record(
                            text
                        ):
                            if gate_lock_held:
                                release_gate_lock()
                            continue
                        if _is_terminal_notice_leading_discriminator_record(text):
                            if gate_lock_held:
                                release_gate_lock()
                            continue
                        if _is_terminal_notice_record(text):
                            if gate_lock_held:
                                release_gate_lock()
                            notice_payload = json.loads(text)
                            if not isinstance(notice_payload, dict):
                                raise ValueError(
                                    "terminal notice stream record did not decode to an object"
                                )
                            notice_capture_hook = (
                                self._stream_debug_before_terminal_notice_capture
                            )
                            if notice_capture_hook is not None:
                                notice_capture_hook(notice_payload)
                            notice_hook = (
                                self._stream_debug_before_terminal_action_discriminant
                            )
                            if notice_hook is not None:
                                notice_hook(notice_payload)
                            continue
                        if _is_terminal_stream_record(text):
                            terminal_record = text
                            break
                        try:
                            payload = json.loads(text)
                        except json.JSONDecodeError:
                            recovered_payload = _recover_embedded_terminal_stream_payload(text)
                            if recovered_payload is not None:
                                self._record_stream_transport_non_json_line(
                                    text,
                                    classification=(
                                        "partial_json_framing_recovered_terminal_payload"
                                    ),
                                    recovered_terminal_payload=True,
                                )
                                terminal_payload = recovered_payload
                                break
                            classification = _classify_non_json_stream_transport_line(text)
                            self._record_stream_transport_non_json_line(
                                text,
                                classification=classification,
                            )
                            if classification != "benign_child_stdout_noise":
                                raise ValueError(
                                    "stream transport corrupted JSON record: "
                                    f"{_stream_transport_preview(text)!r}"
                                )
                            print(
                                f"[owlmlx/stream-transport] non-JSON child stdout noise "
                                f"(skipping): {text!r}",
                                file=sys.stderr,
                            )
                            continue
                        if not isinstance(payload, dict):
                            raise ValueError("stream transport record did not decode to an object")
                        if payload.get("event") == "done" or not payload.get("ok"):
                            terminal_payload = payload
                            break
                        messages.put(("payload", payload))
                finally:
                    if gate_lock_held:
                        self._io_lock.release()
                        gate_lock_held = False
                if terminal_record is not None:
                    if stdout_lock_held:
                        session.stream_stdout_lock.release()
                        stdout_lock_held = False
                    capture_hook = self._stream_debug_before_terminal_payload_capture
                    if capture_hook is not None:
                        capture_hook(terminal_record)
                    try:
                        decoded_payload = json.loads(terminal_record)
                    except json.JSONDecodeError as exc:
                        self._record_stream_transport_non_json_line(
                            terminal_record,
                            classification="corrupt_json_transport_record",
                        )
                        raise ValueError(
                            "stream transport corrupted JSON terminal record: "
                            f"{_stream_transport_preview(terminal_record)!r}"
                        ) from exc
                    if not isinstance(decoded_payload, dict):
                        raise ValueError("terminal stream record did not decode to an object")
                    terminal_payload = decoded_payload
                if terminal_payload is not None:
                    debug_hook = self._stream_debug_before_terminal_payload_commit
                    if debug_hook is not None:
                        debug_hook(terminal_payload)
                    messages.put(("payload", terminal_payload))
            except Exception as exc:
                messages.put(("error", {"ok": False, "error": str(exc)}))
            finally:
                if gate_lock_held:
                    self._io_lock.release()
                if stdout_lock_held:
                    session.stream_stdout_lock.release()
                messages.put(("end", None))

        threading.Thread(target=worker, daemon=True).start()
        while True:
            kind, payload = messages.get()
            if kind == "payload" and payload is not None:
                yield payload
                continue
            if kind == "error" and payload is not None:
                yield payload
            return

    def _drop_dead_session(self, model_id: str, session: _ChildSession) -> None:
        self._sessions.pop(model_id, None)
        self._last_error = session.last_error or "child process exited unexpectedly"

    def _probe_session(self, model_id: str, session: _ChildSession) -> dict[str, Any]:
        result = self._exchange(
            session,
            {"action": "ping", "model_id": self._runner_model_id(model_id)},
            timeout_s=self.health_probe_timeout_s,
        )
        if result.ok:
            session.last_payload = result.payload
            session.last_error = None
            return {
                "ok": True,
                "pid": result.payload.get("pid"),
                "generation_count": result.payload.get("generation_count"),
            }
        error = str(result.payload.get("error") or result.stderr or result.returncode)
        session.last_error = error
        if session.proc.poll() is not None:
            self._drop_dead_session(model_id, session)
        return {
            "ok": False,
            "error": error,
            "returncode": result.returncode,
        }

    def _restart_session(self, model_id: str, *, reason: str) -> MlxLmSubprocessResult:
        model = self._registrations.get(model_id)
        if model is None:
            return MlxLmSubprocessResult(
                ok=False,
                returncode=-1,
                stdout="",
                stderr="",
                payload={"ok": False, "error": f"no registration for {model_id}"},
            )
        restart_count = self._restart_counts.get(model_id, 0)
        if restart_count >= self.max_restart_attempts:
            return MlxLmSubprocessResult(
                ok=False,
                returncode=-1,
                stdout="",
                stderr="",
                payload={
                    "ok": False,
                    "error": (
                        f"restart attempts exhausted for {model_id}: "
                        f"{restart_count}/{self.max_restart_attempts}"
                    ),
                },
            )
        session = self._start_session(model)
        result = self._exchange(
            session,
            {"action": "load", "model_id": self._runner_model_id(model_id)},
        )
        self._last_result = result
        if result.ok:
            session.last_payload = result.payload
            session.last_error = None
            self._sessions[model_id] = session
            self._restart_counts[model_id] = restart_count + 1
            self._last_error = None
            return MlxLmSubprocessResult(
                ok=True,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                payload={
                    **result.payload,
                    "restart_count": self._restart_counts[model_id],
                    "restart_reason": reason,
                },
            )
        self._terminate_session(session)
        self._last_error = str(result.payload.get("error") or result.stderr or result.returncode)
        return MlxLmSubprocessResult(
            ok=False,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            payload={
                **result.payload,
                "restart_count": restart_count,
                "restart_reason": reason,
            },
        )

    def _terminate_session(self, session: _ChildSession) -> None:
        proc = session.proc
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except Exception:
            pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2.0)

    def _ensure_session(
        self,
        model_id: str,
        *,
        reason_prefix: str,
    ) -> tuple[_ChildSession | None, GenerateResult | None]:
        if model_id not in self._registrations:
            return None, GenerateResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        session = self._sessions.get(model_id)
        if session is None and self.auto_restart_dead_session:
            restarted = self._restart_session(
                model_id,
                reason=f"missing session before {reason_prefix}",
            )
            if restarted.ok:
                session = self._sessions.get(model_id)
        if session is None:
            return None, GenerateResult(
                ok=False,
                message=f"model session unavailable: {model_id}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
            )
        if session.proc.poll() is not None:
            session.last_error = "child process exited unexpectedly"
            self._drop_dead_session(model_id, session)
            if self.auto_restart_dead_session:
                restarted = self._restart_session(
                    model_id,
                    reason=f"dead child before {reason_prefix}",
                )
                if restarted.ok:
                    session = self._sessions.get(model_id)
                else:
                    return None, GenerateResult(
                        ok=False,
                        message=(
                            f"mlx-lm subprocess {reason_prefix} failed: "
                            f"{restarted.payload.get('error')}"
                        ),
                        error_code=RuntimeErrorCode.backend_error,
                        model_id=model_id,
                        detail={"payload": restarted.payload},
                    )
            else:
                return None, GenerateResult(
                    ok=False,
                    message=(
                        f"mlx-lm subprocess {reason_prefix} failed: child process is not running"
                    ),
                    error_code=RuntimeErrorCode.backend_error,
                    model_id=model_id,
                    detail={"stderr": self._collect_stderr(session)},
                )
        return session, None

    def generate(self, model_id: str, prompt: str, **kwargs: object) -> GenerateResult:
        session, error = self._ensure_session(model_id, reason_prefix="generate")
        if error is not None:
            return error
        assert session is not None

        result = self._exchange(
            session,
            {
                "action": "generate",
                "model_id": self._runner_model_id(model_id),
                "prompt": prompt,
                "params": dict(kwargs),
            },
        )
        self._last_result = result
        if not result.ok:
            error = str(result.payload.get("error") or result.stderr or result.returncode)
            self._last_error = error
            session.last_error = error
            if session.proc.poll() is not None:
                self._drop_dead_session(model_id, session)
            return GenerateResult(
                ok=False,
                message=f"mlx-lm subprocess generate failed: {error}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
                detail={
                    "returncode": result.returncode,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                    "payload": result.payload,
                },
            )

        session.generation_count += 1
        session.last_payload = result.payload
        session.last_error = None
        self._last_error = None
        return GenerateResult(
            ok=True,
            message="generated",
            model_id=model_id,
            text=str(result.payload.get("text", "")),
            detail={
                "returncode": result.returncode,
                "pid": result.payload.get("pid"),
                "generation_count": result.payload.get("generation_count"),
            },
        )

    def generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> GenerateResult:
        session, error = self._ensure_session(model_id, reason_prefix="generate messages")
        if error is not None:
            return error
        assert session is not None

        result = self._exchange(
            session,
            {
                "action": "generate_messages",
                "model_id": self._runner_model_id(model_id),
                "messages": [
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
                "params": dict(kwargs),
            },
        )
        self._last_result = result
        if not result.ok:
            error = str(result.payload.get("error") or result.stderr or result.returncode)
            self._last_error = error
            session.last_error = error
            if session.proc.poll() is not None:
                self._drop_dead_session(model_id, session)
            return GenerateResult(
                ok=False,
                message=f"mlx-lm subprocess message generate failed: {error}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
                detail={
                    "returncode": result.returncode,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                    "payload": result.payload,
                },
            )

        session.generation_count += 1
        session.last_payload = result.payload
        session.last_error = None
        self._last_error = None
        return GenerateResult(
            ok=True,
            message="generated",
            model_id=model_id,
            text=str(result.payload.get("text", "")),
            detail={
                "returncode": result.returncode,
                "pid": result.payload.get("pid"),
                "generation_count": result.payload.get("generation_count"),
                "message_count": result.payload.get("message_count"),
            },
        )

    def generate_cohort(
        self,
        model_id: str,
        prompts: list[str],
        **kwargs: object,
    ) -> GenerateCohortResult:
        """Dispatch multiple non-stream generate requests in one child exchange."""

        if not prompts:
            return GenerateCohortResult(
                ok=False,
                message="at least one prompt is required",
                error_code=RuntimeErrorCode.invalid_request,
                model_id=model_id,
            )

        session, error = self._ensure_session(model_id, reason_prefix="generate cohort")
        if error is not None:
            return GenerateCohortResult(
                ok=False,
                message=error.message,
                error_code=error.error_code,
                model_id=model_id,
                results=(),
                detail=error.detail,
            )
        assert session is not None

        request_payload = {
            "action": "generate_batch",
            "model_id": self._runner_model_id(model_id),
            "requests": [
                {
                    "prompt": prompt,
                    "params": dict(kwargs),
                }
                for prompt in prompts
            ],
        }
        result = self._exchange(session, request_payload)
        self._last_result = result
        if not result.ok:
            backend_error = str(result.payload.get("error") or result.stderr or result.returncode)
            self._last_error = backend_error
            session.last_error = backend_error
            if session.proc.poll() is not None:
                self._drop_dead_session(model_id, session)
            return GenerateCohortResult(
                ok=False,
                message=f"mlx-lm subprocess cohort generate failed: {backend_error}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
                results=(),
                detail={
                    "returncode": result.returncode,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                    "payload": result.payload,
                },
            )

        payload_results = result.payload.get("results")
        if not isinstance(payload_results, list):
            payload_results = []
        generated: list[GenerateResult] = []
        item_errors: list[dict[str, Any]] = []
        for index, item in enumerate(payload_results):
            payload_item = item if isinstance(item, dict) else {}
            item_ok = bool(payload_item.get("ok", True))
            item_error = (
                RuntimeErrorCode.backend_error if not item_ok else None
            )
            generated.append(
                GenerateResult(
                    ok=item_ok,
                    message=str(
                        payload_item.get("message")
                        or ("generated" if item_ok else "child batch item failed")
                    ),
                    error_code=item_error,
                    model_id=model_id,
                    text=str(payload_item.get("text", "")),
                    finish_reason=(
                        None
                        if payload_item.get("finish_reason") is None
                        else str(payload_item.get("finish_reason"))
                    ),
                    prompt_tokens=(
                        None
                        if payload_item.get("prompt_tokens") is None
                        else int(payload_item.get("prompt_tokens"))
                    ),
                    completion_tokens=(
                        None
                        if payload_item.get("completion_tokens") is None
                        else int(payload_item.get("completion_tokens"))
                    ),
                    detail={"batch_index": index},
                )
            )
            if not item_ok:
                item_errors.append(
                    {
                        "batch_index": index,
                        "error": str(payload_item.get("error") or "child batch item failed"),
                    }
                )

        overall_ok = result.ok and not item_errors and len(generated) == len(prompts)
        if overall_ok:
            session.generation_count += 1
            session.aggregated_dispatch_count += 1
            session.aggregated_dispatch_request_count += len(generated)
            session.max_aggregated_dispatch_batch_size = max(
                session.max_aggregated_dispatch_batch_size,
                len(generated),
            )
            session.last_payload = result.payload
            session.last_error = None
            self._last_error = None
            return GenerateCohortResult(
                ok=True,
                message="generated cohort through one child exchange",
                model_id=model_id,
                results=tuple(generated),
                detail={
                    "returncode": result.returncode,
                    "pid": result.payload.get("pid"),
                    "batch_size": int(result.payload.get("batch_size", len(generated)) or 0),
                    "generation_count": result.payload.get("generation_count"),
                    "child_exchange_mode": "aggregated_non_stream_child_exchange_visible",
                    "exchange_count": 1,
                },
            )

        backend_error = (
            str(result.payload.get("error") or "child batch item failure")
            if result.ok
            else str(result.payload.get("error") or result.stderr or result.returncode)
        )
        self._last_error = backend_error
        session.last_error = backend_error
        return GenerateCohortResult(
            ok=False,
            message=f"mlx-lm subprocess cohort generate failed: {backend_error}",
            error_code=RuntimeErrorCode.backend_error,
            model_id=model_id,
            results=tuple(generated),
            detail={
                "returncode": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
                "payload": result.payload,
                "item_errors": item_errors,
            },
        )

    def stream_generate(
        self,
        model_id: str,
        prompt: str,
        **kwargs: object,
    ) -> Iterator[StreamEvent]:
        session, error = self._ensure_session(model_id, reason_prefix="stream")
        if error is not None:
            yield StreamEvent(
                event="error",
                model_id=model_id,
                error_code=error.error_code,
                detail={"message": error.message, **error.detail},
            )
            return
        assert session is not None
        try:
            for payload in self._stream_exchange(
                session,
                {
                    "action": "stream_generate",
                    "model_id": self._runner_model_id(model_id),
                    "prompt": prompt,
                    "params": dict(kwargs),
                },
            ):
                self._last_result = MlxLmSubprocessResult(
                    ok=bool(payload.get("ok")),
                    returncode=0 if session.proc.poll() is None else int(session.proc.returncode or 0),
                    stdout="",
                    stderr=self._collect_stderr(session),
                    payload=payload,
                )
                if not payload.get("ok"):
                    error = str(payload.get("error") or self._collect_stderr(session))
                    self._last_error = error
                    session.last_error = error
                    if session.proc.poll() is not None:
                        self._drop_dead_session(model_id, session)
                    yield StreamEvent(
                        event="error",
                        model_id=model_id,
                        error_code=RuntimeErrorCode.backend_error,
                        detail={"message": error, "payload": payload},
                    )
                    return
                event = str(payload.get("event") or "token")
                if event == "token":
                    yield StreamEvent(
                        event="token",
                        model_id=model_id,
                        text=str(payload.get("text", "")),
                        sequence=payload.get("sequence"),
                        prompt_tokens=payload.get("prompt_tokens"),
                        completion_tokens=payload.get("completion_tokens"),
                        finish_reason=payload.get("finish_reason"),
                        detail=_stream_payload_detail(payload),
                    )
                    continue
                if event == "done":
                    session.generation_count = int(
                        payload.get("generation_count") or (session.generation_count + 1)
                    )
                    session.last_payload = payload
                    session.last_error = None
                    self._last_error = None
                    yield StreamEvent(
                        event="done",
                        model_id=model_id,
                        sequence=payload.get("sequence"),
                        prompt_tokens=payload.get("prompt_tokens"),
                        completion_tokens=payload.get("completion_tokens"),
                        finish_reason=payload.get("finish_reason"),
                        detail=_stream_payload_detail(
                            payload,
                            include_generation_count=True,
                        ),
                    )
                    return
        except Exception as exc:
            error = str(exc)
            self._last_error = error
            session.last_error = error
            if session.proc.poll() is not None:
                self._drop_dead_session(model_id, session)
            yield StreamEvent(
                event="error",
                model_id=model_id,
                error_code=RuntimeErrorCode.backend_error,
                detail={"message": error},
            )

    def stream_generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> Iterator[StreamEvent]:
        session, error = self._ensure_session(model_id, reason_prefix="stream messages")
        if error is not None:
            yield StreamEvent(
                event="error",
                model_id=model_id,
                error_code=error.error_code,
                detail={"message": error.message, **error.detail},
            )
            return
        assert session is not None
        try:
            for payload in self._stream_exchange(
                session,
                {
                    "action": "stream_generate_messages",
                    "model_id": self._runner_model_id(model_id),
                    "messages": [
                        {"role": message.role, "content": message.content}
                        for message in messages
                    ],
                    "params": dict(kwargs),
                },
            ):
                self._last_result = MlxLmSubprocessResult(
                    ok=bool(payload.get("ok")),
                    returncode=0 if session.proc.poll() is None else int(session.proc.returncode or 0),
                    stdout="",
                    stderr=self._collect_stderr(session),
                    payload=payload,
                )
                if not payload.get("ok"):
                    error = str(payload.get("error") or self._collect_stderr(session))
                    self._last_error = error
                    session.last_error = error
                    if session.proc.poll() is not None:
                        self._drop_dead_session(model_id, session)
                    yield StreamEvent(
                        event="error",
                        model_id=model_id,
                        error_code=RuntimeErrorCode.backend_error,
                        detail={"message": error, "payload": payload},
                    )
                    return
                event = str(payload.get("event") or "token")
                if event == "token":
                    yield StreamEvent(
                        event="token",
                        model_id=model_id,
                        text=str(payload.get("text", "")),
                        sequence=payload.get("sequence"),
                        prompt_tokens=payload.get("prompt_tokens"),
                        completion_tokens=payload.get("completion_tokens"),
                        finish_reason=payload.get("finish_reason"),
                        detail=_stream_payload_detail(
                            payload,
                            include_message_count=True,
                        ),
                    )
                    continue
                if event == "done":
                    session.generation_count = int(
                        payload.get("generation_count") or (session.generation_count + 1)
                    )
                    session.last_payload = payload
                    session.last_error = None
                    self._last_error = None
                    yield StreamEvent(
                        event="done",
                        model_id=model_id,
                        sequence=payload.get("sequence"),
                        prompt_tokens=payload.get("prompt_tokens"),
                        completion_tokens=payload.get("completion_tokens"),
                        finish_reason=payload.get("finish_reason"),
                        detail=_stream_payload_detail(
                            payload,
                            include_generation_count=True,
                            include_message_count=True,
                        ),
                    )
                    return
        except Exception as exc:
            error = str(exc)
            self._last_error = error
            session.last_error = error
            if session.proc.poll() is not None:
                self._drop_dead_session(model_id, session)
            yield StreamEvent(
                event="error",
                model_id=model_id,
                error_code=RuntimeErrorCode.backend_error,
                detail={"message": error},
            )

    def unload(self, model_id: str) -> UnloadResult:
        session = self._sessions.pop(model_id, None)
        if session is None:
            stale_model = self._registrations.pop(model_id, None)
            self._restart_counts.pop(model_id, None)
            if stale_model is not None:
                previous_error = self._last_error
                previous_failure_class = _classify_last_subprocess_failure(
                    last_error=self._last_error,
                    last_result=self._last_result,
                )
                registered_without_session = [
                    registered_model_id
                    for registered_model_id in self._registrations
                    if registered_model_id not in self._sessions
                ]
                if not registered_without_session:
                    self._last_error = None
                return UnloadResult(
                    ok=True,
                    message=f"cleared stale subprocess registration: {model_id}",
                    model_id=model_id,
                    freed_gb=stale_model.memory_gb,
                    detail={
                        "stale_registration_cleared": True,
                        "previous_error": previous_error,
                        "previous_failure_class": previous_failure_class,
                    },
                )
            return UnloadResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        self._registrations.pop(model_id, None)
        self._restart_counts.pop(model_id, None)
        result = self._exchange(
            session,
            {
                "action": "shutdown",
                "model_id": self._runner_model_id(model_id),
            },
        )
        self._last_result = result
        if session.proc.poll() is None:
            self._terminate_session(session)
        if not result.ok:
            self._last_error = str(result.payload.get("error") or result.stderr or result.returncode)
            return UnloadResult(
                ok=True,
                message=f"force-unloaded {model_id} after child failure",
                model_id=model_id,
                freed_gb=session.model.memory_gb,
                detail={
                    "pid": session.pid,
                    "returncode": result.returncode,
                    "stderr": result.stderr[-2000:],
                    "payload": result.payload,
                },
            )
        if not self._registrations:
            self._last_error = None
        return UnloadResult(
            ok=True,
            message=f"unloaded {model_id}",
            model_id=model_id,
            freed_gb=session.model.memory_gb,
            detail={"pid": session.pid},
        )

    def status(self) -> BackendStatus:
        dead_models = [
            model_id
            for model_id, session in self._sessions.items()
            if session.proc.poll() is not None
        ]
        for model_id in dead_models:
            session = self._sessions[model_id]
            session.last_error = "child process exited unexpectedly"
            self._drop_dead_session(model_id, session)
        child_health = {}
        for model_id, session in list(self._sessions.items()):
            child_health[model_id] = self._probe_session(model_id, session)
        registered_without_session = sorted(
            model_id
            for model_id in self._registrations
            if model_id not in self._sessions
        )
        restartable_models: list[str] = []
        restart_exhausted_models: list[str] = []
        for model_id in self._registrations:
            if model_id in self._sessions:
                continue
            restart_count = self._restart_counts.get(model_id, 0)
            if self.auto_restart_dead_session and restart_count < self.max_restart_attempts:
                restartable_models.append(model_id)
            else:
                restart_exhausted_models.append(model_id)
        children = {
            model_id: {
                "pid": session.pid,
                "alive": session.proc.poll() is None,
                "generation_count": session.generation_count,
                "restart_count": self._restart_counts.get(model_id, 0),
                "aggregated_dispatch_count": session.aggregated_dispatch_count,
                "aggregated_dispatch_request_count": session.aggregated_dispatch_request_count,
                "max_aggregated_dispatch_batch_size": session.max_aggregated_dispatch_batch_size,
            }
            for model_id, session in self._sessions.items()
        }
        repeated_generation_models = sorted(
            model_id
            for model_id, child in children.items()
            if int(child.get("generation_count", 0)) >= 2
        )
        reuse_counter = sum(
            max(int(child.get("generation_count", 0)) - 1, 0)
            for child in children.values()
        )
        aggregated_dispatch_batch_count = sum(
            int(child.get("aggregated_dispatch_count", 0))
            for child in children.values()
        )
        aggregated_dispatch_request_count = sum(
            int(child.get("aggregated_dispatch_request_count", 0))
            for child in children.values()
        )
        max_aggregated_dispatch_batch_size = max(
            (
                int(child.get("max_aggregated_dispatch_batch_size", 0))
                for child in children.values()
            ),
            default=0,
        )
        last_failure_class = _classify_last_subprocess_failure(
            last_error=self._last_error,
            last_result=self._last_result,
        )
        return BackendStatus(
            backend_name=self.name,
            healthy=self._last_error is None and not registered_without_session,
            loaded_models=tuple(
                self._registrations[model_id]
                for model_id in self._registrations
            ),
            detail={
                "model_count": len(self._registrations),
                "persistent_child": True,
                "last_error": self._last_error,
                "last_failure_class": last_failure_class,
                "dead_registered_models": registered_without_session,
                "auto_restart_dead_session": self.auto_restart_dead_session,
                "max_restart_attempts": self.max_restart_attempts,
                "children": children,
                "child_health": child_health,
                "cache_runtime_observations": {
                    "persistent_child_reuse_visible": bool(repeated_generation_models),
                    "total_generation_count": sum(
                        int(child.get("generation_count", 0))
                        for child in children.values()
                    ),
                    "reuse_counter": reuse_counter,
                    "repeated_generation_models": repeated_generation_models,
                    "child_exchange_mode": (
                        "aggregated_non_stream_child_exchange_visible"
                        if aggregated_dispatch_request_count > 0
                        else "single_request_per_child_exchange"
                    ),
                    "aggregated_child_exchange_visible": aggregated_dispatch_request_count > 0,
                    "aggregated_child_exchange_batch_count": aggregated_dispatch_batch_count,
                    "aggregated_child_exchange_request_count": (
                        aggregated_dispatch_request_count
                    ),
                    "max_aggregated_child_batch_size": max_aggregated_dispatch_batch_size,
                    "cache_counter_visibility": {
                        "residency": False,
                        "reuse": reuse_counter > 0,
                        "eviction": False,
                    },
                },
                "recoverability": {
                    "restartable_models": restartable_models,
                    "restart_exhausted_models": restart_exhausted_models,
                },
                "stream_transport_diagnostics": {
                    "non_json_line_count": len(self._stream_transport_non_json_lines),
                    "diagnostics": list(self._stream_transport_non_json_diagnostics),
                },
                "last_subprocess": (
                    {
                        "ok": self._last_result.ok,
                        "returncode": self._last_result.returncode,
                        "stdout": self._last_result.stdout[-2000:],
                        "stderr": self._last_result.stderr[-2000:],
                        "payload": self._last_result.payload,
                    }
                    if self._last_result is not None
                    else None
                ),
            },
        )
