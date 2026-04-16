# Phase 45: Pre-Claim Marker Clear/Observer Boundary

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_clear_observer_boundary`

## Frozen Truth

Once the inert pre-claim marker carrier is exact, the remaining ingress blocker
narrows again:

- only explicit pre-claim drop/cancel logic may clear the carrier
- gate-claim expiry may also clear it
- pre-claim discard may observe it, but may not gain clearer ownership

The following paths remain ineligible to clear the marker before gate claim:

- scheduler paths
- child/backend paths
- stream paths
- execution-priority paths

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_clear_observer_boundary.py --run-harness`

## Next Exact Question

After clearer/observer ownership is exact, the next local cache question is:

- whether any pre-claim path may mutate marker state beyond clear-only
  semantics
- or whether marker state must remain fully immutable before whole-request gate
  claim
