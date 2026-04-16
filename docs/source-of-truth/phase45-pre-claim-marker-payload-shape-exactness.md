# Phase 45: Pre-Claim Marker Payload-Shape Exactness

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_payload_shape_exactness`

## Frozen Truth

Once marker immutability is exact, the remaining ingress blocker narrows again:

- before whole-request gate claim, marker state collapses to pure
  presence/absence only
- no reason-code payload may exist
- no priority payload may exist
- no queue-metadata or child/stream/execution payload fields may exist

This keeps the pre-claim marker shape fully inert and non-executable.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_payload_shape_exactness.py --run-harness`

## Next Exact Question

After marker payload shape is exact, the next local cache question is:

- what exact inert encoding carrier represents that presence/absence bit before
  gate claim
- and whether that encoding still avoids hidden queue ownership
