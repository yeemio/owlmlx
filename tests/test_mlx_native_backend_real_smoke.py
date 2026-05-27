"""Env-var gated real-model lifecycle smokes.

Two backends covered, each gated by its own env vars and skipped by default:

1. ``MlxNativeBackend`` (in-process) — gated by
   ``OWLMLX_NATIVE_SMOKE_MODEL_PATH`` / ``OWLMLX_NATIVE_SMOKE_MAX_TOKENS``.
   Runs an actual ``mlx_lm`` model through
   ``load → stream_generate → unload``.

2. ``MlxLmSubprocessBackend`` for DSV4-Flash 2bit-DQ (D6 mainline backend
   integration) — gated by ``OWLMLX_DSV4_SUBPROCESS_SMOKE_PYTHON`` /
   ``OWLMLX_DSV4_SUBPROCESS_SMOKE_MODEL_PATH`` /
   ``OWLMLX_DSV4_SUBPROCESS_SMOKE_MAX_TOKENS`` (default 32). The reject test
   uses ``OWLMLX_DSV4_SUBPROCESS_SMOKE_FALLBACK_PYTHON`` to pin a python
   that does NOT have ``mlx_lm.models.deepseek_v4`` available.

Default path is to skip — owlmlx CI does not by default download or load
real models. Subprocess-backend DSV4 evidence (when run) is the D6
mainline-backend lifecycle gate; see
``docs/architect/design/D6-mainline-backend-integration-spec.md``.
"""

from __future__ import annotations

import os
import time

import pytest


_MODEL_ENV = "OWLMLX_NATIVE_SMOKE_MODEL_PATH"
_MAX_TOKENS_ENV = "OWLMLX_NATIVE_SMOKE_MAX_TOKENS"


def _smoke_model() -> str | None:
    return os.environ.get(_MODEL_ENV) or None


def _smoke_max_tokens() -> int:
    raw = os.environ.get(_MAX_TOKENS_ENV)
    if not raw:
        return 8
    try:
        n = int(raw)
    except ValueError:
        return 8
    return max(1, min(n, 64))


def _smoke_enabled() -> bool:
    return _smoke_model() is not None


@pytest.mark.skipif(
    not _smoke_enabled(),
    reason=(
        f"{_MODEL_ENV} not set; real-model native lifecycle smoke is opt-in"
    ),
)
def test_real_model_lifecycle_load_stream_unload() -> None:
    """Drive a real ``mlx_lm`` model through ``load → stream_generate → unload``.

    Asserts the minimum honest contract:
    - load succeeds and returns a ``LoadedModelInfo`` with the right backend
    - stream_generate yields at least one ``token`` event followed by ``done``
    - the ``done`` event has a ``finish_reason`` and ``completion_tokens > 0``
    - the per-request ``prompt_cache`` was created (binding layer worked)
    - unload succeeds and the model leaves ``status().loaded_models``
    """

    from owlmlx.runtime.mlx_native_backend import MlxNativeBackend

    model_id = _smoke_model()
    assert model_id is not None

    backend = MlxNativeBackend()
    started = time.time()
    load_result = backend.load(model_id)
    load_took_s = time.time() - started
    assert load_result.ok, f"native load failed: {load_result.message}"
    assert load_result.model is not None
    assert load_result.model.backend == "mlx-native"
    assert load_result.model.model_id == model_id

    max_tokens = _smoke_max_tokens()
    events: list[str] = []
    finish_reason: str | None = None
    completion_tokens: int | None = None
    stream_started = time.time()
    for ev in backend.stream_generate(
        model_id,
        "Say one short sentence.",
        max_tokens=max_tokens,
    ):
        events.append(ev.event)
        if ev.event == "done":
            finish_reason = ev.finish_reason
            completion_tokens = ev.completion_tokens
    stream_took_s = time.time() - stream_started

    assert "token" in events, f"no token events; got {events}"
    assert events[-1] == "done", f"final event was not done: {events[-1]}"
    assert finish_reason is not None
    assert completion_tokens is not None and completion_tokens > 0

    cap = backend.capability_entry_points(model_id)
    assert cap["available"] is True
    assert (
        cap["kv_cache_factory"]["status"]
        == "bound_per_request_single_request_only"
    )
    assert cap["kv_cache_factory"]["prompt_cache_call_count"] >= 1
    assert cap["kv_cache_factory"]["cross_request_reuse_claimed"] is False

    unload_result = backend.unload(model_id)
    assert unload_result.ok, f"unload failed: {unload_result.message}"
    assert unload_result.model_id == model_id
    assert all(
        m.model_id != model_id for m in backend.status().loaded_models
    )

    print(
        f"\n[real_smoke] model={model_id} load_s={load_took_s:.2f} "
        f"stream_s={stream_took_s:.2f} max_tokens={max_tokens} "
        f"completion_tokens={completion_tokens} finish={finish_reason} "
        f"events={events}"
    )


@pytest.mark.skipif(
    not _smoke_enabled(),
    reason=(
        f"{_MODEL_ENV} not set; real-model native lifecycle smoke is opt-in"
    ),
)
def test_real_model_two_streams_serialize_under_admission() -> None:
    """Real model + adapter ticketed admission must preserve max_concurrent=1.

    This is the real-mlx_lm counterpart to the fake-stub
    ``test_native_backend_admission_serializes_concurrent_streams``. It
    proves the post-claim invariant on the actual upstream stream path,
    not just on a fake-injected stub.
    """

    import threading

    from owlmlx.runtime.mlx_native_backend import MlxNativeBackend

    model_id = _smoke_model()
    assert model_id is not None

    backend = MlxNativeBackend()
    load_result = backend.load(model_id)
    assert load_result.ok, f"native load failed: {load_result.message}"

    max_tokens = _smoke_max_tokens()
    results: list[tuple[str, list[str]]] = []
    results_lock = threading.Lock()

    def runner(prompt: str) -> None:
        events = [
            ev.event
            for ev in backend.stream_generate(
                model_id, prompt, max_tokens=max_tokens
            )
        ]
        with results_lock:
            results.append((prompt, events))

    threads = [
        threading.Thread(target=runner, args=(f"prompt-{i}",))
        for i in range(2)
    ]
    started = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=300.0)
    elapsed = time.time() - started

    assert all(not t.is_alive() for t in threads), (
        f"real-stream threads hung after {elapsed:.1f}s"
    )
    assert len(results) == 2
    for prompt, events in results:
        assert events and events[-1] == "done", (
            f"prompt {prompt} did not reach done: {events}"
        )

    snap = backend.status().detail["admission"]
    assert snap["max_observed_concurrency"] == 1
    assert snap["next_ticket"] == 2
    assert snap["serving"] == 2
    assert snap["in_critical_section"] == 0

    backend.unload(model_id)


# ---------------------------------------------------------------------------
# D6 · MlxLmSubprocessBackend DSV4-Flash 2bit-DQ lifecycle smoke (env-gated).
# Spec: docs/architect/design/D6-mainline-backend-integration-spec.md §9.4
# ---------------------------------------------------------------------------


_DSV4_SUBPROCESS_PYTHON_ENV = "OWLMLX_DSV4_SUBPROCESS_SMOKE_PYTHON"
_DSV4_SUBPROCESS_MODEL_ENV = "OWLMLX_DSV4_SUBPROCESS_SMOKE_MODEL_PATH"
_DSV4_SUBPROCESS_MAX_TOKENS_ENV = "OWLMLX_DSV4_SUBPROCESS_SMOKE_MAX_TOKENS"
_DSV4_SUBPROCESS_FALLBACK_PYTHON_ENV = (
    "OWLMLX_DSV4_SUBPROCESS_SMOKE_FALLBACK_PYTHON"
)


def _dsv4_subprocess_python() -> str | None:
    return os.environ.get(_DSV4_SUBPROCESS_PYTHON_ENV) or None


def _dsv4_subprocess_model_path() -> str | None:
    return os.environ.get(_DSV4_SUBPROCESS_MODEL_ENV) or None


def _dsv4_subprocess_max_tokens() -> int:
    raw = os.environ.get(_DSV4_SUBPROCESS_MAX_TOKENS_ENV)
    if not raw:
        return 32
    try:
        n = int(raw)
    except ValueError:
        return 32
    return max(1, min(n, 128))


def _dsv4_subprocess_fallback_python() -> str | None:
    return os.environ.get(_DSV4_SUBPROCESS_FALLBACK_PYTHON_ENV) or None


def _dsv4_subprocess_smoke_enabled() -> bool:
    return (
        _dsv4_subprocess_python() is not None
        and _dsv4_subprocess_model_path() is not None
    )


@pytest.mark.skipif(
    not _dsv4_subprocess_smoke_enabled(),
    reason=(
        f"{_DSV4_SUBPROCESS_PYTHON_ENV} and {_DSV4_SUBPROCESS_MODEL_ENV} "
        "must both be set; D6 subprocess-backend DSV4 lifecycle smoke is opt-in"
    ),
)
def test_dsv4_subprocess_backend_lifecycle_load_stream_unload() -> None:
    """Drive DSV4-Flash 2bit-DQ through ``MlxLmSubprocessBackend`` lifecycle.

    Mainline backend path (not the D1-D4 isolated harness). The python
    pointed to by ``OWLMLX_DSV4_SUBPROCESS_SMOKE_PYTHON`` must have the
    ``deepseek-experimental`` pyproject extras installed so that
    ``importlib.util.find_spec("mlx_lm.models.deepseek_v4")`` resolves
    inside the child runtime.
    """

    from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend
    from owlmlx.runtime.types import ChatTurn

    backend_python = _dsv4_subprocess_python()
    model_path = _dsv4_subprocess_model_path()
    assert backend_python is not None
    assert model_path is not None

    backend = MlxLmSubprocessBackend(
        python_executable=backend_python,
        timeout_s=900.0,
        auto_restart_dead_session=False,
        max_restart_attempts=0,
    )

    load_started = time.time()
    load_result = backend.load(model_path, memory_gb=100.0)
    load_took_s = time.time() - load_started
    assert load_result.ok, (
        f"DSV4 subprocess load failed: {load_result.message}; "
        f"detail={load_result.detail}"
    )
    assert load_result.model is not None
    assert load_result.model.backend == "mlx-lm-subprocess"

    max_tokens = _dsv4_subprocess_max_tokens()
    messages = [ChatTurn(role="user", content="Say one short sentence.")]
    events: list[str] = []
    finish_reason: str | None = None
    completion_tokens: int | None = None
    stream_started = time.time()
    for ev in backend.stream_generate_messages(
        model_path, messages, max_tokens=max_tokens
    ):
        events.append(ev.event)
        if ev.event == "done":
            finish_reason = ev.finish_reason
            completion_tokens = ev.completion_tokens
    stream_took_s = time.time() - stream_started

    assert "token" in events, f"no token events; got {events}"
    assert events[-1] == "done", f"final event was not done: {events[-1]}"
    assert finish_reason is not None
    assert completion_tokens is not None and completion_tokens > 0

    unload_result = backend.unload(model_path)
    assert unload_result.ok, f"DSV4 subprocess unload failed: {unload_result.message}"
    status = backend.status()
    assert all(m.model_id != model_path for m in status.loaded_models)
    assert status.healthy is True

    print(
        f"\n[dsv4_subprocess_smoke] python={backend_python} "
        f"load_s={load_took_s:.2f} stream_s={stream_took_s:.2f} "
        f"max_tokens={max_tokens} completion_tokens={completion_tokens} "
        f"finish={finish_reason} freed_gb={unload_result.freed_gb}"
    )


@pytest.mark.skipif(
    _dsv4_subprocess_fallback_python() is None
    or _dsv4_subprocess_model_path() is None,
    reason=(
        f"{_DSV4_SUBPROCESS_FALLBACK_PYTHON_ENV} (a venv WITHOUT the "
        "deepseek-experimental extras) and "
        f"{_DSV4_SUBPROCESS_MODEL_ENV} must both be set; the D6 clean-reject "
        "fallback test is opt-in"
    ),
)
def test_dsv4_subprocess_backend_rejects_when_extras_missing() -> None:
    """When the configured venv lacks ``mlx_lm.models.deepseek_v4``,
    ``MlxLmSubprocessBackend.load`` must refuse cleanly and NOT spawn a
    child process or dirty backend health (D4-equivalent fallback for the
    D6 mainline backend path).
    """

    from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend
    from owlmlx.runtime.types import RuntimeErrorCode

    fallback_python = _dsv4_subprocess_fallback_python()
    model_path = _dsv4_subprocess_model_path()
    assert fallback_python is not None
    assert model_path is not None

    backend = MlxLmSubprocessBackend(
        python_executable=fallback_python,
        timeout_s=60.0,
        auto_restart_dead_session=False,
        max_restart_attempts=0,
    )
    status_before = backend.status()

    result = backend.load(model_path, memory_gb=100.0)
    assert result.ok is False
    assert result.error_code == RuntimeErrorCode.unsupported_model_family
    assert isinstance(result.detail, dict)
    assert result.detail.get("does_not_start_child") is True
    assert result.detail.get("does_not_dirty_backend_health") is True

    status_after = backend.status()
    assert status_before.healthy == status_after.healthy
    assert status_after.loaded_models == ()
