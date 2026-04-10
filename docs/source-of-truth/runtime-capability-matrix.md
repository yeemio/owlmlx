# owlmlx Runtime Capability Matrix

> Status: authoritative
> Updated: 2026-04-10

Capability labels:

- `supported`
- `partial`
- `experimental`
- `not in scope`

## 1. owlmlx Core Supported Capabilities

| Capability | Label | Notes |
|---|---|---|
| Runtime identity as self-owned project | supported | This repository exists to freeze that boundary |
| Runtime architecture truth | supported | Core documents define the architecture boundary |
| Memory governance under multi-model switching | supported | Formal runtime principle |
| Switch safety and active-request protection | supported | Formal runtime principle |
| Runtime truth exposure as owned requirement | supported | Upper layers should consume runtime truth rather than invent it |
| Background-heavy serving as a runtime class | supported | Formal runtime principle, even though path maturity differs |
| Hazardous-operation governance | supported | Runtime-risking work belongs to runtime governance |
| Safe-resume contract as runtime governance | supported | Controlled re-entry is part of runtime truth |
| Fully self-owned implementation stack | partial | Two Python modules exist (schema validation + generation gate); lifecycle implementation remains outside owlmlx |
| Queue-based generation gate (owlmlx-owned) | supported | `owlmlx/serving.py` — GenerationGate class with 11 tests; enforces validated concurrency boundary |
| Formal adoption model (reuse open-source, own truth layer) | supported | Adoption rule frozen in product-definition section 6 |
| Extraction discipline with wave ordering | supported | Discipline rules frozen in extraction-inventory section 3 |
| Autonomous loop discipline for self-iteration | supported | Loop discipline frozen in autonomous-loop-discipline.md |

## 2. Large-Weight Path Supported Capabilities

| Capability | Label | Notes |
|---|---|---|
| Large-weight runtime path exists | supported | First mature path inside `owlmlx` |
| Background-heavy serving posture | supported | Honest current direction |
| Honest specimen-specific capability labels | supported | Path should not overclaim from a single specimen |
| Path naming independent of one model | supported | `Kimi` is not the permanent path name |
| Single-worker queue-based serving | supported | Validated through K-Q4c; generation lock serializes safely |
| Same-process parallel generation unsafe | supported | MLX/Metal substrate limitation; boundary = 1 |
| Linear memory scaling for layer loading | supported | Validated 1→61 layers; no superlinear accumulation |
| Heavy execution protocol field-validated | supported | K-Q3a→K-Q4d escalation proved the protocol |

## 3. Specialized-Only Capabilities

| Capability | Label | Notes |
|---|---|---|
| `Kimi` as first validated specimen | supported | Historical and architectural milestone |
| Specimen-specific runtime behavior | partial | Must not be confused with core runtime truth |
| Borrowed implementation auto-promoted to supported | not in scope | Adoption model explicitly rejects silent promotion |
| A specimen proving a path can exist | supported | Does not automatically generalize to other specimens |

## 4. Future Or Not Yet Established

| Capability | Label | Notes |
|---|---|---|
| Generalized foreground-interactive runtime | experimental | Not yet established as current truth |
| Additional runtime paths beyond large-weight | experimental | Future only when real capability truth exists |
| High-fidelity teacher/reference runtime path | experimental | Candidate direction, not yet frozen as supported path |
| `gemma-4-31B-it` as first high-fidelity candidate | experimental | Useful planning candidate; not yet a frozen path class |
| Fully internalized replacements for all external runtime mechanisms | partial | Directional goal, not current fact |
| Full-rewrite of every execution layer | not in scope | Adoption model explicitly rejects this as unnecessary |
| External runtime features observed but not adopted | not in scope | External reference is not `owlmlx` support |
| `Kimi` as permanent name for the whole path | not in scope | Explicitly rejected |

## 5. Product-Layer Relationship

| Capability | Label | Notes |
|---|---|---|
| Desktop product shell above `owlmlx` | supported | Frozen boundary; repository naming may change |
| Desktop shell defining runtime identity | not in scope | Runtime truth belongs here |
| Shared runtime truth consumed by upper layers | supported | Required architecture direction |

## 6. Label Promotion Rules

A capability may only move from `partial` or `experimental` to `supported`
when the promotion criteria in `extraction-inventory.md` section 8 are
satisfied: implementation evidence, test coverage, no false dependency,
governance compliance, and adoption label resolved.

No capability may be promoted based solely on documentation existing or a
feature working in an external runtime.
