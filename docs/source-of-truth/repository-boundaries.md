# owlmlx Repository Boundaries

> Status: authoritative
> Updated: 2026-04-09

## 1. Repository Mission

This repository owns the truth for the `owlmlx` runtime line.

Its primary job is to define and gradually absorb the runtime capabilities that
should live in a self-owned MLX runtime project.

## 2. What Belongs Here

The `owlmlx` repository owns:

- runtime identity and naming
- runtime architecture
- runtime path definitions
- runtime capability labels
- runtime memory governance strategy
- runtime switching safety strategy
- runtime truth exposure contracts
- runtime extraction and packaging plans

It also owns the formal runtime principles behind those capabilities:

- memory governance under multi-model switching
- switch safety and active-request protection
- runtime truth exposure
- background-heavy serving

## 3. What Does Not Belong Here

This repository does not own:

- desktop-shell-first product truth
- dashboard UX truth
- generic platform orchestration unrelated to runtime internals
- unrelated model catalog or onboarding narratives

Those belong in the current desktop product shell repository or other
product-level repositories.

## 4. Relationship To Existing Repositories

### 4.1 oMLX

`oMLX` is a replacement target and reference system.

If a capability is currently implemented there but is part of our runtime
future, the long-term answer is to define and own it inside `owlmlx`, not to
leave `owlmlx` as documentation for a permanent patch layer.

### 4.2 vMLX

`vMLX` is a reference system.

Useful serving, caching, packaging, or productization ideas may be studied and
re-expressed here, but they should enter this repository as `owlmlx`
architecture.

### 4.3 Current Product Shell Repository

The current desktop product shell repository sits above this repository.

It may temporarily contain runtime-adjacent glue while extraction is incomplete,
but the source-of-truth direction is that runtime identity and runtime
architecture belong here.

## 5. Runtime Vs Platform Shell Boundary

### 5.1 owlmlx Runtime Source Of Truth Owns

`owlmlx` owns:

- runtime principles
- runtime path definitions
- runtime capability labels
- runtime memory and switching semantics
- runtime truth contracts
- extraction direction for runtime-owned logic

### 5.2 Product Shell Owns

The current desktop product shell repository owns:

- desktop shell workflows
- user-facing routing and integration behavior
- control-plane presentation
- onboarding and product entry
- product packaging above the runtime

### 5.3 Code That Should Eventually Move Into owlmlx

Code should eventually migrate into `owlmlx` when it primarily implements:

- memory-governance decisions
- eviction, reclaim, or restart-safe runtime logic
- active-request-aware switching logic
- runtime truth exposure contracts
- large-weight path serving behavior owned as runtime truth

### 5.4 Code That Should Stay In The Platform Shell

Code should remain in the current desktop product shell repository when it
primarily implements:

- desktop UI
- dashboard rendering and operator UX
- onboarding sequences
- shell-level routing composition
- product integration around runtime outputs

## 6. Extraction Map Discipline

Each capability should be classified one of three ways:

1. `owlmlx-owned judgment`
2. `borrow and internalize`
3. `external reference only`

A capability cannot be labeled `supported` for `owlmlx` until it is at least
classified as `owlmlx-owned judgment` and represented in this repository's
truth.

## 7. Boundary Test

A change probably belongs in `owlmlx` when it answers one of these questions:

- What should the runtime itself do?
- What runtime state must be visible and authoritative?
- What runtime path exists and what is it honestly capable of?
- What safety or memory rule should govern runtime behavior?

A change probably does not belong in `owlmlx` when it mainly answers:

- How should the desktop shell present this?
- How should product onboarding explain this?
- How should a control-plane screen arrange this?

## 8. Extraction Rule

If implementation currently lives elsewhere but clearly matches `owlmlx`'s owned
boundary, the right long-term direction is extraction into `owlmlx`, not
boundary drift in the documentation.

The current working inventory for that process lives in
`extraction-inventory.md`.
