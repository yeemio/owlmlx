# Stage 3.3 Track B Resume — Cache / Residency / Eviction Runtime Loop

## Role

You are the Track B runtime executor for `owlmlx`.

Your job is to resume the current `owlmlx` mainline: implement the first
runtime-owned cache / residency / eviction loop.

Important correction:

```text
owlmlx mainline remains owlmlx runtime capability.
OwlCoda is a downstream consumer, not this round's implementation target.
The OwlCoda learning loop is a future public-release acceptance gate, not the
current Track B scope.
```

This round must stay inside `owlmlx`.

## Starting Point

Repository:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
git switch refactor/runtime-spine-stage-1-to-3.1
git switch -c refactor/stage-3.3-cache-eviction-activation
```

Before editing, read:

- `AGENTS.md`
- `docs/source-of-truth/owlcoda-learning-loop-coordination.md`
- `docs/source-of-truth/runtime-spine-architecture-blueprint.zh.md`
- `docs/source-of-truth/public-release-standard.md`
- `files/execution-prompts/owlmlx/stage-3.3-track-b-cache-eviction-activation.md`
- `owlmlx/cache_manager.py`
- `owlmlx/cache_residency_tracker.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/model_residency_policy.py`
- `owlmlx/runtime/kernel.py`
- `owlmlx/runtime/server.py`
- relevant tests for the files above

## Goal

Build a deterministic, testable runtime loop:

```text
load decision
  -> residency state
  -> memory pressure signal
  -> deterministic eviction candidate
  -> unload / release ledger
  -> runtime status evidence
```

This is an `owlmlx` runtime-foundation capability. It supports future
long-running local learning, but it does **not** close public release and does
**not** implement OwlCoda integration.

## Write Scope

Allowed code files:

- `owlmlx/cache_manager.py`
- `owlmlx/cache_residency_tracker.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/model_residency_policy.py`
- `owlmlx/runtime/kernel.py`
- `owlmlx/runtime/server.py`
- `owlmlx/runtime/types.py` only if typed result fields are required

Allowed tests:

- `tests/test_cache_manager.py`
- `tests/test_cache_residency_tracker.py`
- `tests/test_memory_pressure_eviction_policy.py`
- `tests/test_model_residency_policy.py`
- `tests/test_runtime_kernel*.py`
- new focused tests if needed

Allowed checkpoint:

- optional new file under `files/execution-prompts/owlmlx/`

Forbidden:

- any OwlCoda repo file
- any OwlOps repo file
- anything under `/Users/yeemio/AI/Agent`
- `docs/source-of-truth/contract-mapping.md`
- `docs/source-of-truth/extraction-inventory.md`
- `docs/source-of-truth/system-architecture.md`
- PR #1 body
- `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`

## Required Behavior

Implement enough runtime behavior to prove all of the following without loading
a real large model:

1. The runtime can identify an eviction candidate from residency state.
2. Pinned models are never selected for eviction.
3. Active / hot models outrank resident models.
4. Evictable models are selected before resident / hot models.
5. Same-priority ties resolve deterministically, preferably by LRU or
   last-used sequence.
6. Eviction invokes the normal runtime unload path or a clearly factored
   internal release path.
7. Release ledger records at least model id, reason, sequence, and relevant
   use-count / residency facts.
8. Failed unload / release is surfaced as a structured blocker and is not
   marked successful.
9. Runtime status exposes the last eviction decision or a bounded eviction
   ledger summary.
10. No prefix-cache, continuous-batching, cache-parity, or public-release claim
    is introduced.

## Suggested Implementation Shape

Prefer improving existing runtime-consumed primitives over adding new modules.

Possible shape:

```python
RuntimeKernel.evict_for_memory_pressure(...)
RuntimeKernel.cache_residency_status(...)
```

or a narrower internal helper if that fits the current kernel design better.

Use existing modules first:

- `cache_manager.py`
- `cache_residency_tracker.py`
- `memory_pressure_eviction_policy.py`
- `model_residency_policy.py`

Do not create a new spec-as-code module. A new Python module is allowed only if
`owlmlx/runtime/` imports it and reads its fields/functions in real runtime
logic.

## Tests To Add Or Update

Required test coverage:

1. `pinned_models_never_evicted`
2. `evictable_selected_before_resident_or_hot`
3. `hot_or_active_model_not_evicted_under_normal_pressure`
4. `lru_tiebreak_is_deterministic`
5. `eviction_records_release_ledger_event`
6. `failed_unload_surfaces_blocker`
7. `runtime_status_exposes_eviction_state`
8. `no_prefix_cache_batching_or_public_release_claims_added`

Use fake backend objects for core tests. Live model smoke is optional and must
not be part of default pytest.

## Verification

Run focused tests first:

```bash
uv run pytest \
  tests/test_cache_manager.py \
  tests/test_cache_residency_tracker.py \
  tests/test_memory_pressure_eviction_policy.py \
  tests/test_model_residency_policy.py \
  tests/test_runtime_kernel*.py \
  -q
```

Then run:

```bash
uv run pytest -q
git diff --check
git status --short
```

If you add or modify HTTP routes, run a temporary server smoke:

```bash
uv run --extra runtime python scripts/runtime_technical_preview_server.py \
  --host 127.0.0.1 \
  --port 8079 \
  --models-root /Users/yeemio/AI/Agent/models \
  --backend-timeout-s 30 \
  --runtime-monitor-sample-interval-s 0 \
  --log-level warning
```

Then curl only touched route(s) plus:

```bash
curl -fsS http://127.0.0.1:8079/healthz
curl -fsS http://127.0.0.1:8079/v1/runtime/memory-watermark | python3 -m json.tool
```

Stop the temporary server after smoke.

## Commit Discipline

Prefer one or two focused commits:

1. policy/tracker/kernel behavior
2. HTTP status surface, only if touched

Do not stage `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`.
Do not use `git add .`.

## Final Report

Report:

- branch name
- commits
- files changed
- exact behavior now owned by `owlmlx`
- labels that remain unchanged
- tests run and results
- route smoke results if any
- blockers / deferred items

## Final Status Wording

Use:

```text
stage_3_3_cache_residency_eviction_loop_partial_owned
```

Do not use:

```text
prefix_cache_supported
continuous_batching_supported
cache_parity_supported
public_release_ready
owlcoda_learning_loop_complete
omlx_patch_migrated
```
