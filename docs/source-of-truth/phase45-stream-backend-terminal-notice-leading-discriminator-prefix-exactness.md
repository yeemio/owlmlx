# owlmlx Phase 45: Stream Backend Terminal-Notice Leading-Discriminator Prefix Exactness

> Status: authoritative
> Updated: 2026-04-18
> Scope: runtime-only stream exactness after runtime-owned leading-discriminator truth is already frozen

## 1. Purpose

Freeze the next exact stream dependency once:

- the bounded pre-gate request-aggregation window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- terminal-notice marker-key-lead truth is already frozen as preserved old
  record truth
- one runtime-owned terminal-notice leading-discriminator record already exists
  ahead of that old record boundary

The question is:

- should `owlmlx` keep full runtime-owned leading-discriminator detection as
  the current exact stream seam, or can it narrow again to an earlier unique
  prefix on that same runtime-owned transport record

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness.py`
now owns:

- `build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness(...)`
- `cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_notice_leading_discriminator_prefix`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_leading_discriminator_prefix_exact`
- `summary.verdict = backend_terminal_notice_leading_discriminator_dependency_narrowed`
- `backend_terminal_notice_leading_discriminator_prefix.leading_discriminator_prefix_status = backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_detection_visible`
- `backend_terminal_notice_leading_discriminator_prefix.exchange_boundary = backend_terminal_notice_leading_discriminator_prefix_detected_before_notice_leading_discriminator_detection`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_notice_leading_discriminator_prefix_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_prefix_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` had already frozen:

- one runtime-owned terminal-notice leading-discriminator record ahead of the
  old marker-key-lead seam
- full leading-discriminator detection as the current exact blocker inside the
  live backend exchange

Now `owlmlx` can say something narrower:

- a second backend stream request can now be written once child stdout reaches
  an earlier unique prefix on that runtime-owned leading-discriminator record
- that second backend stream request can now be written before child stdout
  fully matches the full leading-discriminator action on that record
- the remaining exact stream seam now sits at terminal-notice
  leading-discriminator prefix detection

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that `owlmlx` has narrowed the live serial boundary one step
earlier on its own runtime-owned leading-discriminator transport record, while
keeping old marker-key lead as preserved secondary truth on the old notice
record.

## 6. Next Closure Step

The next coordinator choice is no longer whether full runtime-owned
leading-discriminator detection is the current exact seam.

The next coordinator choice is whether the current
`backend_terminal_notice_leading_discriminator_prefix_dependency` seam can
narrow again on that same runtime-owned transport record while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
