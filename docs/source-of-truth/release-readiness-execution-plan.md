# owlmlx Release-Readiness Execution Plan

> Status: authoritative
> Updated: 2026-04-26 (3.2C closeout)
> Scope: execution plan for closing `release-readiness-backlog.md` floors

## 1. Purpose

This document turns `release-readiness-backlog.md` into an executable
burn-down plan.

It answers:

**What is the order of attack, what counts as progress, who owns each lane, and
what is the honest time/risk estimate before `owlmlx` can meet the release
floor?**

It does not relax the release floor.
It does not turn execution estimates into readiness claims.

## 2. Current Release Position

Current floor status:

- `3 / 7` release-floor items are closed:
  - `3.1` closed 2026-04-25 via the non-stream main runtime path;
    stream-branch dispatch remains the active phase45 seam, preserved as
    secondary truth
  - `3.3` closed 2026-04-25 via the runtime-owned non-resident loadability
    lineage contract (`owlmlx.nonresident_loadability_lineage`) consumed by
    `owlmlx.nonresident_model_admission_policy`; B3 review
    `owlmlx_release_floor_3_3B3_closure_review_pass_closed_recommended`
    confirmed the lineage round trip
  - `3.2` closed 2026-04-26 via the runtime-owned memory-pressure eviction
    decision contract (`owlmlx.memory_pressure_eviction_policy`) and the
    runtime-owned execution path
    (`RuntimeKernel.execute_memory_pressure_eviction`); 3.2C independent
    closeout review
    `owlmlx_release_floor_3_2C_independent_closeout_closed`
    resolved the 3.2B self-audit caveat
- `owlmlx` remains `early_formal_runtime, below reference-grade stability`
- no external release, parity, replacement, or production-grade claim is honest
- floor `3.4` has read-only pre-flight notes; implementation may now begin
  through one next prompt at coordinator authorization, since the `3.2`
  ledger decision is complete
- OwlOps R156 introduced an external live-upstream blocker: OwlOps local
  comparison wiring is waiting on `owlmlx` to implement and mount
  `/v1/runtime/comparative-evidence` plus
  `/v1/runtime/comparative-evidence/history`

The immediate correction is:

- stop treating new narrow exactness or side contracts as release progress by
  default
- require every active round to name one release floor
- require each round to either close, progress, or hard-block that floor with
  tests or live/runtime evidence

## 3. Ownership Model

Coordinator:

- owns floor ordering
- freezes the active floor before each round
- rejects work that does not reduce the active floor
- updates `release-readiness-backlog.md` only when the evidence threshold is met

Executor:

- owns implementation, docs, tests, and command evidence for the active floor
- may not switch floors without coordinator approval
- must report changed files, tests/live checks, verdict, and deferred scope

Reviewer:

- verifies the executor's claims against code, docs, tests, and live output
- must reject exactness-only progress if the floor requires runtime capability
- must reject release/parity wording until all floors close

### 3.1 Multi-Model Compute Scheduling Mapping

The previously discussed multi-model compute-scheduling problem is included,
but it is not a single isolated floor. It is a cross-cutting release gate across
four floor items:

- request / dispatch scheduling
  - release floor: `3.1 Cache Scheduler Closure`
  - required answer: which request may run next, and whether bounded
    aggregation or dispatch-level scheduling exists beyond marker exactness
- model placement and residency
  - release floor: `3.3 Model Residency Non-Resident Path`
  - required answer: when a target model is not resident, should the runtime
    admit-and-load, defer, or reject under current budget and pressure truth
- memory / residency sacrifice under pressure
  - release floor: `3.2 Memory-Pressure Decision Closure`
  - required answer: which resident model or cache state is sacrificed first,
    and whether the eviction/reclaim action updates runtime truth atomically
- recovery after failed scheduling cleanup
  - release floor: `3.4 Recovery Policy Closure`
  - required answer: what happens when unload, reclaim, restart, or recovery
    leaves the runtime in an unsafe state

This means multi-model compute scheduling is not considered closed until:

- admission can explain why a request runs now, waits, or fails
- non-resident model targets have deterministic load/defer/reject semantics
- memory pressure can choose and execute a victim transition
- recovery policy can fail closed after cleanup or restart failures
- tests or live/runtime evidence show these decisions under repeated or
  competing workload conditions

Current limitation:

- `owlmlx` does not yet own a separate CPU/GPU/Metal compute-capacity contract
  with per-model cost accounting, active compute-slot accounting, or fairness
  weights. The current plan treats compute scheduling through admission,
  residency, memory pressure, and recovery surfaces. If a later release target
  requires explicit Metal/compute accounting, this plan must add a new floor or
  split one out from floors `3.1` and `3.2`.

## 4. Execution Order

### Stage 0: Coordination Reset

Status:

- active now

Required result:

- `release-readiness-backlog.md` governs the loop
- side prompts are parked unless they directly reduce an active floor
- the next active prompt is floor `3.1`

Current active prompt:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`

Parked prompt:

- `files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`
  - useful later for floor `3.4`
  - not current active work

### Stage 1: Floor 3.1 Cache Scheduler Closure

Primary owner:

- executor

Reviewer owner:

- reviewer after executor produces changed files and verification output

Current A/B split:

- Executor A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A-pre-gate-test-truth-restoration.md`
  - owns the red pre-gate seam test family and any minimal implementation fix
    required to make that test truth honest
- Executor B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B-cache-scheduler-capability-audit.md`
  - owns independent non-exactness scheduler capability audit and evidence
    mapping, without editing A-owned code/tests
- Coordinator:
  - merges A's green/red gate result with B's capability audit before deciding
    whether floor `3.1` is closed, progressed, or still blocked

Next A/B split after the first A/B results:

- Executor A2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A2-repeated-dispatch-proof.md`
  - owns the smallest implementation/test proof for repeated-load
    non-exactness scheduler behavior, but only after A1 restores the red
    pre-gate test truth
- Executor B2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-floor-verdict-review.md`
  - owns read-only merge review of A1/A2/B1 evidence and the floor `3.1`
    verdict recommendation
- Coordinator:
  - does not mark floor `3.1` closed until A2 implementation evidence and B2
    review both satisfy the release-floor criteria

Closeout split after A2 evidence appears:

- Coordinator / Reviewer C:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-closeout-review-and-ledger-decision.md`
  - owns final floor `3.1` closure/progress/still-blocked decision
  - may update `release-readiness-backlog.md` only if the full section-3.1
    release-floor requirement is met
- Executor C-A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-A-verification-runner.md`
  - owns command verification and a read-only evidence handoff
  - must not edit release ledger docs
- Executor C-B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-B-ledger-truth-decision.md`
  - owns truth/ledger decision after C-A evidence exists
  - must not edit runtime code or tests

Why first:

- `phase45-dominant-gap-reselection.md` already selects
  `cache_scheduler_depth`
- active seam is `owlmlx.cache_request_aggregation_active_seam`
- current test gate is red:
  `pytest -q tests/test_cache_pre_gate_admission_window_seam.py` reports
  `3 failed, 2 passed`

Required deliverables:

- restore the `test_cache_pre_gate_admission_window_seam_*` family to truthful
  green or document a hard downgrade
- prove one non-exactness scheduler capability on the active runtime path, or
  identify the smallest missing runtime capability
- update release truth without marking floor closed unless section 3.1 of
  `release-readiness-backlog.md` is fully met

Expected effort:

- minimum: 1 round to restore test truth and produce a hard floor verdict
- likely: 2-4 rounds if observable aggregated dispatch under repeated load can
  be reached from existing runtime surfaces
- high-risk path: 5+ rounds if actual dispatch-level scheduler work is missing

Exit criteria:

- floor `3.1` closed, or
- an exact blocker exists in floor language with tests proving the blocker

Closeout (2026-04-25, Round C `owlmlx_release_floor_3_1C_closeout_closed`):

- floor `3.1` is closed via the non-stream main runtime path
  (`RuntimeKernel.generate` → `GenerationGate.execute_async_cohort_with_admission`
  → `backend.generate_cohort`) with repeated-load proof in
  `tests/test_runtime_kernel.py::test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load`
  and the bounded pre-gate cohort/aggregated child-exchange capability already
  proven by the existing harness tests
- stream-branch dispatch-level closure is **not** required for floor `3.1`
  closure under the backlog's literal "one closed non-exactness scheduler
  capability" language, but the stream-hold seam blocker
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`
  remains the active phase45 seam and stays preserved as secondary truth in
  `phase45-request-aggregation-active-seam.md`
- this closure does **not** imply release readiness, parity, replacement, or
  production-grade; floors `3.2`, `3.3`, `3.4`, `3.5`, `3.6`, `3.7` remain open

### Stage 2: Floors 3.3 Then 3.2

Order:

1. `3.3 Model Residency Non-Resident Path`
2. `3.2 Memory-Pressure Decision Closure`

Why this order:

- eviction decisions need a governed answer for non-resident targets and
  residency transitions
- pressure classification without residency action remains observability, not
  release behavior

Required deliverables for `3.3`:

- deterministic `admit_and_load / defer / reject` policy for non-resident
  target models under budget and pressure inputs
- round-trip through residency, lineage, and pressure surfaces

Current A/B split for `3.3`:

- Executor A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy.md`
  - owns the implementation, tests, runtime endpoint, source-of-truth doc, and
    handoff for the non-resident admission policy
- Executor B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B-residency-pressure-review.md`
  - owns scoped review of A's policy and evidence, with particular attention to
    residency/pressure/recovery boundaries and preventing accidental floor
    `3.2` eviction claims from being smuggled into `3.3`
- Coordinator:
  - may mark floor `3.3` closed only after A returns implementation evidence
    and B returns `pass`; otherwise record `progressed` or `still_blocked`
    with the exact missing runtime signal

Current post-A review step:

- Executor A returned
  `owlmlx_release_floor_3_3A_nonresident_admission_policy_progressed`
  after introducing `owlmlx.nonresident_model_admission_policy`,
  `GET /v1/runtime/nonresident-model-admission-policy`, docs, tests, and a
  handoff
- B's first handoff was a Pre-A audit map with
  `blocked_waiting_for_A`; it does not review A's implementation and must not
  be treated as the current floor verdict
- Reviewer B2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B2-post-A-nonresident-policy-review.md`
  - owns post-A review and must decide whether A's `progressed` verdict is
    valid, whether any needs-fix findings block it, and whether the next
    exact blocker is
    `runtime_owned_non_resident_loadability_lineage`

B2 result:

- B2 returned
  `owlmlx_release_floor_3_3B2_post_A_review_pass_progressed_confirmed`
- no blocking findings
- floor `3.3` remains `progressed`, not `closed`
- the confirmed next blocker is exactly
  `runtime_owned_non_resident_loadability_lineage`

Current A2 implementation step:

- Executor A2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A2-nonresident-loadability-lineage.md`
  - owns the runtime-owned non-resident loadability lineage contract and its
    integration into `owlmlx.nonresident_model_admission_policy`
  - must not implement automatic loading, pressure eviction, or any other floor

A2 round result (2026-04-25,
`owlmlx_release_floor_3_3A2_loadability_lineage_candidate_closed_pending_review`):

- new contract `owlmlx.nonresident_loadability_lineage` lives at
  `owlmlx/nonresident_loadability_lineage.py`, transport at
  `GET /v1/runtime/nonresident-loadability-lineage`, docs at
  `docs/source-of-truth/nonresident-loadability-lineage.md`,
  tests at `tests/test_nonresident_loadability_lineage.py`
- the contract returns exactly one of `known_loadable / not_loadable /
  unknown`, consumes `runtime_model_visibility` (registry + artifact gate)
  and `model_lineage` (validation + alignment), and rejects request-level
  hints as the source of truth
- `nonresident_model_admission_policy` now consumes the new contract; when
  `loadability_lineage` returns `known_loadable`, admission can produce
  `admit_and_load` without any `known_loadable_model_ids` hint, proven by an
  HTTP integration test
- `release-readiness-backlog.md` section 5 is **not** moved by A2; the row
  for `3.3` stays `open` until the next B review confirms closure

Current B3 closure-review step:

- Reviewer B3:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B3-loadability-lineage-closure-review.md`
  - should be run by an executor that did not author A2, to avoid self-review
  - owns independent verification of the loadability-lineage round trip and
    ledger recommendation
- if B3 confirms closure, the coordinator may flip
  `release-readiness-backlog.md` section 5 row `3.3` from `open` to
  `closed (via runtime-owned loadability lineage)`

B3 closeout (2026-04-25,
`owlmlx_release_floor_3_3B3_closure_review_pass_closed_recommended`):

- B3 ran via an independent reviewer context (not the A2 author) and
  produced
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B3-loadability-lineage-closure-review-handoff.md`
- B3 verdict: `pass`; recommendation: `closed_recommended`; aggregate
  123 tests pass, py_compile clean, `git diff --check` clean; all eight
  blocking-finding tripwires from B3 §4 held
- coordinator action applied 2026-04-25: section 5 row for `3.3` flipped
  from `open` to `closed (via runtime-owned loadability lineage)` with
  references to the lineage contract docs, the two test files, the A2
  handoff, and the B3 handoff; section 2 floor count moved from `1/7` to
  `2/7`
- this closure does **not** imply replacement-grade scheduler/cache
  closure or release readiness; floors `3.2`, `3.4`, `3.5`, `3.6`, `3.7`
  remain open

Required deliverables for `3.2`:

- deterministic eviction-candidate ordering under pressure
- runtime-owned execution path that updates residency and eviction history
- repeated-load test showing pressure causes observable residency change

Current A/B split for `3.2`:

- Executor A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution.md`
  - owns the decision surface, runtime execution path, docs, tests, and handoff
  - must preserve `GenerationGate` invariants and must not implement broad
    reclaim or automatic background eviction
- Reviewer B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review.md`
  - should be run by an executor that did not author A
  - owns scoped review of whether A really closed both decision and execution
    requirements, rather than merely improving pressure observability
- Coordinator:
  - may move floor `3.2` to `closed` only after A reaches candidate closure and
    B returns `pass_closed_recommended`

Expected effort:

- floor `3.3`: 2-4 rounds
- floor `3.2`: 3-6 rounds

Exit criteria:

- non-resident switching is governed
- pressure no longer stops at classification-only truth

### Stage 3: Floor 3.4 Recovery Policy Closure

Primary owner:

- executor

Inputs:

- existing `recovery_supervisor_contract`
- later use of the parked failed-unload/reclaim prompt if it still matches
  current truth
- pre-flight notes:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4-pre-flight-notes.md`

Required deliverables:

- frozen policy per termination cause class:
  `retry / quarantine / surface_to_coordinator / drop`
- coverage for load failure, OOM-class failure, host forensics anomaly, and
  graceful unload
- tests exercising the policy, not only docs

Sequencing decision after the 2026-04-26 recoordination pass:

- do not pre-split or pre-assign multiple 3.4 executors
- after `3.2C` closes, issue exactly one next prompt
- preferred next prompt: `3.4A0` as a failed-unload/reclaim barrier event
  sub-round, seeded by
  `files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`
- only after `3.4A0` returns should the coordinator decide whether the next
  single prompt is full four-class termination-cause policy work
- do not start any `3.4` implementation before the `3.2` ledger row closes

Expected effort:

- 3-5 rounds

Exit criteria:

- upper layers can trust runtime recovery posture across failures they did not
  cause

### Stage 4: Floor 3.5 Comparative Evidence

Primary owner:

- executor

Current parallel status:

- this stage may start as a schema/surface preparation lane while floor `3.1`
  remains the main release burn-down lane
- it must not mark floor `3.5` closed until the measured-record closure criteria
  in `comparative-evidence-harness-contract.md` section 8 are satisfied
- active prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5-comparative-evidence-schema-and-record-surface.md`
- external-blocker prompt for OwlOps R156:
  `files/execution-prompts/owlmlx/owlmlx-comparative-evidence-surface-for-owlops-r156.md`

Required deliverables:

- in-repo benchmark harness with identical workload against `owlmlx` and at
  least one reference runtime on the same host
- throughput, first-token latency, peak resident set, and frozen verdict
- verdict must not auto-promote to parity or replacement

Expected effort:

- 2-4 rounds if reference runtime invocation is already stable
- longer if the host/runtime setup is not reproducible

Exit criteria:

- replacement discussion is evidence-based, not rhetorical

### Stage 5: Floor 3.7 Public Surface

Primary owner:

- coordinator plus executor

Required deliverables:

- frozen `public-surface.md` or equivalent
- supported modules, contracts, and CLIs named exactly
- all non-listed surfaces explicitly internal

Expected effort:

- 1-2 rounds

Exit criteria:

- a technical-preview surface can be discussed without exposing internal seams

### Stage 6: Floor 3.6 External Customer Evidence

Primary owner:

- coordinator for evidence requirement
- external deployment owner for real-world run
- executor only for instrumentation/supporting fixes

Required deliverables:

- at least one external deployment evidence record with host class, workload
  class, frozen pass/fail verdict, and blocker/success outcome

Expected effort:

- cannot be honestly estimated from repo-only work
- earliest start should be after floors `3.1`, `3.3`, and `3.4` have enough
  closure to make an external run meaningful

Exit criteria:

- external evidence exists in the ledger

## 5. Time Estimate

These are round estimates, not readiness promises.

Assuming one focused executor round is about 2-3 hours:

- fastest meaningful internal technical-preview floor burn-down:
  12-20 focused rounds
- realistic internal release-floor burn-down:
  18-30 focused rounds
- full release floor including external evidence:
  cannot be promised until an external deployment owner and host are assigned

Calendar estimate if execution is continuous:

- internal floor closure: roughly 1-3 focused weeks depending on whether floor
  `3.1` and floor `3.2` require new runtime implementation
- external release claim: gated by floor `3.6`; no honest date yet

The main schedule risks are:

- `3.1` may reveal that observable aggregated dispatch does not exist yet
- `3.2` may require real eviction execution, not only ordering
- `3.6` depends on non-repo external deployment evidence

## 6. Immediate Next Step

Parked external dependency prompt:

- OwlOps R156 is blocked on a live upstream `owlmlx` comparative evidence
  endpoint, not on OwlOps local wiring
- archived owlmlx-side prompt:
  `files/execution-prompts/owlmlx/owlmlx-comparative-evidence-surface-for-owlops-r156.md`
- do not assign OwlOps until this surface is live-curl verified
- this does not automatically close release floor `3.5`; measured same-host
  evidence is still required for floor closure
- this prompt is not the current release burn-down executor allocation after
  the 3.2C closeout

Floors `3.1` and `3.3` closed on 2026-04-25. Floor `3.2` closed on
2026-04-26 via the 3.2C independent closeout review
(`owlmlx_release_floor_3_2C_independent_closeout_closed`). The
release-readiness burn-down active floor is now
`3.4 Recovery Policy Closure` per Stage 3 of this plan. The current single
active executor allocation is:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event.md`

Do not run another executor in parallel. After 3.4A0 returns, re-coordinate
from its handoff before issuing the next prompt.

The `3.2` A/B prompts exist:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review.md`

A round result (2026-04-26,
`owlmlx_release_floor_3_2A_memory_pressure_eviction_candidate_closed_pending_review`):

- new contract `owlmlx.memory_pressure_eviction_policy` lives at
  `owlmlx/memory_pressure_eviction_policy.py`, decision transport at
  `GET /v1/runtime/memory-pressure-eviction-policy`, execution transport at
  `POST /v1/runtime/memory-pressure-eviction`, docs at
  `docs/source-of-truth/memory-pressure-eviction-policy.md`, tests at
  `tests/test_memory_pressure_eviction_policy.py`
- the contract returns exactly one of `evict / defer / reject / unknown`,
  consumes `memory_pressure_contract` (pressure classification),
  `model_residency_policy` (resident inventory, active model id), and
  `recovery_supervisor_contract` (hard recovery barriers); it never
  invents OS-level pressure events
- candidate ordering is deterministic: unpinned-first → ttl-expired
  unpinned → non-active-protected → larger memory → lexical model_id
- new runtime-owned execution path
  `RuntimeKernel.execute_memory_pressure_eviction(...)` refuses execution
  unless `decision == "evict"`, unloads the selected victim through
  existing `unload_model` semantics, records an eviction-history event
  with `source = "memory_pressure_policy"`, returns a structured result
  with decision snapshot, victim, unload result, residency after-state,
  and the recorded event; pinned models remain double-protected by the
  unload-side pin check
- when the loadability lineage registry is connected at `create_app(...)`,
  the POST endpoint also includes `loadability_lineage_after` for the
  evicted model
- repeated-pressure scenario test
  (`tests/test_memory_pressure_eviction_policy.py
  ::test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`)
  proves observable residency change across rounds with two
  `memory_pressure_policy` events accumulating in eviction history
- `release-readiness-backlog.md` section 5 is **not** moved by A; the
  `3.2` row stays `open` until B review confirms closure

B self-audit result (2026-04-26,
`owlmlx_release_floor_3_2B_review_pass_closed_recommended`):

- B confirmed the A implementation against the 3.2 review checklist and
  re-ran the focused suites, with all reported checks passing
- however, B disclosed that it was authored by the same Opus instance as A
  after an explicit one-round override; the B handoff therefore recommends a
  non-Opus second review before the coordinator flips the ledger

3.2C closeout (2026-04-26,
`owlmlx_release_floor_3_2C_independent_closeout_closed`):

- 3.2C ran via an independent fresh `claude-opus-4-7` instance that did not
  author 3.2A or the 3.2B self-audit; the prompt's recommended `gpt-5.4`
  was not used and the handoff records this as a cross-instance rather
  than cross-family independence guarantee
- 3.2C verified all 14 closure questions, ran the full verification matrix
  (16 + 16 + 28 + 8 + 37 tests pass; py_compile clean; `git diff --check`
  clean), and confirmed the implementation closes both decision and
  execution requirements without weakening serial runtime invariants
- coordinator action applied 2026-04-26: section 5 row for `3.2` flipped
  from `open` to
  `closed (runtime-owned pressure eviction decision and execution)`
  with references to the eviction policy contract, the four supporting
  source-of-truth docs, the test file, and the 3.2A / 3.2B / 3.2C
  handoffs; section 2 floor count moved from `2/7` to `3/7`
- this closure does **not** imply replacement-grade scheduler/cache
  closure or release readiness; floors `3.4`, `3.5`, `3.6`, `3.7`
  remain open

Recoordination packet:

- `files/execution-prompts/owlmlx/owlmlx-release-readiness-recoordination-2026-04-26.md`

Next active floor:

- `3.4 Recovery Policy Closure`

The coordinator should issue exactly one next prompt at this time per the
single-active-executor rule. The preferred next prompt is `3.4A0` as a
failed-unload/reclaim barrier event sub-round, seeded by
`files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`.

The 3.4 pre-flight notes are accepted only as preparation. The 3.4A0 prompt
above is the actual implementation authorization.

## 7. Stop / Escalation Conditions

Stop and escalate when:

- a floor requires product/business priority rather than runtime truth
- external evidence is the only remaining blocker
- a runtime change would weaken serial safety invariants
- the executor cannot reduce a floor after one focused diagnosis round

Do not stop merely because a prompt was archived.
Prompt archival is coordination, not delivery.
