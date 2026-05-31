# owlmlx Release-Readiness Backlog

> Status: authoritative
> Updated: 2026-04-28
> Scope: what `owlmlx` must close before any external release claim is honest

## 1. Purpose

This document freezes the honest gap between the current `owlmlx` state and any
external release claim. It is not a roadmap, not a marketing surface, and not a
parity claim. It exists because Phase 45 has accumulated enough exactness work
on narrow seams that the broader release-readiness picture must be tracked in
repository truth, not only in chat or planning notes.

It complements but does not replace:

- `replacement-grade-stability-gaps.md`
- `phase45-dominant-gap-reselection.md`
- `phase45-customer-runtime-evidence-ledger.md`
- `runtime-capability-matrix.md`

This document answers one narrow question:

**Given current frozen runtime truth, what must close before `owlmlx` can be
called a release rather than an internal source-of-truth project?**

## 2. Honest Top-Level Verdict

`owlmlx` is currently:

- a real runtime substrate with disciplined contracts
- frozen at `early_formal_runtime, below reference-grade stability`
- not in a state where any external release claim against `oMLX` or `vMLX`
  would be honest

Stating "ready for release" today would violate:

- `delivery-discipline.md` section 2.4 (scope must freeze before widening)
- `replacement-grade-stability-gaps.md` section 2 (no parity claim)

Release readiness is therefore a separate freeze, not an inferred consequence
of further seam exactness work.

## 3. Release Floor

The minimum release floor is the conjunction of all of the following. None is
sufficient alone.

### 3.1 Cache Scheduler Closure Beyond Exactness

Current state:

- the active seam is
  `owlmlx.cache_request_aggregation_active_seam`
- the active blocker is
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`
- exactness work continues to refine internal marker boundaries

Release-floor requirement:

- one closed non-exactness scheduler capability must exist on the active
  runtime path; for example one of:
  - one bounded request-aggregation cohort that produces an observable
    aggregated dispatch under repeated load, not only an exact handoff record
  - one bounded continuous-batching seam closed at the dispatch level, not
    only at the marker-discrimination level
- the closure must be visible in `tests/` under repeated runs, not only in
  marker-exactness assertions
- failing tests in the
  `test_cache_pre_gate_admission_window_seam_*` family must reach green or be
  honestly downgraded with a tracked reason

Until this is true, `closure_level` for cache remains
`aggregation_active_seam_exact` and release floor is not met.

### 3.2 Memory-Pressure Decision Closure

Current state per `memory-pressure-contract.md`:

- pressure is classifiable: `over_budget`, `near_budget`, `within_budget`
- the contract explicitly declines to:
  - select an eviction victim
  - execute eviction
  - respond to OS-level memory pressure events

Release-floor requirement:

- one runtime-owned decision surface that, given a pressure classification and
  a residency snapshot, yields a deterministic eviction-candidate ordering
- one runtime-owned execution path that performs the eviction and updates
  residency, lineage, and eviction-history governance surfaces atomically
- both surfaces must be tested with at least one repeated-load scenario where
  pressure transitions cause an observable residency change

Classification without decision is not release-grade; it is observability.

### 3.3 Model Residency Non-Resident Path

Current state per `model-residency-policy.md`:

- residency classes (`resident`, `pinned`, `ttl`, `evictable`) are owned
- non-resident target handling is explicitly unowned

Release-floor requirement:

- one runtime-owned surface that decides, for a non-resident target under a
  given budget and pressure state, one of:
  - admit and load
  - defer behind a named precondition
  - reject with a frozen reason
- the decision must be deterministic given the inputs and must round-trip
  through residency, lineage, and pressure surfaces

Without this, multi-model switching cannot honestly be called governed.

### 3.4 Recovery Policy Closure

Current state:

- termination-recovery state machine exists
- closed 2026-04-27 via the runtime-owned termination recovery policy
  (`owlmlx.termination_recovery_policy`) plus the cleanup-boundary event
  surface (`owlmlx.settle_barrier_event`); resolution semantics are
  runtime-owned and exercised in tests

Release-floor requirement:

- one frozen recovery policy stating, per termination cause class, the
  runtime-owned next action (retry / quarantine / surface to coordinator /
  drop)
- coverage must include at least: load failure, OOM-class failure, host
  forensics anomaly, and graceful unload
- the policy must be exercised in tests, not only described

Recovery without a closed policy means upper layers cannot trust the runtime
across restarts they did not cause.

### 3.5 Comparative Evidence Against Reference Runtimes

Current state:

- evidence is internal: Gemma mainline pilot PASS, Kimi heavy-boundary frozen
- closed 2026-04-28 via same-host measured comparative evidence against
  `omlx` for `workload_class = "single_prompt_short"` on
  `host_class = "Mac17,6-arm64-macOS-26.4.1-128GB"`; the record is
  schema-valid, HTTP-consumable, and backed by repeat-run raw artifacts

Release-floor requirement:

- at least one repeatable, in-repo benchmark harness that runs an identical
  workload against `owlmlx` and at least one reference runtime on the same
  host
- the harness must record: throughput, first-token latency, peak resident set,
  and a frozen verdict statement
- the verdict must not be auto-promoted to "parity" or "replacement"; the
  harness's only job is to make the comparison honest

Without comparative evidence the replacement claim is rhetoric, not truth.

### 3.6 External Customer Evidence

Current state:

- evidence ledger now contains one external deployment-boundary record
- closed 2026-04-28 via OwlOps-boundary external runtime-truth consumer
  evidence (host_class `Mac17,6-arm64-macOS-26.4.1-128GB`, workload_class
  `external_runtime_status_probe`, verdict `pass`); see
  `phase45-customer-runtime-evidence-ledger.md` §9 and the
  `20260428T025051Z` evidence directory

Release-floor requirement:

- at least one external deployment whose evidence is recorded in
  `phase45-customer-runtime-evidence-ledger.md` (or a successor ledger) with:
  - host class
  - workload class
  - frozen pass/fail verdict
  - one tracked external blocker or one frozen external success
- internal-only Gemma/Kimi evidence does not satisfy this floor

### 3.7 Public Surface Discipline

Current state:

- 134+ source-of-truth documents
- runtime surfaces stable enough to be referenced by upper layers
- closed 2026-04-28 via the runtime-owned `public-surface.md` freeze plus
  `tests/test_public_surface_contract.py` validation; the supported HTTP
  routes, Python modules, operator scripts, and source-of-truth contracts
  are exactly enumerated, and anything not listed is `internal` by default

Release-floor requirement:

- one frozen `public-surface.md` (or equivalent) that names exactly which
  modules, contracts, and CLIs are part of the supported release surface
- everything not on that list is internal and may change without notice
- the public surface must reference, not duplicate, existing source-of-truth
  documents

Releasing without a frozen public surface invites external consumers to depend
on internal seams and breaks the ownership boundary.

## 4. Hard Rules

### 4.1 Exactness Alone Is Not Release

Further refinement of stream-terminal marker discriminants does not reduce any
floor item in section 3. A round may be exactness-closed and still leave the
release floor untouched.

### 4.2 No Floor Item May Be Marked Closed Without All Four

Per `delivery-discipline.md` section 2.2, a floor item only closes when:

- implementation or truth files changed
- tests or live/runtime checks ran
- an honest verdict is stated
- deferred / blocked scope is stated

Documentation-only closure of a floor item is rejected.

### 4.3 No Replacement Claim Until Floor Closes

Until every item in section 3 is closed and section 5 records it, the
following claims remain dishonest:

- "release-ready"
- "replaces oMLX"
- "replaces vMLX"
- "parity"
- "production-grade"

Acceptable interim claims include:

- "early formal runtime"
- "internal source-of-truth project"
- "technical preview" (only if section 3.7 is closed)

### 4.4 Floor Order Is Not A Roadmap

Section 3 lists floor items in dependency-friendly order, not in execution
order. The dominant-gap reselection process owns execution order. This
document only freezes what must eventually be true.

## 5. Closure Ledger

This section records floor-item closure as it happens. Empty until a floor
item closes under section 4.2.

| Floor item | Status | Closed at | Reference |
| --- | --- | --- | --- |
| 3.1 cache scheduler closure | closed (non-stream main path) | 2026-04-25 | `release-floor-3-1-cache-scheduler-capability-audit.md`, `phase45-cache-pre-gate-admission-window-seam.md`, `phase45-request-aggregation-active-seam.md`, `tests/test_runtime_kernel.py::test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load` |
| 3.2 memory-pressure decision | closed (runtime-owned pressure eviction decision and execution) | 2026-04-26 | `memory-pressure-contract.md`, `memory-pressure-eviction-policy.md`, `model-residency-policy.md`, `nonresident-loadability-lineage.md`, `tests/test_memory_pressure_eviction_policy.py`, `owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`, `owlmlx-release-floor-3-2B-memory-pressure-eviction-review-handoff.md`, `owlmlx-release-floor-3-2C-independent-closure-review-and-ledger-decision-handoff.md` |
| 3.3 residency non-resident path | closed (via runtime-owned loadability lineage) | 2026-04-25 | `nonresident-model-admission-policy.md`, `nonresident-loadability-lineage.md`, `tests/test_nonresident_model_admission_policy.py`, `tests/test_nonresident_loadability_lineage.py`, `owlmlx-release-floor-3-3A2-nonresident-loadability-lineage-handoff.md`, `owlmlx-release-floor-3-3B3-loadability-lineage-closure-review-handoff.md` |
| 3.4 recovery policy | closed (via runtime-owned termination recovery policy) | 2026-04-27 | `reclaim-barrier-event.md`, `termination-recovery-policy.md`, `recovery-supervisor-contract.md`, `tests/test_settle_barrier_event.py`, `tests/test_termination_recovery_policy.py`, `owlmlx-release-floor-3-4A0-reclaim-barrier-event-handoff.md`, `owlmlx-release-floor-3-4A-termination-recovery-policy-handoff.md`, `owlmlx-release-floor-3-4B-termination-recovery-policy-closeout-review-handoff.md` |
| 3.5 comparative evidence | closed (via same-host measured comparative evidence) | 2026-04-28 | `comparative-evidence-harness-contract.md`, `comparative-evidence-schema-stub.md`, `tests/test_runtime_comparative_evidence_measured_runner.py`, `scripts/runtime_comparative_evidence.py`, `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl`, `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/manifest.json`, `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt`, `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt`, `owlmlx-release-floor-3-5E-codex-live-measured-run-rerun-handoff.md`, `owlmlx-release-floor-3-5F-comparative-evidence-closeout-review-handoff.md` |
| 3.6 external customer evidence | closed (via OwlOps-boundary external runtime-truth consumer evidence) | 2026-04-28 | `phase45-customer-runtime-evidence-ledger.md`, `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/`, `owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record-handoff.md`, `owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync-handoff.md` |
| 3.7 public surface | closed (via runtime-owned public-surface freeze) | 2026-04-28 | `public-surface.md`, `tests/test_public_surface_contract.py`, `owlmlx-release-floor-3-7A-public-surface-freeze-handoff.md`, `owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync-handoff.md` |

## 6. Restart Condition

This document is reopened only when:

- one floor item transitions to closed under section 4.2, or
- a floor item is honestly downgraded with a tracked reason, or
- a new release-blocking gap is identified that section 3 does not cover

This document is not reopened to relax floor items in response to schedule
pressure.
