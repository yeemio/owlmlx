# owlmlx Execution Handoff 3.4A: Termination Recovery Policy

> Lane: single owlmlx executor (release floor 3.4 sub-round 3.4A on top of 3.4A0)
> Updated: 2026-04-27
> Active release floor: `3.4 Recovery Policy Closure` — **candidate closed, pending review**

## 1. Outcome Label

`owlmlx_release_floor_3_4A_termination_recovery_policy_candidate_closed_pending_review`

The four required termination cause classes plus a fail-safe `unknown`
map deterministically to one action each. Event resolution semantics
are runtime-owned. The policy is exercised in tests, not only
described. The literal `release-readiness-backlog.md` §3.4 prose
requirements appear to be met. Coordinator / reviewer must confirm
before the section-5 ledger row moves.

## 2. Changed Files

New runtime module:

- `owlmlx/termination_recovery_policy.py`
  - `TERMINATION_RECOVERY_POLICY_SURFACE = "owlmlx.termination_recovery_policy"`,
    `version = "v1"`
  - `TERMINATION_CAUSE_CLASSES`, `TERMINATION_RECOVERY_ACTIONS`,
    `REQUIRED_DECISION_FIELDS`, `DOMINANT_CAUSE_PRIORITY`
  - `build_termination_recovery_policy(...)`,
    `termination_recovery_policy_to_dict(...)`,
    `termination_cause_decision_to_dict(...)`
  - `TerminationRecoveryPolicy`, `TerminationCauseDecision`

Modified runtime modules (integration only):

- `owlmlx/runtime/kernel.py`
  - new `_load_failure_events: list[dict[str, Any]]` and
    `_load_failure_event_seq: int` instance state
  - new `_record_load_failure_event(...)` recorder
  - new `_resolve_matching_load_failure_events(model_id=...)` helper
  - new `_resolve_matching_reclaim_barrier_events(model_id, operations)`
    helper
  - new public `resolve_reclaim_barrier_event(event_id)` explicit
    override path (returns `{ok, already_resolved, event}` or
    `{ok=False, error_code="reclaim_barrier_event_not_found"}`)
  - `load_model(...)` now records `oom_class_failure` events for
    `memory_budget_exceeded` and `load_failure` events for backend
    failures (excluding `invalid_request` preflight and
    `model_already_loaded` redundant paths); successful load
    auto-resolves prior load_failure events for the same model id
  - `unload_model(...)` success now auto-resolves matching
    `explicit_unload` / `ttl_sweep_reclaim` reclaim-barrier events
  - `restart_model(...)` success now auto-resolves matching
    `restart_unload_stage` reclaim-barrier events
  - `status_dict()` exposes a new diagnostic section `load_failure`
    with `events`, `total_event_count`, `unresolved_event_count`; the
    `diagnostic_sections` list now includes `load_failure`
- `owlmlx/runtime/server.py`
  - new imports for `build_termination_recovery_policy`,
    `termination_recovery_policy_to_dict`
  - new route `GET /v1/runtime/termination-recovery-policy`

Tests:

- `tests/test_termination_recovery_policy.py` — 25 new tests covering
  vocabulary, every cause-to-action mapping, every active path,
  dominant-cause priority, resolution rules (auto + explicit),
  final-status-look-clean negative case, route coverage, recovery /
  admission / orchestration consumption, no-platform-dependency, and
  documentation of the unused `drop` action
- `tests/test_runtime_kernel.py` — updated `diagnostic_sections` pin
  to include `"load_failure"`
- `tests/test_runtime_server.py` — same `diagnostic_sections` pin
  update

Updated source-of-truth docs:

- `docs/source-of-truth/termination-recovery-policy.md` — **new**,
  frozen vocabulary / cause-to-action mapping / dominant priority /
  resolution rules / what-this-does-not-claim / out-of-scope
- `docs/source-of-truth/recovery-supervisor-contract.md` — §7 records
  that the four-class policy is now frozen by
  `termination-recovery-policy.md` while this contract still does
  not run any action
- `docs/source-of-truth/reclaim-barrier-event.md` — new §8
  "Event Resolution Semantics (3.4A)" describing auto-resolution and
  the explicit override path; renumbered §9 "What This Does Not
  Claim"
- `docs/source-of-truth/orchestration-status-surface.md` — §4
  recovery-layer note records that the cause-to-action policy is
  frozen with auto-resolution
- `docs/source-of-truth/runtime-status-schema.md` — new §18
  describing the `/v1/runtime/termination-recovery-policy` route
  and the `load_failure` diagnostic section
- `docs/source-of-truth/master-outline.md` — index entry 133 for
  `termination-recovery-policy.md`
- `docs/source-of-truth/release-readiness-execution-plan.md` — header
  date and §6 record the 3.4A closeout outcome and name a
  coordinator review as the next allocation; ledger row remains open
  pending that review

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A-termination-recovery-policy-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not**
modified per §9 — this round produces `candidate_closed_pending_review`
not `closed`. The section-5 row `3.4 recovery policy` stays `open`
until the coordinator/reviewer confirms.

## 3. Commands and Results

```text
$ pytest -q tests/test_termination_recovery_policy.py
.........................                                                [100%]
25 passed in 0.38s

$ pytest -q tests/test_reclaim_barrier_event.py
.................                                                        [100%]
17 passed in 0.67s

$ pytest -q tests/test_recovery_supervisor_contract.py \
            tests/test_scheduler_admission_contract.py \
            tests/test_orchestration_status.py
............................                                             [100%]
28 passed in 0.36s

$ pytest -q tests/test_runtime_kernel.py -k "load or unload or reclaim or restart or recovery"
.................                                                        [100%]
17 passed, 8 deselected in 0.57s

$ pytest -q tests/test_runtime_server.py -k "termination_recovery or reclaim_barrier or recovery_supervisor or orchestration_status"
...                                                                      [100%]
3 passed, 38 deselected in 0.32s

# Full server suite also run as a regression check (the §11 -k filter
# matches only 3 tests because the new HTTP coverage lives inside
# tests/test_termination_recovery_policy.py and
# tests/test_reclaim_barrier_event.py):
$ pytest -q tests/test_runtime_server.py
.........................................                                [100%]
41 passed in 1.16s

$ python3 -m py_compile \
    owlmlx/termination_recovery_policy.py \
    owlmlx/reclaim_barrier_event.py \
    owlmlx/runtime/kernel.py \
    owlmlx/recovery_supervisor_contract.py \
    owlmlx/orchestration_status.py \
    owlmlx/runtime/server.py
compile OK

$ git diff --check
(clean, exit 0)
```

Aggregate: 25 + 17 + 28 + 17 + 3 + 41 = 131 unique test executions
across the touched surfaces, all green. No substitution was needed —
the prompt's `-k` filter on `test_runtime_server.py` matched 3 of 41
tests and the full file was also run for regression catch.

## 4. Termination Cause Vocabulary

Frozen in `TERMINATION_CAUSE_CLASSES`:

- `load_failure`
- `oom_class_failure`
- `host_forensics_anomaly`
- `graceful_unload_failure`
- `unknown`

## 5. Action Vocabulary

Frozen in `TERMINATION_RECOVERY_ACTIONS`:

- `retry`
- `quarantine`
- `surface_to_coordinator`
- `drop`

## 6. Cause-To-Action Mapping

| Cause | Action | Source signal |
| --- | --- | --- |
| `load_failure` | `retry` | runtime-owned `load_failure` event from `RuntimeKernel.load_model` boundary (excluding `invalid_request` / `model_already_loaded` / `memory_budget_exceeded`) |
| `oom_class_failure` | `surface_to_coordinator` | runtime-owned `load_failure` event with `error_code = "memory_budget_exceeded"` (budget preflight) |
| `host_forensics_anomaly` | `surface_to_coordinator` | `abort_recovery.snapshot()` reports `state == "contaminated"` or `recovery_required == True`, OR `runtime_status.summary.backend_healthy == False` |
| `graceful_unload_failure` | `quarantine` | unresolved `owlmlx.reclaim_barrier_event` event |
| `unknown` | `surface_to_coordinator` | no runtime-owned status payload, or no decisive cause active (fail-safe) |

Dominant-cause priority when multiple are active (highest priority
first): `host_forensics_anomaly`, `graceful_unload_failure`,
`oom_class_failure`, `load_failure`, `unknown`.

`drop` is in the frozen vocabulary but no required cause maps to it
this round; the gap is recorded in
`missing_signals[layer="drop"]` so a future round can either map it
honestly or formally remove it from the action vocabulary.

## 7. Event Resolution Rules

Auto-resolution (primary path, runtime-owned, unconditional):

- `RuntimeKernel.unload_model(model_id)` success →
  resolves all unresolved reclaim-barrier events with matching
  `model_id` and `operation in {explicit_unload, ttl_sweep_reclaim}`
- `RuntimeKernel.restart_model(model_id)` success →
  resolves all unresolved reclaim-barrier events with matching
  `model_id` and `operation == restart_unload_stage`
- `RuntimeKernel.load_model(model_id)` success →
  resolves all unresolved load-failure events with matching `model_id`

Final-status look-clean alone never resolves an event. Verified by
`test_resolution_does_not_happen_from_final_status_alone`.

Explicit override (operator path):

- `RuntimeKernel.resolve_reclaim_barrier_event(event_id)` marks one
  specific reclaim-barrier event resolved without retrying or
  remediating; idempotent on already-resolved events; returns
  `{ok=False, error_code="reclaim_barrier_event_not_found"}` for
  unknown event IDs
- there is intentionally **no** `POST /v1/runtime/reclaim-barrier-event/resolve`
  HTTP write route in this round; the runtime method is sufficient
  for the tested flow, and adding a write route is left as future
  scope to keep this round's blast radius minimal
- there is no explicit `resolve_load_failure_event` method; load
  failures rely on auto-resolution by successful subsequent load

## 8. Write Routes Added

None at the HTTP layer. The only write surface introduced this round
is the kernel method
`RuntimeKernel.resolve_reclaim_barrier_event(event_id)` described in
§7. It does not retry, remediate, or re-execute the underlying
operation — it only marks an event resolved.

## 9. Recovery / Admission / Orchestration Consumption

Unchanged from 3.4A0. The new contract is an additional read-only
surface for upper layers; the existing recovery hard-barrier wiring
continues to drive admission and orchestration:

- `owlmlx.recovery_supervisor_contract` still reports
  `recovery_state = "failed_reclaim_barrier"` with hard recovery
  barrier whenever an unresolved `reclaim_barrier_event` event is
  visible
- `owlmlx.scheduler_admission_contract` still rejects via the
  existing `recovery.barrier.hard_recovery_barrier` path (no
  duplicated lifecycle logic)
- `owlmlx.orchestration_status` still reports
  `summary.bottleneck_layer = "recovery"` whenever the recovery
  contract is hard-blocked; verified by the cross-surface tests

`owlmlx.termination_recovery_policy` itself is consumed by upper
layers via `GET /v1/runtime/termination-recovery-policy`. It is
read-only.

## 10. Floor 3.4 Status

`candidate_closed_pending_review`. The `release-readiness-backlog.md`
section 5 row `3.4 recovery policy` is **not** moved by this round.

The literal `§3.4` requirements are now met by the conjunction of
3.4A0 (cleanup-boundary event surface) + 3.4A (cause-to-action policy
+ resolution rules):

- ✓ "one frozen recovery policy stating, per termination cause class,
  the runtime-owned next action
  (`retry / quarantine / surface_to_coordinator / drop`)"
- ✓ "coverage must include at least: load failure, OOM-class failure,
  host forensics anomaly, and graceful unload"
- ✓ "the policy must be exercised in tests, not only described"

Per §4.2 of the backlog, ledger movement requires implementation/truth
files changed (yes), tests/runtime checks ran (yes — 131 passes), an
honest verdict (yes — `candidate_closed_pending_review`), and
deferred scope stated (yes — see §11 below). Coordinator confirms.

## 11. Out Of Scope (Recorded As `missing_signals` / `out_of_scope`)

- background recovery supervisor daemon
- automatic retry / quarantine execution / drop / operator
  remediation workflows
- pressure-ranked victim selection or automatic unload under pressure
- stream-hold counters, durations, active stream-session tracking
- per-model load-attempt counters and load-attempt scheduling
- backend-side OOM events distinct from runtime budget preflight
- richer host-forensics signals beyond `abort_recovery` substrate
  state and backend health
- frozen `drop` action use-case for a required cause class
- HTTP write route for explicit reclaim-barrier resolution

## 12. Next Prompt Recommendation

The coordinator should issue a single 3.4 review / closeout prompt
(analogous to 3.2C) before moving the ledger. The reviewer should:

1. read `termination-recovery-policy.md`,
   `reclaim-barrier-event.md` (with new §8), and the kernel diff
2. run the full §11 verification matrix
3. verify the four required cause classes map deterministically and
   are exercised in tests
4. verify event resolution rules: auto-resolve on successful
   same-model follow-up, explicit override marks resolved without
   remediation, final-status look-clean alone never resolves
5. recommend either:
   - `closed_recommended` — coordinator flips
     `release-readiness-backlog.md` section 5 row `3.4` from `open`
     to `closed (via runtime-owned termination recovery policy)`
     with date `2026-04-27`, references to
     `reclaim-barrier-event.md`, `termination-recovery-policy.md`,
     `recovery-supervisor-contract.md`, the two test files, and the
     3.4A0 + 3.4A handoffs; section 2 floor count `3/7 → 4/7`
   - `still_progressed` / `needs_fix` with the exact remaining
     sub-blocker

After 3.4 closes, the next active floor by Stage 4 of the plan is
`3.5 Comparative Evidence` (measured-record sub-round on top of the
existing OwlOps R156 surface from `edcbc92`).

## 13. Lane Constraints Confirmation

- **No background daemon**: confirmed. No timer, no async task, no
  thread loop in any new module or kernel hook.
- **No automatic retry loop**: confirmed. The only resolution
  mechanisms are auto-resolve on observed successful follow-up
  (which the operator initiates) and explicit kernel override. The
  policy does **not** initiate any operation by itself.
- **No automatic quarantine execution**: confirmed.
  `graceful_unload_failure` maps to `quarantine` as a recommendation
  only; no kernel API marks any model as "quarantined" or excludes
  it from future operations.
- **No silent drop**: confirmed. `drop` is in vocabulary but no cause
  maps to it this round; the gap is recorded in `missing_signals`,
  not silently used.
- **`GenerationGate` invariants preserved**: confirmed. No edits to
  `serving.py`, `runtime/kernel.py`'s `generate*` paths, or the
  pre-claim admission flow. The new module declares
  `max_concurrent_1_after_gate_claim`, `ticketed_fifo_after_gate_claim`,
  `no_post_claim_gate_bypass`, `no_hidden_retry_loop`,
  `no_automatic_recovery_supervisor_loop`,
  `pinned_models_never_evicted`, and `no_pressure_ranked_eviction`
  in `preserved_invariants`.
- **No pressure-ranked eviction**: confirmed. Memory-pressure
  eviction policy is unchanged from `edcbc92`. The
  `runtime_owned_pressure_victim_selection` boundary in
  `memory_pressure_contract` is still `False`.
- **No stream-hold counter**: confirmed. No new `StreamEvent` field,
  no gate counter, no stream-session tracker.
- **OwlOps / OwlCoda / desktop UI / `/Users/yeemio/AI/Agent`
  untouched**: confirmed. `git status -uno` shows only
  owlmlx-internal paths. No cross-repo edits.
- **Comparative evidence not touched**: confirmed.
  `comparative_evidence_*` modules and the OwlOps R156 surface are
  unchanged from `edcbc92`.
- **Floor `3.4` not marked closed**: confirmed.
  `release-readiness-backlog.md` row stays `open`. Outcome label is
  `candidate_closed_pending_review`, not a closure label. The
  ledger row will move only after the coordinator/reviewer round.
- **Unrelated dirty/staged work preserved**: confirmed.
  `git diff --check` is clean. Pre-existing dirty/untracked paths
  from session start (README, phase45 docs, owlmlx/__init__.py,
  etc.) remain unchanged by this round.
- **No release / parity / replacement / production-grade claim**:
  confirmed. The new doc explicitly disclaims all four; the
  execution-plan §6 update keeps the
  `candidate_closed_pending_review` language and does not claim
  ledger movement.
