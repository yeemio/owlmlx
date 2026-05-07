# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker Earlier Runtime-Owned Boundary Earlier-Earlier-Boundary Exactness

> Status: authoritative
> Updated: 2026-05-07
> Scope: runtime-only stream exactness after a new distinct earlier-earlier runtime-owned boundary record was introduced ahead of the existing earlier-boundary record

## 1. Purpose

Freeze whether `owlmlx` can honestly introduce one distinct runtime-owned
terminal record ahead of:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency`

without reopening governance, host, heavy-weight, stream interleaving,
continuous batching, or cache-parity claims.

This is a backend-transport change, not a metadata-only freeze. It introduces
a new sentinel `runtime_owned_terminal_earlier_earlier_boundary` and a new
trigger `_earlier_e` (which is the first honest unique prefix that
distinguishes the new earlier-earlier-boundary record from the existing
earlier-boundary record). It also tightens the existing earlier-boundary
trigger from the shared `_e` prefix to `_earlier_b`, matching the
first-unique-boundary freeze that just shipped.

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_introduced`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary.earlier_runtime_owned_boundary_earlier_earlier_boundary_status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected_before_earlier_boundary_detection`

The active dependency therefore becomes:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could already say:

- earlier-runtime-owned-boundary earlier-boundary detection was already the
  first honest unique boundary on the newer earlier-boundary record (frozen
  metadata-only)
- the active stream seam sat at earlier-runtime-owned-boundary earlier-boundary
  detection
- the existing earlier-boundary trigger was the shared `_e` prefix

Now `owlmlx` can say something narrower and still honest:

- one distinct earlier-earlier runtime-owned terminal record now exists ahead
  of the existing earlier-boundary record
- the new child transport record is `runtime_owned_terminal_earlier_earlier_boundary`
- the existing earlier-boundary trigger is now tightened from `_e` to
  `_earlier_b`, the honest unique stem identified by the just-shipped
  first-unique-boundary freeze
- the new earlier-earlier-boundary trigger is `_earlier_e`, the first honest
  unique prefix that distinguishes the new record from the existing earlier-
  boundary record
- a second backend stream request can now be written once child stdout reaches
  `runtime_owned_terminal_earlier_earlier_boundary`
- that write happens before child stdout reaches `runtime_owned_terminal_earlier_boundary`,
  the existing earlier-boundary trigger
- the second-request timing fact is captured at request write time, not
  reconstructed after thread join
- post-claim `max_concurrent = 1`, ticketed FIFO, and serial safety remain
  preserved

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists
- customer-ready or replacement-ready status exists

It only claims that the active stream seam now sits at earlier-runtime-owned-
boundary earlier-earlier-boundary detection.

## 6. Next Closure Step

The next coordinator choice is whether `owlmlx` can narrow inside:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
- non-stream handoff as already-earned checkpoint truth
