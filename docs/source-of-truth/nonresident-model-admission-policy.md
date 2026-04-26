# owlmlx Non-Resident Model Admission Policy

> Status: authoritative
> Updated: 2026-04-25
> Scope: runtime-only pre-claim admission decision for non-resident model targets

## 1. Purpose

This document freezes the runtime-owned answer to the release-floor `3.3`
question:

**Given a non-resident target model plus current budget, pressure, residency,
lineage, and recovery truth, should `owlmlx` admit-and-load, defer, reject, or
return unknown?**

It is a narrow pre-claim decision contract. It does not implement an automatic
loader, a pressure-ranked eviction engine, or a continuous-batching scheduler.
It does not bypass the post-claim `GenerationGate` invariants.

## 2. Owned Contract

`owlmlx/nonresident_model_admission_policy.py` now owns:

- `build_nonresident_model_admission_policy(...)`
- `nonresident_model_admission_policy_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/nonresident-model-admission-policy`
  - query parameters:
    - `model_id` — target non-resident model id (required for non-`reject`)
    - `request_context_class` — optional, e.g. `high_context`
    - `known_loadable_model_ids` — optional repeated query param, operator-
      supplied lineage hint while runtime-owned loadability discovery is missing

Contract:

- `surface = "owlmlx.nonresident_model_admission_policy"`
- `version = "v1"`

Stable sections:

- `summary`
- `reason`
- `required_preconditions`
- `blocking_signals`
- `preserved_invariants`
- `inputs`
- `decision_support`
- `policy_boundaries`
- `missing_signals`

## 3. Decision Vocabulary

The policy returns exactly one decision:

- `admit_and_load`
  - target is known non-resident
  - target is in operator-supplied `known_loadable_model_ids`
  - memory pressure is `within_budget`
  - no hard recovery barrier is active
  - no high-context defer condition applies
- `defer`
  - a named precondition must resolve before a safe load decision; current
    sources of `defer` are:
    - recovery is `probing` and the request is `high_context`
    - memory pressure is `near_budget` and no pressure-action policy exists
- `reject`
  - no `model_id` was provided
  - the target is already resident (the policy does not produce admit_and_load
    for already-loaded models)
  - recovery supervisor reports a hard barrier (backend unhealthy, restart
    exhausted, or substrate contaminated)
  - memory pressure is `over_budget` and runtime does not yet own a pressure-
    ranked eviction execution policy (release floor `3.2`)
- `unknown`
  - memory pressure truth is absent or incomplete
  - target is non-resident and operator did not supply a lineage hint
  - `unknown` is never used to hide a deterministic reject

Each decision payload includes:

- `reason` (`code` plus human-readable `message`)
- `target_model_id`
- `required_preconditions`
- `blocking_signals`
- `preserved_invariants`
- `missing_signals`
- `inputs` (residency, memory_pressure, recovery summaries)

## 4. Required Round Trip

The policy round-trips through three existing runtime-owned contracts on every
build:

- `owlmlx.model_residency_policy` — to classify the target as resident or
  non-resident, and to expose `resident_model_ids`
- `owlmlx.memory_pressure_contract` — to classify pressure as
  `within_budget` / `near_budget` / `over_budget` / `unknown` /
  `insufficient_signal`
- `owlmlx.recovery_supervisor_contract` — to expose hard recovery barriers and
  high-context-only barriers

The round trip is read-only. The policy does not mutate any of those
contracts; it only consumes their decisions.

## 5. Boundary With Other Contracts

This contract is intentionally bounded:

- it does not select pressure-eviction victims; that belongs to release floor
  `3.2`
- it does not run a recovery loop; that belongs to release floor `3.4` and is
  partially staged through `recovery_supervisor_contract`
- it does not implement an automatic non-resident loader; runtime-owned
  load/unload remains explicit operator action through `/v1/load` and
  `/v1/unload`
- it does not bypass `GenerationGate`; the `preserved_invariants` field
  records `max_concurrent_1_after_gate_claim`, `ticketed_fifo_after_gate_claim`,
  `no_post_claim_gate_bypass`, and `pre_claim_decision_only`

## 6. Lineage Truth Status

Runtime now owns a non-resident loadability discovery surface through
`owlmlx.nonresident_loadability_lineage` (see
`nonresident-loadability-lineage.md`). The current honest posture is:

- when `loadability_lineage` is supplied to the policy and returns
  `known_loadable`, admission can produce `admit_and_load` **without** any
  `known_loadable_model_ids` operator hint
- when `loadability_lineage` returns `not_loadable`, admission rejects with
  reason code
  `runtime_owned_loadability_lineage_says_not_loadable`, even if an operator
  hint is supplied
- when `loadability_lineage` returns `unknown` (source not connected), the
  policy falls back to the operator-supplied
  `known_loadable_model_ids` as a labeled legacy fallback; this fallback is
  not closure
- `inputs.loadability_lineage.decision`,
  `inputs.loadability_lineage.loadability_lineage_truth_status`, and
  `inputs.known_loadable_truth_status` make the source of every decision
  inspectable
- `missing_signals.runtime_owned_non_resident_loadability_lineage`
  disappears from the payload only when the contract is connected and
  returns `known_loadable` or `not_loadable`; it stays present while the
  contract returns `unknown` so future rounds can distinguish "contract not
  connected" from "contract connected and decisive"

Connection point: `loadability_lineage_records` (and
`visibility_models_root`, `visibility_registry`) are passed to
`owlmlx.runtime.server.create_app(...)` at app construction time, not as
per-request query hints.

## 7. Scheduler Admission Integration

`scheduler_admission_contract` does not yet consume this policy. The
integration is deferred to a later round on purpose:

- the new contract should stabilize on its own surface before another contract
  starts depending on it
- `scheduler_admission_contract` already has 400+ lines of behavior tests; a
  cross-contract change in this same lane would risk regressing them and
  blurring the floor `3.3` verdict
- the policy already exposes a stable shape (`decision`, `reason.code`,
  `blocking_signals`) suitable for a thin pre-claim defer-to-load consumer

`missing_signals` records this explicitly under
`scheduler_admission_integration` so future rounds can find the integration
seam without re-deriving it.

## 8. What This Does Not Claim

It does not claim:

- an automatic non-resident loader exists
- a pressure-ranked eviction engine exists
- recovery supervision is closed
- continuous batching exists
- multi-worker scheduling exists
- release readiness, parity, or replacement against `oMLX` or `vMLX`

It only claims:

- `owlmlx` now owns one runtime-owned pre-claim admission decision surface for
  non-resident model targets
- the decision is deterministic given the round-trip inputs and the operator-
  supplied lineage hint
- the decision exposes its blockers and missing signals rather than hiding
  them as silent unknowns
