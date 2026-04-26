# owlmlx Recovery Supervisor Contract

> Status: authoritative
> Updated: 2026-04-25
> Scope: runtime-only recovery barrier classification without a background
> supervisor loop

## 1. Purpose

This document freezes the narrow recovery layer behind single-host
orchestration:

**Given runtime-owned backend health, restart visibility, and abort-recovery
state, is a recovery barrier required, what request impact is safe to claim,
and which recovery semantics remain unknown?**

This is not a recovery daemon.
It is the contract that prevents upper layers from treating restart visibility
as full recovery closure.

## 2. Owned Contract

`owlmlx/recovery_supervisor_contract.py` owns:

- `build_recovery_supervisor_contract(...)`
- `recovery_supervisor_contract_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/recovery-supervisor-contract`

Contract:

- `surface = "owlmlx.recovery_supervisor_contract"`
- `version = "v1"`

Stable sections:

- `summary`
- `barrier`
- `substrate`
- `restart`
- `lifecycle`
- `request_impact`
- `policy_boundaries`
- `missing_signals`

## 3. Current Inputs

The contract consumes only runtime-owned truth:

- `AbortRecoveryTracker.snapshot()`
- `/v1/runtime/status` summary health
- restartable / restart-exhausted model visibility
- governance observations already exposed by the runtime

It does not read product-shell state or ops-side inference.

## 4. Current Recovery States

Current state vocabulary:

- `clean`
  - abort recovery state is clean and no restart exhaustion is visible
- `probing`
  - abort recovery state is probing; high-context work should defer until probe
    truth exists
- `contaminated`
  - abort recovery reports contamination or recovery required
- `restart_exhausted`
  - one or more models have exhausted runtime-owned restart attempts
- `backend_unhealthy`
  - backend health is false and generation must fail closed
- `unknown`
  - restart visibility exists but abort recovery truth is absent

## 5. Barrier Semantics

The contract may claim a hard recovery barrier only for:

- `backend_unhealthy`
- `restart_exhausted`
- `contaminated`

It may claim a high-context-only barrier for:

- `probing`

It may claim no current barrier only for:

- `clean`

## 6. Boundary With Other Contracts

This contract does not replace:

- `scheduler_admission_contract`
- `model_residency_policy`
- `memory_pressure_contract`
- `orchestration_status`

It feeds `orchestration_status` as the recovery child surface.

`scheduler_admission_contract` may consume this contract's hard recovery
barrier to reject generation admission before whole-request gate claim.
It also consumes `request_context_length_truth` so high-context-only probing
barriers defer only requests that are known `high_context`.
Known `non_high_context` requests and `unknown` context requests are not
globally rejected or deferred solely because probing exists.

`memory_pressure_contract` may expose restart visibility as context, but only
this contract may classify recovery barrier impact.

## 7. What This Does Not Claim

It does not claim:

- automatic recovery supervisor loop exists
- failed reclaim or failed unload barrier events are fully modeled
- worker pollution is detected beyond abort-recovery state
- pressure-ranked eviction exists
- restart visibility equals recovery closure

It only claims:

- `owlmlx` now owns the current recovery barrier classification
- hard recovery barriers fail closed
- high-context probing state is visible without being inflated into full
  recovery closure
