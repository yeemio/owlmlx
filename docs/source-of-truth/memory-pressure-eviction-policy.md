# owlmlx Memory-Pressure Eviction Policy

> Status: authoritative
> Updated: 2026-04-26
> Scope: runtime-only memory-pressure eviction decision and execution

## 1. Purpose

This document freezes the runtime-owned answer to the floor-`3.2` question:

**Given the current memory-pressure classification and residency snapshot,
which resident model should `owlmlx` evict first, and can `owlmlx` execute
that transition while updating residency, lineage/loadability, and eviction-
history truth without weakening serial runtime invariants?**

It is a narrow pressure-eviction contract. It is not a general reclaim
engine, not an automatic background eviction loop, and not a continuous-
batching scheduler.

## 2. Owned Contract

`owlmlx/memory_pressure_eviction_policy.py` now owns:

- `build_memory_pressure_eviction_policy(...)`
- `memory_pressure_eviction_policy_to_dict(...)`

`owlmlx.runtime.kernel.RuntimeKernel.execute_memory_pressure_eviction(...)`
owns the runtime-owned execution path: it builds the policy, refuses to
execute unless the decision is `evict`, unloads the selected victim through
the existing `unload_model` semantics, records a runtime-owned eviction-
history event with `source = "memory_pressure_policy"`, and returns a
structured result.

Runtime transport surfaces:

- `GET /v1/runtime/memory-pressure-eviction-policy` — read-only decision
  - query parameter:
    - `protect_active` — bool, default `true` (protect the active model from
      eviction unless explicitly overridden)
- `POST /v1/runtime/memory-pressure-eviction` — execution
  - body:
    - `protect_active` — bool, default `true`
  - response includes `decision_snapshot`, `selected_victim`,
    `unload_result`, `residency_after`, and `eviction_history_event`; when
    the loadability lineage registry is connected at `create_app(...)`, the
    response also includes `loadability_lineage_after` for the evicted
    model

Contract:

- `surface = "owlmlx.memory_pressure_eviction_policy"`
- `version = "v1"`

Stable sections:

- `summary`
- `reason`
- `selected_victim`
- `candidate_order`
- `pressure`
- `residency_summary`
- `recovery_summary`
- `blocking_signals`
- `preserved_invariants`
- `decision_support`
- `missing_signals`
- `inputs`

## 3. Decision Vocabulary

Exactly one of:

- `evict`
  - memory pressure is `over_budget`
  - at least one resident candidate is unload-eligible (unpinned and not
    active-protected)
  - the candidate ordering is deterministic
- `defer`
  - pressure is `within_budget` (no trigger) or `near_budget` (not yet
    strong enough)
- `reject`
  - pressure is `over_budget` but no safe candidate exists (all pinned,
    only the protected active model unpinned, or no resident models)
  - recovery supervisor reports a hard barrier
- `unknown`
  - pressure truth is absent or `insufficient_signal`
  - `unknown` is never used to hide a deterministic `reject`

## 4. Candidate Ordering

The policy emits a deterministic ordered candidate list. Sort key in
priority order (lower = higher priority for selection):

1. unpinned before pinned (`pinned_models_never_evicted` invariant)
2. TTL-expired unpinned before merely manual-unload-eligible
3. non-active before active (under `protect_active=True`)
4. larger memory footprint before smaller
5. lexical `model_id` ascending tie-break

The first eligible candidate (`pinned == False`,
`active_protected == False`) is selected as the victim. Pinned candidates
remain visible in `candidate_order` with `ordering_reason = "blocked_by_pin"`
but are never selected.

## 5. Round-Trip Inputs

Every decision is built by round-tripping through three runtime-owned
contracts:

- `owlmlx.memory_pressure_contract` — pressure classification
  (`within_budget` / `near_budget` / `over_budget` / `unknown` /
  `insufficient_signal`)
- `owlmlx.model_residency_policy` — resident model inventory and active
  model id
- `owlmlx.recovery_supervisor_contract` — hard recovery barriers

The round trip is read-only; the policy does not mutate any of those
contracts.

## 6. Execution Atomicity

`RuntimeKernel.execute_memory_pressure_eviction` is the runtime-owned
execution surface. It:

1. builds the current policy through `build_memory_pressure_eviction_policy`
2. refuses to execute unless `decision == "evict"` (returns a structured
   `executed=False` result with `reason_code =
   "execution_refused_unless_decision_is_evict"`)
3. calls `self.unload_model(victim_id)` — pinned models are still
   protected by `unload_model`'s pin check, so the invariant is
   double-enforced
4. on unload success, records an eviction-history event:
   `{event: "memory_pressure_evicted", source: "memory_pressure_policy",
   model_id, sequence, recorded_at_s}`
5. returns a structured snapshot with `decision_snapshot`,
   `selected_victim`, `unload_result`, `residency_after`,
   `eviction_history_event`

On unload failure, the result reports `executed=False`, the unload error,
and does not record an eviction-history event. After-state truth is never
claimed when the underlying transition did not occur.

## 7. After-State: Residency, Lineage, Eviction History

After successful eviction:

- residency: `RuntimeKernel.status_dict()["backend"]["loaded_models"]` no
  longer includes the victim; `governance_policy.recent_eviction_history`
  contains the new event
- loadability lineage: when the loadability lineage registry is connected
  at `create_app(...)`, `POST /v1/runtime/memory-pressure-eviction`
  includes `loadability_lineage_after`, which reports whether the
  now-non-resident victim is still `known_loadable`. Lineage records
  themselves are not mutated by eviction
- eviction history: the new event is visible through
  `governance_policy.eviction_history_visible == True`,
  `recent_eviction_history`, and the `phase45-multi-model-eviction-
  history-governance.md` consumer

## 8. Boundary With Other Contracts

This contract is intentionally bounded:

- it does not implement an automatic background eviction loop (rejected by
  Hard Rule 2 of the 3.2A prompt)
- it does not select OS-level pressure events; budget classification is
  the only pressure trigger consumed
- it does not implement scheduler-admission integration; `scheduler_admission_contract`
  does not yet consume this policy. The integration is recorded in
  `missing_signals.scheduler_admission_integration` and deferred to a
  later round
- it does not freeze active reassignment under pressure; the active model
  is protected by default (`protect_active=True`) and `out_of_scope`
  records this
- it does not bypass `GenerationGate`; `preserved_invariants` records
  `max_concurrent_1_after_gate_claim`, `ticketed_fifo_after_gate_claim`,
  `no_post_claim_gate_bypass`, `pinned_models_never_evicted`, and
  `no_automatic_background_eviction_loop`

## 9. What This Does Not Claim

It does not claim:

- automatic reclaim or background eviction
- OS-level pressure observation
- multi-worker scheduling, continuous batching, or fairness scheduling
- replacement-grade scheduler/cache closure
- release readiness, parity, replacement, or production-grade against
  `oMLX` or `vMLX`

It only claims:

- `owlmlx` now owns one runtime-owned pressure-eviction decision surface
  and one runtime-owned execution path
- the decision is deterministic given runtime-owned pressure, residency,
  and recovery inputs
- execution updates residency, eviction history, and (when connected)
  loadability lineage after-state in a single result snapshot
- repeated-load or repeated-pressure scenarios produce observable
  residency change, proven by tests
