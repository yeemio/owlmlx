"""Runtime-owned harness for exact backend terminal-payload-capture dependency."""

from __future__ import annotations

import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalPayloadCaptureHarnessResult:
    """Observed backend terminal-payload-capture behavior on the active path."""

    backend_terminal_payload_capture_boundary_visible: bool
    payload_capture_status: str
    second_stream_blocked_before_terminal_window: bool
    second_stream_started_before_first_terminal_payload_captured: bool
    second_stream_started_before_first_terminal_event_consumed: bool
    terminal_window_ms: int
    first_stream_events: tuple[str, ...]
    second_stream_events: tuple[str, ...]


def _write_runner(tmpdir: Path, *, terminal_delay_s: float) -> str:
    module = tmpdir / "cache_stream_backend_terminal_payload_capture_runner.py"
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


def run_cache_stream_backend_terminal_payload_capture_harness(
    *,
    prompts: tuple[str, str] = ("capture-a", "capture-b"),
    terminal_window_ms: int = 180,
) -> CacheStreamBackendTerminalPayloadCaptureHarnessResult:
    """Observe whether terminal-payload capture is now narrower than the live stream seam."""

    from .runtime import MlxLmSubprocessBackend

    first_stream_events: list[str] = []
    second_stream_events: list[str] = []
    first_token_seen = threading.Event()
    first_terminal_event_consumed = threading.Event()
    first_terminal_payload_capture_hook_entered = threading.Event()
    allow_first_terminal_payload_capture = threading.Event()
    second_token_seen = threading.Event()
    hook_count = 0
    hook_count_lock = threading.Lock()

    with tempfile.TemporaryDirectory(prefix="owlmlx-stream-terminal-payload-capture-") as tmp:
        tmpdir = Path(tmp)
        runner = _write_runner(tmpdir, terminal_delay_s=terminal_window_ms / 1000)
        backend = MlxLmSubprocessBackend(
            runner_module=runner,
            extra_pythonpath=(str(tmpdir),),
        )

        def before_terminal_payload_capture(_: str) -> None:
            nonlocal hook_count
            with hook_count_lock:
                hook_count += 1
                should_block = hook_count == 1
            if should_block:
                first_terminal_payload_capture_hook_entered.set()
                if not allow_first_terminal_payload_capture.wait(timeout=2.0):
                    raise RuntimeError(
                        "timed out waiting to release first terminal payload capture"
                    )

        backend._stream_debug_before_terminal_payload_capture = (
            before_terminal_payload_capture
        )
        loaded = backend.load("stream-terminal-payload-capture-probe", memory_gb=1.0)
        if not loaded.ok:
            raise RuntimeError(
                f"backend terminal-payload-capture harness load failed: {loaded.message}"
            )

        def run_first() -> None:
            for event in backend.stream_generate(
                "stream-terminal-payload-capture-probe",
                prompts[0],
            ):
                first_stream_events.append(event.event)
                if event.event == "token" and not first_token_seen.is_set():
                    first_token_seen.set()
                if event.event == "done":
                    first_terminal_event_consumed.set()

        def run_second() -> None:
            for event in backend.stream_generate(
                "stream-terminal-payload-capture-probe",
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
        second_stream_blocked_before_terminal_window = not second_token_seen.wait(
            timeout=max(terminal_window_ms / 1000 / 3, 0.05)
        )
        if not first_terminal_payload_capture_hook_entered.wait(
            timeout=max((terminal_window_ms / 1000) * 2, 0.3)
        ):
            raise RuntimeError("first terminal payload capture hook never entered")
        if not second_token_seen.wait(timeout=0.3):
            raise RuntimeError(
                "second backend stream did not start before first terminal payload capture"
            )
        second_stream_started_before_first_terminal_payload_captured = (
            not allow_first_terminal_payload_capture.is_set()
        )
        second_stream_started_before_first_terminal_event_consumed = (
            not first_terminal_event_consumed.is_set()
        )
        allow_first_terminal_payload_capture.set()
        first_thread.join(timeout=2.0)
        second_thread.join(timeout=2.0)
        backend.unload("stream-terminal-payload-capture-probe")

    first_stream_event_tuple = tuple(first_stream_events)
    second_stream_event_tuple = tuple(second_stream_events)
    visible = (
        second_stream_blocked_before_terminal_window
        and second_stream_started_before_first_terminal_payload_captured
        and second_stream_started_before_first_terminal_event_consumed
        and first_stream_event_tuple == ("token", "done")
        and second_stream_event_tuple == ("token", "done")
    )
    return CacheStreamBackendTerminalPayloadCaptureHarnessResult(
        backend_terminal_payload_capture_boundary_visible=visible,
        payload_capture_status=(
            "backend_terminal_payload_capture_boundary_visible"
            if visible
            else "backend_terminal_payload_capture_boundary_not_yet_visible"
        ),
        second_stream_blocked_before_terminal_window=(
            second_stream_blocked_before_terminal_window
        ),
        second_stream_started_before_first_terminal_payload_captured=(
            second_stream_started_before_first_terminal_payload_captured
        ),
        second_stream_started_before_first_terminal_event_consumed=(
            second_stream_started_before_first_terminal_event_consumed
        ),
        terminal_window_ms=terminal_window_ms,
        first_stream_events=first_stream_event_tuple,
        second_stream_events=second_stream_event_tuple,
    )
