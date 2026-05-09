# owlmlx Memory Actuator — Scaffold Landing Round (C-3)

## You Are

You are the `owlmlx` main-line executor.

The seven-line architectural assessment recorded in
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` §7 lists
**Line 3 — Memory governance** as `partial`. The recommended close is
"a memory actuator layer wrapping `mx.clear_cache` / `set_cache_limit`."

This round is the **scaffold-grade landing** of that layer. It defines
the actuator surface; it does not wire any production caller, does not
modify the native backend's `unload`, and does not promote any
capability matrix row.

## Single-Round Goal

Produce a brand-new `owlmlx/memory_actuator.py` module that:

- defines five capabilities (single-model release, multi-model
  coordinated reclamation, allocator floor configuration,
  caller-driven pressure-event seam, read-only observability),
- works with an injectable `mlx_module` parameter that defaults to
  `None` (no-op path),
- honors the frozen invariants `pinned_models_never_evicted` and
  `no_automatic_background_eviction_loop` literally, with no thread,
  daemon, or scheduler in any code path.

Land the architecture doc, scaffold tests, this round prompt, and a
coordinator checkpoint that records the surface freeze.

## What This Round **Does NOT** Do (Hard Rules)

- **Does not** modify `owlmlx/runtime/mlx_native_backend.py`,
  `owlmlx/runtime/mlx_lm_subprocess_backend.py`, or
  `owlmlx/runtime/server.py`.
- **Does not** modify `owlmlx/memory_budget.py`,
  `owlmlx/model_inventory.py`,
  `owlmlx/memory_pressure_eviction_policy.py`,
  `owlmlx/memory_pressure_contract.py`,
  `owlmlx/multi_model_eviction_history_governance.py`,
  `owlmlx/host_pressure.py`.
- **Does not** modify `pyproject.toml`, `uv.lock`, `.python-version`,
  `conftest.py`, `README.md`, or any existing test file.
- **Does not** add a new third-party dependency. The standard library
  module `gc` is fine; nothing else new.
- **Does not** call `mx.clear_cache()` from any production runtime
  path. The scaffold's `release_single_model` calls
  `mlx_module.clear_cache()` only when an mlx module was injected at
  construction; no production caller injects one in this round.
- **Does not** import real `mlx` from any test. Tests use
  fake-injected modules exclusively.
- **Does not** spawn any thread, start any daemon, register any
  signal handler, install any `atexit` callback, or run any
  `while True:` loop.
- **Does not** promote any row in
  `docs/source-of-truth/native-mlx-backend-capability-matrix.md`.
- **Does not** stage or commit any change. Working-tree only.
- **Does not** run `pytest`.

## What This Round Does

### 1. Add `owlmlx/memory_actuator.py`

The scaffold module. Surface:

- `class MemoryActuator(*, mlx_module=None)` — no auto-import of
  `mlx`. Production callers pass `mx`; tests pass fakes.
- `release_single_model(*, model_id, declared_freed_gb)` →
  `ReclaimReceipt`. The **only** call site of
  `mlx_module.clear_cache()` in owlmlx. Reads
  `get_active_memory()` / `get_cache_memory()` before and after,
  calls `gc.collect()`, then `clear_cache()` (when reachable on the
  injected module). On `mlx_module=None`, returns a shaped no-op
  receipt (all byte fields `None`,
  `actuator_invoked_clear_cache=False`).
- `coordinate_reclamation(*, eviction_decision)` →
  `Sequence[ReclaimReceipt]`. Accepts a dict shaped like the
  serialized policy decision; honors `pinned_models_never_evicted` by
  skipping any victim whose id is in the decision's pinned list.
- `configure_allocator_floor(*, cache_limit_bytes=None,
  wired_limit_bytes=None)` → `AllocatorFloorConfig`. Wraps
  `set_cache_limit` and (when reachable via `hasattr`)
  `set_wired_limit`. macOS 15+ sensitivity is via attribute presence,
  not version check.
- `register_pressure_listener(*, subscriber_name,
  condition="host_pressure_block")` →
  `PressureEventSubscription` and `notify_pressure(*, condition)` →
  `int`. Caller-driven only. No daemon, no thread.
- `read_active_memory_bytes()`, `read_cache_memory_bytes()`,
  `read_peak_memory_bytes()`, `status_dict()`.

Frozen `@dataclass(frozen=True, slots=True)` records:

- `ReclaimReceipt(model_id, declared_freed_gb,
  active_memory_before_bytes, active_memory_after_bytes,
  cache_memory_before_bytes, cache_memory_after_bytes,
  actuator_invoked_clear_cache, mlx_module_available)` with `to_dict()`.
- `AllocatorFloorConfig(cache_limit_bytes, wired_limit_bytes,
  wired_limit_supported)` with `to_dict()`.
- `PressureEventSubscription(subscriber_name, registered_at,
  condition)` with `to_dict()`.

Module docstring states ownership (execution layer vs. judgment layer)
and cites Line 3 of the seven-line architectural assessment. Comments
record three "future extension points" that are deliberately not
implemented this round (Mach pressure subscription, native unload
integration, inventory-aware coordinate reclamation).

### 2. Add `docs/source-of-truth/memory-actuator-architecture.md`

Architecture doc covering:

1. Status, scope, authorship, round (C-3).
2. Why this module exists — Line 3 (`partial`); the judgment-vs-actuator gap.
3. Ownership boundaries — table comparing the actuator to
   `memory_budget.py`, `model_inventory.py`,
   `memory_pressure_eviction_policy.py`,
   `multi_model_eviction_history_governance.py`,
   `host_pressure.py`. Explicit: this module is the missing
   actuator.
4. Scaffold contract — public API + receipt / config / subscription
   shapes.
5. Frozen invariants honored — how the scaffold respects each.
6. mlx primitive map — table mapping each mlx symbol to an actuator
   method.
7. Measure-not-declare contract — receipts carry before/after byte
   readings so callers can detect whether release actually happened.
8. No-op-when-no-mlx pattern — explicit boundary.
9. Pressure-event seam — caller-driven only.
10. Promotion-gate coupling — explicit: this scaffold round does not
    advance any matrix row.
11. Extension points (not implemented).
12. What this doc does not claim.

### 3. Add `tests/test_memory_actuator.py`

8-12 tests, all using fake-injected mlx-shaped modules. Coverage:

- starts with no subscriptions
- no thread spawned during init / register / notify
- release with no mlx module returns no-op receipt
- release with no mlx module never attempts `clear_cache`
- release with fake module calls `clear_cache` exactly once
- release with fake module records before/after byte readings
- configure floor with no mlx echoes args (no-op)
- configure floor with fake calls `set_cache_limit`
- configure floor skips `set_wired_limit` when fake lacks the attribute
- register pressure listener creates subscription with provided name
- notify pressure returns count of matching listeners
- coordinate reclamation skips pinned models (top-level pinned list)
- coordinate reclamation skips pinned via residency_summary
- coordinate reclamation with no mlx yields no-op receipts
- read forwarders return `None` on no-op
- read forwarders return int with fake module
- status_dict shape includes subscription count and mlx availability

Tests must NOT import real `mlx`, NOT import the native backend, NOT
load any model.

### 4. This Round Prompt
`files/execution-prompts/owlmlx/owlmlx-memory-actuator-scaffold-landing.md`
(this file).

### 5. Coordinator Checkpoint
`files/execution-prompts/owlmlx/coordinator-checkpoint-memory-actuator-scaffold-landed.md`.

## Acceptance Shape

After landing the five files, working tree contains:

- `owlmlx/memory_actuator.py` (new)
- `docs/source-of-truth/memory-actuator-architecture.md` (new)
- `tests/test_memory_actuator.py` (new)
- `files/execution-prompts/owlmlx/owlmlx-memory-actuator-scaffold-landing.md` (new)
- `files/execution-prompts/owlmlx/coordinator-checkpoint-memory-actuator-scaffold-landed.md` (new)

`git status --short` shows exactly these five new files (`??`) plus
whatever was already-staged / already-modified in the workspace before
the round began. Nothing else outside this list is modified.

## Discipline Recap

1. Read-only outside the five deliverable paths.
2. Evidence-language: "scaffold contract" / "no-op when not injected"
   / "extension point". Never "actuator works" / "memory is released"
   without injected real mlx.
3. Frozen invariants are non-negotiable.
4. No staging.
5. No `pytest` run.
6. No new dependencies.
7. `mlx_module` injection pattern is THE boundary.
8. Run `git status --short` after edits and report.

## Next Authorized Round (After This One)

After the surface is frozen:

- **Native backend `unload` integration.** Modify
  `owlmlx/runtime/mlx_native_backend.py:314-335` to receive a
  `MemoryActuator` (constructor injection), call
  `release_single_model(...)` after dropping references, and emit
  the receipt on the `UnloadResult.detail`. That round must produce
  real before/after byte deltas against an admitted candidate to
  qualify for any matrix-row promotion under the §1a Anti-Pollution
  Contract.

This scaffold round closes Line 3 in the seven-line assessment in
`partial (closed by scaffold)` form. Promotion to a stronger label
requires the wiring round above, not just this scaffold.
