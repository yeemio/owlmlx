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

The formal path truth (serving posture, concurrency boundary, memory behavior,
lifecycle, governance) is frozen in `large-weight-path-truth.md`.

### 5.1 Owned Serving Modules

The following owlmlx modules implement runtime contracts for this path:

- `owlmlx/serving.py` — `GenerationGate` enforces the queue-based single-worker
  generation discipline (concurrency boundary = 1)
- `owlmlx/serving_status.py` — `build_large_weight_serving_status()` produces
  the owlmlx-owned status shape; `merge_specimen_identity()` layers specimen
  detail on top
- `owlmlx/runtime_status.py` — schema validation for both core and large-weight
  status payloads

### 5.2 Validated Runtime Boundaries (From First Specimen)

The following runtime boundaries were established through the Kimi K2.5
experiment line (Phase 42, gates K-Q3a through K-Q4d) and have been absorbed
into large-weight path truth:

**Serving concurrency:**

- Same-process parallel generation is unsafe on MLX/Metal (substrate-level
  thread-safety limitation, not specimen-specific)
- Serialized queue-based serving (generation lock) is the safe production
  pattern; validated to 4 queued connections
- Multi-process isolation bypasses the thread-safety crash but is not
  cost-effective (2× memory for ~1.1× throughput due to Metal GPU contention)

**Memory behavior:**

- BF16 attention layer loading scales linearly with layer count (no
  superlinear accumulation observed across 1→61 layer escalation)
- GC cleanup returns Metal active memory to pool floor; no persistent
  accumulation detected
- Memory pressure from concurrent engine instances is additive and predictable

**Serving architecture:**

- Single-worker, queue-based serving is the recommended production pattern
  for large-weight path models
- Engine warmup (prefill + initial generation) should happen before accepting
  requests
- Health and status endpoints must remain responsive even under generation load

**Governance validation:**

- The heavy execution protocol (dry-run → single-unit → serial → thresholded
  → expansion) was field-validated through the full K-Q3/K-Q4 escalation
- Safe-resume contracts were exercised after a real host incident
- These governance rules are now runtime truth, not just documentation

These boundaries are path-level truth. Specimen-specific details (layer count,
per-layer memory size, generation speed) remain specimen-scoped and should not
be generalized without evidence from additional specimens.

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
