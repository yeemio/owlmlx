# owlmlx Execution Prompt A: Release Floor 3.1 Pre-Gate Test Truth Restoration

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor A
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`

## Mission

Restore the red pre-gate admission-window seam test family to a truthful state
so release floor `3.1` has a reliable baseline.

This is not a broad scheduler rewrite.
This is the blocking red-gate repair lane.

## Coordination Truth

Read these first:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `owlmlx/cache_pre_gate_admission_window_seam.py`
- `owlmlx/cache_request_aggregation_active_seam.py`
- `tests/test_cache_pre_gate_admission_window_seam.py`

Current coordinator reproduction:

```text
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
-> 3 failed, 2 passed
```

Failure shape:

- three tests instantiate `CacheRequestAggregationActiveSeam` with an older
  constructor shape
- the dataclass now requires five newer earlier-runtime-owned-boundary fields

## Owned Write Scope

Executor A may edit only these areas unless a blocking implementation mismatch
requires a tiny adjacent fix:

- `tests/test_cache_pre_gate_admission_window_seam.py`
- `tests/` helper fixtures if you introduce a shared current
  `CacheRequestAggregationActiveSeam` factory
- `owlmlx/cache_pre_gate_admission_window_seam.py` only if the implementation,
  not the test, is wrong
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md` only if
  the test repair proves the preserved seam truth itself is stale

Do not edit:

- `owlmlx/cache_request_aggregation_active_seam.py`
- `tests/test_cache_request_aggregation_active_seam.py`
- release-floor docs outside the single preserved seam doc above
- orchestration, memory-pressure, residency, recovery, or public-surface files

Executor B owns the independent non-exactness scheduler capability audit.
Do not duplicate B's work.

## Hard Rules

1. Do not mark release floor `3.1` closed.
2. Do not claim release readiness, parity, replacement, or production grade.
3. Do not use exactness-only wording as release progress.
4. Do not add new marker-discriminant exactness surfaces.
5. Preserve `max_concurrent=1`, `ticketed_fifo`, and whole-request
   `GenerationGate`.
6. Keep unrelated dirty worktree changes untouched.
7. If the test is stale, fix the test honestly.
8. If implementation regressed, fix the implementation honestly.
9. If truth docs are stale, say so and update only the required seam doc.

## Required Work

1. Reproduce the failing test:

   ```bash
   pytest -q tests/test_cache_pre_gate_admission_window_seam.py
   ```

2. Inspect the current `CacheRequestAggregationActiveSeam` dataclass and decide
   whether the failure is stale-test drift or implementation drift.

3. Restore the test family to truthful green or produce a hard blocked result.

4. Run the immediate adjacent tests:

   ```bash
   pytest -q tests/test_cache_pre_gate_admission_window_seam.py
   pytest -q tests/test_cache_request_aggregation_active_seam.py
   python3 -m py_compile owlmlx/cache_pre_gate_admission_window_seam.py owlmlx/cache_request_aggregation_active_seam.py
   git diff --check
   ```

## Expected Outcome Labels

Return exactly one:

- `owlmlx_release_floor_3_1A_pre_gate_test_truth_restored`
- `owlmlx_release_floor_3_1A_pre_gate_test_truth_still_blocked`

## Final Report

Return:

- outcome label
- changed files
- exact commands and results
- whether `tests/test_cache_pre_gate_admission_window_seam.py` is green
- whether the failure was stale-test drift, implementation drift, or stale truth
- whether any source-of-truth doc changed
- explicit statement that floor `3.1` is not closed by this lane alone
- explicit statement that no release/parity/replacement claim was made
