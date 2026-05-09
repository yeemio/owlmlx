# owlmlx Coordinator Checkpoint — Cache Manager Release-Side Wired (C-1.2)

## Verdict

- `cache_manager_release_side_wired_acquire_release_pair_closed`

`cache_manager.release_for_request(handle)` is now invoked at all
production lifecycle exit points: generate return, stream_generate
terminal yield, stream_generate exception, stream_generate early
caller close, and unload. The manager's per-model handle registry
empties cleanly after each request. Behavior unchanged externally
(fresh per-request cache, single-request semantics, zero cross-request
reuse claim).

## What This Checkpoint Is

The second C-1.x wiring round and the round that closes the
acquire-release pair started in C-1.1. C-1.1 turned the manager into
the canonical KV-cache call gateway; C-1.2 turns it into a canonical
**ledger** by ensuring each acquire is matched with a release at the
exact lifecycle moment the cache leaves use. This is what makes
`backend._cache_manager._handles_by_model` actually represent
"currently-in-flight handles" instead of monotonically growing.

## What Is Now Frozen Exact

### `owlmlx/runtime/mlx_native_backend.py` — four-part diff

1. **Import addition**: `CachedRequestHandle` added to the existing
   `from owlmlx.cache_manager import ...` line
2. **`_NativeSession` dataclass field**:
   `active_cache_handle: CachedRequestHandle | None = None` — the
   active handle to release when the request lifecycle exits
3. **`_make_fresh_prompt_cache` body**:
   - Stores the handle on `session.active_cache_handle` instead of
     `del handle`
   - On the failure path (exception during acquire), explicitly clears
     `session.active_cache_handle = None`
4. **New helper `_release_active_cache(self, session)`**: hands the
   active handle back to the manager and clears the field. Idempotent
   (early return when no handle is active).
5. **Three release injection points in finally clauses**:
   - `generate()`: in the outer `try/finally`, calls
     `self._release_active_cache(session)` **before**
     `self._admission.release()` — preserves the ordering invariant
     that the cache release happens within the gate
   - `stream_generate()`: same pattern in the outer `try/finally`.
     Python's generator semantics guarantees this `finally` runs on
     terminal yield, on exception, AND on early `gen.close()` from the
     caller — proven by `test_release_fires_on_early_stream_close`
   - `unload()`: calls `self._release_active_cache(session)` before
     dropping `session.model` / `session.tokenizer` — handles the
     pathological "pending handle at unload time" case

Net change: ~22 lines added across the file, no deletions.

### New test file `tests/test_mlx_native_backend_cache_release.py` — 6 tests

All tests use fake `mlx_lm` injection (no real `mlx_lm` import). They
observe release semantics through `backend._cache_manager._handles_by_model`
directly:

- `test_release_fires_after_generate_completion` — generate() returns
  → handle removed from registry; counters.entries == 1 (acquire
  counter is monotonic per scaffold design)
- `test_release_fires_after_stream_generate_completion` — full
  consumption to `done` event → registry clean
- `test_release_fires_on_early_stream_close` — `next(gen)` then
  `gen.close()` → registry clean (Python `finally` semantics)
- `test_release_fires_on_unload_with_pending_handle` — pathological
  pending handle at unload → unload releases before dropping session
- `test_release_idempotent_when_no_active_handle` — calling
  `_release_active_cache` twice is safe
- `test_active_cache_handle_set_during_make_fresh_prompt_cache` —
  session field is populated after acquire, cleared after release

### Manager API and implementation — UNCHANGED

`cache_manager.acquire_for_request` still returns the
`(handle, cache_object)` tuple introduced in C-1.1.
`cache_manager.release_for_request` semantics is exactly as written in
the C-1 scaffold (idempotent removal from `_handles_by_model`,
counters not decremented).

## Test Counts

After C-1.2:

- `tests/test_mlx_native_backend_cache_release.py`: **6 passed** (new
  this round)
- `tests/test_mlx_native_backend.py`: 13 passed + 1 skipped (no change)
- `tests/test_mlx_native_backend_post_claim_invariants.py`: 6 passed
  (no change)
- `tests/test_mlx_native_backend_real_upstream_binding.py`: 4 passed
  (no change)
- `tests/test_cache_manager.py`: 10 passed (no change since C-1.1)
- combined regression on the C-x bundle + native MLX adapter set +
  release contract: **95 passed, 3 skipped, 2 warnings in 1.97 s**

The B-1.2 env-gated smoke (`tests/test_mlx_native_backend_real_smoke.py`)
was not re-run in this round; the wiring change is observable through
the unit-test layer (registry cleanliness assertions on a fake-injected
cache surface), and the real-upstream binding tests still pass.

## What This Checkpoint Closes

- the C-1.1 cap statement "`release_for_request` is not yet called from
  the native backend on generator close or unload"
- the latent leak in `_handles_by_model` registry (would have grown
  monotonically without this round)
- the precondition for any future cache_manager extension that depends
  on accurate "currently-in-flight handle" state (eviction policy that
  would otherwise pick a long-released handle as a victim, residency
  tracker that would over-count)
- the acquire-release pair's lifecycle correctness on all four exit
  paths

## What This Checkpoint Does Not Claim

- **no capability matrix row promoted, demoted, or extended.** Wiring
  is refactor; the matrix is untouched
- **no eviction, no LRU, no PromptTrie integration, no reuse.**
  cache_manager remains scaffold-grade with single-request semantics
- **no `session.last_prompt_cache*` field deprecation.** Backward
  compat preserved. Field deprecation is C-1.3 (or later) — separate
  round whose value is purely cosmetic
- **no `release_for_request` semantics change.** Counters still
  monotonic on acquire, untouched on release. Eviction event counter
  still reserved for the future eviction extension
- **no env-gated B-1.2 smoke run.** Refactor risk is unit-testable;
  operator may re-run the smoke separately
- **no `_make_fresh_prompt_cache` removal.** Function still exists; its
  body is now the acquire-then-store-handle pattern
- **no environment / dependency / pyproject change**

## Notable Implementation Choices

1. **Release ordering: cache before admission.** In `generate()` and
   `stream_generate()`'s finally clauses, `_release_active_cache(session)`
   runs **before** `self._admission.release()`. Rationale: the ticketed
   admission is the outermost concurrency boundary; a cache release
   that fires after the gate would race with the next acquire. Putting
   the cache release inside the gate's hold window guarantees the
   manager's registry is clean before the next request enters
2. **Session field retained, not removed.** `last_prompt_cache_id`
   continues to use Python `id(cache)`. The handle's monotonic
   `cache_object_id` (manager-canonical) lives in
   `session.active_cache_handle.cache_object_id` — observers can read
   either. Unifying them is C-1.3's responsibility (or never, if the
   dual identifier proves useful)
3. **`unload`'s defensive release.** In normal flows, no pending handle
   exists at unload time (generate / stream / close all release first).
   But `test_release_fires_on_unload_with_pending_handle` exercises the
   pathological case by force-acquiring outside the lifecycle, so the
   contract is locked: unload always releases before drop, regardless
   of whether the lifecycle properly released earlier
4. **Registry observation, not API extension.** Tests observe release
   semantics via `backend._cache_manager._handles_by_model` (private
   attribute). This is intentional for scaffold-round tests — the
   manager's public read surface (`status_dict()`,
   `counters()`) doesn't currently expose per-model handle counts in a
   form that's useful for "is the registry empty for this model_id"
   queries. A future round may extend the public read surface; for
   now, private-attribute observation is the cheapest correct test
   shape

## Side Effects

- one new field on `_NativeSession` (`active_cache_handle`); zero
  memory cost when no acquire is in-flight (None)
- one new method on `MlxNativeBackend` (`_release_active_cache`);
  zero-cost when called with no active handle
- the manager's private `_handles_by_model` dict now empties cleanly
  per request rather than growing monotonically — observable through
  any future telemetry exporter that reads it

## Current Frozen Active Seam (No Change)

- phase45 sentinel chain unchanged
- top-level customer-runtime-evidence label remains
  `early_formal_runtime`

## Next Authorized Round

Three candidates, ranked:

### Path C-3.1 (recommended after Batch 2 completes): memory_actuator wiring into unload

- file: `files/execution-prompts/owlmlx/owlmlx-memory-actuator-wiring-into-native-unload.md`
  (to be authored after this commit lands)
- scope: replace the "drop session refs and hope" pattern in
  `mlx_native_backend.unload` with `memory_actuator.release_single_model(...)`
  + the existing release_active_cache call. First time the production
  unload path actually invokes `mx.clear_cache()`. Touches
  `mlx_native_backend.py` again — must serialize after C-1.2
- moves seven-line Line 3 (memory governance) from `partial` toward
  `partial-with-actuator-bound`

### Path C-1.3 (deferrable): session field deprecation

- file: `files/execution-prompts/owlmlx/owlmlx-cache-manager-session-field-deprecation.md`
- scope: remove `last_prompt_cache_id` and `prompt_cache_call_count`
  from `_NativeSession`; route observers to `session.active_cache_handle`
  / `backend._cache_manager.counters()`. Update tests
- pure cosmetic value; doesn't move any seven-line dial. Defer until
  matrix promotion or a new feature actually requires the cleanup

### Path D-3 (parallel, server.py only): unified error envelope wiring

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d3-unified-error-envelope-wiring.md`
- scope: install `app.add_exception_handler(...)` for `RuntimeError`
  and a generic `Exception` fallback that produces
  `UnifiedErrorEnvelope` shapes; promote `/v1/generate` to return
  proper HTTP status codes when `ok=False`. Touches `server.py` —
  conflicts with D-2 (which is in flight)

I recommend **C-3.1 next** to keep the C-1.x → C-3.x progression
moving on the same file with serialized commits, then take stock of
seven-line position.
