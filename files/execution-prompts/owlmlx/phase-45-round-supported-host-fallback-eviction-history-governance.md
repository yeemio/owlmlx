# owlmlx Phase 45 Round: Supported-Host Fallback Eviction-History Governance

## Branch

`Branch B`

## Why This Round Exists

- supported-host baseline establishment is still exact-blocked locally
- cache remains frozen at `structural_ingress_seam_introduced`
- runtime pinning already exists
- runtime TTL policy now exists
- the remaining governance policy gap is now only:
  - `eviction_history_governance`

## Dominant Objective

Add one minimal runtime-owned eviction-history governance surface or control
that shrinks the last remaining local policy gap without widening cache or
claiming broader multi-model parity.

## Hard Rules

- work only in `owlmlx`
- do not reopen cache widening
- do not touch shell/control-plane/UI repos
- do not claim full multi-model closure
- keep the round bounded to runtime-owned eviction-history governance

## Acceptance

1. `owlmlx` gains one real eviction-history governance ability or exact
   runtime-owned governance truth
2. tests and live script prove it
3. `customer_runtime_evidence` and `replacement-grade-stability-gaps` stay
   honest
4. dominant-gap truth updates only if the gap actually moves
