# owlmlx Execution Prompt B: Release Floor 3.1 Cache Scheduler Capability Audit

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor B
> Active release floor: `3.1 Cache Scheduler Closure Beyond Exactness`

## Mission

Independently audit whether `owlmlx` currently has a non-exactness cache
scheduler capability on the active runtime path, and identify the smallest
runtime/test gap if it does not.

This lane is evidence mapping, not red-test repair.
Executor A owns the red pre-gate seam test family.

## Coordination Truth

Read these first:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`
- `docs/source-of-truth/phase45-dominant-gap-reselection.md`
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`
- `owlmlx/cache_request_aggregation_active_seam.py`
- `owlmlx/runtime/kernel.py`
- `owlmlx/serving.py`
- `tests/test_cache_request_aggregation_active_seam.py`
- `tests/test_runtime_kernel.py`
- `tests/test_serving_pre_gate_admission_hook.py`

Release floor `3.1` requires more than exactness:

- one closed non-exactness scheduler capability on the active runtime path
- repeated-run or runtime-path proof
- observable aggregated dispatch or equivalent dispatch-level scheduler closure

## Owned Write Scope

Preferred mode:

- read-only audit with final report

Optional write scope if you need to preserve machine-readable audit evidence:

- `docs/source-of-truth/release-floor-3-1-cache-scheduler-capability-audit.md`

Do not edit:

- `tests/test_cache_pre_gate_admission_window_seam.py`
- `owlmlx/cache_pre_gate_admission_window_seam.py`
- `owlmlx/cache_request_aggregation_active_seam.py`
- `tests/test_cache_request_aggregation_active_seam.py`
- `owlmlx/runtime/kernel.py`
- `owlmlx/serving.py`

If you discover a minimal proof test that should be added, describe it
precisely in the final report instead of patching A-owned or runtime files.
Coordinator will assign the implementation after A's red gate is resolved.

## Hard Rules

1. Do not mark release floor `3.1` closed by audit alone.
2. Do not claim release readiness, parity, replacement, or production grade.
3. Do not treat marker/discriminant exactness as release-floor closure.
4. Do not work on failed unload/reclaim, memory pressure, non-resident
   residency, public surface, or benchmark floors.
5. Do not modify A-owned red-test files.
6. Do not add broad scheduler implementation.
7. Keep `unknown` if runtime evidence is insufficient.

## Audit Questions

Answer these from code, tests, and runnable evidence:

1. Does a bounded request-aggregation cohort form before whole-request gate
   claim on the active runtime path?
2. Does any test or live path prove one child exchange carries multiple
   requests in a repeated or runtime-like run?
3. Is aggregated dispatch observable as behavior, not just as a frozen seam
   record?
4. Does stream hold still prevent dispatch-level closure?
5. What is the smallest missing runtime signal or test needed for floor `3.1`
   to progress after Executor A restores the red gate?

## Required Commands

Run at minimum:

```bash
pytest -q tests/test_cache_request_aggregation_active_seam.py
pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q
pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q
git diff --check
```

If a command fails because Executor A's red-gate work is not yet present, report
that precisely and continue with read-only audit where possible.

## Expected Outcome Labels

Return exactly one:

- `owlmlx_release_floor_3_1B_scheduler_capability_audit_completed`
- `owlmlx_release_floor_3_1B_scheduler_capability_audit_blocked`

## Final Report

Return:

- outcome label
- files inspected
- changed files, if any
- exact commands and results
- direct answer to all five audit questions
- whether current evidence satisfies release floor `3.1`
- if not, the smallest missing runtime/test capability
- explicit statement that no other release floor was worked
- explicit statement that no release/parity/replacement claim was made
