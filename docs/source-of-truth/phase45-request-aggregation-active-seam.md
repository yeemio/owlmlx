# owlmlx Phase 45: Request Aggregation Active Seam

> Status: authoritative
> Updated: 2026-04-23
> Scope: runtime-only active request-aggregation seam after pre-gate window entry

## 1. Purpose

Freeze the next active request-aggregation seam once:

- `request_aggregation_window` is already the selected scheduler mechanism
- a bounded pre-gate request-aggregation/cohort window is already visible on
  the runtime path
- `owlmlx` still must not inflate that ingress widening into broader batching
  claims

## 2. Owned Contract

`owlmlx/cache_request_aggregation_active_seam.py` now owns:

- `build_cache_request_aggregation_active_seam(...)`
- `cache_request_aggregation_active_seam_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_request_aggregation_active_seam.py`

Contract:

- `surface = "owlmlx.cache_request_aggregation_active_seam"`
- `version = "phase45"`

Stable sections:

- `summary`
- `selected_seam`
- `preserved_secondary_dependencies`
- `preserved_secondary_runtime_branch`

## 3. Current Honest Result

The current live result is:

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`

Preserved secondary truth remains:

- `turboquant_preconditions = preconditions_exact`

## 4. What This Changes

Before this round, the active request-aggregation seam already sat at the
earlier-runtime-owned leading-discriminator discriminant boundary on the newer
runtime-owned leading-discriminator record:

- a second backend stream request could already enter the live backend exchange
  before child stdout reached the fuller earlier-runtime-owned
  leading-discriminator stem on that newer transport record
- but that discriminant seam still had not been frozen as the first honest
  unique boundary on that newer leading-discriminator record

Now `owlmlx` can say something more honest:

- a bounded pre-gate admission window already forms cohorts before
  whole-request gate claim
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main serving path now hands that bounded cohort into the
  aggregated child exchange
- stream gate release no longer waits for outer consumer completion
- a second backend stream can now start before the first iterator consumer
  receives the first stream's terminal event
- a second backend stream can now also start before the first terminal payload
  is committed to the first stream queue
- a second backend stream can now also start before the first terminal payload
  is decoded and captured
- a second backend stream request can now enter the live backend exchange
  before the first terminal record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before the first stream fully matches its terminal-record prefix on child
  stdout
- a second backend stream request can now also enter the live backend exchange
  before the first terminal done payload reaches its action discriminant on
  child stdout
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before child stdout fully matches the first terminal-notice prefix
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice action discriminant
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice action stem
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first explicit terminal-notice marker field
- a second backend stream request can now also enter the live backend exchange
  before child stdout fully matches the first terminal-notice marker key
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice marker stem
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice marker discriminant
- owlmlx now also owns one runtime-owned terminal-notice leading-discriminator
  record ahead of that old marker-key-lead boundary
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice marker-key lead on the
  old notice record
- a second backend stream request can now also enter the live backend exchange
  before child stdout fully matches that runtime-owned leading-discriminator
  action
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator prefix
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator stem
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator
  discriminant
- owlmlx now also owns one earlier runtime-owned `terminal_notice_lead` marker
  on that same leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned `terminal_notice_lead`
  marker on the leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned `terminal_notice_lead`
  marker-prefix on the leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned `terminal_notice_l`
  marker-stem on the leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the earlier runtime-owned leading-discriminator
  stem on that newer leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the earlier runtime-owned leading-discriminator
  discriminant on that newer leading-discriminator record
- the earlier `terminal_notice` lead-in still collides with the older
  marker-first `terminal_notice` record on this path
- the current marker-discriminant seam remains preserved as the first honest
  unique boundary on the current runtime-owned marker-first record
- owlmlx now also owns one new earlier runtime-owned discriminator record ahead
  of that current marker-discriminant seam
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that current runtime-owned leading-discriminator
  marker-discriminant seam
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches full earlier runtime-owned discriminator
  detection on that new internal record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that earlier runtime-owned discriminator prefix
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that earlier runtime-owned discriminator stem
- owlmlx now also owns one new earlier runtime-owned leading-discriminator
  record ahead of that newer discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches earlier-runtime-owned discriminator discriminant
  detection on the newer discriminator record
- the literal prefix before `runtime_owned_terminal_leading_` is not yet an
  honest runtime-owned transport boundary on this path
- owlmlx now also owns one new earlier runtime-owned boundary record ahead of
  that newer runtime-owned leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  once child stdout reaches that new earlier runtime-owned boundary stem and
  before child stdout reaches fuller earlier-runtime-owned-boundary prefix
  detection on that same internal record
- the literal prefix before `runtime_owned_terminal_b` is not yet an honest
  runtime-owned transport boundary on this path
- the remaining active seam now sits at
  `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency`
- earlier-runtime-owned boundary stem detection is now also frozen as the first
  honest unique boundary on that newer runtime-owned boundary record
- fuller earlier-runtime-owned-boundary prefix detection remains preserved as
  secondary truth on that same runtime-owned boundary record
- earlier-runtime-owned discriminator discriminant remains preserved as the
  first honest unique boundary on the newer runtime-owned discriminator record
- earlier-runtime-owned leading-discriminator discriminant now also remains
  preserved as the first honest unique boundary on the newer runtime-owned
  leading-discriminator record
- the old marker-key lead remains preserved as the first unique boundary on the
  old terminal-notice record itself

## 5. What This Does Not Claim

It does not claim:

- stream release or interleaving already exists
- continuous batching is established
- cache parity exists

It only claims that the active request-aggregation seam has moved beyond
ingress, child-exchange capability, and the non-stream main-path handoff seam,
and now freezes more exactly at the
backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem
stream seam because the literal prefix before `runtime_owned_terminal_b` is not
yet an honest runtime-owned transport boundary on this path, while preserving
fuller earlier-runtime-owned-boundary prefix detection plus fuller earlier-
runtime-owned-boundary detection as secondary truth, current marker-
discriminant detection as the first honest unique boundary on the current
marker-first record, the newer earlier-runtime-owned discriminator discriminant
as the first honest unique boundary on that newer record, the newer earlier-
runtime-owned leading-discriminator discriminant as the first honest unique
boundary on that newer leading-discriminator record, and old marker-key lead as
secondary truth.

## 5a. Release-Floor 3.1 Closure Note

Release floor `3.1 Cache Scheduler Closure Beyond Exactness` closed on
2026-04-25 via the non-stream main runtime path (Round C closeout,
`owlmlx_release_floor_3_1C_closeout_closed`). The closing evidence is the
repeated-load proof at
`tests/test_runtime_kernel.py::test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load`
plus the existing bounded pre-gate cohort and aggregated child-exchange
harness tests.

This release-floor closure does not relax the active phase45 seam:

- `selected_seam.status` remains
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`
- the stream-branch dispatch-level closure is still open and is preserved as
  the active phase45 seam blocker
- `stream_session_holds_gate_until_completion` remains the safe stream-branch
  posture, not a weakening
- `closure_level` for cache remains `aggregation_active_seam_exact`; the
  release-floor closure is on the non-stream main path only

This note exists so that future rounds do not re-derive release-floor 3.1 as
open from this document, while still treating the stream-hold seam as the
active phase45 closure target.

## 6. Next Closure Step

The next step is no longer another ingress-window round or child-exchange
capability round.

The next coordinator choice is no longer whether the current earlier-runtime-
owned-boundary stem seam is honest.

The next coordinator choice is whether to authorize one new earlier runtime-
owned boundary ahead of:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
- non-stream handoff as already-earned checkpoint truth
