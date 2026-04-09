# owlmlx Master Outline

> Status: authoritative outline
> Updated: 2026-04-09

## 1. What `owlmlx` Is

`owlmlx` is our own runtime source of truth.

It is the project boundary where our Apple Silicon runtime direction becomes a
first-class system rather than a collection of patches attached to another
runtime.

## 2. What `owlmlx` Is Not

- Not a renamed `oMLX`
- Not a `vMLX` clone
- Not a desktop shell project
- Not the entire current desktop product shell repository
- Not a claim that every runtime path is already mature

## 3. Why `owlmlx` Must Exist

`owlmlx` exists because our runtime goals already exceed the scope of upstream
patching:

- Multi-model switching with explicit memory governance
- Switch-safe behavior under pressure and restart conditions
- Runtime truth exposure to upper layers
- Background-heavy serving paths for large-weight models

These are runtime-level goals, not temporary integration work.

## 4. Current Top-Level Product Truth

- `owlmlx` is our own runtime
- `owlmlx` is intended to replace `oMLX`
- `oMLX` and `vMLX` are borrowable reference systems, not identity sources
- The first mature runtime path is `large-weight runtime path`
- `Kimi` is the first validated specimen on that path
- the current desktop product shell repository sits above `owlmlx`

## 5. Core Documents

1. `master-outline.md`
2. `product-definition.md`
3. `system-architecture.md`
4. `repository-boundaries.md`
5. `runtime-capability-matrix.md`
6. `runtime-contracts.md`
7. `runtime-status-schema.md`
8. `runtime-governance.md`
9. `hazardous-operations.md`
10. `rename-strategy.md`
11. `contract-mapping.md`
12. `runtime-contract-adoption-plan.md`
13. `extraction-inventory.md`
14. `roadmap.md`

## 6. Current Dominant Question

The present task is not "how much code has moved yet?"

The present task is:

How do we freeze a correct runtime identity, architecture, and extraction
boundary so future implementation work lands in the right repository and under
the right truth model?
