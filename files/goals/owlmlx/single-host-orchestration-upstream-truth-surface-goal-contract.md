# owlmlx Goal Contract: Single-Host Orchestration Upstream Truth Surface

> Status: active goal contract
> Updated: 2026-04-23

## Goal ID

`owlmlx-single-host-orchestration-upstream-truth-surface`

## Title

Introduce one runtime-owned orchestration truth surface that `ops` can consume
without inventing `owlmlx` scheduler or bottleneck semantics.

## Success Definition

This goal succeeds only when `owlmlx` owns one narrow orchestration surface
with all of the following:

1. one stable authoritative contract for orchestration-layer assessment
2. runtime-owned fields that let upper layers consume:
   - current bottleneck-layer verdict when evidence is sufficient
   - per-layer assessment for:
     - `admission`
     - `generation_gate`
     - `stream_hold`
     - `model_residency`
     - `memory_pressure`
     - `recovery`
     - `unknown`
3. honest `unknown` / `insufficient_signal` handling for layers that cannot yet
   be classified
4. runnable code plus a transport surface or operator entry
5. tests and source-of-truth updates that freeze the contract and its limits

## Blocked Definition

This goal is blocked only if:

- current runtime-owned signal is too thin to define even a minimal honest
  orchestration assessment surface, and the exact missing signal family is
  frozen clearly, or
- the next step requires a product/control-plane choice that `owlmlx` cannot
  resolve from runtime truth alone

## Hard Rules

1. Work only inside `/Users/yeemio/AI/gitrep/owlmlx`.
2. `runtime truth ownership > ops-side inference`.
3. Do not widen this branch into a full local scheduler or general control
   plane.
4. Do not reopen the current Phase 45 cache seam as if this branch were its
   direct continuation.
5. Do not rewrite `/v1/runtime/status` stable sections to smuggle in a new
   contract.
6. Do not turn `memory_budget`, `loaded_model_count`, or restart visibility
   into fake `memory_pressure` or `recovery` bottleneck verdicts.
7. Use `unknown` or `insufficient_signal` when runtime-owned evidence is not
   strong enough.

## Out Of Scope

- `owlops` implementation details or service-layer UX
- cluster scheduling, multi-node placement, or cloud orchestration
- claiming replacement-grade scheduler parity
- broad memory-pressure or recovery-policy closure beyond what this narrow
  surface can honestly express
- reopening governance, heavy-weight, or customer-readiness branches

## Current Truth

- `single-host-orchestration-architecture.md` already freezes
  `orchestration_status_surface` as one of the immediate runtime-owned
  contracts that should exist next.
- `owlmlx` already owns runtime truth for:
  - `GenerationGate`
  - `ticketed_fifo`
  - bounded pre-gate admission / cohort window
  - inventory / active-default selection
  - pinning / TTL / eviction-history governance
  - budget and restart visibility
- `owlmlx` does not yet own a dedicated orchestration bottleneck-assessment
  surface.
- the paired prompt split is now frozen:
  - `owlmlx` owns upstream truth surface work
  - `owlops` may consume runtime truth but may not invent runtime semantics
- the current broad upstream prompt already freezes that weak signals must stay
  `unknown` instead of being narrated as solved orchestration.

## Remaining Gaps

- no stable runtime-owned orchestration assessment contract exists yet
- no transport or operator entry exposes that contract directly
- per-layer signal sufficiency is not yet frozen in one machine-readable shape
- `ops` still lacks one stable upstream surface to consume for bottleneck
  classification

## Dominant Next Gap

`orchestration_status_surface_introduction`
