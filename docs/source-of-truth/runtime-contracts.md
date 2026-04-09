# owlmlx Runtime Contracts

> Status: authoritative
> Updated: 2026-04-09

## 1. Purpose

This document defines runtime-owned contracts that should live in `owlmlx`
rather than only inside platform-layer protocol documents.

The platform shell may proxy, aggregate, or present these contracts, but the
semantic ownership belongs here.

## 2. Contract Families

`owlmlx` currently recognizes two first-class contract families:

1. `core runtime status`
2. `large-weight runtime path status`

These are runtime contracts, not dashboard-only response shapes.

## 3. Contract Rules

### 3.1 Runtime Truth Is Authoritative

Runtime contracts must describe runtime truth as the runtime itself understands
it. Platform layers may add product context, but they must not rewrite the
meaning of runtime state.

### 3.2 Capability Labels Must Be Honest

A contract must not imply a capability that the runtime does not honestly
support.

### 3.3 Path-Level Contracts Must Not Be Generalized Improperly

Specimen-specific or path-specific fields must remain path-scoped. A
large-weight runtime path contract must not be mistaken for generalized
foreground runtime support.

## 4. Core Runtime Status Contract

The core runtime status contract exists to expose authoritative runtime facts
such as:

- runtime identity
- load state
- memory state
- switching and readiness state
- cache or lifecycle truth where owned by the runtime

This contract may initially be fulfilled through external runtime surfaces, but
the contract itself belongs to `owlmlx`.

## 5. Large-Weight Runtime Path Contract

The large-weight runtime path contract exists to expose runtime facts specific
to the first mature path, including:

- runtime variant identity
- memory and cache state
- lifecycle mode
- path-specific serving posture
- honest interactive-status labels

`Kimi` currently validates this path, but the contract is path-owned rather than
specimen-owned.

## 6. Relationship To Platform Protocols

The current desktop product shell repository may continue to define:

- proxy routes
- snapshot composition
- UI-specific aggregation
- shell-level error handling

But those should reference runtime-owned contracts from `owlmlx`, not serve as
the only truth source for runtime semantics.

The same rule applies to governance contracts such as hazardous-operation
classification and safe-resume state.
