# owlmlx Phase 45: Customer Runtime Evidence Ledger

> Status: authoritative
> Updated: 2026-04-28
> Scope: runtime-only customer-runtime evidence for replacement-grade alignment

## 1. Purpose

This document advances `customer_runtime_evidence` from a narrative verdict
into a runtime-owned evidence ledger.

The question it answers is:

**How much replacement-grade runtime evidence now exists inside `owlmlx`, which
gaps remain externally blocked, and which locally reducible gap should be
worked next?**

## 2. Owned Contract

`owlmlx/customer_runtime_evidence.py` now owns:

- `build_customer_runtime_evidence(...)`
- `customer_runtime_evidence_to_dict(...)`

Operator entry:

- `scripts/runtime_customer_runtime_evidence.py`

Contract:

- `surface = "owlmlx.customer_runtime_evidence"`
- `version = "phase45"`

Stable sections:

- `summary`
- `gap_evidence`
- `next_step`

## 3. What The Ledger Summarizes

The ledger aggregates the runtime-owned closure surfaces for:

- `host_stable_execution`
- `cache_scheduler_depth`
- `multi_model_lifecycle_governance`
- `multi_model_governance_controls`
- `multi_model_governance_transition_ledger`
- `heavy_weight_runtime_repeatability`

For each gap it records:

- the owned contract surface
- whether runnable verification exists
- the current closure level
- whether the remaining blocker is external

## 4. Evidence Labels

Current `summary.evidence_label` values:

- `early_formal_runtime`
- `runtime_evidence_expanding`
- `approaching_reference_grade_stability`

Interpretation:

- `early_formal_runtime`
  - formal runtime contracts exist
  - the runtime is still below reference-grade stability
- `runtime_evidence_expanding`
  - core runtime-owned evidence is accumulating
  - major external blockers are no longer dominating the ledger
- `approaching_reference_grade_stability`
  - stronger closure surfaces exist across multiple gaps
  - this still does not imply customer readiness

## 5. Current Honest Result

The current honest result remains:

- `summary.evidence_label = "early_formal_runtime"`
- `next_step.dominant_next_gap = "cache_scheduler_depth"`
- `next_step.exact_external_blocker = null`

because `owlmlx` still has:

- cache now pointed at `aggregation_active_seam_exact`
- exact active cache blocker:
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`
- governance still below reference-grade residency parity even though the local
  policy branch is closed
- heavy-weight repeatability now sits at
  `supported_host_repeatability_visible`
- a current host that now has a supported candidate baseline and two successful
  repeat runs on the selected budget-fit heavier path on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- repeated heavy-weight proof is now visible on that selected path
- the newly visible bounded pre-gate request-aggregation window still remains
  below broader request-aggregation closure
- one non-stream child exchange can now already carry multiple requests
- the non-stream main serving path now also hands that bounded cohort into one
  aggregated child exchange
- stream gate release is now decoupled from outer consumer completion
- the active stream seam is now narrowed beyond iterator completion,
  terminal-event delivery, terminal-payload commit, and terminal-payload
  capture and terminal-record capture and terminal-record prefix detection and
  terminal-action discriminant detection and full terminal-notice capture and
  full terminal-notice prefix detection and terminal-notice
  action-discriminant detection and terminal-notice action-stem detection and
  terminal-notice marker detection and terminal-notice marker-prefix
  detection and terminal-notice marker-stem detection and terminal-notice
  marker-discriminant detection and terminal-notice marker-key-lead detection
  and full terminal-notice leading-discriminator detection and runtime-owned
  leading-discriminator prefix detection and runtime-owned
  leading-discriminator stem detection and onto backend terminal-notice
  leading-discriminator discriminant detection and onto backend terminal-
  notice leading-discriminator marker-prefix detection and onto backend
  terminal-notice leading-discriminator marker-stem detection and now onto
  backend terminal-notice leading-discriminator marker-discriminant detection,
  which remains frozen as the first honest unique boundary on the current
  runtime-owned marker-first record, and now onto one new earlier
  runtime-owned terminal-notice discriminator record ahead of that current
  marker-discriminant seam, with the fuller earlier-runtime-owned
  discriminator prefix and stem boundaries now already passed and the
  newer discriminator discriminant now already frozen as the first honest
  unique boundary on that newer runtime-owned record, and now onto one new
  earlier runtime-owned leading-discriminator record ahead of that newer
  discriminator record, where full leading-discriminator detection and prefix
  and stem boundaries are now already passed, the literal prefix before
  `runtime_owned_terminal_leading_` is not yet an honest runtime-owned
  transport boundary, and now onto one new earlier runtime-owned boundary
  record ahead of that newer leading-discriminator record, where a second
  backend stream request can now be written once child stdout reaches that
  new runtime-owned boundary stem and before child stdout reaches fuller
  earlier-runtime-owned-boundary prefix detection on that same internal
  record, where the literal prefix before `runtime_owned_terminal_b` is not
  yet an honest runtime-owned transport boundary, so the earlier-runtime-
  owned-boundary stem was frozen as the first honest unique boundary on that
  newer runtime-owned boundary record, and now onto one distinct earlier
  runtime-owned terminal record `runtime_owned_terminal_earlier_boundary`
  ahead of that stem, where a second backend stream request can be written
  before child stdout reaches `runtime_owned_terminal_b`; the current exact
  blocker is now earlier-runtime-owned-boundary earlier-boundary detection,
  while the fuller stem/prefix/detection truth stays preserved as secondary
  truth and the newer leading-discriminator discriminant stays frozen as the
  first honest unique boundary on that newer runtime-owned record; and the
  earlier-runtime-owned-boundary earlier-boundary detection is now also frozen
  as the first honest unique boundary on the newer earlier-boundary record
  itself, because the literal prefix before `runtime_owned_terminal_earlier_b`
  is the same shared prefix `{"ok": true, "runtime_owned_terminal_` that also
  fronts the older runtime-owned boundary record on this path, so it is not
  yet an honest runtime-owned transport boundary — this is a metadata-only
  freeze that does not move the active seam, does not introduce a new
  runtime-owned record, and does not relax post-claim serial invariants;
  and now onto one distinct earlier-earlier runtime-owned terminal record
  `runtime_owned_terminal_earlier_earlier_boundary` ahead of the existing
  earlier-boundary record, where the existing earlier-boundary trigger has
  been tightened from the shared `_e` prefix to `_earlier_b` (the honest
  unique stem identified by the prior freeze) and the new earlier-earlier
  trigger is `_earlier_e`, so a second backend stream request can be written
  once child stdout reaches `runtime_owned_terminal_earlier_earlier_boundary`
  and before child stdout reaches `runtime_owned_terminal_earlier_boundary`;
  the current exact blocker is now earlier-runtime-owned-boundary
  earlier-earlier-boundary detection, while the prior earlier-boundary first-
  unique-boundary truth stays preserved as secondary truth and post-claim
  `max_concurrent = 1`, ticketed FIFO, and serial safety remain preserved

## 6. What This Changes

Before this round, `owlmlx` had:

- runtime-owned host-stability truth
- runtime-owned cache closure truth
- runtime-owned governance truth
- runtime-owned heavy-weight repeatability truth

But it still lacked one machine-readable answer to:

- how much cumulative runtime evidence now exists
- which open gaps are external versus internal
- which locally reducible gap should be worked next

Now `owlmlx` owns that answer directly.

The operator entry also refreshes governance evidence against a narrow
governance harness so the customer ledger does not lag behind the stronger
runtime-owned transition ledger when that truth is already available locally.

After the cache branch was frozen at
`structural_ingress_seam_introduced`, the ledger supported a governance
fallback posture while supported-host baseline establishment was still
exact-blocked locally.

That fallback posture is now closed more honestly:

- runtime pinning exists
- runtime TTL policy exists
- explicit TTL expiry sweep exists
- runtime eviction-history governance now also exists

That means the local governance fallback branch is now policy-closed on this
host:

- governance may remain below reference-grade parity
- `host_stable_execution` is no longer exact-blocked locally
- `next_step.exact_external_blocker = null`
- the current host now has a supported candidate baseline
- the selected budget-fit heavier path now has supported-host repeated proof
  visible on this host
- the old structural checkpoint remains preserved exact
- cache no longer needs to stop at `structural_ingress_seam_introduced`
- cache now reopens beyond ingress on the request-aggregation active seam
- governance must not reopen as another local micro-round

The ledger now also consumes `owlmlx.dominant_gap_reselection` so
`dominant_next_gap` is no longer inferred ad hoc once:

- governance is already policy-gap closed on this host
- cache scheduler backlog is already implementation-gap exact
- TurboQuant is already preconditions exact
- heavy-weight repeatability now sits at
  `supported_host_repeatability_visible`

Once supported-host repeated heavy-weight proof becomes visible and cache is
reauthorized, the customer ledger can move `dominant_next_gap` to
`cache_scheduler_depth` without pretending:

- request aggregation exists
- continuous batching exists
- cache parity improved
- governance reached reference-grade residency parity

The operator entry now also refreshes cache closure against the active runtime
observation harness instead of leaving cache stuck at the old default
`truth_only` baseline. That means the customer ledger can now point at
`cache_scheduler_depth` for a narrower reason:

- repeated-serving runtime activity is visible
- one direct runtime-owned `reuse_counter` is now visible
- but `residency_counter` and `eviction_counter` are still absent
- and scheduler depth remains serial-only

With the residual cache counter gap now frozen exactly, the customer ledger no
longer needs to point at `owlmlx.cache_closure_rung` for cache. It can point
at `owlmlx.cache_counter_gap` directly when the live harness proves:

- repeated-serving runtime behavior is frozen strongly enough
- the remaining blocker is now exact
- the missing pieces are counter-grade and scheduler-grade, not observation-grade

Once counter ownership is frozen more tightly, the customer ledger can narrow
again and point at `owlmlx.cache_counter_feasibility`:

- `reuse_counter` is already runtime-owned and visible
- `residency_counter` and `eviction_counter` are not runtime-owned on this path
- the next cache closure step is therefore scheduler depth / TurboQuant, not
  more fake counter work

Once the scheduler/TurboQuant split is exact, the customer ledger can narrow
again and point at `owlmlx.cache_scheduler_turboquant_split`:

- cache counter ownership is already exact
- the remaining cache branch can be read explicitly as `scheduler_depth`
- TurboQuant stays exact but secondary

Once the scheduler branch itself is frozen, the customer ledger can narrow one
step further and point at `owlmlx.cache_scheduler_floor_gap`:

- `queue_discipline = serial`
- `max_concurrent = 1`
- `scheduler_depth = serial_single_worker`
- the cache branch is now scheduler-implementation work first, not more cache
  counter or split work

Once the scheduler branch is frozen strongly enough, the customer ledger can
narrow one step further and point at `owlmlx.cache_scheduler_implementation_backlog`:

- the serial GenerationGate floor is already exact
- the remaining gap is now an implementation backlog, not a truth-gap
- the missing scheduler capabilities are explicit:
  - `continuous_batching`
  - `multi_worker_scheduler_depth`

The scheduler backlog has now narrowed once more:

- the serial queue policy is explicitly visible as `ticketed_fifo`
- `deeper_queue_policy` is no longer an unfrozen absence on this path
- the remaining scheduler-grade work is now only:
  - `continuous_batching`
  - `multi_worker_scheduler_depth`

The scheduler backlog is now also branch-selected:

- `owlmlx.cache_scheduler_branch_selection` keeps
  `continuous_batching` as the next locally reducible scheduler branch
- `multi_worker_scheduler_depth` is still present, but only as a
  `safety_revalidation_required` secondary branch on the current path

The cache gap is now narrower again:

- `owlmlx.cache_continuous_batching_feasibility` freezes continuous batching as
  an exact feasibility blocker, not just a selected implementation branch
- `owlmlx.cache_batching_mechanism_subgap` then freezes the next exact local
  mechanism as `request_aggregation_window`
- `owlmlx.cache_request_aggregation_window_exactness` then freezes the ingress
  blocker under that mechanism:
  - no pre-gate admission window exists yet
  - the generation gate still claims the session before cohort formation
- `owlmlx.cache_pre_gate_cohort_window_feasibility` now also refreshes
  honestly:
  - owlmlx now owns a bounded pre-gate cohort window before whole-request gate
    claim
  - serial safety still remains validated only after claim
- `owlmlx.cache_pre_gate_admission_hook_exactness` now freezes the next ingress
  blocker more exactly after the authorized ingress widening:
  - the bounded admission hook has widened into a real pre-claim cohort window
  - the post-claim serial invariants remain frozen
  - any later widening must still preserve those invariants
- `owlmlx.cache_request_aggregation_active_seam` now becomes the active cache
  surface:
  - the selected seam is now
    `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency`
  - the exact blocker is now
    `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection`
  - one non-stream child exchange now already carries multiple requests in one
    exchange
  - the non-stream main serving path now also hands that bounded cohort into
    one aggregated child exchange
  - stream gate release no longer waits for outer consumer completion
  - a second backend stream can now start before the first iterator consumer
    receives the first stream's terminal event
  - a second backend stream can now also start before the first terminal
    payload is committed to the first stream queue
  - a second backend stream can now also start before the first terminal
    payload is decoded and captured
  - a second backend stream request can now also enter the live backend
    exchange before the first terminal record is fully captured
  - a second backend stream request can now also enter the live backend
    exchange before the first stream fully matches its terminal-record prefix
    on child stdout
  - a second backend stream request can now also enter the live backend
    exchange before the first terminal done payload reaches its action
    discriminant on child stdout
  - a second backend stream request can now also enter the live backend
    exchange before the first terminal-notice record is fully captured
  - a second backend stream request can now also enter the live backend
    exchange before child stdout fully matches the first terminal-notice
    prefix
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches the first terminal-notice action stem
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches the first explicit terminal-notice
    marker field
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches the first terminal-notice marker key
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches the first terminal-notice marker stem
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches the first terminal-notice marker
    discriminant
  - owlmlx now also owns one runtime-owned terminal-notice leading-discriminator
    record ahead of the old marker-key-lead seam
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches the first terminal-notice marker-key
    lead on the old notice record
  - a second backend stream request can now also enter the live backend
    exchange before child stdout fully matches that runtime-owned
    leading-discriminator action
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches that runtime-owned
    leading-discriminator prefix
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches that runtime-owned
    leading-discriminator stem
  - a second backend stream request can now also enter the live backend
    exchange before child stdout reaches that runtime-owned
    leading-discriminator discriminant
  - owlmlx now also owns one earlier runtime-owned `terminal_notice_lead`
    marker on that same leading-discriminator record
  - full leading-discriminator detection and runtime-owned
    leading-discriminator prefix detection remain preserved secondary truth on
    that newer record while leading-discriminator stem detection is now the
    current active blocker
  - marker-key lead remains preserved as the first unique boundary on the old
    terminal-notice record
  - TurboQuant remains secondary
- `owlmlx.cache_admission_hook_safety_contract` now freezes those invariants
  explicitly:
  - no bypass of whole-request gate claim
  - no reordering after claim
  - no post-claim parallel generation
- `owlmlx.cache_pre_claim_admission_contract` now freezes the next narrower
  truth:
  - the only possible future pre-claim seam is bounded metadata/ticket staging
    before whole-request gate claim
  - that seam may not claim the gate, start child exchange, start streaming, or
    execute model work before the first runtime-owned boundary
  - batching therefore remains pre-claim staging-contract work, not hidden
    pre-claim execution work

Phase 45 now also preserves one real structural ingress checkpoint:

- `owlmlx.cache_structural_ingress_seam`

That surface still preserves cache truth at:

- `structural_ingress_seam_introduced`

It still must not claim:

- request aggregation supported
- continuous batching supported
- cache parity

But after the authorized window round, the ledger no longer needs to stop at
the pre-gate seam either. It can preserve both earlier ingress checkpoints
while moving the active cache blocker to `owlmlx.cache_request_aggregation_active_seam`.
- `owlmlx.cache_pre_claim_marker_state_carrier` now narrows that staging path
  again:
  - a marker may live only in one inert write-once/clear-only record before
    gate claim
  - that carrier may not become queue slot identity, batch membership, child
    payload attachment, or stream/execution state
- `owlmlx.cache_pre_claim_marker_clear_observer_boundary` narrows again:
  - only explicit pre-claim drop/cancel logic and gate-claim expiry may clear
    the inert carrier
  - pre-claim discard may only observe it
  - scheduler, child/backend, stream, and execution-priority paths remain
    ineligible as clearers before gate claim
- `owlmlx.cache_pre_claim_marker_immutability_boundary` narrows again:
  - before gate claim marker state may change only by clear-only semantics
  - no pre-claim path may rewrite payload or mutate priority/queue/child/stream
    execution state through marker state
- `owlmlx.cache_pre_claim_marker_payload_shape_exactness` narrows again:
  - before gate claim marker state collapses to pure presence/absence only
  - no reason-code, priority, queue-metadata, or child/stream/execution
    payload fields may exist
- `owlmlx.cache_pre_claim_marker_encoding_carrier_exactness` narrows again:
  - before gate claim marker presence may live only in one inert boolean slot
  - that slot may not encode queue identity, ticket identity, child payload,
    or stream/execution handles
- `owlmlx.cache_pre_claim_marker_storage_locality_exactness` narrows again:
  - before gate claim the inert boolean marker slot may live only adjacent to
    staged metadata and outside ticket identity / immutable metadata payload
  - it may not occupy queue, scheduler, child, stream, or execution-local
    storage
- `owlmlx.cache_pre_claim_marker_locality_access_exactness` narrows again:
  - before gate claim only explicit pre-claim drop/cancel logic, gate-claim
    expiry, and pre-claim discard observation may reach the adjacent inert slot
  - scheduler, child/backend, stream, and execution-priority paths may not
    access it
- `owlmlx.cache_pre_claim_marker_locality_isolation_exactness` narrows again:
  - before gate claim the adjacent inert marker slot is isolated per staged
    request
  - no shared pending-state scheduler/backend/stream locality or cross-request
    marker merge may exist
- `owlmlx.cache_pre_claim_marker_locality_lifetime_coupling` narrows again:
  - before gate claim the isolated adjacent marker slot is coupled only to its
    own staged-request lifetime
  - reclaim may occur only by same-request pre-claim discard or same-request
    gate-claim expiry transition
  - no cross-request slot reuse or retained ownership may emerge from that
    coupling
- `owlmlx.cache_pre_claim_marker_reclaim_reset_exactness` narrows again:
  - reclaim clears the adjacent inert marker slot back to a fully empty inert
    state
  - no prior request history or reclaim reason remains visible after reclaim
  - later staged requests may reuse that locality only after a fully inert
    reset
- `owlmlx.cache_pre_claim_admission_carrier_construction` narrows again:
  - any bounded pre-claim admission carrier may be constructed only from
    immutable request metadata, observational ticket reservation, and a fully
    reset inert marker slot
  - no queue-owned, execution-bearing, child/stream-attached, or
    scheduler-priority carrier may exist before gate claim
- `owlmlx.cache_pre_claim_admission_carrier_field_exactness` narrows again:
  - a bounded pre-claim carrier may hold only immutable request metadata,
    observational ticket reservation, and a fully reset inert marker presence
    bit
  - no queue identity, scheduler priority, batch membership, child/stream
    attachment, or execution-bearing field may exist before gate claim
- `owlmlx.cache_pre_claim_admission_carrier_encoding_exactness` narrows again:
  - immutable request metadata, observational ticket reservation, and a fully
    reset inert marker presence bit may be encoded only as one bounded inert
    pre-claim record
  - no queue identity, scheduler priority, batch membership, child/stream
    attachment, or execution-bearing encoding may exist before gate claim
- `owlmlx.cache_pre_claim_admission_carrier_locality_exactness` narrows again:
  - the bounded inert pre-claim record may live only in single-request staged
    locality adjacent to metadata/ticket state before gate claim
  - it may not occupy queue, scheduler, child/stream, or execution-owned
    locality before claim
- `owlmlx.cache_pre_claim_admission_carrier_locality_access_exactness` narrows again:
  - only staged metadata snapshot building, observational ticket reservation,
    same-request pre-claim drop/cancel reset, and same-request pre-claim
    discard observation may reach the bounded inert pre-claim carrier before
    claim
  - queue/cohort scheduler, child/backend payload, stream-handle, and
    execution-entitlement paths may not access it
- `owlmlx.cache_pre_claim_admission_carrier_locality_isolation_exactness` narrows again:
  - the bounded inert pre-claim carrier remains isolated per staged request
    before claim
  - no shared scheduler/backend/stream pending-state carrier locality or
    cross-request carrier merge may exist
- `owlmlx.cache_pre_claim_admission_carrier_locality_lifetime_coupling` narrows again:
  - the bounded inert pre-claim carrier is coupled only to its own staged-
    request lifetime before claim
  - it may be reclaimed only by same-request pre-claim discard or gate-claim
    expiry transition
  - it may not survive into cross-request reuse or retained scheduler/backend/
    stream lifetime
- `owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness` narrows again:
  - reclaim resets that bounded inert pre-claim carrier back to a fully empty
    inert state before any later reuse
  - no prior request history or execution-bearing residue remains visible after
    reclaim
  - later staged requests may reuse adjacent locality only after that clean
    empty reset
- `owlmlx.cache_pre_claim_admission_carrier_branch_reselection` narrows again:
  - the admission-carrier exactness chain is complete on the current path
  - no narrower residual carrier subgap remains open
  - the next cache sub-branch therefore moves back to scheduler-vs-TurboQuant
    reselection
- `owlmlx.cache_scheduler_turboquant_branch_reselection` narrows again:
  - scheduler depth is the selected next branch on the current path
  - the selected scheduler sub-branch remains `continuous_batching`
  - TurboQuant stays exact-but-secondary on the same path
- `owlmlx.cache_continuous_batching_branch_reduction` narrows again:
  - scheduler depth remains the selected cache branch on the current path
  - `continuous_batching` remains the selected scheduler sub-branch
  - `request_aggregation_window` is now the next exact reduction target
  - `shared_prefill_batch_step` and `interleaved_decode_scheduler` stay secondary
- `owlmlx.cache_request_aggregation_window_reentry` narrows again:
  - `request_aggregation_window` has re-entered as the active cache subchain
  - `shared_prefill_batch_step` and `interleaved_decode_scheduler` stay secondary
  - TurboQuant stays exact-but-secondary
- `owlmlx.cache_pre_claim_staging_seam_exactness` now freezes the seam itself:
  - only immutable request metadata plus ticket reservation may be staged
    before gate claim
  - gate ownership transfer, child payload assembly, stream-handle allocation,
    and model state/prefill all remain outside the seam
  - batching is now narrowed further into metadata/ticket ownership work, not
    generic staging narrative
- `owlmlx.cache_pre_claim_metadata_ticket_ownership` now freezes that ownership
  boundary:
  - ticket reservation is observational-only and grants no execution rights
    before gate claim
  - immutable request metadata remains read-only before gate claim
  - neither staged unit may promote into child, stream, or model-execution
    state before the first runtime-owned boundary
- `owlmlx.cache_pre_claim_inert_state_semantics` now freezes the inert state
  itself:
  - the only allowed inert semantics before gate claim are drop/cancel markers
  - owlmlx still owns no cohort membership before gate claim
  - inert state still may not acquire execution priority or prefill-batch
    membership before the first runtime-owned boundary
- `owlmlx.cache_pre_claim_marker_lifetime` now freezes marker lifetime:
  - an inert drop/cancel marker may exist only until explicit pre-claim discard
    or whole-request gate claim
  - marker lifetime may not create queue ownership
  - marker lifetime may not transfer execution entitlement into post-claim
    state
- `owlmlx.cache_pre_claim_marker_visibility` now freezes marker visibility:
  - an inert marker may be observed only by explicit pre-claim discard logic or
    gate-claim expiry logic
  - marker visibility may not leak into scheduler selection, child dispatch,
    stream handling, or execution-priority paths before gate claim
- `owlmlx.cache_pre_claim_marker_trigger_inputs` now freezes trigger inputs:
  - an inert marker may be cleared only by explicit pre-claim drop/cancel
    signals or gate-claim expiry
  - scheduler pressure, child/backend events, stream events, and
    execution-priority signals remain unavailable as pre-claim trigger inputs
- `owlmlx.cache_pre_claim_marker_reader_writer_ownership` now freezes reader
  versus writer ownership:
  - only explicit pre-claim drop/cancel logic and gate-claim expiry may author
    a marker
  - pre-claim discard may only observe it
  - scheduler, child/backend, stream, and execution-priority paths remain
    ineligible for writer ownership before gate claim
- `shared_prefill_batch_step` and `interleaved_decode_scheduler` remain
  explicit but secondary behind aggregate admission

TurboQuant can now also be read more narrowly as an exact-but-secondary branch:

- `owlmlx.cache_turboquant_preconditions_gap` freezes the exact missing
  preconditions
- the current active path still lacks:
  - `bits_in_cache_key`
  - `invalidates_on_config_toggle`
  - `runtime_verified`
- this does not overtake the scheduler backlog as the dominant cache branch

With that refresh in place, the remaining governance blocker should now be read
more narrowly:

- not missing transition visibility
- not missing local policy controls on this host
- but still below reference-grade multi-model governance parity overall

## 7. What This Does Not Claim

It does not claim:

- customer readiness
- parity with `oMLX` or `vMLX`
- supported-host heavy-weight repeatability proof already exists

It only claims:

- `owlmlx` now owns a customer-runtime evidence ledger
- one budget-fit heavy boundary entry can now appear in the ledger without
  being misreported as repeated proof
- the governance gap can absorb stronger transition-ledger truth without
  hiding absent lifecycle controls
- once the local policy branch closes, the ledger can return
  `dominant_next_gap` to `host_stable_execution` without pretending the host
  blocker disappeared
- the cache gap can now absorb stronger active-runtime evidence without
  pretending runtime-owned counters already exist
- the cache gap can also freeze when counter ownership itself is already exact,
  so the next cache step can move to scheduler/TurboQuant work
- the cache gap can narrow again from split truth into an exact scheduler-floor
  truth on the active path
- the cache gap can narrow once more into an exact scheduler implementation backlog
- the cache gap can also freeze TurboQuant as an exact-but-secondary preconditions branch
- the remaining external blocker is exact rather than narrative
- the next locally reducible dominant gap can be selected from runtime truth
  through `owlmlx.dominant_gap_reselection`
- once cache remains dominant, the next scheduler implementation branch can
  also be selected from runtime truth through
  `owlmlx.cache_scheduler_branch_selection`
- once `continuous_batching` is the selected branch, the runtime can freeze
  whether it is merely absent or structurally blocked through
  `owlmlx.cache_continuous_batching_feasibility`
- once the bounded post-claim safety contract is exact, the runtime can also
  freeze the only allowable pre-claim contract surface through
  `owlmlx.cache_pre_claim_admission_contract`
- once that contract is exact, the runtime can freeze the seam itself through
  `owlmlx.cache_pre_claim_staging_seam_exactness`
- once the seam itself is exact, the runtime can freeze ownership/lifetime
  boundaries for those staged units through
  `owlmlx.cache_pre_claim_metadata_ticket_ownership`
- once those ownership boundaries are exact, the runtime can freeze inert
  cohort/drop semantics through `owlmlx.cache_pre_claim_inert_state_semantics`
- once inert semantics are exact, the runtime can freeze exact marker lifetime
  and expiry boundaries through `owlmlx.cache_pre_claim_marker_lifetime`
- once marker lifetime is exact, the runtime can freeze exact marker
  visibility/discard-trigger semantics through
  `owlmlx.cache_pre_claim_marker_visibility`
- once marker visibility is exact, the runtime can freeze exact discard-trigger
  inputs through `owlmlx.cache_pre_claim_marker_trigger_inputs`
- once trigger inputs are exact, the runtime can freeze exact reader/writer
  ownership through `owlmlx.cache_pre_claim_marker_reader_writer_ownership`

## 8. Release-Floor 3.1 Closure Command Evidence

Release floor `3.1 Cache Scheduler Closure Beyond Exactness` closed on
2026-04-25 (Round C closeout). Evidence recorded here is command-level
runtime evidence, not a parity or replacement claim. The replacement-grade
posture remains `early_formal_runtime` and `dominant_next_gap` remains
`cache_scheduler_depth` (further closure beyond release-floor language is
still open).

Command evidence captured under the C closeout round:

```text
$ pytest -q tests/test_cache_pre_gate_admission_window_seam.py
... 5 passed in 0.08s

$ pytest -q tests/test_runtime_kernel.py -k \
    "repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load \
     or concurrent_generations_handoff_cohort_into_aggregated_child_exchange"
... 2 passed, 23 deselected in 0.60s

$ pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py
... 28 passed in 1.16s

$ pytest -q tests/test_cache_request_aggregation_active_seam.py
... 15 passed in 0.09s

$ pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py
... 60 passed in 17.74s

$ git diff --check
(clean)
```

The closure is on the non-stream main runtime path only. The stream-branch
dispatch-level closure remains the active phase45 seam blocker
(`backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`)
preserved as secondary truth.

## 9. Release-Floor 3.6 External Customer Evidence Candidate

Record:

```text
record_id = owlmlx_release_floor_3_6A_20260428T025051Z
recorded_at = 2026-04-28T02:51:45Z
deployment_owner_or_boundary = OwlOps external consumer boundary
repo_or_host_boundary = /Users/yeemio/AI/gitrep/owlops -> http://127.0.0.1:8065
host_class = Mac17,6-arm64-macOS-26.4.1-128GB
workload_class = external_runtime_status_probe
runtime_surface_used = GET /v1/runtime/status, GET /healthz
command_or_request = python3 urllib.request probe from /Users/yeemio/AI/gitrep/owlops
verdict = pass
external_blocker_or_success = OwlOps-boundary external consumer successfully fetched owlmlx runtime status and health truth over HTTP from outside the owlmlx repository.
evidence_pointer = files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/
not_release_claim = true
```

Evidence files:

```text
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/external-run-notes.md
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stdout.json
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stderr.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.exit-status
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-before.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-after.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/host-class.txt
```

This record is external because the live HTTP request was issued from the
OwlOps repository boundary, whose adapter and connection validator consume
`owlmlx` runtime truth surfaces. It is intentionally narrow: it proves external
runtime-truth consumption, not model inference quality, public-surface freeze,
release readiness, parity, replacement, production-grade posture, or
superiority.
