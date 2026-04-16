# Phase 45: Pre-Claim Admission-Carrier Branch Reselection

> Status: frozen runtime truth
> Updated: 2026-04-16

## Surface

- `owlmlx.cache_pre_claim_admission_carrier_branch_reselection`

## Frozen Truth

Once admission-carrier reclaim/reset exactness is frozen, the carrier-local
chain is complete enough for honest reselection:

- the admission-carrier exactness chain is complete on the current path
- no narrower residual carrier subgap remains open
- the next cache sub-branch moves back to scheduler-vs-TurboQuant reselection

This does not claim cache closure. It only says the carrier-local branch is no
longer the next honest reduction target.

## Operator Entry

- `python3 scripts/runtime_cache_pre_claim_admission_carrier_branch_reselection.py --run-harness`

## Next Exact Question

After admission-carrier branch reselection is frozen, the next local cache
question is:

- which non-carrier cache branch should be reduced next without regressing the
  already-frozen ingress invariants
