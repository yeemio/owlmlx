from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path

from owlmlx.runtime import MlxLmSubprocessBackend, RuntimeErrorCode, RuntimeKernel
from owlmlx.runtime.types import ChatTurn


def _clock_box(start: float = 100.0):
    state = {"now": float(start)}

    def clock() -> float:
        return float(state["now"])

    return state, clock


def _write_runner(
    tmp_path: Path,
    *,
    ok: bool = True,
    crash_on_generate: bool = False,
    error_on_generate: bool = False,
) -> str:
    module = tmp_path / "fake_runner.py"
    if ok:
        generate_body = (
            "        raise SystemExit(7)"
            if crash_on_generate
            else (
                "        print(json.dumps({'ok': False, 'error': 'child boom'}), flush=True)"
                if error_on_generate
                else (
                "        count += 1\n"
                "        print(json.dumps({'ok': True, 'action': 'generate', "
                "'text': req['prompt'] + ' :: child', 'pid': os.getpid(), "
                "'generation_count': count, 'prompt_tokens': 7, 'completion_tokens': 3}), flush=True)"
                )
            )
        )
        module.write_text(
            "\n".join(
                [
                    "import json, os, sys",
                    "loaded = None",
                    "count = 0",
                    "for line in sys.stdin:",
                    "    req = json.loads(line)",
                    "    action = req.get('action')",
                    "    if action == 'load':",
                    "        loaded = req['model_id']",
                    "        count = 0",
                    "        print(json.dumps({'ok': True, 'action': 'load', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                    "    elif action == 'generate':",
                    *generate_body.splitlines(),
                    "    elif action == 'generate_batch':",
                    "        requests = list(req.get('requests', []))",
                    "        count += 1",
                    "        results = [",
                    "            {'ok': True, 'text': item.get('prompt', '') + ' :: child', 'finish_reason': 'stop'}",
                    "            for item in requests",
                    "        ]",
                    "        print(json.dumps({'ok': True, 'action': 'generate_batch', 'results': results, 'batch_size': len(results), 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                    "    elif action == 'generate_messages':",
                    "        count += 1",
                    "        text = ' | '.join(f\"{m['role']}:{m['content']}\" for m in req.get('messages', []))",
                    "        print(json.dumps({'ok': True, 'action': 'generate_messages', 'text': text + ' :: child', 'pid': os.getpid(), 'generation_count': count, 'message_count': len(req.get('messages', [])), 'prompt_tokens': 9, 'completion_tokens': 4}), flush=True)",
                    "    elif action == 'stream_generate':",
                    "        count += 1",
                    "        timing = {'surface': 'owlmlx.child_stream_timing', 'version': 'v1', 'first_response_ms': 11.0, 'first_visible_token_ms': 12.0, 'stream_wall_ms': 13.0}",
                    "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming', 'timing': timing}), flush=True)",
                    "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop', 'timing': timing}), flush=True)",
                    "    elif action == 'stream_generate_messages':",
                    "        count += 1",
                    "        text = ' | '.join(f\"{m['role']}:{m['content']}\" for m in req.get('messages', []))",
                    "        timing = {'surface': 'owlmlx.child_stream_timing', 'version': 'v1', 'prompt_render_ms': 2.0, 'first_response_ms': 11.0, 'first_visible_token_ms': 12.0, 'stream_wall_ms': 13.0}",
                    "        print(json.dumps({'ok': True, 'action': 'stream_message_event', 'event': 'token', 'text': text, 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming', 'message_count': len(req.get('messages', [])), 'timing': timing}), flush=True)",
                    "        print(json.dumps({'ok': True, 'action': 'stream_message_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop', 'message_count': len(req.get('messages', [])), 'timing': timing}), flush=True)",
                    "    elif action == 'ping':",
                    "        print(json.dumps({'ok': True, 'action': 'ping', 'model_id': loaded, 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                    "    elif action in ('shutdown', 'unload'):",
                    "        print(json.dumps({'ok': True, 'action': action, 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                    "        break",
                    "    else:",
                    "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
                ]
            ),
            encoding="utf-8",
        )
    else:
        module.write_text(
            "\n".join(
                [
                    "import json, sys",
                    "for _line in sys.stdin:",
                    "    print(json.dumps({'ok': False, 'error': 'child boom'}), flush=True)",
                    "    continue",
                ]
            ),
            encoding="utf-8",
        )
    return module.stem


def _write_prefill_progress_runner(tmp_path: Path) -> str:
    module = tmp_path / "prefill_progress_runner.py"
    module.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "loaded = None",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        loaded = req['model_id']",
                "        print(json.dumps({'ok': True, 'action': 'load', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        chunk = req.get('params', {}).get('prefill_chunk_tokens')",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'prefill_progress', 'model_id': loaded, 'pid': os.getpid(), 'processed': 1024, 'total': 4096, 'ratio': 0.25, 'prefill_sequence': 1, 'received_prefill_chunk_tokens': chunk}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 4, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 4, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action == 'stream_generate_messages':",
                "        count += 1",
                "        chunk = req.get('params', {}).get('prefill_chunk_tokens')",
                "        text = ' | '.join(f\"{m['role']}:{m['content']}\" for m in req.get('messages', []))",
                "        print(json.dumps({'ok': True, 'action': 'stream_message_event', 'event': 'prefill_progress', 'model_id': loaded, 'pid': os.getpid(), 'processed': 2048, 'total': 4096, 'ratio': 0.5, 'prefill_sequence': 1, 'message_count': len(req.get('messages', [])), 'received_prefill_chunk_tokens': chunk}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_message_event', 'event': 'token', 'text': text, 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 4, 'completion_tokens': 1, 'finish_reason': 'streaming', 'message_count': len(req.get('messages', []))}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_message_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 4, 'completion_tokens': 1, 'finish_reason': 'stop', 'message_count': len(req.get('messages', []))}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    elif action == 'ping':",
                "        print(json.dumps({'ok': True, 'action': 'ping', 'model_id': loaded, 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    return module.stem


def _write_fake_mlx_lm_package(
    tmp_path: Path,
    *,
    model_modules: tuple[str, ...] = (),
) -> None:
    models_dir = tmp_path / "mlx_lm" / "models"
    models_dir.mkdir(parents=True)
    (tmp_path / "mlx_lm" / "__init__.py").write_text("", encoding="utf-8")
    (models_dir / "__init__.py").write_text("", encoding="utf-8")
    for module_name in model_modules:
        (models_dir / f"{module_name}.py").write_text("", encoding="utf-8")


def _write_metal_oom_runner(tmp_path: Path) -> str:
    module = tmp_path / "metal_oom_runner.py"
    module.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "loaded = None",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        loaded = req['model_id']",
                "        print(json.dumps({'ok': True, 'action': 'load', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "    elif action == 'generate':",
                "        print('libc++abi: terminating due to uncaught exception of type std::runtime_error: [METAL] Command buffer execution failed: Insufficient Memory (00000008:kIOGPUCommandBufferCallbackErrorOutOfMemory)', file=sys.stderr, flush=True)",
                "        raise SystemExit(134)",
                "    elif action == 'ping':",
                "        print(json.dumps({'ok': True, 'action': 'ping', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "        break",
            ]
        ),
        encoding="utf-8",
    )
    return module.stem


def test_subprocess_backend_load_starts_persistent_child(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )

    result = backend.load("model-a", memory_gb=2.0)

    assert result.ok is True
    assert result.model is not None
    status = backend.status()
    assert status.loaded_models[0].model_id == "model-a"
    assert status.detail["persistent_child"] is True
    assert status.detail["children"]["model-a"]["alive"] is True
    assert status.detail["children"]["model-a"]["pid"] is not None
    backend.unload("model-a")


def test_subprocess_backend_rejects_unsupported_model_type_without_dirty_health(
    tmp_path: Path,
) -> None:
    _write_fake_mlx_lm_package(tmp_path, model_modules=("gemma4",))
    model_dir = tmp_path / "DeepSeek-V4-Flash-2bit-DQ"
    model_dir.mkdir()
    (model_dir / "config.json").write_text(
        '{"model_type": "deepseek_v4"}',
        encoding="utf-8",
    )
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        python_executable=sys.executable,
        runner_module=runner,
        model_path_resolver=lambda _model_id: str(model_dir),
        extra_pythonpath=(str(tmp_path),),
    )
    kernel = RuntimeKernel(backend)

    result = kernel.load_model("DeepSeek-V4-Flash-2bit-DQ", memory_gb=1.0)

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.unsupported_model_family
    assert result.detail["does_not_start_child"] is True
    assert result.detail["does_not_dirty_backend_health"] is True
    assert result.detail["preflight"]["model_type"] == "deepseek_v4"
    assert result.detail["preflight"]["module_name"] == "mlx_lm.models.deepseek_v4"
    status = kernel.status_dict()
    assert status["backend"]["healthy"] is True
    assert status["backend"]["detail"]["last_error"] is None
    assert status["backend"]["detail"]["children"] == {}
    assert status["backend"]["detail"]["model_count"] == 0
    assert status["health"]["readiness"] == "degraded"
    assert status["load_failure"]["events"] == []
    assert status["load_failure"]["unresolved_event_count"] == 0


def test_subprocess_backend_generate_reuses_same_child(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    first = backend.generate("model-a", "hello", max_tokens=4)
    second = backend.generate("model-a", "again", max_tokens=4)

    assert first.ok is True
    assert second.ok is True
    assert first.text == "hello :: child"
    assert second.text == "again :: child"
    assert first.detail["pid"] == second.detail["pid"]
    assert first.detail["generation_count"] == 1
    assert second.detail["generation_count"] == 2
    assert backend.status().detail["children"]["model-a"]["generation_count"] == 2
    assert (
        backend.status().detail["cache_runtime_observations"]["persistent_child_reuse_visible"]
        is True
    )
    assert backend.status().detail["cache_runtime_observations"]["reuse_counter"] == 1
    assert backend.status().detail["cache_runtime_observations"]["cache_counter_visibility"][
        "reuse"
    ] is True
    assert backend.status().detail["cache_runtime_observations"][
        "repeated_generation_models"
    ] == ["model-a"]
    backend.unload("model-a")


def test_subprocess_backend_generate_surfaces_usage_token_counts(tmp_path: Path) -> None:
    # Supported-backend parity with the native non-stream usage fix: the child
    # emits prompt_tokens/completion_tokens; the backend must surface them on the
    # GenerateResult so the routes can build a usage block.
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)
    result = backend.generate("model-a", "hello", max_tokens=4)
    assert result.ok is True
    assert result.prompt_tokens == 7
    assert result.completion_tokens == 3
    backend.unload("model-a")


def test_subprocess_backend_stream_generate_reuses_same_child(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    events = list(backend.stream_generate("model-a", "hello", max_tokens=4))

    assert [event.event for event in events] == ["token", "done"]
    assert events[0].text == "hello"
    assert events[0].detail["pid"] == events[1].detail["pid"]
    assert events[0].detail["timing"]["first_visible_token_ms"] == 12.0
    assert events[1].detail["timing"]["surface"] == "owlmlx.child_stream_timing"
    assert backend.status().detail["children"]["model-a"]["generation_count"] == 1
    backend.unload("model-a")


def test_subprocess_backend_stream_generate_yields_prefill_progress(
    tmp_path: Path,
) -> None:
    runner = _write_prefill_progress_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    events = list(
        backend.stream_generate(
            "model-a",
            "hello",
            max_tokens=4,
            prefill_chunk_tokens=1024,
        )
    )

    assert [event.event for event in events] == ["prefill_progress", "token", "done"]
    assert events[0].detail["processed"] == 1024
    assert events[0].detail["total"] == 4096
    assert events[0].detail["ratio"] == 0.25
    assert events[0].detail["prefill_sequence"] == 1
    assert events[0].detail["received_prefill_chunk_tokens"] == 1024
    backend.unload("model-a")


def test_stream_transport_line_uses_readline_not_byte_reads() -> None:
    class ReadlineOnlyStdout:
        def readline(self) -> str:
            return (
                '{"ok":true,"action":"stream_done","event":"done",'
                '"finish_reason":"stop"}\n'
            )

        def read(self, _: int) -> str:
            raise AssertionError("stream transport must not use byte-at-a-time reads")

    backend = MlxLmSubprocessBackend()
    released = False

    def release_serial_boundary() -> None:
        nonlocal released
        released = True

    text, terminal_prefix_detected = backend._read_stream_transport_line(
        ReadlineOnlyStdout(),
        release_serial_boundary=release_serial_boundary,
    )

    assert text.startswith('{"ok":true,"action":"stream_done"')
    assert terminal_prefix_detected is True
    assert released is True


def test_subprocess_backend_releases_stream_lock_before_terminal_payload_capture(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_payload_capture_hook_entered = threading.Event()
    allow_first_terminal_payload_capture = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_token_seen = threading.Event()
    hook_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_payload_capture(_: str) -> None:
        nonlocal hook_count
        with hook_lock:
            hook_count += 1
            should_block = hook_count == 1
        if should_block:
            first_terminal_payload_capture_hook_entered.set()
            if not allow_first_terminal_payload_capture.wait(timeout=2.0):
                raise RuntimeError("timed out waiting to release terminal payload capture")

    backend._stream_debug_before_terminal_payload_capture = (
        before_terminal_payload_capture
    )

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_token_seen.wait(timeout=0.05) is False
    assert first_terminal_payload_capture_hook_entered.wait(timeout=0.6) is True
    assert second_token_seen.wait(timeout=0.3) is True
    assert allow_first_terminal_payload_capture.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_payload_capture.set()
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_discriminant_hook_entered = threading.Event()
    allow_first_discriminant = threading.Event()
    first_stem_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    discriminant_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_discriminant_detection(_: str) -> None:
        nonlocal discriminant_hook_count
        with hook_lock:
            discriminant_hook_count += 1
            should_block = discriminant_hook_count == 1
        if should_block:
            first_discriminant_hook_entered.set()
            if not allow_first_discriminant.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned discriminator discriminant"
                )

    def before_stem_detection(_: str) -> None:
        first_stem_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection = (
        before_discriminant_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection = (
        before_stem_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_discriminant_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_stem_hook_entered.is_set() is False
    assert allow_first_discriminant.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_discriminant.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_leading_discriminator': True, 'action': 'stream_runtime_owned_terminal_leading_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_leading_discriminator_hook_entered = threading.Event()
    allow_first_leading_discriminator = threading.Event()
    first_discriminator_discriminant_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_leading_discriminator_detection(_: str) -> None:
        nonlocal leading_discriminator_hook_count
        with hook_lock:
            leading_discriminator_hook_count += 1
            should_block = leading_discriminator_hook_count == 1
        if should_block:
            first_leading_discriminator_hook_entered.set()
            if not allow_first_leading_discriminator.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned leading discriminator"
                )

    def before_discriminator_discriminant_detection(_: str) -> None:
        first_discriminator_discriminant_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection = (
        before_leading_discriminator_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection = (
        before_discriminator_discriminant_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_leading_discriminator_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_discriminator_discriminant_hook_entered.is_set() is False
    assert allow_first_leading_discriminator.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_leading_discriminator.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_leading_discriminator': True, 'action': 'stream_runtime_owned_terminal_leading_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_prefix_hook_entered = threading.Event()
    allow_first_prefix = threading.Event()
    first_detection_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_prefix_detection(_: str) -> None:
        nonlocal prefix_hook_count
        with hook_lock:
            prefix_hook_count += 1
            should_block = prefix_hook_count == 1
        if should_block:
            first_prefix_hook_entered.set()
            if not allow_first_prefix.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned leading discriminator prefix"
                )

    def before_detection(_: str) -> None:
        first_detection_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection = (
        before_prefix_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection = (
        before_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_prefix_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_detection_hook_entered.is_set() is False
    assert allow_first_prefix.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_leading_discriminator': True, 'action': 'stream_runtime_owned_terminal_leading_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_stem_hook_entered = threading.Event()
    allow_first_stem = threading.Event()
    first_prefix_hook_entered = threading.Event()
    allow_first_prefix = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    stem_hook_count = 0
    prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_stem_detection(_: str) -> None:
        nonlocal stem_hook_count
        with hook_lock:
            stem_hook_count += 1
            should_block = stem_hook_count == 1
        if should_block:
            first_stem_hook_entered.set()
            if not allow_first_stem.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned leading discriminator stem"
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
                    "timed out waiting to release earlier runtime-owned boundary prefix from stem test"
                )

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection = (
        before_stem_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection = (
        before_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_stem_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_prefix_hook_entered.is_set() is False
    assert allow_first_stem.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_prefix.set()
    allow_first_stem.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_leading_discriminator': True, 'action': 'stream_runtime_owned_terminal_leading_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_discriminant_hook_entered = threading.Event()
    allow_first_discriminant = threading.Event()
    first_stem_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    discriminant_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_discriminant_detection(_: str) -> None:
        nonlocal discriminant_hook_count
        with hook_lock:
            discriminant_hook_count += 1
            should_block = discriminant_hook_count == 1
        if should_block:
            first_discriminant_hook_entered.set()
            if not allow_first_discriminant.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned leading discriminator discriminant"
                )

    def before_stem_detection(_: str) -> None:
        first_stem_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection = (
        before_discriminant_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection = (
        before_stem_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_discriminant_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_stem_hook_entered.is_set() is False
    assert allow_first_discriminant.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_discriminant.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_record_capture(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_record_capture_hook_entered = threading.Event()
    allow_first_terminal_record_capture = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    record_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_record_capture(_: str) -> None:
        nonlocal record_hook_count
        with hook_lock:
            record_hook_count += 1
            should_block = record_hook_count == 1
        if should_block:
            first_terminal_record_capture_hook_entered.set()
            if not allow_first_terminal_record_capture.wait(timeout=2.0):
                raise RuntimeError("timed out waiting to release terminal record capture")

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_record_capture = (
        before_terminal_record_capture
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_record_capture_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert allow_first_terminal_record_capture.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_record_capture.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_record_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_record_prefix_hook_entered = threading.Event()
    allow_first_terminal_record_prefix = threading.Event()
    first_terminal_record_capture_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_record_prefix_detection(_: str) -> None:
        nonlocal prefix_hook_count
        with hook_lock:
            prefix_hook_count += 1
            should_block = prefix_hook_count == 1
        if should_block:
            first_terminal_record_prefix_hook_entered.set()
            if not allow_first_terminal_record_prefix.wait(timeout=2.0):
                raise RuntimeError("timed out waiting to release terminal record prefix")

    def before_terminal_record_capture(_: str) -> None:
        first_terminal_record_capture_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_record_prefix_detection = (
        before_terminal_record_prefix_detection
    )
    backend._stream_debug_before_terminal_record_capture = (
        before_terminal_record_capture
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_record_prefix_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_record_capture_hook_entered.is_set() is False
    assert allow_first_terminal_record_prefix.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_record_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_action_discriminant_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_action_discriminant_hook_entered = threading.Event()
    allow_first_terminal_action_discriminant = threading.Event()
    first_terminal_record_prefix_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    action_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_action_discriminant(_: dict[str, object]) -> None:
        nonlocal action_hook_count
        with hook_lock:
            action_hook_count += 1
            should_block = action_hook_count == 1
        if should_block:
            first_terminal_action_discriminant_hook_entered.set()
            if not allow_first_terminal_action_discriminant.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal action discriminant"
                )

    def before_terminal_record_prefix_detection(_: str) -> None:
        first_terminal_record_prefix_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_action_discriminant = (
        before_terminal_action_discriminant
    )
    backend._stream_debug_before_terminal_record_prefix_detection = (
        before_terminal_record_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_action_discriminant_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_record_prefix_hook_entered.is_set() is False
    assert allow_first_terminal_action_discriminant.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_action_discriminant.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_capture(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_prefix_hook_entered = threading.Event()
    allow_first_terminal_notice_prefix = threading.Event()
    first_terminal_notice_capture_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_prefix_detection(_: str) -> None:
        nonlocal notice_prefix_hook_count
        with hook_lock:
            notice_prefix_hook_count += 1
            should_block = notice_prefix_hook_count == 1
        if should_block:
            first_terminal_notice_prefix_hook_entered.set()
            if not allow_first_terminal_notice_prefix.wait(timeout=2.0):
                raise RuntimeError("timed out waiting to release terminal notice prefix")

    def before_terminal_notice_capture(_: dict[str, object]) -> None:
        first_terminal_notice_capture_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_prefix_detection = (
        before_terminal_notice_prefix_detection
    )
    backend._stream_debug_before_terminal_notice_capture = (
        before_terminal_notice_capture
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_prefix_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_capture_hook_entered.is_set() is False
    assert allow_first_terminal_notice_prefix.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_action_discriminant_hook_entered = threading.Event()
    allow_first_terminal_notice_action_discriminant = threading.Event()
    first_terminal_notice_prefix_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_action_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_action_discriminant(_: str) -> None:
        nonlocal notice_action_hook_count
        with hook_lock:
            notice_action_hook_count += 1
            should_block = notice_action_hook_count == 1
        if should_block:
            first_terminal_notice_action_discriminant_hook_entered.set()
            if not allow_first_terminal_notice_action_discriminant.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice action discriminant"
                )

    def before_terminal_notice_prefix_detection(_: str) -> None:
        first_terminal_notice_prefix_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_action_discriminant = (
        before_terminal_notice_action_discriminant
    )
    backend._stream_debug_before_terminal_notice_prefix_detection = (
        before_terminal_notice_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_action_discriminant_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_prefix_hook_entered.is_set() is False
    assert allow_first_terminal_notice_action_discriminant.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_action_discriminant.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_action_discriminant_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_action_stem_hook_entered = threading.Event()
    allow_first_terminal_notice_action_stem = threading.Event()
    first_terminal_notice_action_discriminant_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_stem_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_action_stem(_: str) -> None:
        nonlocal notice_stem_hook_count
        with hook_lock:
            notice_stem_hook_count += 1
            should_block = notice_stem_hook_count == 1
        if should_block:
            first_terminal_notice_action_stem_hook_entered.set()
            if not allow_first_terminal_notice_action_stem.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice action stem"
                )

    def before_terminal_notice_action_discriminant(_: str) -> None:
        first_terminal_notice_action_discriminant_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_action_stem = (
        before_terminal_notice_action_stem
    )
    backend._stream_debug_before_terminal_notice_action_discriminant = (
        before_terminal_notice_action_discriminant
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_action_stem_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_action_discriminant_hook_entered.is_set() is False
    assert allow_first_terminal_notice_action_stem.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_action_stem.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_action_stem_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_marker_hook_entered = threading.Event()
    allow_first_terminal_notice_marker = threading.Event()
    first_terminal_notice_action_stem_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_marker_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_marker_detection(_: str) -> None:
        nonlocal notice_marker_hook_count
        with hook_lock:
            notice_marker_hook_count += 1
            should_block = notice_marker_hook_count == 1
        if should_block:
            first_terminal_notice_marker_hook_entered.set()
            if not allow_first_terminal_notice_marker.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice marker"
                )

    def before_terminal_notice_action_stem(_: str) -> None:
        first_terminal_notice_action_stem_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_marker_detection = (
        before_terminal_notice_marker_detection
    )
    backend._stream_debug_before_terminal_notice_action_stem = (
        before_terminal_notice_action_stem
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_marker_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_action_stem_hook_entered.is_set() is False
    assert allow_first_terminal_notice_marker.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_marker.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_marker_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "delayed_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_marker_prefix_hook_entered = threading.Event()
    allow_first_terminal_notice_marker_prefix = threading.Event()
    first_terminal_notice_marker_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_marker_prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_marker_prefix_detection(_: str) -> None:
        nonlocal notice_marker_prefix_hook_count
        with hook_lock:
            notice_marker_prefix_hook_count += 1
            should_block = notice_marker_prefix_hook_count == 1
        if should_block:
            first_terminal_notice_marker_prefix_hook_entered.set()
            if not allow_first_terminal_notice_marker_prefix.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice marker prefix"
                )

    def before_terminal_notice_marker_detection(_: str) -> None:
        first_terminal_notice_marker_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_marker_prefix_detection = (
        before_terminal_notice_marker_prefix_detection
    )
    backend._stream_debug_before_terminal_notice_marker_detection = (
        before_terminal_notice_marker_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_marker_prefix_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_marker_hook_entered.is_set() is False
    assert allow_first_terminal_notice_marker_prefix.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_marker_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_marker_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "terminal_notice_marker_prefix_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_marker_stem_hook_entered = threading.Event()
    allow_first_terminal_notice_marker_stem = threading.Event()
    first_terminal_notice_marker_prefix_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_marker_stem_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_marker_stem_detection(_: str) -> None:
        nonlocal notice_marker_stem_hook_count
        with hook_lock:
            notice_marker_stem_hook_count += 1
            should_block = notice_marker_stem_hook_count == 1
        if should_block:
            first_terminal_notice_marker_stem_hook_entered.set()
            if not allow_first_terminal_notice_marker_stem.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice marker stem"
                )

    def before_terminal_notice_marker_prefix_detection(_: str) -> None:
        first_terminal_notice_marker_prefix_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_marker_stem_detection = (
        before_terminal_notice_marker_stem_detection
    )
    backend._stream_debug_before_terminal_notice_marker_prefix_detection = (
        before_terminal_notice_marker_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_marker_stem_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_marker_prefix_hook_entered.is_set() is False
    assert allow_first_terminal_notice_marker_stem.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_marker_stem.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_marker_stem_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "terminal_notice_marker_stem_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_marker_discriminant_hook_entered = threading.Event()
    allow_first_terminal_notice_marker_discriminant = threading.Event()
    first_terminal_notice_marker_stem_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_marker_discriminant_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_marker_discriminant_detection(_: str) -> None:
        nonlocal notice_marker_discriminant_hook_count
        with hook_lock:
            notice_marker_discriminant_hook_count += 1
            should_block = notice_marker_discriminant_hook_count == 1
        if should_block:
            first_terminal_notice_marker_discriminant_hook_entered.set()
            if not allow_first_terminal_notice_marker_discriminant.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice marker discriminant"
                )

    def before_terminal_notice_marker_stem_detection(_: str) -> None:
        first_terminal_notice_marker_stem_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_marker_discriminant_detection = (
        before_terminal_notice_marker_discriminant_detection
    )
    backend._stream_debug_before_terminal_notice_marker_stem_detection = (
        before_terminal_notice_marker_stem_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_marker_discriminant_hook_entered.wait(timeout=0.6)
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_marker_stem_hook_entered.is_set() is False
    assert allow_first_terminal_notice_marker_discriminant.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_marker_discriminant.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_marker_discriminant_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "terminal_notice_marker_discriminant_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_marker_key_lead_hook_entered = threading.Event()
    allow_first_terminal_notice_marker_key_lead = threading.Event()
    first_terminal_notice_marker_discriminant_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_marker_key_lead_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_marker_key_lead_detection(_: str) -> None:
        nonlocal notice_marker_key_lead_hook_count
        with hook_lock:
            notice_marker_key_lead_hook_count += 1
            should_block = notice_marker_key_lead_hook_count == 1
        if should_block:
            first_terminal_notice_marker_key_lead_hook_entered.set()
            if not allow_first_terminal_notice_marker_key_lead.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice marker key lead"
                )

    def before_terminal_notice_marker_discriminant_detection(_: str) -> None:
        first_terminal_notice_marker_discriminant_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_marker_key_lead_detection = (
        before_terminal_notice_marker_key_lead_detection
    )
    backend._stream_debug_before_terminal_notice_marker_discriminant_detection = (
        before_terminal_notice_marker_discriminant_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_marker_key_lead_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_marker_discriminant_hook_entered.is_set() is False
    assert allow_first_terminal_notice_marker_key_lead.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_marker_key_lead.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_marker_key_lead_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_marker_key_lead_hook_entered = threading.Event()
    allow_first_terminal_notice_marker_key_lead = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    notice_marker_key_lead_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_marker_key_lead_detection(_: str) -> None:
        nonlocal notice_marker_key_lead_hook_count
        with hook_lock:
            notice_marker_key_lead_hook_count += 1
            should_block = notice_marker_key_lead_hook_count == 1
        if should_block:
            first_terminal_notice_marker_key_lead_hook_entered.set()
            if not allow_first_terminal_notice_marker_key_lead.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice marker key lead"
                )

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_marker_key_lead_detection = (
        before_terminal_notice_marker_key_lead_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_terminal_notice_marker_key_lead_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert allow_first_terminal_notice_marker_key_lead.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_marker_key_lead.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice_lead', 'terminal_notice_lead': True, 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_hook_entered = threading.Event()
    allow_first_terminal_notice_leading_discriminator = threading.Event()
    first_terminal_notice_marker_key_lead_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_detection(_: str) -> None:
        nonlocal leading_discriminator_hook_count
        with hook_lock:
            leading_discriminator_hook_count += 1
            should_block = leading_discriminator_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator"
                )

    def before_terminal_notice_marker_key_lead_detection(_: str) -> None:
        first_terminal_notice_marker_key_lead_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_detection = (
        before_terminal_notice_leading_discriminator_detection
    )
    backend._stream_debug_before_terminal_notice_marker_key_lead_detection = (
        before_terminal_notice_marker_key_lead_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_hook_entered.wait(timeout=0.6)
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_marker_key_lead_hook_entered.is_set() is False
    assert allow_first_terminal_notice_leading_discriminator.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice_lead', 'terminal_notice_lead': True, 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_prefix_hook_entered = (
        threading.Event()
    )
    allow_first_terminal_notice_leading_discriminator_prefix = threading.Event()
    first_terminal_notice_leading_discriminator_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_prefix_detection(_: str) -> None:
        nonlocal leading_discriminator_prefix_hook_count
        with hook_lock:
            leading_discriminator_prefix_hook_count += 1
            should_block = leading_discriminator_prefix_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_prefix_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator_prefix.wait(
                timeout=2.0
            ):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator prefix"
                )

    def before_terminal_notice_leading_discriminator_detection(_: str) -> None:
        first_terminal_notice_leading_discriminator_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_prefix_detection = (
        before_terminal_notice_leading_discriminator_prefix_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_detection = (
        before_terminal_notice_leading_discriminator_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_prefix_hook_entered.wait(
            timeout=0.6
        )
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_leading_discriminator_hook_entered.is_set() is False
    assert allow_first_terminal_notice_leading_discriminator_prefix.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_stem_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice_lead', 'terminal_notice_lead': True, 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_stem_hook_entered = (
        threading.Event()
    )
    allow_first_terminal_notice_leading_discriminator_stem = threading.Event()
    first_terminal_notice_leading_discriminator_prefix_hook_entered = (
        threading.Event()
    )
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_stem_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_stem_detection(_: str) -> None:
        nonlocal leading_discriminator_stem_hook_count
        with hook_lock:
            leading_discriminator_stem_hook_count += 1
            should_block = leading_discriminator_stem_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_stem_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator_stem.wait(
                timeout=2.0
            ):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator stem"
                )

    def before_terminal_notice_leading_discriminator_prefix_detection(
        _: str,
    ) -> None:
        first_terminal_notice_leading_discriminator_prefix_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_stem_detection = (
        before_terminal_notice_leading_discriminator_stem_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_prefix_detection = (
        before_terminal_notice_leading_discriminator_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_stem_hook_entered.wait(
            timeout=0.6
        )
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_leading_discriminator_prefix_hook_entered.is_set() is False
    assert allow_first_terminal_notice_leading_discriminator_stem.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator_stem.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_discriminant_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'action': 'stream_terminal_notice_lead', 'terminal_notice_lead': True, 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_discriminant_hook_entered = (
        threading.Event()
    )
    allow_first_terminal_notice_leading_discriminator_discriminant = (
        threading.Event()
    )
    first_terminal_notice_leading_discriminator_stem_hook_entered = (
        threading.Event()
    )
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_discriminant_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_discriminant_detection(
        _: str,
    ) -> None:
        nonlocal leading_discriminator_discriminant_hook_count
        with hook_lock:
            leading_discriminator_discriminant_hook_count += 1
            should_block = leading_discriminator_discriminant_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_discriminant_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator_discriminant.wait(
                timeout=2.0
            ):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator discriminant"
                )

    def before_terminal_notice_leading_discriminator_stem_detection(
        _: str,
    ) -> None:
        first_terminal_notice_leading_discriminator_stem_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_discriminant_detection = (
        before_terminal_notice_leading_discriminator_discriminant_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_stem_detection = (
        before_terminal_notice_leading_discriminator_stem_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_discriminant_hook_entered.wait(
            timeout=0.6
        )
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_leading_discriminator_stem_hook_entered.is_set() is False
    assert (
        allow_first_terminal_notice_leading_discriminator_discriminant.is_set()
        is False
    )
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator_discriminant.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_marker_hook_entered = (
        threading.Event()
    )
    allow_first_terminal_notice_leading_discriminator_marker = threading.Event()
    first_terminal_notice_leading_discriminator_discriminant_hook_entered = (
        threading.Event()
    )
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_marker_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_marker_detection(_: str) -> None:
        nonlocal leading_discriminator_marker_hook_count
        with hook_lock:
            leading_discriminator_marker_hook_count += 1
            should_block = leading_discriminator_marker_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_marker_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator_marker.wait(
                timeout=2.0
            ):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator marker"
                )

    def before_terminal_notice_leading_discriminator_discriminant_detection(
        _: str,
    ) -> None:
        first_terminal_notice_leading_discriminator_discriminant_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_detection = (
        before_terminal_notice_leading_discriminator_marker_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_discriminant_detection = (
        before_terminal_notice_leading_discriminator_discriminant_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_marker_hook_entered.wait(
            timeout=0.6
        )
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert (
        first_terminal_notice_leading_discriminator_discriminant_hook_entered.is_set()
        is False
    )
    assert allow_first_terminal_notice_leading_discriminator_marker.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator_marker.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_marker_prefix_hook_entered = (
        threading.Event()
    )
    allow_first_terminal_notice_leading_discriminator_marker_prefix = (
        threading.Event()
    )
    first_terminal_notice_leading_discriminator_marker_hook_entered = (
        threading.Event()
    )
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_marker_prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_marker_prefix_detection(
        _: str,
    ) -> None:
        nonlocal leading_discriminator_marker_prefix_hook_count
        with hook_lock:
            leading_discriminator_marker_prefix_hook_count += 1
            should_block = leading_discriminator_marker_prefix_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_marker_prefix_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator_marker_prefix.wait(
                timeout=2.0
            ):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator marker prefix"
                )

    def before_terminal_notice_leading_discriminator_marker_detection(
        _: str,
    ) -> None:
        first_terminal_notice_leading_discriminator_marker_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_prefix_detection = (
        before_terminal_notice_leading_discriminator_marker_prefix_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_detection = (
        before_terminal_notice_leading_discriminator_marker_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_marker_prefix_hook_entered.wait(
            timeout=0.6
        )
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert first_terminal_notice_leading_discriminator_marker_hook_entered.is_set() is False
    assert (
        allow_first_terminal_notice_leading_discriminator_marker_prefix.is_set()
        is False
    )
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator_marker_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_stem_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_marker_stem_hook_entered = (
        threading.Event()
    )
    allow_first_terminal_notice_leading_discriminator_marker_stem = (
        threading.Event()
    )
    first_terminal_notice_leading_discriminator_marker_prefix_hook_entered = (
        threading.Event()
    )
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_marker_stem_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_marker_stem_detection(
        _: str,
    ) -> None:
        nonlocal leading_discriminator_marker_stem_hook_count
        with hook_lock:
            leading_discriminator_marker_stem_hook_count += 1
            should_block = leading_discriminator_marker_stem_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_marker_stem_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator_marker_stem.wait(
                timeout=2.0
            ):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator marker stem"
                )

    def before_terminal_notice_leading_discriminator_marker_prefix_detection(
        _: str,
    ) -> None:
        first_terminal_notice_leading_discriminator_marker_prefix_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_stem_detection = (
        before_terminal_notice_leading_discriminator_marker_stem_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_prefix_detection = (
        before_terminal_notice_leading_discriminator_marker_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_marker_stem_hook_entered.wait(
            timeout=0.6
        )
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert (
        first_terminal_notice_leading_discriminator_marker_prefix_hook_entered.is_set()
        is False
    )
    assert allow_first_terminal_notice_leading_discriminator_marker_stem.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator_marker_stem.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_discriminant_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_terminal_notice_leading_discriminator_marker_discriminant_hook_entered = (
        threading.Event()
    )
    allow_first_terminal_notice_leading_discriminator_marker_discriminant = (
        threading.Event()
    )
    first_terminal_notice_leading_discriminator_marker_stem_hook_entered = (
        threading.Event()
    )
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    leading_discriminator_marker_discriminant_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_terminal_notice_leading_discriminator_marker_discriminant_detection(
        _: str,
    ) -> None:
        nonlocal leading_discriminator_marker_discriminant_hook_count
        with hook_lock:
            leading_discriminator_marker_discriminant_hook_count += 1
            should_block = leading_discriminator_marker_discriminant_hook_count == 1
        if should_block:
            first_terminal_notice_leading_discriminator_marker_discriminant_hook_entered.set()
            if not allow_first_terminal_notice_leading_discriminator_marker_discriminant.wait(
                timeout=2.0
            ):
                raise RuntimeError(
                    "timed out waiting to release terminal notice leading discriminator marker discriminant"
                )

    def before_terminal_notice_leading_discriminator_marker_stem_detection(
        _: str,
    ) -> None:
        first_terminal_notice_leading_discriminator_marker_stem_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_discriminant_detection = (
        before_terminal_notice_leading_discriminator_marker_discriminant_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_stem_detection = (
        before_terminal_notice_leading_discriminator_marker_stem_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert (
        first_terminal_notice_leading_discriminator_marker_discriminant_hook_entered.wait(
            timeout=0.6
        )
        is True
    )
    assert second_request_written.wait(timeout=0.3) is True
    assert (
        first_terminal_notice_leading_discriminator_marker_stem_hook_entered.is_set()
        is False
    )
    assert (
        allow_first_terminal_notice_leading_discriminator_marker_discriminant.is_set()
        is False
    )
    assert first_terminal_event_consumed.is_set() is False
    allow_first_terminal_notice_leading_discriminator_marker_discriminant.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_earlier_runtime_owned_discriminator_hook_entered = threading.Event()
    allow_first_earlier_runtime_owned_discriminator = threading.Event()
    first_terminal_notice_leading_discriminator_marker_discriminant_hook_entered = (
        threading.Event()
    )
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    earlier_runtime_owned_discriminator_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_earlier_runtime_owned_discriminator_detection(_: str) -> None:
        nonlocal earlier_runtime_owned_discriminator_hook_count
        with hook_lock:
            earlier_runtime_owned_discriminator_hook_count += 1
            should_block = earlier_runtime_owned_discriminator_hook_count == 1
        if should_block:
            first_earlier_runtime_owned_discriminator_hook_entered.set()
            if not allow_first_earlier_runtime_owned_discriminator.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned discriminator"
                )

    def before_terminal_notice_leading_discriminator_marker_discriminant_detection(
        _: str,
    ) -> None:
        first_terminal_notice_leading_discriminator_marker_discriminant_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection = (
        before_earlier_runtime_owned_discriminator_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_discriminant_detection = (
        before_terminal_notice_leading_discriminator_marker_discriminant_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_earlier_runtime_owned_discriminator_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert (
        first_terminal_notice_leading_discriminator_marker_discriminant_hook_entered.is_set()
        is False
    )
    assert allow_first_earlier_runtime_owned_discriminator.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_earlier_runtime_owned_discriminator.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_prefix_hook_entered = threading.Event()
    allow_first_prefix = threading.Event()
    first_earlier_runtime_owned_discriminator_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_prefix_detection(_: str) -> None:
        nonlocal prefix_hook_count
        with hook_lock:
            prefix_hook_count += 1
            should_block = prefix_hook_count == 1
        if should_block:
            first_prefix_hook_entered.set()
            if not allow_first_prefix.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned discriminator prefix"
                )

    def before_earlier_runtime_owned_discriminator_detection(_: str) -> None:
        first_earlier_runtime_owned_discriminator_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection = (
        before_prefix_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection = (
        before_earlier_runtime_owned_discriminator_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_prefix_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert (
        first_earlier_runtime_owned_discriminator_hook_entered.is_set() is False
    )
    assert allow_first_prefix.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_stem_hook_entered = threading.Event()
    allow_first_stem = threading.Event()
    first_prefix_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    second_request_written_before_first_terminal_event_consumed = False
    stem_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_stem_detection(_: str) -> None:
        nonlocal stem_hook_count
        with hook_lock:
            stem_hook_count += 1
            should_block = stem_hook_count == 1
        if should_block:
            first_stem_hook_entered.set()
            if not allow_first_stem.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned discriminator stem"
                )

    def before_prefix_detection(_: str) -> None:
        first_prefix_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        nonlocal second_request_written_before_first_terminal_event_consumed
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written_before_first_terminal_event_consumed = (
                not first_terminal_event_consumed.is_set()
            )
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection = (
        before_stem_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection = (
        before_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_stem_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_prefix_hook_entered.is_set() is False
    assert allow_first_stem.is_set() is False
    assert second_request_written_before_first_terminal_event_consumed is True
    allow_first_stem.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_generate_messages_reuses_same_child(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    result = backend.generate_messages(
        "model-a",
        [ChatTurn(role="system", content="be terse"), ChatTurn(role="user", content="hello")],
        max_tokens=4,
    )

    assert result.ok is True
    assert result.text == "system:be terse | user:hello :: child"
    assert result.detail["message_count"] == 2
    backend.unload("model-a")


def test_subprocess_backend_generate_cohort_uses_single_child_exchange(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    result = backend.generate_cohort("model-a", ["hello", "again"], max_tokens=4)

    assert result.ok is True
    assert [item.text for item in result.results] == [
        "hello :: child",
        "again :: child",
    ]
    assert result.detail["batch_size"] == 2
    assert result.detail["exchange_count"] == 1
    status = backend.status()
    assert (
        status.detail["cache_runtime_observations"]["child_exchange_mode"]
        == "aggregated_non_stream_child_exchange_visible"
    )
    assert (
        status.detail["cache_runtime_observations"]["aggregated_child_exchange_batch_count"]
        == 1
    )
    assert (
        status.detail["cache_runtime_observations"]["aggregated_child_exchange_request_count"]
        == 2
    )
    assert status.detail["cache_runtime_observations"]["max_aggregated_child_batch_size"] == 2
    backend.unload("model-a")


def test_subprocess_backend_stream_generate_messages_reuses_same_child(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    events = list(
        backend.stream_generate_messages(
            "model-a",
            [ChatTurn(role="user", content="hello"), ChatTurn(role="assistant", content="hi")],
            max_tokens=4,
        )
    )

    assert [event.event for event in events] == ["token", "done"]
    assert events[0].text == "user:hello | assistant:hi"
    assert events[0].detail["message_count"] == 2
    assert events[0].detail["timing"]["prompt_render_ms"] == 2.0
    assert events[1].detail["timing"]["stream_wall_ms"] == 13.0
    backend.unload("model-a")


def test_subprocess_backend_stream_generate_messages_yields_prefill_progress(
    tmp_path: Path,
) -> None:
    runner = _write_prefill_progress_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    events = list(
        backend.stream_generate_messages(
            "model-a",
            [ChatTurn(role="user", content="hello")],
            max_tokens=4,
            prefill_chunk_tokens=512,
        )
    )

    assert [event.event for event in events] == ["prefill_progress", "token", "done"]
    assert events[0].detail["processed"] == 2048
    assert events[0].detail["total"] == 4096
    assert events[0].detail["ratio"] == 0.5
    assert events[0].detail["message_count"] == 1
    assert events[0].detail["received_prefill_chunk_tokens"] == 512
    backend.unload("model-a")


def test_subprocess_backend_status_performs_ping_health_probe(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    status = backend.status()

    assert status.healthy is True
    assert status.detail["child_health"]["model-a"]["ok"] is True
    assert status.detail["child_health"]["model-a"]["pid"] == status.detail["children"]["model-a"]["pid"]
    backend.unload("model-a")


def test_subprocess_backend_generate_requires_loaded_model(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )

    result = backend.generate("missing", "hello")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.model_not_loaded


def test_subprocess_backend_reports_child_failure(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path, error_on_generate=True)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    result = backend.generate("model-a", "hello")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error
    assert "child boom" in result.message
    assert backend.status().healthy is False
    backend.unload("model-a")


def test_subprocess_backend_unload_stops_persistent_child(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)
    child_pid = backend.status().detail["children"]["model-a"]["pid"]

    result = backend.unload("model-a")

    assert result.ok is True
    assert result.freed_gb == 2.0
    assert child_pid is not None
    assert backend.status().loaded_models == ()
    assert backend.status().detail["children"] == {}


def test_subprocess_backend_successful_unload_clears_prior_latched_error(
    tmp_path: Path,
) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)
    backend._last_error = "prior transport parse error"  # noqa: SLF001

    result = backend.unload("model-a")

    assert result.ok is True
    status = backend.status()
    assert status.healthy is True
    assert status.detail["last_error"] is None
    assert status.detail["last_subprocess"]["ok"] is True


def test_runtime_kernel_can_use_subprocess_backend(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    kernel = RuntimeKernel(backend)

    loaded = kernel.load_model("model-a", memory_gb=2.0)
    first = asyncio.run(kernel.generate("hello", max_tokens=4))
    second = asyncio.run(kernel.generate("again", max_tokens=4))

    assert loaded.ok is True
    assert first.ok is True
    assert second.ok is True
    assert first.detail["pid"] == second.detail["pid"]
    assert kernel.status_dict()["backend"]["backend_name"] == "mlx-lm-subprocess"
    kernel.unload_model("model-a")


def test_real_runner_missing_mlx_lm_returns_structured_load_failure() -> None:
    backend = MlxLmSubprocessBackend(
        python_executable=sys.executable,
        runner_module="owlmlx.runtime.mlx_lm_runner",
        timeout_s=20.0,
    )

    loaded = backend.load("model-a", memory_gb=1.0)

    assert loaded.ok is False
    assert loaded.error_code is RuntimeErrorCode.backend_error
    assert "subprocess load failed" in loaded.message


def test_subprocess_backend_reports_empty_child_output(tmp_path: Path) -> None:
    runner = tmp_path / "empty_runner.py"
    runner.write_text(
        "raise SystemExit(9)\n",
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )

    loaded = backend.load("model-a", memory_gb=1.0)

    assert loaded.ok is False
    assert loaded.error_code is RuntimeErrorCode.backend_error
    assert "child process produced no output" in loaded.message


def test_subprocess_backend_drops_dead_child_after_generate_crash(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path, crash_on_generate=True)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=1.0)
    assert loaded.ok is True

    result = backend.generate("model-a", "hello")

    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error
    assert backend.status().detail["children"] == {}
    assert backend.status().healthy is False


def test_subprocess_backend_auto_restarts_dead_child_on_next_generate(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path, crash_on_generate=True)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
        max_restart_attempts=2,
    )
    loaded = backend.load("model-a", memory_gb=1.0)
    assert loaded.ok is True

    first = backend.generate("model-a", "hello")
    assert first.ok is False

    ok_runner = _write_runner(tmp_path, ok=True)
    backend.runner_module = ok_runner

    second = backend.generate("model-a", "again")

    assert second.ok is True
    status = backend.status()
    assert status.detail["children"]["model-a"]["restart_count"] == 1
    assert status.detail["child_health"]["model-a"]["ok"] is True
    backend.unload("model-a")


def test_subprocess_backend_status_reports_restartable_model_after_dead_child(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path, crash_on_generate=True)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
        max_restart_attempts=2,
    )
    loaded = backend.load("model-a", memory_gb=1.0)
    assert loaded.ok is True

    result = backend.generate("model-a", "hello")
    assert result.ok is False

    status = backend.status()
    assert status.detail["recoverability"]["restartable_models"] == ["model-a"]
    assert status.detail["recoverability"]["restart_exhausted_models"] == []
    assert status.detail["dead_registered_models"] == ["model-a"]


def test_subprocess_backend_unload_clears_stale_registration_after_dead_child(
    tmp_path: Path,
) -> None:
    runner = _write_runner(tmp_path, crash_on_generate=True)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
        max_restart_attempts=2,
    )
    loaded = backend.load("model-a", memory_gb=1.0)
    assert loaded.ok is True

    result = backend.generate("model-a", "hello")
    assert result.ok is False
    ghost_status = backend.status()
    assert ghost_status.healthy is False
    assert ghost_status.loaded_models[0].model_id == "model-a"
    assert ghost_status.detail["children"] == {}
    assert ghost_status.detail["dead_registered_models"] == ["model-a"]

    unloaded = backend.unload("model-a")

    assert unloaded.ok is True
    assert unloaded.message == "cleared stale subprocess registration: model-a"
    assert unloaded.freed_gb == 1.0
    assert unloaded.detail["stale_registration_cleared"] is True
    recovered_status = backend.status()
    assert recovered_status.healthy is True
    assert recovered_status.loaded_models == ()
    assert recovered_status.detail["dead_registered_models"] == []
    assert recovered_status.detail["recoverability"]["restartable_models"] == []


def test_subprocess_backend_classifies_metal_oom_child_loss(tmp_path: Path) -> None:
    runner = _write_metal_oom_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
        max_restart_attempts=2,
    )
    loaded = backend.load("model-a", memory_gb=1.0)
    assert loaded.ok is True

    result = backend.generate("model-a", "hello")

    assert result.ok is False
    status = backend.status()
    assert status.detail["last_failure_class"] == "metal_oom"
    assert status.detail["dead_registered_models"] == ["model-a"]
    unloaded = backend.unload("model-a")
    assert unloaded.ok is True
    assert unloaded.detail["previous_failure_class"] == "metal_oom"


def test_kernel_unload_clears_active_model_after_dead_subprocess_registration(
    tmp_path: Path,
) -> None:
    runner = _write_runner(tmp_path, crash_on_generate=True)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
        max_restart_attempts=2,
    )
    kernel = RuntimeKernel(backend)
    loaded = kernel.load_model("model-a", memory_gb=1.0)
    assert loaded.ok is True
    assert kernel.active_model_id == "model-a"

    failed = asyncio.run(kernel.generate("hello"))
    assert failed.ok is False
    ghost_status = kernel.status_dict()
    assert ghost_status["backend"]["detail"]["dead_registered_models"] == ["model-a"]
    assert ghost_status["active_model_id"] == "model-a"

    unloaded = kernel.unload_model("model-a")

    assert unloaded.ok is True
    assert unloaded.detail["stale_registration_cleared"] is True
    assert kernel.active_model_id is None
    recovered_status = kernel.status_dict()
    assert recovered_status["backend"]["loaded_models"] == []
    assert recovered_status["backend"]["detail"]["dead_registered_models"] == []
    assert recovered_status["summary"]["readiness"] != "blocked"


def test_kernel_blocks_new_load_during_metal_oom_cooldown(tmp_path: Path) -> None:
    clock_state, clock = _clock_box()
    runner = _write_metal_oom_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
        max_restart_attempts=2,
    )
    kernel = RuntimeKernel(backend, clock=clock)
    loaded = kernel.load_model("model-a", memory_gb=1.0)
    assert loaded.ok is True

    failed = asyncio.run(kernel.generate("hello"))
    assert failed.ok is False
    assert kernel.status_dict()["backend"]["detail"]["dead_registered_models"] == ["model-a"]
    stale_blocked = kernel.load_model("model-b", memory_gb=1.0)
    assert stale_blocked.ok is False
    assert (
        stale_blocked.detail["recovery_barrier"]["reason_code"]
        == "dead_registered_models_require_unload"
    )

    cleared = kernel.unload_model("model-a")
    assert cleared.ok is True
    cooldown_blocked = kernel.load_model("model-b", memory_gb=1.0)

    assert cooldown_blocked.ok is False
    assert cooldown_blocked.error_code is RuntimeErrorCode.backend_error
    cooldown = cooldown_blocked.detail["memory_pressure_cooldown"]
    assert cooldown["active"] is True
    assert cooldown["reason_code"] == "metal_oom_child_loss_cooldown"
    assert kernel.status_dict()["memory_pressure_cooldown"]["active"] is True

    clock_state["now"] += 121.0
    ok_after_cooldown = kernel.load_model("model-b", memory_gb=1.0)

    assert ok_after_cooldown.ok is True
    assert kernel.status_dict()["memory_pressure_cooldown"]["active"] is False
    kernel.unload_model("model-b")


def test_subprocess_backend_status_reports_restart_exhausted_model(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path, crash_on_generate=True)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
        max_restart_attempts=0,
    )
    loaded = backend.load("model-a", memory_gb=1.0)
    assert loaded.ok is True

    result = backend.generate("model-a", "hello")
    assert result.ok is False

    status = backend.status()
    assert status.detail["recoverability"]["restartable_models"] == []
    assert status.detail["recoverability"]["restart_exhausted_models"] == ["model-a"]


def test_subprocess_backend_survives_repeated_restart_generate_unload_cycles(tmp_path: Path) -> None:
    runner = _write_runner(tmp_path)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    kernel = RuntimeKernel(backend)

    for index in range(3):
        model_id = f"model-{index}"
        loaded = kernel.load_model(model_id, memory_gb=1.0)
        assert loaded.ok is True

        generated = asyncio.run(kernel.generate(f"hello-{index}", max_tokens=4))
        assert generated.ok is True
        assert generated.text == f"hello-{index} :: child"

        restarted = kernel.restart_model(model_id)
        assert restarted.ok is True
        assert restarted.model_id == model_id

        generated_after_restart = asyncio.run(kernel.generate(f"again-{index}", max_tokens=4))
        assert generated_after_restart.ok is True
        assert generated_after_restart.text == f"again-{index} :: child"

        unloaded = kernel.unload_model(model_id)
        assert unloaded.ok is True

    status = backend.status()
    assert status.loaded_models == ()
    assert status.detail["children"] == {}


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_boundary': True, 'action': 'stream_runtime_owned_terminal_boundary', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_leading_discriminator': True, 'action': 'stream_runtime_owned_terminal_leading_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_boundary_hook_entered = threading.Event()
    allow_first_boundary = threading.Event()
    first_leading_discriminator_discriminant_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    boundary_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_boundary_detection(_: str) -> None:
        nonlocal boundary_hook_count
        with hook_lock:
            boundary_hook_count += 1
            should_block = boundary_hook_count == 1
        if should_block:
            first_boundary_hook_entered.set()
            if not allow_first_boundary.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned boundary"
                )

    def before_leading_discriminator_discriminant_detection(_: str) -> None:
        first_leading_discriminator_discriminant_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection = (
        before_boundary_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection = (
        before_leading_discriminator_discriminant_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_boundary_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_leading_discriminator_discriminant_hook_entered.is_set() is False
    assert allow_first_boundary.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_boundary.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_boundary': True, 'action': 'stream_runtime_owned_terminal_boundary', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_leading_discriminator': True, 'action': 'stream_runtime_owned_terminal_leading_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_prefix_hook_entered = threading.Event()
    allow_first_prefix = threading.Event()
    first_boundary_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    prefix_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_prefix_detection(_: str) -> None:
        nonlocal prefix_hook_count
        with hook_lock:
            prefix_hook_count += 1
            should_block = prefix_hook_count == 1
        if should_block:
            first_prefix_hook_entered.set()
            if not allow_first_prefix.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned boundary prefix"
                )

    def before_boundary_detection(_: str) -> None:
        first_boundary_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection = (
        before_prefix_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection = (
        before_boundary_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_prefix_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_boundary_hook_entered.is_set() is False
    assert allow_first_prefix.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_prefix.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


def test_subprocess_backend_releases_stream_lock_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys, time",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        print(json.dumps({'ok': True, 'action': 'load', 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        time.sleep(0.18)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_boundary': True, 'action': 'stream_runtime_owned_terminal_boundary', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_leading_discriminator': True, 'action': 'stream_runtime_owned_terminal_leading_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'runtime_owned_terminal_notice_discriminator': True, 'action': 'stream_runtime_owned_terminal_notice_discriminator', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice_lead': True, 'action': 'stream_terminal_notice_lead', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    loaded = backend.load("model-a", memory_gb=2.0)
    assert loaded.ok is True

    first_token_seen = threading.Event()
    first_stem_hook_entered = threading.Event()
    allow_first_stem = threading.Event()
    first_prefix_hook_entered = threading.Event()
    first_terminal_event_consumed = threading.Event()
    second_request_written = threading.Event()
    second_token_seen = threading.Event()
    stem_hook_count = 0
    request_write_count = 0
    hook_lock = threading.Lock()
    first_events: list[str] = []
    second_events: list[str] = []

    def before_stem_detection(_: str) -> None:
        nonlocal stem_hook_count
        with hook_lock:
            stem_hook_count += 1
            should_block = stem_hook_count == 1
        if should_block:
            first_stem_hook_entered.set()
            if not allow_first_stem.wait(timeout=2.0):
                raise RuntimeError(
                    "timed out waiting to release earlier runtime-owned boundary stem"
                )

    def before_prefix_detection(_: str) -> None:
        first_prefix_hook_entered.set()

    def after_request_write(request: dict[str, object]) -> None:
        nonlocal request_write_count
        if str(request.get("action") or "") != "stream_generate":
            return
        with hook_lock:
            request_write_count += 1
            is_second_request = request_write_count == 2
        if is_second_request:
            second_request_written.set()

    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection = (
        before_stem_detection
    )
    backend._stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection = (
        before_prefix_detection
    )
    backend._stream_debug_after_request_write = after_request_write

    def run_first() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            first_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()
            if event.event == "done":
                first_terminal_event_consumed.set()

    def run_second() -> None:
        for event in backend.stream_generate("model-a", "again", max_tokens=4):
            second_events.append(event.event)
            if event.event == "token":
                second_token_seen.set()

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)
    first_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    second_thread.start()
    assert second_request_written.wait(timeout=0.05) is False
    assert first_stem_hook_entered.wait(timeout=0.6) is True
    assert second_request_written.wait(timeout=0.3) is True
    assert first_prefix_hook_entered.is_set() is False
    assert allow_first_stem.is_set() is False
    assert first_terminal_event_consumed.is_set() is False
    allow_first_stem.set()
    assert second_token_seen.wait(timeout=2.0) is True
    first_thread.join(timeout=2.0)
    second_thread.join(timeout=2.0)

    assert first_events == ["token", "done"]
    assert second_events == ["token", "done"]
    backend.unload("model-a")


# ---------------------------------------------------------------------------
# Non-JSON line resilience (stream transport blocker regression)
# ---------------------------------------------------------------------------

def _write_non_json_stream_runner(tmp_path: Path, *, inject_on_count: int = 1) -> str:
    """Runner that injects a non-JSON line mid-stream on the N-th stream_generate call."""
    module = tmp_path / "non_json_stream_runner.py"
    module.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "loaded = None",
                "count = 0",
                f"inject_on = {inject_on_count}",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        loaded = req['model_id']",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        timing = {'surface': 'owlmlx.child_stream_timing', 'version': 'v1', 'first_response_ms': 5.0, 'first_visible_token_ms': 6.0, 'stream_wall_ms': 7.0}",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming', 'timing': timing}), flush=True)",
                "        if count == inject_on:",
                "            print('100%|########| 27/27 [00:02<00:00, 9.1it/s]', flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop', 'timing': timing}), flush=True)",
                "    elif action == 'ping':",
                "        print(json.dumps({'ok': True, 'action': 'ping', 'model_id': loaded, 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    return module.stem


def test_subprocess_backend_skips_non_json_line_mid_stream(tmp_path: Path) -> None:
    """A non-JSON line between token and done is skipped; stream completes cleanly."""
    runner = _write_non_json_stream_runner(tmp_path, inject_on_count=1)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    events = list(backend.stream_generate("model-a", "hello", max_tokens=4))

    assert [e.event for e in events] == ["token", "done"], events
    assert events[0].text == "hello"
    assert events[0].error_code is None
    assert len(backend._stream_transport_non_json_lines) == 1
    assert "100%" in backend._stream_transport_non_json_lines[0]
    backend.unload("model-a")


def test_subprocess_backend_repeated_stream_non_json_second_run_succeeds(
    tmp_path: Path,
) -> None:
    """Two consecutive stream_generate calls succeed when the second emits a non-JSON line."""
    runner = _write_non_json_stream_runner(tmp_path, inject_on_count=2)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    first_events = list(backend.stream_generate("model-a", "run1", max_tokens=4))
    second_events = list(backend.stream_generate("model-a", "run2", max_tokens=4))

    assert [e.event for e in first_events] == ["token", "done"]
    assert first_events[0].error_code is None
    assert [e.event for e in second_events] == ["token", "done"], second_events
    assert second_events[0].error_code is None
    assert len(backend._stream_transport_non_json_lines) == 1
    backend.unload("model-a")


def test_subprocess_backend_non_json_lines_captured_in_attribute(
    tmp_path: Path,
) -> None:
    """_stream_transport_non_json_lines captures benign non-JSON stdout diagnostics."""
    runner = _write_non_json_stream_runner(tmp_path, inject_on_count=1)
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    list(backend.stream_generate("model-a", "a", max_tokens=2))
    list(backend.stream_generate("model-a", "b", max_tokens=2))

    assert len(backend._stream_transport_non_json_lines) == 1
    assert len(backend._stream_transport_non_json_diagnostics) == 1
    assert (
        backend._stream_transport_non_json_diagnostics[0]["classification"]
        == "benign_child_stdout_noise"
    )
    backend.unload("model-a")


def _write_corrupt_terminal_stream_runner(
    tmp_path: Path,
    *,
    recoverable_embedded_done: bool,
) -> str:
    """Runner that emits a malformed terminal transport line after a token."""
    module = tmp_path / "corrupt_terminal_stream_runner.py"
    terminal_line = (
        "'{\"ok\": true, ' + json.dumps(done)"
        if recoverable_embedded_done
        else "'{\"ok\": true, \"action\": \"stream_done\",'"
    )
    module.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "loaded = None",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        loaded = req['model_id']",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        timing = {'surface': 'owlmlx.child_stream_timing', 'version': 'v1', 'first_response_ms': 5.0, 'first_visible_token_ms': 6.0, 'stream_wall_ms': 7.0}",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming', 'timing': timing}), flush=True)",
                "        done = {'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop', 'timing': timing}",
                f"        print({terminal_line}, flush=True)",
                "    elif action == 'ping':",
                "        print(json.dumps({'ok': True, 'action': 'ping', 'model_id': loaded, 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    return module.stem


def test_subprocess_backend_recovers_embedded_terminal_payload(
    tmp_path: Path,
) -> None:
    """A malformed prefix plus embedded done record is recovered with diagnostics."""
    runner = _write_corrupt_terminal_stream_runner(
        tmp_path,
        recoverable_embedded_done=True,
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    events = list(backend.stream_generate("model-a", "hello", max_tokens=4))

    assert [event.event for event in events] == ["token", "done"]
    assert events[-1].completion_tokens == 1
    assert len(backend._stream_transport_non_json_diagnostics) == 1
    diagnostic = backend._stream_transport_non_json_diagnostics[0]
    assert diagnostic["classification"] == (
        "partial_json_framing_recovered_terminal_payload"
    )
    assert diagnostic["recovered_terminal_payload"] is True
    backend.unload("model-a")


def test_subprocess_backend_corrupt_json_transport_is_not_marked_success(
    tmp_path: Path,
) -> None:
    """Unrecoverable JSON-looking transport corruption yields an error event."""
    runner = _write_corrupt_terminal_stream_runner(
        tmp_path,
        recoverable_embedded_done=False,
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    events = list(backend.stream_generate("model-a", "hello", max_tokens=4))

    assert [event.event for event in events] == ["token", "error"]
    assert "stream transport corrupted JSON terminal record" in str(events[-1].detail)
    assert len(backend._stream_transport_non_json_diagnostics) == 1
    assert (
        backend._stream_transport_non_json_diagnostics[0]["classification"]
        == "corrupt_json_transport_record"
    )
    backend.unload("model-a")


def test_subprocess_backend_status_probe_waits_for_stream_stdout_lock(
    tmp_path: Path,
) -> None:
    """Health probes must not read shared stdout while a stream drains terminal records."""
    runner = tmp_path / "status_probe_during_stream_runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "loaded = None",
                "count = 0",
                "for line in sys.stdin:",
                "    req = json.loads(line)",
                "    action = req.get('action')",
                "    if action == 'load':",
                "        loaded = req['model_id']",
                "        count = 0",
                "        print(json.dumps({'ok': True, 'action': 'load', 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "    elif action == 'stream_generate':",
                "        count += 1",
                "        print(json.dumps({'ok': True, 'action': 'stream_event', 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                "        print(json.dumps({'ok': True, 'terminal_notice': True, 'action': 'stream_terminal_notice', 'terminal_action': 'stream_done', 'pid': os.getpid(), 'sequence': 1}), flush=True)",
                "        print(json.dumps({'ok': True, 'action': 'stream_done', 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                "    elif action == 'ping':",
                "        print(json.dumps({'ok': True, 'action': 'ping', 'model_id': loaded, 'pid': os.getpid(), 'generation_count': count}), flush=True)",
                "    elif action in ('shutdown', 'unload'):",
                "        print(json.dumps({'ok': True, 'action': action, 'model_id': loaded, 'pid': os.getpid()}), flush=True)",
                "        break",
                "    else:",
                "        print(json.dumps({'ok': False, 'error': 'unsupported action'}), flush=True)",
            ]
        ),
        encoding="utf-8",
    )
    backend = MlxLmSubprocessBackend(
        runner_module=runner.stem,
        extra_pythonpath=(str(tmp_path),),
    )
    backend.load("model-a", memory_gb=2.0)

    first_token_seen = threading.Event()
    terminal_notice_capture_entered = threading.Event()
    allow_terminal_notice = threading.Event()
    status_finished = threading.Event()
    stream_events: list[str] = []
    status_holder: list[object] = []

    def before_terminal_notice_capture(_: dict[str, object]) -> None:
        terminal_notice_capture_entered.set()
        if not allow_terminal_notice.wait(timeout=2.0):
            raise RuntimeError("timed out waiting to release terminal notice")

    backend._stream_debug_before_terminal_notice_capture = before_terminal_notice_capture

    def run_stream() -> None:
        for event in backend.stream_generate("model-a", "hello", max_tokens=4):
            stream_events.append(event.event)
            if event.event == "token":
                first_token_seen.set()

    def run_status() -> None:
        status_holder.append(backend.status())
        status_finished.set()

    stream_thread = threading.Thread(target=run_stream)
    status_thread = threading.Thread(target=run_status)
    stream_thread.start()
    assert first_token_seen.wait(timeout=2.0) is True
    assert terminal_notice_capture_entered.wait(timeout=2.0) is True

    status_thread.start()
    assert status_finished.wait(timeout=0.1) is False
    allow_terminal_notice.set()

    stream_thread.join(timeout=2.0)
    status_thread.join(timeout=2.0)

    assert stream_events == ["token", "done"]
    assert status_finished.is_set() is True
    assert status_holder
    assert status_holder[0].healthy is True
    assert len(backend._stream_transport_non_json_diagnostics) == 0
    backend.unload("model-a")


def test_subprocess_backend_non_json_diagnostics_are_capped() -> None:
    """Malformed stdout diagnostics are bounded by a fixed ring buffer."""
    backend = MlxLmSubprocessBackend()

    for index in range(40):
        backend._record_stream_transport_non_json_line(
            f"noise-{index}",
            classification="benign_child_stdout_noise",
        )

    assert len(backend._stream_transport_non_json_lines) == 32
    assert len(backend._stream_transport_non_json_diagnostics) == 32
    assert backend._stream_transport_non_json_lines[0] == "noise-8"
    assert backend._stream_transport_non_json_diagnostics[-1]["preview"] == "noise-39"
