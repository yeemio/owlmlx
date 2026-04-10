# owlmlx Contract Mapping

> Status: working mapping
> Updated: 2026-04-10

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

| Current shell truth | owlmlx contract target | Category | Notes |
|---|---|---|---|
| oMLX runtime status route | `core runtime status` | `owned but still shell-hosted` | Semantics belong to runtime truth even if transport remains in shell |
| Per-model memory & load state | `core runtime status` | `owned but still shell-hosted` | Runtime fact, not merely dashboard state |
| Cache tier truth | `core runtime status` | `owned but still shell-hosted` | Cache truth belongs to runtime semantics |
| Quantization metadata truth | `core runtime status` | `owned but still shell-hosted` | Runtime identity and memory-fit semantics |
| Snapshot composition | none | `shell-only` | Snapshot embedding is a shell integration concern |

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

The biggest current drifts are:

- runtime contracts still transported mainly through shell protocol docs
- cache and quant truth still described primarily from shell-facing routes
- large-weight path schema still anchored to specimen-specific shell docs
- governance truth now exists in `owlmlx`, but shell prompts have not yet been
  fully rewritten to reference it first

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

1. move shell-facing runtime protocol sections to reference `owlmlx`
2. align runtime contract tests with `owlmlx` schema language
3. separate path-level runtime truth from specimen-only shell narratives
4. update risky execution prompts to cite `runtime-governance.md`
