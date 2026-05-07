# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Marker Earlier Runtime-Owned Boundary Earlier-Boundary First-Unique-Boundary Exactness

> Status: authoritative
> Updated: 2026-05-07
> Scope: runtime-only stream exactness after the new earlier-runtime-owned earlier-boundary record was introduced and is already the active seam

## 1. Purpose

Freeze whether `owlmlx` can honestly narrow again before earlier-runtime-owned
earlier-boundary detection on the newer earlier-boundary record, or whether
that seam is already the first honest unique boundary on that newer record.

This round does not introduce any new runtime-owned terminal record, does not
change post-claim serial invariants, and does not relax the active seam.

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.py`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency_still_blocked`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary.earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection_visible`
- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary.exchange_boundary = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_is_first_honest_unique_boundary_visible`

The active dependency therefore remains:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could already say:

- one distinct earlier runtime-owned terminal record
  (`runtime_owned_terminal_earlier_boundary`) exists ahead of the previous
  earlier-runtime-owned-boundary stem (`runtime_owned_terminal_b`)
- a second backend stream request can already be written once child stdout
  reaches `runtime_owned_terminal_earlier_boundary` and before it reaches
  `runtime_owned_terminal_b`
- the active stream seam sits at earlier-runtime-owned-boundary earlier-
  boundary detection

But the project still had not stated, with a machine-readable proof, whether
that earlier-boundary detection was already the first honest unique boundary
on the newer earlier-boundary record itself.

Now `owlmlx` can say something narrower and still honest:

- the literal prefix before `runtime_owned_terminal_earlier_b` is the same
  shared prefix `{"ok": true, "runtime_owned_terminal_` that also fronts the
  older runtime-owned boundary record on this path, so it is not yet an honest
  runtime-owned transport boundary
- earlier-runtime-owned-boundary earlier-boundary detection is therefore
  already the first honest unique boundary on the newer earlier-boundary record
- so the active seam stays exactly where the live backend stream exchange is
  still blocked today, and any further narrowing requires a real new earlier
  runtime-owned record

This is a metadata-only freeze. It does not change backend behavior, does not
relax post-claim `max_concurrent = 1`, ticketed FIFO, or serial-safety
invariants, and does not move the active seam.

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists
- any earlier live seam already exists
- the active phase45 seam has moved

It only claims that the existing earlier-boundary detection seam is already
the first honest unique boundary on its own newer earlier-boundary record.

## 6. Next Closure Step

The next coordinator choice is no longer whether the current earlier-runtime-
owned-boundary earlier-boundary seam is honest.

The next coordinator choice is whether to authorize one new earlier runtime-
owned record ahead of:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
- non-stream handoff as already-earned checkpoint truth
