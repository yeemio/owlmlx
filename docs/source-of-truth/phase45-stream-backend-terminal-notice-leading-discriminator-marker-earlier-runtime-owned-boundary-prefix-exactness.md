# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker Earlier Runtime-Owned Boundary Prefix Exactness

> Status: authoritative
> Updated: 2026-04-22
> Scope: runtime-only stream exactness after one earlier runtime-owned boundary record was introduced ahead of the newer runtime-owned leading-discriminator record

## 1. Purpose

Freeze whether `owlmlx` can honestly narrow:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency`

down to an earlier prefix boundary on that same runtime-owned boundary record,
without reopening governance, host, heavy-weight, interleaving, continuous
batching, or cache-parity claims.

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency_narrowed`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix.earlier_runtime_owned_boundary_prefix_status = backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection`

The active dependency therefore becomes:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, the current exact blocker still sat at full earlier
runtime-owned boundary detection on the newer runtime-owned boundary record.

Now `owlmlx` can say something narrower and still honest:

- the live serial boundary is no longer coupled to full earlier runtime-owned
  boundary detection
- a second backend stream request can now enter the live backend exchange once
  child stdout reaches the earlier runtime-owned boundary prefix on that same
  internal record
- that second backend stream request can do so before child stdout reaches the
  fuller earlier runtime-owned boundary detection boundary
- post-claim `max_concurrent = 1`, ticketed FIFO, and serial safety remain
  preserved

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the active stream seam now sits at earlier runtime-owned
boundary prefix detection.

## 6. Next Closure Step

The next coordinator choice is whether `owlmlx` can narrow again inside:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
