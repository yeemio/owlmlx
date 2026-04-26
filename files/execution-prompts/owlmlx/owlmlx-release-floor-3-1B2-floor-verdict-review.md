# owlmlx Execution Prompt B2: Release Floor 3.1 Verdict Review

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor B2
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`
> Entry gate: start after Executor A1 and Executor B1 reports exist; include
> Executor A2 output if it has landed.

## Mission

Merge-review the A/B evidence for release floor `3.1` and produce the floor
verdict recommendation:

- `closed`
- `progressed`
- `still_blocked`

This lane is review and coordination evidence.
It must not write runtime implementation.

## Coordination Truth

Read these first:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A-pre-gate-test-truth-restoration.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B-cache-scheduler-capability-audit.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A2-repeated-dispatch-proof.md`
- Executor A1 final report
- Executor B1 final report
- Executor A2 final report, if available
- changed files from A1 / A2
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`

## Owned Write Scope

Preferred mode:

- read-only review with final report

Optional write scope if the coordinator asks for a tracked review artifact:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-verdict-review-handoff.md`

Do not edit:

- runtime modules
- tests
- release-readiness backlog closure ledger
- active seam docs
- comparative evidence / floor 3.5 files

If the verdict requires doc updates, list exact proposed edits; do not apply
them unless explicitly assigned.

## Hard Rules

1. Do not mark floor `3.1` closed unless every release-floor requirement is
   met.
2. Reject exactness-only proof as floor closure.
3. Require repeated-run or runtime-path evidence for non-exactness scheduler
   behavior.
4. Reject release/parity/replacement wording.
5. Do not bless a test-only fixture if it does not correspond to the active
   runtime path.
6. Keep `unknown` when evidence is insufficient.
7. Do not work on any other release floor.

## Review Questions

Answer these explicitly:

1. Is `tests/test_cache_pre_gate_admission_window_seam.py` green or honestly
   downgraded with a tracked reason?
2. Did A2 introduce or prove a non-exactness scheduler capability on the active
   runtime path?
3. Is the proof repeated-run or runtime-like, not just constructor/exactness
   proof?
4. Does the proof preserve `max_concurrent=1`, `ticketed_fifo`, and
   whole-request `GenerationGate` safety?
5. Does current evidence satisfy `release-readiness-backlog.md` section 3.1?
6. If not, what is the smallest remaining blocker in floor language?

## Required Commands

Run at minimum:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
pytest -q tests/test_cache_request_aggregation_active_seam.py
pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q
pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q
git diff --check
```

If A2 added a narrower test, run that test explicitly.

## Expected Outcome Labels

Return exactly one:

- `owlmlx_release_floor_3_1B2_verdict_review_closed_recommended`
- `owlmlx_release_floor_3_1B2_verdict_review_progressed_recommended`
- `owlmlx_release_floor_3_1B2_verdict_review_still_blocked_recommended`
- `owlmlx_release_floor_3_1B2_verdict_review_blocked_missing_A_outputs`

Use `closed_recommended` only if section 3.1 is fully satisfied.

## Final Report

Return:

- outcome label
- reports/files reviewed
- changed files, if any
- exact commands and results
- answers to all six review questions
- recommended floor `3.1` verdict
- exact remaining blocker if not closed
- whether any active-path truth remains untracked
- confirmation that no other release floor was worked
- confirmation that no release/parity/replacement claim was made
