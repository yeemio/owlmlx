# Phase 45: Pre-Claim Marker Locality-Lifetime Coupling

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_locality_lifetime_coupling`

## Frozen Truth

Once marker locality isolation is exact, the remaining ingress blocker narrows
again:

- the isolated adjacent marker slot is coupled only to its own staged-request
  lifetime before whole-request gate claim
- reclaim may occur only by same-request pre-claim discard or same-request
  gate-claim expiry transition
- no cross-request slot reuse, scheduler-retained lifetime, backend/stream
  retained lifetime, or execution entitlement may emerge from that coupling

This keeps isolated marker locality lifetime-coupled but still non-owning.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_locality_lifetime_coupling.py --run-harness`

## Next Exact Question

After marker locality-lifetime coupling is exact, the next local cache question
is:

- what exact clean-state reset remains in the adjacent inert slot after reclaim
- and whether any later staged request may reuse that locality only after a
  fully inert reset
