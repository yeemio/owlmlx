# owlmlx Coordinator Checkpoint — Memory Actuator Allocator Floor Configuration (C-3.3)

## Verdict

- `allocator_floor_configuration_wired_operator_opt_in_idempotent_first_load`

`MlxNativeBackend.load` now invokes
`memory_actuator.configure_allocator_floor(...)` exactly once per
backend instance, but **only when at least one of**
`OWLMLX_NATIVE_CACHE_LIMIT_BYTES` / `OWLMLX_NATIVE_WIRED_LIMIT_BYTES`
is set. Operators who do not opt in see zero behavior change. The
resulting `AllocatorFloorConfig` is observable on
`backend._last_allocator_floor_config`.

This closes the C-3.x trilogy: C-3.1 wired the actuator into
`unload` (`mx.clear_cache`), C-3.2 surfaced measured freed bytes on
`UnloadResult`, C-3.3 wires the allocator floor on `load`
(`mx.set_cache_limit` + `mx.set_wired_limit`).

## What Is Now Frozen Exact

### `owlmlx/runtime/mlx_native_backend.py` — five-part diff

1. **Imports**: added `os` stdlib; extended `from owlmlx.memory_actuator import ...` to also import `AllocatorFloorConfig`
2. **`__init__`**: two new fields:
   - `_allocator_floor_configured: bool = False` (idempotent flag)
   - `_last_allocator_floor_config: AllocatorFloorConfig | None = None`
3. **New method `_maybe_configure_allocator_floor()`**:
   - Returns early if `_allocator_floor_configured` is True (idempotent)
   - Sets the flag BEFORE doing work (defensive against future reentrancy)
   - Reads `OWLMLX_NATIVE_CACHE_LIMIT_BYTES` and `OWLMLX_NATIVE_WIRED_LIMIT_BYTES` via `_read_env_int`
   - Returns silently if both are `None` (operator opted out)
   - Lazy-imports mlx.core via the existing `_try_import_mlx_core`
   - Constructs `MemoryActuator(mlx_module=...)` and calls `configure_allocator_floor(cache_limit_bytes=..., wired_limit_bytes=...)`
   - Persists result on `_last_allocator_floor_config`
4. **New staticmethod `_read_env_int(env_var)`**: returns `None` for unset / empty / unparseable; otherwise the int value
5. **`load()` body**: one new line — `self._maybe_configure_allocator_floor()` call right before `return LoadResult(ok=True, ..., model=info)`

Net change: ~52 lines added, no deletions.

### `tests/test_mlx_native_backend_allocator_floor_config.py` — 7 new tests

All use fake mlx_lm injection + monkeypatched `_try_import_mlx_core`:

- `test_load_does_not_configure_when_no_env_vars` — both env vars unset → no configure call, `_last_allocator_floor_config` is None, but `_allocator_floor_configured` flag IS set (opting-out is also one-shot)
- `test_load_configures_when_cache_limit_env_set` — sets cache only; verifies `set_cache_limit(N)` called, `set_wired_limit` NOT called
- `test_load_configures_when_wired_limit_env_set` — symmetric
- `test_load_configures_only_once_across_multiple_loads` — three sequential loads, configure fires exactly once (asserts list length == 1)
- `test_load_with_no_mlx_returns_noop_config_when_env_set` — env set but mlx unavailable → actuator no-op branch returns shaped config with operator-supplied bytes echoed; `wired_limit_supported=False`
- `test_load_handles_invalid_env_var_value_gracefully` — both env vars unparseable → load still succeeds, no configure call
- `test_load_skips_wired_limit_when_mlx_lacks_attribute` — fake mlx variant lacking `set_wired_limit` (older / non-15+) → cache_limit set but wired skipped; `wired_limit_supported=False`

## Test Counts

After C-3.3:

- `tests/test_mlx_native_backend_allocator_floor_config.py`: **7 passed** (new)
- combined regression: **133 passed, 3 skipped, 2 warnings in 2.36 s** (was 126 in Batch 4)

## What This Checkpoint Closes

- C-3.x trilogy: C-3.1 (release wiring) + C-3.2 (measured-freed plumbing) + C-3.3 (allocator floor) — all three actuator surfaces (release / observability deltas / floor config) now have production wiring on the native backend
- the latent "cache pool grows unboundedly" pathology that bites long-running runtimes (now operator can cap it)
- the precondition for C-3.4 (`notify_pressure` integration) which can now use the floor as a back-pressure trigger boundary

## What This Checkpoint Does Not Claim

- **no default behavior change.** Operators who do not set either env var see no change — `configure_allocator_floor` is never called. This is intentional: choosing the right cache limit is operator-tuning, not owlmlx default
- **no capability matrix promotion.** Wiring is refactor + opt-in surface; the matrix is untouched
- **no automatic pressure response.** The `_automatic_background_eviction_loop` invariant from `memory_pressure_eviction_policy.py` is honored — there is no daemon, no threshold-driven trigger, no scheduler. Configuration is one-shot at first load
- **no env var validation beyond integer parsing.** Operator-supplied values pass straight through to `mx.set_cache_limit`. Negative values, zero, or absurdly large values are not rejected by owlmlx; mlx itself decides what to do with them
- **no UnloadResult / LoadResult shape change**
- **no subprocess backend update.** Subprocess processes have their own allocator state; floor config is native-only
- **no pyproject / dependency change**

## Notable Implementation Choices

1. **Idempotent flag set BEFORE work.** `_allocator_floor_configured = True` runs at the top of `_maybe_configure_allocator_floor`, before any env read or actuator call. Rationale: prevents double-configure if a future refactor introduces concurrent first-load races. The registry lock in `load()` already serializes entry but this is belt-and-suspenders
2. **"Opt-out is also one-shot."** When env vars are unset, the flag is still set after the first load. Subsequent loads still skip the configure path (because both env vars stay unset for the backend's lifetime). This makes the behavior predictable: configure decision is taken once, at first-load time
3. **Operator opt-in, not magic default.** Choosing 8 GB / 16 GB / 32 GB as a default cache limit would be wrong for some operators (single-large-model hosts may want unlimited; multi-tenant hosts want a strict cap). Owlmlx refuses to choose; the operator does. This matches the existing `memory_budget.py` pattern of recording defaults but not enforcing them
4. **`_read_env_int` swallows ParseError.** Misconfigured env vars must not block model load — operators should be able to set OWLMLX_NATIVE_CACHE_LIMIT_BYTES to "auto" (currently unparseable, treated as None) without breaking serving. A future round may add a warning log; this round doesn't because that requires structured logging plumbing
5. **No `actuator.configure_allocator_floor` is called when both env vars are None.** Even though the actuator's no-op branch handles that case correctly, calling with both None is informationally empty — easier to skip the call than to record an empty config

## Side Effects

- two new env vars become operator-tunable knobs:
  - `OWLMLX_NATIVE_CACHE_LIMIT_BYTES`
  - `OWLMLX_NATIVE_WIRED_LIMIT_BYTES`
- one new field on `MlxNativeBackend` — small, just a flag + Optional config object
- on the **first successful load** of a backend instance, when env vars are set, owlmlx now calls `mx.set_cache_limit` and/or `mx.set_wired_limit` once. These are bounded operations (set integer, return previous integer); no allocation, no GC

## Current Frozen Active Seam (No Change)

- phase45 sentinel chain unchanged
- top-level customer-runtime-evidence label remains `early_formal_runtime`

## Seven-Line Movement

After C-3.3, Line 3 (Memory governance) gains the **third actuator
surface** (release + observability + floor) but the label still does
not advance to "close" — eviction policy, residency tracker, and
pressure subscription still missing. The label is a measure of
**observable capability**, and operator-opt-in floor is observable
only to operators who opt in.

That said, C-3.x trilogy completion means owlmlx now **has its own
voice in unified-memory governance** at every defensive primitive
mlx exposes. Future work is policy (when to evict, when to grow),
not primitive wiring.

## Next Authorized Round

Three candidates, ranked:

### Path C-3.4 (recommended): pressure subscription wiring

- file: `files/execution-prompts/owlmlx/owlmlx-memory-actuator-pressure-subscription-wiring.md`
- scope: connect `host_pressure.sample_host_pressure` returning
  `host_pressure_block` to `actuator.notify_pressure(condition="host_pressure_block")`.
  This is the first **dynamic** trigger of the actuator (today only
  `unload` triggers it). Honors `no_automatic_background_eviction_loop` —
  the trigger is caller-driven (called from existing host_pressure
  read sites)
- moves Line 3 from "primitive wiring complete" toward "policy primitive
  wired"

### Path D-5 (parallel, in flight): per-route id deduplication

- already dispatched as background subagent during C-3.3 foreground;
  will complete shortly

### Path C-2.1 (heaviest, biggest leverage)

- repeatability harness real implementation; needs 67 GB RAM + multi-
  hour campaign. Direction-change decision, not auto-continue

I recommend taking stock after C-3.4 + D-5 land — at that point the
C-3.x and D-x wiring stories are both complete, and the next round
becomes a strategic choice (C-2.1 vs new chain).
