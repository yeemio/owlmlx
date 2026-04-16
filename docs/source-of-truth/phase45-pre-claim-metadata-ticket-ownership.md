# owlmlx Phase 45: Pre-Claim Metadata/Ticket Ownership

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only cache scheduler inert pre-claim state on the active path

## 1. Purpose

Freeze the exact ownership/lifetime boundary for the only staged units that may
exist before whole-request gate claim.

## 2. Owned Contract

`owlmlx/cache_pre_claim_metadata_ticket_ownership.py` now owns:

- `build_cache_pre_claim_metadata_ticket_ownership(...)`
- `cache_pre_claim_metadata_ticket_ownership_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_metadata_ticket_ownership.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_metadata_ticket_ownership"`
- `version = "phase45"`

Stable sections:

- `summary`
- `ownership_boundary`
- `forbidden_promotions`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = ownership_boundary_exact`

The ownership boundary is:

- `ticket_ownership_status = reservation_only_no_execution_rights_before_gate_claim`
- `metadata_ownership_status = immutable_snapshot_only_no_mutation_rights_before_gate_claim`
- `ownership_scope_boundary = pre_claim_state_is_inert_until_gate_claim`

The forbidden promotions are:

- `no_gate_claim_rights_from_ticket_reservation`
- `no_mutable_request_state_from_metadata_snapshot`
- `no_child_or_stream_handle_derivation_before_claim`
- `no_model_execution_entitlement_before_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- only metadata/ticket staging may exist pre-claim
- that seam cannot expand into child/stream/model work

Now it can say something narrower:

- ticket reservation is inert and observational-only
- metadata snapshot is inert and read-only
- the remaining question is not ownership anymore, but what cohort/drop
  semantics can exist on that inert state

## 5. What This Does Not Claim

It does not claim:

- a real cohort window exists
- request aggregation exists
- any inert pre-claim state may gain execution rights

It only freezes the ownership/lifetime boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze inert-state cohort/drop semantics:

- what exact cohort candidacy can exist on inert ticket/metadata state
- what exact drop/cancel semantics are allowed before gate claim
- what still must wait until whole-request gate claim occurs
