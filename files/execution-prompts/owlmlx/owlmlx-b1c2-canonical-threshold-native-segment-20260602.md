# Execution Prompt: B-1c §2 Canonical Threshold Native Segment

> Created: 2026-06-02
> Goal: `owlmlx-runtime-acceleration-substrate-b1c2-b2`
> Dominant gap: promote the short threshold-native B-1c §2 path from a
> 3-swap smoke into a count-canonical 24-swap evidence candidate without
> weakening capability labels.

## Current Verified Truth

- The `20260602T095334Z` native threshold smoke passed all four configured
  axes at 3 swaps:
  - load stability passed
  - throughput stability passed with 18 usable throughput samples
  - switch stability passed
  - concurrency/breadth passed with 6 prompt entries
- That smoke is not graduation evidence because
  `canonical_gate.canonical_switch_requirement_met=false` and
  `graduates.soak_plus_swap_stability=false`.
- Session KV cache and no-header prefix cache remain `experimental`.
- Two operator-paused fast-count attempts (`20260602T095953Z` and
  `20260602T100243Z`) produced partial ledgers without rollups. They are not
  acceptable pass evidence.
- The B-1c §2 runner now has SIGINT/SIGTERM handling matching the B-1c §1
  pattern: interrupted runs write a blocked segment rollup, preserve cleanup
  evidence, and keep all graduation flags false.

## Objective

Run a count-canonical B-1c §2 native segment that keeps the four-axis threshold
configuration from the short smoke, raises `swap_count` and
`required_swap_count` to 24, and requires cache eviction pressure.

This round is allowed to use fast count cadence (`duration_s=0`) so it can close
inside an execution turn. It must not be described as 5-minute-cadence or 2-hour
evidence.

## Command

```bash
uv run python scripts/bench/eviction_soak.py \
  --gate b1c2-soak-plus-swap \
  --runtime owlmlx \
  --backend native \
  --model-a /Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit \
  --model-a-gb 27 \
  --model /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --model-gb 31 \
  --model-b /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B \
  --model-b-gb 35 \
  --rotation-label qwen-gemma-qwen35-canonical-threshold-fast-count \
  --b1c1-prerequisite-satisfied \
  --duration-s 0 \
  --required-duration-s 0 \
  --sample-interval-s 0 \
  --swap-count 24 \
  --required-swap-count 24 \
  --max-tokens 1 \
  --b1c2-prompt-growth-max-chars 3000 \
  --b1c2-cache-breadth-entry-count 6 \
  --b1c2-throughput-decay-max-relative 0.30 \
  --b1c2-throughput-min-samples 6 \
  --b1c2-concurrency-min-entry-breadth 6 \
  --b1c2-concurrency-require-cache-eviction
```

## Offline Preflight

Preflight checked during the 2026-06-02 goal continuation while MLX was still
occupied by a separate `mlx_lm lora -c lora_config.yaml` process:

- all three model directories exist:
  - `/Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit`
  - `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
  - `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`
- `scripts/bench/eviction_soak.py --help` exposes all required canonical flags,
  including `--required-swap-count`,
  `--b1c2-throughput-decay-max-relative`,
  `--b1c2-concurrency-min-entry-breadth`, and
  `--b1c2-concurrency-require-cache-eviction`.
- The runner sets `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES` internally to the
  reviewed B-1c §2 resident working-set budget, so the eviction requirement is
  backed by resident-cap pressure during the 24-swap run.
- `scripts/bench/session_kv_soak_audit.py --help` exposes
  `--require-canonical`, `--require-cache-eviction`, and `--require-rollup`.
- `python3 -m py_compile scripts/bench/eviction_soak.py
  scripts/bench/session_kv_soak_audit.py scripts/bench/prefix_cache_compatibility.py`
  passed.
- `uv run pytest tests/test_eviction_soak_bench.py
  tests/test_session_kv_soak_audit.py
  tests/test_prefix_cache_compatibility_bench.py -q` passed with `78 passed`.
- `tests/test_eviction_soak_bench.py` includes a no-MLX regression proving
  `--b1c2-concurrency-require-cache-eviction` keeps concurrency `blocked` when
  no eviction counter is observed and passes only when an eviction is recorded.
- `tests/test_session_kv_soak_audit.py` includes a no-MLX regression proving
  `--require-cache-eviction` rejects canonical rollups that pass count gates but
  lack explicit cache-eviction requirement/observation fields.

## Acceptance Criteria

- Rollup exists under `files/evidence/owlmlx/bench/session-kv-soak/`.
- If the run is interrupted, a blocked rollup still exists and
  `interrupted_soak_plus_swap.interrupted=true`.
- `canonical_gate.required_swap_count=24`.
- `canonical_gate.observed_swap_count=24`.
- `canonical_gate.canonical_switch_requirement_met=true`.
- All four axis verdicts pass.
- `session_cache_drops_total=0`, `session_cache_expirations_total=0`, and
  `session_cache_rejects_total=0`.
- `axis_verdicts.concurrency_stability.cache_eviction_observed=true`.
- `graduates.session_kv_supported=false` remains unchanged.

Post-run audit should use both canonical and eviction-pressure guards:

```bash
uv run python scripts/bench/session_kv_soak_audit.py \
  --segment-rollup <rollup-path> \
  --require-canonical \
  --require-cache-eviction
```

## Honest Claim Ceiling

If this passes, it is count-canonical fast-cadence B-1c §2 evidence. It does
not prove the recommended 5-minute-cadence / 2-hour canonical run and does not
promote session KV or B-2 no-header prefix cache to `supported`.
