# Execution Prompt: B-2 Post-B-1c Route-Level Policy Closure

> Created: 2026-06-03
> Goal: `owlmlx-runtime-acceleration-substrate-b1c2-b2`
> Dominant gap: turn the accepted B-1c §2 fast-count evidence into the correct
> B-2 no-header prefix-cache policy posture without over-promoting the
> capability.

## Current Verified Truth

- B-1c §2 canonical fast-count evidence is accepted:
  `20260603T031832Z` passed 24/24 swaps, all four axes, and cache-eviction
  pressure. `session_kv_soak_audit.py --require-canonical
  --require-cache-eviction` reports `canonical_acceptance_status=canonical_passed`.
- This is count-based fast-cadence evidence, not continuous 24h evidence.
- Session KV cache and no-header automatic prefix cache remain `experimental`.
- B-2.3 already has a narrow default-off no-header automatic prefix slice behind
  `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`.
- Existing real-model route evidence covers no-header OpenAI SSE and Anthropic
  SSE cached/read token metadata on Qwen27, Qwen35, and Gemma31.

## Objective

Close the B-2 post-B-1c policy/evidence gap:

1. Re-run offline B-2 audits for the existing no-header native-streaming and
   compat-route ledgers.
2. Confirm the claim ceiling: narrow, opt-in, native-streaming, default-off,
   route-level evidence only.
3. Refresh B-2 source-of-truth so it no longer says B-1c §2 canonical evidence
   is missing.
4. Keep automatic prefix cache `experimental`; do not claim default-on, cross-
   user reuse, subprocess cache transport, paged KV, continuous batching, or
   `supported`.

## Verification Commands

```bash
uv run python scripts/bench/prefix_cache_compatibility.py audit-auto-prefix-ledger \
  --ledger files/evidence/owlmlx/bench/prefix-cache-compatibility/20260602T011000Z-b2-auto-prefix-qwen27-real-hit.jsonl

uv run python scripts/bench/prefix_cache_compatibility.py audit-compat-route-ledger \
  --ledger files/evidence/owlmlx/bench/prefix-cache-compatibility/20260602T015245Z-b2-compat-route-qwen27-real-hit.jsonl \
  --ledger files/evidence/owlmlx/bench/prefix-cache-compatibility/20260602T015559Z-b2-compat-route-qwen35-real-hit.jsonl \
  --ledger files/evidence/owlmlx/bench/prefix-cache-compatibility/20260602T015559Z-b2-compat-route-gemma31-real-hit.jsonl

uv run pytest tests/test_prefix_cache_compatibility_bench.py \
  tests/test_runtime_session_kv_cache_route.py \
  tests/test_session_kv_soak_audit.py -q

git diff --check
```

## Acceptance Criteria

- Offline B-2 audits return 0 for the Qwen27 auto-prefix hit ledger and the
  Qwen27/Qwen35/Gemma31 compat-route ledgers.
- Source-of-truth docs describe B-1c §2 as accepted fast-count evidence and B-2
  as the next policy/route-level closure.
- Capability labels remain honest: Session KV and automatic prefix cache stay
  `experimental`.
- No new `owlmlx/` Python module is added for spec-only text.
