# owlmlx Roadmap

> Status: working roadmap
> Updated: 2026-04-09

## 1. Phase 0: Source-of-Truth Freeze

Immediate goal:

- establish `owlmlx` as a self-owned runtime source of truth
- freeze naming, boundaries, and architecture
- stop describing `owlmlx` as a borrowed runtime identity

Acceptance:

- core documents align on the same project definition
- `large-weight runtime path` replaces specimen-led naming
- the current desktop product shell repository is clearly documented as the
  shell above `owlmlx`

## 2. Phase 1: Runtime Extraction Plan

Goal:

- identify which runtime-adjacent code and contracts should eventually move into
  `owlmlx`

Focus areas:

- memory governance logic
- switching safety logic
- runtime truth exposure contracts
- large-weight serving path ownership

Acceptance:

- extraction map exists
- runtime-owned vs shell-owned modules are clearly separated
- extraction inventory names concrete current files and split directions

## 2.3 Phase 1A: Runtime Governance Freeze

Goal:

- write hazardous operation governance and safe-resume contract into owlmlx truth
- stop treating runtime governance as temporary incident notes

Acceptance:

- runtime-governance.md and hazardous-operations.md exist as authoritative truth
- hazardous operation classification is formal, not ad-hoc
- safe-resume contract is defined as runtime governance, not only crash recovery

Status: **complete** (2026-04-09)

## 2.5 Phase 1B: Rename And Contract Migration

Goal:

- stop freezing temporary shell names into runtime truth
- map shell-hosted runtime truth to `owlmlx`-owned contracts

Acceptance:

- rename strategy exists
- contract mapping exists
- shell-only versus runtime-owned truth is called out explicitly

Status: **complete** (2026-04-09)

## 2.7 Phase 1C: Runtime Bridge

Goal:

- owlmlx acquires its first executable code (runtime status schema validation)
- main repo (AI/Agent) formally references owlmlx as upstream runtime truth
- owlmlx governance rules enter main repo execution contract
- contract-mapping honesty labels are corrected

Acceptance:

- owlmlx has at least one Python module with passing tests
- main repo has at least 2 formal references to owlmlx
- phase-delivery-agent-contract.md includes runtime governance gate
- contract-mapping.md labels reflect actual ownership honestly

Status: **complete** (2026-04-09)

Prompt: `docs/phase-prompts/owlmlx-phase-1c-runtime-bridge.md`

Actual outputs:

- first executable Python package: `owlmlx/runtime_status.py`
- first owlmlx tests: `tests/test_runtime_status.py`
- main repo references to owlmlx runtime truth and governance
- phase-delivery contract updated with runtime governance gate

## 2.9 Phase 1D: Contract Adoption

Goal:

- make the current desktop product shell repository adopt `owlmlx` contract
  language through tests and references

Acceptance:

- shell-side bridge test imports `owlmlx`
- runtime contract adoption plan exists
- shell-side runtime samples validate against `owlmlx` schema

Status: **substantially complete** (2026-04-10)

Waves 1–3 of the contract adoption plan are complete. Wave 4 (runtime-owned
module expansion beyond schema validation) is deferred to Phase 2 because it
requires new owlmlx implementation, which is the Phase 2 goal.

Prompt: `docs/phase-prompts/owlmlx-phase-1d-contract-adoption.md`

Current achieved outputs:

- shell-side bridge test imports `owlmlx`
- shell runtime samples validate against `owlmlx` schema
- shell protocol sections now reference `owlmlx` runtime contracts
- router runtime-status builders normalize through `owlmlx` helper functions

Deferred to Phase 2:

- wider contract-test alignment beyond runtime-status paths
- additional runtime-owned helper expansion (requires new owlmlx modules)

## 2.11 Phase 1E: Adoption Model And Loop Discipline Freeze

Goal:

- formally freeze the open-source adoption model into core source-of-truth
- establish autonomous loop discipline as a self-iteration protocol
- tighten extraction inventory with discipline rules and wave ordering

Acceptance:

- adoption model exists in product-definition.md as a formal section
- autonomous-loop-discipline.md exists as authoritative document
- extraction-inventory.md includes discipline rules before candidates list
- capability matrix reflects adoption model and loop discipline as supported
- AGENTS.md, README.md, and master-outline.md reference adoption model

Status: **complete** (2026-04-10)

Round: `owlmlx-round-1.md`

Actual outputs:

- adoption model section (product-definition.md section 6)
- extraction discipline rules (extraction-inventory.md section 3)
- autonomous-loop-discipline.md (new authoritative document)
- capability matrix updated with adoption + extraction + loop rows
- README, master-outline, AGENTS.md updated with adoption model truth

## 3. Phase 2: Large-Weight Path Productization

Goal:

- turn the first mature path into an explicitly owned `owlmlx` runtime path
- produce real owlmlx-owned serving/lifecycle modules, not just documentation

Focus areas:

- naming and artifact structure that outlast a single specimen
- serving and lifecycle rules for large-weight workloads
- operator-visible truth for path-specific health and limits

Acceptance:

- path has stable terminology
- specimen-specific facts are separated from path-level facts
- at least one real owlmlx-owned serving module with tests
- platform shell references the new module

Status: **in progress** (2026-04-10)

Round 1 outputs:

- path scope frozen (path-level vs specimen-only facts)
- first owned module selected: queue-based generation gate
- `owlmlx/serving.py` — GenerationGate class extracted and rebuilt
- `tests/test_serving.py` — 11 tests including serialization, exception
  safety, async execution, timing verification
- extraction-inventory and capability-matrix updated

Round 2 outputs:

- `owlmlx/serving_status.py` — large-weight serving status builder
- `tests/test_serving_status.py` — 10 tests for status composition
- `build_large_weight_serving_status()` composes gate + memory + lifecycle
- `merge_specimen_identity()` layers specimen detail on owlmlx base

Round 3 outputs:

- `kimi-sharded-engine.py` bridged to import owlmlx GenerationGate
- `kimi-sharded-engine.py` bridged to import owlmlx serving status builders
- Graceful fallback when owlmlx not on path (backward compatible)
- Generate endpoint exposes gate timing metadata
- Shell now formally references owlmlx as upstream runtime truth

## 4. Phase 3: Core Runtime Consolidation

Goal:

- reduce dependence on external runtime identity and patch inheritance

Focus areas:

- self-owned core modules
- self-owned lifecycle and memory strategy
- self-owned runtime status surfaces

Acceptance:

- `owlmlx` has its own implementation center of gravity
- runtime behavior is documented and owned here first

## 5. Phase 4: Additional Runtime Paths

Goal:

- add more runtime paths only when they have real capability truth

Candidate areas:

- generalized interactive path
- second large-weight specimen family
- high-fidelity teacher/reference path
- alternate specialization paths
- overflow / NVMe-tier execution path

Acceptance:

- each new path has its own honest capability matrix
- no path is named after one temporary specimen

Current live candidate:

- `gemma-4-31B-it` as the first serious high-fidelity teacher/reference
  specimen candidate

External reference:

- Hypura is recorded as a future overflow-path reference in
  `hypura-overflow-path-reference.md`. It is not an adopted backend and should
  not be used to reopen current Kimi large-weight serving boundaries.

## 6. Training And Production Program

Goal:

- unify owlmlx training substrate with Gemma production mainline
- owlmlx owns training environment, artifact, and training-to-serving contracts
- Gemma validates the substrate as the first production mainline model

Program contract: `owlmlx-gemma-training-and-production-mainline`

### Round 1 — Training Substrate Contract

Status: **complete** (2026-04-10)

Delivered:

- `training-substrate-contract.md` — authoritative training environment,
  stack selection, and substrate boundary contract
- `runtime-contracts.md` updated — training substrate added as third contract
  family
- `runtime-capability-matrix.md` updated — training substrate row added
- `master-outline.md` updated — new document listed, dominant question updated

### Round 2 — Artifact Layout Contract

Status: **complete** (2026-04-10)

Delivered:

- `artifact-layout-contract.md` — base model paths, tuned artifact layout,
  run-id naming, metadata.json registration, checkpoint structure
- `runtime-contracts.md` updated — artifact layout added as 4th contract family
- `runtime-capability-matrix.md` updated — artifact layout row added
- `master-outline.md` updated — new document listed

### Round 3 — Training-To-Serving Contract

Status: **complete** (2026-04-10)

Delivered:

- `training-to-serving-contract.md` — load path, serving feasibility checklist,
  runtime status extension for tuned artifacts, responsibility boundary
- `runtime-contracts.md` updated — training-to-serving added as 5th family
- `runtime-capability-matrix.md` updated — training-to-serving row added
- `master-outline.md` updated — new document listed

### Round 4 — Minimal Gemma Pilot

Status: **complete** (2026-04-10)

Delivered:

- `owlmlx/training.py` — artifact registration module (build, write, read,
  discover, validate_for_serving)
- `tests/test_training.py` — 17 tests for artifact registration
- Minimal LoRA pilot: 5-step training on gemma-4-31B-it (loss 10.5→6.5)
- Adapter saved to contract-compliant path with metadata.json
- Load verification: adapter loads via mlx_lm.load(adapter_path=...)
- Inference delta: confirmed (tuned output differs from base)
- Feasibility note: `files/pilot-results/gemma-pilot-lora-20260410-feasibility-note.md`

### Round 5 — Production Mainline Freeze

Status: **complete** (2026-04-10)

Delivered:

- `gemma-high-fidelity-role.md` rewritten as authoritative production freeze
- Gemma formally frozen as production mainline (not candidate)
- Current capabilities (6 items) and limitations (8 items) explicitly listed
- owlcoda boundary defined: consumes, does not define substrate
- What comes next listed (data engineering → evaluation → production training)

## 7. Platform Capability Absorption And Convergence Program

Goal:

- absorb mature capabilities from the original local LLM platform into owlmlx
- freeze ownership boundary between runtime (owlmlx) and control-plane/shell
- prevent owlmlx from becoming a parallel system that duplicates the platform
- place model lines (Gemma, Kimi 1T, gpt-oss-120b) in unified architecture

Program contract: `owlmlx-platform-capability-absorption-and-convergence`

### Round 1 — Freeze Capability Absorption Inventory

Status: **complete** (2026-04-10)

Delivered:

- `capability-absorption-inventory.md` — gap-driven inventory organized around
  what owlmlx lacks, not platform archaeology
- 8 gaps identified with maturity classification and absorption recommendation
- 14 explicit non-candidates with reasoning
- Next-round decision hooks for ownership boundary and first absorption target
- Strongest first-absorption candidates: abort recovery + context concurrency

### Round 2 — Freeze Ownership Boundary

Status: **complete** (2026-04-10)

Delivered:

- `ownership-boundary.md` — formal ownership table for all platform capabilities
- 5 ownership categories: runtime-owned (R), control-plane (C), routing (T),
  shell-hosted (S), product-surface (P)
- 19 runtime-owned capabilities (10 already owned, 9 to absorb)
- 9 control-plane, 7 routing, 5 shell-hosted, 6 product-surface
- Ownership split rules frozen (runtime IS vs platform DOES WITH)
- Provisional model-line placement for Gemma, Kimi 1T, gpt-oss-120b
- Truth owner index for future questions

### Round 3 — Freeze Model-Line Placement

Status: **complete** (2026-04-10)

Delivered:

- `model-line-placement.md` — formal position for every model line
- Gemma: owlmlx-native production mainline (only training-integrated line)
- Kimi 1T: large-weight path specimen (lab, not production)
- gpt-oss-120b: platform-managed stable heavy synthesis
- Distilled-27B: platform default (standard + backup paths)
- Qwen3.5, Mistral-Large: standard platform models
- Two runtime path classes identified: standard MLX + large-weight
- owlmlx does not own product roles — permanent split

### Round 4 — First High-Value Absorption Target

Status: **complete** (2026-04-10)

Delivered:

- `first-absorption-target.md` — selected first absorption group
- Group: abort recovery + context concurrency + memory budget (~460 LOC)
- All three are hardware-verified MLX/Metal substrate boundaries
- Why more urgent than training: prevents dual-system drift on physical truths
- Expected deliverables: new owlmlx module(s), tests, router imports owlmlx
- Second-wave candidates ranked: health semantics, lifecycle states, lineage

### Round 5 — Convergence Freeze

Status: **complete** (2026-04-10)

Delivered:

- `convergence-posture.md` — formal convergence posture freeze
- Convergence scorecard: 46/46 capabilities assigned, 4/19 runtime-owned in code
- 9 capabilities to absorb (code still in platform)
- No bifurcation risk — every capability has one truth owner
- Recommendation: enter code absorption phase (substrate boundaries first)
- All 5 program success criteria satisfied
- All 7 hard rules compliant
  (small, hardware-verified, self-contained)
