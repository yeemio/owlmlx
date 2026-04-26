# owlmlx Phase 45: Stream Backend Terminal-Payload-Capture Exactness

> Status: authoritative
> Updated: 2026-04-17
> Scope: runtime-only stream exactness after terminal-payload commit is already decoupled from the live serial boundary

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

The question is no longer whether terminal-payload commit to the first stream
queue still owns the serial boundary.

The question is:

- does the remaining serial boundary still live at backend terminal-payload
  capture under the subprocess I/O lock, or has that blocker narrowed again to
  backend terminal-record capture on child stdout before payload decode

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_payload_capture_exactness.py` now owns:

- `build_cache_stream_backend_terminal_payload_capture_exactness(...)`
- `cache_stream_backend_terminal_payload_capture_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_payload_capture_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_payload_capture_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_payload_capture`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_payload_capture_exact`
- `summary.verdict = backend_terminal_payload_capture_dependency_narrowed`
- `backend_terminal_payload_capture.payload_capture_status = backend_serial_boundary_decoupled_from_terminal_payload_capture_visible`
- `backend_terminal_payload_capture.exchange_boundary = backend_terminal_record_capture_before_payload_decode`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_record_capture_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- a second backend stream can already start before the first iterator consumer
  receives the terminal event
- and it can already start before the first terminal payload is committed to
  the first stream queue
- but the remaining stream seam still looked like terminal-payload capture
  under the subprocess I/O lock

Now `owlmlx` can say something narrower:

- a second backend stream still does not enter the live backend exchange
  immediately after the first stream emits its first token
- that second backend stream is still blocked during the terminal window
- but it can start before the first stream decodes and captures its terminal
  payload
- the remaining exact blocker is therefore backend terminal-record capture on
  child stdout, not terminal-payload capture

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the remaining stream seam is now narrower than
terminal-payload capture and that the live serial boundary is still owned by
the backend stream exchange until terminal-record capture.

## 6. Next Closure Step

The next coordinator choice is no longer whether terminal-payload capture still
owns the gate.

The next coordinator choice is whether `owlmlx` can narrow beyond:

- `backend_terminal_record_capture_dependency`

without breaking:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
