# owlmlx Product Definition

> Status: authoritative
> Updated: 2026-04-09

## 1. Formal Definition

`owlmlx` is our self-owned runtime project for MLX-based model serving and
runtime management on Apple Silicon.

Its role is to become the runtime source of truth for the capabilities we
actually need, rather than extending another runtime indefinitely through local
patches and integration glue.

## 2. Frozen Project Statements

The repository is defined by four frozen statements:

1. `owlmlx` is our own runtime.
2. Its direction is to replace `oMLX`, while absorbing valuable ideas from
   `oMLX`, `vMLX`, and related systems as `owlmlx`'s own architecture.
3. The `large-weight runtime path` is the first mature path inside `owlmlx`;
   `Kimi` is the first validated specimen on that path.
4. The desktop product shell and integration layer above `owlmlx` is not the
   runtime source of truth, regardless of current repository naming.

## 3. Why This Is a Runtime Project

`owlmlx` is justified by runtime-specific goals that have already emerged in our
work:

- Multi-model switching under constrained unified memory
- Memory governance during load, unload, restart, and recovery
- Switch safety when active requests, cache pressure, or restart conditions
  exist
- Runtime truth surfaces that expose honest state to operators and upper layers
- Background-heavy serving for very large-weight models
- Runtime governance for hazardous and host-risking operations

These goals define a runtime program with its own architecture and capability
matrix.

## 4. Formal Runtime Principles

The following are not implementation anecdotes. They are formal runtime
principles of `owlmlx`.

### 4.1 Memory Governance Under Multi-Model Switching

`owlmlx` treats memory governance as a first-class runtime responsibility.

The runtime must make explicit decisions about load, unload, eviction, reclaim,
and restart behavior when multiple models compete for constrained unified
memory. "The model loaded successfully once" is not an adequate success
criterion.

### 4.2 Switch Safety And Active-Request Protection

`owlmlx` treats switching safety as a correctness requirement.

Runtime transitions must account for active requests, in-flight work, and
pressure conditions so that model switching does not silently corrupt serving
behavior or destabilize the runtime under load.

### 4.3 Runtime Truth Exposure

`owlmlx` requires runtime truth to be explicitly exposed upward.

The runtime must surface authoritative state about load status, memory
conditions, switching outcomes, runtime mode, and path-specific limitations.
Upper layers should consume runtime truth, not guess it.

### 4.4 Background-Heavy Serving

`owlmlx` explicitly recognizes that some runtime paths are background-heavy by
nature.

When a workload does not honestly support foreground-interactive behavior, the
runtime should model it as a background-heavy path rather than pretending it
belongs to the same product posture as smaller or faster interactive paths.

### 4.5 Runtime Governance

`owlmlx` treats hazardous operations, safe-resume rules, and heavy execution
protocols as runtime responsibilities.

If a path can threaten host stability or requires controlled re-entry after an
incident, that governance belongs inside runtime truth rather than being left as
temporary project memory.

## 5. Relationship To External Systems

### 5.1 MLX

`MLX` is the underlying compute and tensor substrate.

It is not the runtime identity of this project.

### 5.2 oMLX

`oMLX` is a major reference system and an immediate replacement target.

It matters because it demonstrates useful runtime mechanisms and because our
current platform work has historically depended on it. It does not define
`owlmlx`'s identity.

### 5.3 vMLX

`vMLX` is another important reference system.

It contributes implementation ideas, operational patterns, and packaging
examples that may be worth internalizing. It is not the origin story of
`owlmlx`.

### 5.4 Product Shell Layer

The desktop product shell sits above `owlmlx`.

It integrates runtime truth into user-facing desktop workflows, routing,
operator surfaces, and system lifecycle. It is not the runtime source-of-truth
repository.

Current repository history may still use legacy names for this shell layer, but
those names should not be treated as permanent runtime-truth terminology.

## 6. Adoption Model

`owlmlx` is a self-owned runtime, but self-owned does not mean full rewrite.

### 6.1 Formal Adoption Rule

`owlmlx` reuses open-source runtime mechanisms wherever they are proven and
useful. It does not require — and does not intend — a ground-up rewrite of
every execution layer beneath it.

What `owlmlx` owns is:

- runtime identity
- runtime principles
- runtime governance
- runtime truth contracts
- runtime path semantics
- extraction direction

What `owlmlx` borrows freely:

- MLX tensor execution substrate
- loader and model-format machinery from the MLX ecosystem
- cache scheduling ideas from `oMLX`
- serving and packaging patterns from `vMLX`
- any proven open-source mechanism that fits `owlmlx`'s own principles

### 6.2 Adoption Boundary

When a borrowed mechanism enters `owlmlx`, it accepts `owlmlx`'s capability
labels and governance semantics. The origin system does not automatically
define it as `supported` in `owlmlx`.

Borrowed implementation that has not been evaluated against `owlmlx` runtime
principles must be labeled `partial` or `experimental`, never `supported`.

### 6.3 What Adoption Is Not

- Adoption is not re-branding another project's code as `owlmlx`.
- Adoption is not pretending `owlmlx` invented something it borrowed.
- Adoption is not avoiding credit where implementation came from.
- Adoption is not declaring independence for the sake of optics.

### 6.4 Why This Rule Matters

Without a formal adoption model, `owlmlx` risks two failure modes:

1. **Full-rewrite theater** — wasting effort reimplementing things that already
   work, in order to "look independent"
2. **Identity collapse** — borrowing so heavily that `owlmlx` becomes a thin
   wrapper with no owned truth, defeating the purpose of the project

The adoption model exists to occupy the correct middle ground: own the truth
layer, reuse the execution layer, and be honest about which is which.

## 7. Extraction Map

`owlmlx` needs a disciplined separation between runtime judgments we already own,
ideas we plan to internalize, and external references that are not yet `owlmlx`
capabilities.

### 7.1 Already Ours In Runtime Judgment

These are already part of `owlmlx`'s runtime direction, regardless of where all
implementation currently lives:

- memory governance under multi-model switching
- switch safety and active-request protection
- runtime truth exposure as an owned contract
- background-heavy serving as an explicit runtime class
- runtime governance for hazardous operations and safe-resume

### 7.2 Borrow And Internalize

These may be borrowed from external systems, but only by being rewritten as
`owlmlx` architecture:

- cache, scheduling, and lifecycle ideas from `oMLX`
- serving and packaging patterns from `vMLX`
- any future runtime mechanism that fits `owlmlx`'s own principles and
  capability model

### 7.3 External Reference Only

The following do not count as `owlmlx` supported capability merely because they
exist elsewhere:

- an external runtime feature we have not adopted into `owlmlx` truth
- an upstream admin or UI surface we only observe from outside
- a specimen-specific behavior that has not been elevated into path-level or
  core-runtime truth

## 8. First Mature Path

The first mature path in `owlmlx` is the `large-weight runtime path`.

This path exists for models whose weight size, loading behavior, latency
profile, and serving pattern do not fit standard interactive runtime
expectations.

Current truth:

- It is background-heavy rather than foreground-interactive
- It requires honest capability labels
- It should not be named after a single specimen forever
- `Kimi` is the first validated specimen on this path

## 9. Current Non-Claims

`owlmlx` does not currently claim:

- that generalized foreground runtime is fully solved
- that all current platform runtime behavior already belongs in this repository
- that external runtime ideas can be copied without reinterpretation
- that the first mature path is the only future path

## 10. Product Success Criteria

`owlmlx` starts succeeding when it can do three things clearly:

1. Define runtime truth without borrowing identity from upstream projects
2. Separate runtime ownership from desktop-shell ownership
3. Provide a stable home for runtime-specific evolution, extraction, and
   productization
