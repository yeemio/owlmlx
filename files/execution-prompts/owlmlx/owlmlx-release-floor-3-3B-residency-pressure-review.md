# owlmlx Execution Prompt 3.3B: Residency / Pressure Review

> Date: 2026-04-25
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor B
> Active release floor: `3.3 Model Residency Non-Resident Path`
> Role: scoped review, source-of-truth audit, and floor-verdict guard

## 1. Objective

Review floor `3.3` independently so the A lane cannot accidentally mark the
non-resident model path closed on weak evidence.

This lane is intentionally defensive:

**Verify whether `owlmlx` now owns deterministic non-resident
`admit_and_load / defer / reject / unknown` semantics that round-trip through
residency, pressure, lineage, and recovery truth.**

If A has not returned yet, produce the audit map and exact review checklist.
If A has returned, review A's changed files and verification evidence.

## 2. Required Read Order

Read these before reviewing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/model-residency-policy.md`
5. `docs/source-of-truth/memory-pressure-contract.md`
6. `docs/source-of-truth/scheduler-admission-contract.md`
7. `docs/source-of-truth/recovery-supervisor-contract.md`
8. `docs/source-of-truth/orchestration-status-surface.md`
9. `docs/source-of-truth/runtime-status-schema.md`
10. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy.md`
11. If present:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy-handoff.md`
12. Any files changed by A

## 3. Review Questions

Answer these precisely:

1. Does the new or proposed contract have a stable runtime-owned surface?
2. Are the decision values exactly:
   `admit_and_load`, `defer`, `reject`, `unknown`?
3. Does each decision include a frozen reason and named missing/precondition
   signals?
4. Does the contract use `model_residency_policy` for residency truth rather
   than re-deriving it ad hoc?
5. Does the contract use `memory_pressure_contract` for pressure truth without
   pretending floor `3.2` eviction is closed?
6. Does the contract honor `recovery_supervisor_contract` hard barriers?
7. Is model loadability / lineage truth real, or is it inferred from path names,
   config guesses, or docs-only assumptions?
8. Does `scheduler_admission_contract` integration preserve the serial gate and
   pre-claim boundary?
9. Do tests cover all decisive branches, including blocked / unknown cases?
10. Is the release-floor ledger updated only if the floor actually closes?

## 4. Blocking Findings

Return `needs_fix` if any of these are true:

- `admit_and_load` can occur without runtime-owned loadability truth
- `over_budget` silently becomes admit without a closed eviction policy
- recovery hard barriers do not fail closed
- scheduler admission bypasses or weakens `GenerationGate`
- missing lineage truth is hidden behind `unknown` when it should be a named
  blocker
- docs claim release, parity, replacement, or production readiness
- floor `3.3` is marked closed without tests or live/runtime checks
- A touches floor `3.2` eviction execution and presents it as part of 3.3

## 5. Optional Audit Doc

If A has not returned yet, or if the review uncovers a durable truth gap, you
may write:

- `docs/source-of-truth/release-floor-3-3-nonresident-path-review.md`

If you create this source-of-truth document, also add it to
`docs/source-of-truth/master-outline.md`.

Do not edit runtime code in B lane unless explicitly authorized later.

## 6. Verification Commands

At minimum, run the focused tests A reports. If A has not returned, run current
baseline checks that establish the starting truth:

```bash
pytest -q tests/test_model_residency_policy.py tests/test_memory_pressure_contract.py tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py
pytest -q tests/test_orchestration_status.py tests/test_runtime_server.py -k "residency or pressure or recovery or scheduler_admission or orchestration_status"
git diff --check
```

If A adds `tests/test_nonresident_model_admission_policy.py`, include it in the
focused suite.

## 7. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B-residency-pressure-review-handoff.md`

The handoff must include:

- review verdict: `pass`, `needs_fix`, or `blocked_waiting_for_A`
- floor `3.3` recommendation: `closed`, `progressed`, or `still_blocked`
- blocking findings first, with file/line references where possible
- non-blocking notes
- exact commands and results
- explicit statement whether any source-of-truth docs were created or indexed
- exact next action for coordinator

## 8. Allowed Outcome Labels

Use one:

- `owlmlx_release_floor_3_3B_review_pass`
- `owlmlx_release_floor_3_3B_review_needs_fix`
- `owlmlx_release_floor_3_3B_blocked_waiting_for_A`

Use `pass` only if A's implementation and evidence are present and reviewable.
If A has not returned, use `blocked_waiting_for_A` after producing the review
checklist/audit map.

