# owlmlx Termination Recovery Policy

> Status: authoritative
> Updated: 2026-04-27
> Scope: runtime-only termination-cause classification and cause-to-action recovery policy (release floor 3.4 sub-round 3.4A on top of 3.4A0)

## 1. Purpose

This document freezes the runtime-owned answer to the release-floor `3.4`
question:

**Given a runtime-owned termination cause, what is the next safe
runtime-owned action: `retry`, `quarantine`, `surface_to_coordinator`, or
`drop`, and when may an unresolved reclaim-barrier event be marked
resolved?**

It is **not** a recovery daemon. It does not retry, quarantine, drop, or
remediate. It records the policy and the resolution rules.

It is the cause-to-action layer on top of `reclaim-barrier-event.md` plus
runtime-owned load-operation-boundary failure events.

## 2. Owned Contract

`owlmlx/termination_recovery_policy.py` now owns:

- `build_termination_recovery_policy(...)`
- `termination_recovery_policy_to_dict(...)`
- `termination_cause_decision_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/termination-recovery-policy`

Contract:

- `surface = "owlmlx.termination_recovery_policy"`
- `version = "v1"`

Stable sections:

- `summary`
- `reason`
- `cause_decisions`
- `active_causes`
- `policy_boundaries`
- `preserved_invariants`
- `missing_signals`

## 3. Termination Cause Vocabulary

Frozen, exactly five classes:

- `load_failure`
- `oom_class_failure`
- `host_forensics_anomaly`
- `graceful_unload_failure`
- `unknown`

## 4. Action Vocabulary

Frozen, exactly four actions:

- `retry`
- `quarantine`
- `surface_to_coordinator`
- `drop`

The `drop` action is in the frozen vocabulary but is **not** mapped to any
required cause class in this round. It is reserved for future
request-level non-recoverable cases. This intentional gap is recorded in
`missing_signals`.

## 5. Cause-To-Action Mapping

| Cause | Action | Source signal |
| --- | --- | --- |
| `load_failure` | `retry` | runtime-owned `load_failure` event recorded at `RuntimeKernel.load_model` boundary (excluding `invalid_request` preflight, `model_already_loaded`, and `memory_budget_exceeded`) |
| `oom_class_failure` | `surface_to_coordinator` | runtime-owned `load_failure` event with `error_code = "memory_budget_exceeded"` (budget preflight failure) |
| `host_forensics_anomaly` | `surface_to_coordinator` | `abort_recovery.snapshot()` reports `state == "contaminated"` or `recovery_required == True`, OR `runtime_status.summary.backend_healthy == False` |
| `graceful_unload_failure` | `quarantine` | unresolved `owlmlx.reclaim_barrier_event` event (`failed_unload`, `failed_reclaim`, or `restart_unload_failed`) |
| `unknown` | `surface_to_coordinator` | no runtime-owned status payload, or no decisive cause active |

When more than one cause is active, the dominant cause is selected by
the priority order:

1. `host_forensics_anomaly` (never safe to auto-retry)
2. `graceful_unload_failure` (residency state untrusted)
3. `oom_class_failure` (operator must free memory)
4. `load_failure` (naturally retryable)
5. `unknown` (fail-safe last)

This priority lives in `DOMINANT_CAUSE_PRIORITY` in
`owlmlx/termination_recovery_policy.py`.

## 6. Resolution Rules

3.4A0 left reclaim-barrier events permanently `resolved = False`. This
round freezes resolution semantics:

### 6.1 Auto-resolve on successful same-model follow-up

Runtime-owned auto-resolution is the primary path. Implemented in
`RuntimeKernel`:

- `unload_model(model_id)` success →
  resolves all unresolved `reclaim_barrier_event` events with
  `model_id == model_id` and
  `operation in {explicit_unload, ttl_sweep_reclaim}`
- `restart_model(model_id)` success →
  resolves all unresolved `reclaim_barrier_event` events with
  `model_id == model_id` and `operation == restart_unload_stage`
- `load_model(model_id)` success →
  resolves all unresolved `load_failure` events with
  `model_id == model_id`

A successful follow-up is required. **Final-status look-clean alone is
not sufficient**: an unresolved event remains active across unrelated
cleanup or new operations on different models. This is enforced by
test `test_resolution_does_not_happen_from_final_status_alone`.

### 6.2 Explicit operator override

`RuntimeKernel.resolve_reclaim_barrier_event(event_id)` is the explicit
operator override path. It marks one specific reclaim-barrier event
resolved. It does **not** retry, remediate, or re-execute the
underlying operation; the operator is asserting the situation is
otherwise resolved.

There is intentionally no HTTP write route in this round. The runtime
method is sufficient for the policy to be tested and consumed; a
narrow `POST /v1/runtime/reclaim-barrier-event/resolve` route is left
as future scope to keep this round's blast radius minimal.

Equivalent resolution for `load_failure` events is auto-resolve only
(no explicit `resolve_load_failure_event` method in this round). Load
failures are naturally resolved by a successful subsequent load
attempt.

## 7. Decision Field Contract

Each cause decision exposes:

- `termination_cause_class`
- `next_action`
- `confidence`
- `reason_code`
- `source_signal`
- `operator_visible_message`
- `resolution_rule`
- `forbidden_automation`
- `active`
- `detected_signals`

`active` is true when at least one runtime-owned input signal proves
the cause. The full per-cause decision is exposed unconditionally so
upper layers can read both the policy *and* whether it currently
fires.

## 8. Integration With Other Contracts

This contract:

- consumes `owlmlx.reclaim_barrier_event` directly
- consumes runtime-owned load-failure events from
  `runtime_status["load_failure"]`
- consumes `runtime_status["summary"]["backend_healthy"]` for host
  forensics
- consumes the abort-recovery snapshot for substrate state

It does **not**:

- re-derive `recovery_supervisor_contract`'s recovery state (the
  recovery contract's `failed_reclaim_barrier` state and
  hard-recovery-barrier wiring continue to drive admission /
  orchestration unchanged)
- modify `reclaim_barrier_event` events; only the kernel mutates
  them, through the auto-resolve and explicit-resolve paths above
- touch `serving.py`, the `GenerationGate`, or any pre-claim
  admission flow

`owlmlx.scheduler_admission_contract` continues to reject admission
via the existing recovery hard-barrier path. No duplicated lifecycle
logic.

`owlmlx.orchestration_status` continues to surface
`summary.bottleneck_layer = "recovery"` whenever the recovery contract
reports a hard barrier.

## 9. What This Does Not Claim

It does not claim:

- a background recovery supervisor daemon
- automatic retry, quarantine execution, drop, or operator
  remediation
- pressure-ranked victim selection or automatic unload under pressure
- stream-hold counters, durations, or active stream-session tracking
- backend-side OOM events distinct from runtime budget preflight (a
  future event source could distinguish them)
- richer host-forensics signals beyond `abort_recovery` substrate
  state and backend health
- a frozen use case for the `drop` action on any required cause
- closure of release floor `3.4` — that is a coordinator decision
  after review

It only claims:

- `owlmlx` now owns one runtime-owned termination-cause classification
  surface
- the four required cause classes (`load_failure`,
  `oom_class_failure`, `host_forensics_anomaly`,
  `graceful_unload_failure`) plus a fail-safe `unknown` map
  deterministically to one action each
- event resolution semantics are runtime-owned: auto-resolve on
  successful same-model follow-up operation, plus explicit kernel
  override; final-status look-clean alone never resolves an event
- the policy is exercised in tests, not only described

## 10. Out Of Scope

Explicitly future-floor work, recorded in `policy_boundaries.out_of_scope`
and `missing_signals`:

- background recovery supervisor daemon
- automatic retry / quarantine / drop execution
- operator remediation workflow
- pressure-ranked victim selection or automatic unload under pressure
- stream-hold counters and active stream-session tracking
- load-attempt scheduling or per-model load-attempt counters
- backend-side OOM event source distinct from runtime budget preflight
- richer host-forensics signals
- frozen drop-action use cases
