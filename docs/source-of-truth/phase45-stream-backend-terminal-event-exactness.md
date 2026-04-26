# owlmlx Phase 45: Stream Backend Terminal-Event Exactness

> Status: authoritative
> Updated: 2026-04-17
> Scope: runtime-only stream exactness after gate release is already decoupled from outer consumer drain

## 1. Purpose

Freeze the next exact stream dependency once:

- a bounded pre-gate request-aggregation/cohort window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange
- stream gate release is already decoupled from outer consumer completion

The question is no longer whether stream sessions hold the gate for the whole
outer consumer session.

The question is:

- does the remaining serial boundary still live at backend terminal-event
  commitment inside the live backend exchange, or has that blocker narrowed
  again to backend terminal-payload commit before iterator delivery of the
  terminal event

## 2. Owned Contract

`owlmlx/cache_stream_backend_terminal_event_exactness.py` now owns:

- `build_cache_stream_backend_terminal_event_exactness(...)`
- `cache_stream_backend_terminal_event_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_backend_terminal_event_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_backend_terminal_event_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `backend_terminal_event`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_backend_terminal_event_exact`
- `summary.verdict = backend_stream_terminal_event_dependency_narrowed`
- `backend_terminal_event.terminal_event_status = backend_terminal_event_serial_boundary_visible`
- `backend_terminal_event.exchange_boundary = backend_terminal_payload_commit_before_iterator_terminal_event_delivery`

The next active dependency is now:

- `next_active_dependency.dependency = backend_terminal_payload_commit_dependency`
- `next_active_dependency.status = backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- stream gate release no longer waited for outer consumer drain
- but the remaining stream seam still looked like backend terminal-event
  commitment in generic form

Now `owlmlx` can say something narrower:

- a second backend stream still does not enter the live backend exchange
  immediately after the first stream emits its first token
- that second backend stream is still blocked during the terminal-event window
- but it can start before the first iterator consumer receives the first
  stream's terminal event
- the remaining exact blocker is therefore backend terminal-payload commit
  inside the backend exchange, not terminal-event delivery to the iterator
  consumer

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the remaining stream seam is now narrower than backend
terminal-event delivery to the iterator consumer and that the live serial
boundary is still owned by the backend stream exchange until terminal-payload
commit.

## 6. Next Closure Step

The next coordinator choice is no longer whether backend terminal-event
delivery still owns the gate.

The next coordinator choice is whether `owlmlx` can narrow beyond:

- `backend_terminal_payload_commit_dependency`

without breaking:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
