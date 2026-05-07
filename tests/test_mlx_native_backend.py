"""Tests for the experimental native MLX backend adapter.

These tests do **not** require ``mlx_lm`` to be installed. They exercise the
adapter's interface shape, graceful-failure paths when the optional runtime
extra is missing, and the lifecycle contract on non-loaded model_ids.

Anything that requires a real MLX model load is deliberately out of scope for
this round (feasibility / scaffold).
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

from owlmlx.runtime.mlx_native_backend import MlxNativeBackend
from owlmlx.runtime.types import (
    BackendStatus,
    ChatTurn,
    GenerateResult,
    LoadResult,
    RuntimeErrorCode,
    StreamEvent,
    UnloadResult,
)


def test_native_backend_instantiates_without_mlx_lm() -> None:
    backend = MlxNativeBackend()
    assert isinstance(backend, MlxNativeBackend)


def test_native_backend_status_reports_unhealthy_without_mlx_lm() -> None:
    # Belt-and-suspenders: if mlx_lm happens to be importable in this env we
    # still want healthy=True; otherwise we want healthy=False with import error.
    backend = MlxNativeBackend()
    status = backend.status()
    assert isinstance(status, BackendStatus)
    assert status.backend_name == "mlx-native"
    assert status.loaded_models == ()
    assert "backend_kind" in status.detail
    assert status.detail["backend_kind"] == "experimental_native_mlx"
    assert status.detail["entry_points_owned_by_owlmlx"] is False
    if "mlx_lm" in sys.modules or _mlx_lm_importable():
        assert status.healthy is True
    else:
        assert status.healthy is False
        assert "import_error" in status.detail


def test_native_backend_load_returns_backend_error_when_mlx_lm_missing() -> None:
    if _mlx_lm_importable():
        pytest.skip("mlx_lm is installed; this test covers the missing-extra path")
    backend = MlxNativeBackend()
    result = backend.load("any-model-id")
    assert isinstance(result, LoadResult)
    assert result.ok is False
    assert result.error_code == RuntimeErrorCode.backend_error
    assert result.detail.get("reason") == "mlx_lm_not_installed"


def test_native_backend_load_rejects_empty_model_id() -> None:
    backend = MlxNativeBackend()
    result = backend.load("")
    assert result.ok is False
    assert result.error_code == RuntimeErrorCode.invalid_request


def test_native_backend_unload_of_unknown_model_returns_not_loaded() -> None:
    backend = MlxNativeBackend()
    result = backend.unload("not-loaded")
    assert isinstance(result, UnloadResult)
    assert result.ok is False
    assert result.error_code == RuntimeErrorCode.model_not_loaded
    assert result.model_id == "not-loaded"


def test_native_backend_generate_of_unloaded_model_returns_not_loaded() -> None:
    backend = MlxNativeBackend()
    result = backend.generate("not-loaded", "hello")
    assert isinstance(result, GenerateResult)
    assert result.ok is False
    assert result.error_code == RuntimeErrorCode.model_not_loaded


def test_native_backend_stream_generate_of_unloaded_model_yields_error() -> None:
    backend = MlxNativeBackend()
    events = list(backend.stream_generate("not-loaded", "hello"))
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, StreamEvent)
    assert event.event == "error"
    assert event.error_code == RuntimeErrorCode.model_not_loaded


def test_native_backend_stream_generate_messages_is_iterable() -> None:
    backend = MlxNativeBackend()
    events = list(
        backend.stream_generate_messages(
            "not-loaded",
            [ChatTurn(role="user", content="hi")],
        )
    )
    assert events and events[0].event == "error"


def test_native_backend_capability_entry_points_unloaded() -> None:
    backend = MlxNativeBackend()
    info = backend.capability_entry_points("not-loaded")
    assert info["available"] is False
    assert info["reason"] == "model_not_loaded"


def test_native_backend_load_succeeds_with_fake_mlx_lm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With a stub `mlx_lm` injected into sys.modules, load/unload run end-to-end."""

    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    fake.load = fake_load  # type: ignore[attr-defined]
    previous_mlx_lm = sys.modules.get("mlx_lm")
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    # Force the deferred importer to see the stub.
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    try:
        backend = mod.MlxNativeBackend()
        result = backend.load("fake-model")
        assert result.ok is True
        assert result.model is not None
        assert result.model.backend == "mlx-native"
        status = backend.status()
        assert status.healthy is True
        assert any(m.model_id == "fake-model" for m in status.loaded_models)
        cap = backend.capability_entry_points("fake-model")
        assert cap["available"] is True
        assert cap["model_handle_present"] is True
        assert cap["kv_cache_factory"]["status"] == "not_verified_this_round"
        assert cap["sampler_factory"]["status"] == "not_verified_this_round"
        unloaded = backend.unload("fake-model")
        assert unloaded.ok is True
        assert unloaded.model_id == "fake-model"
        assert backend.status().loaded_models == ()
    finally:
        # Restore the real module state for subsequent tests.
        if previous_mlx_lm is None:
            sys.modules.pop("mlx_lm", None)
        else:
            sys.modules["mlx_lm"] = previous_mlx_lm
        importlib.reload(mod)


def test_native_backend_stream_generate_yields_token_then_done_with_fake_mlx_lm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    class _FakeToken:
        def __init__(self, text: str, finish_reason: str | None = None) -> None:
            self.text = text
            self.finish_reason = finish_reason

    def fake_stream_generate(model, tokenizer, *, prompt, max_tokens):
        yield _FakeToken("hello")
        yield _FakeToken(" world", finish_reason="stop")

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    previous_mlx_lm = sys.modules.get("mlx_lm")
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")
        events = list(backend.stream_generate("fake-model", "hi"))
        assert [e.event for e in events] == ["token", "token", "done"]
        assert events[0].text == "hello"
        assert events[1].text == " world"
        assert events[-1].finish_reason == "stop"
        assert events[-1].completion_tokens == 2
    finally:
        if previous_mlx_lm is None:
            sys.modules.pop("mlx_lm", None)
        else:
            sys.modules["mlx_lm"] = previous_mlx_lm
        importlib.reload(mod)


def test_native_backend_generate_succeeds_with_fake_mlx_lm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    def fake_generate(model, tokenizer, *, prompt, max_tokens):
        return f"generated:{prompt}:{max_tokens}"

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    previous_mlx_lm = sys.modules.get("mlx_lm")
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")
        result = backend.generate("fake-model", "hi", max_tokens=3)
        assert result.ok is True
        assert result.model_id == "fake-model"
        assert result.text == "generated:hi:3"
        assert result.execution_time_s is not None
    finally:
        if previous_mlx_lm is None:
            sys.modules.pop("mlx_lm", None)
        else:
            sys.modules["mlx_lm"] = previous_mlx_lm
        importlib.reload(mod)


def test_native_backend_module_has_no_subprocess_or_sentinel_chain_ties() -> None:
    """The native adapter must not import subprocess machinery or sentinel parsers."""

    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "runtime", "mlx_native_backend.py"
    ).read_text()
    forbidden = [
        "import subprocess",
        "from subprocess",
        "subprocess.Popen",
        "subprocess.run",
        "_STREAM_TERMINAL_NOTICE",
        "runtime_owned_terminal_",
        "_is_terminal_notice_leading_discriminator_marker",
    ]
    for token in forbidden:
        assert token not in source, f"native adapter must not reference: {token}"


def test_native_backend_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "runtime", "mlx_native_backend.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source


def _mlx_lm_importable() -> bool:
    try:
        import mlx_lm  # type: ignore[import-not-found] # noqa: F401
    except ImportError:
        return False
    return True
