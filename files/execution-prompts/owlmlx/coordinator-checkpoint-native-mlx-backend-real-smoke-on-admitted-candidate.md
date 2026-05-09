# owlmlx Coordinator Checkpoint — Native MLX Backend Real Smoke on Admitted Candidate (B-1.2)

## Verdict

- `native_mlx_backend_real_adapter_lifecycle_evidence_collected_on_admitted_candidate`

The native adapter (`MlxNativeBackend`) drove `load → stream_generate →
unload` end-to-end against the admitted Qwen3.6-35B-A3B candidate, and
two real concurrent streams serialized through the adapter's ticketed
admission. **Both env-gated tests passed (2 passed, 44 s)**. No `§3`
row state changes in this round; B-1.3 is the round that walks §1a
Promotion Gate.

## What This Checkpoint Is

The redirected main line's sixth round and the **first round with
declared-provenance evidence flowing through the adapter on a real
model**. Prior rounds' adapter evidence was either fake-injected
(`tests/test_mlx_native_backend.py`,
`tests/test_mlx_native_backend_post_claim_invariants.py`) or
upstream-binding-only (`tests/test_mlx_native_backend_real_upstream_binding.py`).
B-1.2 runs the adapter on a real candidate, lifting the structural cap
B-1.1 declared.

## Resource Pre-Check (Step 1)

Before the smoke:

- physical RAM: 128 GB
- reading: free 62.7 GB, inactive 26.3 GB, speculative 0.5 GB →
  reclaimable total **89.5 GB** (134% of the model's 67 GB on-disk
  footprint)
- gate satisfied
- `omlx.cli serve` (PID 49722) was up at 124 MB RSS (idle, no model
  loaded). It had been auto-respawned by the Platform Bootstrap
  Supervisor after B-1's SIGTERM (chain: `supervisor` tmux session
  running `start-supervisor.sh` → uvicorn `ops_dashboard.supervisor:app`
  → recreated `omlx` tmux session at 21:47:38 → `python -m omlx.cli
  serve` inside). Idle oMLX did not block the smoke; not killed in this
  round

## Step 2 Result — `pytest tests/test_mlx_native_backend_real_smoke.py`

Activation:
```
OWLMLX_NATIVE_SMOKE_MODEL_PATH=/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B
OWLMLX_NATIVE_SMOKE_MAX_TOKENS=8
```

Outcome: **2 passed, 2 warnings, 44.00 s wall**

Two warnings are upstream `DeprecationWarning` from `swig`-related
internals during `mlx` import; not actionable.

### Test 1 — `test_real_model_lifecycle_load_stream_unload`

```
[real_smoke] model=/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B
            load_s=12.34 stream_s=6.92
            max_tokens=8 completion_tokens=8 finish=length
            events=['token','token','token','token',
                    'token','token','token','token','done']
```

Critical assertions that passed:

- `load_result.ok = True`,
  `load_result.model.backend = "mlx-native"`,
  `load_result.model.model_id = <local path>`
- 8 `token` events + 1 terminal `done` event
- `finish_reason = "length"`, `completion_tokens = 8`
- `cap['kv_cache_factory']['status'] == "bound_per_request_single_request_only"`
- `cap['kv_cache_factory']['prompt_cache_call_count'] >= 1`
- `cap['kv_cache_factory']['cross_request_reuse_claimed'] is False`
- after `unload`: model id no longer in `backend.status().loaded_models`

This is the first time the adapter's `_make_fresh_prompt_cache` binding
**actually fires under a real-model lifecycle**, not just under
upstream-binding-only synthetic tests.

### Test 2 — `test_real_model_two_streams_serialize_under_admission`

Two threaded `backend.stream_generate(...)` calls on the same model,
both reached `done`. Final admission snapshot:

- `max_observed_concurrency = 1`
- `next_ticket = 2`
- `serving = 2`
- `in_critical_section = 0`

This is the first time `_TicketedAdmission` is observed serializing
**real upstream stream traffic** (not fake-stub yields).

## Provenance (per §1a gate 2)

- candidate: Qwen3.6-35B-A3B local mirror at
  `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`
- admissibility row: §3, verdict `admissible` (B-1, 2026-05-08)
- upstream HF repo: `Qwen/Qwen3.6-35B-A3B`
- upstream commit SHA: `53c43178507d69762986fbfa314f6e8d4d859409`
- mlx_lm version: 0.31.2
- evidence script: existing pytest invocation (no new files); raw
  output retained outside repo at `/tmp/owlmlx_b12_smoke.out`

## Document Changes

- `docs/source-of-truth/native-mlx-backend-capability-matrix.md` —
  added §3c "B-1.2 Real Adapter Lifecycle Evidence". Review also
  refreshed stale §3 Notes / §3a / §3b / §5 / §6 / §7 wording that still
  described real-model adapter smoke as deferred. No §3 row state changes
  in B-1.2

## What This Checkpoint Closes

- the structural gap between "the adapter has been built and unit-
  tested with fakes" and "the adapter has been driven through a real
  lifecycle on an admitted candidate"
- the B-1.1 cap statement on four already-promoted rows (model handle,
  tokenizer handle, decode_step iterator, per-step finish_reason) — the
  cap was that adapter-routed evidence had not been produced; B-1.2
  produces it
- the prerequisite for the KV cache handle row's promotion candidacy:
  the adapter binding must fire under real load. B-1.2 confirms it
  fires (`prompt_cache_call_count >= 1`). The actual promotion is
  B-1.3's call

## What This Checkpoint Does Not Claim

- no row reaches `supported` in B-1.2. Promotion is reserved for B-1.3
- adapter-side cancellation evidence is **not** produced here (both
  tests ran to terminal events). A future round (B-4) would need to
  exercise mid-stream cancellation
- no claim of multi-stream true interleaving, KV cache reuse across
  requests, prefix cache, structured output, speculative decoding,
  sampler injection. All remain at their pre-B-1.2 row state
- no environment file modified
- no `pyproject.toml` / `uv.lock` / `.python-version` / `conftest.py`
  modification
- no admissibility doc edit
- no input-contract / conversion-ownership / promotion-gate clause
  edit
- the auto-respawn behavior of `omlx.cli serve` via the Platform
  Bootstrap Supervisor is recorded as a side observation, not a state
  change

## Test Counts

This round did not add or modify test files. With the env-gated smoke
activated, the focused MLX native adapter set runs as:

- `tests/test_mlx_native_backend.py`: 13 passed + 1 skipped
- `tests/test_mlx_native_backend_post_claim_invariants.py`: 6 passed
- `tests/test_mlx_native_backend_real_upstream_binding.py`: 4 passed
- `tests/test_mlx_native_backend_real_smoke.py`: **2 passed (was 2 skipped)**

When the env var is not set (default), the smoke remains skipped. The
default-CI count is unchanged from the prior round.

## Current Frozen Active Seam (No Change)

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

## Notable Implementation Choices

1. **No new tests written.** The existing
   `tests/test_mlx_native_backend_real_smoke.py` already encodes the
   lifecycle and concurrent-admission contracts B-1.2 needs to prove.
   Activating it via env var is the round's product, not new code
2. **Evidence-collection round, not promotion round.** B-1 → B-1.1 set
   the pattern: B-1 collected admissibility evidence, B-1.1 walked the
   gate. B-1.2 collects adapter-routed evidence, B-1.3 will walk the
   gate. Merging them would re-create the "test passes = row promoted"
   pollution-vector that §1a was written to prevent
3. **idle oMLX not killed.** B-1 had to kill it because it held 52 GB
   RSS competing for memory. B-1.2's oMLX was idle (124 MB), no
   competition. The supervisor's auto-respawn is informative
   background, not a state change requiring round-level decision

## Side Effects

- two-test pytest invocation took 44 s wall, two model loads + unloads
  performed (one per test, each with its own `MlxNativeBackend`
  instance)
- one `caffeinate -i` wrapper used to prevent system sleep mid-load
- one tee log retained at `/tmp/owlmlx_b12_smoke.out` (outside repo)

## Next Authorized Round

Three candidates, ranked:

### Path B-1.3 (recommended): Capability Matrix Promotion from B-1.2 Evidence

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-capability-matrix-promotion-from-b1-2-evidence.md`
  (to be authored)
- scope: walk §1a Promotion Gate for the six B-1.2 promotion candidates
  (model handle, tokenizer handle, decode_step iterator, per-step
  finish_reason, KV cache handle, scheduler admission hook); decide
  per-row whether each goes `partial → supported`; record decline
  reasons for any row that does not promote despite having evidence
- explicitly does **not** promote cancellation, sampler, drafter,
  logits, prefill-decode separation, pinning, structured output,
  multi-stream, KV reuse — those have no B-1.2 evidence
- doc-only round; zero runtime / test / environment change

### Path B-2 (parallel-safe, deferrable): Sibling Candidate Admissibility

- B-1-shaped admissibility for `Qwen3.6-27B` (`qwen3_5`) and
  `gemma-4-31B-it` (`gemma4`); each its own round
- adds candidate breadth but does not unblock matrix `supported`
  promotions further

### Path B-4 (new, deferrable): Cooperative Cancellation Real-Stream Evidence

- run a single test that starts a `stream_generate`, drops the iterator
  early (after 1-2 tokens), and asserts the admission ticket is
  released so a follow-up `stream_generate` proceeds
- this is the only path to evidence that lifts the cancellation row's
  cap; B-1.2's lifecycle tests do not cover it
- requires either a new test case in the existing real-smoke file, or
  a new test file — operator decision

I recommend **B-1.3 first** for the same reason B-1.1 was the right
choice after B-1: cash in this round's evidence into matrix state
while operator memory is fresh, before evidence half-life decay.
B-2 / B-4 are independent and can be run any time.
