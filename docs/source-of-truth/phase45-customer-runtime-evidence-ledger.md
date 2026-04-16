# owlmlx Phase 45: Customer Runtime Evidence Ledger

> Status: authoritative
> Updated: 2026-04-16
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

because `owlmlx` still has:

- an exact host-level external blocker for supported heavy-weight proof
- deeper governance/cache closure still below reference-grade parity

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
`structural_ingress_seam_introduced`, the ledger now also supports the
governance fallback posture:

- if supported-host baseline establishment is exact-blocked locally
- and governance policy controls have started to land
- the ledger may move `dominant_next_gap` back to
  `multi_model_lifecycle_governance`
  without pretending the host blocker disappeared or cache parity improved

That fallback posture is now narrower again:

- runtime pinning exists
- runtime TTL policy exists
- explicit TTL expiry sweep exists
- runtime eviction-history governance now also exists

That means the local governance fallback branch is now policy-closed on this
host:

- governance may remain below reference-grade parity
- but the next honest step is no longer another local policy-control round
- the next honest step is to return to supported-host baseline establishment
  while keeping cache frozen at `structural_ingress_seam_introduced`

The ledger now also consumes `owlmlx.dominant_gap_reselection` so
`dominant_next_gap` is no longer inferred ad hoc once:

- governance is already policy-gap exact
- cache scheduler backlog is already implementation-gap exact
- TurboQuant is already preconditions exact
- heavy-weight repeatability is already externally blocked

Once the governance policy gap closes locally, the customer ledger can stop
treating governance as the active local fallback branch and return the dominant
next gap to `host_stable_execution` while keeping cache frozen at
`structural_ingress_seam_introduced`.

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
- `owlmlx.cache_pre_gate_cohort_window_feasibility` then freezes the next
  stronger truth:
  - owlmlx still does not own any queueing/admission seam before whole-request
    gate claim
  - a pre-gate cohort window is therefore not locally expressible yet on the
    current path
- `owlmlx.cache_pre_gate_admission_hook_exactness` now freezes the next ingress
  blocker more exactly:
  - no bounded admission hook exists before whole-request gate claim
  - any future hook must preserve the validated post-claim serial invariants
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

Phase 45 now also has one real structural ingress upgrade:

- `owlmlx.cache_structural_ingress_seam`

That surface upgrades cache truth only to:

- `structural_ingress_seam_introduced`

It still must not claim:

- request aggregation supported
- continuous batching supported
- cache parity
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
