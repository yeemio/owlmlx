# owlmlx Execution Prompt C: Release Floor 3.1 Closeout Review And Ledger Decision

> Split note: this parent closeout gate is now split into C-A and C-B execution
> prompts. Use C-A for verification, C-B for ledger/truth decision, then merge
> both outputs under this coordinator gate.
>
> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Coordinator / Reviewer C
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`
> Entry gate: run after A1/B1/B2 and the A2 repeated-dispatch evidence are
> present in the worktree.

## Mission

Perform the closeout review for release floor `3.1` and decide whether the
floor is:

- `closed`
- `progressed`
- `still_blocked`

This is a verification and truth-sync round.
Do not add new scheduler features in this lane.

## Current Coordination Snapshot

Known inputs already present or expected in the worktree:

- A1 restored `tests/test_cache_pre_gate_admission_window_seam.py` to green
  under current staged truth
- B1 produced:
  `docs/source-of-truth/release-floor-3-1-cache-scheduler-capability-audit.md`
- B2 produced:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-verdict-review-handoff.md`
- A2 appears to have added repeated-load proof in
  `tests/test_runtime_kernel.py`:
  `test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load`

Do not trust the snapshot blindly. Re-run the checks below.

## Required Read Order

Read these before deciding:

1. `docs/source-of-truth/release-readiness-backlog.md`
2. `docs/source-of-truth/release-readiness-execution-plan.md`
3. `docs/source-of-truth/release-floor-3-1-cache-scheduler-capability-audit.md`
4. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-verdict-review-handoff.md`
5. `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
6. `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
7. `docs/source-of-truth/replacement-grade-stability-gaps.md`
8. `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
9. `tests/test_cache_pre_gate_admission_window_seam.py`
10. `tests/test_runtime_kernel.py`
11. `tests/test_serving_pre_gate_admission_hook.py`
12. `tests/test_cache_request_aggregation_active_seam.py`

## Hard Rules

1. Do not claim release readiness, parity, replacement, or production grade.
2. Do not mark any floor except `3.1` closed.
3. Do not mark floor `3.1` closed unless every requirement in
   `release-readiness-backlog.md` section 3.1 is satisfied.
4. Exactness-only proof is insufficient.
5. A repeated-load test must prove observable non-exactness scheduler behavior
   on the active runtime path while preserving serial safety.
6. Stream-branch closure is not required for this specific floor if the
   non-stream main runtime path satisfies the "one closed non-exactness
   scheduler capability" requirement, but stream hold must remain documented as
   an open phase45 seam.
7. Do not write runtime code in this lane.
8. Keep unrelated dirty worktree changes untouched.

## Closure Questions

Answer these explicitly:

1. Is `tests/test_cache_pre_gate_admission_window_seam.py` green?
2. Is there a non-exactness scheduler capability on the active runtime path?
3. Is the capability visible in tests under repeated runs?
4. Does the repeated-run proof preserve:
   - `max_concurrent = 1`
   - `ticketed_fifo`
   - whole-request `GenerationGate`
   - `queue_discipline = "serial"`
5. Is the proof behavioral/runtime-observable, not only a seam record?
6. Does section 3.1 of `release-readiness-backlog.md` now close?
7. What remains open after 3.1, especially stream-hold and later floors?

## Required Commands

Run at minimum:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
pytest -q tests/test_runtime_kernel.py -k "repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load or concurrent_generations_handoff_cohort_into_aggregated_child_exchange"
pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q
pytest -q tests/test_cache_request_aggregation_active_seam.py
pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q
git diff --check
```

If A2 added a different focused repeated-load test, run that exact test too.

## Allowed Documentation Updates

If and only if the evidence supports the decision, update:

- `docs/source-of-truth/release-readiness-backlog.md`
  - mark floor `3.1` closed only if all closure questions pass
  - otherwise record `progressed` or leave `open` with exact blocker wording
- `docs/source-of-truth/release-readiness-execution-plan.md`
  - record the closeout result and next active floor
- `docs/source-of-truth/replacement-grade-stability-gaps.md`
  - sync the cache scheduler closure posture
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
  - preserve stream-hold residual truth if 3.1 closes through non-stream path
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
  - add command evidence if the posture changes
- `docs/source-of-truth/master-outline.md`
  - only if new source-of-truth docs are added

Do not update runtime code or tests in this lane.

## Expected Outcome Labels

Return exactly one:

- `owlmlx_release_floor_3_1C_closeout_closed`
- `owlmlx_release_floor_3_1C_closeout_progressed`
- `owlmlx_release_floor_3_1C_closeout_still_blocked`
- `owlmlx_release_floor_3_1C_closeout_blocked_missing_evidence`

Use `closed` only when the release floor itself closes. This still does not
mean `owlmlx` is release-ready.

## Next Floor Selection

If floor `3.1` closes, select the next active floor according to
`release-readiness-execution-plan.md`:

1. `3.3 Model Residency Non-Resident Path`
2. then `3.2 Memory-Pressure Decision Closure`

If floor `3.1` does not close, authorize the smallest next `3.1` round instead
of switching floors.

## Final Report

Return:

- outcome label
- files reviewed
- changed files
- exact commands and results
- answers to all seven closure questions
- floor `3.1` verdict
- if not closed, the exact blocker in floor language
- if closed, the next active floor
- confirmation that no other floor was marked closed
- confirmation that no release/parity/replacement claim was made
- whether active-path truth / handoff files are tracked
