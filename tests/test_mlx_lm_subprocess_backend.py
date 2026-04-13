from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from owlmlx.runtime import MlxLmSubprocessBackend, RuntimeErrorCode, RuntimeKernel
from owlmlx.runtime.types import ChatTurn


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
                "'generation_count': count}), flush=True)"
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
                    "    elif action == 'generate_messages':",
                    "        count += 1",
                    "        text = ' | '.join(f\"{m['role']}:{m['content']}\" for m in req.get('messages', []))",
                    "        print(json.dumps({'ok': True, 'action': 'generate_messages', 'text': text + ' :: child', 'pid': os.getpid(), 'generation_count': count, 'message_count': len(req.get('messages', []))}), flush=True)",
                    "    elif action == 'stream_generate':",
                    "        count += 1",
                    "        print(json.dumps({'ok': True, 'event': 'token', 'text': req['prompt'], 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming'}), flush=True)",
                    "        print(json.dumps({'ok': True, 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop'}), flush=True)",
                    "    elif action == 'stream_generate_messages':",
                    "        count += 1",
                    "        text = ' | '.join(f\"{m['role']}:{m['content']}\" for m in req.get('messages', []))",
                    "        print(json.dumps({'ok': True, 'event': 'token', 'text': text, 'pid': os.getpid(), 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'streaming', 'message_count': len(req.get('messages', []))}), flush=True)",
                    "        print(json.dumps({'ok': True, 'event': 'done', 'pid': os.getpid(), 'generation_count': count, 'sequence': 1, 'prompt_tokens': 1, 'completion_tokens': 1, 'finish_reason': 'stop', 'message_count': len(req.get('messages', []))}), flush=True)",
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
    assert backend.status().detail["children"]["model-a"]["generation_count"] == 1
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
