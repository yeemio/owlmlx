# owlmlx Execution Prompt C-B: Release Floor 3.1 Ledger Truth Decision

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor C-B
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`
> Role: truth sync and ledger decision after C-A verification

## Mission

Use C-A verification evidence to decide and record the honest release-floor
`3.1` state.

This lane may update truth docs.
It must not edit runtime code or tests.

## Entry Gate

Do not start unless this file exists:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-A-verification-handoff.md`

If it is missing, stop with:

- `owlmlx_release_floor_3_1C_B_blocked_missing_C_A_handoff`

## Required Read Order

Read these before editing:

1. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-A-verification-handoff.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/release-floor-3-1-cache-scheduler-capability-audit.md`
5. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-verdict-review-handoff.md`
6. `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
7. `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
8. `docs/source-of-truth/replacement-grade-stability-gaps.md`
9. `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`

## Owned Write Scope

C-B may edit:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-B-ledger-truth-handoff.md`

Do not edit:

- runtime modules
- tests
- comparative evidence / floor `3.5` files
- memory-pressure, residency, recovery, public-surface, or external evidence
  floors

## Decision Rules

Mark floor `3.1` closed only if C-A proves all of these:

- `tests/test_cache_pre_gate_admission_window_seam.py` is green
- a non-exactness scheduler capability exists on the active runtime path
- repeated-load test evidence exists in `tests/`
- proof is behavioral/runtime-observable, not only a seam record
- serial safety is preserved:
  - `max_concurrent = 1`
  - `ticketed_fifo`
  - whole-request `GenerationGate`
  - `queue_discipline = "serial"`

If any item is missing, do not mark closed.
Record `progressed` or keep `open` with exact blocker wording.

Even if floor `3.1` closes:

- do not claim `owlmlx` is release-ready
- do not claim parity, replacement, production-grade, or reference-grade
- select the next active floor as `3.3 Model Residency Non-Resident Path`
  unless a blocker forces another `3.1` round

## Required Commands

Run at minimum after edits:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
pytest -q tests/test_runtime_kernel.py -k "repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load or concurrent_generations_handoff_cohort_into_aggregated_child_exchange"
pytest -q tests/test_cache_request_aggregation_active_seam.py
git diff --check
```

If C-A already ran broader suites successfully and no runtime/tests changed,
you may cite C-A for the broader suite evidence, but still run the three checks
above.

## Expected Outcome Labels

Return exactly one:

- `owlmlx_release_floor_3_1C_B_ledger_closed`
- `owlmlx_release_floor_3_1C_B_ledger_progressed`
- `owlmlx_release_floor_3_1C_B_ledger_still_blocked`
- `owlmlx_release_floor_3_1C_B_blocked_missing_C_A_handoff`

Use `ledger_closed` only when floor `3.1` itself closes.

## Final Handoff File

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-B-ledger-truth-handoff.md`

Include:

- outcome label
- changed files
- exact commands and results
- floor `3.1` final verdict
- exact next active floor if closed
- exact blocker if not closed
- confirmation that no other floor was marked closed
- confirmation that no release/parity/replacement claim was made
- whether all active-path truth and handoff files are tracked

## Final Chat Report

Return the handoff path, outcome label, and next active floor or blocker.
