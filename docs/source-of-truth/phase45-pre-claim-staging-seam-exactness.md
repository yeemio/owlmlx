# owlmlx Phase 45: Pre-Claim Staging Seam Exactness

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only cache scheduler ingress staging seam on the active path

## 1. Purpose

Freeze the exact bounded staging seam, if any, that may exist before
whole-request gate claim after the broader pre-claim admission contract is
already exact.

## 2. Owned Contract

`owlmlx/cache_pre_claim_staging_seam_exactness.py` now owns:

- `build_cache_pre_claim_staging_seam_exactness(...)`
- `cache_pre_claim_staging_seam_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_staging_seam_exactness.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_staging_seam_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `allowed_staging_units`
- `forbidden_staging_expansions`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = staging_seam_exact`

The only allowed pre-claim staging units are:

- `immutable_request_metadata_snapshot`
- `ticket_reservation_without_gate_claim`

The seam boundary is:

- `staging_must_stop_before_first_runtime_owned_gate_boundary`

The forbidden staging expansions are:

- `no_gate_ownership_transfer_before_claim`
- `no_child_payload_assembly_before_claim`
- `no_stream_handle_allocation_before_claim`
- `no_model_state_or_prefill_before_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- a pre-claim seam, if it exists, is limited to bounded metadata/ticket staging
- the seam must not claim the gate or start execution work

Now it can say something narrower:

- the allowed staged units are exact
- the seam is limited to immutable request metadata plus ticket reservation
- child, stream, and model work remain outside that seam

## 5. What This Does Not Claim

It does not claim:

- request aggregation is now implemented
- a cohort window exists
- any pre-claim seam may allocate execution state

It only freezes the next exact boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze ownership/lifetime boundaries for the
allowed staged units themselves:

- what exact ownership a ticket reservation has before gate claim
- what exact metadata may be snapshotted pre-claim
- what must still wait until whole-request gate claim occurs
