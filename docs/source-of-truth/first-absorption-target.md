# owlmlx First Absorption Target Selection

> Status: authoritative
> Updated: 2026-04-10
> Program: owlmlx-platform-capability-absorption-and-convergence
> Round: 4

## 1. Purpose

This document selects the first group of capabilities to absorb from the
original platform into owlmlx. The selection is based on the gap inventory
(Round 1), ownership boundary (Round 2), and model-line placement (Round 3).

## 2. Selection Criteria

The first absorption target must satisfy ALL of:

1. **High value** — fills a real owlmlx gap, not just organizational tidying
2. **Low risk** — small, self-contained, minimal coupling to platform internals
3. **Hardware-verified** — based on empirical runtime truth, not speculation
4. **More urgent than training** — continuing training without this creates drift
5. **Immediately testable** — can produce owlmlx-owned tests on day one

## 3. First Absorption Group: Runtime Substrate Boundaries

### Selected: Gap 2 (Abort Recovery) + Gap 3 (Context Concurrency) + Gap 4 (Memory Budget)

These three capabilities form a natural bundle: **"What are the physical
boundaries of the MLX/Metal substrate on this machine?"**

Together they answer:

- How many concurrent requests can the substrate handle? (Gap 3)
- What happens when the substrate fails under pressure? (Gap 2)
- How much memory is available for models? (Gap 4)

### 3.1 Why This Group First

| Reason | Explanation |
|---|---|
| **Prevents drift** | Without owlmlx owning these boundaries, the router and control-plane independently re-derive them. Two systems defining the same hardware truth = guaranteed drift. |
| **More urgent than training** | Training consumes these boundaries (LoRA pilot used ~62 GB, hit OOM at dual-load). Without owlmlx owning memory budget truth, training and serving make independent budget assumptions. |
| **Small and self-contained** | abort_recovery.py (265 LOC) + context_concurrency_policy.py (147 LOC) + memory budget logic (~50 LOC). Total: ~460 LOC to absorb. |
| **Hardware-verified** | All three are empirically established on M5 Max 128 GB with oMLX 0.3.2. Not theoretical. |
| **Already partially absorbed** | GenerationGate (owlmlx/serving.py) is the large-weight-path concurrency boundary. Gap 3 is the standard-path equivalent. Memory governance is already an owlmlx principle — Gap 4 gives it enforcement code. |
| **Immediately testable** | Each capability has clear input/output: context length → concurrency limit, health probe → contamination state, model size → budget fit/reject. |

### 3.2 What Gets Absorbed

#### Absorption Target A: Context Concurrency Boundary Definitions

**Source:** `llm_router/context_concurrency_policy.py`

**What moves to owlmlx:**
- Hardware-verified concurrency boundaries as a formal contract
- Boundary definition: ≤48K tokens → up to 4-way parallel; >48K → 1-way
- Machine capability description (M5 Max, 128 GB, Metal 4, oMLX 0.3.2)
- Boundary constants and the logic that maps context length to max concurrency

**What stays in router:**
- Semaphore acquisition at request dispatch time (T7)
- Active/served request counters
- HTTP endpoint for gate map

**owlmlx module direction:** New contract document or constants module that
the router imports for boundary definitions.

#### Absorption Target B: Abort Recovery State Machine

**Source:** `llm_router/abort_recovery.py`

**What moves to owlmlx:**
- State machine definition: `clean` → `probing` → `contaminated`
- Transition rules (what triggers each state change)
- Health probe protocol (how to verify substrate recovery)
- Contamination semantics (what "contaminated" means for the MLX engine)

**What stays in router:**
- Request blocking enforcement (when contaminated, reject requests)
- Integration with streaming response handling
- HTTP-level abort detection

**owlmlx module direction:** New module `owlmlx/substrate_health.py` or
extension of `runtime_status.py` to include substrate contamination state.

#### Absorption Target C: Memory Budget Definition

**Source:** `ops_dashboard/control_service.py` → `_check_memory_budget()`

**What moves to owlmlx:**
- Machine memory budget constant (116 GB usable on 128 GB)
- Budget calculation logic (total available - system reserve - loaded models)
- "Will this model fit?" function
- Budget truth as a runtime fact

**What stays in control-plane:**
- Pre-flight validation policy (reject load if over budget)
- Whitelist enforcement (which backends can be loaded)
- User-facing error messages

**owlmlx module direction:** New module `owlmlx/memory_budget.py` or
constants in an existing module.

### 3.3 Absorption Scope Boundaries

| In Scope | Out of Scope |
|---|---|
| Boundary constants and definitions | Request-time enforcement logic |
| State machine semantics | HTTP endpoint transport |
| Budget calculation | Policy decisions (load/reject) |
| Contract documents | Platform integration wiring |
| owlmlx-side tests | Router/dashboard test migration |

### 3.4 Expected Deliverables

When this absorption executes (in a future code-absorption round):

1. New owlmlx module(s) with boundary definitions, state machine, budget logic
2. owlmlx-owned tests for each absorbed capability
3. Router/dashboard imports owlmlx definitions instead of defining their own
4. Updated ownership-boundary.md (R11, R12, R13 → "absorbed")
5. Updated capability-matrix.md with new `supported` rows

## 4. Second-Wave Candidates (Not Selected For First)

These are valuable but larger-scope or dependent on first-wave completion:

| Gap | Capability | Why Deferred |
|---|---|---|
| Gap 1 | Runtime health semantics | Larger scope (5-tier load_state, 4-level inference health). Should follow after substrate boundaries are owned. |
| Gap 6 | Model lifecycle state definitions | Splits across layers. Absorbing state enum alone without the full lifecycle logic risks orphaned definitions. Better after boundary ownership proves the pattern. |
| Gap 8 | Model lineage schema | Schema-only, no enforcement code. Lower urgency — current models have verified lineage in platform docs. |
| Gap 5 | Cache profile management | Specialized to Distilled-27B. Generalization needed before absorption. |
| Gap 7 | Per-model runtime truth schema | Depends on Gap 1 (health semantics) being resolved first. |

## 5. Why This Is More Valuable Than Continuing Training

| If we continue training next | If we absorb substrate boundaries next |
|---|---|
| Gemma training runs on undocumented memory assumptions | Memory budget is a formal owlmlx contract |
| OOM during dual-load is an incident, not a governed boundary | OOM is a predictable, rejectable budget violation |
| Router and training independently guess concurrency limits | One truth source for "how many concurrent requests?" |
| Abort during high-context training has no recovery protocol | Substrate contamination is detected and governed |
| Two systems (owlmlx + platform) define the same hardware truth | One system owns hardware truth; others consume it |

The convergence value is: **stop owlmlx and the platform from independently
deriving the same physical truths about the machine.**
