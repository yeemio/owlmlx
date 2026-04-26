# owlmlx Execution Prompt 3.3A: Non-Resident Admission Policy

> Date: 2026-04-25
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor A
> Active release floor: `3.3 Model Residency Non-Resident Path`
> Role: implementation, tests, docs, and runtime transport

## 1. Objective

Close or materially progress release floor `3.3` by introducing the smallest
honest runtime-owned decision surface for non-resident model targets.

The required question is:

**Given a non-resident target model plus current budget, pressure, residency,
lineage, and recovery truth, should `owlmlx` admit-and-load, defer, reject, or
return unknown?**

This is a runtime-owned orchestration contract. It is not a product UI change,
not an ops-side interpretation, and not a release claim.

## 2. Required Read Order

Read these before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/model-residency-policy.md`
5. `docs/source-of-truth/memory-pressure-contract.md`
6. `docs/source-of-truth/scheduler-admission-contract.md`
7. `docs/source-of-truth/recovery-supervisor-contract.md`
8. `docs/source-of-truth/request-context-length-truth.md`
9. `docs/source-of-truth/orchestration-status-surface.md`
10. `docs/source-of-truth/runtime-status-schema.md`
11. `owlmlx/model_residency_policy.py`
12. `owlmlx/memory_pressure_contract.py`
13. `owlmlx/scheduler_admission_contract.py`
14. `owlmlx/recovery_supervisor_contract.py`
15. `owlmlx/orchestration_status.py`
16. `owlmlx/runtime/kernel.py`
17. `owlmlx/runtime/server.py`
18. Existing tests for the files above

## 3. Implementation Target

Introduce one narrow contract. Preferred name:

- module: `owlmlx/nonresident_model_admission_policy.py`
- surface: `owlmlx.nonresident_model_admission_policy`
- transport: `GET /v1/runtime/nonresident-model-admission-policy`
- docs: `docs/source-of-truth/nonresident-model-admission-policy.md`
- tests: `tests/test_nonresident_model_admission_policy.py`

If you find a better name while reading the code, keep the meaning identical
and explain the rename in your handoff.

## 4. Stable Decision Vocabulary

The policy must return exactly one of:

- `admit_and_load`
- `defer`
- `reject`
- `unknown`

Use these semantics:

- `admit_and_load`
  - only when the target is known non-resident
  - the model is known loadable from runtime-owned inventory or lineage truth
  - memory pressure is not `over_budget`
  - no hard recovery barrier is active
  - required load preconditions are known
- `defer`
  - when a named precondition must resolve before a safe load decision
  - examples: gate currently active, recovery is `probing` for high-context
    request, pressure is `near_budget` and no pressure-action policy exists
- `reject`
  - when the target cannot be resolved
  - when the model is not known loadable by runtime-owned truth
  - when memory pressure is `over_budget` and no eviction execution policy is
    closed
  - when recovery supervisor reports a hard barrier
- `unknown`
  - when the required input truth is absent or too weak
  - do not use `unknown` to hide a deterministic reject

Each decision must include:

- `reason`
- `target_model`
- `required_preconditions`
- `blocking_signals`
- `preserved_invariants`
- `missing_signals`

## 5. Required Round Trip

Release floor `3.3` requires the decision to round-trip through these surfaces:

- residency:
  - resident / non-resident / pinned / TTL / evictable status must come from
    `model_residency_policy`
- pressure:
  - pressure state must come from `memory_pressure_contract`
- recovery:
  - hard recovery barriers must come from `recovery_supervisor_contract`
- admission:
  - `scheduler_admission_contract` may consume the new policy only as a
    pre-claim decision input, never as a post-claim gate bypass

If lineage truth is missing, freeze that as a specific blocker instead of
inventing loadability.

## 6. Hard Rules

1. Do not implement floor `3.2` pressure-ranked eviction in this lane.
2. Do not implement a broad automatic model loader unless the existing runtime
   already owns every required safety signal.
3. Do not weaken `GenerationGate` serial invariants:
   `max_concurrent = 1`, `ticketed_fifo`, and no post-claim bypass.
4. Do not claim continuous batching, multi-worker scheduling, parity,
   replacement, release-ready, or production-grade.
5. Do not move work into `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent`.
6. Preserve existing staged/dirty changes you did not create.
7. If the honest result is still blocked, land the blocker as source-of-truth
   and tests where possible; do not narrate future policy as current runtime
   behavior.

## 7. Minimum Acceptance Criteria

A successful A-lane result must include:

- a runtime-owned contract builder and dictionary serializer
- a stable HTTP endpoint returning the contract payload
- docs in `docs/source-of-truth/`
- runtime status schema update if the new payload shape is stable enough to be
  consumed by other layers
- tests for:
  - non-resident known-loadable target under safe budget
  - non-resident unknown target
  - over-budget rejection or defer with explicit missing eviction policy
  - recovery hard barrier fail-closed
  - scheduler admission integration or explicit documented reason why
    integration must wait
- an honest floor verdict:
  - `closed`
  - `progressed`
  - `still_blocked`

Use `closed` only if all section 3.3 requirements in
`release-readiness-backlog.md` are met.

## 8. Suggested Verification

Run the tightest relevant suite first, then broaden:

```bash
pytest -q tests/test_nonresident_model_admission_policy.py
pytest -q tests/test_model_residency_policy.py tests/test_memory_pressure_contract.py tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py
pytest -q tests/test_orchestration_status.py tests/test_runtime_server.py -k "nonresident or residency or pressure or recovery or scheduler_admission or orchestration_status"
python3 -m py_compile owlmlx/nonresident_model_admission_policy.py owlmlx/runtime/server.py
git diff --check
```

If you add or rename files, adjust the commands honestly.

## 9. Output Handoff

Write a handoff file:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy-handoff.md`

The handoff must state:

- outcome label
- floor `3.3` verdict: `closed`, `progressed`, or `still_blocked`
- changed files
- exact commands and results
- endpoint path and sample decisive fields
- whether scheduler admission now consumes the policy
- whether lineage/loadability truth is complete or still a blocker
- explicit deferred scope, especially anything that belongs to floor `3.2`

## 10. Allowed Outcome Labels

Use one:

- `owlmlx_release_floor_3_3A_nonresident_admission_policy_closed`
- `owlmlx_release_floor_3_3A_nonresident_admission_policy_progressed`
- `owlmlx_release_floor_3_3A_nonresident_admission_policy_still_blocked`

`closed` means floor `3.3` itself is closed, not merely that a module exists.

