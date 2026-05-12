# owlmlx Reclaim Barrier Event Contract

> Status: authoritative
> Updated: 2026-05-12
> Scope: runtime-only failed-unload / failed-reclaim / restart-unload-stage barrier event surface (release floor 3.4 sub-round 3.4A0)

## 1. Purpose

This document freezes the runtime-owned answer to one narrow operation-boundary
question:

**When an unload, reclaim, or restart-unload-stage attempt actually reaches the
cleanup boundary and fails, can `owlmlx` record a stable recovery barrier event
that recovery, admission, and orchestration surfaces consume without guessing
from final status?**

It is **not** a recovery policy. It does not retry, quarantine, drop, or
remediate. It records.

It is **not** the full release-floor `3.4` closure. It is sub-round
`3.4A0`. The four-class termination-cause recovery policy
(`retry / quarantine / surface_to_coordinator / drop`) and its event-resolution
rules remain future 3.4 work.

## 2. Owned Contract

`owlmlx/reclaim_barrier_event.py` now owns:

- `build_reclaim_barrier_event(...)`
- `reclaim_barrier_event_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/reclaim-barrier-event`
- `GET /v1/runtime/reclaim-barrier-event/stats`

Contract:

- `surface = "owlmlx.reclaim_barrier_event"`
- `version = "v1"`

Stable sections:

- `summary`
- `barrier`
- `events`
- `operation_support`
- `policy_boundaries`
- `preserved_invariants`
- `missing_signals`

The HTTP route is read-only. It must not clear events, retry operations, or
perform recovery.

The `/stats` route is also read-only. It aggregates unload/reclaim boundary
measurements that `RuntimeKernel` records alongside the barrier-event stream.
It does not change event resolution state.

## 3. Operation Vocabulary

Events are recorded under one of:

- `explicit_unload` — `RuntimeKernel.unload_model(model_id)` reached
  `backend.unload(...)` and the result was `ok=False` with an error code
  other than `model_not_loaded`
- `ttl_sweep_reclaim` — `RuntimeKernel.sweep_expired_models(...)` attempted
  to unload an expired, unpinned model and that unload reached the backend
  cleanup boundary and failed
- `restart_unload_stage` — `RuntimeKernel.restart_model(model_id)` reached
  its unload stage and that stage's `backend.unload(...)` returned a failure
  result other than `model_not_loaded`
- `unknown` — fallback for events whose operation classification is absent

## 4. Barrier State Vocabulary

Exactly one of:

- `clean` — no unresolved failed unload/reclaim/restart-unload-stage event
  is currently visible
- `failed_unload` — at least one unresolved event with
  `operation = "explicit_unload"`
- `failed_reclaim` — at least one unresolved event with
  `operation = "ttl_sweep_reclaim"`
- `restart_unload_failed` — at least one unresolved event with
  `operation = "restart_unload_stage"`
- `unknown` — runtime status snapshot does not expose the
  `reclaim_barrier` section

When multiple unresolved events exist, the latest event's operation
determines the barrier state, since the latest event is the most recent
runtime-owned operation-boundary truth.

## 5. Event Fields

Each event carries the following fields (consumed by both the contract and
the kernel-side recorder):

- `event_id` (monotonic integer)
- `model_id`
- `operation` (`explicit_unload` / `ttl_sweep_reclaim` /
  `restart_unload_stage` / `unknown`)
- `source` (currently `"runtime_kernel"`)
- `stage` (currently `"backend_unload"`)
- `error_code` (the underlying `RuntimeErrorCode.value` or `null`)
- `message` (the underlying operation result message)
- `recorded_at_s` (kernel clock timestamp, second precision)
- `requires_recovery_barrier` (currently always `True`)
- `resolved` (currently always `False`; resolution policy is future work)

## 6. What Is Not A Reclaim Barrier

The following are explicitly not classified as reclaim-failure barrier
events:

- pinned model unload blocked before the backend cleanup boundary
- missing-model preflight failure (`error_code = "model_not_loaded"`)
- TTL-expired pinned model skipped by policy (continues to record
  `ttl_expiry_blocked_by_pinning` in eviction history, not in this contract)
- `over_budget` budget pressure without an actual reclaim/unload attempt
- restart visibility without a failed cleanup event

These remain policy / preflight / observability truth, not recovery
failure barriers.

## 7. Integration With Other Contracts

`owlmlx.recovery_supervisor_contract` consumes the contract and reports
recovery state `failed_reclaim_barrier` with
`barrier_decision = "recovery_barrier_required"` whenever an unresolved
event is visible. This is a hard recovery barrier.

`owlmlx.scheduler_admission_contract` continues to reject admission via
the recovery hard-barrier path; it does not duplicate lifecycle logic.

`owlmlx.orchestration_status` reports
`summary.bottleneck_layer = "recovery"` whenever the recovery contract is
hard-blocked by this event (`bottleneck_layer` already routes through
`hard_recovery_barrier`).

`owlmlx.memory_pressure_contract` records that runtime-owned reclaim
attempt-result visibility now exists
(`policy_boundaries.runtime_owned_reclaim_attempt_result_visibility`),
but still does not own a reclaim engine, pressure-ranked eviction, or a
recovery supervisor loop.

`owlmlx.runtime.kernel.RuntimeKernel.status_dict()` exposes the snapshot
under the diagnostic section `reclaim_barrier`:

- `events` — the most recent up to 32 events (read-only snapshot)
- `total_event_count` — total events recorded
- `unresolved_event_count` — unresolved events

`RuntimeKernel.reclaim_barrier_stats()` exposes a separate aggregate surface
through `GET /v1/runtime/reclaim-barrier-event/stats`:

- `summary.measurement_count` — unload/reclaim boundary measurements recorded
  by the kernel
- `duration_ms` — min / p50 / p95 / p99 / max for backend unload-boundary
  duration
- `observed_active_memory_freed_bytes` and
  `observed_cache_memory_freed_bytes` — distributions when the backend reports
  measured reclaim fields on `UnloadResult`
- `expected_minus_observed_active_bytes` — signed distribution for declared
  reclaim bytes minus observed active-memory freed bytes when both signals are
  available
- `operation_counts` and `failure_counts` — aggregate counts by operation and
  error code

The stats surface intentionally keeps successful unload measurements separate
from `reclaim_barrier.events`, because the event stream remains reserved for
cleanup-boundary failures that may require a recovery barrier.

## 8. Event Resolution Semantics (3.4A)

3.4A0 intentionally left every event `resolved = False`. The follow-on
3.4A round freezes resolution semantics inside `RuntimeKernel`:

- successful `unload_model(model_id)` resolves any unresolved event
  with matching `model_id` and `operation in
  {explicit_unload, ttl_sweep_reclaim}`
- successful `restart_model(model_id)` resolves any unresolved event
  with matching `model_id` and `operation == restart_unload_stage`
- the explicit operator override is
  `RuntimeKernel.resolve_reclaim_barrier_event(event_id)`; it marks
  one specific event resolved without retrying, remediating, or
  re-executing the underlying operation
- final-status look-clean alone never resolves an event; only a
  successful follow-up operation or the explicit override may resolve

See `termination-recovery-policy.md` §6 for the full resolution rules.

## 9. What This Does Not Claim

It does not claim:

- automatic retry, quarantine execution, restart loops, operator
  remediation
- a background recovery supervisor daemon
- pressure-ranked victim selection or automatic unload under pressure
- stream-hold counters or active stream-session tracking
- automatic execution of the four-class termination-cause recovery
  policy (`retry / quarantine / surface_to_coordinator / drop`); the
  policy itself is frozen by `termination-recovery-policy.md`, but
  this contract only records and resolves events
- release readiness, parity, replacement, or production-grade against
  `oMLX` / `vMLX`
- closure of release floor `3.4` — that remains a coordinator
  decision after review of `termination-recovery-policy.md`

It only claims:

- `owlmlx` now owns one runtime-owned cleanup-boundary failure event
  surface
- failed unload, failed reclaim, and restart unload stage failures are
  recorded at the operation boundary
- recovery, admission, and orchestration consume the snapshot through
  the existing recovery hard-barrier path, without duplicating lifecycle
  logic
- pinned-policy blocks, missing-model preflight failures, TTL-pinned
  skips, and budget pressure alone are explicitly not reclaim failures
