# owlmlx Platform Convergence Posture

> Status: authoritative
> Updated: 2026-04-11
> Program: owlmlx-platform-capability-absorption-and-convergence
> Round: model-inventory-registry

## 1. Purpose

This document freezes the convergence posture between owlmlx and the original
local LLM platform at the conclusion of the capability absorption and
convergence program. It records what has been unified, what remains separated,
and what should happen next.

## 2. What Has Been Frozen This Program

| Round | Deliverable | Document |
|---|---|---|
| R1 | Gap-driven capability inventory | `capability-absorption-inventory.md` |
| R2 | Ownership boundary (5 categories, all capabilities assigned) | `ownership-boundary.md` |
| R3 | Model-line placement (6 model lines, 2 path classes) | `model-line-placement.md` |
| R4 | First absorption target (substrate boundaries: ~460 LOC) | `first-absorption-target.md` |
| R5 | Convergence posture (this document) | `convergence-posture.md` |

## 3. Current Convergence State

### 3.1 What Is Already Unified

| Area | Status |
|---|---|
| Runtime identity | owlmlx is the runtime source of truth; platform acknowledges this |
| Training substrate | owlmlx owns end-to-end (contracts + code + pilot results) |
| Large-weight path contracts | owlmlx owns (GenerationGate + serving status + path truth) |
| Model-line architecture | All 6 model lines placed in 2 path classes |
| Ownership boundary | Every capability has exactly one truth owner |
| Shell bridge | kimi-sharded-engine.py imports owlmlx modules |
| Schema validation | Platform validates against owlmlx runtime status schema |

### 3.2 What Remains Separated (Still-Separated Areas)

| Area | owlmlx Side | Platform Side | Why Still Separate |
|---|---|---|---|
| Substrate boundaries | All three substrate boundaries absorbed: memory budget (R13), context concurrency (R12), abort recovery (R11) | **Platform consumes owlmlx truth** — `control_service.py` imports `owlmlx.memory_budget`, `context_concurrency_policy.py` imports `owlmlx.context_concurrency`, `abort_recovery.py` delegates state tracking to `owlmlx.abort_recovery.AbortRecoveryTracker` | **Consumption wired**; local duplicate definitions removed |
| Runtime health semantics | **Absorbed + consumed** (R14): 6 enums, 7 derivation functions in `owlmlx/runtime_health.py`; platform consumes via `model_inventory.inventory_health_snapshot()` and imports `derive_platform_status()` | Platform owns all probing (HTTP, socket, tmux), backend-specific introspection, preflight check execution, recovery actions | **Consumption wired** — inline derivation chains replaced |
| Model lifecycle states | Ownership assigned (R15) | State machine lives in lifecycle.py + docs | Split absorption needed |
| Per-model runtime truth | Model inventory registry absorbed | `owlmlx/model_inventory.py`; platform consumes in metrics/control_service | Endpoint transport and mutations stay platform-owned |
| Cache truth | Not yet started | distilled_cache_substrate.py | Specialized; needs generalization |
| Model lineage | Training artifacts have metadata.json | Served model lineage in platform docs | Schema not yet extracted |

### 3.3 Convergence Scorecard

| Metric | Score |
|---|---|
| Capabilities with assigned truth owner | **46/46** (100%) |
| owlmlx-owned capabilities with code | **9/19** (47%) — runtime_status, serving, serving_status, training, memory_budget, context_concurrency, abort_recovery, runtime_health, model_inventory |
| owlmlx-owned capabilities consumed by platform | **5/9** (56%) — memory_budget, context_concurrency, abort_recovery, runtime_health, model_inventory (platform imports owlmlx truth, no local duplicates) |
| owlmlx-owned capabilities as doc-only | **6/19** (32%) — governance, hazardous-ops, safe-resume, training contracts |
| owlmlx-owned capabilities to absorb | **4/19** (21%) — Gaps 5, 6, 8 plus remaining per-model mutation/transport schema work (Gaps 1+2+3+4 absorbed; Gap 7 inventory layer absorbed) |
| Model lines with formal placement | **6/6** (100%) |
| Platform capabilities with clear non-absorption reasoning | **14/14** (100%) |

## 4. Formal Convergence Posture

### 4.1 Posture Statement

**owlmlx and the original local LLM platform are no longer at risk of
bifurcation.** Every capability has a truth owner. Every model line has a
placement. The ownership boundary is explicit and documented.

**The first code absorption is complete.** The substrate boundary trio
(R11 abort recovery, R12 context concurrency, R13 memory budget) has been
absorbed into owlmlx modules AND the platform now consumes them via direct
imports. Local duplicate truth definitions have been removed from the platform.

**Runtime health semantics absorbed and consumed.** R14 added 6 enums
and 7 pure derivation functions to `owlmlx/runtime_health.py`. Platform
consumes runtime health through `model_inventory.inventory_health_snapshot()`
and imports `derive_platform_status()`.

**Model inventory registry absorbed and consumed.** R17 now has an owlmlx
input truth layer: `LoadedModelEntry`, `ModelInventorySnapshot`,
loaded-memory aggregation, and pure budget/health integration. Platform
`metrics.py` and `control_service.py` fill inventory snapshots; owlmlx
derives downstream truth.

**Remaining convergence work:** 4 of 19 runtime-owned capabilities still
need code absorption. The 5 absorbed+consumed capabilities prove the
pattern for future rounds.

### 4.2 What This Means Operationally

1. **No new platform capability should be created that duplicates an owlmlx-
   owned truth.** If someone needs a concurrency boundary, they check owlmlx —
   not re-derive it in the router.

2. **No owlmlx capability should be created that duplicates a platform-owned
   responsibility.** Recovery orchestration, catalog management, and product
   routing stay in the platform.

3. **New model lines slot into existing path classes.** Standard MLX or
   large-weight. No third path class until real capability truth requires it.

4. **Training continues via owlmlx substrate.** Gemma training does not need
   to wait for code absorption. The contracts are already frozen.

## 5. Next Phase Recommendation

### Recommendation: Continue Code Absorption — Second Wave

The substrate boundary trio (Gap 2+3+4) is fully absorbed and consumed.
The pattern is proven: owlmlx defines truth → platform imports and consumes
→ local duplicates removed → tests pass through owlmlx truth.

~~Gap 1: Runtime Health Semantics (R14) — completed 2026-04-11.~~
~~Model Inventory Registry (R17 input truth layer) — completed 2026-04-11.~~

The next dominant gap is **Model Lifecycle State Definitions** (R15):
absorb state names and transition truth only. Lifecycle daemon polling,
auto-heal, TTL policy, endpoint transport, and operator actions remain
platform-owned.

| Step | Action | Expected Output |
|---|---|---|
| 1 | Map lifecycle state sources (`lifecycle.py` + lifecycle docs) | State/transition mapping |
| 2 | Add owlmlx lifecycle state definitions | Pure enums + transition helpers |
| 3 | Write owlmlx-side tests | Valid transitions, terminal states, no platform imports |
| 4 | Wire platform to consume if narrow seam exists | Lifecycle code imports owlmlx definitions |
| 5 | Update source-of-truth docs | Mark absorbed / consumed accurately |

Secondary candidates (after inventory closes):
- Gap 8: Model lineage schema (R16)
- Gap 5: Cache truth contract (R18)

### What Has Changed Since Round 5

The original recommendation was "Enter Code Absorption Phase." That phase
has been entered and partially completed:

- **Substrate trio absorbed** (Rounds 4–6): 3 modules, 97 tests, ~736 LOC
- **Platform consumption wired** (Rounds A–C): 3 platform files rewired, local truth removed
- **Pattern proven**: owlmlx truth → platform import → backward-compatible re-export → tests pass

## 6. Program Success Evaluation

### Success Criteria (from program contract)

| # | Criterion | Status |
|---|---|---|
| 1 | Capability absorption map (gap-driven, not archaeology) | ✓ `capability-absorption-inventory.md` |
| 2 | Ownership boundary (runtime / control-plane / shell / product; truth-owner clear) | ✓ `ownership-boundary.md` |
| 3 | At least one high-value absorption round (not empty directory work) | ✓ `first-absorption-target.md` — concrete ~460 LOC target |
| 4 | Explicit "what NOT to absorb" | ✓ 14 non-candidates with reasoning |
| 5 | Gemma, Kimi, 120B placement in unified boundary | ✓ `model-line-placement.md` |

All 5 success criteria satisfied.

### Hard Rules Compliance

| Rule | Compliance |
|---|---|
| Not written as replacement complete state | ✓ 9/19 capabilities still to absorb |
| Not mechanical copy of all platform capabilities | ✓ 14 explicit non-candidates |
| Not training expansion | ✓ Training explicitly deferred |
| Not unverified experimental promoted | ✓ All candidates are verified |
| Not "future can integrate" — specific ownership given | ✓ Every capability has one owner |
| Not detached from code — code scan done | ✓ 4 code directories scanned |
| Not reference docs — each round feeds next | ✓ R1→R2→R3→R4→R5 decision chain |

## 7. Document Registry After This Program

owlmlx source-of-truth now contains 25 documents:

1–20: (existing, see master-outline.md)
21. `capability-absorption-inventory.md` (R1)
22. `ownership-boundary.md` (R2)
23. `model-line-placement.md` (R3)
24. `first-absorption-target.md` (R4)
25. `convergence-posture.md` (R5)
