# owlmlx KV Cache Manager — Architecture (Scaffold)

> Status: authoritative
> Updated: 2026-05-12
> Round: C-1 plus native wiring and default-off session-cache extension
> Implementation: `owlmlx/cache_manager.py`

## 1. Why this module exists

The seven-line architectural assessment in
`reference-runtime-comparison-matrix.md` records owlmlx as `behind` on
**Line 5 — Cache / scheduler depth**. The recommended-next-round line in
`native-mlx-backend-capability-matrix.md` §7 names the scaffold path:

> **Line 5 — Cache / scheduler depth (`behind`)**: begins with
> `cache_manager.py` scaffold (C-1)

This document freezes what that scaffold owns, what it deliberately does
not own, and which upstream and owlmlx-internal modules surround it.

The original scaffold did **not** close Line 5 by itself. It landed the
ownership domain so that follow-up rounds could extend it. As of 2026-05-12,
`MlxNativeBackend` consumes `CacheManager` for single-request prompt-cache
lifetime, and `owlmlx/session_kv_cache.py` adds a separate default-off,
explicit-session experimental reuse store. The broader cache / scheduler depth
gap remains open until these extension points are exercised through the
promotion gate with real soak and TTFT evidence.

## 2. Distinct from `cache_truth.py`

`cache_truth.py` (270 lines) owns the **legacy oMLX SSD/hot-cache schema**:

| Owned by `cache_truth.py` |
|---|
| `CacheProfile` labels (`baseline`, `cache-enabled`, `not_running`, `unknown`) |
| `CacheFlags` env / CLI normalization (`OMLX_CACHE_DIR`, `--paged-ssd-cache-dir`, …) |
| Configured / runtime profile derivation |
| `TurboQuantCacheSafety` rules |

`cache_truth.py` has **zero overlap** with the in-process KV cache
lifetime. KV caches are produced by `mlx_lm.models.cache.make_prompt_cache`
on a per-request basis; the SSD/hot-cache schema in `cache_truth.py`
predates the native MLX backend and is platform-shell-oriented. The two
modules describe different objects, live at different layers, and are
not collapsed in this round.

## 3. Ownership boundaries

| Layer | Owner | Concern |
|---|---|---|
| In-process KV cache lifetime (per request) | **`owlmlx/cache_manager.py` (this scaffold)** | acquire / release a fresh upstream cache object per request; expose a 5-counter zero-baseline ledger |
| Upstream KV cache primitives | `mlx_lm.models.cache` | `make_prompt_cache`, `KVCache`, `RotatingKVCache`, `QuantizedKVCache`, `ConcatenateKVCache`, `ChunkedKVCache`, `ArraysCache`, `BatchKVCache`, `BatchRotatingKVCache`, `CacheList`, `TokenBuffer`, `PromptTrie`, `LRUPromptCache` |
| Adapter-side single-request binding | `owlmlx/runtime/mlx_native_backend.py` (`_make_fresh_prompt_cache`) | drives `make_prompt_cache(model)` per `generate` / `stream_generate` and threads it via `prompt_cache=` kwarg |
| Explicit session KV reuse | `owlmlx/session_kv_cache.py` | default-off experimental store for explicit `(session_id, model_id)` cache reuse on the native backend only |
| Legacy SSD / hot-cache schema | `owlmlx/cache_truth.py` | platform-shell-oriented cache profile + TurboQuant safety; not KV-cache-related |
| Cache manager counters | `owlmlx/cache_manager.py` | declares the 5 live counter names; the older `cache_residency_evidence.py` scaffold is archived |
| Pre-claim metadata / ticket staging | `cache_pre_claim_*.py` family (e.g. `cache_pre_claim_admission_contract.py:53-58`), archived to `archive/spec-layer-v0/owlmlx/` | bounded metadata staging seam **before** gate claim; explicitly forbidden actions include `no_gate_claim_from_pre_claim_seam`, `no_child_exchange_from_pre_claim_seam`, `no_stream_start_from_pre_claim_seam`, `no_model_execution_from_pre_claim_seam` |
| Pre-gate admission hook / cohort window | `cache_pre_gate_*.py` family, archived to `archive/spec-layer-v0/owlmlx/` | window feasibility, admission hook exactness; does not own KV cache lifetime |
| Closure rung / counter feasibility / gap | `cache_closure_rung.py`, `cache_counter_*.py`, archived to `archive/spec-layer-v0/owlmlx/` | accounting truth surfaces; do not own KV cache lifetime |

> **Update (2026-05-30)**: the Stage-1 spec-layer archival (`a6d32665` /
> `a2bc5dd5`) moved the `cache_pre_claim_*`, `cache_pre_gate_*`,
> `cache_closure_rung`, and `cache_counter_*` families to
> `archive/spec-layer-v0/owlmlx/` (139 `cache_*.py` files now live there).
> Only **4** `cache_*.py` files remain live in `owlmlx/`:
> `cache_manager.py`, `cache_residency_tracker.py`,
> `cache_scheduler_status.py`, and `cache_truth.py`. The original survey
> sentence below (which counted 141 in `owlmlx/`) describes the pre-archival
> tree and is retained for historical context.

The 141 existing `cache_*.py` files in `owlmlx/` are surveyed by name and
none of them own KV-cache lifetime: they are legacy schema, evidence /
observation, scheduler-truth, or pre-claim metadata staging. The
scaffold respects their boundaries and is not modified by this round.

In particular, **`cache_manager.py` honors the pre-claim contract**:
the manager is touched only after gate claim (i.e. from the
post-admission, model-execution path), never from the pre-claim staging
seam. The forbidden actions in
`cache_pre_claim_admission_contract.py:53-58` remain forbidden; this
scaffold does not weaken them and does not introduce a pre-claim cache
path.

## 4. Scaffold contract

The public API of `CacheManager` is minimal and intentional:

```python
class CacheManager:
    def __init__(self) -> None: ...
    def acquire_for_request(
        self,
        *,
        model_id: str,
        mlx_lm_module: Any,
        model: Any,
    ) -> CachedRequestHandle: ...
    def release_for_request(self, handle: CachedRequestHandle) -> None: ...
    def counters(self) -> CacheManagerCounters: ...
    def status_dict(self) -> dict[str, Any]: ...
```

Intended invariants in this scaffold round:

- `acquire_for_request` produces a **fresh** upstream cache object per
  call; consecutive calls produce distinct `cache_object_id` values
- `acquire_for_request` calls
  `mlx_lm_module.models.cache.make_prompt_cache(model)` via a defensive
  attribute walk that mirrors
  `_resolve_make_prompt_cache` in `mlx_native_backend.py`
- `acquire_for_request` increments **only** the `entries` counter; the
  other four counters stay at zero by design in scaffold semantics
- `release_for_request` drops the handle reference and does **not**
  update any counter (release is incidental in single-request mode and
  is not an eviction event)
- `counters()` returns a frozen `CacheManagerCounters` snapshot
- `status_dict()` returns a payload whose `counters` key exposes the live
  runtime-owned counter names directly
- the manager raises a clear `RuntimeError` when the upstream attribute
  path is missing — the manager's contract is to fail loudly because
  callers reach it only when they intend to bind

## 5. Single-request semantics — explicit and intentional

The scaffold deliberately does **not** do cross-request reuse, even
though `mlx_lm.models.cache.LRUPromptCache` (lines 1589-1729 of the
upstream `cache.py`) is a near-complete eviction engine that owlmlx
could compose against today.

The reasons are intentional, not accidental:

1. **Promotion-gate respect.** Cross-request reuse is a capability
   matrix concern. The KV cache handle row in
   `native-mlx-backend-capability-matrix.md` is held at `partial` after
   B-1/B-1.2 evidence; claiming reuse or moving to `supported` requires
   a §1a-style walkthrough that this scaffold round does not perform.
2. **Adapter coupling.** `MlxNativeBackend._make_fresh_prompt_cache`
   currently establishes that consecutive calls produce **distinct**
   cache objects (single-request semantics locked by test, not by
   convention). Introducing a manager that returns the same object
   across calls would silently void that locked contract.
3. **Pre-claim contract preservation.** Cross-request reuse implies a
   manager-side lookup before model execution; that is the kind of
   action the pre-claim contract scrutinizes. Adopting reuse without a
   walkthrough would risk widening the staging seam.

The scaffold therefore makes the single-request commitment explicit:
`CachedRequestHandle.cross_request_reuse_claimed` is a materialized
field that always reads `False` in scaffold, and `status_dict()` exposes
the same as a top-level key. A future round that turns cross-request
reuse on flips this flag explicitly and accepts the §1a obligation.

## 6. Counter contract

The 5-counter zero-baseline ledger is owned directly by
`CacheManagerCounters`:

| Counter | Scaffold behavior | Future surface |
|---|---|---|
| `entries` | incremented on every successful `acquire_for_request` | total handles ever acquired |
| `resident_bytes` | always zero | future residency tracking layer |
| `reuse_events` | always zero | future cross-request reuse layer |
| `hit_count` | always zero | future prefix lookup layer |
| `eviction_events` | always zero | future LRU / size-pressure eviction layer |

`CacheManagerCounters.to_dict()` returns plain `int` values for every
field (never `None`). The manager publishes a stable shape so runtime
status consumers see consistent zero-baselines instead of "field present /
field absent" toggling.

`status_dict()`'s `counters` key uses the same field names so that the
adapter wiring round (which is **not** this round) can drop the
`status_dict()` output into the existing `BackendStatus.detail` pathway
without a translation layer.

## 7. Extension points (not implemented)

These are extension points for **future rounds**, not code in this
round. Each is named here so the corresponding upstream primitive is on
the record before any future implementation:

### 7.1 Eviction policy

- **Future round responsibility.** A round dedicated to size-pressure
  / count-pressure / TTL eviction.
- **Upstream primitive.** `mlx_lm.models.cache.LRUPromptCache.trim_to`
  (cache.py:1589-1729) implements bytes-bounded LRU eviction with a
  configurable `max_size` and `max_bytes`. A future round may compose
  the manager against this surface or replicate the policy directly.
- **Counter wired.** `eviction_events` is reserved.
- **Scaffold posture.** No `evict()` method is stubbed. Introducing
  one requires §1a-style walkthrough on the affected matrix rows.

### 7.2 Prefix reuse

- **Future round responsibility.** A round that keys cache handles by
  tokenized prefix and returns an existing cache when a hit is found.
- **Upstream primitive.** `mlx_lm.models.cache.PromptTrie.search`
  (cache.py:1498-1586) implements a token-keyed trie search.
  `mlx_lm.models.cache.trim_prompt_cache` provides the corresponding
  per-handle truncation primitive.
- **Counters wired.** `reuse_events`, `hit_count`.
- **Scaffold posture.** No `lookup()` / `search()` method is stubbed.
  `CachedRequestHandle.cross_request_reuse_claimed` stays `False`.

### 7.3 Cross-request handle keying

- **Future round responsibility.** A round that introduces a stable
  handle key (e.g. `(model_id, prefix_hash, dtype, max_kv_size)`) and
  returns an existing handle in lieu of producing a fresh one.
- **Upstream primitive.** `mlx_lm.models.cache.make_prompt_cache(model, max_kv_size=None)`
  parameterization, plus the trie / LRU primitives above.
- **Counter wired.** `reuse_events` (with handle-level granularity);
  `hit_count` (with key-level granularity).
- **Scaffold posture.** Handle keying is deliberately **not**
  pre-stubbed. The decision to introduce it must be a §1a-style
  walkthrough in its own round.

## 8. Promotion-gate coupling

This scaffold does **not** promote any row in
`docs/source-of-truth/native-mlx-backend-capability-matrix.md`. Specifically:

- the **KV cache handle (`make_prompt_cache`)** row, currently held at
  `partial`, is **not** advanced by this round
- the **KV cache reuse across requests** row, currently held at
  `not_in_scope`, is **not** changed (the scaffold deliberately enforces
  single-request semantics; reuse remains structurally absent, not
  merely undocumented)
- no other native row's status changes

Future wiring of `CacheManager` into `MlxNativeBackend` and any
subsequent extension-point landing (eviction / prefix reuse / keying)
will require:

1. real-load evidence on an admitted candidate (matrix §1a gate 2)
2. a coordinator-checkpoint document with provenance citation
3. a §1a-style row-by-row walkthrough that names the upstream stable
   API and confirms no upstream patching is required

This scaffold deliberately skips all three by remaining unwired and not
claiming any matrix transition.

> **Update (2026-05-30)**: the "remaining unwired" framing above describes
> the original C-1 scaffold round only. As of C-1.1 / C-1.2 (commit
> `fc27a021`, 2026-05-12) `CacheManager` **is** wired into
> `MlxNativeBackend`: `mlx_native_backend.py` imports it (`:37`),
> instantiates `self._cache_manager = CacheManager()` (`:343`), acquires a
> per-request handle via `acquire_for_request(...)` (`:412`), and releases
> it via `release_for_request(...)` (`:677`). This wiring drove **no**
> matrix-row promotion — the gate obligations (1)–(3) above remain the bar
> for any status transition, which is still pending. §1 reflects this
> as-built state.

## 9. What this doc does not claim

> **Update (2026-05-30)**: the first bullet below was true for the C-1
> scaffold round but is now stale — `CacheManager` was wired into
> `MlxNativeBackend` in C-1.1 / C-1.2 (`fc27a021`); see the §8 update and
> §1. The remaining bullets (no eviction / prefix reuse / cross-request
> keying; no matrix-row promotion; no Line 5 closure) still hold.

- it does **not** claim `cache_manager.py` is wired into
  `MlxNativeBackend` — the adapter remains untouched in this round
  *(superseded — see the 2026-05-30 update above)*
- it does **not** claim eviction, residency tracking beyond
  zero-baseline counters, prefix reuse, or cross-request handle keying
  exist
- it does **not** claim any matrix row has been promoted, declined, or
  re-evaluated
- it does **not** claim Line 5 (cache / scheduler depth) is closed —
  Line 5 closure requires the extension points described in §7 to be
  implemented and walked through §1a; this scaffold lands only the
  ownership domain
- it does **not** claim `cache_manager.py` replaces, supersedes, or
  overlaps with `cache_truth.py` — the two modules describe disjoint
  concerns
- it does **not** claim the pre-claim contract is weakened — the
  manager is touched only after gate claim
- it does **not** introduce a runtime status surface change — the
  scaffold provides `status_dict()` as a shape-stable read, but no
  serving path consumes it in this round
- it does **not** introduce new optional dependencies — the manager
  uses only stdlib and the same `mlx_lm` module reference shape that
  the existing native adapter resolves
