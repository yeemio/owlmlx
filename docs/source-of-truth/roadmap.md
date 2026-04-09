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

Status: **in progress** (2026-04-09)

Prompt: `docs/phase-prompts/owlmlx-phase-1d-contract-adoption.md`

Current achieved outputs:

- shell-side bridge test imports `owlmlx`
- shell runtime samples validate against `owlmlx` schema
- shell protocol sections now reference `owlmlx` runtime contracts
- router runtime-status builders normalize through `owlmlx` helper functions

Remaining inside Phase 1D:

- wider contract-test alignment beyond runtime-status paths
- additional runtime-owned helper expansion

## 3. Phase 2: Large-Weight Path Productization

Goal:

- turn the first mature path into an explicitly owned `owlmlx` runtime path

Focus areas:

- naming and artifact structure that outlast a single specimen
- serving and lifecycle rules for large-weight workloads
- operator-visible truth for path-specific health and limits

Acceptance:

- path has stable terminology
- specimen-specific facts are separated from path-level facts

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
- alternate specialization paths

Acceptance:

- each new path has its own honest capability matrix
- no path is named after one temporary specimen
