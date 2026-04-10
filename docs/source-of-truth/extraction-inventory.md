# owlmlx Extraction Inventory

> Status: working inventory
> Updated: 2026-04-09

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
| `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime_status.py` | `owlmlx-owned judgment` | First extracted executable runtime-truth module |
| `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_status.py` | `owlmlx-owned judgment` | First test protection for extracted runtime-truth code |

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

### Wave B: Runtime Entrypoints

Then pull out:

- large-weight runtime startup path
- owned serve entrypoints
- runtime-specific health and status surfaces

### Wave C: Memory Governance Internals

Then internalize:

- load/unload safety rules
- restart and reclaim semantics
- active-request protection semantics
- migration away from patching upstream files in place

## 8. Explicit Non-Extraction

The following should not be described as `owlmlx` support just because they
exist nearby:

- dashboard pages or desktop cards
- router-only orchestration policy
- upstream `oMLX` admin surfaces we have not re-owned
- specimen-specific operational details not yet elevated into runtime truth
- legacy repository names used by the current product shell
