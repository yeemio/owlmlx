# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Exactness

> Status: authoritative
> Updated: 2026-04-18
> Scope: runtime-only stream exactness after terminal-notice marker-key-lead truth is already frozen

## 1. Purpose

Freeze the next exact stream dependency once:

- the bounded pre-gate request-aggregation window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- terminal-notice marker-key-lead truth is already frozen as the first unique
  boundary on the old terminal-notice record

The question is:

- should `owlmlx` keep key-lead detection as the current exact stream seam, or
  introduce a new earlier runtime-owned terminal-notice leading discriminator
  ahead of that old record boundary

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_notice_leading_discriminator`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_dependency_introduced`
- `backend_terminal_notice_leading_discriminator.leading_discriminator_status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection_visible`
- `backend_terminal_notice_leading_discriminator.exchange_boundary = backend_terminal_notice_leading_discriminator_detected_before_notice_marker_key_lead_detection`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` had already frozen:

- terminal-notice marker-key lead as the first unique boundary on the old
  terminal-notice record
- the earlier opening quote of that old record key was still not honest because
  it collided with ordinary `ok=true` stream records

Now `owlmlx` can say something narrower:

- one runtime-owned terminal-notice leading-discriminator record now exists
  ahead of the old marker-key-lead seam
- a second backend stream request can now be written once child stdout reaches
  that leading-discriminator record
- that second backend stream request can now be written before child stdout
  reaches the first terminal-notice marker-key lead on the old notice record
- the remaining exact stream seam now sits at terminal-notice
  leading-discriminator detection

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that `owlmlx` now owns one earlier runtime-owned transport
record ahead of the old key-lead seam, and the live serial boundary now
freezes at that new leading-discriminator detection.

## 6. Next Closure Step

The next coordinator choice is no longer whether `owlmlx` should introduce a
new earlier leading discriminator.

The next coordinator choice is whether the current
`backend_terminal_notice_leading_discriminator_dependency` seam can narrow
again on that runtime-owned transport record while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
