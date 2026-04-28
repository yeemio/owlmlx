# owlmlx Execution Prompt 3.4A: Termination Recovery Policy

> Date: 2026-04-26
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.4 Recovery Policy Closure`
> Lane: single active executor
> Role: implementation, tests, docs, and handoff
> Prerequisite: `3.4A0` introduced `owlmlx.reclaim_barrier_event`

## 1. Mission

Author the runtime-owned termination-cause recovery policy on top of the
cleanup-boundary event truth introduced by 3.4A0.

The required question is:

**Given a runtime-owned termination cause, what is the next safe
runtime-owned action: `retry`, `quarantine`, `surface_to_coordinator`, or
`drop`, and when may an unresolved reclaim-barrier event be marked resolved?**

This is still not a background recovery daemon. This round freezes policy and
the minimal operation-boundary resolution semantics needed for upper layers to
trust recovery posture. It must not implement automatic retry loops,
quarantine execution daemons, or operator remediation.

## 2. Coordination Truth

Verified current state:

- `3.1 Cache Scheduler Closure` is closed.
- `3.2 Memory-Pressure Decision Closure` is closed.
- `3.3 Model Residency Non-Resident Path` is closed.
- `3.4 Recovery Policy Closure` remains open.
- `3.4A0` introduced `owlmlx.reclaim_barrier_event`:
  - cleanup-boundary failures are recorded for explicit unload, TTL sweep
    reclaim, and restart unload stage
  - `recovery_supervisor_contract` reports `failed_reclaim_barrier`
  - admission and orchestration consume that hard recovery barrier through
    existing paths
  - event resolution remains future work

This round owns the next layer: termination-cause classification,
cause-to-action policy, and tested resolution rules.

## 3. Required Read Order

Read before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/reclaim-barrier-event.md`
5. `docs/source-of-truth/recovery-supervisor-contract.md`
6. `docs/source-of-truth/runtime-status-schema.md`
7. `docs/source-of-truth/orchestration-status-surface.md`
8. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event-handoff.md`
9. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4-pre-flight-notes.md`
10. `owlmlx/reclaim_barrier_event.py`
11. `owlmlx/recovery_supervisor_contract.py`
12. `owlmlx/runtime/kernel.py`
13. `owlmlx/runtime/types.py`
14. `owlmlx/runtime/backends.py`
15. `owlmlx/runtime/server.py`
16. Related tests:
    `tests/test_reclaim_barrier_event.py`,
    `tests/test_recovery_supervisor_contract.py`,
    `tests/test_scheduler_admission_contract.py`,
    `tests/test_orchestration_status.py`,
    `tests/test_runtime_kernel.py`,
    `tests/test_runtime_server.py`

## 4. Implementation Target

Preferred new runtime-owned contract:

- module: `owlmlx/termination_recovery_policy.py`
- surface: `owlmlx.termination_recovery_policy`
- route: `GET /v1/runtime/termination-recovery-policy`
- docs: `docs/source-of-truth/termination-recovery-policy.md`
- tests: `tests/test_termination_recovery_policy.py`

Required builder shape:

- `build_termination_recovery_policy(...)`
- `termination_recovery_policy_to_dict(...)`

The policy must consume runtime-owned truth only:

- `owlmlx.reclaim_barrier_event` for graceful-unload / cleanup-boundary
  failures
- runtime status load/restart/backend failure truth where already available
- explicit injected raw status in tests when the real backend cannot naturally
  produce a cause

Do not read OwlOps, OwlCoda, desktop UI, or `/Users/yeemio/AI/Agent`.

## 5. Required Vocabulary

Termination cause classes, minimum:

- `load_failure`
- `oom_class_failure`
- `host_forensics_anomaly`
- `graceful_unload_failure`
- `unknown`

Action vocabulary, exact:

- `retry`
- `quarantine`
- `surface_to_coordinator`
- `drop`

Each policy decision must include:

- `termination_cause_class`
- `next_action`
- `confidence`
- `reason_code`
- `source_signal`
- `operator_visible_message`
- `resolution_rule`
- `forbidden_automation`

Do not invent a broader vocabulary unless the doc and tests explain why.

## 6. Policy Requirements

The policy must freeze one next action for each required cause class.

Minimum honest rules:

- `graceful_unload_failure`
  - must consume unresolved `owlmlx.reclaim_barrier_event` events
  - must not resolve the event just because final status looks clean
  - must name a resolution rule tied to a successful follow-up operation
- `load_failure`
  - must not treat `restart_exhausted_models` as a general load-failure signal;
    pre-flight notes established it is session-death-specific
  - if no runtime-owned load-failure event source exists, the policy must either
    introduce one at the load operation boundary or classify the cause as
    `unknown` with a precise missing signal; do not fake it
- `oom_class_failure`
  - must distinguish memory budget / OOM-class failure from ordinary load
    failure where runtime-owned signals allow it
  - if the existing error code vocabulary is insufficient, add the smallest
    explicit classification needed and test it
- `host_forensics_anomaly`
  - must be surfaced to coordinator/operator; do not auto-retry or auto-drop
    host-forensics anomalies
- `unknown`
  - must fail safe and name the missing signal

The executor may choose the exact cause-to-action mapping, but every mapping
must be deterministic, documented, and tested. It is acceptable for more than
one cause class to map to the same action. It is not acceptable for a required
cause class to remain undocumented.

## 7. Resolution Rules

3.4A0 intentionally left reclaim-barrier events unresolved. This round must
freeze resolution semantics.

Minimum acceptable resolution behavior:

- a reclaim-barrier event may only become `resolved = True` after a
  runtime-owned successful follow-up operation on the same model / operation
  family
- resolution must be recorded as runtime truth, not reconstructed from final
  status after unrelated cleanup
- read-only policy routes must not clear events
- if the executor implements a write action, prefer a narrow runtime method and
  route such as:
  - `RuntimeKernel.resolve_reclaim_barrier_event(...)`
  - `POST /v1/runtime/reclaim-barrier-event/resolve`
- any write route must be explicit, tested, and must not retry or remediate
  work by itself

If event resolution cannot be implemented honestly in this round, return a
`policy_introduced_still_blocked_on_resolution` style handoff and keep floor
`3.4` open with the exact blocker.

## 8. Hard Rules

1. Do not implement a background recovery supervisor loop.
2. Do not implement automatic retry loops.
3. Do not execute quarantine automatically.
4. Do not silently drop requests without exposing policy truth.
5. Do not weaken `GenerationGate`, `ticketed_fifo`, `max_concurrent=1`, or
   post-claim serial execution.
6. Do not implement pressure-ranked eviction or automatic unload under
   pressure.
7. Do not implement stream-hold counters, durations, or active stream-session
   tracking.
8. Do not edit OwlOps, OwlCoda, desktop UI, or `/Users/yeemio/AI/Agent`.
9. Do not mark release floor `3.4` closed unless the full backlog §3.4
   requirement is met and the handoff explicitly recommends closure.
10. Preserve unrelated dirty/staged work.

## 9. Required Documentation Updates

Update or add source-of-truth docs:

- `docs/source-of-truth/termination-recovery-policy.md`
- `docs/source-of-truth/recovery-supervisor-contract.md`
- `docs/source-of-truth/reclaim-barrier-event.md`
- `docs/source-of-truth/orchestration-status-surface.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/release-readiness-backlog.md` only if the 3.4 row
  posture honestly changes
- `docs/source-of-truth/master-outline.md` if a new authoritative doc is added

Docs must state:

- the four termination cause classes
- the four action vocabulary values
- the cause-to-action mapping
- event resolution rules
- what remains out of scope
- whether release floor `3.4` remains open or is candidate-closed pending
  review

## 10. Required Tests

Add or update tests for:

- every termination cause class maps to exactly one action
- action vocabulary is exactly
  `retry / quarantine / surface_to_coordinator / drop`
- `graceful_unload_failure` consumes `owlmlx.reclaim_barrier_event`
- load failure is not inferred from `restart_exhausted_models` alone
- OOM-class failure is distinguishable or honestly blocked by a named missing
  signal
- host-forensics anomaly surfaces to coordinator/operator and does not
  auto-retry
- unknown cause fails safe
- resolution cannot happen from final status alone
- successful same-model follow-up operation can resolve the relevant event if
  resolution is implemented
- recovery/admission/orchestration surfaces reflect resolved vs unresolved
  state correctly
- route-level coverage for any new endpoint
- no platform dependency enters the new module

## 11. Required Verification

Run at minimum:

```bash
pytest -q tests/test_termination_recovery_policy.py
pytest -q tests/test_reclaim_barrier_event.py
pytest -q tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py tests/test_orchestration_status.py
pytest -q tests/test_runtime_kernel.py -k "load or unload or reclaim or restart or recovery"
pytest -q tests/test_runtime_server.py -k "termination_recovery or reclaim_barrier or recovery_supervisor or orchestration_status"
python3 -m py_compile \
  owlmlx/termination_recovery_policy.py \
  owlmlx/reclaim_barrier_event.py \
  owlmlx/runtime/kernel.py \
  owlmlx/recovery_supervisor_contract.py \
  owlmlx/orchestration_status.py \
  owlmlx/runtime/server.py
git diff --check
```

If a filter matches zero tests, run the relevant unfiltered test file and record
the substitution.

## 12. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A-termination-recovery-policy-handoff.md`

The handoff must include:

- outcome label
- changed files
- exact commands and results
- termination cause vocabulary
- action vocabulary
- cause-to-action mapping
- event resolution rules
- whether any write route was added and what it does
- how recovery/admission/orchestration consume the policy
- whether floor `3.4` remains open, is candidate-closed pending review, or is
  still blocked
- exact next prompt recommendation
- confirmation that no background daemon, automatic retry loop, automatic
  quarantine, pressure-ranked eviction, stream-hold counter, OwlOps, OwlCoda,
  or comparative-evidence work was touched

## 13. Allowed Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_4A_termination_recovery_policy_candidate_closed_pending_review`
- `owlmlx_release_floor_3_4A_termination_recovery_policy_introduced`
- `owlmlx_release_floor_3_4A_termination_recovery_policy_still_blocked`

Use `candidate_closed_pending_review` only if the implementation appears to
satisfy the literal `release-readiness-backlog.md` §3.4 requirement and needs
only coordinator/review confirmation before the ledger can move.

Use `introduced` if policy exists and is useful but one required cause,
action, resolution rule, or test condition remains open.

Use `still_blocked` if no honest runtime-owned policy can be frozen from
current signals.
