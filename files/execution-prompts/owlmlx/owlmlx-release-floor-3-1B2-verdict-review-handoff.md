# owlmlx Execution Handoff B2: Release Floor 3.1 Verdict Review

> Lane: Executor B2 (read-only verdict review)
> Updated: 2026-04-25
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`
> Scope: merge-review of A1 / B1 evidence (A2 not yet landed) and floor verdict
> recommendation

## 1. Outcome Label

`owlmlx_release_floor_3_1B2_verdict_review_progressed_recommended`

Floor 3.1 is **not closed**. It is **progressed**. A2 has not yet produced its
repeated-load proof, and the stream branch still holds at the active phase45
seam. Detailed evidence below.

## 2. Reports / Files Reviewed

Lane prompts:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A-pre-gate-test-truth-restoration.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B-cache-scheduler-capability-audit.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A2-repeated-dispatch-proof.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-floor-verdict-review.md`

Coordination truth:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/phase45-dominant-gap-reselection.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`

Lane outputs reviewed:

- A1: no separate final-report file in `files/execution-prompts/`. A1's
  evidence is the staged delta itself:
  - `tests/test_cache_pre_gate_admission_window_seam.py` (M, 207-line addition
    visible in `git diff --cached --stat`)
  - `owlmlx/cache_request_aggregation_active_seam.py` (MM; 1618 staged
    insertions adding the five new earlier-runtime-owned-boundary fields and
    their wiring)
  - reproduction: `pytest -q tests/test_cache_pre_gate_admission_window_seam.py`
    -> 5 passed
- B1: `docs/source-of-truth/release-floor-3-1-cache-scheduler-capability-audit.md`
  (untracked / written by Executor B1)
- A2: not landed. No new test file matching `tests/test_cache_*repeated*` and
  no new instrumentation in runtime modules referenced by the A2 prompt.

## 3. Changed Files By This Lane

Only this handoff document. Read-only review otherwise.

## 4. Commands and Results

```text
$ pytest -q tests/test_cache_pre_gate_admission_window_seam.py
... 5 passed in 0.09s

$ pytest -q tests/test_cache_request_aggregation_active_seam.py
... 15 passed in 0.10s

$ pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py
... 27 passed in 0.78s

$ pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py
... 60 passed in 18.61s

$ git diff --check
(clean)
```

A2 added no narrower test, so no extra command was applicable.

## 5. Review Question Answers

### Q1. Is `tests/test_cache_pre_gate_admission_window_seam.py` green or honestly downgraded with a tracked reason?

**Green.** The current worktree shows 5/5 passing under the staged A1 delta
(test file rewrite plus the 5 new earlier-runtime-owned-boundary fields on
`CacheRequestAggregationActiveSeam`). The reproduction baseline cited in the
3.1 prompt (`3 failed, 2 passed`) is no longer reachable in this worktree.

Caveat: A1's separate final-report file does not exist in
`files/execution-prompts/`. The verdict here treats the staged delta plus
the green test command as the equivalent evidence. If the coordinator wants
a written A1 final report on disk, that is a paperwork action, not a
runtime gap.

### Q2. Did A2 introduce or prove a non-exactness scheduler capability on the active runtime path?

**No. A2 has not landed.** No new test, no new runtime instrumentation, no
new doc edit attributable to A2 is present in the worktree. The pre-A2
non-exactness capability that B1 mapped is what remains:

- `tests/test_cache_cohort_to_child_exchange_handoff_harness.py` proves a
  single-iteration runtime-path cohort handoff via two concurrent
  `kernel.generate()` (asyncio.gather), landing in one aggregated child
  exchange (`aggregated_request_count >= 2`, `aggregated_batch_count >= 1`,
  `gate_total_served == 2`, `max_concurrent == 1`,
  `queue_discipline == "serial"`).
- `tests/test_cache_child_exchange_aggregated_dispatch_harness.py` proves
  the backend-only path (`exchange_count == 1`, `batch_size == 2`).
- `tests/test_serving_pre_gate_admission_hook.py
  ::test_pre_gate_hook_exists_before_claim_without_reopening_post_claim_invariants`
  proves the bounded pre-gate cohort window forms before whole-request gate
  claim under midflight observation.

This is real non-exactness evidence already in the tree. It is not the same
thing as A2's intended repeated-load proof.

### Q3. Is the proof repeated-run or runtime-like, not just constructor/exactness proof?

**Runtime-like, not yet repeated-run.**

- The cohort-to-child handoff harness is a real runtime path through
  `RuntimeKernel` + `MlxLmSubprocessBackend` with `asyncio.gather`. It is
  not a constructor or exactness fixture.
- No test currently iterates the harness (or any equivalent path) across
  multiple cohorts in a single run. `release-readiness-backlog.md` 3.1
  explicitly asks for closure visible "in tests/ under repeated runs". A2
  is the lane that was supposed to satisfy that language.

### Q4. Does the proof preserve `max_concurrent=1`, `ticketed_fifo`, and whole-request `GenerationGate` safety?

**Yes.**

- `tests/test_cache_cohort_to_child_exchange_handoff_harness.py` asserts
  `max_concurrent == 1` and `queue_discipline == "serial"` after the
  cohort lands, with `gate_total_served == 2` and
  `gate_total_queued == 2`.
- `tests/test_serving_pre_gate_admission_hook.py
  ::test_pre_gate_hook_exists_before_claim_without_reopening_post_claim_invariants`
  asserts the gate's final state preserves
  `max_concurrent == 1`, `queue_policy == "ticketed_fifo"`, and that
  `preserved_post_claim_invariants` lists
  `max_concurrent_1_after_gate_claim`,
  `ticketed_fifo_after_gate_claim`,
  `serial_safety_validated_only_after_gate_claim`.
- Stream branch still holds the gate until completion
  (`stream_session_holds_gate_until_completion`), which is the safe
  posture, not a weakening.

### Q5. Does current evidence satisfy `release-readiness-backlog.md` section 3.1?

**No.** Section 3.1 requires the conjunction of three things:

1. one closed non-exactness scheduler capability on the active runtime path
   - **partially satisfied**: the non-stream main path already shows
     observable aggregated dispatch via `RuntimeKernel.generate` →
     `GenerationGate.execute_async_cohort_with_admission` →
     `backend.generate_cohort`, with runtime-observable counters on both
     gate and backend status surfaces. Single-iteration concurrent proof
     exists. The stream-branch dispatch-level closure is still open per
     `phase45-request-aggregation-active-seam.md`.
2. closure visible in `tests/` under repeated runs
   - **not satisfied**: no repeated-iteration test exists. A2 was the lane
     for it and has not landed.
3. failing seam tests reach green or are honestly downgraded with a tracked
   reason
   - **satisfied for the named family**:
     `test_cache_pre_gate_admission_window_seam.py` is green (5/5).

Two of three requirements are met; one is missing. That is a
`progressed`, not `closed`, posture under Hard Rule 1 of the audit prompt
chain.

### Q6. If not, what is the smallest remaining blocker in floor language?

**Single blocker: repeated-run test instrumentation on the non-stream
runtime-kernel cohort path.**

In floor language: floor 3.1 cannot be marked closed until a
`tests/`-resident test runs the cohort handoff harness (or equivalent
runtime-kernel concurrent-generate path) across at least three iterations
and asserts that aggregated dispatch counters accumulate while
`max_concurrent`, queue discipline, and serial-safety invariants remain
preserved each iteration.

Stream-branch dispatch-level closure is **not** blocking floor 3.1 closure
under the backlog's literal language ("one closed non-exactness scheduler
capability"). It remains the active phase45 seam blocker and stays
preserved as secondary truth, but it is not the floor's only
honest-closure pathway.

## 6. Recommended Floor 3.1 Verdict

**`progressed`**, not `closed`, not `still_blocked`.

Reasoning chain:

- A1 closed the test-truth gate; that part of section 3.1 is now satisfied.
- B1 mapped existing non-exactness capability and identified the single
  remaining test-side gap.
- A2 is the lane that converts B1's identified gap into closure evidence,
  but A2 has not run yet.
- No new release-blocking surface has appeared.
- The floor has measurably less open work than at the start of round 1, so
  `still_blocked` would be inaccurate.
- The floor still has one named missing piece, so `closed` is dishonest.

## 7. Active-Path Truth Tracking

Two items in the worktree are not yet tracked under git:

- `docs/source-of-truth/release-floor-3-1-cache-scheduler-capability-audit.md`
  (B1's audit deliverable; untracked)
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-verdict-review-handoff.md`
  (this document; will be untracked at write time)

Coordinator action: stage these two files (and any A1 final-report file
that may be added later) before declaring the floor-3.1 round closed for
review. The runtime modules and tests touched by A1 are already staged.

## 8. Lane Constraints Confirmation

- This lane wrote no runtime code.
- This lane edited no test file.
- This lane edited no source-of-truth doc beyond producing this handoff.
- No other release floor was worked or claimed reduced.
- No release, parity, replacement, or production-grade claim was made.
- The recommended verdict (`progressed`) does not move section 5 of
  `release-readiness-backlog.md`; that ledger remains at `open`.

## 9. Coordinator Next Step (Recommended, Not Applied)

Authorize Executor A2 to execute against
`files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A2-repeated-dispatch-proof.md`.
A1 entry gate is now satisfied, so A2's hard entry condition holds.

After A2 returns, re-run B2 with A2's output included before any `closed`
recommendation is considered.
