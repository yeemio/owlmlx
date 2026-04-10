# owlmlx Master Outline

> Status: authoritative outline
> Updated: 2026-04-10

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
14. `autonomous-loop-discipline.md`
15. `large-weight-path-truth.md`
16. `roadmap.md`
17. `gemma-high-fidelity-role.md`
18. `training-substrate-contract.md`
19. `artifact-layout-contract.md`
20. `training-to-serving-contract.md`
21. `capability-absorption-inventory.md`

## 6. Adoption Model

`owlmlx` reuses open-source runtime mechanisms wherever they are proven. It does
not require full rewrite of every execution layer. What `owlmlx` owns is
identity, principles, governance, truth contracts, and path semantics. What it
borrows freely is MLX substrate, loader machinery, and proven serving patterns.

The formal adoption rule is frozen in `product-definition.md` section 6.

## 7. Autonomous Loop Discipline

`owlmlx` progresses through self-directed iteration rounds. Each round
identifies a dominant gap, executes against it, verifies delivery, and decides
whether to continue. The discipline is frozen in
`autonomous-loop-discipline.md`.

## 8. Current Dominant Question

The training-and-production program is complete. The platform capability
absorption and convergence program is now in progress. The current question is:

**Which mature capabilities from the original local LLM platform should owlmlx
absorb as runtime-owned truth, which must stay in the platform control-plane or
shell layers, and how do we prevent owlmlx from becoming a parallel system?**

Concrete sub-questions:

1. Where is the ownership boundary between owlmlx (runtime truth) and the
   platform (control-plane, routing, product entry)?
2. How do Gemma, Kimi 1T, gpt-oss-120b, and other model lines sit in the
   unified architecture?
3. Which absorption target should be first?
