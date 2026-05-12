# owlmlx Extraction Inventory

> Status: working inventory
> Updated: 2026-05-12 (Stage 3.1 c3 — post Stage 1/2 cleanup)

## 1. Purpose

This document turns `owlmlx` extraction from a principle into an inventory.

It answers three questions:

1. what already reflects `owlmlx` runtime judgment
2. what should be borrowed and internalized into `owlmlx`
3. what should remain external reference or platform-shell code

## 2. Classification Rules

Each item must be classified as one of:

1. `owlmlx-owned judgment`
2. `borrow and internalize`
3. `external reference only`
4. `platform-shell retained`

Only items in categories 1 and 2 are extraction candidates for `owlmlx`.

## 3. Extraction Discipline Rules

Before any extraction candidate moves or is reclassified, it must pass these
checks:

1. **Boundary test** — does this code primarily answer a runtime question?
   (See `repository-boundaries.md` section 7 for test questions.)
2. **Adoption label** — is this `owlmlx-owned judgment` or `borrow and
   internalize`? If the latter, has it been evaluated against owlmlx runtime
   principles?
3. **Capability label assignment** — what honest label does this get in the
   capability matrix? Borrowed code that has not been validated under owlmlx
   governance enters as `partial` or `experimental`, never `supported`.
4. **Split rule** — if a file mixes runtime truth with shell logic, split
   first, then extract the runtime portion. Do not move the whole file.
5. **Wave ordering** — respect the wave sequence (A → B → C). Do not skip
   ahead to Wave C internals if Wave A contracts are still unstable.
6. **No silent promotion** — moving code into the owlmlx repo does not
   automatically upgrade its capability label. Label promotion requires
   explicit evaluation and evidence.

## 4. Immediate Extraction Candidates

### 4.1 Large-Weight Path Runtime

| Current location | Classification | Why |
|---|---|---|
| `/Users/yeemio/AI/Agent/scripts/kimi-sharded-engine.py` | `owlmlx-owned judgment` | This is the clearest current implementation of the large-weight runtime path |
| `/Users/yeemio/AI/Agent/scripts/start-kimi.sh` | `borrow and internalize` | Startup wrapper for the large-weight path should eventually become an `owlmlx` runtime entrypoint |

### 4.2 Runtime Memory Governance And Switch Safety

| Current location | Classification | Why |
|---|---|---|
| `/Users/yeemio/AI/Agent/runtime_patches/omlx/swap-safe/apply-swap-safe-patch-v034.py` | `borrow and internalize` | Encodes runtime memory-governance and restart-safety ideas that should stop living as upstream patch machinery |
| `/Users/yeemio/AI/Agent/runtime_patches/omlx/swap-safe/apply-full-patch.py` | `borrow and internalize` | Same reason; transitional patch productization, not final home |
| `/Users/yeemio/AI/Agent/runtime_patches/omlx/swap-safe/validate-swap-safe-patch.py` | `borrow and internalize` | Validation logic reflects runtime invariants we will want in owned form |
| `/Users/yeemio/AI/Agent/runtime_patches/omlx/swap-safe/patch-guard.sh` | `external reference only` | Upgrade guard for patched oMLX remains transitional until `owlmlx` no longer depends on patched upstream files |

### 4.3 Runtime Truth Contracts

| Current location | Classification | Why |
|---|---|---|
| `/Users/yeemio/AI/Agent/tests/test_omlx_runtime_status.py` | `borrow and internalize` | Contract tests encode runtime truth expectations that should eventually point at `owlmlx` |
| `/Users/yeemio/AI/Agent/tests/test_kimi_runtime_status.py` | `borrow and internalize` | Same for large-weight path runtime truth |
| `/Users/yeemio/AI/Agent/docs/source-of-truth/local-llm-platform/platform-protocol-schema.md` | `platform-shell retained` | Current shell protocol remains above runtime, but runtime-owned contracts should be split out and then referenced here |
| `/Users/yeemio/AI/Agent/files/verification-assets/phase-42/kimi-crash-safe-resume-gate.md` | `borrow and internalize` | Safe-resume logic should become runtime governance truth inside `owlmlx` |
| `/Users/yeemio/AI/Agent/files/verification-assets/phase-42/kimi-nextgen-next-round-entry-safe-resume.md` | `borrow and internalize` | Resume-entry semantics should be normalized into runtime governance and hazard classification |
| `/Users/yeemio/AI/gitrep/owlmlx/files/verification-assets/phase-42-imported/kimi-crash-safe-resume-gate.md` | `owlmlx-owned judgment` | Imported first-instance safe-resume artifact preserved inside owlmlx |
| `/Users/yeemio/AI/gitrep/owlmlx/files/verification-assets/phase-42-imported/kimi-nextgen-next-round-entry-safe-resume.md` | `owlmlx-owned judgment` | Imported first-instance hazardous-operation reclassification artifact preserved inside owlmlx |
| `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime_status.py` | `owlmlx-owned judgment` | _Archived in Stage 1 (2026-05-11)_ — spec-shaped module with no runtime consumer; replaced by `RuntimeKernel.status_dict()` truth path. Lives at `archive/spec-layer-v0/owlmlx/runtime_status.py`. |
| `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py` | `owlmlx-owned judgment` | Queue-based generation gate — first owlmlx-owned serving discipline module |
| `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/settle_barrier_event.py` | `owlmlx-owned judgment` | Stage 2 (2026-05-12) renamed `reclaim_barrier_event` → `settle_barrier_event` to align with PR #649 vocabulary. Contract surface `owlmlx.settle_barrier_event`. |
| `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/memory_watermark.py` | `owlmlx-owned judgment` | Stage 2 PR #649 four-level pressure summary (`MemoryWatermark` / `WatermarkAction` + thresholds 65/80/90 %). Consumed by `memory_pressure_contract_to_dict` and `GET /v1/runtime/memory-watermark`. |
| `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/nonresident_model_admission_policy.py` | `owlmlx-owned judgment` | Hosts `pre_load_check()` — Stage 2 PR #649-shaped admission entrypoint. |
| `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_status.py` | `owlmlx-owned judgment` | _Archived in Stage 1 alongside `runtime_status.py`._ |
| `/Users/yeemio/AI/gitrep/owlmlx/tests/test_serving.py` | `owlmlx-owned judgment` | Tests for generation gate serialization, exception safety, async execution |
| `/Users/yeemio/AI/gitrep/owlmlx/tests/test_memory_watermark.py` | `owlmlx-owned judgment` | Stage 2 — 32 cases covering threshold mapping, classification bridge, four-outcome action policy. |
| `/Users/yeemio/AI/gitrep/owlmlx/tests/test_pre_load_check.py` | `owlmlx-owned judgment` | Stage 2 — 6 cases verifying alias contract + four-outcome verdict invariant. |
| `/Users/yeemio/AI/gitrep/owlmlx/tests/test_settle_barrier_event.py` | `owlmlx-owned judgment` | Stage 2 — 17 cases (renamed from `test_reclaim_barrier_event.py`). |

## 5. Platform-Shell Retained Areas

The following remain with the current desktop product shell repository even if
they consume `owlmlx` truth:

| Current location | Classification | Why |
|---|---|---|
| `/Users/yeemio/AI/Agent/llm_router/` | `platform-shell retained` | Router is integration and product routing glue above the runtime |
| `/Users/yeemio/AI/Agent/ops_dashboard/` | `platform-shell retained` | Dashboard and operator presentation remain outside runtime ownership |
| `/Users/yeemio/AI/Agent/local-llm-desktop/` | `platform-shell retained` | Desktop shell, onboarding, and user-facing workflows are not runtime source of truth |

## 6. Boundary-Split Items

Some current platform files mix runtime truth with shell logic. These should be
split rather than moved whole.

| Current location | Classification | Split direction |
|---|---|---|
| `/Users/yeemio/AI/Agent/llm_router/app.py` | `borrow and internalize` | Extract runtime-owned status contracts and path semantics into `owlmlx`; retain routing endpoints in platform shell |
| `/Users/yeemio/AI/Agent/ops_dashboard/metrics.py` | `borrow and internalize` | Extract runtime-owned truth shape and semantics into `owlmlx`; retain dashboard aggregation here |
| `/Users/yeemio/AI/Agent/ops_dashboard/app.py` | `platform-shell retained` | Keep UI/API composition; reference runtime-owned contracts from `owlmlx` |

## 7. Near-Term Extraction Sequence

### Wave A: Runtime Truth Contracts

First pull out:

- runtime status schemas
- large-weight path status schemas
- capability labels and path semantics
- contract-test expectations

The first owned truth targets for this wave are:

- `runtime-contracts.md`
- `runtime-status-schema.md`

**Wave A completion gate:**

Wave A is considered complete when:

1. `runtime-contracts.md` and `runtime-status-schema.md` are authoritative and
   stable (no open truth drift issues)
2. At least one executable module (`runtime_status.py`) validates against the
   schema
3. At least one shell-side consumer references owlmlx contract definitions
4. Contract-test expectations from the platform shell repository point at
   owlmlx truth, not at local copies

Current status: **complete** (2026-05-12, Stage 3.1 c3) —
- `serving.py`, `cache_truth.py`, `model_inventory.py`, `model_lineage.py`,
  `memory_budget.py`, `context_concurrency.py`, `abort_recovery.py`,
  `runtime_health.py`, `memory_pressure_contract.py`,
  `memory_pressure_eviction_policy.py`, `settle_barrier_event.py`,
  `recovery_supervisor_contract.py`, `request_context_length_truth.py`,
  `model_residency_policy.py`, `nonresident_loadability_lineage.py`,
  `nonresident_model_admission_policy.py`, and `memory_watermark.py`
  exist and validate against runtime decision paths.
- Shell-side `metrics.py`, `control_service.py`,
  `distilled_cache_substrate.py`, `primary_line_status.py`,
  `context_concurrency_policy.py`, and `abort_recovery.py` consume owlmlx
  contracts (see runtime-capability-matrix.md section 1 — `**platform
  consumes**` annotations).
- `kimi-sharded-engine.py` imports `GenerationGate` and large-weight
  serving status from owlmlx.
- Stage 1 (2026-05-11) archived 151 spec-as-code modules whose
  dataclasses had no runtime consumer; Stage 2 (2026-05-12) added
  `MemoryWatermark`, `SettleBarrierEvent`, and `pre_load_check` as
  PR #649-aligned public landmark types and wired them into the runtime
  consumer chain.

Wave A is closed. Open work belongs to Wave B and Wave C below.

### Wave B: Runtime Entrypoints

Then pull out:

- large-weight runtime startup path
- owned serve entrypoints
- runtime-specific health and status surfaces

**Wave B entry prerequisite:** Wave A completion gate must be satisfied.

**Wave B completion gate:**

Wave B is considered complete when:

1. owlmlx has at least one owned serve entrypoint (not a wrapper around an
   external runtime's server)
2. Large-weight path startup can be invoked through an owlmlx-owned command
3. Health and status surfaces return owlmlx-schema-compliant responses
4. The startup path has been validated against the heavy execution protocol
   (dry-run, single-unit, serial, thresholded)

Current status: **started, partial** (updated 2026-05-12) — owlmlx now
serves its own HTTP surface via `owlmlx.runtime.server.create_app` with
frozen `/healthz` and `/v1/runtime/status` contracts (Stabilization-1),
streaming `/v1/messages` (Anthropic shape), `/v1/chat/completions`,
`/v1/completions`, and Stage 2's `/v1/runtime/memory-watermark`. Real
local smokes verified on `gpt-oss-20b-MXFP4-Q4`, `Qwen3.5-27B`, and
`Qwen3.5-35B-A3B-4bit`. Large-weight startup path (Wave B item 2) and
heavy execution protocol dry-run validation (Wave B item 4) remain open.

### Wave C: Memory Governance Internals

Then internalize:

- load/unload safety rules
- restart and reclaim semantics
- active-request protection semantics
- migration away from patching upstream files in place

**Wave C entry prerequisite:** Wave B completion gate must be satisfied.

**Wave C completion gate:**

Wave C is considered complete when:

1. Memory governance decisions are made by owlmlx-owned code, not by patches
   applied to an upstream runtime
2. Active-request protection logic lives inside owlmlx, not as patch-guard
   scripts
3. The patched-upstream dependency can be removed or reduced to substrate-only
4. Runtime governance (hazardous operations, safe-resume) is enforced by owlmlx
   code, not just documented

Current status: **partially internalized** (updated 2026-05-12) —
- Active-request protection lives in `owlmlx/serving.py` (`GenerationGate`)
  and is enforced by tests.
- Memory governance decisions (watermark + admission + eviction) are
  made by owlmlx-owned code in `memory_pressure_contract.py`,
  `memory_pressure_eviction_policy.py`, `memory_watermark.py`, and
  `nonresident_model_admission_policy.py`.
- Settle-barrier semantics are owlmlx-owned via `settle_barrier_event.py`.
- Runtime governance (hazardous operations / safe-resume) is documented
  but not yet enforced in code beyond the abort recovery state machine.
- **Patch-form dependency**: operational scripts in
  `/Users/yeemio/AI/Agent/runtime_patches/omlx/swap-safe/` still apply
  patches on top of an upstream oMLX install. These are Stage 3+
  migration candidates (see contract-mapping.md §3, §8). The runtime
  principles they enforce are owlmlx-owned; only the operational
  tooling needs to move.

## 8. Capability Label Promotion Criteria

A capability currently labeled `partial` or `experimental` in the runtime
capability matrix may only be promoted to `supported` when:

1. **Implementation evidence** — owlmlx-owned code exists that implements the
   capability (not just documents describing it)
2. **Test coverage** — at least one test validates the capability's core
   behavior
3. **No false dependency** — the capability works through owlmlx's own code
   path, not solely through an external runtime being patched
4. **Governance compliance** — if the capability touches hazardous territory,
   it must have entered through the heavy execution protocol
5. **Adoption label resolved** — if borrowed, it has been explicitly evaluated
   against owlmlx runtime principles and relabeled as owlmlx-owned

A capability may NOT be promoted based solely on:

- documentation existing
- the feature working in an external runtime we reference
- a single specimen demonstrating it once

## 9. Explicit Non-Extraction

The following should not be described as `owlmlx` support just because they
exist nearby:

- dashboard pages or desktop cards
- router-only orchestration policy
- upstream `oMLX` admin surfaces we have not re-owned
- specimen-specific operational details not yet elevated into runtime truth
- legacy repository names used by the current product shell
