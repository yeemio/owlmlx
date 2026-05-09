# owlmlx Coordinator Checkpoint — Cache Manager Scaffold Landed (C-1)

## Verdict

- `cache_manager_scaffold_landed_ownership_domain_frozen_unwired`

The KV cache lifetime ownership domain now exists in the `owlmlx`
package as a scaffold module, with single-request semantics enforced
and the 5-counter zero-baseline ledger published in a shape stable for
existing residency-evidence consumers. The scaffold is **not** wired
into `MlxNativeBackend` and **not** consumed by any serving path. No
row in `native-mlx-backend-capability-matrix.md` is promoted by this
round.

## What This Checkpoint Is

A scaffold-grade landing marker for the C-1 round. It declares that the
ownership boundary for in-process KV cache lifetime is now occupied by
`owlmlx/cache_manager.py`, which is distinct from `cache_truth.py`
(legacy oMLX SSD/hot-cache schema), distinct from `mlx_lm.models.cache`
(upstream KV primitives), and distinct from the existing 141
`cache_*.py` files (legacy schema, evidence / observation,
scheduler-truth, pre-claim metadata staging).

It is **not** a promotion checkpoint. It is **not** a wiring
checkpoint. It is the round that lets a follow-up round (C-1.1 wiring;
later eviction / prefix reuse / cross-request keying rounds) extend
against a frozen scaffold contract instead of inventing an ownership
domain alongside whatever feature it is implementing.

## What Is Now Frozen Exact

### New module: `owlmlx/cache_manager.py`

- frozen dataclass `CacheManagerCounters` with the 5 fields named in
  `cache_residency_evidence.py:19-28` (`entries`, `resident_bytes`,
  `reuse_events`, `hit_count`, `eviction_events`), all defaulting to 0;
  `to_dict()` returns plain `int` for every key
- frozen dataclass `CachedRequestHandle` with fields `model_id: str`,
  `cache_object_id: int`, `created_at: float`,
  `cross_request_reuse_claimed: bool = False`
- class `CacheManager`:
  - `acquire_for_request(self, *, model_id, mlx_lm_module, model)`
    resolves `mlx_lm_module.models.cache.make_prompt_cache` via a
    defensive attribute walk, calls it with `model`, records the handle,
    increments only the `entries` counter, returns the handle. Single-
    request semantics: no prefix keying, no prior-handle lookup, no
    reuse / hit / eviction event
  - `release_for_request(self, handle)` drops the handle reference
    without updating any counter (release is incidental in single-
    request mode, not an eviction event)
  - `counters(self)` returns a frozen `CacheManagerCounters` snapshot
  - `status_dict(self)` returns a payload whose `counters` key matches
    the `CacheResidencyMetrics` field names so existing residency-
    evidence consumers can read the manager without bespoke adapters;
    additional top-level keys explicitly state
    `single_request_semantics_enforced: True`,
    `cross_request_reuse_claimed: False`,
    `wired_into_native_backend: False`
- attribute-walk resolver raises a clear `RuntimeError` when the
  upstream surface is missing — stricter than
  `mlx_native_backend._resolve_make_prompt_cache` which returns `None`
  to allow silent skip; the manager's contract is to fail loudly
  because callers reach the manager only when they intend to bind
- explicit "future extension point" comments at module bottom for
  (a) eviction policy referencing `LRUPromptCache.trim_to`,
  (b) prefix reuse referencing `PromptTrie.search`,
  (c) cross-request handle keying — comments only, no method stubs
- `__all__ = ["CacheManager", "CacheManagerCounters", "CachedRequestHandle"]`

### New doc: `docs/source-of-truth/cache-manager-architecture.md`

- 9 sections: Status / scope; Why this module exists; Distinct from
  `cache_truth.py`; Ownership boundaries (table covering cache_manager
  / `cache_truth.py` / `mlx_lm.models.cache` / 141 existing
  `cache_*.py`); Scaffold contract; Single-request semantics — explicit
  and intentional; Counter contract; Extension points (not
  implemented); Promotion-gate coupling; What this doc does not claim
- explicitly records that `cache_pre_claim_admission_contract.py:53-58`
  forbidden actions remain forbidden and the manager is touched only
  after gate claim
- explicitly records that no row in
  `native-mlx-backend-capability-matrix.md` is promoted, declined, or
  re-evaluated by this round

### New tests: `tests/test_cache_manager.py`

- 9 tests, all using fake `mlx_lm` injection (no real `mlx_lm` import):
  - `test_cache_manager_starts_with_zero_counters`
  - `test_acquire_for_request_returns_handle_with_correct_model_id`
  - `test_acquire_calls_make_prompt_cache_via_attribute_walk`
  - `test_acquire_increments_entries_counter`
  - `test_consecutive_acquires_produce_distinct_cache_object_ids`
  - `test_release_drops_handle_reference_without_changing_counters`
  - `test_status_dict_shape_matches_residency_evidence_consumer_expectation`
  - `test_acquire_when_make_prompt_cache_attribute_missing_raises_clear_error`
  - `test_acquire_rejects_empty_model_id`
- tests must pass without the optional `runtime` extra installed
- the fake module pattern mirrors the shape used in
  `tests/test_mlx_native_backend.py` for module-attribute-walk testing

### New round prompt and checkpoint

- `files/execution-prompts/owlmlx/owlmlx-cache-manager-scaffold-landing.md`
  authorizes this round
- `files/execution-prompts/owlmlx/coordinator-checkpoint-cache-manager-scaffold-landed.md`
  (this file) records its close

## Provenance

This is a scaffold round, not a promotion round. There is no
declared-provenance real-candidate evidence to cite, by design:

- no model is loaded
- no upstream `mlx_lm` is invoked at runtime by this round (the
  defensive attribute walk is exercised through fake-module injection
  only)
- no `mlx_lm` version is pinned beyond what
  `mlx_native_backend.py` already records (0.31.2)
- no candidate is admitted or re-admitted in
  `native-mlx-backend-local-candidate-admissibility.md`
- no row crosses §1a Promotion Gate

The scaffold's correctness is entirely structural: the ownership domain
is occupied, the counter ledger is shape-stable, the single-request
semantics is locked by test, and the upstream attribute path is
honored.

## What This Checkpoint Closes

- the question of where in `owlmlx/` the in-process KV cache lifetime
  ownership domain lives — it lives in `owlmlx/cache_manager.py` and is
  distinct from every other `cache_*.py` module in the package
- the question of how existing `cache_residency_evidence.py` consumers
  read manager state — `CacheManager.status_dict()['counters']` matches
  `CacheResidencyMetrics` field names, with all five fields published
  as plain integers
- the question of how cross-request reuse is treated in scaffold —
  `CachedRequestHandle.cross_request_reuse_claimed` is a materialized
  field that always reads `False`, and `status_dict()` exposes the same
  at the top level

## What This Checkpoint Does Not Claim

- `cache_manager.py` is wired into `MlxNativeBackend` — it is not;
  `_make_fresh_prompt_cache` in `owlmlx/runtime/mlx_native_backend.py`
  is unchanged
- eviction policy exists — it does not; `eviction_events` stays at zero
- prefix reuse exists — it does not; `reuse_events` and `hit_count`
  stay at zero
- cross-request handle keying exists — it does not;
  `cross_request_reuse_claimed` stays `False`
- residency tracking beyond zero-baseline counters exists — it does
  not; `resident_bytes` stays at zero
- any row in `native-mlx-backend-capability-matrix.md` has changed —
  no row's status field is modified by this round, including the KV
  cache handle row (held at `partial`) and the KV cache
  reuse-across-requests row (held at `not_in_scope`)
- Line 5 of the seven-line architectural assessment is closed — Line 5
  closure requires C-1.1 wiring + later eviction / prefix reuse /
  cross-request keying rounds; the scaffold lands only the ownership
  domain
- the pre-claim admission contract is weakened — the manager is
  touched only after gate claim, never from the staging seam, and the
  forbidden actions in
  `cache_pre_claim_admission_contract.py:53-58` remain forbidden
- a new public runtime status surface is introduced — `status_dict()`
  is shape-stable, but no serving path consumes it in this round
- a new optional dependency is introduced — the scaffold uses only
  stdlib and the same `mlx_lm` module reference shape that
  `_resolve_make_prompt_cache` already walks
- the active phase45 seam moves —
  `aggregation_active_seam_exact` /
  `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
  remains frozen
- the subprocess sentinel chain is touched — it is not

## Test Counts

This round adds one new test file:

- `tests/test_cache_manager.py`: 9 tests, designed to pass under fake
  `mlx_lm` injection without any optional extra installed.

Coordinator review later ran:

```bash
.venv/bin/python -m pytest \
  tests/test_cache_manager.py \
  tests/test_repeatability_harness.py \
  tests/test_memory_actuator.py \
  tests/test_serving_hardening.py \
  tests/test_mlx_native_backend.py \
  tests/test_mlx_native_backend_post_claim_invariants.py \
  tests/test_mlx_native_backend_real_upstream_binding.py \
  tests/test_mlx_native_backend_real_smoke.py -q
```

Result: `83 passed, 3 skipped` (plus upstream warnings). C-1's scoped
file contributed 9 passed tests.

No existing test file is modified. No existing test count changes.

## Notable Implementation Choices

1. **Stricter resolver than the adapter.** The manager's
   `_resolve_make_prompt_cache` raises `RuntimeError` on missing
   upstream surface, while
   `mlx_native_backend._resolve_make_prompt_cache` returns `None` to
   allow silent skip. The two contracts are deliberately different:
   the adapter must remain robust for fake-mlx_lm tests that never
   intend to bind, while the manager is reached only when the caller
   intends to bind, so a missing surface there is a real bug worth
   surfacing.
2. **Counters as a frozen dataclass replaced on every increment.** The
   `entries += 1` operation creates a new `CacheManagerCounters`
   instance under the lock instead of mutating in place. This costs
   one allocation per acquire and gains a snapshot guarantee on
   `counters()` reads. The other four counters stay at zero by design.
3. **Materialized `cross_request_reuse_claimed` field.** Rather than
   a comment that scaffold "happens to" not reuse, the handle dataclass
   carries the flag explicitly. A future round that turns reuse on
   must flip the flag and accept the §1a obligation; it cannot quietly
   sneak the change in.
4. **No method stubs for extension points.** Eviction, prefix reuse,
   and cross-request keying are described in module-bottom comments
   and in §7 of the architecture doc, but no `evict()`, `lookup()`, or
   `acquire_or_reuse()` method is pre-stubbed. Pre-stubbing would
   suggest the surface is "almost there"; the scaffold's discipline
   is that introducing those methods is its own §1a-style walkthrough,
   not a one-line edit.
5. **Counter shape uses plain int, not Optional[int].** This is
   stricter than `cache_residency_evidence.CacheResidencyMetrics`
   which permits `None` per field. The manager publishes a stable
   shape so consumers see consistent zero-baselines instead of
   "field present / field absent" toggling. A consumer expecting
   `Optional[int]` reads a zero-int as a valid narrowing.

## Discipline Edge Cases

- the existing `cache_*.py` family (141 files) was surveyed by name
  only; no module was opened beyond `cache_truth.py`,
  `cache_residency_evidence.py`, and
  `cache_pre_claim_admission_contract.py`. The survey is sufficient
  to confirm none own KV-cache lifetime, which is all the scaffold
  needs to record
- the executor phase did not run pytest. Coordinator review later ran
  the combined C-x/native scoped pytest sweep and observed
  `83 passed, 3 skipped`
- no `git add` was performed. The operator stages

## Current Frozen Active Seam (No Change)

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- `preserved_secondary_runtime_branch = turboquant_preconditions`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

This checkpoint does not move the active phase45 seam. The cache
manager scaffold is parallel and not invoked by any published serving
path.

## Next Authorized Round

Several candidates, ranked:

### Path C-1.1 (recommended): Cache Manager Wiring Into MlxNativeBackend

- file: `files/execution-prompts/owlmlx/owlmlx-cache-manager-wiring-into-native-mlx-backend.md`
  (to be authored)
- scope: replace the inline `_make_fresh_prompt_cache` call site in
  `MlxNativeBackend.generate` / `stream_generate` with delegation to
  `CacheManager.acquire_for_request` / `release_for_request`; preserve
  single-request semantics; surface `cache_manager.status_dict()` in
  `BackendStatus.detail`
- explicitly does **not** introduce eviction / prefix reuse / cross-
  request keying
- requires §1a-style walkthrough on the KV cache handle row before
  any matrix promotion is even considered

### Path C-2 (parallel-safe): Multi-Prompt Randomized-Load Repeatability Harness

- targets Line 6 (host-stable execution confidence) of the
  seven-line assessment; orthogonal to C-1.1 and can run any time
- doc + harness round; no native adapter changes

### Path C-3 (parallel-safe): Memory Governance Actuator

- targets Line 3 (memory governance) of the seven-line assessment;
  orthogonal to both C-1.1 and C-2
- wraps `mx.clear_cache` / `set_cache_limit` with a runtime-owned
  policy surface

### Path C-4 (parallel-safe): Serving Surface Hardening

- targets Line 4 (serving surface) of the seven-line assessment;
  orthogonal to C-1.x / C-2 / C-3
- request-id middleware, per-request timeout, graceful shutdown
  drain, unified error envelope, `/metrics`

C-1.1 is recommended first because it cashes in this round's frozen
scaffold contract into actual adapter behavior, while operator memory
of the scaffold's invariants is fresh. C-2 / C-3 / C-4 are independent
and can be run any time.

The C-1 scaffold by itself does **not** close Line 5 (cache /
scheduler depth) of the seven-line architectural assessment. Line 5
closure requires C-1.1 wiring + later eviction / prefix reuse /
cross-request keying rounds. This checkpoint records that explicitly
so that no downstream document mistakes the scaffold landing for the
line-closure event.
