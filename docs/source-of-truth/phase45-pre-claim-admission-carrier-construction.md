# Phase 45: Pre-Claim Admission-Carrier Construction

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_admission_carrier_construction`

## Frozen Truth

Once marker reclaim-reset exactness is frozen, the remaining ingress blocker
narrows again:

- any bounded pre-claim admission carrier may be constructed only from already
  frozen inert units
- the only allowed units are immutable request metadata, observational ticket
  reservation, and a fully reset inert marker slot
- no queue-owned, execution-bearing, child/stream-attached, or scheduler-priority
  carrier may exist before whole-request gate claim

This keeps admission-carrier construction inert and non-owning.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_admission_carrier_construction.py --run-harness`

## Next Exact Question

After admission-carrier construction is exact, the next local cache question
is:

- what exact fields may inhabit that bounded inert carrier before gate claim
- and whether any field set can remain inert without turning the carrier into
  hidden queue ownership
