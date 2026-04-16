# Phase 45: Pre-Claim Marker Locality-Access Exactness

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_locality_access_exactness`

## Frozen Truth

Once marker storage locality is exact, the remaining ingress blocker narrows
again:

- before whole-request gate claim only explicit pre-claim drop/cancel logic may
  access the adjacent inert marker slot
- gate-claim expiry may access it
- pre-claim discard may observe it
- scheduler, child/backend, stream, and execution-priority paths may not
  access it

This keeps marker locality reachability non-owning and non-executable.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_locality_access_exactness.py --run-harness`

## Next Exact Question

After marker locality access is exact, the next local cache question is:

- whether that adjacent inert slot is isolated per staged request
- or whether any shared pending-state locality still remains possible
