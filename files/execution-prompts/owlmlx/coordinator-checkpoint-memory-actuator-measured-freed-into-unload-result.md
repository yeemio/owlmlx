# owlmlx Coordinator Checkpoint — Memory Actuator Measured-Freed-Bytes into UnloadResult (C-3.2)

## Verdict

- `unload_result_carries_measured_active_and_cache_freed_bytes_alongside_declared_freed_gb`

`UnloadResult` gains two optional fields — `active_memory_freed_bytes`
and `cache_memory_freed_bytes` — populated by the native backend's
unload from the C-3.1 actuator receipt's before/after readings.
`freed_gb` remains the declared value (unchanged); the new fields
carry the measured allocator deltas. Both default to `None` for
backward compat with all existing callers and for any backend that
does not invoke the actuator (subprocess, kernel-side wrappers, etc.).

## What This Checkpoint Is

The fourth C-x wiring round and the round that promotes the actuator's
measurement output from internal observation
(`backend._last_unload_receipt`) to first-class API surface. HTTP
callers of `/v1/unload`, OwlOps dashboards, and any future audit
trail can now compare declared vs measured release bytes without
joining against a separate runtime status query.

## What Is Now Frozen Exact

### `owlmlx/runtime/types.py` — UnloadResult schema extension

Two fields added at the end of the dataclass body (preserving
positional order of all prior fields):

```python
active_memory_freed_bytes: int | None = None
cache_memory_freed_bytes: int | None = None
```

Both default to `None`. All existing constructors of `UnloadResult`
(found at: `owlmlx/runtime/mlx_lm_subprocess_backend.py:2574`, `:2585`,
`:2605`, `:2619`; `owlmlx/runtime/kernel.py:859`;
`owlmlx/runtime/mlx_lm_backend.py:410`, `:417`;
`owlmlx/runtime/backends.py:379`, `:385`;
`owlmlx/runtime/mlx_native_backend.py:378`, `:406`;
`tests/test_termination_recovery_policy.py:44`;
`tests/test_reclaim_barrier_event.py:59`) continue to work unchanged
because all use keyword arguments and ignore the new optional fields.

### `owlmlx/runtime/mlx_native_backend.py` — `unload` body extension

After the actuator call (added in C-3.1), before `return UnloadResult(...)`:

1. Compute `active_freed = self._compute_freed_bytes(receipt.active_memory_before_bytes, receipt.active_memory_after_bytes)`
2. Compute `cache_freed` the same way for cache memory fields
3. Pass both to `UnloadResult(...)` constructor

New static method `_compute_freed_bytes(before, after)`:
- Returns `None` if either reading is `None` (no-mlx no-op receipt)
- Otherwise returns `max(0, before - after)` — **clamps negative
  deltas to zero** to prevent allocator-growth-during-clear from
  surfacing as misleading negative "freed bytes"

Net change to `mlx_native_backend.py`: ~22 lines added, no deletions.

### `tests/test_mlx_native_backend_memory_actuator_release.py` — 4 new tests appended

The file now holds 10 tests (6 from C-3.1 + 4 new for C-3.2):

- `test_unload_result_carries_measured_active_freed_bytes_when_mlx_present`
  — fake_mx clear_cache shrinks active by 200_000_000; assertion
  `active_memory_freed_bytes == 200_000_000`, `cache_memory_freed_bytes
  == 500_000_000`
- `test_unload_result_measured_fields_are_none_without_mlx` — no-mlx
  path; both fields `None`; `freed_gb` still set to declared value
- `test_unload_result_clamps_negative_deltas_to_zero` — uses a
  pathological `_GrowingMlx` whose clear_cache **grows** active+cache
  memory; assertion `active_memory_freed_bytes == 0` and
  `cache_memory_freed_bytes == 0`. Also verifies the receipt itself
  carries the raw before/after (clamp is at UnloadResult layer, not
  receipt layer)
- `test_unload_result_preserves_freed_gb_when_measurement_present` —
  declared 12.5 GB and measured 200_000_000 bytes coexist in the same
  result; neither overwrites the other

## Test Counts

After C-3.2:

- `tests/test_mlx_native_backend_memory_actuator_release.py`:
  **10 passed** (was 6 in C-3.1)
- combined regression on the C-x bundle + native MLX adapter set:
  **119 passed, 3 skipped, 2 warnings in 2.21 s** (was 115 passed
  in Batch 3)

The B-1.2 env-gated smoke was not re-run; the schema change is
observable through unit tests with fake mlx_module injection.

## What This Checkpoint Closes

- the gap between "actuator measurements live on internal field" and
  "actuator measurements are HTTP API surface"
- the OwlOps blocker "we can't show declared vs measured side-by-side
  without two API calls" — now `/v1/unload` response carries both in
  one payload
- the precondition for any audit-trail layer that wants to compare
  declared model footprint against measured allocator behavior over
  time (e.g. catching "this model was declared 67 GB but only released
  64 GB — we're leaking ~3 GB per unload" patterns)

## What This Checkpoint Does Not Claim

- **no capability matrix row promoted, demoted, or extended.** Wiring
  + schema extension; matrix is untouched
- **no new actuator capability.** The receipt was already produced by
  C-3.1; C-3.2 just plumbs it
- **no behavior change for subprocess backend.** `mlx_lm_subprocess_backend`
  still constructs `UnloadResult` without the new fields, leaving
  them at default `None`. Subprocess backend's true reclamation
  happens via process exit, not via `mx.clear_cache`, so populating
  these fields would be misleading
- **no `freed_gb` value change.** `freed_gb` continues to mirror
  `session.info.memory_gb` (declared). The new fields are alongside,
  not a replacement
- **no `LoadResult` / `GenerateResult` / `RestartResult` change.**
  Only `UnloadResult` gains the fields
- **no HTTP API breaking change.** Callers reading the existing
  fields (`ok`, `message`, `model_id`, `freed_gb`, `error_code`,
  `detail`) see no schema change. Callers using strict JSON-schema
  validators that reject unknown fields will need to update their
  schemas — that's the only edge case
- **no new pip dependency / no env-gated smoke run / no env file change**

## Notable Implementation Choices

1. **Two separate fields, not a sub-dict.** `active_memory_freed_bytes`
   and `cache_memory_freed_bytes` are two top-level optional ints
   instead of one nested `measured: dict`. Rationale: future-proof
   for callers that `getattr(result, "active_memory_freed_bytes",
   None)`-style read; flatter is easier to consume in dashboards
2. **Clamp at the UnloadResult layer, not at the receipt layer.** The
   `_compute_freed_bytes` helper that does `max(0, before - after)`
   lives on `MlxNativeBackend`, not on `MemoryActuator`. The receipt
   itself preserves raw before/after readings honestly; only the
   "freed bytes" surfaced to API callers is clamped. This keeps the
   actuator's measurement layer truthful while preventing misleading
   negative values at the API surface
3. **Did not extend ReclaimReceipt with `freed_bytes_clamped`.** The
   receipt is a measurement record; the clamp is an API contract.
   Mixing them would couple measurement semantics to consumer
   expectations
4. **No subprocess backend update.** Adding the fields to subprocess
   `UnloadResult` constructions would require either always passing
   `None` (verbose, no value) or computing process-exit-based deltas
   (would require reading `/proc`-style stats which are unreliable on
   macOS post-exit). Easier and more honest to leave them as default
   `None` and let the schema's "no measurement available" semantics
   apply
5. **`freed_gb` still in float GB units; new fields in int bytes.**
   Different units are intentional: `freed_gb` is operator-facing
   (declared); bytes are machine-precise (measured). Future
   refactors may unify, but the distinction is currently informative

## Side Effects

- one schema field-set extension on `UnloadResult` (frozen dataclass
  with slots); zero memory cost when fields are at default `None`
- one new staticmethod on `MlxNativeBackend` (`_compute_freed_bytes`);
  trivially small
- HTTP `/v1/unload` JSON responses now carry two additional fields
  on the success path. Existing callers see no behavior change
- OwlOps dashboard can now show "declared 12.5 GB / measured 200 MB"
  side-by-side per unload event without joining against runtime status

## Current Frozen Active Seam (No Change)

- phase45 sentinel chain unchanged
- top-level customer-runtime-evidence label remains
  `early_formal_runtime`

## Seven-Line Movement

After C-3.2, Line 3 (Memory governance) gains an observable surface
but the label does not advance. The change is API-shape, not new
capability. Line 3 stays `partial`.

## Next Authorized Round

Three candidates, ranked:

### Path C-3.3 (recommended): allocator floor configuration

- file: `files/execution-prompts/owlmlx/owlmlx-memory-actuator-allocator-floor-configuration.md`
- scope: at `MlxNativeBackend.__init__` (or first load), call
  `actuator.configure_allocator_floor(cache_limit_bytes=...)` to bound
  the unified-memory cache pool. Default value to be operator-set via
  env var or kept at the actuator scaffold's default
- prevents long-running runtime cache pool growth (a typical
  pathology that bites multi-day uptime)
- touches `mlx_native_backend.py` only

### Path D-4 (parallel, in flight): Prometheus /metrics endpoint

- already dispatched as background subagent during C-3.2 foreground;
  will complete shortly

### Path D-5 (parallel after D-4 completes): per-route id deduplication

- now that D-1's middleware sets `x-request-id` uniformly, the per-
  route ad-hoc generation at `server.py:1258 / 1293 / 1445 / 1587 /
  1676` is redundant. D-5 removes those local generators, letting the
  middleware be the sole source. Touches `server.py` only

I recommend **C-3.3 next** to keep the C-3.x progression complete on
`mlx_native_backend.py`, then take stock of the seven-line position
after `Memory governance` has its first defensive guardrail.
