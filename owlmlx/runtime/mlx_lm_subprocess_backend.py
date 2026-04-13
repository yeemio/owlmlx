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
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from .types import (
    BackendStatus,
    ChatTurn,
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
    last_payload: dict[str, Any] | None = None
    last_error: str | None = None
    stderr_thread: threading.Thread | None = None

    @property
    def pid(self) -> int | None:
        return self.proc.pid


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


class MlxLmSubprocessBackend:
    """RuntimeBackend that isolates mlx-lm execution in persistent child processes."""

    name = "mlx-lm-subprocess"

    def __init__(
        self,
        *,
        python_executable: str | None = None,
        env_overrides: dict[str, str] | None = None,
        runner_module: str = "owlmlx.runtime.mlx_lm_runner",
        timeout_s: float = 600.0,
        health_probe_timeout_s: float = 2.0,
        auto_restart_dead_session: bool = True,
        max_restart_attempts: int = 1,
        extra_pythonpath: tuple[str, ...] = (),
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.env_overrides = dict(env_overrides or {})
        self.runner_module = runner_module
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

    def load(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        if model_id in self._registrations:
            return LoadResult(
                ok=False,
                message=f"model already loaded: {model_id}",
                error_code=RuntimeErrorCode.model_already_loaded,
                model=self._registrations[model_id],
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
                "model_id": model_id,
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
            with self._io_lock:
                if proc.stdin is None:
                    raise ValueError("child stdin pipe is unavailable")
                proc.stdin.write(json.dumps(request) + "\n")
                proc.stdin.flush()
                payload, discarded = self._read_payload_line(session, timeout_s=timeout_s)
        except Exception as exc:
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
            try:
                with self._io_lock:
                    if proc.stdin is None:
                        raise ValueError("child stdin pipe is unavailable")
                    if proc.stdout is None:
                        raise ValueError("child stdout pipe is unavailable")
                    proc.stdin.write(json.dumps(request) + "\n")
                    proc.stdin.flush()
                    while True:
                        discarded: list[str] = []
                        while True:
                            line = proc.stdout.readline()
                            if not line:
                                raise ValueError("child process produced no output")
                            text = line.strip()
                            if not text:
                                continue
                            try:
                                payload = json.loads(text)
                                if isinstance(payload, dict):
                                    break
                            except Exception:
                                discarded.append(text)
                        messages.put(("payload", payload))
                        if payload.get("event") == "done" or not payload.get("ok"):
                            break
            except Exception as exc:
                messages.put(("error", {"ok": False, "error": str(exc)}))
            finally:
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
            {"action": "ping", "model_id": model_id},
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
            {"action": "load", "model_id": model_id},
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
                "model_id": model_id,
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
                "model_id": model_id,
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
                    "model_id": model_id,
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
                        detail={"pid": payload.get("pid")},
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
                        detail={
                            "pid": payload.get("pid"),
                            "generation_count": payload.get("generation_count"),
                        },
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
                    "model_id": model_id,
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
                        detail={
                            "pid": payload.get("pid"),
                            "message_count": payload.get("message_count"),
                        },
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
                        detail={
                            "pid": payload.get("pid"),
                            "generation_count": payload.get("generation_count"),
                            "message_count": payload.get("message_count"),
                        },
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
                "model_id": model_id,
            },
        )
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
        return BackendStatus(
            backend_name=self.name,
            healthy=self._last_error is None,
            loaded_models=tuple(
                self._registrations[model_id]
                for model_id in self._registrations
            ),
            detail={
                "model_count": len(self._registrations),
                "persistent_child": True,
                "last_error": self._last_error,
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
