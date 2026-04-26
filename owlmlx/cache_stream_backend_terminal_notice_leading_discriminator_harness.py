"""Runtime-owned harness for terminal-notice leading-discriminator introduction."""

from __future__ import annotations

import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorHarnessResult:
    """Observed backend behavior after a runtime-owned leading discriminator is introduced."""

    backend_terminal_notice_leading_discriminator_boundary_visible: bool
    leading_discriminator_status: str
    second_stream_blocked_before_terminal_window: bool
    second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected: bool
    second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected: bool
    second_stream_request_written_before_first_terminal_event_consumed: bool
    terminal_window_ms: int
    first_stream_events: tuple[str, ...]
    second_stream_events: tuple[str, ...]


def _write_runner(tmpdir: Path, *, terminal_delay_s: float) -> str:
    module = tmpdir / "cache_stream_backend_terminal_notice_leading_discriminator_runner.py"
    module.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "generation_count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        generation_count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action in ('stream_generate', 'stream_generate_messages'):",
                "        generation_count += 1",
                "        prompt = req.get('prompt', '') or 'messages'",
                "        print(json.dumps({",
                "            'ok': True,",
                "            'action': 'stream_event',",
                "            'event': 'token',",
                "            'text': prompt + ' :: token',",
                "            'sequence': 1,",
                "            'prompt_tokens': 1,",
                "            'completion_tokens': 1,",
                "            'finish_reason': None,",
                "            'pid': os.getpid(),",
                "        }), flush=True)",
                f"        time.sleep({terminal_delay_s})",
                "        print(json.dumps({",
                "            'ok': True,",
                "            'action': 'stream_terminal_notice_lead',",
                "            'terminal_notice_lead': True,",
                "            'terminal_action': 'stream_done',",
                "            'sequence': 1,",
                "            'pid': os.getpid(),",
                "        }), flush=True)",
                "        print(json.dumps({",
                "            'ok': True,",
                "            'terminal_notice': True,",
                "            'action': 'stream_terminal_notice',",
                "            'terminal_action': 'stream_done',",
                "            'sequence': 1,",
                "            'pid': os.getpid(),",
                "        }), flush=True)",
                "        print(json.dumps({",
                "            'ok': True,",
                "            'action': 'stream_done',",
                "            'event': 'done',",
                "            'sequence': 1,",
                "            'prompt_tokens': 1,",
                "            'completion_tokens': 1,",
                "            'finish_reason': 'stop',",
                "            'generation_count': generation_count,",
                "            'pid': os.getpid(),",
                "        }), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    return module.stem


def run_cache_stream_backend_terminal_notice_leading_discriminator_harness(
    *,
    prompts: tuple[str, str] = (
        "notice-leading-discriminator-a",
        "notice-leading-discriminator-b",
    ),
    terminal_window_ms: int = 180,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorHarnessResult:
    """Observe whether a new runtime-owned leading discriminator now moves the serial boundary."""

    from .runtime import MlxLmSubprocessBackend

    first_stream_events: list[str] = []
    second_stream_events: list[str] = []
    first_token_seen = threading.Event()
    first_terminal_event_consumed = threading.Event()
    first_terminal_notice_leading_discriminator_hook_entered = threading.Event()
    allow_first_terminal_notice_leading_discriminator = threading.Event()
    first_terminal_notice_marker_key_lead_hook_entered = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()

    with tempfile.TemporaryDirectory(
        prefix="owlmlx-stream-terminal-notice-leading-discriminator-"
    ) as tmp:
        tmpdir = Path(tmp)
        runner = _write_runner(tmpdir, terminal_delay_s=terminal_window_ms / 1000)
        backend = MlxLmSubprocessBackend(
            runner_module=runner,
            extra_pythonpath=(str(tmpdir),),
        )

        def before_terminal_notice_leading_discriminator_detection(_: str) -> None:
            nonlocal leading_discriminator_hook_count
            with hook_lock:
                leading_discriminator_hook_count += 1
                should_block = leading_discriminator_hook_count == 1
            if should_block:
                first_terminal_notice_leading_discriminator_hook_entered.set()
                if not allow_first_terminal_notice_leading_discriminator.wait(timeout=2.0):
                    raise RuntimeError(
                        "timed out waiting to release first terminal notice leading discriminator hook"
                    )

        def before_terminal_notice_marker_key_lead_detection(_: str) -> None:
            first_terminal_notice_marker_key_lead_hook_entered.set()

        def after_request_write(request: dict[str, object]) -> None:
            nonlocal request_write_count
            if str(request.get("action") or "") not in {
                "stream_generate",
                "stream_generate_messages",
            }:
                return
            with hook_lock:
                request_write_count += 1
                is_second_stream_request = request_write_count == 2
            if is_second_stream_request:
                second_request_written.set()

        backend._stream_debug_before_terminal_notice_leading_discriminator_detection = (
            before_terminal_notice_leading_discriminator_detection
        )
        backend._stream_debug_before_terminal_notice_marker_key_lead_detection = (
            before_terminal_notice_marker_key_lead_detection
        )
        backend._stream_debug_after_request_write = after_request_write
        loaded = backend.load(
            "stream-terminal-notice-leading-discriminator-probe",
            memory_gb=1.0,
        )
        if not loaded.ok:
            raise RuntimeError(
                "backend terminal-notice-leading-discriminator harness load failed: "
                f"{loaded.message}"
            )

        def run_first() -> None:
            for event in backend.stream_generate(
                "stream-terminal-notice-leading-discriminator-probe",
                prompts[0],
            ):
                first_stream_events.append(event.event)
                if event.event == "token" and not first_token_seen.is_set():
                    first_token_seen.set()
                if event.event == "done":
                    first_terminal_event_consumed.set()

        def run_second() -> None:
            for event in backend.stream_generate(
                "stream-terminal-notice-leading-discriminator-probe",
                prompts[1],
            ):
                second_stream_events.append(event.event)
                if event.event == "token" and not second_token_seen.is_set():
                    second_token_seen.set()

        first_thread = threading.Thread(target=run_first)
        second_thread = threading.Thread(target=run_second)
        first_thread.start()
        if not first_token_seen.wait(timeout=2.0):
            raise RuntimeError("first backend stream produced no token")
        second_thread.start()
        second_stream_blocked_before_terminal_window = not second_request_written.wait(
            timeout=max(terminal_window_ms / 1000 / 3, 0.05)
        )
        if not first_terminal_notice_leading_discriminator_hook_entered.wait(
            timeout=max((terminal_window_ms / 1000) * 2, 0.3)
        ):
            raise RuntimeError(
                "first terminal notice leading discriminator hook never entered"
            )
        second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected = (
            second_request_written.wait(timeout=0.3)
        )
        if not second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected:
            raise RuntimeError(
                "second backend stream request was not written after first terminal notice leading discriminator detection"
            )
        second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected = (
            not first_terminal_notice_marker_key_lead_hook_entered.is_set()
        )
        second_stream_request_written_before_first_terminal_event_consumed = (
            not first_terminal_event_consumed.is_set()
        )
        allow_first_terminal_notice_leading_discriminator.set()
        if not second_token_seen.wait(timeout=2.0):
            raise RuntimeError("second backend stream never produced a token")
        first_thread.join(timeout=2.0)
        second_thread.join(timeout=2.0)
        backend.unload("stream-terminal-notice-leading-discriminator-probe")

    first_stream_event_tuple = tuple(first_stream_events)
    second_stream_event_tuple = tuple(second_stream_events)
    visible = (
        second_stream_blocked_before_terminal_window
        and second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected
        and second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected
        and second_stream_request_written_before_first_terminal_event_consumed
        and first_stream_event_tuple == ("token", "done")
        and second_stream_event_tuple == ("token", "done")
    )
    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorHarnessResult(
        backend_terminal_notice_leading_discriminator_boundary_visible=visible,
        leading_discriminator_status=(
            "backend_terminal_notice_leading_discriminator_boundary_visible"
            if visible
            else "backend_terminal_notice_leading_discriminator_boundary_not_yet_visible"
        ),
        second_stream_blocked_before_terminal_window=(
            second_stream_blocked_before_terminal_window
        ),
        second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected=(
            second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected
        ),
        second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected=(
            second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected
        ),
        second_stream_request_written_before_first_terminal_event_consumed=(
            second_stream_request_written_before_first_terminal_event_consumed
        ),
        terminal_window_ms=terminal_window_ms,
        first_stream_events=first_stream_event_tuple,
        second_stream_events=second_stream_event_tuple,
    )
