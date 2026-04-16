# Phase 45: Pre-Claim Admission-Carrier Reclaim-Reset Exactness

> Status: frozen runtime truth
> Updated: 2026-04-16

## Surface

- `owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness`

## Frozen Truth

Once admission-carrier locality-lifetime coupling is frozen, the remaining
carrier question narrows again:

- reclaim resets the bounded inert pre-claim carrier back to a fully empty
  inert state before any later reuse
- no prior request history or execution-bearing residue remains visible after
  reclaim
- later staged requests may reuse adjacent locality only after that clean
  empty reset

This keeps reclaim/reset exact while preserving already-frozen post-claim
serial safety invariants.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_admission_carrier_reclaim_reset_exactness.py --run-harness`

## Next Exact Question

After admission-carrier reclaim/reset exactness is frozen, the next local
cache question is:

- whether the admission-carrier sub-branch is now complete enough for honest
  branch reselection
- or whether one narrower residual carrier subgap still remains and should be
  frozen explicitly
