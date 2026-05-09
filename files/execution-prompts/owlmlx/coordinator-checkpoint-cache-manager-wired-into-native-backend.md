# owlmlx Coordinator Checkpoint — Cache Manager Wired into Native Backend (C-1.1)

## Verdict

- `cache_manager_wired_into_native_backend_canonical_ledger`

The C-1 scaffold `CacheManager` is now the **canonical KV-cache call
gateway** for `MlxNativeBackend`. The native backend's
`_make_fresh_prompt_cache` delegates to `self._cache_manager.acquire_for_request(...)`
instead of inlining `make_prompt_cache(model)`. Behavior unchanged
(fresh per-request cache, single-request semantics, zero cross-request
reuse claim). Counter ledger now centralized in the manager. Session
fields remain populated as a backward-compatible mirror.

## What This Checkpoint Is

The first C-x wiring round and the second touch of the redirected main
line on `MlxNativeBackend` after the original B-1.x evidence chain.
This round refactors a production runtime path; it is **not** a
capability matrix promotion round. The matrix is untouched.

## What Is Now Frozen Exact

### `owlmlx/cache_manager.py` API extension

`acquire_for_request` now returns `tuple[CachedRequestHandle, Any]`
(was: just `CachedRequestHandle`). The caller owns the cache_object
strong reference; the manager intentionally does not retain it
(single-request semantics preserved). Per-manager monotonic
`cache_object_id` is independent of Python's `id(cache_object)`.

### `tests/test_cache_manager.py` adaptation

All `manager.acquire_for_request(...)` call sites updated to unpack
`(handle, cache)`. One new test added (
`test_acquire_returns_handle_and_cache_object_tuple`) locking the
contract that the returned cache_object is the **same object reference**
returned by upstream `make_prompt_cache(model)`.

Test count for cache_manager: **10 tests passing** (was 9 in C-1
scaffold round).

### `owlmlx/runtime/mlx_native_backend.py` wiring

Three additions:

1. Import `from owlmlx.cache_manager import CacheManager`
2. `MlxNativeBackend.__init__` instantiates
   `self._cache_manager = CacheManager()`
3. `_make_fresh_prompt_cache` body refactored:
   - First probes upstream reachability via existing
     `_resolve_make_prompt_cache(...)` (defensive: returns `None`
     silently on fake-stub paths to preserve adapter's existing
     contract — manager would raise `RuntimeError` on missing surface
     which would break fake-injection tests)
   - On reachable upstream: delegates to
     `self._cache_manager.acquire_for_request(model_id=
     session.info.model_id, mlx_lm_module=mlx_lm_module,
     model=session.model)`
   - Mirrors returned `cache` into `session.last_prompt_cache`,
     `session.last_prompt_cache_id` (using `id(cache)` for backward
     compat), increments `session.prompt_cache_call_count`
   - Discards `handle` (not surfaced on session — manager owns the
     canonical ledger; session is a backward-compat mirror)

Lines changed in `mlx_native_backend.py`: ~8 net additions, no
deletions. The function still returns `cache | None`.

## Test Counts

After wiring:

- `tests/test_cache_manager.py`: **10 passed** (was 9 in C-1 scaffold)
- `tests/test_mlx_native_backend.py`: 13 passed + 1 skipped (no change)
- `tests/test_mlx_native_backend_post_claim_invariants.py`: 6 passed (no change)
- `tests/test_mlx_native_backend_real_upstream_binding.py`: 4 passed (no change)
- combined regression on the C-x bundle + native MLX adapter set:
  **89 passed, 3 skipped, 2 warnings in 2.18 s**

The B-1.2 env-gated smoke (`tests/test_mlx_native_backend_real_smoke.py`)
was **not** triggered in this round (RAM headroom 59.8 GB at check
time, below the 67 GB the 35B-A3B candidate requires; refactor
risk is also bounded — same upstream call, same return value, so
the real_upstream_binding tests cover the binding contract for
this round).

## What This Checkpoint Closes

- the gap between C-1 scaffold ownership claim and actual production
  path participation — `cache_manager.acquire_for_request` is now
  the path that runs every time the native backend creates a KV
  cache for a request
- the C-1 checkpoint statement "NOT yet bound into MlxNativeBackend"
  — that is now obsolete; the bound state holds
- the precondition for any future cache_manager extension (eviction,
  reuse, residency tracking) to take effect end-to-end without
  needing a separate wiring step

## What This Checkpoint Does Not Claim

- **no capability matrix row promoted, demoted, or extended.** The
  matrix is untouched. Wiring is refactor, not new capability
- **no eviction, no LRU, no PromptTrie integration, no reuse.**
  cache_manager remains scaffold-grade with single-request semantics
- **no `session.last_prompt_cache*` field deprecation.** Backward
  compat preserved; session fields continue to mirror the manager's
  acquire result. Field deprecation is a future round (C-1.2)
- **no release-side wiring.** `cache_manager.release_for_request` is
  not yet called from the native backend on generator close or
  unload — that is also C-1.2
- **no env-gated B-1.2 smoke run.** Refactor risk is contained at
  the unit-test layer; operator may choose to re-run the smoke
  separately (RAM permitting) without invalidating this checkpoint
- **no `_make_fresh_prompt_cache` removal.** The function still
  exists on the adapter, but its body is now a delegation. Removing
  the function is also a future round
- **no environment / dependency / pyproject change**

## Notable Implementation Choices

1. **Two parallel ids retained.** The handle's monotonic
   `cache_object_id` (canonical) and `session.last_prompt_cache_id`
   (Python `id(cache)`, backward-compat) coexist as separate
   identifiers. Unifying them would change observable behavior of
   `tests/test_mlx_native_backend_real_upstream_binding.py`'s identity
   assertions; that's a deliberate non-goal of C-1.1
2. **Defensive None-skip preserved.** When upstream
   `make_prompt_cache` is unreachable (fake stubs), the adapter
   returns `None` silently. The manager raises `RuntimeError` on
   the same condition. The wiring uses
   `_resolve_make_prompt_cache(...) is None` as a pre-check so the
   adapter contract holds; on reachable upstream the manager call
   is wrapped in `try/except` that mirrors the existing
   `last_error` semantics
3. **Manager owns the call, session mirrors the result.** Two
   ledgers exist temporarily by design — manager's counters are
   forward-looking (eviction events, reuse events ready to be
   populated), session's fields are backward-looking (existing
   tests + introspection tools read them). Convergence is C-1.2's
   responsibility, not C-1.1's
4. **`session.info.model_id` is the manager key.** The manager keys
   handles by model_id; the session knows its model_id through
   `session.info`. This binding ties the manager's per-model handle
   registry to the same identity the adapter uses elsewhere

## Side Effects

- one additional Python import in `mlx_native_backend.py` module top
  (`from owlmlx.cache_manager import CacheManager`); no new pip
  dependency
- `MlxNativeBackend()` construction now also constructs a
  `CacheManager()` (zero-cost: just initializes empty registry +
  zero counters + lock)
- the manager's monotonic counter `_next_cache_object_id` advances
  on every cache acquire, observable via
  `backend._cache_manager.counters().entries`

## Current Frozen Active Seam (No Change)

- `summary.seam_rung = aggregation_active_seam_exact`
- top-level customer-runtime-evidence label remains
  `early_formal_runtime`
- phase45 sentinel chain unchanged

## Next Authorized Round

Three candidates, ranked:

### Path C-1.2 (recommended): release-side wiring + session field deprecation

- file: `files/execution-prompts/owlmlx/owlmlx-cache-manager-release-side-wiring.md`
  (to be authored)
- scope: hook `cache_manager.release_for_request(handle)` into the
  native backend's generator-close / unload path; phase out
  `session.last_prompt_cache*` fields by routing observers to the
  manager's `status_dict()`; update tests
- behavior unchanged externally (still single-request, no reuse)
- closes the dual-ledger transitional state from C-1.1

### Path C-3.1 (parallel-conflict, must serialize): memory_actuator wiring into unload

- file: `files/execution-prompts/owlmlx/owlmlx-memory-actuator-wiring-into-native-unload.md`
  (to be authored)
- scope: replace `mlx_native_backend.unload`'s "drop session refs and
  hope" with `memory_actuator.release_single_model(...)` call; first
  caller to actually invoke `mx.clear_cache()` on the production
  unload path
- conflicts with C-1.2 (same file `mlx_native_backend.py`); must
  serialize
- moves seven-line Line 3 (memory governance) from `partial` toward
  `partial-with-actuator`

### Path D-2 (independent of cache/native, conflicts only with D-1's file): GracefulShutdown wiring

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d2-graceful-shutdown-wiring.md`
  (to be authored)
- scope: install `GracefulShutdown` lifespan hook in `server.py`'s
  `create_app(...)`; touches `runtime/server.py`
- conflicts with D-1 (same file); must wait until D-1 is committed
- moves seven-line Line 4 (serving) from `partial` toward
  `partial-with-shutdown-drain`

I recommend **C-1.2 first** to close the dual-ledger transitional
state cleanly before any further cache-side work, then **C-3.1** or
**D-2** in parallel-by-file (both touch different files post-C-1.2).
