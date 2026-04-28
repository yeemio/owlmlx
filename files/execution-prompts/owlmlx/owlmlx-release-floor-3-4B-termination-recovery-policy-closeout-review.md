# owlmlx Execution Prompt 3.4B: Termination Recovery Policy Closeout Review

> Date: 2026-04-27
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.4 Recovery Policy Closure`
> Assigned executor: ClaudeCode
> Lane: single active executor
> Role: independent closeout reviewer and ledger decision
> Scope: review / verification / truth update only

## 1. Mission

Perform the independent closeout review for release floor `3.4 Recovery
Policy Closure`.

This round decides whether the combined `3.4A0` and `3.4A` work honestly
meets the literal `release-readiness-backlog.md` section `3.4`
requirement:

> one frozen recovery policy stating, per termination cause class, the
> runtime-owned next action (`retry / quarantine / surface_to_coordinator /
> drop`); coverage includes at least load failure, OOM-class failure, host
> forensics anomaly, and graceful unload; the policy is exercised in tests,
> not only described.

If and only if the evidence passes, move the section-5 ledger row for `3.4`
from `open` to `closed (via runtime-owned termination recovery policy)`.

Do not implement a new runtime feature in this round.
Do not start floor `3.5`.
Do not run a second executor in parallel.

## 2. Coordination Truth

Current frozen position:

- `3.1 Cache Scheduler Closure` is closed.
- `3.2 Memory-Pressure Decision Closure` is closed.
- `3.3 Model Residency Non-Resident Path` is closed.
- `3.4 Recovery Policy Closure` is candidate-closed pending review.
- `3.5 Comparative Evidence` remains open; the OwlOps R156 HTTP surface is
  mounted, but no same-host measured reference-runtime record exists yet.

`3.4A0` introduced:

- `owlmlx.reclaim_barrier_event`
- route `GET /v1/runtime/reclaim-barrier-event`
- operation-boundary cleanup failure events for explicit unload, TTL sweep
  reclaim, and restart unload stage
- recovery hard-barrier propagation through recovery supervisor, admission,
  and orchestration status

`3.4A` introduced:

- `owlmlx.termination_recovery_policy`
- route `GET /v1/runtime/termination-recovery-policy`
- runtime-owned load-failure event recording
- deterministic cause-to-action policy for:
  `load_failure`, `oom_class_failure`, `host_forensics_anomaly`,
  `graceful_unload_failure`, and `unknown`
- runtime-owned event resolution semantics:
  same-model successful follow-up operations auto-resolve matching events;
  `RuntimeKernel.resolve_reclaim_barrier_event(event_id)` provides explicit
  override; final-status look-clean alone never resolves

The executor reported:

- `tests/test_termination_recovery_policy.py`: `25 passed`
- `tests/test_reclaim_barrier_event.py`: `17 passed`
- recovery/admission/orchestration aggregate: `28 passed`
- filtered runtime kernel: `17 passed`
- filtered runtime server: `3 passed`
- full runtime server file: `41 passed`
- aggregate command set: `143 passed`
- `py_compile`: OK
- `git diff --check`: clean

Treat those as claims to reproduce or falsify, not as automatically accepted
truth.

## 3. Required Read Order

Read before deciding:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/reclaim-barrier-event.md`
5. `docs/source-of-truth/termination-recovery-policy.md`
6. `docs/source-of-truth/recovery-supervisor-contract.md`
7. `docs/source-of-truth/orchestration-status-surface.md`
8. `docs/source-of-truth/runtime-status-schema.md`
9. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event.md`
10. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event-handoff.md`
11. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A-termination-recovery-policy.md`
12. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A-termination-recovery-policy-handoff.md`
13. `owlmlx/reclaim_barrier_event.py`
14. `owlmlx/termination_recovery_policy.py`
15. `owlmlx/recovery_supervisor_contract.py`
16. `owlmlx/scheduler_admission_contract.py`
17. `owlmlx/orchestration_status.py`
18. `owlmlx/runtime/kernel.py`
19. `owlmlx/runtime/server.py`
20. Related tests:
    `tests/test_reclaim_barrier_event.py`,
    `tests/test_termination_recovery_policy.py`,
    `tests/test_recovery_supervisor_contract.py`,
    `tests/test_scheduler_admission_contract.py`,
    `tests/test_orchestration_status.py`,
    `tests/test_runtime_kernel.py`,
    `tests/test_runtime_server.py`

## 4. Review Questions

Answer each question with `yes`, `no`, or `not proven`, and cite file paths
plus line numbers where possible.

1. Does `3.4A0 + 3.4A` satisfy the literal backlog §3.4 requirement?
2. Is there one frozen recovery policy per termination cause class?
3. Are the required four cause classes covered:
   `load_failure`, `oom_class_failure`, `host_forensics_anomaly`, and
   `graceful_unload_failure`?
4. Is the action vocabulary exactly and consistently
   `retry / quarantine / surface_to_coordinator / drop`?
5. Does each active cause class map deterministically to one next action?
6. Is `drop` being unused for the required causes acceptable for this floor,
   because it is present in the vocabulary and explicitly recorded as a
   missing/future signal, rather than a closure blocker?
7. Is `load_failure` recorded from a runtime-owned load operation boundary
   and not inferred from `restart_exhausted_models` alone?
8. Is `oom_class_failure` distinguishable from ordinary load failure through
   runtime-owned error classification?
9. Does `host_forensics_anomaly` surface to coordinator/operator and avoid
   automatic retry or automatic drop?
10. Does `graceful_unload_failure` consume unresolved
    `owlmlx.reclaim_barrier_event` truth?
11. Are event resolution semantics runtime-owned, operation-boundary based,
    and safe?
12. Is final-status look-clean alone unable to resolve an event?
13. Are read-only routes truly read-only?
14. Were forbidden automations avoided:
    background supervisor loop, automatic retry loop, automatic quarantine
    execution, silent drop, pressure-ranked eviction, stream-hold counters,
    or GenerationGate weakening?
15. Are the policy and resolution behaviors exercised in tests, not only docs?
16. Do recovery, admission, and orchestration surfaces remain aligned after
    the policy and event-resolution additions?
17. Did the round stay inside `/Users/yeemio/AI/gitrep/owlmlx` without editing
    OwlOps, OwlCoda, desktop UI, or `/Users/yeemio/AI/Agent`?
18. Are there any stale docs that still say the recovery policy is incomplete
    in a way that contradicts the new 3.4A truth?

## 5. Required Verification

Run at minimum:

```bash
pytest -q tests/test_termination_recovery_policy.py
pytest -q tests/test_reclaim_barrier_event.py
pytest -q tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py tests/test_orchestration_status.py
pytest -q tests/test_runtime_kernel.py -k "load or unload or reclaim or restart or recovery"
pytest -q tests/test_runtime_server.py -k "termination_recovery or reclaim_barrier or recovery_supervisor or orchestration_status"
pytest -q tests/test_runtime_server.py
python3 -m py_compile \
  owlmlx/termination_recovery_policy.py \
  owlmlx/reclaim_barrier_event.py \
  owlmlx/runtime/kernel.py \
  owlmlx/recovery_supervisor_contract.py \
  owlmlx/orchestration_status.py \
  owlmlx/runtime/server.py
git diff --check
```

If a command is impossible to run, record the exact reason and do not claim
the evidence exists.

## 6. Allowed Edits

This is a closeout-review round. Allowed edits are limited to:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- narrow source-of-truth wording fixes needed to remove stale contradiction
  discovered during review
- a new handoff:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4B-termination-recovery-policy-closeout-review-handoff.md`

Do not edit runtime code or tests unless the review finds a blocking defect.
If a blocking defect exists, stop with `needs_fix` and describe the exact
executor-owned follow-up instead of quietly repairing it inside this review.

## 7. Ledger Decision Rule

If every required review question passes and verification is green:

- update `docs/source-of-truth/release-readiness-backlog.md` section 5 row
  `3.4 recovery policy`:
  - status: `closed (via runtime-owned termination recovery policy)`
  - date: `2026-04-27`
  - references should include at least:
    `reclaim-barrier-event.md`,
    `termination-recovery-policy.md`,
    `recovery-supervisor-contract.md`,
    `tests/test_reclaim_barrier_event.py`,
    `tests/test_termination_recovery_policy.py`,
    `owlmlx-release-floor-3-4A0-reclaim-barrier-event-handoff.md`,
    `owlmlx-release-floor-3-4A-termination-recovery-policy-handoff.md`,
    and this 3.4B handoff
- update `docs/source-of-truth/release-readiness-execution-plan.md`:
  - section 2 count: `3 / 7` -> `4 / 7`
  - record the 3.4B closeout outcome
  - set the next active floor to `3.5 Comparative Evidence`, specifically
    the measured same-host reference-runtime record sub-round

If any required review question fails:

- do not move the backlog ledger
- write the exact blocker and the smallest next executor prompt needed
- use `needs_fix` or `still_blocked`, not `closed`

## 8. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_4B_closeout_closed`
- `owlmlx_release_floor_3_4B_closeout_needs_fix`
- `owlmlx_release_floor_3_4B_closeout_still_blocked`
- `owlmlx_release_floor_3_4B_closeout_blocked_missing_evidence`

## 9. Required Handoff Shape

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-4B-termination-recovery-policy-closeout-review-handoff.md`

It must contain:

- outcome label
- verdict: `closed`, `needs_fix`, `still_blocked`, or
  `blocked_missing_evidence`
- review answers for all questions in section 4
- exact commands run and results
- files changed
- ledger decision
- next active floor if closed
- exact next prompt recommendation if not closed
- explicit statement that no runtime implementation was performed unless a
  blocking defect forced a stop

## 10. Hard Rules

- Do not mark floor `3.4` closed without green verification.
- Do not treat `candidate_closed_pending_review` as final closure.
- Do not start floor `3.5` implementation in this round.
- Do not create a second executor lane.
- Do not edit OwlOps, OwlCoda, desktop UI, or `/Users/yeemio/AI/Agent`.
- Do not promote any release, parity, replacement, or production-grade claim.
- Preserve unrelated dirty/staged work.
