# owlmlx Ownership Boundary

> Status: authoritative
> Updated: 2026-04-11
> Program: owlmlx-platform-capability-absorption-and-convergence
> Round: consumption-wiring

## 1. Purpose

This document freezes the formal ownership boundary between owlmlx (runtime)
and the original local LLM platform layers. Every capability that touches
runtime truth must have exactly one truth owner.

## 2. Ownership Categories

| Category | Code | Meaning |
|---|---|---|
| `runtime-owned` | R | owlmlx defines the truth, owns the schema and semantics |
| `control-plane-owned` | C | ops_dashboard / lifecycle daemon owns orchestration |
| `routing-owned` | T | llm_router owns transport and multi-backend abstraction |
| `shell-hosted` | S | Platform shell hosts execution; owlmlx provides contracts |
| `product-surface-owned` | P | Desktop / CLI / UI owns user-facing experience |
| `verification-residue` | V | Experimental or test artifact; not a long-term truth source |

## 3. Capability Ownership Table

### 3.1 Runtime Truth (owlmlx-owned)

| # | Capability | Owner | Current Location | Absorption Status |
|---|---|---|---|---|
| R1 | Runtime identity and architecture | R | owlmlx docs | Already owned |
| R2 | Runtime status schema validation | R | `owlmlx/runtime_status.py` | Already owned |
| R3 | Generation gate (concurrency boundary) | R | `owlmlx/serving.py` | Already owned |
| R4 | Large-weight serving status | R | `owlmlx/serving_status.py` | Already owned |
| R5 | Training substrate contract | R | owlmlx docs | Already owned |
| R6 | Artifact layout contract | R | owlmlx docs | Already owned |
| R7 | Training-to-serving contract | R | owlmlx docs | Already owned |
| R8 | Memory governance principles | R | owlmlx docs | Already owned (doc-only) |
| R9 | Hazardous-operation governance | R | owlmlx docs | Already owned (doc-only) |
| R10 | Safe-resume contract | R | owlmlx docs | Already owned (doc-only) |
| R11 | Abort recovery state machine | R | `owlmlx/abort_recovery.py` | **Absorbed + consumed** — platform `abort_recovery.py` delegates to `AbortRecoveryTracker` |
| R12 | Context concurrency boundary definitions | R | `owlmlx/context_concurrency.py` | **Absorbed + consumed** — platform `context_concurrency_policy.py` imports gate, threshold, version |
| R13 | Memory budget definition and calculation | R | `owlmlx/memory_budget.py` | **Absorbed + consumed** — platform `control_service.py` consumes via `model_inventory.inventory_budget_check()` plus budget constants |
| R14 | Runtime health semantic tiers | R | `owlmlx/runtime_health.py` | **Absorbed + consumed** — 6 enum types, 7 derivation functions; platform `metrics.py` consumes via `model_inventory.inventory_health_snapshot()` and `derive_platform_status()` |
| R15 | Model lifecycle state definitions | R | `model-lifecycle-and-upgrade-gate.md` | **Deferred** — 6 states (stable/backup/candidate/experimental/blocked/parked) are product lifecycle classification, not runtime substrate truth; `lifecycle.py` has no state enum or transition function; absorbing would produce an orphan enum with no derivation chain or platform consumer |
| R16 | Model lineage schema | R | `owlmlx/model_lineage.py` | **Absorbed + consumed** — canonical lineage schema, validation, and truth inheritance rules; platform `primary_line_status.py` normalizes/validates catalog lineage |
| R17 | Per-model runtime truth schema | R | `owlmlx/model_inventory.py` | **Absorbed + consumed** — model inventory schema + pure budget/health derivation; platform fills snapshots and keeps transport/probes |
| R18 | Cache truth contract | R | `owlmlx/cache_truth.py` | **Absorbed + consumed** — cache profile labels, flag schema, restart-required derivation, and TurboQuant cache-safety rules; platform keeps env mutation, process probing, Distilled assets, and endpoints |
| R19 | Gemma production mainline identity | R | owlmlx docs | Already owned |
| R20 | Runtime model visibility contract | R | `owlmlx/runtime_model_visibility.py` | **Introduced** — owlmlx owns rule `runtime_gate_required_before_visible`; formal visibility list now lives at `GET /v1/openai/models`, diagnostics at `GET /v1/runtime/model-visibility`, and `/v1/models` stays loaded inventory; gate is owlmlx registry plus base-model `config.json` presence, while lifecycle curation and extreme-experiment classification remain platform-owned |

### 3.2 Control-Plane (platform-owned)

| # | Capability | Owner | Location | Notes |
|---|---|---|---|---|
| C1 | Lifecycle daemon (polling + auto-heal) | C | `ops_dashboard/lifecycle.py` | Consumes R14; owns lifecycle state definitions (R15 deferred — product classification); executes TTL/auto-heal policy |
| C2 | Recovery orchestration | C | `ops_dashboard/recovery_service.py` | Policy-driven restart decisions |
| C3 | Bootstrap supervisor | C | `ops_dashboard/supervisor.py` | Layer-0 cold-start; not runtime |
| C4 | Action persistence + state machine | C | `ops_dashboard/control_jobs.py` | Operational audit trail |
| C5 | Model load enforcement | C | `ops_dashboard/control_service.py` | Uses R13 budget truth; enforces whitelist |
| C6 | TTL eviction policy | C | `ops_dashboard/lifecycle.py` | Policy decisions, not runtime truth |
| C7 | Upgrade gate test execution | C | platform docs + tests | Quality validation is product concern |
| C8 | Platform readiness aggregation | C | `ops_dashboard/metrics.py` | Aggregates R14 into composite view |
| C9 | Diagnostics endpoints | C | `ops_dashboard/app.py` | HTTP API for dashboard consumption |

### 3.3 Routing Layer (router-owned)

| # | Capability | Owner | Location | Notes |
|---|---|---|---|---|
| T1 | Multi-backend routing | T | `llm_router/backends.py` | Abstracts across runtimes |
| T2 | Runtime handoff (fallback policy) | T | `llm_router/runtime_handoff.py` | oMLX→llama.cpp fallback |
| T3 | OpenAI compatibility proxy | T | `llm_router/app.py` catch-all | Transport, not runtime |
| T4 | Background job queue | T | `llm_router/background_jobs.py` | Generic async infrastructure |
| T5 | Chain executor | T | `llm_router/chain_executor.py` | Multi-model pipeline |
| T6 | Per-model runtime truth transport | T | `llm_router/app.py` endpoints | HTTP transport of R17 schema |
| T7 | Context concurrency enforcement | T | `llm_router/context_concurrency_policy.py` | Enforces R12 boundaries at request level |

### 3.4 Shell-Hosted (platform hosts, owlmlx provides contract)

| # | Capability | Owner | Location | Notes |
|---|---|---|---|---|
| S1 | Kimi sharded engine | S | `kimi-sharded-engine.py` | Imports owlmlx GenerationGate + status |
| S2 | oMLX engine instance | S | External process (:8001) | owlmlx defines contracts, not engine |
| S3 | llama.cpp instance | S | External process (:8012) | Backup runtime, not owlmlx-hosted |
| S4 | vLLM-MLX instance | S | External process (:8010) | Alternate runtime |
| S5 | manage-local-stack.sh | S | Platform scripts | Operator tooling, not runtime |

### 3.5 Product Surface (desktop/CLI-owned)

| # | Capability | Owner | Location | Notes |
|---|---|---|---|---|
| P1 | Desktop UI shell | P | `local-llm-desktop/` | Tauri + Svelte product entry |
| P2 | CLI wrappers (codex-local, claude-local) | P | Platform scripts | Product entry points |
| P3 | Catalog & intent routing | P | `catalog.json` | Product-layer model selection |
| P4 | Work capability standard | P | Platform docs | Evaluation / quality benchmark |
| P5 | Image generation pipeline | P | `ops_dashboard/image_service.py` | Separate capability line |
| P6 | Dashboard views | P | `ops_dashboard/views.py` | UI presentation |

## 4. Ownership Split Rules

### 4.1 Runtime-Owned vs Control-Plane Split

The split line is: **"Does this define what the runtime IS, or what the
platform DOES WITH the runtime?"**

- Runtime IS: health tiers, concurrency boundaries, memory budget, lifecycle
  states, lineage schema → owlmlx
- Platform DOES: poll health, enforce policy, orchestrate restart, aggregate
  snapshots, present UI → control-plane

### 4.2 Runtime-Owned vs Routing Split

The split line is: **"Does this define a substrate truth, or does it apply
the truth at request-dispatch time?"**

- Substrate truth: "≤48K → 4-way, >48K → 1-way" is a hardware fact → owlmlx
- Request dispatch: "this request is >48K, acquire semaphore" → router
- Transport: HTTP endpoint shape for runtime truth → router
- Schema + semantics of what the endpoint returns → owlmlx

### 4.3 Shell-Hosted Boundary

Shell-hosted means the platform runs the process, but owlmlx provides the
contracts the process must honor. If owlmlx provides a `GenerationGate`,
the shell imports it. If owlmlx defines a status schema, the shell validates
against it.

## 5. Provisional Model-Line Placement

These placements feed Round 3 finalization.

### 5.1 Gemma (gemma-4-31B-it)

| Aspect | Placement | Owner |
|---|---|---|
| Production mainline identity | owlmlx (R19) | Runtime-owned |
| Training substrate | owlmlx (R5, R6, R7) | Runtime-owned |
| Serving on platform | Shell-hosted (S2 via oMLX) | Shell-hosted |
| Product routing | Router (T1, T6) | Routing-owned |
| Lifecycle state (stable promotion) | Platform-owned (R15 deferred); platform defines states and executes gate (C7) | Platform-owned |

Gemma is the first model line that is owlmlx-native from training through
serving. Its runtime contracts are already frozen. It currently serves via
oMLX on the standard platform path. No special shell treatment needed.

### 5.2 Kimi 1T (large-weight path)

| Aspect | Placement | Owner |
|---|---|---|
| Large-weight path validation | owlmlx (R3, R4) | Runtime-owned |
| Sharded engine | Shell-hosted (S1) | Shell-hosted (imports owlmlx) |
| Background-heavy serving posture | owlmlx docs | Runtime-owned |
| Product routing | Router (T1) via dedicated port :8014 | Routing-owned |
| Lifecycle state | Experimental / lab | Platform-owned (R15 deferred); product classification, not runtime truth |

Kimi is the first validated specimen on the large-weight path. It already
bridges into owlmlx (GenerationGate, serving status). It is NOT a production
mainline — it is a lab/experimental specimen that proved path-level truths.

### 5.3 gpt-oss-120b (retired local heavy synthesis)

| Aspect | Placement | Owner |
|---|---|---|
| Model identity | Retired from local active set | Platform-owned historical line |
| Runtime | None in active owlmlx visibility | Not active |
| Runtime truth | Historical evidence only | Not a current gate |
| Lifecycle state | Removed from active RC and visibility | Coordinator-owned decision |
| Memory budget | No longer used as pressure canary | Replaced by DeepSeek 2bit-DQ lane |

gpt-oss-120b was removed from the active local model set on 2026-05-05. It no
longer blocks the Model RC gate, no longer appears in the runtime-owned
visibility registry, and no longer serves as the heavyweight pressure canary.
DeepSeek-V4-Flash-2bit-DQ owns the pressure/adaptation lane instead.

### 5.4 Other Platform Models

| Model | Runtime | Lifecycle State | Special Treatment |
|---|---|---|---|
| Distilled-27B (MLX-4bit) | oMLX | Stable (primary default) | Cache substrate (Gap 5) |
| Distilled-27B (Q4_K_M GGUF) | llama.cpp | Backup | Conversion lineage consumed via R16 |
| Qwen3.5-35B-A3B-4bit | oMLX | Stable (fast general) | None |
| Mistral-Large Q4-MLX | oMLX | Stable (alternate) | None |
| MiroThinker-1.7 Q8 | Kimi engine | Stable (search scout) | Lab engine |

These models are platform-managed. owlmlx provides: (a) runtime truth schema
they conform to, (b) lineage schema (R16, absorbed + consumed). Lifecycle state
definitions (R15) remain platform-owned — product classification, not
runtime truth. The platform manages their catalog placement, routing,
lifecycle gates, and product surface.

## 6. Truth Owner Index

For any future question "who owns the truth about X?", use this index:

| Question | Truth Owner |
|---|---|
| Is this model loaded? | owlmlx (R14, R17) |
| Can this model serve right now? | owlmlx (R14) health tier |
| Should we restart this backend? | Control-plane (C1, C2) |
| What is the memory budget? | owlmlx (R13) |
| Does this request fit concurrency limits? | owlmlx (R12) defines; router (T7) enforces |
| Is the engine contaminated after abort? | owlmlx (R11) |
| What lifecycle state is this model? | Platform-owned (R15 deferred — product classification) |
| Where did these weights come from? | owlmlx (R16) lineage schema |
| Which model should the user see by default? | Product surface (P3) catalog |
| How do we recover from a cold start? | Control-plane (C3) |
