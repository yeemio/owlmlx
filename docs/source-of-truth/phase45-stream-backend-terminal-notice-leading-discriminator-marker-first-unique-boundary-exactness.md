# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker First-Unique-Boundary Exactness

> Status: authoritative
> Updated: 2026-04-18
> Scope: runtime-only stream exactness after runtime-owned leading-discriminator marker-discriminant detection is already the active seam

## 1. Purpose

Freeze the next exact stream decision once:

- the bounded pre-gate request-aggregation window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- one runtime-owned marker-first `terminal_notice_lead` record already exists
  ahead of the older marker-first `terminal_notice` record
- runtime-owned leading-discriminator marker detection, marker-prefix
  detection, and marker-stem detection are already preserved secondary truth
  on that newer record
- runtime-owned leading-discriminator marker-discriminant detection is already
  the current active seam

The question is:

- can `owlmlx` honestly narrow again before runtime-owned
  `terminal_notice_` marker-discriminant detection on that newer marker-first
  record, or is that already the first honest unique boundary on the current
  runtime-owned record

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_discriminant_dependency_still_blocked`
- `backend_terminal_notice_leading_discriminator_marker_first_unique_boundary.leading_discriminator_marker_first_unique_boundary_status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_first_unique_boundary.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_discriminant_is_first_unique_boundary_visible`

The active dependency therefore remains:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_discriminant_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could already say:

- a second backend stream request can enter the live backend exchange before
  child stdout reaches the fuller runtime-owned `terminal_notice_l`
  marker-stem on the newer marker-first record
- but the remaining exact seam still looked like
  `terminal_notice_` marker-discriminant detection without an explicit
  machine-readable statement about whether any earlier boundary was honest

Now `owlmlx` can say something narrower and more honest:

- the earlier `terminal_notice` lead-in still collides with the older
  marker-first `terminal_notice` record on this path
- runtime-owned `terminal_notice_` marker-discriminant detection is already
  the first honest unique boundary on the newer runtime-owned marker-first
  record
- so the active seam remains exactly where the live backend stream exchange is
  still blocked today

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the live serial boundary still remains at runtime-owned
leading-discriminator marker-discriminant detection, and that this boundary is
now frozen more honestly as the first unique boundary on the current
runtime-owned marker-first record.

## 6. Next Closure Step

The next coordinator choice is no longer whether the current
marker-discriminant seam is real.

The next coordinator choice is whether `owlmlx` should introduce a new earlier
runtime-owned marker-first discriminator ahead of:

- `backend_terminal_notice_leading_discriminator_marker_discriminant_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
