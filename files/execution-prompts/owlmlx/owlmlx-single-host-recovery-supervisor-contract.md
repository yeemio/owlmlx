# owlmlx Execution Prompt: Single-Host Recovery Supervisor Contract

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Goal: introduce the narrow runtime-owned recovery supervisor contract after
> orchestration status composition refresh.

## Coordination Truth

The previous orchestration loop has landed:

- `owlmlx.scheduler_admission_contract`
- `owlmlx.model_residency_policy`
- `owlmlx.memory_pressure_contract`
- `owlmlx.orchestration_status`

`orchestration_status` now composes the three child surfaces above and keeps
recovery as `partial` because restart visibility exists but recovery-barrier
semantics are not yet runtime-owned.

The next dominant gap is therefore:

- `recovery_supervisor_contract`

This is not a full recovery daemon.
This is not automatic pressure eviction.
This is not continuous batching.

## Objective

Introduce one narrow runtime-owned surface that answers:

**Given current runtime restart visibility, backend health, and abort-recovery
state, is a recovery barrier required, what admission impact is safe to claim,
and which recovery signals remain unknown?**

Allowed outcome labels:

- `owlmlx_recovery_supervisor_contract_introduced`
- `owlmlx_recovery_supervisor_contract_still_blocked`

## Hard Rules

1. Work only inside `/Users/yeemio/AI/gitrep/owlmlx`.
2. Do not implement a background recovery supervisor loop.
3. Do not add automatic retry, auto unload, pressure-ranked eviction, or reclaim
   orchestration.
4. Do not change `GenerationGate` concurrency invariants:
   - `max_concurrent = 1`
   - `ticketed_fifo`
   - whole-request gate claim remains the validated execution boundary.
5. Do not promote restart visibility into full recovery closure.
6. Keep weak signals as `unknown` or `insufficient_signal`.
7. Preserve the boundary between:
   - abort recovery substrate state machine
   - restart action surface
   - recovery supervisor barrier contract.

## Required Implementation

Add:

- `owlmlx/recovery_supervisor_contract.py`

Expose:

- `GET /v1/runtime/recovery-supervisor-contract`

The contract should include stable sections for:

- `summary`
- `barrier`
- `substrate`
- `restart`
- `lifecycle`
- `request_impact`
- `policy_boundaries`
- `missing_signals`

The surface should consume only runtime-owned truth:

- `/v1/runtime/status` style payload
- `AbortRecoveryTracker.snapshot()`
- restart visibility
- backend health
- governance / lifecycle observations where already present

It may classify:

- clean/no barrier
- probing/high-context defer
- contaminated/recovery required
- restart exhausted/operator recovery required
- backend unhealthy/runtime unavailable
- unknown/insufficient signal

It must not claim:

- failed reclaim closure
- worker-pollution detection beyond abort recovery state
- pressure eviction policy
- automatic recovery loop
- full replacement-grade recovery parity

## Required Orchestration Refresh

After introducing the contract, update `owlmlx.orchestration_status` so the
recovery layer consumes `owlmlx.recovery_supervisor_contract` instead of only
counting restart fields directly.

The bottleneck summary may report `recovery` only when the recovery supervisor
contract reports a hard recovery barrier such as:

- substrate contaminated
- restart exhausted
- backend unavailable

Otherwise recovery stays `partial`.

## Required Docs

Update or add source-of-truth docs:

- `docs/source-of-truth/recovery-supervisor-contract.md`
- `docs/source-of-truth/orchestration-status-surface.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/runtime-capability-matrix.md`

## Required Tests

Add or update tests for:

- clean runtime produces no recovery barrier
- abort recovery `probing` defers high-context work but does not claim full
  global recovery closure
- abort recovery `contaminated` requires recovery barrier
- restart exhausted models require recovery barrier
- runtime route exposes the contract
- orchestration status consumes recovery supervisor truth

Run at least:

- `pytest -q tests/test_recovery_supervisor_contract.py`
- `pytest -q tests/test_orchestration_status.py`
- `pytest -q tests/test_runtime_server.py -k "recovery_supervisor or orchestration_status or runtime_status"`

## Final Report

Return:

- selected outcome label
- files changed
- exact checks run
- which recovery decisions are now owned
- which recovery decisions remain `unknown` / `insufficient_signal`
- next dominant gap if the goal is not complete
