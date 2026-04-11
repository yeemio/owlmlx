# owlmlx Master Outline

> Status: authoritative outline
> Updated: 2026-04-11

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
- `Gemma` is the production mainline model (training substrate verified, pilot PASS)
- the current desktop product shell repository sits above `owlmlx`

## 5. Core Documents

1. `master-outline.md`
2. `ARCHITECTURE-TRUTH.md`
3. `product-definition.md`
4. `system-architecture.md`
5. `repository-boundaries.md`
6. `runtime-capability-matrix.md`
7. `runtime-kernel-mvp.md`
8. `runtime2-benchmark-baseline.md`
9. `runtime1-environment-diagnostics.md`
10. `runtime3-serving-surface.md`
11. `runtime3-benchmark-and-streaming.md`
12. `runtime-contracts.md`
13. `runtime-status-schema.md`
14. `runtime-governance.md`
15. `hazardous-operations.md`
16. `rename-strategy.md`
17. `contract-mapping.md`
18. `runtime-contract-adoption-plan.md`
19. `extraction-inventory.md`
20. `autonomous-loop-discipline.md`
21. `large-weight-path-truth.md`
22. `roadmap.md`
23. `gemma-high-fidelity-role.md`
24. `training-substrate-contract.md`
25. `artifact-layout-contract.md`
26. `training-to-serving-contract.md`
27. `capability-absorption-inventory.md`
28. `ownership-boundary.md`
29. `model-line-placement.md`
30. `first-absorption-target.md`
31. `convergence-posture.md`
32. `hypura-overflow-path-reference.md`
33. `model-lineage-schema.md`
34. `cache-truth-contract.md`

## 6. Adoption Model

`owlmlx` reuses open-source runtime mechanisms wherever they are proven. It does
not require full rewrite of every execution layer. What `owlmlx` owns is
identity, principles, governance, truth contracts, and path semantics. What it
borrows freely is MLX substrate, loader machinery, and proven serving patterns.

External systems such as Hypura may be recorded as research references when
they illuminate future runtime paths. Recording a reference does not promote it
to an adopted backend or supported owlmlx capability.

The formal adoption rule is frozen in `product-definition.md` section 6.

## 7. Autonomous Loop Discipline

`owlmlx` progresses through self-directed iteration rounds. Each round
identifies a dominant gap, executes against it, verifies delivery, and decides
whether to continue. The discipline is frozen in
`autonomous-loop-discipline.md`.

## 8. Current Dominant Question

Runtime-3 is now complete. The next question is:

**How does owlmlx move from a completed Runtime-3 serving surface into a more
deployable Runtime-4 serving runtime with stronger transport semantics,
reliability policy, and platform-facing migration seams?**
