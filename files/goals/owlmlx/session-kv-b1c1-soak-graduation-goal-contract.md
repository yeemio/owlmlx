# Goal Contract: Session KV B-1c Soak Graduation

> Status: active goal contract
> Created: 2026-05-17
> Loop driver: `goal-driven-project-loop`

## Goal ID

`owlmlx-session-kv-b1c1-soak-graduation`

## Title

Close the Session KV B-1c section 1 no-swap soak gate without weakening the
24h native requirement.

## Success Definition

This goal succeeds when B-1c section 1 has:

1. a real native no-swap soak ledger with `required_duration_s >= 86400`,
2. `measurement_mode=mlx_core_active_memory`,
3. mixed short / medium / long sessions with gap-free samples,
4. drift within `min(200 MiB, 0.5% host serving budget)`,
5. no FATAL watermark, cache drop/reject, failed reclaim, or cleanup failure,
6. `no_swap_soak_stability=passed`,
7. docs updated without changing Session KV from `experimental` to `supported`.

## Blocked Definition

The goal is blocked only if:

- the native model artifact is unavailable,
- native MLX allocator truth is unavailable,
- the host cannot remain available long enough for a continuous 24h run, or
- repeated interrupted rehearsal exposes a hard failure that must be fixed
  before the full run.

## Hard Rules

- Do not treat interrupted rehearsal as the supported gate.
- Do not merge segments into a fake "24h continuous soak" claim.
- Do not start B-1c section 2 until section 1 truly passes.
- Do not change Session KV cache from `experimental` until section 1 and
  section 2 both pass.
- Keep evidence under `files/evidence/owlmlx/bench/session-kv-soak/`.

## Out Of Scope

- B-1c section 2 soak plus swap.
- Subprocess session cache transport.
- Paged KV, implicit prefix matching, or continuous batching.
- DeepSeek D1-D4 experimental lane.

## Current Truth

- B-1a passed for Qwen3.6 and Gemma 4 second-model evidence.
- B-1b passed native cache-on no-regress N=20.
- B-1c section 1 runner exists and fake/schema smoke remains blocked.
- The 24h native no-swap evidence is still missing.
- Continuous 24h host availability is operationally fragile, so an
  interruption-tolerant rehearsal path is useful but not sufficient.

## Remaining Gaps

1. Record segment metadata for interrupted rehearsal runs.
2. Aggregate multiple segment rollups into one rehearsal report.
3. Keep `no_swap_soak_stability=blocked` for rehearsal evidence.
4. Run the real native 24h section 1 gate when host time is available.

## Dominant Next Gap

`B-1c section 1 interrupted rehearsal aggregation`

The dominant gap is not model performance. It is making interrupted native
soak preparation auditable while preserving the strict 24h graduation rule.
