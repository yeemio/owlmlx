# Stage 3.3 Track B — Cache / Residency / Eviction Activation

## Role

You are the Track B executor for `owlmlx`.

Your job is to implement the first owned runtime capability lane after the
runtime-spine milestone: a real cache / residency / eviction loop owned by
`owlmlx`.

This is a runtime implementation track. It must stay independent from oMLX
patch tooling and from Track A's documentation cleanup.

## Starting Point

Repository:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
```

Start from the milestone branch:

```bash
git switch refactor/runtime-spine-stage-1-to-3.1
git switch -c refactor/stage-3.3-cache-eviction-activation
```

Before editing, read:

- `AGENTS.md`
- `docs/handoff/runtime-spine-stage-1-to-3-1-closeout-handoff-20260512.md`
- `owlmlx/cache_manager.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/model_residency_policy.py`
- `owlmlx/runtime/kernel.py`
- `owlmlx/runtime/server.py`
- existing tests for those modules

## Goal

Build the first real owned cache / residency / eviction runtime loop:

```text
load decision
  -> residency state
  -> memory pressure signal
  -> deterministic eviction candidate
  -> unload / release ledger
  -> status surface evidence
```

This is not prefix-cache activation and not batching. The capability is
eviction / residency closure only.

## Write Scope

Allowed code files:

- `owlmlx/cache_manager.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/model_residency_policy.py`
- `owlmlx/runtime/kernel.py`
- `owlmlx/runtime/server.py`
- `owlmlx/runtime/types.py` if a typed result field is needed

Allowed tests:

- `tests/test_cache_manager.py`
- `tests/test_memory_pressure_eviction_policy.py`
- `tests/test_model_residency_policy.py`
- `tests/test_runtime_kernel*.py`
- new focused tests if needed

Allowed checkpoint:

- optional new file under `files/execution-prompts/owlmlx/`

Forbidden files:

- `docs/source-of-truth/contract-mapping.md`
- `docs/source-of-truth/extraction-inventory.md`
- `docs/source-of-truth/system-architecture.md`
- PR #1 body
- anything under `/Users/yeemio/AI/Agent`
- `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`

Track A owns architecture wording. Track B owns runtime behavior.

## Required Capability

Implement a deterministic eviction loop that can be exercised without loading a
real 30B model.

At minimum, the runtime must expose enough behavior to prove:

1. The kernel can identify an eviction candidate from residency state.
2. Pinned models are never selected.
3. Active / hot models outrank resident models.
4. Evictable models are selected before resident / hot models.
5. Ties are deterministic, preferably by LRU / last-used sequence.
6. Eviction invokes the normal unload path or a clearly factored internal
   release path.
7. Release ledger records the eviction reason and model id.
8. Runtime status exposes the last eviction decision or a bounded eviction
   ledger summary.
9. The behavior is covered with fake backend / fake memory pressure tests.

## Suggested Implementation Shape

Prefer small, runtime-consumed primitives over new spec modules.

Possible shape:

- Add a method on `RuntimeKernel`, for example:

  ```python
  def evict_for_memory_pressure(self, *, reason: str = "memory_pressure") -> dict[str, Any]:
      ...
  ```

- Or add a narrower internal method if there is already a suitable public route
  boundary.

- Reuse existing residency and eviction-policy modules rather than inventing a
  new policy file.

- Add a route only if it is useful for runtime operation or observability, for
  example:

  ```text
  POST /v1/runtime/cache/evict
  GET /v1/runtime/cache/residency
  ```

  If adding mutation routes feels too broad, add read-only status first and
  keep active eviction inside the kernel test path.

## Hard Rules

- Do not touch Agent/oMLX patch tooling.
- Do not mention Stage 3.2 swap-safe migration.
- Do not claim prefix cache, cross-request cache reuse, continuous batching, or
  scheduler parity.
- Do not add module-as-spec files. Any new Python module must be consumed by
  `owlmlx/runtime/`.
- Do not use real model loads for core tests.
- Do not silently evict pinned models.
- Do not hide failed unloads. Failed eviction must surface as a structured
  blocker and must not be marked successful.
- Do not mutate `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`.

## Tests To Add Or Update

Required tests:

1. `pinned_models_never_evicted`
2. `evictable_selected_before_resident_or_hot`
3. `lru_tiebreak_is_deterministic`
4. `eviction_records_release_ledger_event`
5. `failed_unload_surfaces_blocker`
6. `runtime_status_exposes_eviction_state`
7. `no_prefix_cache_or_batching_claims_added`

Use fake backend objects where possible. Only add live smoke as an optional
manual step, not as default pytest.

## Verification

Run:

```bash
uv run pytest tests/test_cache_manager.py tests/test_memory_pressure_eviction_policy.py tests/test_model_residency_policy.py -q
uv run pytest -q
git diff --check
git status --short
```

If you add or modify HTTP routes, also run a temporary server smoke with:

```bash
uv run --extra runtime python scripts/runtime_technical_preview_server.py \
  --host 127.0.0.1 \
  --port 8079 \
  --models-root /Users/yeemio/AI/Agent/models \
  --backend-timeout-s 30 \
  --runtime-monitor-sample-interval-s 0 \
  --log-level warning
```

Then curl only the touched route(s) plus:

```bash
curl -fsS http://127.0.0.1:8079/healthz
curl -fsS http://127.0.0.1:8079/v1/runtime/memory-watermark | python3 -m json.tool
```

Stop the temporary server after smoke.

## Deliverables

- One or more runtime commits on `refactor/stage-3.3-cache-eviction-activation`.
- Tests proving the eviction loop.
- Optional checkpoint under `files/execution-prompts/owlmlx/`.
- Final report with:
  - exact files changed
  - capability that is now genuinely owned
  - capability labels that did not change
  - tests run
  - route smoke results if routes changed
  - blockers or deferred items

## Final Status Wording

Use this verdict if successful:

```text
stage_3_3_cache_residency_eviction_loop_partial_owned
```

Do not use:

```text
prefix_cache_supported
continuous_batching_supported
cache_parity_supported
omlx_patch_migrated
```
