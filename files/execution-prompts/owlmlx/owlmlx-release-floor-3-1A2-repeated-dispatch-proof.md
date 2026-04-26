# owlmlx Execution Prompt A2: Release Floor 3.1 Repeated Dispatch Proof

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor A2
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`
> Entry gate: do not start unless Executor A1 has restored
> `tests/test_cache_pre_gate_admission_window_seam.py` to truthful green or
> produced an accepted hard-downgrade verdict.

## Mission

Produce the smallest honest runtime/test proof for non-exactness scheduler
behavior on the active runtime path.

The target is not another marker/discriminant exactness layer.
The target is repeated-load evidence that the cache scheduler path has a real
capability beyond exactness narration.

## Coordination Truth

Read these first:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A-pre-gate-test-truth-restoration.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B-cache-scheduler-capability-audit.md`
- Executor A1 final report, if available
- Executor B1 final report, if available
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
- `owlmlx/runtime/kernel.py`
- `owlmlx/serving.py`
- `owlmlx/cache_request_aggregation_active_seam.py`
- `tests/test_runtime_kernel.py`
- `tests/test_serving_pre_gate_admission_hook.py`
- `tests/test_cache_request_aggregation_active_seam.py`

## Owned Write Scope

Executor A2 may edit:

- `owlmlx/runtime/kernel.py`
- `owlmlx/serving.py`
- `tests/test_runtime_kernel.py`
- `tests/test_serving_pre_gate_admission_hook.py`
- `tests/test_cache_request_aggregation_active_seam.py` only if the new proof
  needs to connect runtime behavior to active seam truth
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md` only if
  the runtime evidence posture changes

Do not edit:

- `tests/test_cache_pre_gate_admission_window_seam.py`
- `owlmlx/cache_pre_gate_admission_window_seam.py`
- comparative-evidence / 3.5 files
- memory-pressure, residency, recovery, public-surface, or external evidence
  floors

## Hard Rules

1. Do not claim release readiness, parity, replacement, or production grade.
2. Do not describe exactness-only proof as release-floor closure.
3. Do not implement continuous batching unless the smallest existing runtime
   path already proves a bounded dispatch-level capability.
4. Do not introduce multi-worker scheduling.
5. Preserve `max_concurrent=1`, `ticketed_fifo`, and whole-request
   `GenerationGate`.
6. Do not weaken stream safety to make aggregation appear green.
7. Do not broaden into memory-pressure, residency, recovery, or comparative
   evidence work.
8. Keep unrelated dirty worktree changes untouched.

## Required Work

1. Confirm the entry gate:

   ```bash
   pytest -q tests/test_cache_pre_gate_admission_window_seam.py
   ```

   If this is not green and no accepted hard-downgrade verdict exists, stop as
   `owlmlx_release_floor_3_1A2_blocked_on_A1_gate`.

2. Identify the smallest runtime behavior that can prove a non-exactness
   scheduler capability, preferably one of:

   - bounded request-aggregation cohort forms before whole-request gate claim
   - one child exchange carries more than one request in a runtime-like path
   - repeated load shows observable aggregated dispatch without weakening
     serial post-claim safety

3. Add the smallest focused test that proves the behavior under repeated or
   concurrent load.

4. If the runtime path exists but lacks instrumentation, add the smallest
   runtime-owned observation needed for the test.

5. If the runtime path does not exist, do not build a broad scheduler. Stop with
   the exact missing capability.

## Expected Outcome Labels

Return exactly one:

- `owlmlx_release_floor_3_1A2_repeated_dispatch_proof_introduced`
- `owlmlx_release_floor_3_1A2_repeated_dispatch_proof_progressed`
- `owlmlx_release_floor_3_1A2_blocked_on_A1_gate`
- `owlmlx_release_floor_3_1A2_still_blocked_by_missing_runtime_capability`

Use `introduced` only when a test proves non-exactness scheduler behavior on
the active runtime path.

## Required Checks

Run at minimum:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
pytest -q tests/test_cache_request_aggregation_active_seam.py
pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q
pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q
python3 -m py_compile owlmlx/runtime/kernel.py owlmlx/serving.py owlmlx/cache_request_aggregation_active_seam.py
git diff --check
```

If you add a narrower focused test, run it explicitly and report the command.

## Final Report

Return:

- outcome label
- changed files
- exact commands and results
- entry-gate status from A1
- what non-exactness scheduler behavior was proved, if any
- whether floor `3.1` is closed, progressed, or still blocked from A2's view
- if not closed, the exact remaining blocker in floor language
- confirmation that no other release floor was worked
- confirmation that no release/parity/replacement claim was made
