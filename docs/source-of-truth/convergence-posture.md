# owlmlx Platform Convergence Posture

> Status: authoritative
> Updated: 2026-04-10
> Program: owlmlx-platform-capability-absorption-and-convergence
> Round: 5

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
| Substrate boundaries | Abort recovery + context concurrency documented as owlmlx-owned (R11-R12); memory budget absorbed (R13) | Abort recovery + context concurrency code still in router/dashboard | Memory budget absorbed; two capabilities remain |
| Runtime health semantics | Schema validation only | 5-tier load_state, 4-level inference health in metrics.py | Larger scope; second-wave |
| Model lifecycle states | Ownership assigned (R15) | State machine lives in lifecycle.py + docs | Split absorption needed |
| Per-model runtime truth | Status schema exists | Endpoint logic in router app.py | Schema extracted; transport stays |
| Cache truth | Not yet started | distilled_cache_substrate.py | Specialized; needs generalization |
| Model lineage | Training artifacts have metadata.json | Served model lineage in platform docs | Schema not yet extracted |

### 3.3 Convergence Scorecard

| Metric | Score |
|---|---|
| Capabilities with assigned truth owner | **46/46** (100%) |
| owlmlx-owned capabilities with code | **5/19** (26%) — runtime_status, serving, serving_status, training, memory_budget |
| owlmlx-owned capabilities as doc-only | **6/19** (32%) — governance, hazardous-ops, safe-resume, training contracts |
| owlmlx-owned capabilities to absorb | **8/19** (42%) — Gaps 1-3, 5-8 from inventory (Gap 4 memory budget absorbed) |
| Model lines with formal placement | **6/6** (100%) |
| Platform capabilities with clear non-absorption reasoning | **14/14** (100%) |

## 4. Formal Convergence Posture

### 4.1 Posture Statement

**owlmlx and the original local LLM platform are no longer at risk of
bifurcation.** Every capability has a truth owner. Every model line has a
placement. The ownership boundary is explicit and documented.

**However, convergence is not yet complete.** 9 of 19 runtime-owned
capabilities still have their implementation in the original platform. The
boundary is frozen, but code has not yet followed the boundary.

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

### Recommendation: Enter Code Absorption Phase

The convergence program has completed its boundary and planning work.
The next phase should be **code absorption** — actually moving the first
absorption group (Gap 2 + 3 + 4) from platform code into owlmlx modules.

Specifically:

| Step | Action | Expected Output |
|---|---|---|
| 1 | Create `owlmlx/substrate_boundaries.py` | Context concurrency constants + memory budget calculation |
| 2 | Create `owlmlx/substrate_health.py` | Abort recovery state machine |
| 3 | Write owlmlx-side tests | Cover all boundary conditions |
| 4 | Update router to import from owlmlx | Router consumes, does not define |
| 5 | Update dashboard to import from owlmlx | Dashboard consumes budget truth |
| 6 | Update ownership-boundary.md | R11, R12, R13 → "absorbed" |

This is **not** a documentation phase. It produces new Python modules in
owlmlx with tests, and modifies the platform to consume them.

### Why Not Continue Training Instead

Training can proceed in parallel — the substrate contracts are frozen and
the pilot is complete. But if training proceeds without code absorption:

- Training will make memory budget assumptions that are not owlmlx-owned code
- Concurrent training + serving scenarios will not have a single concurrency
  truth source
- Abort recovery during training will be handled ad-hoc

Code absorption first closes this gap. Training can happen alongside or after.

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
