# Phase 45: Pre-Claim Marker Reclaim-Reset Exactness

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_reclaim_reset_exactness`

## Frozen Truth

Once marker locality-lifetime coupling is exact, the remaining ingress blocker
narrows again:

- reclaim clears the adjacent inert marker slot back to a fully empty inert
  state
- no prior request history or reclaim reason remains visible after reclaim
- later staged requests may reuse that locality only after a fully inert reset

This keeps reclaim/reset free of retained ownership or history-bearing reuse.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_reclaim_reset_exactness.py --run-harness`

## Next Exact Question

After marker reclaim-reset exactness is frozen, the next local cache question
is:

- what exact bounded admission-carrier construction could exist before gate
  claim
- and whether any such carrier can remain inert until the first runtime-owned
  boundary
