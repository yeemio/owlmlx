# owlmlx Memory Actuator — Architecture (Scaffold-Grade)

> Status: authoritative (scaffold-grade)
> Updated: 2026-05-08
> Scope: execution-layer surface for memory reclamation in `owlmlx`,
> wrapping the mlx core memory primitives behind a single ownership
> point.
> Author: owlmlx C-3 round.

## 1. Why This Module Exists

The seven-line architectural assessment recorded in
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` §7 lists
**Line 3 — Memory governance** as `partial`. The recommended next
surface for that line is "a memory actuator layer wrapping
`mx.clear_cache` / `set_cache_limit`." This document records the
scaffold-grade landing of that layer. Line 3 remains `partial`; this
scaffold lands the actuator surface but does not close or promote the
line.

Before this scaffold, owlmlx could **judge** memory questions but could
not **act** on them:

- `owlmlx/memory_budget.py` answers "can it fit?" as a pure-function
  calculator. No side effects, no allocator interaction.
- `owlmlx/model_inventory.py` describes which models are present in
  the runtime. No handle, no pid, no allocator reference.
- `owlmlx/memory_pressure_eviction_policy.py` decides which model to
  evict given pressure inputs. The policy emits a decision; nothing
  in this module nor `multi_model_eviction_history_governance.py`
  executes one.
- `owlmlx/host_pressure.py` shells out to macOS `memory_pressure` once
  at admission time and returns a snapshot. It does not subscribe to
  pressure events nor call any allocator.

The mlx core surface verified to exist on the installed `.venv` (string
extraction of the compiled `mlx/core.cpython-311-darwin.so`) exposes
`mx.clear_cache`, `mx.set_memory_limit`, `mx.set_cache_limit`,
`mx.set_wired_limit` (macOS 15+), `mx.get_active_memory`,
`mx.get_peak_memory`, `mx.reset_peak_memory`, and `mx.get_cache_memory`.
**owlmlx today calls none of them.** The native backend's `unload`
path at `owlmlx/runtime/mlx_native_backend.py:314-335` drops session
references but does not invoke `mx.clear_cache()`; its
`UnloadResult.freed_gb` reports the declared `session.info.memory_gb`
value, not a measured allocator delta.

The judgment-vs-actuator gap is the subject of this scaffold. The
module **defines the actuator surface**; it does not change any
production runtime path's behavior.

## 2. Status / Scope

- Module: `owlmlx/memory_actuator.py` (this round adds it).
- Tests: `tests/test_memory_actuator.py` (this round adds them; all
  use fake-injected mlx modules, no real `mlx` import).
- Round: C-3 (Line 3 — Memory governance).
- Out of scope for this round: modifying `mlx_native_backend.py`,
  `mlx_lm_subprocess_backend.py`, `memory_pressure_eviction_policy.py`,
  or any caller. The scaffold lands the surface; a follow-up wires
  callers.

## 3. Ownership Boundaries

| Concern | Module | Layer |
|---|---|---|
| Pure "can it fit?" arithmetic | `memory_budget.py` | judgment |
| Loaded-model inventory description | `model_inventory.py` | judgment |
| Eviction-decision policy | `memory_pressure_eviction_policy.py` | judgment |
| Eviction-history record | `multi_model_eviction_history_governance.py` | observability |
| Host memory-pressure sampling | `host_pressure.py` | observability (probe) |
| **Allocator-side memory release** | **`memory_actuator.py` (this)** | **execution** |

This is the missing actuator. No other owlmlx module today actually
invokes `mx.clear_cache()`, `mx.set_cache_limit(...)`, or
`mx.set_wired_limit(...)`. The native backend's `unload` truly drops
references but does not signal the allocator; the subprocess backend's
`unload` truly frees memory only because subprocess termination tears
down the address space. Neither path measures the allocator.

## 4. Scaffold Contract

### 4.1 `MemoryActuator`

Constructor: `MemoryActuator(*, mlx_module: object | None = None)`.

The actuator never auto-imports `mlx`. Production callers that want
real allocator-side release must pass a real `mlx.core` module via
`mlx_module`. Tests pass a fake object that mimics the surface
methods. When `mlx_module is None`, every operation returns a shaped
no-op so callers can integrate the actuator into their flow before any
wiring round commits the runtime path to real release.

Public methods:

- `release_single_model(*, model_id, declared_freed_gb) -> ReclaimReceipt`
  — capability A, the **only** call site of `mlx_module.clear_cache()`
  in owlmlx. Reads `get_active_memory()` and `get_cache_memory()`
  before and after, calls `gc.collect()`, then `clear_cache()` (when
  available on the injected module).
- `coordinate_reclamation(*, eviction_decision) -> Sequence[ReclaimReceipt]`
  — capability B, accepts a dict shaped like the serialized
  `MemoryPressureEvictionPolicy` decision. Honors
  `pinned_models_never_evicted` by skipping any victim whose id is in
  the decision's pinned list. Calls `release_single_model` per
  non-pinned victim.
- `configure_allocator_floor(*, cache_limit_bytes=None, wired_limit_bytes=None) -> AllocatorFloorConfig`
  — capability C, wraps `mx.set_cache_limit` and (when reachable via
  `hasattr`) `mx.set_wired_limit`.
- `register_pressure_listener(*, subscriber_name, condition="host_pressure_block") -> PressureEventSubscription`
  / `notify_pressure(*, condition) -> int` — capability D, **caller-
  driven only**. Subscribers are notified iff a caller invokes
  `notify_pressure`; the scaffold creates no daemon, no thread, no
  scheduler.
- `read_active_memory_bytes() -> int | None`,
  `read_cache_memory_bytes() -> int | None`,
  `read_peak_memory_bytes() -> int | None` — capability E, observability
  forwarders that return `None` on the no-op path.
- `status_dict() -> dict` — runtime status payload for the actuator.

### 4.2 `ReclaimReceipt`

```python
@dataclass(frozen=True, slots=True)
class ReclaimReceipt:
    model_id: str
    declared_freed_gb: float
    active_memory_before_bytes: int | None
    active_memory_after_bytes: int | None
    cache_memory_before_bytes: int | None
    cache_memory_after_bytes: int | None
    actuator_invoked_clear_cache: bool
    mlx_module_available: bool
```

`to_dict()` returns the receipt as a plain dict for status payloads.

### 4.3 `AllocatorFloorConfig`

```python
@dataclass(frozen=True, slots=True)
class AllocatorFloorConfig:
    cache_limit_bytes: int | None
    wired_limit_bytes: int | None
    wired_limit_supported: bool
```

`wired_limit_supported` reflects `hasattr(mlx_module, "set_wired_limit")`
on the injected module; always False on the no-op path.

### 4.4 `PressureEventSubscription`

```python
@dataclass(frozen=True, slots=True)
class PressureEventSubscription:
    subscriber_name: str
    registered_at: float
    condition: str
```

## 5. Frozen Invariants Honored

`memory_pressure_eviction_policy.PRESERVED_INVARIANTS` (lines 30-36 of
that module) declares two invariants this actuator scaffold honors at
the execution layer:

### 5.1 `pinned_models_never_evicted`

The judgment layer guarantees the policy will not select a pinned
model as a victim. The execution layer must guarantee the same: even
if a malformed decision dict listed a pinned model under
`selected_victim`, `coordinate_reclamation` would still skip it. This
is enforced by `_extract_pinned_ids(decision)` — pinned ids are
gathered from both `decision["pinned"]` (top-level) and
`decision["residency_summary"]["pinned_model_ids"]` (fallback) — and a
victim with a matching id is dropped before `release_single_model`
runs.

### 5.2 `no_automatic_background_eviction_loop`

This is a literal-text invariant. The scaffold contains zero of:

- `threading.Thread` instances
- `asyncio.create_task` invocations
- `concurrent.futures` executors
- `signal` handler installations
- `atexit` registrations
- `sched`-style schedulers
- daemon-style `while True:` loops in any method

`notify_pressure(...)` returns a count of matching subscribers; it
**does not** invoke any callback. A future round may add callable
hooks on the subscription record, but in this round the trigger is a
caller-side fact, not an actuator-side cron. Tests assert that no
thread is spawned during construction.

## 6. mlx Primitive Map

| mlx core symbol | Actuator method | Notes |
|---|---|---|
| `mx.clear_cache()` | `release_single_model` | Sole call site in owlmlx; only via injected module. |
| `mx.set_cache_limit(limit)` | `configure_allocator_floor` | Returns previous on real mlx; scaffold ignores return. |
| `mx.set_wired_limit(limit)` | `configure_allocator_floor` | macOS 15+ only; presence detected via `hasattr`. |
| `mx.set_memory_limit(limit)` | (not bound this round) | Reserved for future cap-management round. |
| `mx.get_active_memory()` | `read_active_memory_bytes` + receipts | Observability forwarder. |
| `mx.get_cache_memory()` | `read_cache_memory_bytes` + receipts | Observability forwarder. |
| `mx.get_peak_memory()` | `read_peak_memory_bytes` | Observability forwarder. |
| `mx.reset_peak_memory()` | (not bound this round) | Reserved; coupled with peak-tracker round. |
| `mx.metal.is_available()` / `mx.metal.device_info()` | (not bound this round) | Device-introspection lives in `mlx_environment.py`. |

## 7. Measure-Not-Declare Contract

The native backend's `UnloadResult.freed_gb` at
`owlmlx/runtime/mlx_native_backend.py:325` reports the declared
`session.info.memory_gb` value. That number is what the caller said
the model was, not a measurement of what was released back to the
allocator.

`ReclaimReceipt` carries before/after byte readings precisely so the
caller can compare:

- declared (`declared_freed_gb`, echoed from caller),
- vs. measured cache delta (`cache_memory_before_bytes -
  cache_memory_after_bytes`),
- vs. measured active delta (`active_memory_before_bytes -
  active_memory_after_bytes`).

When the deltas disagree with the declaration by an unexpectedly large
margin, the caller has the data to surface a discrepancy. This is the
hook that lets a future round introduce a "release verified" signal
without re-plumbing the surface.

In the no-op path (no mlx module injected) all four byte fields are
`None` and `actuator_invoked_clear_cache` is False. Callers should
treat a no-op receipt as "nothing was measured because nothing was
actuated", not as "release succeeded with zero delta".

## 8. No-Op-When-No-mlx Pattern

The scaffold deliberately commits to a single shape regardless of
whether mlx is reachable:

- with `mlx_module=None`: every method returns a shaped no-op (receipt
  with `mlx_module_available=False`, config with
  `wired_limit_supported=False`, observability returning `None`).
- with `mlx_module=<real or fake>`: the same shapes are returned,
  populated.

This pattern lets the wiring round (a future round, deliberately not
this one) flip injection at the call site without changing any caller's
shape contract. Tests use this pattern to verify behavior **without**
importing real `mlx`: a fake module exposes the surface methods with
recorder-style stubs, and the actuator drives them.

The pattern is the boundary. Production callers can only get real
release by passing a real `mx` module. Tests pass fakes. The scaffold
round wires nothing automatically.

## 9. Pressure-Event Seam — Caller-Driven Only

Capability D is the most easily corrupted of the five — it is the one
where a "convenience" implementation would reach for a daemon thread
that polls `host_pressure.sample_host_pressure(...)` and auto-fires
listeners. **The scaffold deliberately does not provide that.**

The seam shape is:

1. A caller registers a subscription via
   `register_pressure_listener(...)`. The actuator records a
   `PressureEventSubscription` carrying `subscriber_name`,
   `registered_at`, and `condition`.
2. Some other caller (later, deliberately) invokes
   `notify_pressure(condition=...)`. The actuator counts matching
   subscriptions and returns the count.
3. There is no callback. There is no thread. There is no scheduler.

A future Mach pressure subscription (future extension point §11.1)
would still fire through this same seam: the Mach listener would call
`notify_pressure(...)` from within whatever event loop owns it. The
actuator would gain no daemon of its own.

This is the literal honoring of `no_automatic_background_eviction_loop`.

## 10. Promotion-Gate Coupling

This scaffold round does **not** advance any
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` row's
state. The matrix's promotion gate (§1a Anti-Pollution Contract)
requires declared-provenance real-candidate evidence to advance from
`partial` to `supported`. A scaffold-only landing of an actuator
surface, exercised exclusively against fake-injected mlx modules,
does not meet that bar.

When a follow-up round wires the native backend's `unload` path to
call `release_single_model(...)` against a real `mx` module on a real
admitted candidate, that round may propose:

- a new matrix row (e.g., "Memory release actuator wiring"), or
- promotion of an existing row to reflect the new evidence.

That round must produce real before/after `ReclaimReceipt` byte
deltas and run the §1a walkthrough; this scaffold round does not.

The seven-line assessment's Line 3 status remains **`partial`**. The
scaffold makes the actuator surface explicit, but closure still
requires real native-unload wiring plus measured `ReclaimReceipt`
byte deltas.

## 11. Extension Points (Not Implemented)

These are recorded so future rounds know the deferred work and can
reference this scaffold without re-deriving the shape.

### 11.1 macOS Mach pressure subscription via `pyobjc`

`host_pressure.sample_host_pressure(...)` shells out once at admission
time. A future round may add a kernel notification subscription for
`DISPATCH_MEMORYPRESSURE_NORMAL/WARN/CRITICAL`, calling
`notify_pressure(...)` on a registered actuator. This requires
`pyobjc` (currently not a dependency); it is deliberately deferred
until a separate round can evaluate the dependency cost.

### 11.2 Native unload integration

`owlmlx/runtime/mlx_native_backend.py:314-335` will be modified in a
follow-up round to receive a `MemoryActuator` (constructor injection)
and call `release_single_model(...)` after dropping references. The
existing `UnloadResult.freed_gb` will continue to carry the declared
value; the receipt will travel alongside it on the response detail.

### 11.3 Inventory-aware coordinate_reclamation

Today `coordinate_reclamation` defaults `declared_freed_gb` to
whatever is on the victim dict (typically 0.0 unless the policy
already recorded `memory_gb`). A future round may accept a callable
that resolves `model_id → memory_gb` via `model_inventory.py`, so
receipts carry the inventory's declared value rather than the
policy's transcribed copy.

### 11.4 set_memory_limit / reset_peak_memory binding

These two mlx primitives are intentionally not bound in capability C.
A future cap-management round will attach them once the wider memory-
governance vocabulary stabilizes. The scaffold leaves the door open by
keeping `configure_allocator_floor`'s shape flat (no nested config
blob).

## 12. What This Doc Does Not Claim

- It does not claim the actuator releases memory. Releasing memory
  requires a real injected `mx` module, which the scaffold round
  does not arrange.
- It does not claim the native backend has been modified. Per the
  round's hard rules, `mlx_native_backend.py` is read-only outside
  the actuator scaffold.
- It does not claim any capability matrix row has been promoted. The
  matrix promotion gate requires real-candidate evidence; the scaffold
  produces fake-injected evidence only.
- It does not claim `pinned_models_never_evicted` is enforced
  end-to-end against production paths. The scaffold honors it within
  `coordinate_reclamation`, but no production path calls
  `coordinate_reclamation` in this round.
- It does not claim the pressure-event seam is hooked up to host
  pressure. `notify_pressure(...)` is caller-driven; nothing in
  `host_pressure.py` calls it today.
- It does not claim `gc.collect()` is sufficient to release model
  memory. The actuator calls it as a defensive prelude to
  `clear_cache()` so dangling Python references are dropped before
  the allocator is signalled; the actual release semantics are
  governed by mlx core, not by this scaffold.
- It does not claim training memory governance. Training stays
  deferred per the program contract recorded in `memory_budget.py`'s
  module docstring.
