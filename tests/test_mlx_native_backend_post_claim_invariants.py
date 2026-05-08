"""Post-claim serial-safety + ticketed-FIFO invariants on the native MLX backend.

These tests prove that ``MlxNativeBackend`` preserves the post-claim invariants
already proved on the subprocess backend by the phase45 sentinel chain:

- ``max_concurrent = 1`` after admission: at most one generate / stream
  critical section is active at any moment
- ticketed FIFO: requests are served strictly in arrival order; later
  arrivals cannot overtake earlier waiters

The tests use a fake `mlx_lm` stub injected into ``sys.modules``. The
behavior under test is the **adapter's own concurrency semantics**, not
``mlx_lm``'s. A plain ``threading.Lock`` is not sufficient to prove ticketed
FIFO; the adapter must implement adapter-local ticketed admission for these
tests to pass.

These invariants are baseline contracts inherited from the subprocess
sentinel chain and reclassified as native-path obligations by the chain-
closed checkpoint. Silent regression here is forbidden by the redirected
main line.
"""

from __future__ import annotations

from collections.abc import Callable
import importlib
import sys
import threading
import time
import types

import pytest


def _reload_native_module():
    import owlmlx.runtime.mlx_native_backend as mod

    return importlib.reload(mod)


def _install_fake_mlx_lm(
    monkeypatch: pytest.MonkeyPatch,
    *,
    stream_step_delay_s: float,
    on_enter_critical: Callable[[str], None] | None = None,
    on_exit_critical: Callable[[str], None] | None = None,
):
    """Install a fake mlx_lm whose stream_generate is observably slow."""

    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    class _FakeToken:
        def __init__(self, text: str, finish_reason: str | None = None) -> None:
            self.text = text
            self.finish_reason = finish_reason

    def fake_stream_generate(model, tokenizer, *, prompt, max_tokens):
        if on_enter_critical is not None:
            on_enter_critical(prompt)
        try:
            time.sleep(stream_step_delay_s)
            yield _FakeToken("hello")
            time.sleep(stream_step_delay_s)
            yield _FakeToken(" world", finish_reason="stop")
        finally:
            if on_exit_critical is not None:
                on_exit_critical(prompt)

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    return _reload_native_module()


def test_native_backend_admission_serializes_concurrent_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """At most one generate / stream critical section is active at any moment."""

    in_critical = 0
    max_observed = 0
    state_lock = threading.Lock()

    def on_enter(prompt: str) -> None:
        nonlocal in_critical, max_observed
        with state_lock:
            in_critical += 1
            if in_critical > max_observed:
                max_observed = in_critical

    def on_exit(prompt: str) -> None:
        nonlocal in_critical
        with state_lock:
            in_critical -= 1

    mod = _install_fake_mlx_lm(
        monkeypatch,
        stream_step_delay_s=0.05,
        on_enter_critical=on_enter,
        on_exit_critical=on_exit,
    )
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")

        def run_one(prompt: str) -> list[str]:
            return [
                e.event for e in backend.stream_generate("fake-model", prompt)
            ]

        threads = []
        results: dict[str, list[str]] = {}
        results_lock = threading.Lock()

        def runner(prompt: str) -> None:
            evts = run_one(prompt)
            with results_lock:
                results[prompt] = evts

        for i in range(5):
            t = threading.Thread(target=runner, args=(f"prompt-{i}",))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        assert all(not t.is_alive() for t in threads), "stream threads hung"
        assert len(results) == 5
        for prompt, events in results.items():
            assert events == ["token", "token", "done"], f"bad events for {prompt}: {events}"
        assert max_observed == 1, (
            f"native admission allowed concurrency {max_observed}, "
            f"violates max_concurrent=1 invariant"
        )
        snapshot = backend.status().detail["admission"]
        assert snapshot["max_observed_concurrency"] == 1
        assert snapshot["next_ticket"] == 5
        assert snapshot["serving"] == 5
        assert snapshot["in_critical_section"] == 0
    finally:
        sys.modules.pop("mlx_lm", None)
        _reload_native_module()


def test_native_backend_admission_preserves_ticketed_fifo_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Requests are served strictly in admission order, not interpreter race order."""

    enter_order: list[str] = []
    enter_lock = threading.Lock()
    release_events = {f"fifo-{i}": threading.Event() for i in range(4)}
    entered_events = {f"fifo-{i}": threading.Event() for i in range(4)}

    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    class _FakeToken:
        def __init__(self, text: str, finish_reason: str | None = None) -> None:
            self.text = text
            self.finish_reason = finish_reason

    def fake_stream_generate(model, tokenizer, *, prompt, max_tokens):
        with enter_lock:
            enter_order.append(prompt)
        entered_events[prompt].set()
        assert release_events[prompt].wait(timeout=5.0)
        yield _FakeToken(prompt, finish_reason="stop")

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    mod = _reload_native_module()
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")

        results: list[tuple[int, str]] = []
        results_lock = threading.Lock()

        def runner(idx: int, prompt: str) -> None:
            events: list[str] = []
            for e in backend.stream_generate("fake-model", prompt):
                events.append(e.event)
            with results_lock:
                results.append((idx, prompt))

        threads: list[threading.Thread] = []

        first = threading.Thread(target=runner, args=(0, "fifo-0"))
        threads.append(first)
        first.start()
        assert entered_events["fifo-0"].wait(timeout=5.0)

        # Start later callers in a strict order and poll the adapter's
        # admission snapshot until each caller has received its ticket before
        # releasing the first request. This proves FIFO order on actual
        # adapter admission, not on generator object creation.
        for i in range(1, 4):
            t = threading.Thread(target=runner, args=(i, f"fifo-{i}"))
            threads.append(t)
            t.start()
            deadline = time.time() + 5.0
            while backend.status().detail["admission"]["next_ticket"] < i + 1:
                assert time.time() < deadline, f"fifo-{i} did not get a ticket"
                time.sleep(0.01)
            assert not entered_events[f"fifo-{i}"].is_set()

        for i in range(4):
            release_events[f"fifo-{i}"].set()
            if i + 1 < 4:
                assert entered_events[f"fifo-{i + 1}"].wait(timeout=5.0)

        for t in threads:
            t.join(timeout=15.0)

        assert all(not t.is_alive() for t in threads), "fifo threads hung"
        # enter_order is recorded inside the fake stream_generate (i.e. inside
        # the admission critical section), so it reflects actual serving order.
        assert enter_order == [f"fifo-{i}" for i in range(4)], (
            f"native admission did not preserve ticketed FIFO order: "
            f"{enter_order}"
        )
        snapshot = backend.status().detail["admission"]
        assert snapshot["max_observed_concurrency"] == 1
    finally:
        sys.modules.pop("mlx_lm", None)
        _reload_native_module()


def test_native_backend_uncontested_requests_are_not_marked_queued(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monotonic tickets must not make later uncontested calls look queued."""

    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    def fake_generate(model, tokenizer, *, prompt, max_tokens):
        return f"{prompt}::done"

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    mod = _reload_native_module()
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")

        first = backend.generate("fake-model", "first")
        second = backend.generate("fake-model", "second")

        assert first.ok is True
        assert second.ok is True
        assert first.was_queued is False
        assert second.was_queued is False
        assert first.wait_time_s is not None
        assert second.wait_time_s is not None
        snapshot = backend.status().detail["admission"]
        assert snapshot["next_ticket"] == 2
        assert snapshot["serving"] == 2
    finally:
        sys.modules.pop("mlx_lm", None)
        _reload_native_module()


def test_native_backend_admission_releases_on_error_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the underlying stream raises, the ticket is still released and the
    next waiter is served.
    """

    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    call_count = 0

    def fake_stream_generate(model, tokenizer, *, prompt, max_tokens):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("simulated upstream failure")

        class _FakeToken:
            def __init__(self, text: str, finish_reason: str | None = None) -> None:
                self.text = text
                self.finish_reason = finish_reason

        yield _FakeToken("ok", finish_reason="stop")

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    mod = _reload_native_module()
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")

        # First request hits the simulated failure.
        first = list(backend.stream_generate("fake-model", "first"))
        assert any(e.event == "error" for e in first)

        # Second request must succeed — proves the ticket was released.
        second = list(backend.stream_generate("fake-model", "second"))
        assert [e.event for e in second] == ["token", "done"]
        snapshot = backend.status().detail["admission"]
        assert snapshot["in_critical_section"] == 0
        assert snapshot["serving"] == snapshot["next_ticket"]
    finally:
        sys.modules.pop("mlx_lm", None)
        _reload_native_module()


def test_native_backend_admission_releases_on_generator_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the caller drops the iterator early (generator close), the ticket
    is still released so subsequent callers are not deadlocked.
    """

    mod = _install_fake_mlx_lm(monkeypatch, stream_step_delay_s=0.0)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")

        # Acquire, take only the first token, then drop the iterator.
        gen = backend.stream_generate("fake-model", "early-close")
        first = next(gen)
        assert first.event == "token"
        gen.close()

        # The next call must complete; if release_on_close is broken this
        # blocks forever.
        events = list(backend.stream_generate("fake-model", "after-close"))
        assert events[-1].event == "done"
        snapshot = backend.status().detail["admission"]
        assert snapshot["in_critical_section"] == 0
    finally:
        sys.modules.pop("mlx_lm", None)
        _reload_native_module()


def test_native_backend_generate_is_also_admission_serialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-streaming `generate` must share the same ticketed admission as
    `stream_generate` — otherwise mixed workloads could violate
    max_concurrent=1.
    """

    fake = types.ModuleType("mlx_lm")

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    in_critical = 0
    max_observed = 0
    state_lock = threading.Lock()

    def fake_generate(model, tokenizer, *, prompt, max_tokens):
        nonlocal in_critical, max_observed
        with state_lock:
            in_critical += 1
            if in_critical > max_observed:
                max_observed = in_critical
        try:
            time.sleep(0.04)
            return f"{prompt}::done"
        finally:
            with state_lock:
                in_critical -= 1

    class _FakeToken:
        def __init__(self, text: str, finish_reason: str | None = None) -> None:
            self.text = text
            self.finish_reason = finish_reason

    def fake_stream_generate(model, tokenizer, *, prompt, max_tokens):
        nonlocal in_critical, max_observed
        with state_lock:
            in_critical += 1
            if in_critical > max_observed:
                max_observed = in_critical
        try:
            time.sleep(0.04)
            yield _FakeToken("tok", finish_reason="stop")
        finally:
            with state_lock:
                in_critical -= 1

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    mod = _reload_native_module()
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")

        def gen_runner(prompt: str) -> None:
            backend.generate("fake-model", prompt)

        def stream_runner(prompt: str) -> None:
            list(backend.stream_generate("fake-model", prompt))

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=gen_runner, args=(f"g-{i}",)))
            threads.append(threading.Thread(target=stream_runner, args=(f"s-{i}",)))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15.0)

        assert all(not t.is_alive() for t in threads)
        assert max_observed == 1, (
            f"mixed generate / stream_generate observed concurrency "
            f"{max_observed}, must be 1"
        )
    finally:
        sys.modules.pop("mlx_lm", None)
        _reload_native_module()
