# owlmlx Execution Prompt: Release Floor 3.1 Cache Scheduler Closure

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Coordinator decision: `release-readiness-backlog.md` now governs the loop.
> The next active round must reduce release floor `3.1 cache scheduler
> closure`, not add another side surface.

## Coordination Truth

`docs/source-of-truth/release-readiness-backlog.md` is authoritative.

Current top-level verdict:

- `owlmlx` is an `early_formal_runtime, below reference-grade stability`
- no external release, parity, production-grade, or replacement claim is honest
- all seven release floors remain open

The next active floor is:

- `3.1 Cache Scheduler Closure Beyond Exactness`

Why this floor first:

- `phase45-dominant-gap-reselection.md` already selected
  `cache_scheduler_depth`
- the active seam is `owlmlx.cache_request_aggregation_active_seam`
- `release-readiness-backlog.md` explicitly says exactness alone does not close
  this floor
- `tests/test_cache_pre_gate_admission_window_seam.py` is currently not green

Coordinator reproduction before this prompt:

```text
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
-> 3 failed, 2 passed
```

Failure shape:

- three tests instantiate `CacheRequestAggregationActiveSeam` with an older
  constructor shape
- the dataclass now requires five newer earlier-runtime-owned-boundary fields:
  - `stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness`
  - `stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness`
  - `stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness`
  - `stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness`
  - `stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness`

Fixing this test drift is necessary but not sufficient. The floor requires
non-exactness scheduler closure, or an honest still-blocked verdict saying why
that closure cannot yet be claimed.

## Objective

Make release floor `3.1 cache scheduler closure` measurably less open.

This round must do both:

1. restore the failing `test_cache_pre_gate_admission_window_seam_*` family to
   a truthful state, either green or honestly downgraded with a tracked reason
2. produce one release-floor-focused verdict on whether any non-exactness cache
   scheduler capability is now closed on the active runtime path

Allowed outcome labels:

- `owlmlx_release_floor_3_1_cache_scheduler_closure_progressed`
- `owlmlx_release_floor_3_1_cache_scheduler_closure_closed`
- `owlmlx_release_floor_3_1_cache_scheduler_closure_still_blocked`

Use `closed` only if the release floor requirement in
`release-readiness-backlog.md` section 3.1 is fully satisfied.

## Hard Rules

1. Do not add unrelated orchestration surfaces.
2. Do not work on failed unload/reclaim barrier events in this round.
3. Do not work on memory-pressure eviction ordering in this round.
4. Do not work on non-resident model load/defer/reject policy in this round.
5. Do not work on public surface or comparative benchmark floors in this round.
6. Do not continue marker-discriminant exactness unless it directly restores
   the floor-3.1 test/truth gate.
7. Do not claim release readiness, parity, replacement, or production grade.
8. Do not describe exactness as release closure.
9. Preserve current serial safety invariants: `max_concurrent=1`,
   `ticketed_fifo`, and whole-request `GenerationGate`.
10. Do not bypass the active seam truth in
    `owlmlx.cache_request_aggregation_active_seam`.
11. Keep unrelated dirty worktree changes untouched.

## Required Read Order

Read these before editing:

1. `docs/source-of-truth/release-readiness-backlog.md`
2. `docs/source-of-truth/delivery-discipline.md`
3. `docs/source-of-truth/phase45-dominant-gap-reselection.md`
4. `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
5. `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
6. `docs/source-of-truth/replacement-grade-stability-gaps.md`
7. `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
8. `owlmlx/cache_pre_gate_admission_window_seam.py`
9. `owlmlx/cache_request_aggregation_active_seam.py`
10. `owlmlx/runtime/kernel.py`
11. `owlmlx/serving.py`
12. `tests/test_cache_pre_gate_admission_window_seam.py`
13. `tests/test_cache_request_aggregation_active_seam.py`
14. `tests/test_runtime_kernel.py`
15. `tests/test_serving_pre_gate_admission_hook.py`

## Execution Gate 1: Restore Test Truth

First reproduce:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
```

Then decide honestly:

- if the tests are stale relative to the current dataclass, update the tests or
  shared fixtures so they instantiate current truth
- if the implementation regressed, fix the implementation
- if the preserved seam doc is no longer the active runtime truth, update the
  doc and higher-level truth instead of forcing the test to lie

After the fix, this command must pass or be explicitly reported as the round's
blocking failure:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
```

## Execution Gate 2: Floor 3.1 Non-Exactness Assessment

After test truth is restored, evaluate the actual release-floor requirement:

> one closed non-exactness scheduler capability must exist on the active runtime
> path, such as observable aggregated dispatch under repeated load or a bounded
> continuous-batching seam closed at dispatch level.

Do not assume this is already true.

Inspect runtime/test surfaces for:

- bounded request-aggregation cohort formation
- observable aggregated dispatch under repeated load
- child-exchange dispatch accepting more than one request in a real test path
- repeated-run proof, not only constructor/exactness proof
- current stream-hold boundary impact on dispatch

If the capability already exists but is under-tested, add the smallest focused
test that proves it.

If it does not exist, do not implement a broad scheduler rewrite unless the
smallest runtime path is already present. Instead, return
`owlmlx_release_floor_3_1_cache_scheduler_closure_progressed` or
`..._still_blocked` with the exact missing runtime capability.

## Required Documentation Updates

Update only the truth needed for this floor:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md` if the
  customer/replacement evidence posture changes
- `docs/source-of-truth/runtime-capability-matrix.md` only if a capability label
  changes
- `docs/source-of-truth/master-outline.md` only if a new authoritative truth
  doc is added

If floor 3.1 is not fully closed, section 5 of
`release-readiness-backlog.md` must remain open. You may add a progress note,
but do not mark closed.

## Required Tests / Checks

Run at minimum:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
pytest -q tests/test_cache_request_aggregation_active_seam.py
pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q
pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q
python3 -m py_compile owlmlx/cache_pre_gate_admission_window_seam.py owlmlx/cache_request_aggregation_active_seam.py owlmlx/runtime/kernel.py owlmlx/serving.py
git diff --check
```

If you add or modify a repeated-load scheduler test, run it explicitly and
report the exact command.

## Final Report

Return:

- outcome label
- changed files
- exact commands and results
- whether `tests/test_cache_pre_gate_admission_window_seam.py` is green
- whether floor 3.1 is closed, progressed, or still blocked
- if not closed, the exact remaining blocker in floor language
- confirmation that no other release floor was claimed closed
- confirmation that no release/parity/replacement claim was made
- whether all active-path truth / prompt files are tracked

If this round cannot honestly reduce floor 3.1, stop as
`owlmlx_release_floor_3_1_cache_scheduler_closure_still_blocked` and state the
smallest missing runtime signal or implementation path. Do not widen into
side-surface work.
