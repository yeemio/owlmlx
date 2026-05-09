# owlmlx Coordinator Checkpoint — Memory Actuator Wired into Native Unload (C-3.1)

## Verdict

- `memory_actuator_wired_into_native_unload_first_owlmlx_call_to_clear_cache`

`MlxNativeBackend.unload` now invokes
`memory_actuator.release_single_model(...)` after the cache_manager
release and after dropping session refs. This is the **first owlmlx
code path** that calls `mx.clear_cache()` on the production unload
path. When `mlx.core` is not importable (no `runtime` extra), the
actuator returns a shaped no-op receipt and existing "drop refs and
hope" behavior is preserved exactly. The most recent receipt is
observable on `backend._last_unload_receipt` for tests and future
telemetry.

## What This Checkpoint Is

The third C-x wiring round and the round that gives owlmlx an actual
voice in unified-memory reclamation. Up to now, the OS-level memory
reclaim observed in B-1.2 (the OwlOps green-spike-then-drop pattern)
was driven by macOS unified memory pressure response — owlmlx held no
explicit `clear_cache` call. C-3.1 makes owlmlx the agent of that
reclaim.

## What Is Now Frozen Exact

### `owlmlx/runtime/mlx_native_backend.py` — four-part diff

1. **Import addition**: `from owlmlx.memory_actuator import MemoryActuator, ReclaimReceipt`
2. **`MlxNativeBackend.__init__`**:
   `self._last_unload_receipt: ReclaimReceipt | None = None`
3. **New static method** `_try_import_mlx_core()`: lazily imports
   `mlx.core`, returns the module on success, `None` on `ImportError`
4. **`unload()` body**: after `_release_active_cache(session)` and
   after dropping session refs, before the `return UnloadResult(...)`,
   instantiates a fresh `MemoryActuator(mlx_module=...)` and calls
   `release_single_model(model_id=..., declared_freed_gb=freed)`.
   Persists the result on `self._last_unload_receipt`.

Net change: ~17 lines added, no deletions.

### Lifecycle order of operations (the wiring contract)

A successful `unload(model_id)` now executes in this order:

1. Pop session from registry (atomic via `_registry_lock`)
2. **`_release_active_cache(session)`** — hand any pending cache_manager
   handle back; manager registry shrinks (C-1.2 wiring)
3. Compute `freed = float(session.info.memory_gb)` (declared, unchanged)
4. Drop session refs (`session.model = None`, etc.)
5. **`_try_import_mlx_core()`** — lazy mlx import attempt
6. **Construct fresh `MemoryActuator(mlx_module=mx_core_or_None)`**
7. **`actuator.release_single_model(...)`** — runs `gc.collect()` then
   `mx.clear_cache()` when mlx is present; produces a `ReclaimReceipt`
8. Persist receipt on `self._last_unload_receipt`
9. Return `UnloadResult(ok=True, ..., freed_gb=freed)`

Steps 2 and 7 cannot be reordered: cache release must complete before
allocator clear, otherwise the manager would hold references when
underlying pages get reclaimed.

### New test file `tests/test_mlx_native_backend_memory_actuator_release.py` — 6 tests

All tests use fake `mlx_lm` for load + monkeypatched
`_try_import_mlx_core` for actuator-side path selection (avoids
fighting Python's import system; no sys.modules pollution beyond
`mlx_lm`):

- `test_unload_invokes_memory_actuator_and_persists_receipt` — no-mlx
  path; receipt is non-None, model_id matches, declared_freed_gb
  matches, mlx_module_available=False
- `test_unload_with_real_mlx_invokes_clear_cache_via_actuator` —
  injects `_FakeMlxCore` with `clear_cache_call_count` counter +
  synthetic memory readings; verifies exactly one invocation and that
  before/after byte readings flow through to the receipt
- `test_unload_with_no_mlx_module_returns_noop_receipt` — verifies
  graceful no-op when mlx.core import returns None
- `test_unload_receipt_carries_declared_freed_gb` — three loads with
  different memory_gb, three unloads, three receipts each with
  matching declared values
- `test_unload_actuator_runs_after_release_active_cache` — ordering
  invariant: traced events `[cache_release, actuator_clear_cache]` in
  that exact order
- `test_unload_unknown_model_does_not_overwrite_last_receipt` —
  unsuccessful unload (model_not_loaded) preserves the prior receipt;
  the actuator only fires on the success path

## Test Counts

After C-3.1:

- `tests/test_mlx_native_backend_memory_actuator_release.py`:
  **6 passed** (new this round)
- `tests/test_mlx_native_backend.py`: 13 passed + 1 skipped (no change)
- `tests/test_mlx_native_backend_post_claim_invariants.py`: 6 passed
- `tests/test_mlx_native_backend_real_upstream_binding.py`: 4 passed
- `tests/test_mlx_native_backend_cache_release.py`: 6 passed (no change)
- `tests/test_cache_manager.py`: 10 passed (no change)
- `tests/test_memory_actuator.py`: 19 passed (no change)
- combined regression on the C-x bundle + native MLX adapter set +
  cache release + actuator release: **106 passed, 3 skipped, 2
  warnings in 2.04 s**

The B-1.2 env-gated smoke was not re-run in this round; the wiring
change is observable through the unit-test layer (the
`_FakeMlxCore.clear_cache_call_count` assertion is the ground truth
that matters). Operator may re-run the smoke separately to verify
the post-unload OwlOps green-spike pattern is now driven by owlmlx
rather than macOS pressure response (the spike timing should
sharpen — `clear_cache` returns pages to the OS faster than waiting
for inactive-pool eviction).

## What This Checkpoint Closes

- the C-3 scaffold cap statement "the native backend's existing
  unload is NOT modified to call this in this round"
- the gap between C-3 actuator ownership claim and actual production
  invocation
- the long-standing critique recorded in the seven-line architectural
  assessment Line 3 (memory governance: partial, "认知大于行动 — owlmlx
  knows memory should be governed but governance's actuator hasn't
  been built"). C-3.1 closes the actuator-not-built half; the
  governance half (eviction policy, residency tracker) remains
  unfinished
- the precondition for C-3.2 (measured freed bytes into UnloadResult)
  and C-3.3 (allocator floor configuration)

## What This Checkpoint Does Not Claim

- **no capability matrix row promoted, demoted, or extended.** Wiring
  is refactor; the matrix is untouched
- **no eviction, no LRU, no residency tracker, no pressure
  subscription.** The actuator's other capabilities (B/C/D/E in the
  C-3 scaffold's surface) are unwired
- **no UnloadResult shape change.** `freed_gb` is still the **declared**
  value (`session.info.memory_gb`). Measured bytes flow through the
  receipt only; `UnloadResult` shape extension is C-3.2
- **no allocator floor configured.** `mx.set_cache_limit` and
  `mx.set_wired_limit` are reachable through the actuator but not
  invoked at backend init; that's C-3.3
- **no automatic background pressure-response loop.** The frozen
  invariant `no_automatic_background_eviction_loop` (per
  `memory_pressure_eviction_policy.py:35`) is honored — the only path
  that triggers actuator action is an explicit `unload(model_id)` call
  from the operator
- **no environment / dependency / pyproject change**

## Side Effects

- one additional Python import in `mlx_native_backend.py` module top
  (`from owlmlx.memory_actuator import ...`); no new pip dependency
- a fresh `MemoryActuator` instance is constructed on each successful
  unload — cheap (just stores mlx_module ref + empty subscription
  list)
- `mx.clear_cache()` is now called once per successful unload when
  `mlx.core` is importable. On the typical owlmlx host this means: an
  unload that previously left dirty pages in mlx's allocator cache
  now eagerly returns those pages to the OS before the function
  returns. Observable in OwlOps 内存余量趋势 (the green-spike sharpens)
  and in mx.get_active_memory() before-vs-after measurements
- `gc.collect()` is also called once per successful unload (inside
  the actuator). This is bounded — Python GC of dropped session refs
  is a few hundred microseconds for the kinds of object graphs
  involved

## Notable Implementation Choices

1. **Fresh actuator per unload, not backend-owned.** The actuator's
   stateful surface is just the pressure-listener registry, which is
   currently unwired everywhere; constructing a fresh instance each
   unload is cheaper than tracking lifetime. If a future round wires
   listeners (C-3.4 or similar), the construction site moves to
   `__init__` then
2. **`_try_import_mlx_core` is staticmethod, monkeypatched in tests.**
   This is the cleanest seam to switch between "no mlx installed" and
   "mlx present" test paths without touching `sys.modules`. Staticmethod
   chosen over module-level function so tests can use
   `monkeypatch.setattr(backend, "_try_import_mlx_core", ...)` per
   instance
3. **Receipt persistence as `_last_unload_receipt` on the backend.**
   Single-slot, not a history list. Rationale: tests need observable
   evidence that the actuator was invoked; production observers can
   read the latest receipt after each unload. A history would add
   memory cost and require eviction policy. Single-slot stays scaffold-
   appropriate
4. **Ordering invariant locked by test.**
   `test_unload_actuator_runs_after_release_active_cache` traces both
   the cache_release and actuator_clear_cache call sequences and
   asserts the exact order. This prevents future refactors from
   accidentally reordering and breaking the invariant
5. **`UnloadResult.freed_gb` unchanged.** Per scope discipline this
   round does not extend the public API. The receipt's measured bytes
   exist only on the internal `_last_unload_receipt`. C-3.2 may
   propagate to UnloadResult; C-3.1 does not

## Current Frozen Active Seam (No Change)

- phase45 sentinel chain unchanged
- top-level customer-runtime-evidence label remains
  `early_formal_runtime`

## Seven-Line Movement

After C-3.1, Line 3 (Memory governance) advances posture but not
label:

| Aspect | Before C-3.1 | After C-3.1 |
|---|---|---|
| Judgment layer (`memory_budget.py`, `model_inventory.py`) | present | unchanged (still present) |
| Actuator layer (release / clear_cache / observability) | scaffold landed (C-3) | **wired into production unload path** |
| Eviction policy | absent | absent (still) |
| Residency tracker | absent | absent (still) |
| Pressure subscription / loop | absent | absent (still) |
| Overall Line 3 label | `partial` | `partial` (still — three sub-pieces remain) |

The label doesn't advance because the seven-line assessment is
about **observable capability**, not internal completeness. A future
operator-visible release-policy or eviction-policy round can move
the label.

## Next Authorized Round

Three candidates, ranked:

### Path C-3.2 (recommended): measured-freed-bytes into UnloadResult

- file: `files/execution-prompts/owlmlx/owlmlx-memory-actuator-measured-freed-into-unload-result.md`
  (to be authored)
- scope: extend `UnloadResult` (or add a sibling field) to carry
  measured `freed_bytes` from the receipt — alongside the declared
  `freed_gb`. Lets HTTP callers and OwlOps distinguish "we said the
  model was 67 GB" from "we measured allocator releasing 64 GB".
  Requires editing `owlmlx/runtime/types.py` so it's a slightly larger
  surface change than wiring rounds, but bounded
- moves Line 3 toward the "measure-not-declare" half of the actuator
  surface

### Path C-3.3 (parallel-safe with C-3.2 since touches different code):
allocator floor configuration

- file: `files/execution-prompts/owlmlx/owlmlx-memory-actuator-allocator-floor-config.md`
- scope: at `MlxNativeBackend.__init__` (or first load), call
  `actuator.configure_allocator_floor(cache_limit_bytes=...)` to bound
  the unified-memory cache pool. Default value to be operator-set
- prevents the typical "cache pool grows to absorb all available RAM"
  pathology that bites long-running runtimes

### Path D-3 (parallel, server.py only — currently in flight):
unified error envelope wiring

- already dispatched as background subagent; expected to complete
  shortly

I recommend **C-3.2 next** if the operator wants to keep the
memory-governance momentum, **D-3 first** if completing the
serving-hardening trilogy (D-1+D-2+D-3) is preferred. Both are
independent and can run in either order.
