# owlmlx Phase 45: Stream Backend Terminal-Notice Marker-Key-Lead Exactness

> Status: authoritative
> Updated: 2026-04-18
> Scope: runtime-only stream exactness after terminal-notice marker-discriminant detection is already decoupled from the live serial boundary

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
- before the first terminal-notice record is fully captured
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
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the first terminal-notice marker stem
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the first terminal-notice marker discriminant

The question is no longer whether terminal-notice marker-discriminant detection
still owns the serial boundary.

The question is:

- does the remaining serial boundary still live at backend terminal-notice
  marker-key-lead detection, or is there any honest earlier live boundary
  before that first unique marker-key character inside the runtime-owned
  terminal-notice transport record

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_marker_key_lead_exactness.py` now owns:

- `build_cache_stream_backend_terminal_notice_marker_key_lead_exactness(...)`
- `cache_stream_backend_terminal_notice_marker_key_lead_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_marker_key_lead_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_notice_marker_key_lead_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_notice_marker_key_lead`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_marker_key_lead_exact`
- `summary.verdict = backend_terminal_notice_marker_key_lead_dependency_still_blocked`
- `backend_terminal_notice_marker_key_lead.notice_marker_key_lead_status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection_visible`
- `backend_terminal_notice_marker_key_lead.exchange_boundary = backend_terminal_notice_marker_key_lead_is_first_unique_notice_marker_boundary_visible`

The next active dependency therefore remains:

- `next_active_dependency.dependency = backend_terminal_notice_marker_key_lead_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- a second backend stream request could already enter the live backend exchange
  before child stdout reached the terminal-notice marker discriminant
- but the remaining stream seam still looked like key-lead detection without a
  machine-readable explanation of whether anything earlier was honest

Now `owlmlx` can say something more exact:

- a second backend stream request is still blocked during the terminal window
- and the current seam still remains at terminal-notice marker-key-lead
  detection
- because the earlier opening quote of that first key still collides with
  ordinary ok-true stream records on this path and is therefore not an honest
  earlier live boundary

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the live serial boundary is still owned by the backend
stream exchange until terminal-notice marker-key-lead detection, and that this
is now frozen more honestly as the first unique terminal-notice marker
boundary on this path.

## 6. Next Closure Step

The next coordinator choice is no longer whether key-lead detection is still
the active seam.

The next coordinator choice is whether `owlmlx` should introduce a new earlier
runtime-owned leading discriminator ahead of:

- `backend_terminal_notice_marker_key_lead_dependency`

without breaking:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
