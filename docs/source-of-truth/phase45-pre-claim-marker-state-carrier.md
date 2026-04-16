# Phase 45: Pre-Claim Marker State-Carrier

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_state_carrier`

## Frozen Truth

Once pre-claim marker reader/writer ownership is exact, the remaining cache
ingress question narrows again:

- owlmlx may hold a pre-claim marker only in a single inert write-once /
  clear-only record before whole-request gate claim
- that record may not become:
  - queue slot identity
  - batch membership
  - child payload attachment
  - stream or execution state

This keeps the pre-claim carrier inert and prevents hidden queue ownership from
forming before the first runtime-owned boundary.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_state_carrier.py --run-harness`

## Next Exact Question

After the inert carrier is exact, the next local cache question is:

- which path may clear that carrier
- which path may only observe it
- and which clearer expansions must remain unavailable before gate claim
