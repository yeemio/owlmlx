# owlmlx Contract Mapping

> Status: working mapping
> Updated: 2026-05-12 (Stage 3.2 Track A — independence cleanup)

## 1. Purpose

This document maps current shell-layer runtime truth surfaces to `owlmlx`'s
owned contract model.

It distinguishes:

- `owned now`
- `owned but still shell-hosted`
- `shell-only`
- `drift or missing`

## 2. Mapping Categories

| Category | Meaning |
|---|---|
| `owned now` | Already captured in `owlmlx` truth |
| `owned but still shell-hosted` | Semantically belongs to `owlmlx`, but current transport or implementation still lives in the shell repository |
| `shell-only` | Product-shell concern, not runtime-owned truth |
| `drift or missing` | Not yet properly mapped into `owlmlx` contracts |

## 3. Core Runtime Contract Mapping

Status reflects post-Stage 1/2 reality (2026-05-12). Items where owlmlx
now owns a stable module AND the shell already references it via a
documented bridge are `owned, shell-proxied`. Items where the owlmlx
contract is stable but the shell still carries its own private copy
remain `owned but still shell-hosted` and are the Stage 3+ migration
candidates.

| Current shell truth | owlmlx contract target | Category | Notes |
|---|---|---|---|
| oMLX-shape runtime status route | `core runtime status` | `owned now` | owlmlx serves its own `/v1/runtime/status` (frozen contract per Stabilization-1). Legacy oMLX-shape status route on the shell side is now redundant; the shell may proxy or retire it. |
| Per-model memory & load state | `core runtime status` | `owned, shell-proxied` | `owlmlx/model_inventory.py` owns this. Shell `metrics.py` and `control_service.py` build inventory snapshots through owlmlx. |
| Cache tier truth | `core runtime status` | `owned, shell-proxied` | `owlmlx/cache_truth.py` owns this. Shell `distilled_cache_substrate.py` and `primary_line_status.py` consume it. |
| Quantization metadata truth | `core runtime status` | `owned now` | Migrated 2026-05-12 (Stage 3.1 c4). `owlmlx/quantization_metadata.py` consolidates the previously scattered coverage: `ModelLineage` artifact-string fields, `cache_truth.turboquant_cache_safety`, and a new bits/is_static/runtime_supported derivation. Exposed at `GET /v1/runtime/quantization-metadata?model_id=X`. 29 tests cover bit parsing, runtime-support classification, cache-safety integration, route resolution, and AGENTS anti-regression rule compliance. |
| Snapshot composition | none | `shell-only` | Snapshot embedding is a shell integration concern. |
| Agent-side oMLX `swap-safe` patch scripts | n/a (already owlmlx-owned via independent contracts) | `external legacy reference` | The runtime ideas these scripts encode (memory governance, settle barrier, abort recovery) are already independently owlmlx-owned via `memory_pressure_contract` / `memory_pressure_eviction_policy` / `settle_barrier_event` / `abort_recovery`. The Agent-side scripts at `/Users/yeemio/AI/Agent/runtime_patches/omlx/` patch a different runtime (oMLX) and are **not an owlmlx extraction target**. They may remain useful as historical comparison material only. owlmlx does not retire them; oMLX does. |

## 4. Large-Weight Runtime Path Mapping

| Current shell truth | owlmlx contract target | Category | Notes |
|---|---|---|---|
| `GET /v1/runtime/kimi/status` response shape | `large-weight runtime path status` | `owned but still shell-hosted` | Path-level runtime truth |
| `interactive_status=background_only` | `large-weight runtime path status` | `owned now` | Already part of owlmlx path honesty |
| `lifecycle_mode=manual_start` | `large-weight runtime path status` | `owned now` | Honest path-level lifecycle truth |
| `prefill_baseline` / `decode_baseline` | `large-weight runtime path status` | `owned but still shell-hosted` | Runtime evidence fields, still shell transport |
| Kimi Lab summary endpoint | none | `shell-only` | Product/operator summary surface above runtime |

## 5. Governance Contract Mapping

| Current shell truth | owlmlx contract target | Category | Notes |
|---|---|---|---|
| `kimi-crash-safe-resume-gate.md` | `runtime governance` | `owned but still shell-hosted` | Principle owned in owlmlx; first concrete implementation still lives in Agent repo |
| `kimi-nextgen-next-round-entry-safe-resume.md` | `hazardous operations` | `owned but still shell-hosted` | Reclassification semantics are owned in owlmlx; concrete entry document remains in Agent repo |
| shell execution prompts for risky runtime work | `runtime governance` | `drift or missing` | Future prompts should reference owlmlx governance directly |

## 6. Current Dominant Drifts

Updated 2026-05-12 (Stage 3.1 c2).

The remaining real drifts after Stage 1/2/3.1/3.2-Track-A cleanup:

- **Shell prompts and risky-execution playbooks** still reference oMLX patch
  paths rather than `runtime-governance.md` / `hazardous-operations.md` /
  `settle_barrier_event` directly. This is shell-side drift; owlmlx already
  owns the principle.

Resolved drift (Stage 3.1 c4, 2026-05-12):

- ~~Quantization metadata lacks a dedicated owlmlx contract~~ — owlmlx now
  owns `owlmlx/quantization_metadata.py` exposed at
  `GET /v1/runtime/quantization-metadata`.

Resolved drift (Stage 3.2 Track A, 2026-05-12):

- ~~`swap-safe` patch tooling drift~~ — recategorized as `external legacy
  reference`. The Agent-side scripts patch a different runtime (oMLX) and
  are **not an owlmlx extraction target**. owlmlx is an independent runtime;
  it neither retires those patches nor depends on them being retired.

Resolved drifts from earlier list:

- ~~runtime contracts still transported mainly through shell protocol docs~~ —
  owlmlx now serves its own HTTP surface (Stabilization-1, frozen
  `/v1/runtime/status`).
- ~~cache and quant truth still described primarily from shell-facing routes~~ —
  cache truth contract is owlmlx-owned and shell-proxied. Quant remains the
  open thread (see above).
- ~~large-weight path schema still anchored to specimen-specific shell docs~~ —
  resolved via `large-weight-runtime-path.md` consolidation.

## 7. Migration Criteria For Shell-Hosted Items

An item classified as `owned but still shell-hosted` may remain in that state
only temporarily. Each such item must eventually resolve to one of:

- `owned now` — implementation or transport has moved to owlmlx
- `owned, shell-proxied` — truth lives in owlmlx, shell proxies it
- `shell-only` — reclassified as not actually runtime-owned

### 7.1 When To Migrate

An `owned but still shell-hosted` item should be migrated when:

1. The corresponding owlmlx contract (schema, module, or test) is stable
2. The shell consumer can switch to referencing owlmlx truth instead of
   carrying its own copy
3. No active feature development depends on the shell-local version

### 7.2 When To Keep Shell-Hosted

An item may remain `owned but still shell-hosted` when:

1. The owlmlx contract it maps to is still `partial` or `experimental`
2. Migration would break active shell functionality with no fallback
3. The item is under active development and splitting mid-change is risky

### 7.3 Mandatory Review

All `owned but still shell-hosted` items must be reviewed at each major
owlmlx phase transition (e.g., Phase 1 → Phase 2) to determine if migration
conditions are now met.

## 8. Next Mapping Actions

Refreshed 2026-05-12 (Stage 3.1 c2):

1. ~~Quantization metadata contract~~ — **done** in Stage 3.1 c4
   (`owlmlx/quantization_metadata.py` + `GET /v1/runtime/quantization-metadata`).
   Shell consumers can now switch off private quant_method parsing.
2. ~~`swap-safe` patch tooling migration~~ — **withdrawn** in Stage 3.2
   Track A (2026-05-12). The Agent-side scripts patch a different
   runtime (oMLX) and are recategorized as `external legacy reference`,
   not an owlmlx extraction target. owlmlx owns the same runtime
   principles independently via `memory_pressure_contract` /
   `settle_barrier_event` / `abort_recovery`; the Agent scripts'
   retirement is oMLX's concern, not owlmlx's.
3. **Risky-execution prompt rewrites** — shell prompts and playbooks
   still cite oMLX patch paths; rewrite to reference
   `runtime-governance.md` / `hazardous-operations.md` /
   `settle_barrier_event` directly. Shell-side work, tracked here for
   completeness.
4. **Stage 4 prep** — the bench at `scripts/bench/eviction_soak.py` is
   scaffolded but unimplemented. When implemented, it will provide the
   first apples-to-apples evidence ledger entry between owlmlx, oMLX,
   and vMLX on the memory-discipline axis. oMLX and vMLX appear here as
   comparison reference runtimes, not as code-migration sources.
5. **Stage 3.2 next** — independence cleanup and owned capability target
   selection. Once Track A documentation lands, the next executor
   chooses the next *owlmlx-owned* capability to deepen (e.g., the
   Cache/Residency/Eviction loop addressed by Stage 3.3 Track B). No
   Agent-side migration item belongs on this list.
