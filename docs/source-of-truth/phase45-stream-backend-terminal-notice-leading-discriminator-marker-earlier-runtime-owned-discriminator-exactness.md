# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker Earlier Runtime-Owned Discriminator Exactness

> Status: authoritative
> Updated: 2026-04-18
> Scope: runtime-only stream exactness after the current marker-discriminant seam was frozen as the first honest unique boundary on the current marker-first record

## 1. Purpose

Freeze the next exact stream decision once:

- the bounded pre-gate request-aggregation window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- runtime-owned leading-discriminator marker-discriminant detection is already
  frozen as the first honest unique boundary on the current marker-first
  record

The question is:

- can `owlmlx` introduce one genuinely earlier runtime-owned discriminator
  record ahead of that current marker-discriminant seam without widening the
  story into interleaving, continuous batching, or cache parity

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_introduced`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator.earlier_runtime_owned_discriminator_status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected_before_notice_leading_discriminator_marker_discriminant_detection`

The active dependency therefore is now:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could already say:

- runtime-owned leading-discriminator marker-discriminant detection was the
  first honest unique boundary on the current marker-first record
- but the live backend stream exchange still had no earlier runtime-owned
  record to release on before reaching that seam

Now `owlmlx` can say something narrower:

- one new earlier runtime-owned discriminator record now exists ahead of the
  current marker-first `terminal_notice_lead` record
- a second backend stream request can now enter the live backend exchange once
  child stdout reaches that new runtime-owned discriminator
- that second backend stream request can do so before child stdout reaches the
  current runtime-owned leading-discriminator marker-discriminant seam

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the live serial boundary has moved from the current
marker-discriminant seam onto one new earlier runtime-owned discriminator
record.

## 6. Next Closure Step

The next coordinator choice is no longer whether a genuinely earlier
runtime-owned discriminator can be introduced.

The next coordinator choice is whether `owlmlx` should narrow again within:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
