"""Env-var gated real-model lifecycle smoke for the native MLX backend.

These tests are **opt-in only**. They run an actual ``mlx_lm`` model
through ``MlxNativeBackend.load → stream_generate → unload``. The default
path is to skip — owlmlx CI does not by default download or load real
models.

Activation:

- set ``OWLMLX_NATIVE_SMOKE_MODEL_PATH`` to a HuggingFace model id (or
  local path) that ``mlx_lm.load`` can resolve. Recommended: a 1-2B
  parameter quantized model from ``mlx-community`` already cached on the
  local machine.
- set ``OWLMLX_NATIVE_SMOKE_MAX_TOKENS`` (optional, default 8) to cap the
  generation length so the test runs in seconds, not minutes.

Without ``OWLMLX_NATIVE_SMOKE_MODEL_PATH`` set, every test in this module
is skipped. This is intentional: lifecycle smoke produces real evidence
toward the ``promoted`` capability-matrix verdict, but the cost (network,
disk, time) is opt-in.

When this round is run with the env var set, the resulting evidence is
cited by the coordinator checkpoint to upgrade specific capability matrix
rows from ``experimental`` / ``partial`` to ``supported``.
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
