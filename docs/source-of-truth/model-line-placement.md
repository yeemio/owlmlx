# owlmlx Model-Line Placement

> Status: authoritative
> Updated: 2026-04-10
> Program: owlmlx-platform-capability-absorption-and-convergence
> Round: 3

## 1. Purpose

This document freezes the formal placement of each model line in the unified
owlmlx + platform architecture. It finalizes the provisional placements from
Round 2 (ownership-boundary.md §5) into authoritative positions.

## 2. Placement Framework

Every model line has exactly one position in this grid:

| Dimension | Question | Who Answers |
|---|---|---|
| Runtime path | Which owlmlx path does this model sit on? | owlmlx |
| Serving posture | Foreground-interactive, background-heavy, or on-demand? | owlmlx |
| Training relationship | Is this model trained via owlmlx substrate? | owlmlx |
| Lifecycle state | stable / backup / candidate / experimental / blocked / parked | owlmlx defines; platform catalogs |
| Product role | What user work type does this model serve? | Product surface |
| Routing treatment | How does the router dispatch to this model? | Router |

## 3. Model-Line Placements

### 3.1 Gemma (gemma-4-31B-it) — Production Mainline

| Dimension | Placement |
|---|---|
| Runtime path | Standard MLX serving path (oMLX) |
| Serving posture | On-demand (loaded when needed, ~62 GB) |
| Training relationship | **owlmlx-native** — first model trained via owlmlx substrate |
| Lifecycle state | `supported` in owlmlx; platform promotion to `stable` pending full gate |
| Product role | Training substrate validator, future production tasks (post-data-engineering) |
| Routing treatment | Standard oMLX backend routing |

**Unique position:** Gemma is the only model line that is owlmlx-native end-to-
end. It was trained via owlmlx training substrate, validated via owlmlx pilot,
and its production mainline was frozen by owlmlx. No other model line has this
depth of owlmlx ownership.

**Current limitation:** Cannot co-reside with other large models (~62 GB).
Sequential load/unload required on 128 GB machine.

**What owlmlx owns:** Training contracts, artifact layout, training-to-serving
bridge, production mainline identity, pilot results.

**What platform owns:** Product routing, catalog placement (when promoted),
user-facing model selection, lifecycle gate execution.

---

### 3.2 Kimi 1T (K2.5 family) — Large-Weight Path Specimen

| Dimension | Placement |
|---|---|
| Runtime path | Large-weight runtime path (owlmlx first mature path) |
| Serving posture | Background-heavy (queue-based, single-worker, :8014) |
| Training relationship | None — Kimi is a served specimen, not a training target |
| Lifecycle state | `experimental` / `lab` (MiroThinker-1.7 Q8 is `stable` as search scout) |
| Product role | Lab research, search scouting (MiroThinker variant) |
| Routing treatment | Dedicated port :8014, background job submission |

**Unique position:** Kimi is not a production mainline model. It is the first
validated specimen on the large-weight runtime path. Its value to owlmlx is
**architectural validation**: it proved concurrency boundaries, memory scaling,
and serving posture for the entire large-weight path class.

**What owlmlx owns:** Path-level contracts (GenerationGate, serving status,
concurrency boundary = 1, memory governance), all extracted from Kimi specimens.

**What platform owns:** Engine hosting (kimi-sharded-engine.py), product
routing, lab surface (kimi_lab.py), background job dispatch.

**owlmlx boundary:** Kimi does not re-enter the production mainline discussion.
It is a lab specimen. New models on the large-weight path will inherit the
path-level contracts Kimi validated, but Kimi itself stays in lab.

---

### 3.3 gpt-oss-120b (MXFP4-Q4) — Platform Heavy Synthesis

| Dimension | Placement |
|---|---|
| Runtime path | Standard MLX serving path (oMLX) |
| Serving posture | On-demand heavy (58 GB, loaded for deep work sessions) |
| Training relationship | None — not an owlmlx training target |
| Lifecycle state | `stable` on platform |
| Product role | Heavy synthesis, deep reasoning (11/12 upgrade gate) |
| Routing treatment | Standard oMLX backend, model-id routing |

**Unique position:** gpt-oss-120b is the platform's verified heavy reasoning
model. It is stable, production-tested, and fully integrated. It does not need
owlmlx-specific treatment beyond conforming to the general runtime truth schema
(R17) and lineage schema (R16).

**What owlmlx owns:** Runtime truth schema it must conform to, lifecycle state
definitions, lineage schema, memory budget truth that determines if it fits.

**What platform owns:** Catalog placement, product routing, work-type
assignment, lifecycle gate execution, user-facing model selection.

**owlmlx boundary:** gpt-oss-120b is a platform-managed model that happens to
run on the MLX substrate owlmlx governs. owlmlx does not own its identity or
product role — only the runtime substrate contracts it must honor.

---

### 3.4 Distilled-27B Family — Platform Default Line

| Variant | Runtime | State | Role |
|---|---|---|---|
| MLX-4bit | oMLX | stable | Primary default (coding, chat, general) |
| Q4_K_M GGUF | llama.cpp | backup | Emergency fallback |

| Dimension | Placement |
|---|---|
| Runtime path | Standard MLX (primary) + llama.cpp (backup) |
| Serving posture | Resident (always loaded, ~15 GB) |
| Training relationship | None currently; future owlmlx fine-tuning candidate |
| Lifecycle state | `stable` (primary) / `backup` (GGUF) |
| Product role | Default for coding, chat, and general work |
| Routing treatment | Default model routing; cache substrate (Gap 5) |

**Unique position:** Most deeply integrated model on the platform. Only model
with a dedicated cache substrate module (`distilled_cache_substrate.py`). Only
model with a verified backup-line GGUF conversion.

**What owlmlx owns:** Cache truth contract (when absorbed — Gap 5), lineage
schema (especially conversion disclosure for GGUF variant), runtime health
truth.

**What platform owns:** Everything else — catalog default, routing priority,
product surface visibility, cache profile switching logic.

---

### 3.5 Qwen3.5-35B-A3B-4bit — Fast General

| Dimension | Placement |
|---|---|
| Runtime path | Standard MLX serving path (oMLX) |
| Serving posture | On-demand (MoE, efficient memory) |
| Training relationship | None |
| Lifecycle state | `stable` |
| Product role | Fast general work, brainstorming, drafting |
| Routing treatment | Standard oMLX backend |

Standard platform model. No owlmlx-specific treatment needed. Conforms to
general runtime truth and lineage schemas.

**Known issue:** Thinking mode infinite loop on coding tasks; cannot disable
on oMLX. Demoted from coding primary.

---

### 3.6 Mistral-Large Q4-MLX — Alternate

| Dimension | Placement |
|---|---|
| Runtime path | Standard MLX serving path (oMLX) |
| Serving posture | On-demand |
| Training relationship | None |
| Lifecycle state | `stable` (alternate) |
| Product role | Alternate general model |
| Routing treatment | Standard oMLX backend |

Standard platform model. No owlmlx-specific treatment needed.

## 4. Placement Summary Matrix

| Model Line | owlmlx Path | Posture | Training | State | Special |
|---|---|---|---|---|---|
| **Gemma** | Standard MLX | On-demand | **owlmlx-native** | supported | Production mainline |
| **Kimi 1T** | Large-weight | Background-heavy | None | experimental | Path validator |
| **gpt-oss-120b** | Standard MLX | On-demand heavy | None | stable | Heavy synthesis |
| **Distilled-27B** | Standard MLX + llama.cpp | Resident | None | stable + backup | Platform default |
| **Qwen3.5-35B-A3B** | Standard MLX | On-demand | None | stable | Fast general |
| **Mistral-Large** | Standard MLX | On-demand | None | stable | Alternate |

## 5. Key Architectural Conclusions

### 5.1 Two Runtime Path Classes

The unified architecture has exactly two runtime path classes:

1. **Standard MLX serving path** — Gemma, gpt-oss-120b, Distilled-27B,
   Qwen3.5, Mistral-Large all use this. owlmlx owns the general contracts
   (health semantics, concurrency policy, memory budget, lineage). Models
   are fungible on this path.

2. **Large-weight runtime path** — Kimi 1T currently. owlmlx owns the
   specialized contracts (GenerationGate, serving status, background-heavy
   posture). New specimens inherit path contracts.

### 5.2 Only One owlmlx-Native Training Line

Gemma is the only model trained via owlmlx substrate. Other models are
downloaded artifacts managed by the platform. This makes Gemma's training
contracts (substrate, artifact layout, training-to-serving) a unique owlmlx
value that no other model line replicates.

### 5.3 owlmlx Does Not Own Product Roles

owlmlx defines runtime truth (can it serve? how much memory? what concurrency?).
Product roles (which model for coding? which for reasoning?) belong to the
product surface (catalog, work-capability-standard). This split is permanent.

### 5.4 Model-Line Placement Does Not Require Code Changes

All placements describe where models sit in the existing architecture. No new
code is needed to enforce these placements. The value is clarity: when the
next model arrives, it slots into an existing path class with known contracts.
