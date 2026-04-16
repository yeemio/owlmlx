# owlmlx Phase 45: Pre-Claim Marker Trigger Inputs

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only pre-claim marker discard-trigger inputs

## 1. Purpose

Freeze the exact discard-trigger inputs for inert pre-claim markers once marker
visibility is already exact.

## 2. Owned Contract

`owlmlx/cache_pre_claim_marker_trigger_inputs.py` now owns:

- `build_cache_pre_claim_marker_trigger_inputs(...)`
- `cache_pre_claim_marker_trigger_inputs_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_marker_trigger_inputs.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_marker_trigger_inputs"`
- `version = "phase45"`

Stable sections:

- `summary`
- `trigger_input_boundary`
- `forbidden_trigger_inputs`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = trigger_inputs_exact`

The trigger-input boundary is:

- `trigger_input_status = trigger_inputs_limited_to_explicit_pre_claim_drop_cancel_or_gate_claim_expiry`
- `unavailable_trigger_status = scheduler_child_stream_and_priority_inputs_unavailable_before_gate_claim`
- `allowed_trigger_inputs = ["explicit_pre_claim_drop_signal", "explicit_pre_claim_cancel_signal", "gate_claim_expiry_transition"]`

The forbidden trigger inputs are:

- `no_scheduler_pressure_input_before_claim`
- `no_child_backend_input_before_claim`
- `no_stream_disconnect_input_before_claim`
- `no_execution_priority_input_before_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- marker visibility was exact
- discard-trigger boundary was exact

Now it can say something narrower:

- the exact trigger inputs are frozen
- the remaining question is now reader/writer ownership, not generic trigger
  availability

## 5. What This Does Not Claim

It does not claim:

- scheduler pressure may clear a marker
- child/backend or stream events may clear a marker pre-claim
- trigger inputs may create hidden queue ownership

It only freezes the trigger-input boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze marker reader/writer ownership:

- which runtime-owned path may author a marker
- which may only observe it
- what exact writer ownership must remain unavailable until gate claim
