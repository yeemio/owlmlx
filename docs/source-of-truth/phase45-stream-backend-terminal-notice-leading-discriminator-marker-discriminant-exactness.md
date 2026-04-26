# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker-Discriminant Exactness

> Status: authoritative
> Updated: 2026-04-18
> Scope: runtime-only stream exactness after runtime-owned `terminal_notice_l` marker-stem truth is already frozen

## 1. Purpose

Freeze the next exact stream dependency once:

- the bounded pre-gate request-aggregation window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- old terminal-notice marker-key-lead truth is already frozen as preserved old
  record truth
- one runtime-owned terminal-notice leading-discriminator record already exists
  ahead of that old record boundary
- one earlier runtime-owned `terminal_notice_lead` marker, one earlier
  runtime-owned `terminal_notice_lead` marker-prefix, and one earlier
  runtime-owned `terminal_notice_l` marker-stem are already frozen on that
  same record

The question is:

- should `owlmlx` keep runtime-owned `terminal_notice_l` marker-stem detection
  as the current exact stream seam, or can it narrow again to an even earlier
  runtime-owned `terminal_notice_` marker-discriminant on that same transport
  record

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_stem_dependency_narrowed`
- `backend_terminal_notice_leading_discriminator_marker_discriminant.leading_discriminator_marker_discriminant_status = backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_stem_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_discriminant.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_discriminant_detected_before_notice_leading_discriminator_marker_stem_detection`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_discriminant_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` had already frozen:

- one runtime-owned terminal-notice leading-discriminator record ahead of the
  old marker-key-lead seam
- one earlier runtime-owned `terminal_notice_lead` marker on that same record
- one earlier runtime-owned `terminal_notice_lead` marker-prefix on that same
  record
- one earlier runtime-owned `terminal_notice_l` marker-stem on that same
  record
- full leading-discriminator detection, leading-discriminator prefix
  detection, leading-discriminator stem detection, leading-discriminator
  discriminant detection, and full marker detection as preserved secondary
  truth on that runtime-owned record

Now `owlmlx` can say something narrower:

- a second backend stream request can now be written once child stdout reaches
  the earlier runtime-owned `terminal_notice_` marker-discriminant on that
  same record
- that second backend stream request can now be written before child stdout
  reaches the runtime-owned `terminal_notice_l` marker-stem on that same
  record
- the remaining exact stream seam now sits at backend terminal-notice
  leading-discriminator marker-discriminant detection

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that `owlmlx` has narrowed the live serial boundary one step
earlier on its own runtime-owned leading-discriminator transport record, while
keeping full leading-discriminator detection, leading-discriminator prefix
detection, leading-discriminator stem detection, leading-discriminator
discriminant detection, full marker detection, runtime-owned
`terminal_notice_lead` marker detection, runtime-owned
`terminal_notice_lead` marker-prefix detection, runtime-owned
`terminal_notice_l` marker-stem detection, and old marker-key lead as
preserved secondary truth.

## 6. Next Closure Step

The next coordinator choice is no longer whether runtime-owned
`terminal_notice_l` marker-stem detection is the current exact seam.

The next coordinator choice is whether the current
`backend_terminal_notice_leading_discriminator_marker_discriminant_dependency`
seam can narrow again on that same runtime-owned transport record while
preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
