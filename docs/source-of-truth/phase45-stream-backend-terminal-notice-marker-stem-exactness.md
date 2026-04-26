# owlmlx Phase 45: Stream Backend Terminal-Notice Marker-Stem Exactness

> Status: authoritative
> Updated: 2026-04-18
> Scope: runtime-only stream exactness after terminal-notice marker-prefix detection is already decoupled from the live serial boundary

## 1. Purpose

Freeze the next exact stream dependency once:

- a bounded pre-gate request-aggregation/cohort window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- a second backend stream can already start before the first iterator consumer
  receives the first terminal event
- a second backend stream can already start before the first terminal payload
  is committed to the first stream queue
- a second backend stream can already start before the first terminal payload
  is decoded and captured
- a second backend stream request can already enter the live backend exchange
  before the first stream fully captures its terminal record
- a second backend stream request can already enter the live backend exchange
  before the first stream fully matches its terminal-record prefix
- a second backend stream request can already enter the live backend exchange
  before the first terminal done payload reaches its action discriminant
- a second backend stream request can already enter the live backend exchange
  before the first terminal-notice record is fully captured
- a second backend stream request can already enter the live backend exchange
  before child stdout fully matches the first terminal-notice prefix
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the first terminal-notice action discriminant
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the first terminal-notice action stem
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the first explicit terminal-notice marker field
- a second backend stream request can already enter the live backend exchange
  before child stdout fully matches the first terminal-notice marker key

The question is no longer whether terminal-notice marker-prefix detection still
owns the serial boundary.

The question is:

- does the remaining serial boundary still live at backend terminal-notice
  marker-stem detection, or has that blocker narrowed again to the earlier
  backend terminal-notice marker discriminant that first isolates the
  marker-key family before the stem is reached

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_marker_stem_exactness.py` now owns:

- `build_cache_stream_backend_terminal_notice_marker_stem_exactness(...)`
- `cache_stream_backend_terminal_notice_marker_stem_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_marker_stem_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_notice_marker_stem_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_notice_marker_stem`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_marker_stem_exact`
- `summary.verdict = backend_terminal_notice_marker_stem_dependency_narrowed`
- `backend_terminal_notice_marker_stem.notice_marker_stem_status = backend_serial_boundary_decoupled_from_terminal_notice_marker_stem_detection_visible`
- `backend_terminal_notice_marker_stem.exchange_boundary = backend_terminal_notice_marker_discriminant_detected_before_notice_marker_stem_detection`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_notice_marker_discriminant_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_discriminant_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- a second backend stream request could already enter the live backend exchange
  before child stdout fully matched the terminal-notice marker key
- but the remaining stream seam still looked like terminal-notice marker-stem
  detection

Now `owlmlx` can say something narrower:

- a second backend stream request is still blocked during the terminal window
- but it can enter the live backend exchange before child stdout reaches the
  terminal-notice marker stem
- the remaining exact blocker is therefore backend terminal-notice
  marker-discriminant detection, not terminal-notice marker-stem detection

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the remaining stream seam is now narrower than
terminal-notice marker-stem detection and that the live serial boundary is
still owned by the backend stream exchange until terminal-notice
marker-discriminant detection.

## 6. Next Closure Step

The next coordinator choice is no longer whether terminal-notice marker-stem
detection still owns the gate.

The next coordinator choice is whether `owlmlx` can narrow beyond:

- `backend_terminal_notice_marker_discriminant_dependency`

without breaking:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
