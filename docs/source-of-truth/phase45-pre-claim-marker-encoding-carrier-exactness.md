# Phase 45: Pre-Claim Marker Encoding-Carrier Exactness

> Status: frozen runtime truth
> Updated: 2026-04-15

## Surface

- `owlmlx.cache_pre_claim_marker_encoding_carrier_exactness`

## Frozen Truth

Once marker payload shape is exact, the remaining ingress blocker narrows
again:

- before whole-request gate claim, marker presence may live only in one inert
  boolean slot
- that slot may not encode queue identity
- that slot may not encode ticket identity
- that slot may not encode child payload or stream/execution handles

This keeps the pre-claim marker encoding carrier inert and non-owning.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_marker_encoding_carrier_exactness.py --run-harness`

## Next Exact Question

After marker encoding carrier is exact, the next local cache question is:

- where that inert boolean slot is stored relative to staged metadata/ticket
  units
- and whether storage locality still avoids hidden queue ownership
