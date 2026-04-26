# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker Earlier Runtime-Owned Leading-Discriminator Exactness

> Status: authoritative
> Updated: 2026-04-20
> Scope: runtime-only stream exactness after earlier-runtime-owned discriminator discriminant detection was frozen as the first honest unique boundary on the newer runtime-owned discriminator record

## 1. Purpose

Freeze whether `owlmlx` can honestly introduce one new earlier runtime-owned
leading-discriminator record ahead of:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency`

without reopening governance, host, heavy-weight, interleaving, continuous
batching, or cache-parity claims.

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_introduced`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator.earlier_runtime_owned_leading_discriminator_status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection`

The active dependency therefore becomes:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, the current exact blocker still sat at earlier-runtime-owned
discriminator discriminant detection, and that boundary was already frozen as
the first honest unique boundary on the newer runtime-owned discriminator
record.

Now `owlmlx` can say something narrower and still honest:

- one new earlier runtime-owned leading-discriminator record now exists ahead
  of that newer runtime-owned discriminator record
- a second backend stream request can now be written once child stdout reaches
  that new earlier runtime-owned leading-discriminator record
- that write happens before child stdout reaches the newer earlier-runtime-
  owned discriminator discriminant boundary
- post-claim `max_concurrent = 1`, ticketed FIFO, and serial safety remain
  preserved

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the active stream seam now sits at earlier-runtime-owned
leading-discriminator detection.

## 6. Next Closure Step

The next coordinator choice is whether `owlmlx` can narrow again inside:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
