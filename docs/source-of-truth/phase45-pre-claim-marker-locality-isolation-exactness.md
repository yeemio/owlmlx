# Phase 45: Pre-Claim Marker Locality-Isolation Exactness

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_locality_isolation_exactness`

## Frozen Truth

Once marker locality access is exact, the remaining ingress blocker narrows
again:

- before whole-request gate claim the adjacent inert marker slot is isolated
  per staged request
- no shared scheduler pending-state locality may exist
- no shared backend/stream pending-state locality may exist
- no cross-request marker merge may exist

This keeps marker locality isolated and non-owning.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_locality_isolation_exactness.py --run-harness`

## Next Exact Question

After marker locality isolation is exact, the next local cache question is:

- how isolated marker locality is reclaimed or expired relative to staged
  request lifetime
- and whether lifetime coupling still avoids hidden queue ownership
