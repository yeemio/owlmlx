# owlmlx B-1c2 Measurement-Continuity Segment · 2026-06-01

## Goal Contract

```yaml
goal_id: owlmlx-b1c2-measurement-continuity-segment-20260601
title: Produce one gap-free B-1c section 2 prompt-reset swap-bearing segment
success_definition:
  - one native B-1c section 2 prompt-reset swap-bearing segment completes
  - measurement_wall_clock_gap_free == true
  - ledger_gap_free == true
  - session_cache_drops_total == 0
  - session_cache_expirations_total == 0
  - session_cache_rejects_total == 0
  - max_drift_bytes <= 209715200
  - swap_boundaries_clean == true
  - fatal_watermark_count == 0
  - unresolved_reclaim_barrier_events == 0
blocked_definition:
  - host sleep, lid close, power state, or manual interruption creates an in-segment wall-clock gap
  - any required model path is unavailable
  - the run remains clean but only produces a short blocked segment; repeat segments are still required for 24h / 6 swaps
hard_rules:
  - keep Session KV cache experimental
  - do not relax the wall-clock gap-free requirement
  - do not claim soak_plus_swap_stability=passed from a single 4h / 1-swap segment
  - do not claim session_kv_supported=true
  - do not edit session_kv_cache.py unless the repeat exposes a new runtime failure
  - leave unrelated dirty/untracked files untouched
current_truth:
  - B-1a passed
  - B-1b passed
  - current-Mac B-1c section 1 prerequisite passed via interrupted no-swap aggregate
  - B-1c section 2 prompt-reset one-swap functional subcriteria are clean
  - latest segment 20260525T061019Z is blocked only because measurement_wall_clock_gap_free=false
dominant_next_gap:
  - measurement continuity on a shared Mac
```

## Execution Round

Run one 4h native segment using the same prompt-reset policy as
`20260525T061019Z`. The segment may still end `blocked` because `duration_s`
and `swap_count` are short of the full §2 aggregate requirement, but it must be
internally gap-free to become valid interrupted-aggregate input.

Canonical command shape:

```zsh
cd /Users/yeemio/AI/gitrep/owlmlx
export OWLMLX_SESSION_CACHE_ENABLED=1
caffeinate -dis uv run python scripts/bench/eviction_soak.py \
  --gate b1c2-soak-plus-swap \
  --runtime owlmlx \
  --backend native \
  --model-a /Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit \
  --model-a-gb 16 \
  --model /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --model-gb 60 \
  --model-b /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit \
  --model-b-gb 20 \
  --rotation-label qwen-gemma-qwen35-prompt-reset-3000-4h \
  --duration-s 14400 \
  --required-duration-s 86400 \
  --swap-count 1 \
  --required-swap-count 6 \
  --sample-interval-s 60 \
  --max-tokens 1 \
  --profile-memory-gb 128 \
  --b1c1-prerequisite-satisfied \
  --b1c2-prompt-growth-max-chars 3000 \
  --session-id-prefix b1c2-prompt-reset-swap-3000
```

## Monitoring

Avoid tmux inspection. Use process and files:

```zsh
pgrep -af 'eviction_soak.py.*b1c2-soak-plus-swap'
pgrep -af 'caffeinate -dis'
ls -t files/evidence/owlmlx/bench/session-kv-soak/*prompt-reset-3000-4h-soak-swap.jsonl | head -1
wc -l files/evidence/owlmlx/bench/session-kv-soak/<ledger>.jsonl
tail -n 1 files/evidence/owlmlx/bench/session-kv-soak/<ledger>.jsonl
```

On completion, audit:

```zsh
uv run python scripts/bench/session_kv_soak_audit.py \
  --ledger files/evidence/owlmlx/bench/session-kv-soak/<timestamp>-b1c2-qwen-gemma-qwen35-prompt-reset-3000-4h-soak-swap.jsonl \
  --segment-rollup files/evidence/owlmlx/bench/session-kv-soak/<timestamp>-b1c2-qwen-gemma-qwen35-prompt-reset-3000-4h-soak-swap-rollup.jsonl \
  --json
```

## Host Discipline

- AC power.
- Lid open.
- Do not manually sleep the host.
- Keep the machine unused during the segment if possible.
- `caffeinate -dis` is required on the current macOS host (`caffeinate -h`
  exposes `[-disu]`, not `-m`). If the runner is started first, attach with
  `caffeinate -dis -w <python_pid>`; prior `tmux + caffeinate -i` did not
  prevent the wall-clock gap.

## Change Log

| Date | Change | By |
|---|---|---|
| 2026-06-01 | Created gap-free B-1c §2 measurement-continuity round after source-of-truth selector cleanup and three read-only subagent audits agreed on the same next executable segment. | Codex |
