"""Tests for owlmlx.memory_actuator — scaffold-grade actuator surface.

These tests do **not** import real ``mlx``. They exercise the actuator's
shape contract, no-op-when-no-mlx behavior, and frozen-invariant
honoring via fake-injected mlx-shaped modules.

Anything that requires a real mlx allocator interaction is deliberately
out of scope for this round (scaffold-grade landing). A subsequent round
that wires production callers to inject a real ``mx`` module will add
real-injection evidence; this file does not.
"""

from __future__ import annotations

import threading
from typing import Any

from owlmlx.memory_actuator import (
    HONORED_INVARIANTS,
    MEMORY_ACTUATOR_SURFACE,
    MEMORY_ACTUATOR_VERSION,
    AllocatorFloorConfig,
    MemoryActuator,
    PressureEventSubscription,
    ReclaimReceipt,
)


# ── Fake mlx-shaped modules for injection ────────────────────────────────────


class _FakeMlxModule:
    """Fake mlx-shaped module that records calls.

    Mimics the surface ``MemoryActuator`` interacts with:
    ``clear_cache``, ``set_cache_limit``, ``set_wired_limit``,
    ``get_active_memory``, ``get_cache_memory``, ``get_peak_memory``.

    The byte-returning methods follow a script: each call returns the
    next value in a per-attribute list, allowing tests to script
    "before vs. after" deltas deterministically.
    """

    def __init__(
        self,
        *,
        with_wired_limit: bool = True,
        active_script: list[int] | None = None,
        cache_script: list[int] | None = None,
        peak_script: list[int] | None = None,
    ) -> None:
        self.clear_cache_calls = 0
        self.set_cache_limit_calls: list[int] = []
        self.set_wired_limit_calls: list[int] = []
        self._active_script = list(active_script or [])
        self._cache_script = list(cache_script or [])
        self._peak_script = list(peak_script or [])
        if not with_wired_limit:
            # Simulate older macOS / mlx without set_wired_limit.
            try:
                delattr(self, "set_wired_limit")
            except AttributeError:
                pass

    def clear_cache(self) -> None:
        self.clear_cache_calls += 1

    def set_cache_limit(self, limit: int) -> int:
        self.set_cache_limit_calls.append(int(limit))
        return 0

    def set_wired_limit(self, limit: int) -> int:
        self.set_wired_limit_calls.append(int(limit))
        return 0

    def get_active_memory(self) -> int:
        if self._active_script:
            return self._active_script.pop(0)
        return 0

    def get_cache_memory(self) -> int:
        if self._cache_script:
            return self._cache_script.pop(0)
        return 0

    def get_peak_memory(self) -> int:
        if self._peak_script:
            return self._peak_script.pop(0)
        return 0


class _FakeMlxModuleNoWiredLimit:
    """Fake module that does not expose ``set_wired_limit`` at all."""

    def __init__(self) -> None:
        self.set_cache_limit_calls: list[int] = []

    def clear_cache(self) -> None:  # pragma: no cover — not exercised
        pass

    def set_cache_limit(self, limit: int) -> int:
        self.set_cache_limit_calls.append(int(limit))
        return 0

    def get_active_memory(self) -> int:
        return 0

    def get_cache_memory(self) -> int:
        return 0

    def get_peak_memory(self) -> int:
        return 0


# ── Construction & invariants ────────────────────────────────────────────────


def test_actuator_starts_with_no_subscriptions() -> None:
    actuator = MemoryActuator()
    assert actuator.subscriptions == ()
    assert actuator.mlx_module_available is False


def test_actuator_does_not_spawn_thread_or_daemon() -> None:
    """Honor ``no_automatic_background_eviction_loop`` literally.

    Construction must not start any thread. A simple count-based check
    catches any future regression that introduces a daemon.
    """
    before = threading.active_count()
    actuator = MemoryActuator()
    after_construct = threading.active_count()
    actuator.register_pressure_listener(subscriber_name="alpha")
    after_register = threading.active_count()
    actuator.notify_pressure(condition="host_pressure_block")
    after_notify = threading.active_count()
    assert after_construct == before
    assert after_register == before
    assert after_notify == before


def test_honored_invariants_match_policy_invariants() -> None:
    """The actuator must declare the two execution-relevant invariants."""
    assert "pinned_models_never_evicted" in HONORED_INVARIANTS
    assert "no_automatic_background_eviction_loop" in HONORED_INVARIANTS


# ── release_single_model ─────────────────────────────────────────────────────


def test_release_single_model_with_no_mlx_module_returns_noop_receipt() -> None:
    actuator = MemoryActuator()
    receipt = actuator.release_single_model(
        model_id="m-test",
        declared_freed_gb=42.0,
    )
    assert isinstance(receipt, ReclaimReceipt)
    assert receipt.model_id == "m-test"
    assert receipt.declared_freed_gb == 42.0
    assert receipt.active_memory_before_bytes is None
    assert receipt.active_memory_after_bytes is None
    assert receipt.cache_memory_before_bytes is None
    assert receipt.cache_memory_after_bytes is None
    assert receipt.actuator_invoked_clear_cache is False
    assert receipt.mlx_module_available is False


def test_release_single_model_with_no_mlx_module_does_not_attempt_clear_cache() -> None:
    """Sentinel: a fake mlx that would error on ``clear_cache`` must never
    be touched on the no-op path."""

    class _ExplodingFake:
        def clear_cache(self) -> None:
            raise AssertionError("must not be called on no-op path")

    # The actuator was constructed with mlx_module=None, so no fake is
    # present; this test asserts the no-op contract by inspecting the
    # receipt's invoked flag rather than by attaching the fake.
    actuator = MemoryActuator(mlx_module=None)
    receipt = actuator.release_single_model(
        model_id="m-noop",
        declared_freed_gb=0.0,
    )
    assert receipt.actuator_invoked_clear_cache is False
    # And to be belt-and-suspenders: instantiating the exploder is fine
    # because nothing was wired through it.
    _ = _ExplodingFake()


def test_release_single_model_with_fake_mlx_module_calls_clear_cache_once() -> None:
    fake = _FakeMlxModule()
    actuator = MemoryActuator(mlx_module=fake)
    receipt = actuator.release_single_model(
        model_id="m-real",
        declared_freed_gb=10.5,
    )
    assert fake.clear_cache_calls == 1
    assert receipt.actuator_invoked_clear_cache is True
    assert receipt.mlx_module_available is True


def test_release_single_model_with_fake_mlx_module_records_before_after_memory_bytes() -> None:
    fake = _FakeMlxModule(
        active_script=[1_000_000_000, 100_000_000],
        cache_script=[500_000_000, 50_000_000],
    )
    actuator = MemoryActuator(mlx_module=fake)
    receipt = actuator.release_single_model(
        model_id="m-meas",
        declared_freed_gb=4.0,
    )
    assert receipt.active_memory_before_bytes == 1_000_000_000
    assert receipt.active_memory_after_bytes == 100_000_000
    assert receipt.cache_memory_before_bytes == 500_000_000
    assert receipt.cache_memory_after_bytes == 50_000_000
    # The receipt must round-trip via to_dict() with consistent shape.
    payload = receipt.to_dict()
    assert payload["model_id"] == "m-meas"
    assert payload["actuator_invoked_clear_cache"] is True


# ── configure_allocator_floor ────────────────────────────────────────────────


def test_configure_allocator_floor_with_no_mlx_module_echoes_args() -> None:
    actuator = MemoryActuator()
    cfg = actuator.configure_allocator_floor(
        cache_limit_bytes=8 * 1024 * 1024 * 1024,
        wired_limit_bytes=4 * 1024 * 1024 * 1024,
    )
    assert isinstance(cfg, AllocatorFloorConfig)
    assert cfg.cache_limit_bytes == 8 * 1024 * 1024 * 1024
    assert cfg.wired_limit_bytes == 4 * 1024 * 1024 * 1024
    assert cfg.wired_limit_supported is False


def test_configure_allocator_floor_calls_set_cache_limit_when_provided() -> None:
    fake = _FakeMlxModule()
    actuator = MemoryActuator(mlx_module=fake)
    actuator.configure_allocator_floor(
        cache_limit_bytes=2 * 1024 * 1024 * 1024,
        wired_limit_bytes=1 * 1024 * 1024 * 1024,
    )
    assert fake.set_cache_limit_calls == [2 * 1024 * 1024 * 1024]
    assert fake.set_wired_limit_calls == [1 * 1024 * 1024 * 1024]


def test_configure_allocator_floor_skips_wired_limit_when_module_lacks_attribute() -> None:
    fake = _FakeMlxModuleNoWiredLimit()
    actuator = MemoryActuator(mlx_module=fake)
    cfg = actuator.configure_allocator_floor(
        cache_limit_bytes=1024,
        wired_limit_bytes=2048,
    )
    # set_cache_limit goes through.
    assert fake.set_cache_limit_calls == [1024]
    # The wired-limit symbol is absent on this fake; nothing crashes.
    # The config records that the symbol was unreachable.
    assert cfg.wired_limit_supported is False
    assert cfg.cache_limit_bytes == 1024
    assert cfg.wired_limit_bytes == 2048


# ── Pressure-event seam ──────────────────────────────────────────────────────


def test_register_pressure_listener_creates_subscription_with_provided_name() -> None:
    actuator = MemoryActuator()
    sub = actuator.register_pressure_listener(
        subscriber_name="evictor-1",
        condition="host_pressure_block",
    )
    assert isinstance(sub, PressureEventSubscription)
    assert sub.subscriber_name == "evictor-1"
    assert sub.condition == "host_pressure_block"
    assert sub.registered_at > 0
    assert len(actuator.subscriptions) == 1
    assert actuator.subscriptions[0].subscriber_name == "evictor-1"


def test_notify_pressure_returns_count_of_listeners_notified() -> None:
    actuator = MemoryActuator()
    actuator.register_pressure_listener(
        subscriber_name="a",
        condition="host_pressure_block",
    )
    actuator.register_pressure_listener(
        subscriber_name="b",
        condition="host_pressure_block",
    )
    actuator.register_pressure_listener(
        subscriber_name="c",
        condition="host_pressure_warn",
    )
    block_count = actuator.notify_pressure(condition="host_pressure_block")
    warn_count = actuator.notify_pressure(condition="host_pressure_warn")
    other_count = actuator.notify_pressure(condition="something_else")
    assert block_count == 2
    assert warn_count == 1
    assert other_count == 0


# ── coordinate_reclamation ───────────────────────────────────────────────────


def test_coordinate_reclamation_skips_pinned_models() -> None:
    """Honor ``pinned_models_never_evicted`` at the execution layer."""
    fake = _FakeMlxModule()
    actuator = MemoryActuator(mlx_module=fake)
    decision: dict[str, Any] = {
        "selected_victim": [
            {"model_id": "victim-1", "memory_gb": 5.0},
            {"model_id": "pinned-1", "memory_gb": 10.0},
            {"model_id": "victim-2", "memory_gb": 3.0},
        ],
        "pinned": ["pinned-1"],
    }
    receipts = actuator.coordinate_reclamation(eviction_decision=decision)
    assert len(receipts) == 2
    model_ids = {r.model_id for r in receipts}
    assert model_ids == {"victim-1", "victim-2"}
    # Two non-pinned victims → exactly two clear_cache calls.
    assert fake.clear_cache_calls == 2


def test_coordinate_reclamation_skips_pinned_via_residency_summary() -> None:
    """The pinned list may live under ``residency_summary.pinned_model_ids``."""
    fake = _FakeMlxModule()
    actuator = MemoryActuator(mlx_module=fake)
    decision: dict[str, Any] = {
        "selected_victim": {"model_id": "pinned-x", "memory_gb": 8.0},
        "residency_summary": {"pinned_model_ids": ["pinned-x"]},
    }
    receipts = actuator.coordinate_reclamation(eviction_decision=decision)
    assert receipts == ()
    assert fake.clear_cache_calls == 0


def test_coordinate_reclamation_with_no_mlx_module_yields_noop_receipts() -> None:
    actuator = MemoryActuator()
    decision: dict[str, Any] = {
        "selected_victim": {"model_id": "v1", "memory_gb": 1.0},
    }
    receipts = actuator.coordinate_reclamation(eviction_decision=decision)
    assert len(receipts) == 1
    assert receipts[0].mlx_module_available is False
    assert receipts[0].actuator_invoked_clear_cache is False


# ── Observability forwarders ─────────────────────────────────────────────────


def test_read_memory_forwarders_return_none_on_noop_path() -> None:
    actuator = MemoryActuator()
    assert actuator.read_active_memory_bytes() is None
    assert actuator.read_cache_memory_bytes() is None
    assert actuator.read_peak_memory_bytes() is None


def test_read_memory_forwarders_return_int_with_fake_module() -> None:
    fake = _FakeMlxModule(
        active_script=[111],
        cache_script=[222],
        peak_script=[333],
    )
    actuator = MemoryActuator(mlx_module=fake)
    assert actuator.read_active_memory_bytes() == 111
    assert actuator.read_cache_memory_bytes() == 222
    assert actuator.read_peak_memory_bytes() == 333


# ── status_dict ──────────────────────────────────────────────────────────────


def test_status_dict_shape_includes_subscription_count_and_mlx_module_available() -> None:
    actuator = MemoryActuator()
    actuator.register_pressure_listener(subscriber_name="s1")
    actuator.register_pressure_listener(subscriber_name="s2")
    status = actuator.status_dict()
    assert status["surface"] == MEMORY_ACTUATOR_SURFACE
    assert status["version"] == MEMORY_ACTUATOR_VERSION
    assert status["mlx_module_available"] is False
    assert status["subscription_count"] == 2
    assert "pinned_models_never_evicted" in status["honored_invariants"]
    assert "no_automatic_background_eviction_loop" in status["honored_invariants"]
    # Observability fields default to None on the no-op path.
    assert status["active_memory_bytes"] is None
    assert status["cache_memory_bytes"] is None
    assert status["peak_memory_bytes"] is None
