# owlmlx Execution Prompt: Scheduler Admission Recovery Barrier Refresh

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Goal: make scheduler admission consume the new recovery supervisor contract.

## Coordination Truth

`owlmlx.recovery_supervisor_contract` now owns recovery barrier classification
for backend health, restart exhaustion, and abort-recovery substrate state.

The next local closure is to make `owlmlx.scheduler_admission_contract` consume
that hard barrier instead of allowing admission to accept requests while the
recovery layer says all generation must fail closed.

## Objective

Refresh `owlmlx.scheduler_admission_contract` so:

- hard recovery barriers reject generation admission
- high-context-only probing barriers are surfaced as recovery signals but do not
  reject ordinary requests without context-length/request-subtype truth
- existing `GenerationGate` invariants remain unchanged

Allowed outcome labels:

- `owlmlx_scheduler_admission_recovery_barrier_refreshed`
- `owlmlx_scheduler_admission_recovery_barrier_still_blocked`

## Hard Rules

1. Do not implement recovery actions.
2. Do not create a background supervisor loop.
3. Do not add pressure-ranked eviction or reclaim orchestration.
4. Do not change `max_concurrent=1`, `ticketed_fifo`, or whole-request gate
   claim semantics.
5. Do not treat `probing` as a global rejection unless context-length truth is
   also runtime-owned for the request.

## Required Changes

- Update `owlmlx/scheduler_admission_contract.py`.
- Update `GET /v1/runtime/scheduler-admission-contract` to pass the
  `AbortRecoveryTracker.snapshot()` truth.
- Update source-of-truth docs.
- Add tests for:
  - hard recovery barrier rejects admission
  - probing high-context barrier is visible but does not globally reject
  - route sees contaminated abort recovery state and rejects admission

## Required Checks

- `pytest -q tests/test_scheduler_admission_contract.py`
- `pytest -q tests/test_recovery_supervisor_contract.py tests/test_orchestration_status.py`
- `pytest -q tests/test_runtime_server.py -k "scheduler_admission_contract or recovery_supervisor or orchestration_status"`

## Final Report

Return:

- outcome label
- changed files
- exact checks
- what admission now owns
- what remains unknown
