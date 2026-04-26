# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker Earlier Runtime-Owned Discriminator Stem Exactness

> Status: authoritative
> Updated: 2026-04-20
> Scope: runtime-only stream exactness after the earlier runtime-owned discriminator prefix boundary became visible

## 1. Purpose

Freeze the next exact stream decision once:

- the bounded pre-gate request-aggregation window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- one earlier runtime-owned discriminator record already exists ahead of the
  current marker-discriminant seam
- that earlier runtime-owned discriminator prefix boundary is already visible

The question is:

- can `owlmlx` narrow again inside that same earlier runtime-owned discriminator
  record onto one earlier exact stem boundary without widening the story into
  interleaving, continuous batching, or cache parity

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_dependency_narrowed`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem.earlier_runtime_owned_discriminator_stem_status = backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection`

The active dependency therefore is now:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could already say:

- one new earlier runtime-owned discriminator record existed ahead of the
  current marker-discriminant seam
- a second backend stream request could already enter the live backend
  exchange once child stdout reached the earlier runtime-owned discriminator
  prefix on that new internal record

Now `owlmlx` can say something narrower:

- the live serial boundary is no longer coupled to that fuller earlier
  runtime-owned discriminator prefix boundary
- a second backend stream request can now enter the live backend exchange once
  child stdout reaches the earlier runtime-owned discriminator stem on that
  same internal record
- that second backend stream request can do so before child stdout reaches the
  fuller earlier runtime-owned discriminator prefix boundary

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the live serial boundary has moved from the fuller earlier
runtime-owned discriminator prefix boundary onto an earlier stem boundary inside
that same runtime-owned discriminator record.

## 6. Next Closure Step

The next coordinator choice is no longer whether the fuller earlier
runtime-owned discriminator prefix boundary is already the tightest seam on
this path.

The next coordinator choice is whether `owlmlx` should narrow again within:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
