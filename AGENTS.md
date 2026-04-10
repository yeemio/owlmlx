# Agent Guide For `owlmlx`

This repository is the source-of-truth home for the `owlmlx` runtime line.

## Read Order

If a task does not specify a narrower entry point, read in this order:

1. `README.md`
2. `AGENTS.md`
3. `docs/source-of-truth/master-outline.md`
4. `docs/source-of-truth/product-definition.md`
5. `docs/source-of-truth/system-architecture.md`
6. `docs/source-of-truth/repository-boundaries.md`
7. `docs/source-of-truth/runtime-capability-matrix.md`
8. `docs/source-of-truth/runtime-contracts.md`
9. `docs/source-of-truth/runtime-status-schema.md`
10. `docs/source-of-truth/runtime-governance.md`
11. `docs/source-of-truth/hazardous-operations.md`
12. `docs/source-of-truth/rename-strategy.md`
13. `docs/source-of-truth/contract-mapping.md`
14. `docs/source-of-truth/extraction-inventory.md`
15. `docs/source-of-truth/autonomous-loop-discipline.md`
16. `docs/source-of-truth/roadmap.md`

## Non-Negotiable Project Truth

- `owlmlx` is our own runtime.
- `oMLX`, `vMLX`, and similar projects are reference inputs, not identity
  sources.
- `owlmlx` exists to replace `oMLX`, not to become a permanent patch stack on
  top of it.
- the current desktop product shell repository, historically referred to as
  `local-llm-platform`, sits above `owlmlx`.
- `Kimi` is a first validated specimen on the `large-weight runtime path`, not
  the permanent name of that path.
- `owlmlx` reuses open-source runtime mechanisms freely. Self-owned does not
  mean full rewrite. What is owned is identity, principles, governance, truth
  contracts, and path semantics.

## Writing Rules

- Keep capability labels honest: `supported`, `partial`, `experimental`, or
  `not in scope`
- Do not describe future generalization as current fact
- Do not collapse runtime truth and desktop product truth into one layer
- Do not describe `owlmlx` as "just a fork" or "just a wrapper"
- When borrowing ideas from external runtimes, rewrite them as `owlmlx`
  architecture, not as borrowed branding

## Boundary Discipline

This repository owns:

- Runtime identity
- Runtime architecture
- Runtime capability labels
- Runtime path definitions
- Runtime extraction and packaging plans

This repository does not own:

- Desktop UI source of truth
- Dashboard-first product narratives
- Generic platform orchestration truth unrelated to runtime internals

## Current Working Assumption

The repository is in source-of-truth bootstrap mode. Prefer clarifying
architecture, naming, capability boundaries, and extraction strategy before
adding large code imports.
