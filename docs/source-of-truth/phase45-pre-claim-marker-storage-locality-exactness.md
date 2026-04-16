# Phase 45: Pre-Claim Marker Storage-Locality Exactness

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_storage_locality_exactness`

## Frozen Truth

Once marker encoding carrier is exact, the remaining ingress blocker narrows
again:

- before whole-request gate claim, the inert boolean marker slot may live only
  adjacent to staged metadata
- it must remain outside ticket identity
- it must remain outside immutable metadata payload
- it may not occupy queue, scheduler, child, stream, or execution-local
  storage

This keeps marker locality non-owning and non-executable.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_storage_locality_exactness.py --run-harness`

## Next Exact Question

After marker storage locality is exact, the next local cache question is:

- which exact pre-claim path may reach that adjacent inert slot
- and whether any locality reachability still remains free of hidden queue
  ownership
