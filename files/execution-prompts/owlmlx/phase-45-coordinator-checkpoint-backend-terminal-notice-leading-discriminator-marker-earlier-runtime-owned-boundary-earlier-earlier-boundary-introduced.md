# owlmlx Phase 45 Coordinator Checkpoint - Backend Terminal Notice Leading-Discriminator Marker Earlier Runtime-Owned Boundary Earlier-Earlier-Boundary Introduced

## Verdict

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_introduced`

This round is a real backend-transport change, not a metadata-only freeze.
A new sentinel record was added; the existing trigger was tightened; the
active seam moved.

## What Is Now Frozen Exact

- one distinct earlier-earlier runtime-owned terminal record now exists ahead
  of the existing earlier-boundary record
- new transport record: `runtime_owned_terminal_earlier_earlier_boundary`
- the existing earlier-boundary trigger has been tightened from the shared
  `_e` prefix to `_earlier_b` (the honest unique stem identified by the
  prior first-unique-boundary freeze)
- the new earlier-earlier trigger is `_earlier_e` (the first honest unique
  prefix that distinguishes the new record from the existing earlier-boundary
  record)
- a new debug hook
  `_stream_debug_before_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
  fires before the new earlier-earlier detection in the live stream parser
- a new sentinel-record filter
  `_is_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_earlier_earlier_boundary_record`
  drops the new record from token-event production
- a second backend stream request can now be written after child stdout
  reaches `runtime_owned_terminal_earlier_earlier_boundary` and before child
  stdout reaches `runtime_owned_terminal_earlier_boundary`
- the second-request timing fact is captured at write time, not reconstructed
  after thread join
- post-claim serial invariants remain preserved:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`
- customer/runtime evidence surface now also recognises the new seam and
  routes to the earlier-earlier-boundary recommended-next-step branch when
  selected_seam matches the new dependency

## Current Cache Truth

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- `preserved_secondary_runtime_branch = turboquant_preconditions`
- `preserved_secondary_runtime_branch.status = preconditions_exact`
- previous earlier-boundary detection (and its first-unique-boundary freeze)
  remain preserved as secondary truth on the existing earlier-boundary record

## What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists
- customer-ready / replacement-ready status exists
- the active seam has reached anything earlier than
  `runtime_owned_terminal_earlier_earlier_boundary`

## Exact Next Decision

The next coordinator choice is whether to freeze the symmetric first-unique-
boundary metadata claim on the new earlier-earlier-boundary record (i.e.
prove `_earlier_e` is the first honest unique boundary on that newer record),
OR to introduce yet another even-earlier sentinel record. Either path is
authorized, but each must remain inside:

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
- non-stream handoff as already-earned checkpoint truth
