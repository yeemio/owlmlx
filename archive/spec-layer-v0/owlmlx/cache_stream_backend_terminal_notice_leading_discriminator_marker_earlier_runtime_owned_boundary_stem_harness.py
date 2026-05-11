"""Runtime-owned harness for earlier terminal-notice boundary stem exactness."""

from __future__ import annotations

import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemHarnessResult:
    """Observed backend behavior once the earlier runtime-owned boundary stem narrows the seam."""

    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible: (
        bool
    )
    earlier_runtime_owned_boundary_stem_status: str
    second_stream_blocked_before_terminal_window: bool
    second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected: (
        bool
    )
    second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected: (
        bool
    )
    second_stream_request_written_before_first_terminal_event_consumed: bool
    terminal_window_ms: int
    first_stream_events: tuple[str, ...]
    second_stream_events: tuple[str, ...]


def _write_runner(tmpdir: Path, *, terminal_delay_s: float) -> str:
    module = (
        tmpdir
        / "cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_runner.py"
    )
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
                "            'runtime_owned_terminal_boundary': True,",
                "            'action': 'stream_runtime_owned_terminal_boundary',",
                "            'terminal_action': 'stream_done',",
                "            'sequence': 1,",
                "            'pid': os.getpid(),",
                "        }), flush=True)",
                "        print(json.dumps({",
                "            'ok': True,",
                "            'runtime_owned_terminal_leading_discriminator': True,",
                "            'action': 'stream_runtime_owned_terminal_leading_discriminator',",
                "            'terminal_action': 'stream_done',",
                "            'sequence': 1,",
                "            'pid': os.getpid(),",
                "        }), flush=True)",
                "        print(json.dumps({",
                "            'ok': True,",
                "            'runtime_owned_terminal_notice_discriminator': True,",
                "            'action': 'stream_runtime_owned_terminal_notice_discriminator',",
                "            'terminal_action': 'stream_done',",
                "            'sequence': 1,",
                "            'pid': os.getpid(),",
                "        }), flush=True)",
                "        print(json.dumps({",
                "            'ok': True,",
                "            'terminal_notice_lead': True,",
                "            'action': 'stream_terminal_notice_lead',",
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


def run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness(
    *,
    prompts: tuple[str, str] = (
        "notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-a",
        "notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-b",
    ),
    terminal_window_ms: int = 180,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemHarnessResult:
    """Observe whether the earlier runtime-owned boundary stem is now the tighter seam."""

    from .runtime import MlxLmSubprocessBackend

    first_stream_events: list[str] = []
    second_stream_events: list[str] = []
    first_token_seen = threading.Event()
    first_terminal_event_consumed = threading.Event()
    first_stem_hook_entered = threading.Event()
    allow_first_stem = threading.Event()
    first_prefix_hook_entered = threading.Event()
    allow_first_prefix = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    second_stream_request_written_before_first_terminal_event_consumed = False
    stem_hook_count = 0
    prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()

    with tempfile.TemporaryDirectory(
        prefix="owlmlx-stream-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-"
    ) as tmp:
        tmpdir = Path(tmp)
        runner = _write_runner(tmpdir, terminal_delay_s=terminal_window_ms / 1000)
        backend = MlxLmSubprocessBackend(
            runner_module=runner,
            extra_pythonpath=(str(tmpdir),),
        )

        def before_stem_detection(_: str) -> None:
            nonlocal stem_hook_count
            with hook_lock:
                stem_hook_count += 1
                should_block = stem_hook_count == 1
            if should_block:
                first_stem_hook_entered.set()
                if not allow_first_stem.wait(timeout=2.0):
                    raise RuntimeError(
                        "timed out waiting to release first earlier runtime-owned boundary stem hook"
                    )

        def before_prefix_detection(_: str) -> None:
            nonlocal prefix_hook_count
            with hook_lock:
                prefix_hook_count += 1
                should_block = prefix_hook_count == 1
            if should_block:
                first_prefix_hook_entered.set()
                if not allow_first_prefix.wait(timeout=2.0):
                    raise RuntimeError(
                        "timed out waiting to release first earlier runtime-owned boundary prefix hook from stem harness"
                    )

        def after_request_write(request: dict[str, object]) -> None:
            nonlocal request_write_count
            nonlocal second_stream_request_written_before_first_terminal_event_consumed
            if str(request.get("action") or "") not in {
                "stream_generate",
                "stream_generate_messages",
            }:
                return
            with hook_lock:
                request_write_count += 1
                is_second_stream_request = request_write_count == 2
            if is_second_stream_request:
                second_stream_request_written_before_first_terminal_event_consumed = (
                    not first_terminal_event_consumed.is_set()
                )
                second_request_written.set()

        backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection = (
            before_stem_detection
        )
        backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection = (
            before_prefix_detection
        )
        backend._stream_debug_after_request_write = after_request_write
        loaded = backend.load(
            "stream-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-probe",
            memory_gb=1.0,
        )
        if not loaded.ok:
            raise RuntimeError(
                "backend terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem harness load failed: "
                f"{loaded.message}"
            )

        def run_first() -> None:
            for event in backend.stream_generate(
                "stream-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-probe",
                prompts[0],
            ):
                first_stream_events.append(event.event)
                if event.event == "token" and not first_token_seen.is_set():
                    first_token_seen.set()
                if event.event == "done":
                    first_terminal_event_consumed.set()

        def run_second() -> None:
            for event in backend.stream_generate(
                "stream-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-probe",
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
        if not first_stem_hook_entered.wait(timeout=max((terminal_window_ms / 1000) * 2, 0.3)):
            raise RuntimeError(
                "first earlier runtime-owned boundary stem hook never entered"
            )
        second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected = (
            second_request_written.wait(timeout=0.3)
        )
        if not second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected:
            raise RuntimeError(
                "second backend stream request was not written after first earlier runtime-owned boundary stem detection"
            )
        second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected = (
            not first_prefix_hook_entered.is_set()
        )
        if not second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected:
            raise RuntimeError(
                "second backend stream request was not written before first earlier runtime-owned boundary prefix detection"
            )
        if not second_stream_request_written_before_first_terminal_event_consumed:
            raise RuntimeError(
                "first terminal event was already consumed before earlier runtime-owned boundary stem narrowing was observed"
            )
        allow_first_prefix.set()
        allow_first_stem.set()
        if not second_token_seen.wait(timeout=2.0):
            raise RuntimeError("second backend stream produced no token")
        first_thread.join(timeout=2.0)
        second_thread.join(timeout=2.0)
        if first_thread.is_alive() or second_thread.is_alive():
            raise RuntimeError(
                "earlier runtime-owned boundary stem harness threads failed to finish"
            )
        backend.unload(
            "stream-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-probe"
        )

    visible = (
        second_stream_blocked_before_terminal_window
        and second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected
        and second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected
        and second_stream_request_written_before_first_terminal_event_consumed
        and tuple(first_stream_events) == ("token", "done")
        and tuple(second_stream_events) == ("token", "done")
    )
    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemHarnessResult(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible=visible,
        earlier_runtime_owned_boundary_stem_status=(
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible"
            if visible
            else "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_not_visible"
        ),
        second_stream_blocked_before_terminal_window=second_stream_blocked_before_terminal_window,
        second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected=(
            second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected
        ),
        second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected=(
            second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected
        ),
        second_stream_request_written_before_first_terminal_event_consumed=(
            second_stream_request_written_before_first_terminal_event_consumed
        ),
        terminal_window_ms=terminal_window_ms,
        first_stream_events=tuple(first_stream_events),
        second_stream_events=tuple(second_stream_events),
    )
