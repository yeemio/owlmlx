# owlmlx Execution Handoff 3.4A0: Reclaim Barrier Event

> Lane: single owlmlx executor (release floor 3.4 sub-round 3.4A0)
> Updated: 2026-04-26
> Active release floor: `3.4 Recovery Policy Closure` (remains **open**)
> Role: implementation, tests, docs, and handoff

## 1. Outcome Label

`owlmlx_release_floor_3_4A0_reclaim_barrier_event_introduced`

Operation-boundary failed-unload / failed-reclaim / restart-unload-stage
barrier truth is implemented, tested, documented, and wired into
recovery / admission / orchestration surfaces. Release floor `3.4`
remains open — the four-class termination-cause recovery policy is
explicitly future work.

## 2. Changed Files

New runtime module:

- `owlmlx/reclaim_barrier_event.py`
  - `RECLAIM_BARRIER_EVENT_SURFACE = "owlmlx.reclaim_barrier_event"`,
    `version = "v1"`
  - `OPERATION_VOCABULARY`, `BARRIER_STATE_VOCABULARY`,
    `REQUIRED_EVENT_FIELDS`
  - `build_reclaim_barrier_event(...)`,
    `reclaim_barrier_event_to_dict(...)`,
    `ReclaimBarrierEventContract`

Modified runtime modules (integration only):

- `owlmlx/runtime/kernel.py`
  - new `_reclaim_barrier_events: list[dict[str, Any]]` and
    `_reclaim_barrier_event_seq: int` instance state
  - new `_record_reclaim_barrier_event(...)` helper that records an
    event at the operation boundary
  - `unload_model(model_id, *, _operation="explicit_unload")` records a
    `failed_unload` event when the backend cleanup boundary returns a
    failure other than `model_not_loaded`; pinned-policy block
    intentionally skips recording
  - `sweep_expired_models(...)` calls
    `unload_model(..., _operation="ttl_sweep_reclaim")` so a sweep cleanup
    failure is recorded as `failed_reclaim`; pinned skip continues to
    record `ttl_expiry_blocked_by_pinning` only
  - `restart_model(...)` records a `restart_unload_stage` event when the
    unload stage fails (other than `model_not_loaded`)
  - `status_dict()` exposes a new diagnostic section `reclaim_barrier`
    with `events` (most recent up to 32), `total_event_count`,
    `unresolved_event_count`; the `diagnostic_sections` list now
    includes `reclaim_barrier`
- `owlmlx/recovery_supervisor_contract.py`
  - imports `build_reclaim_barrier_event`
  - new recovery state `failed_reclaim_barrier` mapped to
    `barrier_decision = "recovery_barrier_required"` (already a hard
    barrier through the existing decision set)
  - `lifecycle` block now reports `reclaim_barrier_state`,
    `reclaim_barrier_unresolved_event_count`, and
    `reclaim_barrier_active`
  - `missing_signals` retired the
    `failed_reclaim_or_failed_unload_barrier_event` placeholder (now
    owned) and added `frozen_four_class_termination_cause_recovery_policy`
- `owlmlx/memory_pressure_contract.py`
  - `policy_boundaries.runtime_owned_reclaim_attempt_result_visibility`
    now points at `owlmlx.reclaim_barrier_event`
  - `missing_signals` retired the standalone reclaim-attempt entry and
    folded the visibility cross-reference into the recovery row
- `owlmlx/runtime/server.py`
  - new imports for `build_reclaim_barrier_event`,
    `reclaim_barrier_event_to_dict`
  - new route `GET /v1/runtime/reclaim-barrier-event` (read-only)

Tests:

- `tests/test_reclaim_barrier_event.py` — 17 new tests covering all
  operation boundaries, all barrier states, recovery / admission /
  orchestration integration, route coverage, schema vocabulary, and a
  no-platform-dependency check
- `tests/test_runtime_kernel.py` — updated the `diagnostic_sections`
  pin to include `"reclaim_barrier"`
- `tests/test_runtime_server.py` — same `diagnostic_sections` pin update
- `tests/test_memory_pressure_contract.py` — updated the
  reclaim/eviction missing-signal assertion to match the new
  `runtime_owned_reclaim_attempt_result_visibility` boundary while
  asserting reclaim engine remains out of scope

Updated source-of-truth docs:

- `docs/source-of-truth/reclaim-barrier-event.md` — **new**, frozen
  contract / vocabulary / non-classifying paths / consumer integration /
  what-this-does-not-claim
- `docs/source-of-truth/recovery-supervisor-contract.md` — added
  `failed_reclaim_barrier` recovery state to §4 and §5; §7 disclaims
  resolve-policy ownership and four-class termination-cause closure
- `docs/source-of-truth/memory-pressure-contract.md` — §7 records
  reclaim-attempt result visibility now exists via
  `owlmlx.reclaim_barrier_event` while disclaiming reclaim engine /
  pressure-ranked eviction execution
- `docs/source-of-truth/model-residency-policy.md` — §7 clarifies that
  cleanup-boundary failures are now recorded by
  `owlmlx.reclaim_barrier_event` while pinned TTL-expiry skips remain
  `ttl_expiry_blocked_by_pinning` and are intentionally not reclaim
  failures
- `docs/source-of-truth/orchestration-status-surface.md` — §4 / §5
  record that recovery bottleneck now includes
  `failed_reclaim_barrier`
- `docs/source-of-truth/runtime-status-schema.md` — added §17
  describing the `/v1/runtime/reclaim-barrier-event` route and the
  `reclaim_barrier` diagnostic section
- `docs/source-of-truth/release-readiness-execution-plan.md` — header
  date and §6 record the 3.4A0 closeout outcome and name 3.4A as the
  next active prompt
- `docs/source-of-truth/master-outline.md` — index entry 132 for
  `reclaim-barrier-event.md`

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not**
modified per §9 — floor `3.4` is not closed by this round, so the
section-5 row stays `open`.
`docs/source-of-truth/scheduler-admission-contract.md` was **not**
modified — admission still rejects via the existing recovery
hard-barrier path; no admission reason surface change was required.

## 3. Commands and Results

```text
$ pytest -q tests/test_reclaim_barrier_event.py
.................                                                        [100%]
17 passed in 0.33s

$ pytest -q tests/test_runtime_kernel.py -k "unload or reclaim or ttl or restart"
............                                                             [100%]
12 passed, 13 deselected in 0.12s

$ pytest -q tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py
......................                                                   [100%]
22 passed in 0.33s

$ pytest -q tests/test_memory_pressure_contract.py tests/test_model_residency_policy.py tests/test_orchestration_status.py
...................                                                      [100%]
19 passed in 0.33s

$ pytest -q tests/test_runtime_server.py -k "reclaim_barrier or recovery_supervisor or scheduler_admission_contract or memory_pressure or orchestration_status"
...                                                                      [100%]
3 passed, 38 deselected in 0.31s

# Full server suite also run as a regression check (the prompt's -k
# filter matches only 3 tests because the cross-surface coverage lives
# inside test_reclaim_barrier_event.py):
$ pytest -q tests/test_runtime_server.py
.........................................                                [100%]
41 passed in 1.10s

$ pytest -q tests/test_reclaim_barrier_event.py tests/test_runtime_kernel.py \
            tests/test_recovery_supervisor_contract.py \
            tests/test_scheduler_admission_contract.py \
            tests/test_memory_pressure_contract.py \
            tests/test_model_residency_policy.py \
            tests/test_orchestration_status.py \
            tests/test_runtime_server.py
124 passed in 2.27s

$ python3 -m py_compile \
    owlmlx/reclaim_barrier_event.py \
    owlmlx/runtime/kernel.py \
    owlmlx/recovery_supervisor_contract.py \
    owlmlx/memory_pressure_contract.py \
    owlmlx/orchestration_status.py \
    owlmlx/runtime/server.py
compile OK

$ git diff --check
(clean, exit 0)
```

Substitution note: the §11 `tests/test_runtime_server.py -k` filter
returns only 3 tests because the new HTTP coverage lives inside
`tests/test_reclaim_barrier_event.py` (which exercises the route via
`TestClient`). The full unfiltered server file was also run (41 pass)
as a regression catch.

## 4. New Barrier Event Vocabulary

Surface: `owlmlx.reclaim_barrier_event` v1.

Operation vocabulary (`OPERATION_VOCABULARY`):

- `explicit_unload`
- `ttl_sweep_reclaim`
- `restart_unload_stage`
- `unknown`

Barrier state vocabulary (`BARRIER_STATE_VOCABULARY`):

- `clean`
- `failed_unload`
- `failed_reclaim`
- `restart_unload_failed`
- `unknown`

Each event carries:

- `event_id` (monotonic integer)
- `model_id`
- `operation`
- `source` (currently `"runtime_kernel"`)
- `stage` (currently `"backend_unload"`)
- `error_code`
- `message`
- `recorded_at_s`
- `requires_recovery_barrier`
- `resolved`

## 5. Runtime Operations Recording Failed Unload / Reclaim Events

| Path | Operation | Recorded When |
| --- | --- | --- |
| `RuntimeKernel.unload_model(model_id)` | `explicit_unload` | `backend.unload(model_id)` returns `ok=False` and `error_code` is **not** `model_not_loaded` |
| `RuntimeKernel.sweep_expired_models()` (TTL sweep of expired unpinned model) | `ttl_sweep_reclaim` | the inner `unload_model(..., _operation="ttl_sweep_reclaim")` reaches the backend cleanup boundary and fails (excluding `model_not_loaded`) |
| `RuntimeKernel.restart_model(model_id)` | `restart_unload_stage` | the unload step's `backend.unload(model_id)` returns `ok=False` and `error_code` is **not** `model_not_loaded` |

Pinned-policy unload blocks (`error_code = model_pinned`),
missing-model preflight (`error_code = model_not_loaded`), TTL-expired
**pinned** model skips, `over_budget` budget pressure without an
unload attempt, and restart visibility without a failed cleanup event
are intentionally **not** recorded as reclaim-failure barrier events.

## 6. Recovery / Admission / Orchestration Consumption

- `owlmlx.recovery_supervisor_contract`
  - reads `runtime_status["reclaim_barrier"]` through
    `build_reclaim_barrier_event(...)`
  - new recovery state `failed_reclaim_barrier` with
    `barrier_decision = "recovery_barrier_required"` whenever an
    unresolved event is visible
  - hard recovery barrier through the existing decision set; no
    duplicated lifecycle logic
- `owlmlx.scheduler_admission_contract`
  - already rejects on `recovery.barrier.hard_recovery_barrier == True`
    via its existing recovery hard-barrier path; the new recovery state
    rides that path without code change
- `owlmlx.orchestration_status`
  - `summary.bottleneck_layer = "recovery"` whenever
    `recovery.barrier.hard_recovery_barrier == True`; the new state
    flows through unchanged
- `owlmlx.memory_pressure_contract`
  - records visibility under
    `policy_boundaries.runtime_owned_reclaim_attempt_result_visibility`,
    while still keeping `runtime_owned_reclaim_barrier = False`,
    `runtime_owned_pressure_victim_selection = False`, and
    `pressure_ranked_eviction` / `reclaim_engine` in `out_of_scope`

## 7. HTTP Surface

`GET /v1/runtime/reclaim-barrier-event` — returns the read-only
contract serialization. It must not (and does not) clear events,
retry, or perform recovery. Verified by the route tests inside
`tests/test_reclaim_barrier_event.py`.

## 8. What Remains Unknown / Out Of Scope

Explicitly future-floor work, recorded as `missing_signals` /
`out_of_scope`:

- four-class termination-cause recovery policy
  (`retry / quarantine / surface_to_coordinator / drop`)
- frozen event resolution semantics (currently every event stays
  `resolved = False`; resolution belongs to the future 3.4 policy
  round)
- automatic recovery supervisor loop / background daemon
- automatic retry, quarantine execution, restart loops, operator
  remediation
- pressure-ranked victim selection / automatic unload under pressure
- stream-hold counters, durations, active stream-session tracking
- load-failure, OOM-class, and host-forensics termination causes
  beyond the cleanup-boundary unload stage
- worker-pollution detection beyond `abort_recovery` state

`reclaim_barrier_event` does **not** advance release floor `3.4` to
`closed`. It is the cleanup-boundary event-recording sub-round that
the future four-class policy will consume.

## 9. Floor 3.4 Status

`open`. `release-readiness-backlog.md` section 5 row `3.4 recovery
policy` was **not** modified. Per §9 of the 3.4A0 prompt and §4.2 of
the backlog, sub-round closure is not floor closure: the four-class
termination-cause policy plus exercised tests, plus event resolution
semantics, are still required.

## 10. Next Prompt Recommendation

`3.4A` — author the four-class termination-cause → four-action
recovery policy on top of the cleanup-boundary event truth introduced
here. Concrete shape suggested by the 3.4 pre-flight notes:

- consume `owlmlx.reclaim_barrier_event` events for the
  "graceful unload (when it fails)" cause class
- add load-failure and OOM-class event sources outside the unload
  stage (per the pre-flight notes' Question 1 framing of
  `restart_exhausted_models` as session-death-specific, not a general
  load-failure signal)
- freeze the four-action vocabulary
  (`retry / quarantine / surface_to_coordinator / drop`) and the
  cause→action mapping
- exercise the policy in tests, not only describe it
- decide event-resolution rules so the runtime can return to `clean`
  after a successful follow-up operation

Per the recoordination discipline, the coordinator should issue
exactly one next prompt. Do not run another executor in parallel
before the 3.4A prompt is authored.

## 11. Lane Constraints Confirmation

- **Pressure-ranked eviction not implemented**: confirmed.
  `memory_pressure_contract` boundaries still report
  `runtime_owned_pressure_victim_selection = False` and keep
  `pressure_ranked_eviction` in `out_of_scope`.
- **Automatic recovery supervisor not implemented**: confirmed. No
  background task, daemon, or scheduler runs anywhere in the new
  module; events are recorded synchronously at the operation boundary
  inside the calling kernel method only.
- **Stream-hold counters not implemented**: confirmed. No new
  `StreamEvent` field, no new gate counter, no new
  `_stream_with_background_producer` modification.
- **`GenerationGate` invariants preserved**: confirmed. No edits to
  `serving.py`, `runtime/kernel.py`'s `generate*` paths, or the
  pre-claim admission flow. The new module declares
  `max_concurrent_1_after_gate_claim`, `ticketed_fifo_after_gate_claim`,
  `no_post_claim_gate_bypass`, `no_hidden_retry_loop`,
  `no_automatic_recovery_supervisor_loop`, and
  `pinned_models_never_evicted` in `preserved_invariants`.
- **OwlOps / OwlCoda / desktop UI / `/Users/yeemio/AI/Agent` untouched**:
  confirmed. `git status -uno` shows only owlmlx-internal paths. No
  cross-repo edits.
- **Comparative evidence not touched**: confirmed. `comparative_evidence_*`
  modules and the OwlOps R156 surface are unchanged from
  `edcbc92`.
- **Floor `3.4` not marked closed**: confirmed.
  `release-readiness-backlog.md` row stays `open`. Outcome label is
  the prerequisite-introduced label, not a closure label.
- **Unrelated dirty/staged work preserved**: confirmed. `git diff
  --check` is clean. Pre-existing dirty paths from session start
  (README, phase45 docs, owlmlx/__init__.py, etc.) remain unstaged
  and unchanged by this round.
- **No release / parity / replacement / production-grade claim**:
  confirmed. The new doc explicitly disclaims all four; the
  execution-plan §6 update keeps the `does not close release floor 3.4`
  language.
