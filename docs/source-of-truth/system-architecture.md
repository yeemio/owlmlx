# owlmlx System Architecture

> Status: authoritative
> Updated: 2026-04-09

## 1. Layer Model

`owlmlx` should be understood as a layered system:

1. `MLX substrate`
2. `owlmlx core runtime`
3. `owlmlx runtime paths`
4. `product integration layer`

## 2. MLX Substrate

The bottom layer is Apple `MLX`.

This layer provides tensor execution and low-level model execution primitives.
It is foundational, but it does not define `owlmlx` as a product or runtime
program.

## 3. owlmlx Core Runtime

The core runtime layer is where `owlmlx` owns its actual runtime behavior.

This layer is responsible for:

- model load and unload behavior
- memory governance
- switching safety
- runtime introspection and truth surfaces
- serving behavior
- cache and state policy
- lifecycle safety under pressure

This is the layer that must become self-owned over time, even where early
implementation work still borrows ideas or code structure from other runtimes.

### 3.1 Adoption Model At The Core Layer

The core runtime layer follows the owlmlx adoption model: it owns identity,
principles, governance, truth contracts, and path semantics. It borrows freely
from MLX substrate, loader machinery, and proven open-source mechanisms.

Borrowed code entering the core runtime layer must be evaluated against owlmlx
runtime principles before it can be labeled `supported`. Until evaluated, it
enters as `partial` or `experimental`.

See `product-definition.md` section 6 for the formal adoption rule.

### 3.2 Core Runtime Principles

The `owlmlx` core runtime is organized around four non-optional principles:

1. memory governance under multi-model switching
2. switch safety with active-request protection
3. runtime truth exposure as a first-class contract
4. background-heavy serving as an explicit runtime posture where required

These principles define the core runtime more than any inherited codebase does.

### 3.3 Core Runtime Ownership

The following belong to the `owlmlx core runtime` layer:

- memory-pressure decisions
- load and unload policy
- eviction and reclaim policy
- switch-safe runtime coordination
- runtime status and truth surfaces
- serving mode classification
- path-level lifecycle policy
- hazardous-operation governance
- safe-resume and heavy-execution protocol ownership

The owned reference documents for those surfaces are:

- `runtime-contracts.md`
- `runtime-status-schema.md`
- `runtime-governance.md`
- `hazardous-operations.md`

## 4. owlmlx Runtime Paths

Above the core runtime sits a set of runtime paths.

A runtime path is a concrete serving and execution strategy shaped by model
class, operational constraints, and product honesty requirements.

### 4.1 Large-Weight Runtime Path

The first mature runtime path is `large-weight runtime path`.

Characteristics:

- built for very large-weight models
- background-heavy serving profile
- not treated as foreground-interactive by default
- requires explicit runtime truth and honest capability labels

`Kimi` is the first validated specimen on this path. It is a milestone, not the
name of the path.

### 4.2 Future Paths

Future runtime paths may exist for:

- generalized interactive serving
- specialized model families
- alternate cache or lifecycle strategies

Those paths should be added only when they have real capability truth, not
because the repository wants to sound broader than it is.

## 5. Product Integration Layer

The layer above `owlmlx` is the product integration layer, currently represented
by a desktop product shell repository family.

That layer is responsible for:

- desktop entry points
- routing and user-facing product integration
- operator dashboards and UI workflows
- packaging and product lifecycle

It consumes runtime truth from `owlmlx`. It does not define runtime truth for
`owlmlx`.

### 5.1 What The Product Layer Does Not Own

The product integration layer does not own:

- runtime memory-governance truth
- runtime switching-safety truth
- runtime path definitions
- runtime capability labels
- runtime identity
- runtime hazardous-operation policy
- safe-resume governance

It may present or orchestrate these, but it must not redefine them.

### 5.2 Extraction Direction

If code currently lives in the current desktop product shell repository but
primarily implements runtime memory governance, switching safety, runtime truth
exposure, or path-specific serving behavior, the long-term direction is
migration into `owlmlx`.

If code primarily implements desktop workflows, UI composition, onboarding,
dashboard presentation, or product shell packaging, it should remain outside the
runtime repository.

## 6. Architectural Principle

The key architectural rule is:

Runtime truth flows upward.

Desktop shell truth must not redefine the runtime boundary retroactively, and
borrowed upstream implementation details must not define `owlmlx`'s identity.
