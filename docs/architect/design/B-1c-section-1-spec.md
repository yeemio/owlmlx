# B-1c Section 1 · Design-Grade Spec

> **Gate**: Campaign B-1c section 1 · Session KV cache no-swap soak
> **Layer**: design-grade, downstream of `docs/architect/01-mainline-roadmap.md`
> **Status**: runner landed; real 24h native run pending
> **Capability label**: Session KV cache remains `experimental`

## 1. Purpose

B-1c section 1 verifies one narrow claim:

```text
With session KV cache enabled, a single loaded model can serve a mixed
short / medium / long session workload for at least 24h without artificial
unload or model swap, without active-memory drift, without FATAL watermark,
and without reclaim-barrier failures.
```

This is not the whole B-1c gate. Section 2, the 24h soak plus model-swap run,
remains separate and must not be merged with this result.

## 2. Scope

In scope:

- native backend no-swap soak with `OWLMLX_SESSION_CACHE_ENABLED=1`
- one model loaded once at the beginning of the soak
- one short / medium / long warmup cycle before measurement so initial cache
  entry creation is not misclassified as drift
- repeated `generate_stream` calls with explicit session ids
- short / medium / long prompt mix at 1:1:1 balance
- periodic `mlx.core.get_active_memory()` sampling
- runtime `reclaim_barrier_stats()` read-only observation
- final cleanup unload after the soak window

Out of scope:

- any model swap during the section 1 measurement window
- any artificial unload during the section 1 measurement window
- supported promotion for session KV cache
- subprocess cache-handle transport
- paged KV, implicit prefix matching, or continuous batching

## 3. Runner

Primary command shape:

```bash
uv run python scripts/bench/eviction_soak.py \
  --gate b1c1-no-swap-soak \
  --backend native \
  --model /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --model-label gemma-4-31B-it \
  --model-gb 60 \
  --duration-s 86400 \
  --required-duration-s 86400 \
  --sample-interval-s 60 \
  --warmup-cycles 1 \
  --max-tokens 2
```

Smoke/schema runs may use `--backend fake`, `--max-samples`, and
`--required-duration-s 0`, but those runs must never be described as a 24h
soak result.

## 4. Evidence

Expected output directory:

```text
files/evidence/owlmlx/bench/session-kv-soak/
```

Expected files:

```text
<timestamp>-b1c1-<model>-no-swap-soak.jsonl
<timestamp>-b1c1-<model>-no-swap-soak-rollup.jsonl
```

Per-sample records use `schema_version = "b1c1.v1"` and `gate =
"B-1c section 1"`.

Each record carries a `phase`:

- `warmup`: cache-entry establishment for the short / medium / long session
  mix. Warmup records remain in the ledger and may fail the run, but they are
  not the drift baseline.
- `measurement`: the actual soak window. `measurement_duration_s` and
  `drift_from_measurement_start_bytes` are computed from this phase only.
  Cleanup unload / settle time must not extend the measured soak duration.

Rollup conclusion field:

```yaml
no_swap_soak_stability: passed | failed | blocked
```

## 5. Pass Criteria

`no_swap_soak_stability = passed` requires all of:

- `duration_requirement_met = true`
- `claimable_24h_duration = true`: `required_duration_s >= 86400` and the
  measurement phase met that requirement
- `allocator_truth_claimable = true`: native backend with
  `measurement_mode = mlx_core_active_memory`
- `ledger_gap_free = true`
- `warmup_cycle_complete = true`: short / medium / long each appear at least
  once in the warmup phase
- measurement samples exist
- `session_mix_complete = true`: short / medium / long each appear at least
  once in the measurement phase
- `session_mix_balanced = true`: measurement prompt-count skew is at most one
- `max_drift_bytes <= min(200 MiB, 0.5% host serving budget)`
- `fatal_watermark_count = 0`
- `failure_measurement_count = 0`
- `unresolved_reclaim_barrier_events = 0`
- `session_cache_drops_total = 0`
- `session_cache_rejects_total = 0`
- every sample has `sample_verdict = passed`
- final cleanup unload succeeds

If the runner completes but the required duration is shorter than 24h, the
conclusion must be `blocked`, not `passed`.

Fake/schema runs and non-native measurement modes may validate ledger shape, but
must not graduate `no_swap_soak_stability` or unblock section 2.

## 5.1 Interruption-Tolerant Rehearsal

If a continuous 24h native run is operationally difficult, run an interrupted
rehearsal instead of weakening the pass criteria.

Recommended rehearsal shapes:

- `3 x 8h` native no-swap segments
- `6 x 4h` native no-swap segments
- shorter local smoke segments while tuning runner parameters

Rehearsal segments must keep separate ledgers and record:

```yaml
interrupted_no_swap_rehearsal:
  rehearsal_segment_id: <stable id>
  segment_duration_s: <measured native duration>
  interruption_reason: planned_stop | host_sleep | user_interrupt | failure | unknown
  resumes_prior_segment: true | false
  aggregate_measurement_duration_s: <sum of completed native segments>
  no_swap_soak_stability: blocked
```

Rehearsal evidence can support confidence statements such as
`interrupted_no_swap_rehearsal = passed`, but it must not:

- set `no_swap_soak_stability = passed`
- set `graduates.unblock_B_1c_section_2 = true`
- count as the B-1c §1 supported gate
- be merged into a single "24h continuous soak" claim

The uninterrupted 24h native run remains the only §1 graduation path. The
rehearsal path exists to make that run less blind, not to replace it.

## 6. Failure Semantics

| Condition | Verdict | Meaning |
|---|---|---|
| Short smoke / schema run | `blocked` | Useful for harness validation only |
| Native run shorter than 24h | `blocked` | Useful for rehearsal only |
| Generation, watermark, or reclaim failure during 24h | `failed` | Section 1 failed; preserve raw ledger |
| Generation, watermark, reclaim, cache drop/reject, or cleanup failure before 24h completes | `failed` | Hard failures are failures, not duration blocks |
| Final cleanup unload fails | `failed` | Soak cannot claim clean lifecycle |
| Section 1 passed but section 2 later fails | section 1 remains `passed` | Supported promotion still blocked |

## 7. Next Step

After one real native 24h section 1 run passes, update:

- `docs/architect/01-mainline-roadmap.md`
- `docs/architect/03-real-accomplishments.md`
- `docs/source-of-truth/runtime-capability-matrix.md`

Do not change session KV cache from `experimental` to `supported` until B-1c
section 2 also passes.
