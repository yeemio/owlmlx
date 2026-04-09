# owlmlx

`owlmlx` is our own runtime.

It exists to become the runtime source of truth we actually need on Apple
Silicon, rather than a long-lived patch layer on top of someone else's
runtime. `oMLX` and `vMLX` matter to this project as reference points and
sources of proven ideas, not as identity anchors.

## Project Definition

`owlmlx` is a self-owned MLX runtime project with four frozen statements:

1. `owlmlx` is our own runtime.
2. Its direction is to replace `oMLX`, while absorbing useful experience from
   `oMLX`, `vMLX`, and other MLX runtimes as `owlmlx`'s own architecture.
3. The `large-weight runtime path` is the first mature path inside `owlmlx`;
   `Kimi` is the first validated specimen on that path, not the path's name.
4. The current desktop product shell repository, historically referred to as
   `local-llm-platform`, sits on top of `owlmlx` and is not a peer runtime
   source of truth.

## Why This Repository Exists

We are no longer solving a "patch upstream and hope it sticks" problem.

Our runtime direction already includes requirements that deserve their own
source of truth:

- Memory governance during multi-model switching
- Switch safety and restart-safe runtime behavior
- Runtime truth exposure to higher layers
- Background-heavy serving for workloads that do not fit interactive latency

Those goals are larger than a few upstream patches. They define a runtime
program.

## Current State

Current honest state:

- `owlmlx` is a runtime source-of-truth repository, not yet a code-heavy
  runtime implementation repository
- The first mature runtime path is the `large-weight runtime path`
- `Kimi` is the first validated specimen on that path
- the current desktop product shell repository remains the operator surface and
  product integration layer above this runtime

## What `owlmlx` Is Not

- Not a renamed `oMLX` fork
- Not a thin wrapper around `vMLX`
- Not a copy of the current desktop product shell repository
- Not a GUI or dashboard project
- Not a claim that generalized foreground runtime is already solved

## Document Map

- `docs/source-of-truth/master-outline.md`
- `docs/source-of-truth/product-definition.md`
- `docs/source-of-truth/system-architecture.md`
- `docs/source-of-truth/repository-boundaries.md`
- `docs/source-of-truth/runtime-capability-matrix.md`
- `docs/source-of-truth/runtime-contracts.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/runtime-governance.md`
- `docs/source-of-truth/hazardous-operations.md`
- `docs/source-of-truth/rename-strategy.md`
- `docs/source-of-truth/contract-mapping.md`
- `docs/source-of-truth/extraction-inventory.md`
- `docs/source-of-truth/roadmap.md`

## Immediate Priority

The current job of this repository is to freeze the runtime boundary and
architecture truth first. Code extraction and package layout come after the
source-of-truth layer is stable.
