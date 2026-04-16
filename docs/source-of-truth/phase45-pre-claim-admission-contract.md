# owlmlx Phase 45: Pre-Claim Admission Contract

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only cache scheduler ingress contract on the active path

## 1. Purpose

Freeze the exact contract for any future pre-claim seam on the current path
after the post-claim admission-hook safety contract is already exact.

## 2. Owned Contract

`owlmlx/cache_pre_claim_admission_contract.py` now owns:

- `build_cache_pre_claim_admission_contract(...)`
- `cache_pre_claim_admission_contract_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_admission_contract.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_admission_contract"`
- `version = "phase45"`

Stable sections:

- `summary`
- `possible_pre_claim_seam`
- `forbidden_pre_claim_actions`

## 3. Current Honest Result

The current exact result is:

- `contract_rung = pre_claim_contract_exact`

The only allowable future pre-claim seam is:

- `possible_pre_claim_seam = bounded_metadata_or_ticket_staging_before_gate_claim`

Its scope limit is:

- `pre_claim_scope_limit = may_stage_only_before_first_runtime_owned_gate_boundary`

The forbidden pre-claim actions are:

- `no_gate_claim_from_pre_claim_seam`
- `no_child_exchange_from_pre_claim_seam`
- `no_stream_start_from_pre_claim_seam`
- `no_model_execution_from_pre_claim_seam`

## 4. What This Changes

Before this round, `owlmlx` could say:

- any future pre-claim hook must preserve exact post-claim safety invariants
- no bounded pre-gate hook currently exists

Now it can say something narrower:

- if a future pre-claim seam exists at all, it is limited to bounded
  metadata/ticket staging before gate claim
- that seam is not allowed to become a hidden execution boundary
- batching remains pre-claim staging-contract work, not implied pre-claim model
  work

## 5. What This Does Not Claim

It does not claim:

- a safe staging seam is already implemented
- request aggregation is now runtime-owned
- child exchange, stream start, or model execution can move before gate claim

It only freezes the next exact contract boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze the bounded metadata/ticket staging
seam itself:

- what exact work may be staged before gate claim
- what metadata/ticket ownership is allowed there
- what must remain outside that seam until whole-request gate claim occurs
