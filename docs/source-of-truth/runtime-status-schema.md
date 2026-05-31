# owlmlx Runtime Status Schema

> Status: authoritative
> Updated: 2026-05-05

## 1. Purpose

This document defines the runtime-owned schema boundary for the status surfaces
that `owlmlx` expects upper layers to consume.

## 2. Core Runtime Status Schema

The core runtime status schema is the owned shape for general runtime truth.

### 2.1 Required Semantic Fields

| Field | Meaning |
|---|---|
| `runtime` | runtime identity |
| `status` | current health or availability state |
| `load_state` | whether runtime or model is loaded, loading, idle, or unavailable |
| `memory_active` | active memory footprint |
| `memory_budget_gb` | runtime memory budget when defined |
| `model_memory_utilization` | budget-relative utilization when computable |
| `queue_state` | active or waiting work when applicable |
| `truth_level` | how direct the runtime truth is |

### 2.2 Optional Semantic Fields

| Field | Meaning |
|---|---|
| `memory_peak` | peak memory usage |
| `cache_truth` | owned cache visibility or reuse state |
| `restart_requested` | runtime-level restart request |
| `loaded_model_count` | number of loaded models when the runtime is multi-model |
| `loaded_model_details` | per-model runtime detail when available |

## 3. Large-Weight Runtime Path Status Schema

This schema is owned by `owlmlx` as a path-level status contract.

### 3.1 Required Semantic Fields

| Field | Meaning |
|---|---|
| `runtime` | runtime identity for the path |
| `path_variant` | owned runtime-path variant name |
| `status` | current runtime state |
| `model` | current specimen or model identity |
| `tier` | serving tier, currently background |
| `interactive_status` | honest interaction posture |
| `lifecycle_mode` | manual, managed, or other lifecycle posture |
| `memory_active` | active memory footprint |
| `memory_budget_gb` | path-specific memory budget |

### 3.2 Optional Semantic Fields

| Field | Meaning |
|---|---|
| `memory_peak` | peak memory usage |
| `layers` | structural layer count |
| `layout` | path-specific artifact layout |
| `fuse_eval` | runtime optimization flag |
| `cache_entries` | cache occupancy |
| `cache_size_gb` | cache size |
| `cache_pinned` | pinned cache count |
| `prefill_baseline` | prefill baseline evidence |
| `decode_baseline` | decode baseline evidence |
| `uptime_s` | runtime uptime |

## 4. Contract Interpretation Rules

- `interactive_status` is an honesty field, not a marketing field.
- `path_variant` belongs to runtime truth, not only to shell labeling.
- `memory_*` fields are runtime facts, not UI estimates, when sourced directly.
- A missing optional field must not be misread as capability support.

## 5. Extraction Direction

The platform shell can keep transport and presentation endpoints, but the schema
definitions above should become the reference point for:

- router proxy responses
- dashboard proxy responses
- snapshot embedding
- contract tests

## 6. Stabilization-1 Contract Freeze

From Stabilization-1 onward, `/v1/runtime/status` is split into:

- stable contract sections:
  - `contract`
  - `summary`
  - `health`
  - `inventory`
  - `budget`
  - `restart`
- diagnostic sections:
  - `backend.detail`
  - `governance_observations`
  - `governance_policy`
  - `generation_gate`
  - `reclaim_barrier`
  - `load_failure`
  - `memory_pressure_cooldown`
  - `host_pressure`
  - `session_kv_cache`

The stable sections are intended for long-lived `owlcoda` / `owlops` consumption.
The diagnostic sections remain useful, but upper layers must treat them as best-effort detail rather than field-stable compatibility promises.

`backend.detail.dead_registered_models` is a diagnostic recovery signal for
subprocess-backed runtimes. It lists model ids whose runtime registration still
exists after the child process/session is gone. Operators may use it to surface
ghost-state recovery needs, but product layers must not treat those entries as
live loaded models.

`memory_pressure_cooldown` is a diagnostic admission signal. It is active when
the kernel has observed backend evidence of a Metal insufficient-memory
child-loss failure and is refusing new model loads for a bounded cooldown
window. It is not a full operating-system pressure oracle.

`host_pressure` is a diagnostic load-admission sample. It is taken before model
load attempts from host-visible macOS memory-pressure output and cached into
status. It may block a new load when free host memory crosses the runtime-owned
threshold, but it is not private Metal allocator or command-queue pressure
truth.

`backend.detail.session_kv_cache` is a diagnostic native-backend cache payload.
It is experimental, default-off, and scoped to explicit `X-Owlmlx-Session-Id`
callers. Product layers must not treat its presence as support for paged KV,
continuous batching, implicit prefix matching, or subprocess cache reuse.

`GET /healthz` is also frozen as a smaller liveness contract in Stabilization-1:

- `contract.surface`
- `contract.version`
- `runtime`
- `backend_name`
- `ok`
- `readiness`
- `active_model_id`
- `model_count`

## 7. Stabilization-2 Runtime-Owned Readiness Surfaces

Stabilization-2 introduces two additional runtime-owned machine/operator
surfaces that sit alongside runtime status:

- `owlmlx.mlx_environment`
  - readiness for safe `mlx_lm` subprocess use on the current machine
- `owlmlx.mlx_blocker_report`
  - machine-level summary when no usable MLX baseline exists

These are not replacements for `/v1/runtime/status`. They are narrower,
runtime-only preparation contracts for large-weight specimen work.

## 8. Stabilization-3 Runtime-Owned First-Smoke Decision Surface

Stabilization-3 adds one further runtime-owned machine/operator surface:

- `owlmlx.large_weight_first_smoke_decision`
  - a locality decision for large-weight first smoke
  - combines:
    - `default_metal` specimen gate
    - `force_cpu` specimen gate
    - host-level crash forensics

This surface exists so `owlmlx` can answer one narrow question honestly:

- should first smoke proceed on this host
- or should first smoke move to another host/system image

This is still not a replacement verdict. It is a runtime-only handoff
decision for large-weight validation.

## 9. Phase 45 Replacement-Grade Stability Surfaces

Phase 45 adds two narrower runtime-owned surfaces that support
replacement-grade stability alignment without claiming parity:

- `owlmlx.host_stable_execution`
  - direct host-level answer for whether this machine is a valid candidate for
    deeper runtime validation
- `owlmlx.cache_scheduler_status`
  - direct runtime-owned answer for current cache/scheduler closure depth
- archived `owlmlx.cache_residency_evidence` scaffold; live cache counters are
  exposed by `owlmlx.cache_manager`
  - direct runtime-owned answer for current cache residency/reuse evidence rung
- `owlmlx.cache_repeatability_evidence`
  - direct runtime-owned answer for repeated-serving cache evidence rung
- `owlmlx.turboquant_readiness`
  - direct runtime-owned answer for whether TurboQuant is still safety-blocked,
    evidence-blocked, or ready for controlled validation
- `owlmlx.cache_closure_rung`
  - direct runtime-owned answer for the current conservative cache closure rung
- `owlmlx.cache_counter_gap`
  - direct runtime-owned answer for whether the remaining cache blocker has narrowed to an exact counter-grade gap
- `owlmlx.cache_counter_feasibility`
  - direct runtime-owned answer for which cache counters are actually owned on the current path and which remaining cache work has shifted to scheduler/TurboQuant closure
- `owlmlx.cache_scheduler_turboquant_split`
  - direct runtime-owned answer for whether the remaining cache closure has now split cleanly between scheduler depth and TurboQuant preconditions
- `owlmlx.cache_scheduler_floor_gap`
  - direct runtime-owned answer for the exact scheduler-grade floor on the active cache path once the split is already exact
- `owlmlx.cache_scheduler_implementation_backlog`
  - direct runtime-owned answer for the exact scheduler implementation work that remains once the serial floor is already exact
- `owlmlx.cache_scheduler_branch_selection`
  - direct runtime-owned answer for which scheduler branch should be worked next once the backlog is already exact
- `owlmlx.cache_continuous_batching_feasibility`
  - direct runtime-owned answer for whether continuous batching is merely absent or is exact-feasibility-blocked on the active path
- `owlmlx.cache_batching_mechanism_subgap`
  - direct runtime-owned answer for which missing batching mechanism is the next exact local subgap once continuous batching is already proven structurally blocked
- `owlmlx.cache_request_aggregation_window_exactness`
  - direct runtime-owned answer for the exact ingress and dependency blockers underneath request aggregation once that mechanism is already selected
- `owlmlx.cache_pre_gate_cohort_window_feasibility`
  - direct runtime-owned answer for whether owlmlx owns any cohort/admission seam before whole-request gate claim on the active path
- `owlmlx.cache_pre_gate_admission_hook_exactness`
  - direct runtime-owned answer for whether any bounded hook exists before whole-request gate claim and which post-claim invariants must remain untouched
- `owlmlx.cache_admission_hook_safety_contract`
  - direct runtime-owned answer for the exact post-claim invariants and forbidden bypasses any future pre-claim hook must preserve
- `owlmlx.cache_structural_ingress_seam`
  - direct runtime-owned answer for whether one bounded pre-gate hook now exists in the live runtime path
  - this surface may only claim `structural_ingress_seam_introduced`
  - it must not claim request aggregation, continuous batching, or cache parity
- `owlmlx.cache_pre_claim_admission_contract`
  - direct runtime-owned answer for the only allowable future pre-claim seam and the forbidden actions that must stay outside that seam
- `owlmlx.cache_pre_claim_staging_seam_exactness`
  - direct runtime-owned answer for which exact metadata/ticket units may be staged pre-claim and which expansions must remain outside that seam
- `owlmlx.cache_pre_claim_metadata_ticket_ownership`
  - direct runtime-owned answer for the exact ownership/lifetime boundary of pre-claim ticket reservation and immutable metadata snapshot
- `owlmlx.cache_pre_claim_inert_state_semantics`
  - direct runtime-owned answer for which inert cohort/drop semantics may exist before gate claim and which ones must remain unavailable
- `owlmlx.cache_pre_claim_marker_lifetime`
  - direct runtime-owned answer for how long inert drop/cancel markers may exist before gate claim and which promotions remain forbidden across that lifetime
- `owlmlx.cache_pre_claim_marker_visibility`
  - direct runtime-owned answer for which pre-claim paths may observe/clear inert markers and which visibility expansions remain forbidden
- `owlmlx.cache_pre_claim_marker_trigger_inputs`
  - direct runtime-owned answer for which exact pre-claim inputs may clear inert markers and which trigger families remain unavailable before gate claim
- `owlmlx.cache_pre_claim_marker_reader_writer_ownership`
  - direct runtime-owned answer for which exact pre-claim paths may author a marker, which may only observe it, and which writer ownership remains unavailable before gate claim
- `owlmlx.cache_pre_claim_marker_state_carrier`
  - direct runtime-owned answer for the exact inert carrier that may hold a marker before gate claim and which carrier semantics must remain unavailable until whole-request gate claim
- `owlmlx.cache_pre_claim_marker_clear_observer_boundary`
  - direct runtime-owned answer for which exact pre-claim paths may clear the inert marker carrier, which may only observe it, and which clearer ownership remains unavailable before gate claim
- `owlmlx.cache_pre_claim_marker_immutability_boundary`
  - direct runtime-owned answer for whether pre-claim marker state may mutate beyond clear-only semantics and which mutation expansions must remain unavailable before gate claim
- `owlmlx.multi_model_ttl_policy_control`
  - direct runtime-owned answer for whether TTL policy exists on the runtime-owned path, whether explicit expiry sweep is visible, and whether pinned expiry remains blocked without inflating eviction-history governance
- `owlmlx.multi_model_eviction_history_governance`
  - direct runtime-owned answer for whether eviction history is visible on the runtime-owned path and whether both TTL unload and pinned-expiry skip events are frozen strongly enough to close the local policy branch
- `owlmlx.cache_pre_claim_marker_payload_shape_exactness`
  - direct runtime-owned answer for whether pre-claim marker state carries any payload fields at all before gate claim or collapses to pure presence/absence only
- `owlmlx.cache_pre_claim_marker_encoding_carrier_exactness`
  - direct runtime-owned answer for what exact inert carrier holds the pre-claim presence/absence bit and which identity/handle encodings remain unavailable before gate claim
- `owlmlx.cache_pre_claim_marker_storage_locality_exactness`
  - direct runtime-owned answer for where that inert boolean marker slot may live relative to staged metadata/ticket units and which ownership-bearing localities remain unavailable before gate claim
- `owlmlx.cache_pre_claim_marker_locality_access_exactness`
  - direct runtime-owned answer for which exact pre-claim paths may reach that adjacent inert slot and which locality-access expansions remain unavailable before gate claim
- `owlmlx.cache_pre_claim_marker_locality_isolation_exactness`
  - direct runtime-owned answer for whether that adjacent inert slot is isolated per staged request or whether any shared pending-state locality remains before gate claim
- `owlmlx.cache_pre_claim_marker_locality_lifetime_coupling`
  - direct runtime-owned answer for whether that isolated adjacent marker slot is coupled only to its own staged-request lifetime, reclaimed only by same-request pre-claim discard / gate-claim expiry, and kept free of retained ownership before gate claim
- `owlmlx.cache_pre_claim_marker_reclaim_reset_exactness`
  - direct runtime-owned answer for whether reclaim returns that adjacent marker slot to a fully inert empty state before any later staged request may reuse that locality
- `owlmlx.cache_pre_claim_admission_carrier_construction`
  - direct runtime-owned answer for whether any bounded pre-claim admission carrier may exist and which already-frozen inert units alone may construct it before gate claim
- `owlmlx.cache_pre_claim_admission_carrier_field_exactness`
  - direct runtime-owned answer for which exact inert fields may inhabit that bounded pre-claim carrier before gate claim
- `owlmlx.cache_pre_claim_admission_carrier_encoding_exactness`
  - direct runtime-owned answer for how those inert fields may be encoded together before gate claim without becoming queue- or execution-bearing
- `owlmlx.cache_pre_claim_admission_carrier_locality_exactness`
  - direct runtime-owned answer for where that bounded inert pre-claim record may live before gate claim without becoming queue-, scheduler-, child/stream-, or execution-owned locality
- `owlmlx.cache_pre_claim_admission_carrier_locality_access_exactness`
  - direct runtime-owned answer for which exact pre-claim paths may reach that bounded inert pre-claim carrier before gate claim without becoming queue-, scheduler-, backend-, stream-, or execution-bearing access
- `owlmlx.cache_pre_claim_admission_carrier_locality_isolation_exactness`
  - direct runtime-owned answer for whether that bounded inert pre-claim carrier remains isolated per staged request before gate claim without becoming shared pending-state locality
- `owlmlx.cache_pre_claim_admission_carrier_locality_lifetime_coupling`
  - direct runtime-owned answer for how that isolated bounded inert pre-claim carrier couples to same-request lifetime and reclaim/expiry before gate claim without becoming retained or cross-request lifetime
- `owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness`
  - direct runtime-owned answer for what exact empty inert state reclaim resets that bounded pre-claim carrier to before any later staged reuse may occur
- `owlmlx.cache_pre_claim_admission_carrier_branch_reselection`
  - direct runtime-owned answer for whether the admission-carrier local exactness chain is complete enough to reselect the next non-carrier cache sub-branch honestly
- `owlmlx.cache_scheduler_turboquant_branch_reselection`
  - direct runtime-owned answer for whether scheduler depth or TurboQuant is now the next honest non-carrier cache branch on the current path
- `owlmlx.cache_continuous_batching_branch_reduction`
  - direct runtime-owned answer for how the selected scheduler-depth branch narrows next once `continuous_batching` is already selected and request aggregation is the next exact reduction target
- `owlmlx.cache_turboquant_preconditions_gap`
  - direct runtime-owned answer for the exact TurboQuant safe-activation requirements still missing on the active cache path
- `owlmlx.dominant_gap_reselection`
  - direct runtime-owned answer for which locally reducible gap should be worked next once cache, governance, and heavy-weight branches are already frozen strongly enough to compare honestly
- `owlmlx.multi_model_governance_status`
  - direct runtime-owned answer for current multi-model lifecycle governance depth
- `owlmlx.multi_model_pinning_control`
  - direct runtime-owned answer for whether pinning now exists as a real local
    governance control, whether pinned unload is blocked, and whether restart
    retains pin state
- `owlmlx.multi_model_governance_controls`
  - direct runtime-owned answer for which governance controls are present today and what repeated transition evidence exists without inventing absent controls
- `owlmlx.multi_model_governance_transition_ledger`
  - direct runtime-owned answer for whether recent governance transitions and repeated transition signals are visible as first-class lifecycle truth
- `owlmlx.multi_model_governance_policy_gap`
  - direct runtime-owned answer for whether the remaining governance blocker is still observation-grade or is now policy-grade only
- `owlmlx.heavy_weight_runtime_repeatability`
  - direct runtime-owned answer for whether heavy-weight repeatability is locally blocked, host-ready, or visible on a supported host
- `owlmlx.customer_runtime_evidence`
  - direct runtime-owned answer for how much cumulative replacement-grade evidence now exists, which gaps remain externally blocked, and which locally reducible gap should be worked next

These surfaces are still narrower than `/v1/runtime/status`. They exist so
`owlmlx` can answer two replacement-grade questions honestly:

- should deeper runtime validation continue on this host
- how much cache/scheduler depth does the runtime actually own today
- what level of cache residency/reuse evidence does the runtime actually own today
- what level of repeated-serving cache evidence does the runtime actually own today
- whether TurboQuant remains blocked by cache safety/evidence or has reached a
  runtime-owned controlled-validation rung
- what the current conservative cache closure rung actually is
- whether the remaining cache blocker is still observation-grade or has narrowed to exact missing counters plus serial-only scheduler depth
- whether cache counter ownership itself is already exact, so the next cache step is scheduler-depth / TurboQuant rather than more fake counter work
- whether the remaining cache closure has already split exactly into scheduler-depth versus TurboQuant work
- whether the scheduler branch itself is now frozen as a serial single-worker floor
- whether the scheduler branch has now narrowed further into an implementation backlog rather than a truth-gap
- whether the next scheduler branch is `continuous_batching` or a different exact path once the backlog is already frozen
- whether `continuous_batching` is merely absent or structurally blocked once it is already the selected scheduler branch
- whether the TurboQuant branch itself is now frozen as an exact set of missing preconditions rather than a generic safety posture
- whether cache remains the next locally reducible dominant gap once governance is policy-gap exact and heavy-weight repeatability is externally blocked
- what multi-model lifecycle behavior the runtime actually owns today
- which multi-model governance controls and transition evidence the runtime actually owns today
- whether recent governance transitions are visible strongly enough to freeze the remaining lifecycle gap exactly
- whether the remaining governance blocker is still observation-grade or has narrowed to policy-grade absent controls
- whether heavy-weight repeatability is blocked locally or only awaits supported-host repeated proof
- how much cumulative customer-runtime evidence now exists without inflating readiness claims

Phase 45 also adds one narrower diagnostic section inside the core runtime
status payload:

- `governance_observations`
  - lightweight active-kernel observations for:
    - transition count
    - recent explicit-targeting/restart activity
    - active-model reassignment visibility
    - restart-restore visibility

This section is diagnostic rather than field-stable policy truth. It exists so
the governance controls and transition ledger can consume runtime-owned
observations instead of harness-only synthetic evidence.

## 10. Phase 3A Single-Host Orchestration Assessment Surface

Phase 3A adds one further runtime-owned surface for single-host orchestration
truth without claiming scheduler parity:

- `owlmlx.orchestration_status`
  - direct runtime-owned answer for which orchestration layers are currently
    classifiable from runtime truth
  - surfaces:
    - current bottleneck-layer verdict when evidence is sufficient
    - per-layer `classification_status`
    - explicit `missing_signals` for pressure / recovery / stream layers that
      remain weaker than admission / gate truth

This surface sits alongside `/v1/runtime/status`.
It does not replace the stable status sections.

Its transport surface is:

- `GET /v1/runtime/orchestration-status`

Its stable sections are:

- `summary`
- `layer_assessment`
- `scheduler`
- `stream`
- `residency`
- `pressure`
- `recovery`
- `child_surfaces`
- `preserved_invariants`
- `upstream_truth_sources`
- `missing_signals`

## 11. Phase 3B Single-Host Scheduler Admission Contract

Phase 3B adds one narrower runtime-owned surface for automatic admission
decisions before whole-request gate claim:

- `owlmlx.scheduler_admission_contract`
  - direct runtime-owned answer for whether one request should currently be
    `accepted`, `deferred`, `rejected`, or left `unknown`
  - combines:
    - request-class truth
    - validated `GenerationGate` floor visibility
    - bounded pre-claim admission-window visibility
    - resident target-model truth
    - hard recovery-barrier truth from `recovery_supervisor_contract`
    - request context-length truth from `request_context_length_truth`
    - weaker budget / recovery / stream-hold signals without inflating them into
      stronger policy closure

This surface sits alongside `/v1/runtime/status` and
`/v1/runtime/orchestration-status`.
It does not replace the stable status sections and does not claim a full local
scheduler.

Its transport surface is:

- `GET /v1/runtime/scheduler-admission-contract`

Its stable sections are:

- `summary`
- `reason`
- `request_class_support`
- `boundary`
- `signals`
- `preserved_invariants`
- `missing_signals`

## 12. Phase 3B.1 Request Context-Length Truth For Admission

Phase 3B.1 adds one narrower runtime-owned support surface for scheduler
admission:

- `owlmlx.request_context_length_truth`
  - direct runtime-owned answer for whether a request is known `high_context`,
    known `non_high_context`, or still `unknown`
  - uses explicit `context_tokens` plus the already-owned
    `HIGH_CONTEXT_THRESHOLD_TOKENS`
  - does not call a tokenizer, estimate tokens from characters, or load a model
  - allows recovery `probing` to defer only known high-context requests

This surface sits alongside `/v1/runtime/scheduler-admission-contract`.
It does not replace generation enforcement or full tokenizer accounting.

Its transport surface is:

- `GET /v1/runtime/request-context-length-truth`

Its stable sections are:

- `summary`
- `classification`
- `thresholds`
- `source`
- `policy_boundaries`
- `missing_signals`

## 13. Phase 3C Single-Host Model Residency Policy

Phase 3C adds one narrower runtime-owned surface for current model residency
state classification:

- `owlmlx.model_residency_policy`
  - direct runtime-owned answer for which loaded models are currently
    `resident`, `default_active`, `pinned`, `ttl_managed`, or TTL-sweep
    `evictable`
  - keeps non-resident target handling at `unknown` until a load-on-demand or
    defer-to-load policy is explicitly frozen
  - keeps memory-pressure victim selection out of scope until a separate
    pressure contract exists

This surface sits alongside `/v1/runtime/status`,
`/v1/runtime/orchestration-status`, and
`/v1/runtime/scheduler-admission-contract`.

Its transport surface is:

- `GET /v1/runtime/model-residency-policy`

Its stable sections are:

- `summary`
- `target_model`
- `models`
- `residency_state_support`
- `policy_boundaries`
- `signals`
- `missing_signals`

## 14. Phase 3D Single-Host Memory Pressure Contract

Phase 3D adds one narrower runtime-owned surface for current budget-pressure
classification:

- `owlmlx.memory_pressure_contract`
  - direct runtime-owned answer for whether the current budget snapshot is
    `within_budget`, `near_budget`, `over_budget`, `cooldown_barrier`,
    `host_pressure_barrier`, or `unknown`
  - keeps reclaim, pressure-ranked eviction, and restart-barrier semantics at
    `insufficient_signal`
  - may surface TTL-sweep evictable model context from residency truth, but does
    not treat that as pressure victim selection
  - may surface host-visible load-admission pressure samples, but does not
    claim private Metal allocator visibility

This surface sits alongside the admission and residency policy surfaces.

Its transport surface is:

- `GET /v1/runtime/memory-pressure-contract`

Its stable sections are:

- `summary`
- `reason`
- `budget`
- `residency_context`
- `recovery_context`
- `policy_boundaries`
- `classification_support`
- `missing_signals`

## 15. Phase 3E Single-Host Recovery Supervisor Contract

Phase 3E adds one narrower runtime-owned surface for recovery barrier
classification:

- `owlmlx.recovery_supervisor_contract`
  - direct runtime-owned answer for whether backend health, restart exhaustion,
    or abort-recovery contamination requires a recovery barrier
  - distinguishes hard all-generation barriers from high-context-only probing
    deferral
  - keeps failed reclaim, failed unload, broader worker-pollution detection, and
    automatic recovery loops at `insufficient_signal`

This surface sits alongside the admission, residency, pressure, and
orchestration surfaces.

Its transport surface is:

- `GET /v1/runtime/recovery-supervisor-contract`

Its stable sections are:

- `summary`
- `barrier`
- `substrate`
- `restart`
- `lifecycle`
- `request_impact`
- `policy_boundaries`
- `missing_signals`

## 16. Comparative Evidence Record Surface

A separate runtime-owned HTTP surface exposes the comparative-evidence
record contract defined by `comparative-evidence-harness-contract.md`
and `comparative-evidence-schema-stub.md`. It sits alongside
`/v1/runtime/status` and is not part of the core status payload.

- `GET /v1/runtime/comparative-evidence`
  - 200: latest validated `comparative_evidence_record` v1
  - 503: explicit `still_blocked` payload when the ledger is not
    connected or empty
- `GET /v1/runtime/comparative-evidence/history`
  - 200: stable `comparative_evidence_record_history` v1 envelope with
    `records`, `ledger_status`
  - 503: explicit `still_blocked` payload when the ledger is not
    connected or empty

The surface is backed by the runtime-owned JSONL ledger
`owlmlx.comparative_evidence_history.ComparativeEvidenceLedger`. The
ledger path is connected at `create_app(...)` construction time
(`comparative_evidence_ledger_path`); `create_fake_app()` honors the
`OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH` environment variable so live
proof under a real `uvicorn` factory remains a one-line operator setup.

This surface is not a release-readiness claim. Floor 3.5 of
`release-readiness-backlog.md` remains open until at least one
`verdict_grade = "measured"` record exists in the ledger.

## 17. Reclaim Barrier Event Surface

A separate runtime-owned HTTP surface exposes the cleanup-boundary
failure event contract defined by `reclaim-barrier-event.md`. It sits
alongside `/v1/runtime/status` and is not part of the core status
payload.

- `GET /v1/runtime/reclaim-barrier-event`
  - 200: read-only `owlmlx.settle_barrier_event` v1 contract
    serialization
  - the route must not clear events, retry operations, or perform
    recovery
- `GET /v1/runtime/reclaim-barrier-event/stats`
  - 200: read-only `owlmlx.reclaim_barrier_event.stats` v1 aggregate
    measurement surface
  - the route reports unload-boundary duration and backend-reported
    reclaim distributions when those signals exist
  - the route must not resolve events, retry operations, or perform
    eviction/recovery

`/v1/runtime/status` exposes a diagnostic section `reclaim_barrier`
with:

- `events` — most recent up to 32 events (read-only snapshot)
- `total_event_count`
- `unresolved_event_count`

The stats route is intentionally separate from `/v1/runtime/status`.
It aggregates the kernel's unload/reclaim boundary measurements while
leaving the failure-event stream reserved for unresolved cleanup
barriers.

This surface does not advance release floor `3.4` to `closed`. It is the
cleanup-boundary event-recording sub-round (`3.4A0`) that the future
four-class termination-cause recovery policy will consume.

## 18. Termination Recovery Policy Surface

A separate runtime-owned HTTP surface exposes the cause-to-action
recovery policy defined by `termination-recovery-policy.md`. It sits
alongside `/v1/runtime/status` and the reclaim-barrier-event surface.

- `GET /v1/runtime/termination-recovery-policy`
  - 200: read-only `owlmlx.termination_recovery_policy` v1 contract
    serialization
  - the route must not retry, quarantine, drop, or remediate

`/v1/runtime/status` exposes a diagnostic section `load_failure` with:

- `events` — most recent up to 32 load-failure events
- `total_event_count`
- `unresolved_event_count`

Load-failure events are recorded inside `RuntimeKernel.load_model` at
the operation boundary (excluding `invalid_request` preflight and
`model_already_loaded` redundant-request paths). Auto-resolution rules
are documented in `termination-recovery-policy.md` §6.

## 19. Model Release-Candidate Evidence Surface

A separate runtime-owned HTTP surface exposes the post-technical-preview model
release-candidate evidence contract defined by
`model-release-candidate-program.md`. It sits alongside `/v1/runtime/status`
and is not part of the core status payload.

- `GET /v1/runtime/model-release-candidates`
  - 200: latest validated `model_release_candidate_record` v1
  - 503: explicit `still_blocked` payload when the ledger is not connected or
    empty
- `GET /v1/runtime/model-release-candidates/history`
  - 200: stable `model_release_candidate_record_history` v1 envelope with
    `records`, `ledger_status`
  - 503: explicit `still_blocked` payload when the ledger is not connected or
    empty

The surface is backed by
`owlmlx.model_release_candidate_history.ModelReleaseCandidateLedger`. The ledger
path is connected at `create_app(...)` construction time
(`model_release_candidate_ledger_path`); `create_fake_app()` honors the
`OWLMLX_MODEL_RELEASE_CANDIDATE_LEDGER_PATH` environment variable for live
operator checks.

This surface does not mark any model as application-ready. It only gives
OwlOps and upper layers a shared evidence schema for the model RC gate.

## 20. Model Load-Admission Projection Surface

A separate runtime-owned HTTP surface exposes model-specific load-admission
projection defined by `model-load-admission.md`. It sits alongside
`/v1/runtime/status` and is not part of the core status payload.

- `GET /v1/runtime/model-load-admission`
  - optional query: `model_id=<id>`
  - 200: `owlmlx.model_load_admission` v1 payload with per-model entries
- `POST /v1/runtime/host-pressure-sample`
  - 200: `owlmlx.host_pressure_sample` v1 payload and a refreshed cached
    `/v1/runtime/status.host_pressure` diagnostic section

The surface combines:

- runtime budget headroom
- runtime model visibility
- cached host-pressure diagnostic sample
- Metal-OOM cooldown and stale-registration barriers
- latest Model RC peak RSS for each model id
- model profile id / family

It does not run a model load, sample private Metal allocator state, or execute
pressure-ranked eviction. When host pressure has not been sampled, the
admission decision remains `unknown` even if the budget projection fits.
