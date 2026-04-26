# owlmlx Memory Pressure Contract

> Status: authoritative
> Updated: 2026-04-24
> Scope: runtime-only budget-pressure classification without reclaim closure

## 1. Purpose

This document freezes the third runtime-owned scheduler contract for the active
single-host path:

**Given the current runtime budget snapshot, what memory pressure classification
can `owlmlx` honestly report, and which reclaim / eviction / recovery decisions
remain unsupported?**

This is not a reclaim engine.
It is the narrow pressure layer that converts budget truth into conservative
classification while refusing to invent pressure events or victim selection.

## 2. Owned Contract

`owlmlx/memory_pressure_contract.py` now owns:

- `build_memory_pressure_contract(...)`
- `memory_pressure_contract_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/memory-pressure-contract`

Contract:

- `surface = "owlmlx.memory_pressure_contract"`
- `version = "v1"`

Stable sections:

- `summary`
- `reason`
- `budget`
- `residency_context`
- `recovery_context`
- `policy_boundaries`
- `classification_support`
- `missing_signals`

## 3. Current Honest Scope

The current contract builds only from runtime-owned truth already visible in
`/v1/runtime/status`:

- serving budget
- warning threshold
- currently loaded memory
- available budget headroom
- utilization
- loaded-model count
- TTL-sweep candidate context from residency/governance truth
- restart visibility as non-decisive context

It does not treat those signals as direct operating-system memory pressure or
as evidence that reclaim policy is complete.

## 4. Pressure Classification Semantics

Current classification vocabulary is:

- `within_budget`
  - budget snapshot has positive headroom below the warning threshold
- `near_budget`
  - loaded memory reaches the warning threshold, or utilization is high enough
    to warn, without exceeding the serving budget
- `over_budget`
  - budget headroom is negative, utilization is above 1.0, or loaded memory
    exceeds the serving budget
- `unknown`
  - required budget fields are missing
- `insufficient_signal`
  - used for action families where budget truth is not enough, such as direct
    pressure events, reclaim results, pressure-ranked eviction, or restart
    barriers

## 5. Boundary With Residency

`model_residency_policy` can expose TTL-expired unpinned models as eligible for
explicit TTL sweep.

`memory_pressure_contract` may include that as context, but it must not promote
that context into pressure victim selection. TTL-sweep eligibility answers
whether an already-expired unpinned model can be swept; it does not answer which
model should be sacrificed under live pressure.

## 6. Boundary With Recovery

Restart visibility is context only in this contract.

The memory pressure contract cannot say:

- reclaim succeeded or failed
- a worker is polluted
- restart is mandatory
- a failed unload must trigger isolation

Those remain recovery-supervisor questions.

## 7. What This Does Not Claim

It does not claim:

- memory pressure closure is complete
- budget utilization is a direct pressure event
- pressure-ranked eviction execution is closed in this contract — the
  decision and runtime-owned execution path now live in the adjacent
  `memory-pressure-eviction-policy.md` and
  `RuntimeKernel.execute_memory_pressure_eviction(...)`; this
  classification contract remains read-only and does not run eviction
  itself
- eviction history equals pressure policy
- restart visibility equals recovery barrier

It only claims:

- `owlmlx` now owns one budget-pressure classification surface
- budget truth is machine-readable without shell-side guessing
- reclaim, eviction ranking, and recovery remain explicit missing signals
