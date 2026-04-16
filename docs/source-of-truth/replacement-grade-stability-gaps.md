# owlmlx Replacement-Grade Stability Gaps

> Status: authoritative
> Updated: 2026-04-13

## 1. Purpose

This document freezes the current replacement-grade stability gap between
`owlmlx` and the local reference runtimes `oMLX` / `vMLX`.

Its purpose is not to claim parity. Its purpose is to stop the `owlmlx` loop
from drifting into narrower specimen or shell concerns while the runtime still
falls short of reference-system stability.

## 2. Honest Top-Level Verdict

`owlmlx` is now a real runtime with real serving seams, real compatibility
entrypoints, and real Owl consumer cutover proof.

`owlmlx` is **not yet** in the same stability class as `oMLX` or `vMLX`.

That means:

- it is no longer honest to call `owlmlx` just a toy
- it is also not honest to present it as customer-ready

The current honest label is:

**early formal runtime, below reference-grade stability**

## 3. Reference Systems Actually Prove More

What `oMLX` and `vMLX` already demonstrate that matters here:

- host-stable local execution on real serving machines
- deeper cache and scheduler behavior than one truth surface or one control
  action
- more mature multi-model lifecycle behavior
- repeatable heavy-weight serving behavior on actual runtime paths
- stronger customer-facing confidence through longer-running operational proof

This is why parity cannot be inferred from `owlmlx` having:

- OpenAI / Anthropic entrypoints
- restart/status contracts
- cutover proofs
- blocker reports

Those are necessary runtime assets. They are not yet sufficient stability.

## 4. Frozen Replacement-Grade Gaps

### 4.1 `host_stable_execution`

Reference systems prove:

- usable local execution baselines exist on real hosts
- serving can proceed without being blocked at import time

`owlmlx` currently has:

- machine-owned blocker truth
- specimen gate
- host forensics
- first-smoke locality decision

`owlmlx` still lacks:

- one verified-safe MLX baseline on a supported host for heavy-weight runtime

Why it blocks customer-grade claims:

- no runtime can claim `oMLX` / `vMLX`-class stability while its primary host
  path remains blocked at the import layer

### 4.2 `cache_scheduler_depth`

Reference systems prove:

- real cache reuse and scheduler depth in live runtime behavior
- cache systems are more than descriptive truth

`owlmlx` currently has:

- cache truth contract
- queue-based single-worker scheduler truth
- runtime-owned cache/scheduler depth status
- runtime-owned cache residency/reuse evidence surface
- runtime-owned cache repeatability evidence surface
- runtime-owned TurboQuant readiness surface
- runtime-owned cache closure rung
- runtime-owned cache counter-gap freeze
- runtime-owned cache counter-feasibility freeze
- runtime-path repeated-serving observations through persistent-child backend bookkeeping
- one bounded runtime-owned pre-gate admission seam before whole-request gate claim
- some operator/control-plane surfaces above it

`owlmlx` still lacks:

- replacement-grade cache/scheduler closure inside the runtime line itself
- deeper scheduler behavior beyond the now-frozen serial floor
- cohort/admission work beyond the new structural ingress seam
- explicit scheduler implementation beyond:
  - `queue_discipline = serial`
  - `max_concurrent = 1`
  - wait-counter visibility
- TurboQuant preconditions beyond the now-frozen exact missing set:
  - `bits_in_cache_key`
  - `invalidates_on_config_toggle`
  - `runtime_verified`

Why it blocks customer-grade claims:

- customer stability requires not just visibility of cache policy, but runtime
  behavior that meaningfully approaches the reference systems

### 4.3 `multi_model_lifecycle_governance`

Reference systems prove:

- stronger model residency, eviction, and lifecycle behavior
- multi-model serving as a governed runtime path, not just a theoretical
  contract

`owlmlx` currently has:

- load/unload/restart semantics
- inventory and budget truth
- runtime-owned multi-model governance status
- runtime-owned multi-model governance controls
- runtime-owned multi-model governance transition ledger
- runtime-owned governance transition observations on the active kernel path
- runtime-owned governance policy-gap freeze

`owlmlx` still lacks:

- pinning
- TTL policy
- eviction-history governance
- deeper replacement-grade multi-model lifecycle depth beyond visible active/default and restart semantics

Why it blocks customer-grade claims:

- customer-grade local runtime is not defined by one-model happy paths alone

### 4.4 `heavy_weight_runtime_repeatability`

Reference systems prove:

- repeatable heavy-weight runtime serving, not just staging or one-off smokes

`owlmlx` currently has:

- specimen completeness gate
- first-smoke gate
- locality decision
- some historical local smokes on other models
- runtime-owned heavy-weight repeatability status

`owlmlx` still lacks:

- repeatable heavy-weight runtime proof on a supported host for the current
  path under active development

Why it blocks customer-grade claims:

- customer trust comes from repeatable runtime behavior, not specimen readiness

### 4.5 `customer_runtime_evidence`

Reference systems prove:

- a body of operational evidence that supports stronger user-facing promises

`owlmlx` currently has:

- formal contracts
- verified tests
- migration seams
- cutover proofs
- runtime-owned customer evidence ledger

`owlmlx` still lacks:

- enough runtime evidence to honestly advance beyond early formal runtime

Why it blocks customer-grade claims:

- stable contracts and cutover proofs are necessary, but still below the
  evidence threshold of a customer-facing runtime

## 5. What This Resets

This document resets one important truth drift:

- the main `owlmlx` goal is **not** "run MiniMax first smoke on this machine"
- the main `owlmlx` goal is **replacement-grade stability alignment**

MiniMax first smoke remains a valid subproblem. It is not the top-level goal.

## 6. Current Dominant Gap

`host_stable_execution` remains a real replacement-grade gap, but the current
host answer is now frozen through `owlmlx.host_stable_execution`.

That means the next locally reducible dominant gap is now:

`cache_scheduler_depth`

Reason:

- the current host is already classified as unsuitable for deeper replacement-grade validation
- continuing to restate the same blocked host truth would not shrink the gap inventory
- cache/scheduler depth was one of the clearest remaining differences versus
  `oMLX` / `vMLX`, and it now has a frozen runtime-owned closure rung
- the exact remaining cache blocker is now explicit:
  - direct runtime-owned `reuse_counter` is now visible on the active runtime path
  - `residency_counter` and `eviction_counter` are now frozen as not-runtime-owned on the current path
  - the scheduler branch is now frozen exactly as `owlmlx.cache_scheduler_floor_gap`
    with:
    - `queue_discipline = serial`
    - `max_concurrent = 1`
    - `scheduler_depth = serial_single_worker`
  - the scheduler-grade remaining work is now frozen exactly as
    `owlmlx.cache_scheduler_implementation_backlog`:
    - `ticketed_fifo` queue policy is now explicit and runtime-owned
    - `continuous_batching`
    - `multi_worker_scheduler_depth`
  - the next scheduler branch is now frozen exactly as
    `owlmlx.cache_scheduler_branch_selection`:
    - `continuous_batching` is the next locally reducible branch
    - `multi_worker_scheduler_depth` stays secondary until concurrency safety
      is revalidated
  - that selected branch is now narrowed further as
    `owlmlx.cache_continuous_batching_feasibility`:
    - the current path is blocked by exact missing batching mechanisms
    - `continuous_batching` is therefore not just absent, but structurally
      blocked on the active path until request aggregation / interleaved
      scheduling exists
  - that feasibility blocker is now narrowed again as
    `owlmlx.cache_batching_mechanism_subgap`:
    - `request_aggregation_window` is the first exact local mechanism subgap
    - `shared_prefill_batch_step` stays secondary
    - `interleaved_decode_scheduler` stays secondary behind aggregate
      admission and full-session stream release
  - that selected mechanism is now narrowed again as
    `owlmlx.cache_request_aggregation_window_exactness`:
    - no pre-gate admission window exists on the current path
    - whole-request gate entry still claims the session before cohort
      formation
    - aggregated child dispatch and stream release remain downstream
      dependencies
  - that ingress blocker is now narrowed again as
    `owlmlx.cache_pre_gate_cohort_window_feasibility`:
    - no runtime-owned cohort window exists before gate claim
    - `GenerationGate` has no pre-admission hook
    - the validated serial safety boundary still begins only after
      whole-request gate claim
  - that ingress blocker is now narrowed again as
    `owlmlx.cache_pre_gate_admission_hook_exactness`:
    - no bounded admission hook exists before whole-request gate claim
    - the first runtime-owned boundary is still whole-request gate claim
    - any future hook must preserve the validated post-claim serial invariants
  - that ingress blocker is now narrowed again as
    `owlmlx.cache_admission_hook_safety_contract`:
    - whole-request gate claim may not be bypassed
    - FIFO order may not be broken after claim
    - post-claim parallel generation remains forbidden
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_contract`:
    - the only allowable future seam is bounded metadata/ticket staging before
      whole-request gate claim
    - that seam may not claim the gate, start child exchange, start streaming,
      or execute model work before the first runtime-owned boundary
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_staging_seam_exactness`:
    - only immutable request metadata and ticket reservation may be staged
      before whole-request gate claim
    - gate ownership transfer, child payload assembly, stream-handle
      allocation, and model state/prefill remain outside the seam
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_metadata_ticket_ownership`:
    - ticket reservation remains observational-only and grants no execution
      rights before gate claim
    - immutable request metadata remains read-only before gate claim
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_inert_state_semantics`:
    - the only allowed inert semantics are drop/cancel markers before gate
      claim
    - no runtime-owned cohort membership exists before gate claim
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_lifetime`:
    - an inert marker may exist only until explicit pre-claim discard or
      whole-request gate claim
    - marker lifetime may not create queue ownership or post-claim execution
      entitlement
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_visibility`:
    - an inert marker may be observed only by pre-claim discard logic or
      gate-claim expiry logic
    - marker visibility may not leak into scheduler selection, child dispatch,
      stream handling, or execution-priority paths
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_trigger_inputs`:
    - an inert marker may be cleared only by explicit pre-claim drop/cancel
      signals or by gate-claim expiry transition
    - scheduler pressure, child/backend, stream, and execution-priority inputs
      remain unavailable as pre-claim marker triggers
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_reader_writer_ownership`:
    - only explicit pre-claim drop/cancel logic and gate-claim expiry may
      author a marker
    - pre-claim discard may only observe it
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_state_carrier`:
    - a marker may live only in a single inert write-once/clear-only record
      before gate claim
    - that inert record may not become queue slot identity, batch membership,
      child payload attachment, or stream/execution state
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_clear_observer_boundary`:
    - only explicit pre-claim drop/cancel logic and gate-claim expiry may
      clear the inert marker carrier
    - pre-claim discard may only observe it
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_immutability_boundary`:
    - before gate claim marker state may only change by clear-only semantics
    - no pre-claim path may rewrite payload, mutate priority, create queue
      membership, or attach child/stream/execution state through marker state
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_payload_shape_exactness`:
    - before gate claim marker state collapses to pure presence/absence only
    - no reason-code, priority, queue-metadata, or child/stream/execution
      payload fields may exist
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_encoding_carrier_exactness`:
    - before gate claim marker presence may live only in one inert boolean slot
    - that slot may not encode queue identity, ticket identity, child payload,
      or stream/execution handles
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_storage_locality_exactness`:
    - before gate claim the inert boolean marker slot may live only adjacent to
      staged metadata and outside ticket identity / immutable metadata payload
    - it may not occupy queue, scheduler, child, stream, or execution-local
      storage
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_locality_access_exactness`:
    - before gate claim only explicit pre-claim drop/cancel logic, gate-claim
      expiry, and pre-claim discard observation may reach the adjacent inert
      marker slot
    - scheduler, child/backend, stream, and execution-priority paths may not
      access it
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_locality_isolation_exactness`:
    - before gate claim the adjacent inert marker slot is isolated per staged
      request
    - no shared pending-state scheduler/backend/stream locality or cross-request
      marker merge may exist
    - the next local cache work is therefore marker locality-lifetime
      coupling exactness, not generic locality-isolation narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_locality_lifetime_coupling`:
    - before gate claim the isolated adjacent marker slot is coupled only to
      its own staged-request lifetime
    - reclaim may occur only by same-request pre-claim discard or same-request
      gate-claim expiry transition
    - no cross-request slot reuse, retained scheduler/backend/stream lifetime,
      or execution entitlement may emerge from that coupling
    - the next local cache work is therefore marker reclaim-reset exactness,
      not generic locality-lifetime narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_marker_reclaim_reset_exactness`:
    - reclaim clears the adjacent inert marker slot back to a fully empty inert
      state
    - no prior request history or reclaim reason remains visible after reclaim
    - later staged requests may reuse that locality only after a fully inert
      reset
    - the next local cache work is therefore pre-claim admission-carrier
      construction exactness, not generic reclaim narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_construction`:
    - any bounded pre-claim admission carrier may be constructed only from
      immutable request metadata, observational ticket reservation, and a fully
      reset inert marker slot
    - no queue-owned, execution-bearing, child/stream-attached, or
      scheduler-priority carrier may exist before gate claim
    - the next local cache work is therefore admission-carrier field exactness,
      not generic carrier-construction narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_field_exactness`:
    - a bounded pre-claim carrier may hold only immutable request metadata,
      observational ticket reservation, and a fully reset inert marker
      presence bit
    - no queue identity, scheduler priority, batch membership, child/stream
      attachment, or execution-bearing field may exist before gate claim
    - the next local cache work is therefore admission-carrier encoding
      exactness, not generic field-selection narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_encoding_exactness`:
    - immutable request metadata, observational ticket reservation, and a
      fully reset inert marker presence bit may be encoded only as one bounded
      inert pre-claim record
    - no queue identity, scheduler priority, batch membership, child/stream
      attachment, or execution-bearing encoding may exist before gate claim
    - the next local cache work is therefore admission-carrier locality
      exactness, not generic encoding narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_locality_exactness`:
    - the bounded inert pre-claim record may live only in single-request
      staged locality adjacent to metadata/ticket state before gate claim
    - it may not occupy queue, scheduler, child/stream, or execution-owned
      locality before claim
    - the next local cache work is therefore admission-carrier locality-access
      exactness, not generic locality narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_locality_access_exactness`:
    - only staged metadata snapshot building, observational ticket
      reservation, same-request pre-claim drop/cancel reset, and same-request
      pre-claim discard observation may reach the bounded inert pre-claim
      carrier before claim
    - queue/cohort scheduler, child/backend payload, stream-handle, and
      execution-entitlement paths may not access it
    - the next local cache work is therefore admission-carrier locality-
      isolation exactness, not generic locality-access narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_locality_isolation_exactness`:
    - the bounded inert pre-claim carrier remains isolated per staged request
      before claim
    - no shared scheduler/backend/stream pending-state carrier locality or
      cross-request carrier merge may exist
    - the next local cache work is therefore admission-carrier locality-
      lifetime coupling, not generic isolation narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_locality_lifetime_coupling`:
    - the bounded inert pre-claim carrier is coupled only to its own staged-
      request lifetime before claim
    - it may be reclaimed only by same-request pre-claim discard or gate-claim
      expiry transition
    - it may not survive into cross-request reuse or retained
      scheduler/backend/stream lifetime
    - the next local cache work is therefore admission-carrier reclaim-reset
      exactness, not generic lifetime narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness`:
    - reclaim resets that bounded inert pre-claim carrier back to a fully
      empty inert state before any later reuse
    - no prior request history or execution-bearing residue remains visible
      after reclaim
    - later staged requests may reuse adjacent locality only after that clean
      empty reset
    - the next local cache work is therefore admission-carrier branch
      reselection, not generic reclaim/reset narrative
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_pre_claim_admission_carrier_branch_reselection`:
    - the admission-carrier exactness chain is complete on the current path
    - no narrower residual carrier subgap remains open
    - the next local cache work therefore moves back to scheduler-vs-TurboQuant
      branch reselection
  - that ingress blocker is now narrowed once more as
    `owlmlx.cache_scheduler_turboquant_branch_reselection`:
    - scheduler depth is the selected next branch on the current path
    - the selected scheduler sub-branch remains `continuous_batching`
    - TurboQuant stays exact-but-secondary on the same path
    - the next local cache work therefore moves into scheduler branch
      reduction, not more branch selection narrative
  - that scheduler branch reduction is now narrowed once more as
    `owlmlx.cache_continuous_batching_branch_reduction`:
    - scheduler depth remains the selected cache branch on the current path
    - `continuous_batching` remains the selected scheduler sub-branch
    - `request_aggregation_window` is the next exact reduction target
    - `shared_prefill_batch_step` and `interleaved_decode_scheduler` stay
      secondary
  - the TurboQuant branch is now frozen exactly as
    `owlmlx.cache_turboquant_preconditions_gap`:
    - `bits_in_cache_key`
    - `invalidates_on_config_toggle`
    - `runtime_verified`
- `multi_model_lifecycle_governance` now has a runtime-owned status surface,
  controls surface, transition ledger, active-kernel governance observations,
  and a governance policy-gap freeze
- its remaining absent controls are now frozen more narrowly as policy-grade
  gaps (`pinning`, `TTL`, `eviction-history governance`) rather than the next
  dominant observation/integration gap
- `heavy_weight_runtime_repeatability` now has a runtime-owned status surface
  too, and the current remaining blocker is exact:
  - a supported host/system image is still required for repeated heavy-weight proof
- `customer_runtime_evidence` already has a runtime-owned evidence ledger, and
  governance can now be frozen more narrowly as a policy-grade residual blocker
  rather than an observation-grade gap
- the next locally reducible dominant gap is therefore
  `cache_scheduler_depth`
- that dominant-gap choice is now also frozen as
  `owlmlx.dominant_gap_reselection`
