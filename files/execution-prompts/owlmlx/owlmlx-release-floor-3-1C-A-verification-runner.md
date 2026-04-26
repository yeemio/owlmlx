# owlmlx Execution Prompt C-A: Release Floor 3.1 Verification Runner

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor C-A
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`
> Role: command verification and evidence handoff only

## Mission

Run the closeout verification for release floor `3.1` and produce a precise
evidence handoff for C-B.

Do not update release ledgers.
Do not edit runtime code or tests.

## Coordination Truth

Read these before running commands:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-closeout-review-and-ledger-decision.md`
- `docs/source-of-truth/release-floor-3-1-cache-scheduler-capability-audit.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-verdict-review-handoff.md`
- `tests/test_runtime_kernel.py`
- `tests/test_cache_pre_gate_admission_window_seam.py`
- `tests/test_serving_pre_gate_admission_hook.py`
- `tests/test_cache_request_aggregation_active_seam.py`

## Owned Write Scope

Write only:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-A-verification-handoff.md`

Do not edit:

- runtime modules
- tests
- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- any floor other than `3.1`

## Verification Questions

Answer these from command output and direct file inspection:

1. Is `tests/test_cache_pre_gate_admission_window_seam.py` green?
2. Does `tests/test_runtime_kernel.py` contain a repeated-load proof named
   `test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load`?
3. Does that test assert repeated aggregated dispatch counters, not just one
   cohort?
4. Does it preserve:
   - `max_concurrent = 1`
   - `queue_discipline = "serial"`
   - `ticketed_fifo` / whole-request `GenerationGate` invariants
5. Do the broader adjacent suites pass?
6. Is `git diff --check` clean?

## Required Commands

Run exactly these unless one fails, then still continue with the remaining safe
read-only checks:

```bash
pytest -q tests/test_cache_pre_gate_admission_window_seam.py
pytest -q tests/test_runtime_kernel.py -k "repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load or concurrent_generations_handoff_cohort_into_aggregated_child_exchange"
pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q
pytest -q tests/test_cache_request_aggregation_active_seam.py
pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q
git diff --check
```

## Expected Outcome Labels

Return exactly one:

- `owlmlx_release_floor_3_1C_A_verification_passed`
- `owlmlx_release_floor_3_1C_A_verification_failed`
- `owlmlx_release_floor_3_1C_A_verification_blocked`

## Final Handoff File

Write a handoff file with:

- outcome label
- exact commands and results
- answers to all six verification questions
- whether C-B may proceed to ledger/truth decision
- if not, the exact failed command or missing evidence
- confirmation that no runtime code, tests, or ledger docs were edited

## Final Chat Report

Return the handoff path and the outcome label only after the file is written.
