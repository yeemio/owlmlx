# B-1c Section 2 · Design-Grade Spec

> **Gate**: Campaign B-1c section 2 · Session KV cache soak plus model swap
> **Layer**: design-grade, downstream of `docs/architect/01-mainline-roadmap.md`
> **Status**: design-grade spec + fake/schema runner landed; native §2 runner landed; first native smoke failed on Qwen3.6-27B-4bit session-cache drop/drift and blocks long §2 segments until triaged
> **Capability label**: Session KV cache remains `experimental`

## 1. Purpose

B-1c section 2 verifies the second long-stability claim:

```text
With session KV cache enabled, owlmlx can survive repeated model switch cycles
under a mixed short / medium / long session workload without reclaim-barrier
failures, FATAL watermark, hidden cache drops, or active-memory drift.
```

This is separate from B-1c §1. Section 1 proves no-swap session-cache soak
stability. Section 2 adds model unload / load / settle boundaries. A clean §2
result must not be used to hide a missing or failed §1 result.

## 2. Prerequisites

Do not run section 2 until one of these is true:

- current Mac route: B-1c §1 has `interrupted_no_swap_rehearsal = passed` with
  cumulative clean native segments >= 24h
- stronger dedicated-host route: B-1c §1 has `no_swap_soak_stability = passed`

The current Mac / laptop route is expected to be operator-interruptible. Section
2 should follow the same principle: explicit segment boundaries are allowed;
hidden wall-clock gaps inside a segment are not.

## 3. Scope

In scope:

- native backend only
- `OWLMLX_SESSION_CACHE_ENABLED=1`
- mixed short / medium / long session workload at 1:1:1 balance inside each
  segment
- explicit unload / settle / load boundaries between models
- read-only reclaim-barrier stats after each swap
- wall-clock continuity checks inside each segment
- final cleanup unload and settle

Out of scope:

- subprocess cache-handle transport
- paged KV, implicit prefix matching, or continuous batching
- changing the §1 verdict
- public `supported` promotion by §2 alone
- OwlCoda / OwlOps consumer behavior

## 4. Model Rotation

Canonical rotation:

```text
Qwen3.6-27B -> Gemma 4-31B-it -> Qwen3.6-35B-A3B -> Qwen3.6-27B
```

The initial implementation may parameterize paths and labels, but the evidence
must preserve stable labels in the rollup:

```yaml
models:
  - qwen3.6-27b
  - gemma-4-31B-it
  - qwen3.6-35b-a3b
```

If one model is unavailable, the run must be `blocked`, not silently downgraded
to a two-model swap ladder.

## 5. Segment Shape

Original D3 shape was one continuous 24h run with six swaps every four hours.
On the current Mac route, use operator-interruptible segments instead:

- target aggregate duration: >= 24h
- target aggregate swap count: >= 6
- recommended shape: `6 x 4h`, each segment contains one planned swap boundary
- acceptable shape: fewer longer segments, if each segment remains wall-clock
  continuous and records the exact swap boundaries

Each segment starts from a clean process state and writes a separate ledger and
rollup. Segment rollups are then aggregated into the §2 conclusion. Do not
merge ledgers by hand.

## 6. Evidence

Expected output directory:

```text
files/evidence/owlmlx/bench/session-kv-soak/
```

Recommended file naming:

```text
<timestamp>-b1c2-<rotation-label>-soak-swap.jsonl
<timestamp>-b1c2-<rotation-label>-soak-swap-rollup.jsonl
<timestamp>-b1c2-interrupted-soak-swap-rollup.jsonl
```

Per-sample records should use:

```yaml
schema_version: b1c2.v1
gate: B-1c section 2
mode: soak_plus_swap
phase: warmup | measurement | swap
```

Per-swap records must include:

```yaml
swap:
  index: <int>
  from_model: <label>
  to_model: <label>
  unload_ok: true | false
  settle_barrier_state: clean | failed_unload | failed_reclaim | unknown
  load_ok: true | false
  active_memory_before_unload_bytes: <int | null>
  active_memory_after_settle_bytes: <int | null>
  expected_minus_observed_active_bytes: <int | null>
```

Segment rollups must include:

```yaml
soak_plus_swap_stability: passed | failed | blocked
measurement_duration_s: <float>
swap_count: <int>
measurement_wall_clock_gap_free: true | false
ledger_gap_free: true | false
max_drift_bytes: <int | null>
fatal_watermark_count: <int>
failure_measurement_count: <int>
unresolved_reclaim_barrier_events: <int>
session_cache_drops_total: <int>
session_cache_expirations_total: <int>
session_cache_rejects_total: <int>
cleanup_unload_result: <object>
cleanup_settle: <object>
```

Aggregate rollups must keep §1 and §2 separate:

```yaml
interrupted_soak_plus_swap:
  aggregate_measurement_duration_s: <float>
  aggregate_swap_count: <int>
  segment_count: <int>
  all_segments_ok_for_rehearsal: true | false
soak_plus_swap_stability: passed | failed | blocked
graduates:
  soak_plus_swap_stability: true | false
  session_kv_supported: false
```

`session_kv_supported` remains false in this runner. Promotion is a separate
source-of-truth update after B-1a, B-1b, B-1c §1, and B-1c §2 are all reviewed.

## 7. Pass Criteria

`soak_plus_swap_stability = passed` requires all of:

- B-1c §1 prerequisite is already satisfied
- native backend with `measurement_mode = mlx_core_active_memory`
- aggregate measurement duration >= 24h
- aggregate swap count >= 6
- every segment has `measurement_wall_clock_gap_free = true`
- every segment has `ledger_gap_free = true`
- short / medium / long session mix appears in every segment
- `max_drift_bytes <= min(200 MiB, 0.5% host serving budget)`
- every unload succeeds
- every settle barrier reports clean
- every load succeeds
- `fatal_watermark_count = 0`
- `failure_measurement_count = 0`
- `unresolved_reclaim_barrier_events = 0`
- `session_cache_drops_total = 0`
- `session_cache_expirations_total = 0`
- `session_cache_rejects_total = 0`
- final cleanup unload succeeds

If total duration or swap count is short but all samples are clean, the result
is `blocked`, not `passed`.

If any generation, unload, settle, load, watermark, reclaim, cache, or cleanup
condition fails, the result is `failed`.

## 8. Failure Semantics

| Condition | Verdict | Meaning |
|---|---|---|
| §1 prerequisite missing | `blocked` | Do not run or aggregate §2 as promotion evidence |
| Segment shorter than target but clean | `blocked` | Useful segment only |
| Segment has host sleep / power gap | `blocked` | Operational interruption inside segment; not hard runtime failure |
| Aggregate duration < 24h | `blocked` | More clean segments required |
| Aggregate swap count < 6 | `blocked` | More clean swap boundaries required |
| Unload / settle / load failure | `failed` | Swap boundary failed |
| FATAL watermark | `failed` | Memory discipline failed |
| Reclaim-barrier unresolved failure | `failed` | Reclaim discipline failed |
| Session cache drop / expiration / reject during measurement | `failed` | Session cache stability failed |

## 9. Runner Implementation Notes

Preferred implementation path:

```text
scripts/bench/eviction_soak.py
  --gate b1c2-soak-plus-swap
  --gate b1c2-interrupted-soak-plus-swap
```

The first code-grade slice landed as a **fake/backend schema runner**. It
validates the ledger shape, swap phase records, blocked rollup semantics, and
the §1 prerequisite guard. It does not use native allocator truth and does not
make §2 native-run evidence.

The native execution slice now admits `--backend native` only when both of
these are true:

- `--b1c1-prerequisite-satisfied` is explicit
- all three rotation model paths are explicit (`--model-a`, `--model`,
  `--model-b`)

The first native smoke after the current-Mac §1 prerequisite was:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260521T074758Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

It proved native load/generate/unload/settle/load plumbing reaches allocator
truth, but the rollup correctly concluded `failed`:

- `allocator_truth_claimable=true`
- `measurement_mode=mlx_core_active_memory`
- `swap_boundaries_clean=true`
- `session_cache_drops_total=3`
- `max_drift_bytes=343408640` > `drift_budget_bytes=209715200`

Do not start 4h/24h §2 native segments until the Qwen3.6-27B-4bit session-cache
drop/drift cause is triaged or the rotation is explicitly changed by decision.

Do not create new `*_harness.py`, `*_ledger.py`, `*_evidence.py`, or
`*_contract.py` modules for this work. Keep the bench runner in `scripts/bench/`
and put durable claims in markdown or JSONL evidence.

The landed smoke-only slice covers:

- fake backend schema run
- one swap boundary
- blocked rollup if duration or swap count is short
- no session KV promotion claim

Only after schema tests pass should native execution be attempted.

## 10. Next Step

Triage the failed native smoke before attempting operator-interruptible §2
aggregate evidence:

1. Determine whether the Qwen3.6-27B-4bit drop path is an expected
   model-specific `trim_prompt_cache` limitation or a fixable generated-token /
   prompt-cache finalization bug.
2. Re-run the short native smoke after the fix or explicit rotation decision.
3. Only then start 4h operator-interruptible §2 segments toward the 24h / 6-swap
   aggregate.
