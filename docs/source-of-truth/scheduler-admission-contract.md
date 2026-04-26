# owlmlx Scheduler Admission Contract

> Status: authoritative
> Updated: 2026-04-25
> Scope: runtime-only automatic admission decisions before whole-request gate claim

## 1. Purpose

This document freezes the first runtime-owned scheduler contract for the active
single-host path:

**Given one incoming request class and the current runtime snapshot, should
`owlmlx` automatically accept it, defer it, reject it, or keep the result
unknown before execution claim?**

This is not a full local scheduler.
It is the narrow admission layer that sits in front of the already-validated
`GenerationGate` floor.

## 2. Owned Contract

`owlmlx/scheduler_admission_contract.py` now owns:

- `build_scheduler_admission_contract(...)`
- `scheduler_admission_contract_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/scheduler-admission-contract`

Contract:

- `surface = "owlmlx.scheduler_admission_contract"`
- `version = "v1"`

Stable sections:

- `summary`
- `reason`
- `request_class_support`
- `boundary`
- `signals`
- `preserved_invariants`
- `missing_signals`

## 3. Current Honest Scope

The current contract intentionally stays narrow.

It builds only from already-owned runtime truth:

- `GenerationGate` state, queue policy, and waiter visibility
- bounded `pre_gate_admission`
- resident-model and active-model truth
- budget truth
- backend health and restart visibility
- `recovery_supervisor_contract` hard-barrier truth
- `request_context_length_truth` for high-context admission support

It does not turn those signals into stronger scheduler/residency/pressure
claims than the runtime currently owns.

## 4. Admission Decision Semantics

Current automatic decision vocabulary is:

- `accepted`
  - only when the backend is healthy
  - the target model is already resident
  - the validated serial `GenerationGate` floor is visible
  - the bounded pre-claim admission hook is visible
  - there are no visible gate waiters or already-staged pre-claim cohorts
- `deferred`
  - when the gate is already active
  - when visible waiters already occupy the serial post-claim boundary
  - when a bounded pre-claim cohort is already staged
  - when recovery is `probing` and the request is known `high_context`
- `rejected`
  - when the backend is unhealthy
  - when `recovery_supervisor_contract` reports a hard recovery barrier
  - when no active or explicit target model can be resolved
  - when the target model is not resident on the current runtime-owned path
- `unknown`
  - when the request class is unknown
  - when the request class is generic `maintenance`
  - when the validated gate floor or bounded pre-claim hook is not visible
    strongly enough

## 5. Request Class Support

Current request-class posture is:

- `interactive`
  - `classification_status = supported`
  - automatic decisions may be `accepted`, `deferred`, or `rejected`
- `stream`
  - `classification_status = supported`
  - automatic decisions may be `accepted`, `deferred`, or `rejected`
  - this still does not claim stream-hold depth is solved
- `benchmark`
  - `classification_status = supported`
  - automatic decisions may be `accepted`, `deferred`, or `rejected`
- `maintenance`
  - `classification_status = partial`
  - generic maintenance traffic stays `unknown` until narrower action semantics
    are frozen
- `unknown`
  - retained as an explicit fallback

## 6. Boundary With `GenerationGate`

The admission contract stops at:

- `before_whole_request_gate_claim`

`GenerationGate` remains:

- the validated post-claim serial safety boundary
- `max_concurrent = 1`
- `ticketed_fifo`

The admission contract must never imply:

- hidden bypass of whole-request gate claim
- post-claim reordering
- post-claim parallel generation
- continuous batching
- multi-worker scheduler depth

## 7. Missing Signals That Still Matter

Even with the new contract, several signal families remain weaker than full
scheduler closure:

- `memory_pressure`
  - budget truth exists, but direct pressure/reclaim admission truth does not
- `stream_hold`
  - stream work shares the gate boundary, but live hold depth is not directly
    visible
- `recovery`
  - hard recovery barriers now reject admission
- `request_context_length`
  - explicit token truth can classify a request as `high_context` or
    `non_high_context`
  - absent token truth remains `unknown`
- `maintenance`
  - generic maintenance action subtypes are not yet frozen
- `model_residency`
  - non-resident targets currently reject because admission still does not own a
    defer-to-load or on-demand residency policy

## 8. What This Does Not Claim

It does not claim:

- a full single-host scheduler already exists
- continuous batching exists
- multi-worker scheduling is safe
- admission policy alone solves residency, pressure, or recovery
- high-context recovery probing is a rejection state
- context-length support is full tokenizer parity

It only claims:

- `owlmlx` now owns one runtime admission contract
- automatic pre-claim decisions are no longer left to shell-side guessing
- hard recovery barriers now fail closed before whole-request gate claim
- high-context-only recovery probing now defers only known high-context requests
- weak signals still remain weak instead of being narrated as scheduler closure
