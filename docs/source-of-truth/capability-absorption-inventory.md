# owlmlx Capability Absorption Inventory

> Status: authoritative
> Updated: 2026-04-10
> Program: owlmlx-platform-capability-absorption-and-convergence
> Round: 1

## 1. Purpose

This document is the gap-driven capability absorption inventory required by
the platform convergence program. It is organized around **what owlmlx
currently lacks**, not around the original platform's module structure.

Each gap identifies:

- what owlmlx needs but does not yet own
- what the original platform already has that fills (or partially fills) the gap
- maturity of the platform implementation
- absorption candidate status
- truth ownership recommendation

## 2. owlmlx Current Owned Capability Summary

Before listing gaps, this is what owlmlx already owns:

| # | Capability | Module / Doc | Status |
|---|---|---|---|
| 1 | Runtime identity + architecture truth | 20 source-of-truth docs | supported |
| 2 | Runtime status schema validation | `runtime_status.py` (6 tests) | supported |
| 3 | Queue-based generation gate | `serving.py` — GenerationGate (11 tests) | supported |
| 4 | Large-weight serving status builder | `serving_status.py` (10 tests) | supported |
| 5 | Training artifact registration | `training.py` (17 tests) | supported |
| 6 | Training substrate contract | `training-substrate-contract.md` | supported |
| 7 | Artifact layout contract | `artifact-layout-contract.md` | supported |
| 8 | Training-to-serving contract | `training-to-serving-contract.md` | supported |
| 9 | Gemma production mainline freeze | `gemma-high-fidelity-role.md` | supported |
| 10 | Memory governance principles | `runtime-governance.md` | doc-only |
| 11 | Hazardous-operation governance | `hazardous-operations.md` | doc-only |
| 12 | Safe-resume contract | `runtime-governance.md` | doc-only |
| 13 | Serving-path memory budget truth | `memory_budget.py` (32 tests) | supported |
| 14 | Serving-path context concurrency truth | `context_concurrency.py` (34 tests) | supported |
| 15 | Serving-path abort recovery state machine | `abort_recovery.py` (31 tests) | supported |

Total: 7 Python modules, 141 tests, 20 truth documents.

## 3. Gap-Driven Inventory

### Gap 1: Runtime Health Semantics — **ABSORBED + CONSUMED**

**What owlmlx now owns:**
`owlmlx/runtime_health.py` — 6 enum types (LoadState, InferenceHealth,
WaitTier, TruthLevel, RuntimeReadiness, PlatformStatus), 7 derivation
functions, 3 normalization functions. 85 tests. Platform `metrics.py`
imports `derive_wait_tier()` and `derive_platform_status()`.

**What the platform retains:**
All HTTP/socket/tmux probing, backend-specific introspection (oMLX
engine_pool, vLLM model lists), preflight check execution, recovery
actions, dashboard rendering. Platform assigns raw load_state values
from probe results; owlmlx derives composite labels.

---

### Gap 2: Abort Recovery State Machine

**What owlmlx lacks:**
No concept of abort detection, contamination state, or recovery protocol
when the MLX/Metal substrate fails under high-context pressure.

**What the platform has:**

- `llm_router/abort_recovery.py` (265 LOC)
- State machine: `clean` → `probing` → `contaminated`
- High-context abort detection (>48K token failures)
- Automatic health probe and request blocking until recovery
- History tracking (abort counts, recovery timestamps)

**Platform maturity:** Verified — field-exercised during real high-context
failures on oMLX 0.3.2.

**Absorption candidate:** YES — this is MLX/Metal substrate behavior under
pressure. The state machine describes runtime truth about when the engine
is trustworthy. This belongs in owlmlx, not in a router module.

**Current platform source files:**
- `llm_router/abort_recovery.py`

---

### Gap 3: Context-Aware Concurrency Policy

**What owlmlx lacks:**
owlmlx has GenerationGate (concurrency boundary = 1) for the large-weight
path, but has no concept of context-dependent concurrency for the general
MLX runtime (e.g., ≤48K → 4-way parallel, >48K → 1-way serialized).

**What the platform has:**

- `llm_router/context_concurrency_policy.py` (147 LOC)
- Hardware-verified policy: ≤48K → up to 4-way, >48K → 1-way serialized
- Verified on oMLX 0.3.2, Apple Silicon 128 GB
- Active request counters, served request counters
- Full gate map API exposure

**Platform maturity:** Verified — hardware-specific, empirically established.

**Absorption candidate:** YES — these are MLX/Metal substrate concurrency
boundaries. They describe hardware truth, not routing policy. owlmlx
should own the boundary definitions; the router consumes them as policy
input.

**Current platform source files:**
- `llm_router/context_concurrency_policy.py`

---

### Gap 4: Memory Budget Enforcement

**What owlmlx lacks:**
owlmlx documents memory governance as a principle ("128 GB machine, memory
is finite, must govern switching") but has zero enforcement code. No budget
calculation, no pre-flight validation, no "will this model fit?" check.

**What the platform has:**

- `ops_dashboard/control_service.py` → `_check_memory_budget()`
- 116 GB usable budget on 128 GB M5 system
- Pre-flight validation before model load
- Loaded model inference for budget calculation
- Rejection path when budget exceeded

**Platform maturity:** Verified — used in production model-load flow.

**Absorption candidate:** YES — memory budget is a runtime substrate fact.
The 116 GB number, the budget calculation logic, and the "will it fit?"
check are all runtime truth. Control-plane can enforce policy on top, but
the budget definition belongs to owlmlx.

**Current platform source files:**
- `ops_dashboard/control_service.py`

---

### Gap 5: Cache Profile Management

**What owlmlx lacks:**
No concept of cache profiles, cache switching, or cache state management.
owlmlx roadmap mentions "cache tier truth" as future work but owns nothing.

**What the platform has:**

- `llm_router/distilled_cache_substrate.py` (20.9 KB)
- Cache profiling and profile switching
- Auto-backup before switch, rollback capability
- Runtime detection via lsof-based port probing
- Honest status reporting for cache state

**Platform maturity:** Verified but specialized — tightly coupled to
`Distilled-27B` model line and current oMLX cache implementation.

**Absorption candidate:** PARTIAL — the concept of cache profile management
as runtime truth belongs to owlmlx. The specific Distilled-27B coupling
does not. owlmlx should own a generalized cache truth contract; the
current implementation is a specimen-specific reference.

**Current platform source files:**
- `llm_router/distilled_cache_substrate.py`

---

### Gap 6: Model Lifecycle State Definitions

**What owlmlx lacks:**
No lifecycle states, no promotion gates, no eviction policies, no state
transition rules. owlmlx knows about training artifacts and serving
feasibility but has no concept of "is this model stable, candidate,
blocked, or parked?"

**What the platform has:**

- `model-lifecycle-and-upgrade-gate.md` — 6 states with entry/exit rules
- Full upgrade gate (G1–G7), backup gate (B1–B4), runtime gate (R1–R3),
  quant gate (Q1–Q3)
- Truth inheritance rules (what carries over vs must re-verify)
- `ops_dashboard/lifecycle.py` — LifecycleDaemon (693 LOC)
- TTL eviction: preview=30m, lab=15m, stable=never
- Auto-heal on consecutive health failures

**Platform maturity:** Verified — exercised across 40+ phases with real
model promotions and demotions.

**Absorption candidate:** SPLIT —

- **State definitions** (stable/backup/candidate/experimental/blocked/parked)
  and **truth inheritance rules** are runtime truth → absorb into owlmlx.
- **Upgrade gate tests** (G1–G7) are product-level quality validation →
  stays in platform.
- **LifecycleDaemon** (polling, eviction, auto-heal) is control-plane
  orchestration → stays in platform.
- **TTL policy** is operational policy → stays in platform.

**Current platform source files:**
- `docs/source-of-truth/local-llm-platform/model-lifecycle-and-upgrade-gate.md`
- `ops_dashboard/lifecycle.py`
- `tests/test_lifecycle.py`
- `tests/test_phase25_lifecycle_ttl.py`

---

### Gap 7: Per-Model Runtime Truth Exposure

**What owlmlx lacks:**
owlmlx has `runtime_status.py` schema validation and
`build_large_weight_serving_status()` for one specific path. It does not
own a generalized per-model runtime truth surface covering load state,
memory fitness, pin state, quantization metadata, or engine identity across
all model types.

**What the platform has:**

- `/v1/runtime/omlx/status` — aggregate runtime truth
- `/v1/runtime/omlx/models` — per-model truth
- Per-model: load_state, memory, budget_fitness, pin_state, engine_type
- Aggregate: TPS, queue depth, cache efficiency
- `POST /v1/runtime/omlx/models/{id}/unload` — runtime mutation

**Platform maturity:** Verified — Router endpoints exercised, Dashboard
consumes these.

**Absorption candidate:** PARTIAL — owlmlx should own the schema and
semantic definition of per-model runtime truth. The HTTP transport
(endpoint routing, proxy logic) stays in the router/platform. owlmlx
defines what fields exist and what they mean; platform transports them.

**Current platform source files:**
- `llm_router/app.py` (runtime status endpoints)
- `ops_dashboard/metrics.py` (status readers)
- `tests/test_omlx_runtime_status.py`
- `tests/test_omlx_models_status.py`

---

### Gap 8: Model Lineage And Provenance

**What owlmlx lacks:**
owlmlx has `artifact-layout-contract.md` for training artifacts with
`metadata.json`, but no concept of served-model lineage: base model origin,
quantization method, conversion path, runtime version, verified context.

**What the platform has:**

- `model-lifecycle-and-upgrade-gate.md` §2 — lineage schema
- Fields: base_model, base_format, quantizer, quant_method, served_format,
  conversion_path, conversion_patches, local_path, file_size_gb, sha256,
  runtime, runtime_version, verified_date, verified_context, known_caveats
- Conversion disclosure rule: "same name ≠ same weights"

**Platform maturity:** Defined — schema exists, mandatory for stable/backup
models. Exercised for Distilled-27B conversion path.

**Absorption candidate:** YES — model provenance is runtime truth. "What
weights are actually being served, and how did they get here?" is a
question the runtime must answer honestly. owlmlx should own the lineage
schema; catalog population stays in platform.

**Current platform source files:**
- `docs/source-of-truth/local-llm-platform/model-lifecycle-and-upgrade-gate.md`

---

## 4. Explicit Non-Candidates (Do Not Absorb)

These platform capabilities are mature but are NOT absorption candidates
because they belong to other architectural layers.

| # | Capability | Platform Source | Why Not owlmlx |
|---|---|---|---|
| N1 | Catalog & intent routing | `platform-protocol-schema.md`, `catalog.json` | Product-layer: maps user intent to model choice. Not runtime truth. |
| N2 | Bootstrap supervisor | `ops_dashboard/supervisor.py` | Control-plane: solves dashboard self-bootstrap paradox. Not runtime. |
| N3 | Recovery orchestration | `ops_dashboard/recovery_service.py` | Control-plane: policy-driven service restart. Runtime provides health truth; control-plane decides recovery action. |
| N4 | Background job queue | `llm_router/background_jobs.py` + `background_worker.py` | Platform infrastructure: generic async SQLite queue. Not runtime-specific. |
| N5 | Multi-backend routing | `llm_router/backends.py`, `llm_router/app.py` | Routing layer: abstracts across runtimes. owlmlx is one runtime, not the router. |
| N6 | Runtime handoff (dual-runtime fallback) | `llm_router/runtime_handoff.py` | Routing policy: oMLX→llama.cpp fallback is platform redundancy policy, not runtime truth. |
| N7 | Chain executor (multi-model pipeline) | `llm_router/chain_executor.py` | Orchestration: framework-agnostic pipeline. Not runtime-level. |
| N8 | Desktop UI shell | `local-llm-desktop/` (Svelte + Tauri) | Product entry: UI above runtime. Consumes runtime truth, does not define it. |
| N9 | Image generation pipeline | `ops_dashboard/image_service.py` | Separate capability line: image != text runtime. |
| N10 | Work capability standard | `work-capability-standard.md` | Product-level: "can this model do this work?" is evaluation, not runtime truth. |
| N11 | Dashboard views & metrics aggregation | `ops_dashboard/views.py`, `ops_dashboard/metrics.py` | Control-plane UI: aggregates and presents. Not runtime-level. |
| N12 | CLI wrappers | `codex-local`, `claude-local` | Product entry: shell above runtime. |
| N13 | Action persistence (control jobs) | `ops_dashboard/control_jobs.py` | Control-plane: action state machine. Not runtime. |
| N14 | Kimi lab research surface | `ops_dashboard/kimi_lab.py` | Specialized UI: read-only research dashboard. Not runtime. |

## 5. Maturity Classification Summary

### Absorption Candidates — By Maturity

| Gap | Capability | Maturity | Absorption Type |
|---|---|---|---|
| Gap 1 | Runtime health semantics | **Absorbed + consumed** | `owlmlx/runtime_health.py` — 6 enums, 7 derivation functions, 85 tests; platform consumes |
| Gap 2 | Abort recovery state machine | Verified (field-tested) | Full module absorption |
| Gap 3 | Context concurrency policy | Verified (hardware-proven) | Full boundary ownership |
| Gap 4 | Memory budget enforcement | Verified (production use) | Full budget logic ownership |
| Gap 6 | Model lifecycle states | Verified (40+ phases) | Split: state definitions only |
| Gap 8 | Model lineage schema | Defined (mandatory for stable) | Full schema ownership |
| Gap 5 | Cache profile management | Verified but specialized | Partial: generalized contract only |
| Gap 7 | Per-model runtime truth | Verified (endpoints live) | Partial: schema + semantics only |

### Non-Candidates — By Reason

| Reason Category | Items |
|---|---|
| Product-layer (intent, UI, evaluation) | N1, N8, N10, N12 |
| Control-plane (orchestration, recovery, bootstrap) | N2, N3, N11, N13 |
| Routing-layer (multi-backend, fallback, pipeline) | N5, N6, N7 |
| Platform infrastructure (generic queues) | N4 |
| Separate capability line | N9 |
| Specialized research surface | N14 |

## 6. Next-Round Decision Hooks

### For Round 2 (Ownership Boundary Freeze)

The following questions must be resolved:

1. **Gap 6 split line:** Which lifecycle state definitions move to owlmlx
   vs stay in platform? Proposal: state enum + transition rules → owlmlx;
   gate tests + TTL policy + daemon → platform.

2. **Gap 5 generalization:** Does owlmlx own a cache truth contract, or
   only note that cache truth is a future gap? Proposal: own a minimal
   contract shell; current implementation stays in platform.

3. **Gap 7 transport boundary:** owlmlx defines the schema, platform
   provides HTTP transport. But who owns the "unload" mutation semantics?
   Proposal: owlmlx owns the mutation contract (what it means to unload);
   platform owns the endpoint (how the request arrives).

4. **Model-line placement (provisional):** Round 2 must give provisional
   placement for Gemma, Kimi 1T, and gpt-oss-120b within the unified
   boundary. This feeds Round 3 finalization.

### For Round 4 (First Absorption Target)

From the maturity ranking, the strongest first-absorption candidates are:

- **Gap 2 + Gap 3 bundle:** Abort recovery + context concurrency. Both are
  small (265 + 147 LOC), hardware-verified, oMLX-specific, and already
  self-contained. This is the highest-value, lowest-risk absorption.

- **Gap 4:** Memory budget enforcement. Small, critical, runtime-truth.

- **Gap 1:** Runtime health semantics. Higher value but larger scope —
  likely second-wave.
