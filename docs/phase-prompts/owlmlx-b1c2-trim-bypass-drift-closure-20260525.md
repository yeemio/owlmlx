# owlmlx B-1c2 Trim-Bypass Drift Closure · 2026-05-25

## Goal Contract

```yaml
goal_id: owlmlx-b1c2-trim-bypass-drift-closure
title: Close B-1c section 2 drift after safe trim-unavailable bypass
success_definition:
  - focused Qwen-only no-swap probe reaches 720 samples
  - max_drift_bytes <= 209715200
  - session_cache_drops_total == 0
  - session_cache_expirations_total == 0
  - session_cache_rejects_total == 0
  - trim-bypass behavior is either rare enough to stay within budget or replaced by a token-stable policy
blocked_definition:
  - trim bypass remains frequent enough to force repeated fresh-cache fallback and active-memory drift > 200 MiB
  - or a lower-level MLX working-set metric is required before the promotion gate can be judged
hard_rules:
  - keep Session KV cache experimental
  - do not resume B-1c section 2 4h or 24h aggregate while focused probe drift is over budget
  - do not treat positive active-memory delta upper bound as a promotion gate
  - leave unrelated untracked files untouched
current_truth:
  - 20260525T051225Z proved sample 371 was reuse_trim_mismatch: requested trim 2, upstream trimmed 0
  - 20260525T051719Z changed that path to safe trim bypass and ran 720 samples with drops/expirations/rejects all 0
  - the same run recorded 173 trim bypasses and max_drift_bytes=293076992, so it still failed the memory budget
dominant_next_gap:
  - reduce or avoid trim-unavailable fresh-cache fallback under bounded prompt growth
```

## Next Round Prompt

Continue from `/Users/yeemio/AI/gitrep/owlmlx` on `main`.

1. Inspect the 3000-char prompt-freeze path and the drop-reason ledger samples.
2. Choose one narrow mitigation:
   - token-stable prompt/window policy that avoids repeated 2-token reuse trims;
   - bounded cache reset policy that prevents fresh-cache high-watermark growth;
   - or precise working-set accounting if active-memory drift is no longer the right gate.
3. Do not downgrade drift failures to pass. A focused probe must keep
   `max_drift_bytes <= 209715200`.
4. Re-run targeted tests:
   `uv run pytest tests/test_eviction_soak_bench.py tests/test_session_kv_soak_audit.py tests/test_session_kv_cache.py tests/test_mlx_native_backend_session_kv_cache.py -q`
5. Re-run the focused native probe only after a code or policy change:
   `--gate b1c2-soak-plus-swap`, Qwen3.6-27B-only, `--max-samples 720`,
   `--b1c2-prompt-growth-max-chars 3000`, `--swap-count 0`.
6. Update B-1c docs and evidence honestly. No `supported` claim until all
   promotion gates pass together.
