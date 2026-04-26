# owlmlx Model Residency Policy

> Status: authoritative
> Updated: 2026-04-24
> Scope: runtime-only current model residency state classification

## 1. Purpose

This document freezes the second runtime-owned scheduler contract for the active
single-host path:

**Given the current runtime snapshot, which models are resident, active, pinned,
TTL-managed, or eligible for TTL-sweep eviction, and which residency questions
must still stay unknown?**

This is not a full eviction engine.
It is the narrow residency layer that sits behind admission and before any
future memory-pressure policy.

## 2. Owned Contract

`owlmlx/model_residency_policy.py` now owns:

- `build_model_residency_policy(...)`
- `model_residency_policy_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/model-residency-policy`

Contract:

- `surface = "owlmlx.model_residency_policy"`
- `version = "v1"`

Stable sections:

- `summary`
- `target_model`
- `models`
- `residency_state_support`
- `policy_boundaries`
- `signals`
- `missing_signals`

## 3. Current Honest Scope

The current contract builds only from runtime-owned truth already visible in
`/v1/runtime/status`:

- loaded model inventory
- active model ID
- pinning policy and pinned model IDs
- TTL policy and explicit sweep visibility
- TTL-expired model IDs
- eviction-history events
- budget truth as informational context

It does not turn those signals into automatic load-on-demand, pressure-ranked
eviction, or recovery-supervisor behavior.

## 4. Residency State Semantics

Current state vocabulary is:

- `resident`
  - the model is present in runtime-owned loaded-model inventory
- `default_active`
  - the model is the current active target used when requests omit a model
- `pinned`
  - the runtime-owned pin set blocks unload
- `ttl_managed`
  - a kernel-owned TTL policy exists for the model
- `evictable`
  - the model is TTL-expired and not pinned, so explicit TTL sweep may unload it
  - this does not mean pressure-based eviction is solved
- `unknown`
  - the target is not resident, no target is provided, or the signal is too weak

## 5. Boundary With Admission

`scheduler_admission_contract` rejects a non-resident generation target today
because `owlmlx` does not yet own load-on-demand scheduling.

`model_residency_policy` explains that boundary:

- resident target classification is supported
- active/default target classification is supported
- pinned and TTL-managed states are supported
- non-resident target policy remains `unknown`

## 6. Boundary With Pressure And Recovery

This contract does not select memory-pressure victims.

It can say:

- which model is pinned
- which model is TTL-managed
- which unpinned TTL-expired model is eligible for explicit TTL sweep
- which TTL-expired model is blocked by pinning

It cannot yet say:

- which model should be evicted under pressure
- whether a failed unload should trigger recovery
- whether a polluted worker must be restarted
- whether loading a non-resident model should preempt resident work

Those remain separate contracts.

## 7. What This Does Not Claim

It does not claim:

- automatic load-on-demand exists
- pressure-ranked eviction exists
- TTL visibility equals full eviction policy closure
- recovery policy is complete
- full local scheduler depth exists

It only claims:

- `owlmlx` now owns one current-state residency policy surface
- active/default, resident, pinned, TTL-managed, and TTL-sweep evictable states
  are inspectable without shell-side guessing
- weaker pressure and recovery questions remain explicitly outside this contract
