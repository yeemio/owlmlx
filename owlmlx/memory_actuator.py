"""owlmlx memory actuator scaffold.

Owns the **execution layer** for memory reclamation that the judgment
layer (``memory_budget.py``, ``model_inventory.py``) cannot perform.
Wraps the mlx core memory primitives (``mx.clear_cache``,
``mx.set_cache_limit``, ``mx.set_wired_limit``, ``mx.get_active_memory``,
``mx.get_cache_memory``, ``mx.get_peak_memory``) behind a single
ownership surface. Honors the frozen invariants from
``memory_pressure_eviction_policy.py``: ``pinned_models_never_evicted``
and ``no_automatic_background_eviction_loop``.

Scaffold-grade. The native backend's ``unload`` path is NOT modified to
call this actuator in this round — that wiring is a follow-up. The
scaffold accepts an injectable ``mlx_module`` parameter; when ``None``,
all operations return shaped no-op receipts so callers can integrate
without committing the runtime path to actual memory release yet.

This module closes Line 3 (Memory governance, ``partial``) of the
seven-line architectural assessment recorded in
``docs/source-of-truth/native-mlx-backend-capability-matrix.md`` §7 by
defining the **actuator surface** that the existing judgment layer
cannot expose. It does NOT itself promote any capability matrix row;
that requires real-injection evidence in a follow-up round.

Layering distinction:

- ``memory_budget.py`` — pure-function "can it fit" calculator
  (judgment layer)
- ``model_inventory.py`` — descriptive inventory of loaded models
  (judgment layer)
- ``memory_pressure_eviction_policy.py`` — decides which model to
  evict (judgment layer)
- ``memory_actuator.py`` (this) — actually releases memory back to
  the allocator when given a real injected mlx module (execution
  layer)

Frozen invariants honored:

- ``pinned_models_never_evicted`` — ``coordinate_reclamation`` skips
  any model in the decision's pinned list before invoking
  ``release_single_model``.
- ``no_automatic_background_eviction_loop`` — there is no daemon, no
  thread, no scheduler, no auto-fire path in this module. Pressure
  listeners are notified only via explicit caller-driven
  ``notify_pressure(...)`` calls.

Dependency policy: standard library ``gc`` only. No new third-party
dependencies are introduced by this scaffold.
"""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass, field
from typing import Any, Sequence


MEMORY_ACTUATOR_SURFACE = "owlmlx.memory_actuator"
MEMORY_ACTUATOR_VERSION = "v1"

# These mirror the frozen invariants declared in
# ``owlmlx.memory_pressure_eviction_policy.PRESERVED_INVARIANTS`` that
# this actuator promises to honor at the execution layer.
HONORED_INVARIANTS: tuple[str, ...] = (
    "pinned_models_never_evicted",
    "no_automatic_background_eviction_loop",
)


# ── Receipts and shaped returns ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ReclaimReceipt:
    """Receipt for a single-model reclamation attempt.

    Carries the **measurement** truth so callers can detect whether
    release actually happened, not just whether the actuator was asked
    to release.

    The native backend's ``UnloadResult.freed_gb`` today reports the
    declared ``session.info.memory_gb`` value. This receipt carries
    before/after byte readings from the allocator (when an mlx module
    is injected) so the caller can compare the declared release to the
    measured allocator delta.

    Attributes:
        model_id: Canonical model identifier the receipt covers.
        declared_freed_gb: GB that the caller declared as the model's
            footprint. Echoed for traceability; NOT a measurement.
        active_memory_before_bytes: ``mx.get_active_memory()`` reading
            taken before the release attempt. ``None`` when no mlx
            module is injected (no-op path).
        active_memory_after_bytes: same reading taken after the release
            attempt. ``None`` on no-op.
        cache_memory_before_bytes: ``mx.get_cache_memory()`` reading
            before. ``None`` on no-op.
        cache_memory_after_bytes: ``mx.get_cache_memory()`` reading
            after. ``None`` on no-op.
        actuator_invoked_clear_cache: True iff this receipt corresponds
            to a path that actually invoked ``mlx_module.clear_cache()``.
            Must be False whenever ``mlx_module_available`` is False.
        mlx_module_available: True iff the actuator was constructed
            with a real (or fake) mlx module; False iff the actuator
            is operating in pure scaffold mode (no-op).
    """

    model_id: str
    declared_freed_gb: float
    active_memory_before_bytes: int | None
    active_memory_after_bytes: int | None
    cache_memory_before_bytes: int | None
    cache_memory_after_bytes: int | None
    actuator_invoked_clear_cache: bool
    mlx_module_available: bool

    def to_dict(self) -> dict[str, Any]:
        """Return the receipt as a plain dict for status payloads."""
        return {
            "model_id": self.model_id,
            "declared_freed_gb": self.declared_freed_gb,
            "active_memory_before_bytes": self.active_memory_before_bytes,
            "active_memory_after_bytes": self.active_memory_after_bytes,
            "cache_memory_before_bytes": self.cache_memory_before_bytes,
            "cache_memory_after_bytes": self.cache_memory_after_bytes,
            "actuator_invoked_clear_cache": self.actuator_invoked_clear_cache,
            "mlx_module_available": self.mlx_module_available,
        }


@dataclass(frozen=True, slots=True)
class AllocatorFloorConfig:
    """Result of an allocator-floor configuration call.

    The mlx core exposes ``mx.set_cache_limit(limit)`` (returns the
    previous value) and, on macOS 15+, ``mx.set_wired_limit(limit)``.
    This dataclass records the request the actuator performed, plus
    whether the underlying ``set_wired_limit`` symbol was actually
    available on the injected module.

    Attributes:
        cache_limit_bytes: The cache-memory ceiling the actuator was
            asked to set on the mlx allocator. ``None`` means "not
            requested in this call".
        wired_limit_bytes: The wired-memory ceiling the actuator was
            asked to set. ``None`` means "not requested in this call".
        wired_limit_supported: True iff the injected mlx module exposed
            a ``set_wired_limit`` attribute. Always False when no mlx
            module is injected.
    """

    cache_limit_bytes: int | None
    wired_limit_bytes: int | None
    wired_limit_supported: bool

    def to_dict(self) -> dict[str, Any]:
        """Return the config as a plain dict for status payloads."""
        return {
            "cache_limit_bytes": self.cache_limit_bytes,
            "wired_limit_bytes": self.wired_limit_bytes,
            "wired_limit_supported": self.wired_limit_supported,
        }


@dataclass(frozen=True, slots=True)
class PressureEventSubscription:
    """Record of a caller-driven pressure-event subscription.

    The scaffold maintains a list of these subscriptions. Subscribers
    are notified **only** via an explicit ``MemoryActuator.notify_pressure``
    call from a caller. There is no daemon, no thread, no scheduler; the
    ``no_automatic_background_eviction_loop`` invariant is honored
    literally — a notification fires iff a caller explicitly fires it.

    Attributes:
        subscriber_name: Caller-supplied identifier for the subscriber.
            Used for tracing and dedup at the caller's discretion.
        registered_at: ``time.time()`` reading at registration. Useful
            for ordering and audit.
        condition: The pressure condition the subscriber wants to be
            notified about (e.g., ``"host_pressure_block"``,
            ``"host_pressure_warn"``). Free-form string; the scaffold
            does not validate against an enum because the scaffold does
            not own the pressure-condition vocabulary.
    """

    subscriber_name: str
    registered_at: float
    condition: str

    def to_dict(self) -> dict[str, Any]:
        """Return the subscription as a plain dict for status payloads."""
        return {
            "subscriber_name": self.subscriber_name,
            "registered_at": self.registered_at,
            "condition": self.condition,
        }


# ── Actuator class ───────────────────────────────────────────────────────────


class MemoryActuator:
    """Single-ownership surface for memory reclamation primitives.

    The actuator never auto-imports ``mlx``. Production callers that
    actually want allocator-side release pass a real ``mlx.core`` module
    via the ``mlx_module`` constructor argument. Tests pass a fake
    object that mimics the surface methods. When no module is injected,
    every operation returns a shaped no-op receipt so callers can
    integrate the actuator into their flow before any wiring round
    commits the runtime path to real release.

    The scaffold-vs-wired distinction is intentional: this round adds
    no automatic call from any production path (native backend
    ``unload``, eviction policy execution, etc.). A subsequent round
    flips the injection so those paths receive a real mlx module; this
    scaffold deliberately does not perform that flip.
    """

    def __init__(self, *, mlx_module: object | None = None) -> None:
        """Construct an actuator.

        Args:
            mlx_module: Optional mlx core module (or test fake mimicking
                its surface). If ``None``, the actuator runs in pure
                scaffold mode and every method returns a no-op shape.
                If non-``None``, the actuator will call methods on it
                where appropriate.
        """
        self._mlx_module = mlx_module
        self._subscriptions: list[PressureEventSubscription] = []

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def mlx_module_available(self) -> bool:
        """True iff a real or fake mlx module was injected at construction."""
        return self._mlx_module is not None

    @property
    def subscriptions(self) -> tuple[PressureEventSubscription, ...]:
        """Currently registered pressure-event subscriptions (immutable view)."""
        return tuple(self._subscriptions)

    # ── Single-model release primitive (capability A) ───────────────────────

    def release_single_model(
        self,
        *,
        model_id: str,
        declared_freed_gb: float,
    ) -> ReclaimReceipt:
        """Attempt single-model memory release and return a measured receipt.

        Capability A from the actuator surface. The **only** code path
        in owlmlx that calls ``mlx_module.clear_cache()``, and only
        when an mlx module was injected at construction. The native
        backend's existing ``unload`` is NOT modified to call this in
        this round; integration is a follow-up extension point.

        Args:
            model_id: Canonical model identifier whose memory the caller
                believes was just released by some upstream unload.
            declared_freed_gb: GB the caller declared as the model's
                footprint. Echoed onto the receipt; the actuator does
                not validate this value.

        Returns:
            A ``ReclaimReceipt`` with before/after allocator readings
            (when mlx is injected) or all ``None`` byte fields (no-op
            mode).
        """
        if self._mlx_module is None:
            return ReclaimReceipt(
                model_id=model_id,
                declared_freed_gb=declared_freed_gb,
                active_memory_before_bytes=None,
                active_memory_after_bytes=None,
                cache_memory_before_bytes=None,
                cache_memory_after_bytes=None,
                actuator_invoked_clear_cache=False,
                mlx_module_available=False,
            )

        active_before = self._safe_int_call("get_active_memory")
        cache_before = self._safe_int_call("get_cache_memory")

        # gc.collect() is stdlib; safe to call regardless of mlx state.
        gc.collect()

        # The single sanctioned mlx.clear_cache() call site in owlmlx.
        clear_cache = getattr(self._mlx_module, "clear_cache", None)
        invoked = False
        if callable(clear_cache):
            clear_cache()
            invoked = True

        active_after = self._safe_int_call("get_active_memory")
        cache_after = self._safe_int_call("get_cache_memory")

        return ReclaimReceipt(
            model_id=model_id,
            declared_freed_gb=declared_freed_gb,
            active_memory_before_bytes=active_before,
            active_memory_after_bytes=active_after,
            cache_memory_before_bytes=cache_before,
            cache_memory_after_bytes=cache_after,
            actuator_invoked_clear_cache=invoked,
            mlx_module_available=True,
        )

    # ── Multi-model coordinated reclamation (capability B) ──────────────────

    def coordinate_reclamation(
        self,
        *,
        eviction_decision: dict[str, Any],
    ) -> Sequence[ReclaimReceipt]:
        """Translate an eviction decision into a sequence of release calls.

        Capability B from the actuator surface. Accepts a dict shaped
        like ``MemoryPressureEvictionPolicy`` (this module does NOT
        import that module — it accepts the dict so the dependency
        flows from caller to actuator, not the reverse).

        Honors ``pinned_models_never_evicted``: any model whose id
        appears in the decision's ``pinned`` list (or under
        ``residency_summary.pinned_model_ids``) is skipped before
        invoking ``release_single_model``.

        Args:
            eviction_decision: Dict-shape mirror of the policy's
                serialized decision. Expected keys (all optional, all
                tolerated as missing):

                - ``selected_victim``: dict with at least
                  ``model_id`` and optionally ``memory_gb``; or a list
                  of such dicts when the policy expands to batch evict
                  (current production form is single-victim).
                - ``pinned``: list of pinned ``model_id`` strings, or
                - ``residency_summary``: dict with ``pinned_model_ids``
                  list as a fallback location.

        Returns:
            One ``ReclaimReceipt`` per non-pinned victim that was
            attempted. Returns an empty sequence if the decision has no
            actionable victims.
        """
        pinned = _extract_pinned_ids(eviction_decision)
        victims = _extract_victims(eviction_decision)

        receipts: list[ReclaimReceipt] = []
        for victim in victims:
            model_id = str(victim.get("model_id") or "").strip()
            if not model_id:
                continue
            if model_id in pinned:
                # Honor pinned_models_never_evicted: skip the call entirely.
                continue
            # We do not have inventory access from this layer, so the
            # declared footprint defaults to 0.0. Future extension point:
            # pass through inventory lookup so receipts carry the real
            # declared GB. The point of this scaffold round is to lock the
            # actuator surface, not to wire inventory through.
            declared = float(victim.get("memory_gb") or 0.0)
            receipts.append(
                self.release_single_model(
                    model_id=model_id,
                    declared_freed_gb=declared,
                )
            )
        return tuple(receipts)

    # ── Allocator floor configuration (capability C) ────────────────────────

    def configure_allocator_floor(
        self,
        *,
        cache_limit_bytes: int | None = None,
        wired_limit_bytes: int | None = None,
    ) -> AllocatorFloorConfig:
        """Configure mlx allocator caps at the scaffold surface.

        Capability C from the actuator surface. Wraps
        ``mx.set_cache_limit`` and (when available) ``mx.set_wired_limit``.

        ``set_wired_limit`` is macOS 15+ only; presence is detected via
        ``hasattr`` on the injected module rather than a version check
        because the scaffold does not assume which mlx version is
        installed.

        Args:
            cache_limit_bytes: Requested ``mx.set_cache_limit`` value
                in bytes. ``None`` to leave the cache cap untouched.
            wired_limit_bytes: Requested ``mx.set_wired_limit`` value
                in bytes. ``None`` to leave the wired cap untouched.
                Even when non-``None``, the call is skipped if the
                injected mlx module does not expose
                ``set_wired_limit``.

        Returns:
            An ``AllocatorFloorConfig`` echoing the requested values
            and recording whether ``set_wired_limit`` was reachable.
        """
        if self._mlx_module is None:
            return AllocatorFloorConfig(
                cache_limit_bytes=cache_limit_bytes,
                wired_limit_bytes=wired_limit_bytes,
                wired_limit_supported=False,
            )

        if cache_limit_bytes is not None:
            set_cache_limit = getattr(self._mlx_module, "set_cache_limit", None)
            if callable(set_cache_limit):
                set_cache_limit(cache_limit_bytes)

        wired_supported = hasattr(self._mlx_module, "set_wired_limit")
        if wired_limit_bytes is not None and wired_supported:
            set_wired_limit = getattr(self._mlx_module, "set_wired_limit", None)
            if callable(set_wired_limit):
                set_wired_limit(wired_limit_bytes)

        return AllocatorFloorConfig(
            cache_limit_bytes=cache_limit_bytes,
            wired_limit_bytes=wired_limit_bytes,
            wired_limit_supported=wired_supported,
        )

    # ── Pressure-event seam (capability D, caller-driven only) ──────────────

    def register_pressure_listener(
        self,
        *,
        subscriber_name: str,
        condition: str = "host_pressure_block",
    ) -> PressureEventSubscription:
        """Register a caller-driven pressure-event subscription.

        Capability D from the actuator surface. The scaffold maintains
        the subscription list and exposes ``notify_pressure(...)`` for
        callers to fire notifications **explicitly**. There is no
        daemon, no thread, no scheduler; the
        ``no_automatic_background_eviction_loop`` invariant is honored
        literally.

        Args:
            subscriber_name: Caller-supplied identifier. The scaffold
                does not enforce uniqueness; the caller may dedup as
                needed.
            condition: Pressure condition the subscriber wants to track
                (free-form string; defaults to ``"host_pressure_block"``).

        Returns:
            The newly created ``PressureEventSubscription``.
        """
        subscription = PressureEventSubscription(
            subscriber_name=subscriber_name,
            registered_at=time.time(),
            condition=condition,
        )
        self._subscriptions.append(subscription)
        return subscription

    def notify_pressure(self, *, condition: str) -> int:
        """Fire pressure-event notifications to matching subscribers.

        Caller-driven trigger. The scaffold returns the count of
        subscribers whose ``condition`` matches the call argument; in
        this round notifications are an accounting concept (no callback
        invocation), so the count is what the caller observes.

        A future extension may carry callbacks on the subscription
        record; that is deliberately deferred so this round commits no
        callable surface that would later be hard to evolve.

        Args:
            condition: Pressure condition string the caller is firing.

        Returns:
            Number of subscriptions whose ``condition`` equals the
            argument exactly.
        """
        return sum(1 for s in self._subscriptions if s.condition == condition)

    # ── Read-only observability (capability E) ──────────────────────────────

    def read_active_memory_bytes(self) -> int | None:
        """Forwarder for ``mx.get_active_memory()``; ``None`` on no-op."""
        return self._safe_int_call("get_active_memory")

    def read_cache_memory_bytes(self) -> int | None:
        """Forwarder for ``mx.get_cache_memory()``; ``None`` on no-op."""
        return self._safe_int_call("get_cache_memory")

    def read_peak_memory_bytes(self) -> int | None:
        """Forwarder for ``mx.get_peak_memory()``; ``None`` on no-op."""
        return self._safe_int_call("get_peak_memory")

    # ── Status payload helper ───────────────────────────────────────────────

    def status_dict(self) -> dict[str, Any]:
        """Return the actuator status for runtime status payloads.

        Embeddable into the runtime status surface so operators can
        observe the actuator's current shape without exercising any
        side-effect path.
        """
        return {
            "surface": MEMORY_ACTUATOR_SURFACE,
            "version": MEMORY_ACTUATOR_VERSION,
            "mlx_module_available": self.mlx_module_available,
            "subscription_count": len(self._subscriptions),
            "honored_invariants": list(HONORED_INVARIANTS),
            "active_memory_bytes": self.read_active_memory_bytes(),
            "cache_memory_bytes": self.read_cache_memory_bytes(),
            "peak_memory_bytes": self.read_peak_memory_bytes(),
        }

    # ── Internal helpers ────────────────────────────────────────────────────

    def _safe_int_call(self, attribute: str) -> int | None:
        """Call a zero-arg int-returning attribute on the injected module.

        Returns ``None`` when no mlx module is injected, when the
        attribute is missing, when it is not callable, or when the call
        raises (the scaffold does not propagate exceptions through the
        observability path).
        """
        if self._mlx_module is None:
            return None
        fn = getattr(self._mlx_module, attribute, None)
        if not callable(fn):
            return None
        try:
            value = fn()
        except Exception:  # noqa: BLE001 — observability never raises
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


# ── Free-function helpers (kept private to avoid surface-area inflation) ─────


def _extract_pinned_ids(decision: dict[str, Any]) -> set[str]:
    """Pull a set of pinned model_ids out of a decision dict.

    Accepts either ``pinned`` (top-level list) or
    ``residency_summary.pinned_model_ids``. Returns an empty set when
    neither is present.
    """
    candidates: list[Any] = []
    pinned_field = decision.get("pinned")
    if isinstance(pinned_field, (list, tuple)):
        candidates.extend(pinned_field)
    residency = decision.get("residency_summary")
    if isinstance(residency, dict):
        residency_pinned = residency.get("pinned_model_ids")
        if isinstance(residency_pinned, (list, tuple)):
            candidates.extend(residency_pinned)
    return {str(item).strip() for item in candidates if isinstance(item, str) and item.strip()}


def _extract_victims(decision: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull a list of victim dicts out of a decision dict.

    Tolerates the production single-victim shape (``selected_victim``
    is a single dict) and a future batch shape (``selected_victim`` is
    a list of dicts). Returns an empty list when nothing is present.
    """
    victims: list[dict[str, Any]] = []
    field_value = decision.get("selected_victim")
    if isinstance(field_value, dict):
        victims.append(field_value)
    elif isinstance(field_value, (list, tuple)):
        for item in field_value:
            if isinstance(item, dict):
                victims.append(item)
    return victims


# ── Future extension points (NOT implemented in this round) ──────────────────
#
# 1. macOS Mach pressure subscription via pyobjc.
#    The current ``host_pressure.py`` shells out to ``memory_pressure``
#    once at admission time. A future round may add a Mach kernel
#    notification subscription for ``DISPATCH_MEMORYPRESSURE_*`` events;
#    when that lands, the auto-fire path would still be **caller-driven
#    here**: the Mach listener would call ``notify_pressure(...)`` on
#    a registered actuator instance. This module would gain no daemon
#    of its own.
#
# 2. Native backend ``unload`` integration.
#    ``owlmlx/runtime/mlx_native_backend.py:314-335`` drops session
#    references but does not call ``mx.clear_cache()``. A future round
#    will inject a ``MemoryActuator`` instance into the native backend
#    so its ``unload`` can call ``release_single_model(...)`` after
#    dropping references and report a measured ``ReclaimReceipt``. That
#    round must also extend the capability matrix legend if it claims
#    a new row's promotion.
#
# 3. Inventory-aware ``coordinate_reclamation``.
#    The current scaffold defaults ``declared_freed_gb`` to whatever is
#    on the victim dict (typically 0.0 unless the policy already
#    recorded ``memory_gb``). A future round may accept a callable that
#    resolves model_id → memory_gb via ``model_inventory.py``, so the
#    receipts carry the same declared GB the inventory layer would
#    have reported.
