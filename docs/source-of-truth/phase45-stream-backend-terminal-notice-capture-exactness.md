# owlmlx Phase 45: Stream Backend Terminal-Notice Capture Exactness

> Status: authoritative
> Updated: 2026-04-17
> Scope: runtime-only stream exactness after terminal-action discriminant detection is already decoupled from the live serial boundary

## 1. Purpose

Freeze the next exact stream dependency once:

- a bounded pre-gate request-aggregation/cohort window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion
- a second backend stream can already start before the first iterator consumer
  receives the first stream's terminal event
- a second backend stream can already start before the first terminal payload
  is committed to the first stream queue
- a second backend stream can already start before the first terminal payload
  is decoded and captured
- a second backend stream request can already enter the live backend exchange
  before the first stream fully captures its terminal record from child stdout
- a second backend stream request can already enter the live backend exchange
  before the first stream fully matches its terminal-record prefix on child
  stdout
- a second backend stream request can already enter the live backend exchange
  before the first terminal done payload reaches its action discriminant on
  child stdout

The question is no longer whether full terminal-notice capture still owns the
serial boundary.

The question is:

- does the remaining serial boundary still live at backend terminal-notice
  capture, or has that blocker narrowed again to backend terminal-notice
  prefix detection before the full notice record is captured

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_notice_capture_exactness.py` now owns:

- `build_cache_stream_backend_terminal_notice_capture_exactness(...)`
- `cache_stream_backend_terminal_notice_capture_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_notice_capture_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_notice_capture_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_notice_capture`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_notice_capture_exact`
- `summary.verdict = backend_terminal_notice_capture_dependency_narrowed`
- `backend_terminal_notice_capture.notice_capture_status = backend_serial_boundary_decoupled_from_terminal_notice_capture_visible`
- `backend_terminal_notice_capture.exchange_boundary = backend_terminal_notice_prefix_detected_before_notice_capture`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_notice_prefix_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_prefix_detection`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- a second backend stream can already start before the first iterator consumer
  receives the terminal event
- it can already start before the first terminal payload is committed to the
  first stream queue
- it can already start before the first terminal payload is decoded and
  captured
- it can already enter the live backend exchange before the first stream fully
  captures its terminal record from child stdout
- it can already enter the live backend exchange before the first stream fully
  matches its terminal-record prefix on child stdout
- it can already enter the live backend exchange before the first terminal
  done payload reaches its action discriminant on child stdout
- but the remaining stream seam still looked like full terminal-notice capture

Now `owlmlx` can say something narrower:

- a second backend stream still does not enter the live backend exchange
  immediately after the first stream emits its first token
- that second backend stream request is still blocked during the terminal
  window
- but it can enter the live backend exchange before the first terminal-notice
  record is fully captured
- the remaining exact blocker is therefore backend terminal-notice prefix
  detection, not full terminal-notice capture

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the remaining stream seam is now narrower than
terminal-notice capture and that the live serial boundary is still owned by
the backend stream exchange until terminal-notice prefix detection.

## 6. Next Closure Step

The next coordinator choice is no longer whether terminal-notice capture still
owns the gate.

The next coordinator choice is whether `owlmlx` can narrow beyond:

- `backend_terminal_notice_prefix_dependency`

without breaking:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
