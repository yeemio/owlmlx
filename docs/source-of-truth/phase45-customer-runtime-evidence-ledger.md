# owlmlx Phase 45: Customer Runtime Evidence Ledger

> Status: authoritative
> Updated: 2026-04-13
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

The ledger now also consumes `owlmlx.dominant_gap_reselection` so
`dominant_next_gap` is no longer inferred ad hoc once:

- governance is already policy-gap exact
- cache scheduler backlog is already implementation-gap exact
- TurboQuant is already preconditions exact
- heavy-weight repeatability is already externally blocked

Once the governance policy gap is exact, the customer ledger can stop treating
governance as the dominant observation gap and move the dominant next gap to
cache/scheduler depth while keeping the governance residual blocker explicit.

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
- but still-missing lifecycle policy controls such as pinning, TTL, and
  eviction-history governance

## 7. What This Does Not Claim

It does not claim:

- customer readiness
- parity with `oMLX` or `vMLX`
- supported-host heavy-weight repeatability proof already exists

It only claims:

- `owlmlx` now owns a customer-runtime evidence ledger
- the governance gap can absorb stronger transition-ledger truth without
  hiding absent lifecycle controls
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
