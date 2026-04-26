# owlmlx Execution Prompt 3.4A0: Reclaim Barrier Event

> Date: 2026-04-26
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.4 Recovery Policy Closure`
> Lane: single active executor
> Role: implementation, tests, docs, and handoff
> Seed prompt: `files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`

## 1. Mission

Introduce the first runtime-owned failed-unload / failed-reclaim barrier event
surface needed by release floor `3.4`.

This is a `3.4A0` sub-round. It does **not** close the full recovery policy
floor by itself. It creates the operation-boundary event truth that the later
four-class recovery policy can consume.

The required question is:

**When an unload, reclaim, or restart-unload-stage attempt actually reaches the
cleanup boundary and fails, can `owlmlx` record a stable recovery barrier event
that recovery, admission, and orchestration surfaces consume without guessing
from final status?**

## 2. Coordination Truth

Verified current state:

- `3.1 Cache Scheduler Closure` is closed.
- `3.2 Memory-Pressure Decision Closure` is closed as of 2026-04-26 through
  `owlmlx_release_floor_3_2C_independent_closeout_closed`.
- `3.3 Model Residency Non-Resident Path` is closed.
- `3.4 Recovery Policy Closure` is now the active release floor.
- `3.4` pre-flight notes identify the parked failed-unload/reclaim event prompt
  as a prerequisite/sub-component of 3.4, not a competing lane.

This round must not work on OwlOps, OwlCoda, comparative evidence, public
surface, or customer evidence.

## 3. Required Read Order

Read before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/recovery-supervisor-contract.md`
5. `docs/source-of-truth/memory-pressure-contract.md`
6. `docs/source-of-truth/model-residency-policy.md`
7. `docs/source-of-truth/orchestration-status-surface.md`
8. `docs/source-of-truth/scheduler-admission-contract.md`
9. `docs/source-of-truth/runtime-status-schema.md`
10. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4-pre-flight-notes.md`
11. `files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`
12. `owlmlx/runtime/kernel.py`
13. `owlmlx/runtime/types.py`
14. `owlmlx/runtime/backends.py`
15. `owlmlx/runtime/server.py`
16. `owlmlx/recovery_supervisor_contract.py`
17. `owlmlx/scheduler_admission_contract.py`
18. `owlmlx/orchestration_status.py`
19. `owlmlx/memory_pressure_contract.py`
20. Related tests:
    `tests/test_runtime_kernel.py`,
    `tests/test_recovery_supervisor_contract.py`,
    `tests/test_scheduler_admission_contract.py`,
    `tests/test_orchestration_status.py`,
    `tests/test_memory_pressure_contract.py`,
    `tests/test_model_residency_policy.py`,
    `tests/test_runtime_server.py`

## 4. Implementation Target

Preferred new runtime contract:

- module: `owlmlx/reclaim_barrier_event.py`
- surface: `owlmlx.reclaim_barrier_event`
- route: `GET /v1/runtime/reclaim-barrier-event`
- docs: `docs/source-of-truth/reclaim-barrier-event.md`
- tests: `tests/test_reclaim_barrier_event.py`

The contract should answer only:

**Given runtime-owned lifecycle operation events, is there an unresolved failed
unload or failed reclaim event that requires a recovery barrier?**

Suggested stable sections:

- `contract`
- `summary`
- `barrier`
- `events`
- `operation_support`
- `policy_boundaries`
- `missing_signals`
- `preserved_invariants`

## 5. Event Vocabulary

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
- `resolved`

Suggested operation vocabulary:

- `explicit_unload`
- `ttl_sweep_reclaim`
- `restart_unload_stage`
- `unknown`

Suggested barrier state vocabulary:

- `clean`
  - no unresolved failed unload/reclaim event is visible
- `failed_unload`
  - explicit unload reached backend unload and failed
- `failed_reclaim`
  - reclaim attempt, such as TTL sweep of expired unpinned model, reached
    unload and failed
- `restart_unload_failed`
  - restart attempted unload stage and that unload failed
- `unknown`
  - runtime cannot determine operation-boundary truth

Do not classify these as failed reclaim barriers:

- pinned model blocks before backend cleanup
- missing model preflight failure
- TTL-expired pinned model skipped by policy
- budget `over_budget` without an actual reclaim/unload attempt
- restart visibility without a failed cleanup event

## 6. Runtime Integration Requirement

The smallest acceptable implementation:

1. `RuntimeKernel` records failed cleanup events at the operation boundary.
2. `RuntimeKernel.status_dict()` exposes an event snapshot with explicit
   contract boundaries.
3. `recovery_supervisor_contract` consumes unresolved events as a hard recovery
   barrier.
4. `scheduler_admission_contract` rejects via the recovery hard barrier; it must
   not duplicate lifecycle logic.
5. `orchestration_status` reports `summary.bottleneck_layer = "recovery"` when
   the barrier is active.
6. `memory_pressure_contract` may report that reclaim-attempt result visibility
   exists, but must not claim a full reclaim engine.
7. `GET /v1/runtime/reclaim-barrier-event` returns the read-only contract
   serialization. It must not clear events, retry operations, or perform
   recovery.

## 7. Operation Semantics

### Explicit unload

When `RuntimeKernel.unload_model(model_id)` reaches
`backend.unload(model_id)` and the result is `ok=False`, record a
`failed_unload` barrier event.

Pinned unload rejection must not record a barrier event because it is a policy
block before backend cleanup.

Missing-model failures should remain preflight/backend result truth, but must
not become failed reclaim unless an actual cleanup boundary was attempted and
failed.

### TTL sweep reclaim

When `RuntimeKernel.sweep_expired_models(...)` attempts to unload an expired,
unpinned model and that unload fails, record a `failed_reclaim` barrier event.

Pinned TTL-expired models skipped by policy may remain
`ttl_expiry_blocked_by_pinning` in eviction history, but must not become reclaim
failure events.

### Restart unload stage

When `RuntimeKernel.restart_model(model_id)` reaches the unload stage and that
stage fails, record `restart_unload_failed` or an equivalent event with
`operation = "restart_unload_stage"`.

Do not broaden this round into full restart recovery. Restart load-stage
failure may be context only if existing code exposes it cleanly.

## 8. Hard Rules

1. Do not implement the full four-class recovery policy in this round.
2. Do not implement automatic retry, quarantine execution, restart loops, or
   operator remediation.
3. Do not implement a background recovery supervisor daemon.
4. Do not implement pressure-ranked victim selection or automatic unload under
   pressure.
5. Do not implement stream-hold counters, durations, or active stream-session
   tracking.
6. Do not weaken `max_concurrent=1`, `ticketed_fifo`, or whole-request
   `GenerationGate` claim semantics.
7. Do not import or edit OwlOps, OwlCoda, desktop UI code, or
   `/Users/yeemio/AI/Agent`.
8. Do not mark release floor `3.4` closed. This is a prerequisite sub-round.
9. Preserve unrelated dirty/staged work.

## 9. Required Documentation Updates

Update or add source-of-truth docs so the boundary is reconstructible:

- `docs/source-of-truth/reclaim-barrier-event.md`
- `docs/source-of-truth/recovery-supervisor-contract.md`
- `docs/source-of-truth/memory-pressure-contract.md`
- `docs/source-of-truth/model-residency-policy.md`
- `docs/source-of-truth/orchestration-status-surface.md`
- `docs/source-of-truth/scheduler-admission-contract.md` if the reason surface
  changes
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/release-readiness-backlog.md` only if the 3.4 row
  posture changes honestly; do not mark it closed
- `docs/source-of-truth/master-outline.md` if a new authoritative doc is added

Docs must explicitly state:

- failed unload/reclaim events are recovery-barrier truth
- full recovery policy remains open after 3.4A0
- pressure-ranked eviction is not implemented by this round
- automatic recovery supervisor loops are not implemented
- stream-hold counters are out of scope
- pinned policy blocks are not reclaim failures
- budget pressure alone is not a reclaim failure

## 10. Required Tests

Add or update tests for:

- clean runtime reports no failed unload/reclaim barrier event
- explicit backend unload failure records `failed_unload`
- pinned unload block does not record failed-unload barrier
- TTL sweep of expired unpinned model records `failed_reclaim` when unload fails
- TTL-expired pinned model skip does not record reclaim-failure barrier
- restart unload-stage failure records `restart_unload_failed` or equivalent
- `recovery_supervisor_contract` reports hard recovery barrier when event is
  unresolved
- `scheduler_admission_contract` rejects because of recovery hard barrier
- `orchestration_status` reports recovery as bottleneck when barrier is active
- `memory_pressure_contract` still does not claim pressure-ranked eviction or
  reclaim engine closure
- route-level coverage for `GET /v1/runtime/reclaim-barrier-event`
- no platform dependency enters the new module

## 11. Required Verification

Run at minimum:

```bash
pytest -q tests/test_reclaim_barrier_event.py
pytest -q tests/test_runtime_kernel.py -k "unload or reclaim or ttl or restart"
pytest -q tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py
pytest -q tests/test_memory_pressure_contract.py tests/test_model_residency_policy.py tests/test_orchestration_status.py
pytest -q tests/test_runtime_server.py -k "reclaim_barrier or recovery_supervisor or scheduler_admission_contract or memory_pressure or orchestration_status"
python3 -m py_compile \
  owlmlx/reclaim_barrier_event.py \
  owlmlx/runtime/kernel.py \
  owlmlx/recovery_supervisor_contract.py \
  owlmlx/memory_pressure_contract.py \
  owlmlx/orchestration_status.py \
  owlmlx/runtime/server.py
git diff --check
```

If a command is substituted, record the exact substitution and why. If a filter
matches zero tests, run the relevant unfiltered file and say so.

## 12. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event-handoff.md`

The handoff must include:

- outcome label
- changed files
- exact commands and results
- new barrier event vocabulary
- which runtime operations now record failed unload/reclaim events
- how recovery/admission/orchestration consume the event
- whether `GET /v1/runtime/reclaim-barrier-event` exists
- what remains unknown or out of scope
- whether floor `3.4` remains open
- exact next prompt recommendation
- confirmation that pressure-ranked eviction, automatic recovery supervisor,
  stream-hold counters, OwlOps, OwlCoda, and comparative evidence were not
  touched

## 13. Allowed Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_4A0_reclaim_barrier_event_introduced`
- `owlmlx_release_floor_3_4A0_reclaim_barrier_event_still_blocked`

Use `introduced` only if operation-boundary failed-unload/reclaim barrier truth
is implemented, tested, documented, and wired into recovery/admission/
orchestration surfaces.

If blocked, do not broaden scope. Report the smallest missing
operation-boundary signal needed to make the barrier honest.
