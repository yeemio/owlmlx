# Phase 45: Pre-Claim Admission-Carrier Locality-Lifetime Coupling

> Status: frozen runtime truth
> Updated: 2026-04-16

## Surface

- `owlmlx.cache_pre_claim_admission_carrier_locality_lifetime_coupling`

## Frozen Truth

Once admission-carrier locality-isolation exactness is frozen, the remaining
ingress blocker narrows again:

- the bounded inert pre-claim carrier is coupled only to its own staged-
  request lifetime before claim
- it may be reclaimed only by same-request pre-claim discard or gate-claim
  expiry transition
- it may not survive into cross-request reuse or retained scheduler/backend/
  stream lifetime

This keeps pre-claim carrier lifetime inert and non-owning.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_admission_carrier_locality_lifetime_coupling.py --run-harness`

## Next Exact Question

After admission-carrier locality-lifetime coupling is frozen, the next local
cache question is:

- what exact clean-state reset reclaim leaves on that bounded inert carrier
  before any later staged request may reuse adjacent locality
- and whether reclaim can remain exact without leaking prior request history
