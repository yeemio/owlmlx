# owlmlx Phase 45: Stream Backend Terminal-Record-Prefix Exactness

> Status: authoritative
> Updated: 2026-04-17
> Scope: runtime-only stream exactness after terminal-record capture is already decoupled from the live serial boundary

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

The question is no longer whether terminal-record prefix detection on child
stdout still owns the serial boundary.

The question is:

- does the remaining serial boundary still live at backend terminal-record
  prefix detection, or has that blocker narrowed again to backend terminal
  action discriminant detection before the full prefix is matched

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_record_prefix_exactness.py` now owns:

- `build_cache_stream_backend_terminal_record_prefix_exactness(...)`
- `cache_stream_backend_terminal_record_prefix_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_record_prefix_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_record_prefix_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_record_prefix`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_record_prefix_exact`
- `summary.verdict = backend_terminal_record_prefix_dependency_narrowed`
- `backend_terminal_record_prefix.prefix_status = backend_serial_boundary_decoupled_from_terminal_record_prefix_detection_visible`
- `backend_terminal_record_prefix.exchange_boundary = backend_terminal_action_discriminant_detected_before_full_record_prefix`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_action_discriminant_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection`

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
- but the remaining stream seam still looked like full terminal-record prefix
  detection on child stdout

Now `owlmlx` can say something narrower:

- a second backend stream still does not enter the live backend exchange
  immediately after the first stream emits its first token
- that second backend stream request is still blocked during the terminal
  window
- but it can enter the live backend exchange before the first stream fully
  matches its terminal-record prefix on child stdout
- the remaining exact blocker is therefore backend terminal action
  discriminant detection, not full terminal-record prefix detection

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the remaining stream seam is now narrower than
terminal-record prefix detection and that the live serial boundary is still
owned by the backend stream exchange until terminal action discriminant
detection.

## 6. Next Closure Step

The next coordinator choice is no longer whether terminal-record prefix
detection still owns the gate.

The next coordinator choice is whether `owlmlx` can narrow beyond:

- `backend_terminal_action_discriminant_dependency`

without breaking:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
