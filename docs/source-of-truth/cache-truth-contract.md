# Cache Truth Contract

> Status: authoritative
> Updated: 2026-04-11
> Round: R18 / Gap 5
> Implementation: `owlmlx/cache_truth.py`

## 1. Purpose

This document freezes the cache truth that `owlmlx` owns.

The original platform had useful cache behavior in
`llm_router/distilled_cache_substrate.py`, but that module mixed four layers:

- generic cache profile semantics
- oMLX runtime flag schema
- Distilled-27B experiment assets
- platform mutation and process inspection

R18 absorbs only the generic runtime truth. Platform-specific mutation,
probing, and specimen facts stay in the platform.

## 2. What owlmlx Owns

`owlmlx/cache_truth.py` owns:

| Truth | Status |
|---|---|
| Cache profile labels | `baseline`, `cache-enabled`, `not_running`, `unknown` |
| oMLX cache env key schema | `OMLX_CACHE_DIR`, `OMLX_CACHE_MAX_SIZE`, `OMLX_HOT_CACHE_SIZE` |
| oMLX cache CLI flag schema | `--paged-ssd-cache-dir`, `--paged-ssd-cache-max-size`, `--hot-cache-max-size` |
| Cache flag normalization | env-shape, platform-shape, and direct dataclass input |
| Configured profile derivation | cache flags → `baseline` / `cache-enabled` |
| Restart-required derivation | configured profile vs runtime profile |
| TurboQuant cache safety | default hard no-activation unless cache keys and invalidation are verified safe |

These are runtime semantics. They are not tied to one model line.

## 3. What owlmlx Does Not Own

`owlmlx` does not own:

| Area | Owner |
|---|---|
| Reading or rewriting `scripts/llm.env` | platform |
| Backing up or rolling back env files | platform |
| Running `lsof`, `ps`, HTTP probes, or subprocess inspection | platform |
| Loading Phase 39 ladder assets | platform / verification residue |
| Distilled-27B model identity | platform model-line placement |
| Cache profile switch endpoint transport | router / platform |
| Cache clearing implementation | runtime host / platform |
| TurboQuant enable endpoint | oMLX / platform |

The boundary is: `owlmlx` answers what the cache state means; the platform
discovers, applies, and displays it.

## 4. Profile Semantics

### `baseline`

No cache flags are active. Runtime should serve without paged SSD cache or hot
cache settings.

### `cache-enabled`

At least one cache flag is active:

- paged SSD cache dir
- paged SSD cache max size
- hot cache max size

Any one of these is sufficient to classify the configured profile as
`cache-enabled`.

### `not_running`

The runtime process is not active. Restart-required must be `false` because
there is no running process to restart for the current config to take effect.

### `unknown`

The platform cannot determine runtime cache state. Restart-required must be
`false` because forcing restart from unknown state is a policy action, not a
truth derivation.

## 5. Restart Rule

`cache_restart_required(configured_profile, runtime_profile)` returns `true`
only when:

1. runtime profile is known and running, and
2. runtime profile differs from configured profile.

It returns `false` for:

- matching profiles
- `not_running`
- `unknown`

This mirrors the platform behavior that was previously embedded in
`distilled_cache_substrate.py`.

## 6. TurboQuant Cache Safety Rule

Runtime KV quantization may only auto-activate when all of the following are
true:

1. runtime is verified for the current model architecture
2. quantization bits are part of the cache key
3. cache invalidates on quantization config toggle

If any condition is false, `turboquant_cache_safety()` returns:

- `can_activate = false`
- `cache_safety_risk = HIGH — no bits-in-cache-key, no invalidation on config toggle`
- required safe-adoption actions:
  - clear SSD + hot cache before any TurboQuant config change
  - unload + reload model after settings change
  - never mix bit-widths on same model without full cache clear

This captures the safe posture learned from the local oMLX TurboQuant tests
without promoting TurboQuant to supported.

## 7. Platform Consumption

The platform consumes R18 in two places:

| Platform file | Consumption |
|---|---|
| `llm_router/distilled_cache_substrate.py` | imports cache env keys, flag extraction, configured profile derivation, active flag shape, and restart-required derivation |
| `llm_router/primary_line_status.py` | imports TurboQuant cache-safety derivation |

The platform still owns runtime probing, env mutation, endpoint transport, and
Distilled-specific experiment summaries.

## 8. Validation

R18 validation requires:

- owlmlx tests for pure cache truth
- platform tests for cache-substrate summary behavior
- platform tests for primary-line TurboQuant safety surface
- no platform imports from `owlmlx/cache_truth.py`

Current implementation has 22 owlmlx cache-truth tests and platform-focused
tests in `test_distilled_cache_substrate.py` and `test_primary_line_status.py`.
