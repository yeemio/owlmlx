# owlmlx B-1c2 Bounded-Context Trim Closure · 2026-05-25

## Goal Contract

```yaml
goal_id: owlmlx-b1c2-bounded-context-trim-closure
title: Close B-1c section 2 bounded-context session KV drop before aggregate rerun
success_definition:
  - B-1c section 2 focused Qwen-only no-swap probe reaches 720 samples
  - max_drift_bytes <= 209715200 under 3000-char prompt freeze
  - session_cache_drops_total == 0
  - session_cache_expirations_total == 0
  - session_cache_rejects_total == 0
  - no session_kv_supported or soak_plus_swap_stability promotion claim
blocked_definition:
  - the sample-371 bounded-context drop cannot be attributed to a concrete trim/finalization operation
  - or the concrete operation is external mlx-lm behavior that cannot be safely adapted in owlmlx
hard_rules:
  - keep Session KV cache experimental
  - do not resume 4h or 24h B-1c section 2 aggregate while the focused probe drops
  - do not use positive active-memory delta upper bound as a promotion gate
  - leave unrelated untracked files untouched
out_of_scope:
  - subprocess cache-handle transport
  - paged KV or implicit prefix matching
  - OwlCoda consumer readiness
current_truth:
  - B-1a, B-1b, and current-Mac B-1c section 1 prerequisite are satisfied
  - 20260524T113306Z reproduced 352MB drift without swap
  - 20260525T040839Z showed positive-delta accounting explains drift only as diagnostic upper bound
  - 20260525T042215Z cache-only 1024-token window had zero drops but still drifted 293MB
  - 20260525T045707Z 3000-char prompt freeze held drift to 150MB but dropped once at sample 371
remaining_gaps:
  - bounded-context cache finalization drop reason is not specific enough
  - focused 720-sample 3000-char probe is not clean
dominant_next_gap:
  - instrument and fix bounded-context trim/finalization so the 3000-char focused probe is clean
```

## Next Round Prompt

Continue from `/Users/yeemio/AI/gitrep/owlmlx` on `main`.

1. Inspect `MlxNativeBackend._prepare_prompt_cache_for_stream()` and
   `_finalize_session_prompt_cache_after_stream()` around session cache reuse,
   exact-prompt hits, `_trim_prompt_cache`, and `drop_for_session_model()`.
2. Add a narrow runtime-owned diagnostic for session KV cache drops:
   distinguish reuse-trim mismatch, completion-trim mismatch, exact-hit empty
   suffix behavior, and prompt-window policy events. Expose the reason in
   `SessionKVCacheStore.status_dict()` and B-1c section 2 ledger records.
3. Fix only the bounded-context path if the diagnosis is owlmlx-owned. Do not
   mask drops by reclassifying them as pass conditions.
4. Re-run targeted tests:
   `uv run pytest tests/test_eviction_soak_bench.py tests/test_session_kv_soak_audit.py tests/test_session_kv_cache.py tests/test_mlx_native_backend_session_kv_cache.py -q`
5. Re-run the focused native probe:
   `--gate b1c2-soak-plus-swap`, Qwen3.6-27B-only, `--max-samples 720`,
   `--b1c2-prompt-growth-max-chars 3000`, `--swap-count 0`.
6. Update `docs/architect/design/B-1c-section-2-spec.md`,
   `docs/architect/03-real-accomplishments.md`,
   `docs/source-of-truth/master-outline.md`, and
   `docs/source-of-truth/runtime-capability-matrix.md` honestly.
7. Commit only relevant B-1c bounded-context files and evidence. Leave
   `docs/architect/04-architecture-canvas.html`,
   `docs/source-of-truth/ds4-mtp-local-llm-stack-research.zh-20260514.md`, and
   `软件著作权申请资料/` untouched.
