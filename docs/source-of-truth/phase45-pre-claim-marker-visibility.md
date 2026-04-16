# owlmlx Phase 45: Pre-Claim Marker Visibility

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only inert marker visibility before gate claim

## 1. Purpose

Freeze the exact visibility and discard-trigger boundary for inert pre-claim
drop/cancel markers once marker lifetime is already exact.

## 2. Owned Contract

`owlmlx/cache_pre_claim_marker_visibility.py` now owns:

- `build_cache_pre_claim_marker_visibility(...)`
- `cache_pre_claim_marker_visibility_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_marker_visibility.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_marker_visibility"`
- `version = "phase45"`

Stable sections:

- `summary`
- `marker_visibility_boundary`
- `forbidden_visibility_expansions`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = marker_visibility_exact`

The marker visibility boundary is:

- `marker_visibility_status = marker_visible_only_to_pre_claim_discard_and_gate_expiry_paths`
- `discard_trigger_status = discard_trigger_limited_to_explicit_pre_claim_discard_or_gate_claim_expiry`
- `allowed_visibility_readers = ["pre_claim_discard_path", "gate_claim_expiry_path"]`

The forbidden visibility expansions are:

- `no_scheduler_selection_visibility_before_claim`
- `no_child_dispatch_visibility_before_claim`
- `no_stream_visibility_before_claim`
- `no_execution_priority_visibility_before_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- inert marker lifetime was exact
- marker expiry boundary was exact

Now it can say something narrower:

- marker visibility is exact
- discard-trigger boundary is exact
- the remaining question is now exact trigger inputs, not generic marker
  visibility

## 5. What This Does Not Claim

It does not claim:

- markers influence scheduler selection
- markers are visible to child/stream execution paths
- markers create hidden queue ownership

It only freezes the visibility/discard-trigger boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze discard-trigger inputs:

- what exact pre-claim signal may clear a marker
- what exact trigger inputs must remain unavailable until gate claim
- what still must remain outside pre-claim ownership
