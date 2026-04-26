# owlmlx Orchestration Status Surface

> Status: authoritative
> Updated: 2026-04-25
> Scope: runtime-only orchestration layer assessment for single-host owlmlx

## 1. Purpose

This document freezes one narrow runtime-owned answer to the orchestration
composition question:

**Given the runtime-owned child contracts for admission, residency, and memory
pressure, which orchestration bottleneck layer is currently visible, and which
layers must still stay `partial`, `unknown`, or `insufficient_signal`?**

The purpose is not to claim full local-scheduler closure.
The purpose is to keep `owlops` and other upper layers from inventing runtime
semantics that `owlmlx` has not yet frozen itself, while also preventing every
consumer from reading the child contracts separately and drawing different
conclusions.

## 2. Owned Contract

`owlmlx/orchestration_status.py` now owns:

- `build_orchestration_status(...)`
- `orchestration_status_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/orchestration-status`

Contract:

- `surface = "owlmlx.orchestration_status"`
- `version = "v1"`

Stable sections:

- `summary`
- `layer_assessment`
- `scheduler`
- `stream`
- `residency`
- `pressure`
- `recovery`
- `child_surfaces`
- `preserved_invariants`
- `upstream_truth_sources`
- `missing_signals`

## 3. Current Composition Inputs

The refreshed surface is intentionally narrow.

It composes these runtime-owned child surfaces:

- `owlmlx.scheduler_admission_contract`
  - admission decision, request class, gate / pre-claim boundary, preserved
    invariants, request context-length signal, and admission missing signals
- `owlmlx.model_residency_policy`
  - resident/default/pinned/TTL/evictable state classification and residency
    missing signals
- `owlmlx.memory_pressure_contract`
  - budget-pressure classification, TTL-sweep candidate context, and pressure
    missing signals
- `owlmlx.recovery_supervisor_contract`
  - abort-recovery state, restart exhaustion, backend-health barrier impact,
    and recovery missing signals

It does not turn those inputs into broader scheduler or recovery claims than the
runtime actually owns.

## 4. Current Layer Assessments

Current honest layer-assessment posture is:

- `admission`
  - `classification_status = supported`
  - derived from `scheduler_admission_contract`
- `generation_gate`
  - `classification_status = supported`
  - derived from the admission contract's serial `ticketed_fifo`,
    `max_concurrent = 1`, and waiter visibility
- `stream_hold`
  - `classification_status = partial`
  - stream work is known to share the `GenerationGate` boundary on the current
    runtime path, but direct hold counters/durations are not yet frozen
- `model_residency`
  - `classification_status = partial`
  - active/default, inventory, pinning, TTL, and TTL-sweep evictability are now
    surfaced through `model_residency_policy`, while load-on-demand policy
    remains unfrozen
- `memory_pressure`
  - `classification_status = partial` when the pressure contract can classify
    the current budget snapshot as `within_budget`, `near_budget`, or
    `over_budget`
  - pressure-event, reclaim, and pressure-ranked eviction semantics remain
    `insufficient_signal`
- `recovery`
  - `classification_status = partial`
  - recovery-barrier classification now comes from
    `recovery_supervisor_contract`, while automatic recovery supervisor loops,
    failed-reclaim barriers, and broader worker-pollution detection remain
    unfrozen
- `unknown`
  - retained as an explicit fallback when no stronger current-layer verdict is
    runtime-owned

## 5. Current Summary Semantics

`summary.bottleneck_layer` is intentionally conservative:

- `recovery`
  - only when `recovery_supervisor_contract` reports a hard recovery barrier
    such as backend unhealthy, restart exhausted, or contaminated substrate
- `memory_pressure`
  - only when `memory_pressure_contract.summary.pressure_classification =
    "over_budget"`
- `admission`
  - when `scheduler_admission_contract.summary.admission_decision = "deferred"`
    because the pre-claim window is already staged
  - also when admission is deferred because known high-context work hits a
    recovery probing barrier
- `generation_gate`
  - when scheduler admission is deferred by visible gate waiters or an active
    post-claim gate
- `unknown`
  - otherwise

That means the surface may still report a strong per-layer assessment while
keeping the current bottleneck verdict at `unknown`.

This is intentional.

## 6. What This Surface Does Not Claim

It does not claim:

- full single-host orchestration parity
- continuous batching
- memory-pressure closure
- recovery-policy closure
- automatic recovery-supervisor closure
- that `stream_hold` is always the dominant current bottleneck
- that `/v1/runtime/status` stable sections have been replaced
- that each child contract can now be bypassed by consumers

It only claims:

- `owlmlx` now owns one runtime-owned orchestration composition surface
- upper layers can consume one stable layer-by-layer contract instead of
  independently interpreting the child surfaces
- weak signals remain weak rather than being narrated as certainty
