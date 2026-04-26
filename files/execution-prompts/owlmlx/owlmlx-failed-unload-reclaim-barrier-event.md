# owlmlx Execution Prompt: Failed Unload / Reclaim Barrier Event

> Coordinator supersession: archived for later recovery-floor work, but **not**
> the next active execution round after
> `docs/source-of-truth/release-readiness-backlog.md` landed. The next active
> release-readiness round is
> `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`.
>
> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Coordinator decision: after request context-length truth closed the recovery
> `probing` admission gap, the next dominant orchestration gap is the missing
> runtime-owned failed-unload / failed-reclaim barrier event. Do this before
> stream-hold counters or pressure-ranked eviction.

## Coordination Truth

The current staged orchestration baseline owns these runtime surfaces:

- `owlmlx.scheduler_admission_contract`
- `owlmlx.request_context_length_truth`
- `owlmlx.model_residency_policy`
- `owlmlx.memory_pressure_contract`
- `owlmlx.recovery_supervisor_contract`
- `owlmlx.orchestration_status`

The latest round introduced request context-length truth:

- known `high_context` + recovery `probing` now defers admission
- known `non_high_context` + recovery `probing` does not defer or reject solely
  because of probing
- unknown context remains explicit `unknown`

That closes the recovery-probing admission gap.

The next missing runtime-owned signal is now:

**When an unload or reclaim attempt actually fails, does `owlmlx` record a
stable recovery barrier event that recovery/admission/orchestration can consume
without guessing from budget or restart visibility?**

## Objective

Introduce a narrow runtime-owned failed-unload / failed-reclaim barrier event
surface and thread it into recovery and orchestration truth.

This round should make failed lifecycle cleanup visible as recovery-barrier
truth. It must not implement a pressure-ranked eviction engine or a background
recovery supervisor.

Allowed outcome labels:

- `owlmlx_failed_unload_reclaim_barrier_event_introduced`
- `owlmlx_failed_unload_reclaim_barrier_event_still_blocked`

## Hard Rules

1. Do not implement pressure-ranked victim selection.
2. Do not implement automatic unload under pressure.
3. Do not implement a background recovery supervisor loop.
4. Do not implement automatic retry, automatic restart, or automatic operator
   remediation.
5. Do not implement stream-hold counters, durations, or active stream-session
   tracking in this round.
6. Do not change `max_concurrent=1`, `ticketed_fifo`, or whole-request
   `GenerationGate` claim semantics.
7. Do not import `llm_router`, `ops_dashboard`, desktop UI code, or
   `/Users/yeemio/AI/Agent` modules.
8. Do not classify a policy block as a recovery failure. Pinned unload blocks,
   missing-model preflight failures, and pinned TTL-expiry skips are not failed
   reclaim barriers.
9. A barrier event must be recorded from the operation result at the operation
   boundary. Do not reconstruct a decisive failure by reading final status after
   unrelated cleanup.
10. If no honest event source exists, keep the outcome `still_blocked` rather
    than inventing a fake barrier.

## Required Read Order

Read these current files before editing:

1. `owlmlx/runtime/kernel.py`
2. `owlmlx/runtime/types.py`
3. `owlmlx/runtime/backends.py`
4. `owlmlx/runtime/server.py`
5. `owlmlx/recovery_supervisor_contract.py`
6. `owlmlx/memory_pressure_contract.py`
7. `owlmlx/model_residency_policy.py`
8. `owlmlx/orchestration_status.py`
9. `owlmlx/scheduler_admission_contract.py`
10. `docs/source-of-truth/recovery-supervisor-contract.md`
11. `docs/source-of-truth/memory-pressure-contract.md`
12. `docs/source-of-truth/model-residency-policy.md`
13. `docs/source-of-truth/orchestration-status-surface.md`
14. `docs/source-of-truth/runtime-status-schema.md`
15. `tests/test_runtime_kernel.py`
16. `tests/test_recovery_supervisor_contract.py`
17. `tests/test_memory_pressure_contract.py`
18. `tests/test_orchestration_status.py`
19. `tests/test_scheduler_admission_contract.py`
20. `tests/test_runtime_server.py`

## Required Design Shape

Add a narrow runtime-owned contract, preferably:

- `owlmlx/reclaim_barrier_event.py`
- `RECLAIM_BARRIER_EVENT_SURFACE = "owlmlx.reclaim_barrier_event"`

The contract should answer only:

**Given runtime-owned lifecycle operation events, is there an unresolved failed
unload or failed reclaim event that requires a recovery barrier?**

Suggested stable sections:

- `summary`
- `barrier`
- `events`
- `operation_support`
- `policy_boundaries`
- `missing_signals`

Suggested event fields:

- `event_id`
- `model_id`
- `operation`
- `source`
- `stage`
- `error_code`
- `message`
- `recorded_at_s`
- `requires_recovery_barrier`

Suggested operation vocabulary:

- `explicit_unload`
- `ttl_sweep_reclaim`
- `restart_unload_stage`
- `unknown`

Suggested barrier state vocabulary:

- `clean`
  - no unresolved failed unload/reclaim event is visible
- `failed_unload`
  - an explicit unload operation reached the backend unload boundary and failed
- `failed_reclaim`
  - a reclaim attempt, such as TTL sweep of an expired unpinned model, reached
    unload and failed
- `restart_unload_failed`
  - restart attempted its unload stage and that unload failed
- `unknown`
  - the runtime cannot determine operation boundary truth

Do not classify these as failed reclaim barriers:

- pinned model blocks unload before backend cleanup
- missing model preflight failure
- TTL-expired pinned model skipped by policy
- budget `over_budget` without an actual reclaim/unload attempt
- restart visibility without a failed cleanup event

## Runtime Integration

The smallest acceptable implementation is:

1. `RuntimeKernel` records failed cleanup events at the exact operation boundary.
2. `RuntimeKernel.status_dict()` exposes the event snapshot in a stable or
   diagnostic section with explicit contract boundaries.
3. `recovery_supervisor_contract` consumes the event snapshot and treats an
   unresolved failed unload/reclaim barrier as a hard recovery barrier.
4. `scheduler_admission_contract` continues to reject via the recovery hard
   barrier, not by duplicating lifecycle logic.
5. `orchestration_status` reports `summary.bottleneck_layer = "recovery"` when
   the recovery supervisor contract is hard-blocked by this event.
6. `memory_pressure_contract` may surface that reclaim-attempt result visibility
   now exists, but must still keep pressure-ranked eviction and reclaim engine
   policy out of scope.

If you add a transport surface, prefer a read-only endpoint:

- `GET /v1/runtime/reclaim-barrier-event`

It should return the contract serialization only. It must not clear events,
retry operations, or perform recovery.

## Required Semantics

### Explicit unload

When `RuntimeKernel.unload_model(model_id)` reaches `backend.unload(model_id)`
and the result is `ok=False`, record a failed-unload barrier event.

Pinned unload rejection must not record a barrier event because it is a policy
block before backend cleanup.

Missing-model failures should remain preflight or backend result truth, but
should not be promoted into failed reclaim unless an actual cleanup boundary was
attempted and failed.

### TTL sweep reclaim

When `RuntimeKernel.sweep_expired_models(...)` attempts to unload an expired,
unpinned model and that unload fails, record a failed-reclaim barrier event.

Pinned TTL-expired models skipped by policy should continue to be recorded as
`ttl_expiry_blocked_by_pinning` in eviction history, but must not become a
reclaim failure.

### Restart unload stage

When `RuntimeKernel.restart_model(model_id)` reaches the unload stage and that
stage fails, record a restart-unload-stage barrier event or map it into the same
failed-unload event contract with `operation = "restart_unload_stage"`.

Do not broaden this round into full restart recovery. Restart load-stage failure
may be included as context only if the existing code already exposes it cleanly,
but the required closure is failed unload/reclaim barrier truth.

## Required Documentation Updates

Update or add source-of-truth docs so the boundary is reconstructible:

- `docs/source-of-truth/reclaim-barrier-event.md`
- `docs/source-of-truth/recovery-supervisor-contract.md`
- `docs/source-of-truth/memory-pressure-contract.md`
- `docs/source-of-truth/model-residency-policy.md`
- `docs/source-of-truth/orchestration-status-surface.md`
- `docs/source-of-truth/scheduler-admission-contract.md` if the reason surface
  changes
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/runtime-capability-matrix.md` only if a capability label
  changes

The docs must explicitly state:

- failed unload/reclaim events are recovery-barrier truth
- pressure-ranked eviction is still not implemented
- automatic recovery supervisor loops are still not implemented
- stream-hold counters are still out of scope
- pinned policy blocks are not reclaim failures
- budget pressure alone is not a reclaim failure

## Required Tests

Add or update tests for:

- clean runtime reports no failed unload/reclaim barrier event
- explicit backend unload failure records `failed_unload`
- pinned unload block does not record a failed-unload barrier
- TTL sweep of expired unpinned model records `failed_reclaim` when unload fails
- TTL-expired pinned model skip does not record a reclaim-failure barrier
- restart unload-stage failure records `restart_unload_failed` or equivalent
  failed-unload event truth
- `recovery_supervisor_contract` reports hard recovery barrier when the event is
  unresolved
- `scheduler_admission_contract` rejects because of the recovery hard barrier
- `orchestration_status` reports recovery as the bottleneck when the barrier is
  active
- `memory_pressure_contract` still does not claim pressure-ranked eviction or
  reclaim engine closure
- route-level coverage for any new endpoint
- no platform dependency enters the new module

## Required Checks

Run at minimum:

```bash
pytest -q tests/test_reclaim_barrier_event.py
pytest -q tests/test_runtime_kernel.py -k "unload or reclaim or ttl or restart"
pytest -q tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py
pytest -q tests/test_memory_pressure_contract.py tests/test_model_residency_policy.py tests/test_orchestration_status.py
pytest -q tests/test_runtime_server.py -k "reclaim_barrier or recovery_supervisor or scheduler_admission_contract or memory_pressure or orchestration_status"
python3 -m py_compile owlmlx/reclaim_barrier_event.py owlmlx/runtime/kernel.py owlmlx/recovery_supervisor_contract.py owlmlx/memory_pressure_contract.py owlmlx/orchestration_status.py owlmlx/runtime/server.py
git diff --check
```

If `tests/test_reclaim_barrier_event.py` is unnecessary because the executor
folds tests into existing files, state that explicitly in the final report.

## Final Report

Return:

- outcome label
- changed files
- exact commands and results
- new barrier event vocabulary
- which runtime operations now record failed unload/reclaim events
- how recovery/admission/orchestration consume the event
- what remains unknown or out of scope
- confirmation that pressure-ranked eviction, automatic recovery supervisor,
  and stream-hold counters were not implemented

If the round is still blocked, do not broaden scope. Report the smallest
missing operation-boundary signal needed to make failed unload/reclaim barrier
truth honest.
