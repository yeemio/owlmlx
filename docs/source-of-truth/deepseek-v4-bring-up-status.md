# DeepSeek-V4 Family Bring-Up Status

> Status: authoritative
> Created: 2026-05-10
> Scope: honest current state and bring-up path for DeepSeek-V4-Flash in owlmlx;
> complements `deepseek-v4-flash-adapter-optimization-candidate.md`

## 1. Current Status

**2026-05-17: D1 isolated repeatability gate passed under adopted messages prompt policy.**

`scripts/bench/deepseek_v4_d1_repeatability.py` now drives the existing
isolated `.runtime-deepseek-v4-mlx` environment through a persistent child
protocol:

```text
load -> generate -> unload -> ping -> shutdown
```

Observed status:

- isolated preflight: passed (`mlx_lm` and `mlx_lm.models.deepseek_v4` import
  in `.runtime-deepseek-v4-mlx`)
- tiny real smoke: passed for 1 prompt / 8 tokens; load / unload / clean health
  completed with no child restart
- formal D1 ladder under adopted default policy:
  `20260517T-d1-full-ladder-adopted-messages-policy.jsonl` passed all 15 rows
  (5 prompts x 128/512/1024) through `generate_messages` / chat-template
  rendering with `repetition_flag=false` and clean load/unload health
- raw prompt diagnostic: blocked at `p1_short_cn` / `max_tokens=1024` by
  `repetition_flag=true`; raw prompt is no longer the accepted D1 gate surface
- direct-vs-runner diagnostic:
  `20260517T-d1-p1-1024-direct-vs-runner.jsonl` classifies the blocker as
  `adapter_or_artifact_likely`; direct `mlx_lm.generate` and
  `owlmlx.runtime.mlx_lm_runner` produced the same completion hash and the same
  repeated-window hash for p1/1024
- prompt-surface diagnostic:
  `20260517T-d1-full-ladder-messages-surface-diagnostic.jsonl` passes the full
  5 prompt x 128/512/1024 D1 matrix through `generate_messages` /
  chat-template rendering with `repetition_flag=false` for all 15 rows and
  clean load/unload health
- lifecycle during the failed ladder remained clean:
  `restart_observed=false`, unload ok, backend health clean after unload
- D1 evidence records now include prompt shape, completion preview/tail,
  structured repetition diagnostics, optional stop-string controls, and stream
  diagnostic events when `--generation-surface stream` is used

This keeps DeepSeek V4 at `experimental_only`. It does not make
`DeepSeek-V4-Flash-2bit-DQ` visible on the default model surface, does not
adopt `ds4.c`, and does not claim supported DeepSeek V4 serving. It closes D1
only for the isolated experimental lane and unlocks D2 metrics-ledger work.

**D2 follow-up status:** the `metrics` subcommand now has p1/p2/p4 × 128/512
ledger coverage after replacing blocking child stdout `readline()` handling
with fd-buffered reads.
`20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl` records 6/6 passed rows,
`missing_metrics=[]`, `rss_sample_scope=child_process`,
`rss_sample_source=ps_rss_kb`, `rss_sample_timing=after_generation_before_unload`,
and clean load / generate / unload / health. The run summary records
`ttft_ms.p50=593.840`, `decode_tps_after_first_token.p50=38.17885`, and
`child_rss_gb.p50=7.214432`. Treat this as the D2 ladder pass for the isolated
experimental lane, not as a supported DeepSeek serving claim. This
child-process RSS sample is not comparable to the earlier 96.574 GB short-smoke
peak-memory note.

**D3 follow-up status:** the checkpoint/MTP inspection gate is complete for the
current local artifact. `20260517T-d3-mtp-checkpoint-inspection.jsonl` records
`num_nextn_predict_layers=1`, 2610 weight keys, 19 safetensors shards, zero
matched MTP/draft/speculative weight keys, zero extra layer keys beyond
`num_hidden_layers=43`, and
`missingReason=mtp_weights_absent_or_stripped`. Treat this as
`capability_conclusion=mtp_checkpoint_not_available`, not as DeepSeek MTP
serving support.

**D4 follow-up status:** the MTP clean pre-load rejection gate is complete for
the current local artifact. `20260517T-d4-mtp-clean-preload-reject.jsonl`
records `schema_version=d4.preload_reject.v1`,
`record_type=mtp_preload_reject`, `requested_capability=deepseek_v4_mtp`,
`decision=rejected_pre_load`, `reason_code=mtp_weights_absent_or_stripped`,
`load_attempted=false`, `child_process_started=false`,
`default_model_surface_changed=false`, and stable 8066 `/healthz` fingerprints
before and after. Treat this as failure isolation for an unavailable MTP path,
not as DeepSeek MTP serving support.

**2026-05-11: Lifecycle complete via intermediate path.**

`DeepSeek-V4-Flash-2bit-DQ` completed load → generate → unload → clean health
on port 8067 using `.runtime-deepseek-v4-mlx` (Blaizzy fork `pc/add-deepseekv4flash-model`,
editable at `/tmp/mlx-lm-dsv4`). A `model_release_candidate_record` row has
been appended to `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`.

Measured:
- load_time_s: 14.125
- TTFT (cold start): 24821 ms (expected — 96 GB weights cold)
- TPS: 32.0 tokens/sec
- Unload: ok, freed_gb=100.0
- Backend health after unload: ok, model_count=0

Residual issues (not blockers):
- `transformers 5.7.0` does not register `deepseek_v4` in CONFIG_MAPPING → tokenizer
  loads via `PreTrainedTokenizerFast` fallback (patched in fork's `tokenizer_utils.py`)
- The upstream `machiabeli/mlx-lm-1` fork is empty/inaccessible; bring-up used
  `Blaizzy/mlx-lm@pc/add-deepseekv4flash-model` (same deepseek_v4 implementation)
- Memory estimate in 3.3 was wrong: actual peak ≈ 96 GB, not 14–16 GB

The bring-up target was: **load → generate → unload → clean health**. ✓ Done.

## 2. Upstream Dependency

DeepSeek-V4 support requires `mlx_lm.models.deepseek_v4`. This module exists
in:

- **PR branch:** `machiabeli/mlx-lm-1`, commit `7d20c1d`
- **Status:** not merged into any `mlx-lm` release as of 2026-05-10
- **Isolated proof:** a first short smoke through the PR branch produced
  visible text; full lifecycle was not completed (memory pressure at 4-bit)
- **Stock release:** `mlx-lm 0.31.3` does not include `deepseek_v4.py`

owlmlx has **no local allowlist** blocking DeepSeek. The check is a pure
`importlib.util.find_spec(f"mlx_lm.models.{model_type}")` probe. When the
module is available, the load path proceeds normally.

## 3. Bring-Up Path

### 3.1 When Upstream Merges

Once `mlx_lm.models.deepseek_v4` is available in a released `mlx-lm` version:

1. Bump `mlx-lm` lower bound in `pyproject.toml` to the release that includes it
2. Run the Model RC harness against `DeepSeek-V4-Flash-2bit-DQ` with the
   `flagship_experimental` lane
3. Collect a clean `load → generate → unload → clean health` record
4. If memory pressure causes OOM (exit 137), classify as
   `memory_budget_exceeded` and record the exact RSS at point of failure
5. Update `native-mlx-backend-capability-matrix.md` and add a measured
   `model_release_candidate_record` row

### 3.2 Intermediate Path (PR Branch)

If owlmlx needs DeepSeek evidence before upstream merges:

1. Create a separate `pyproject.toml` extras group: `[project.optional-dependencies]`
   `deepseek-experimental = ["mlx-lm @ git+https://github.com/machiabeli/mlx-lm@7d20c1d"]`
2. Run the Model RC harness under this extras group in a dedicated venv
3. Record evidence under `files/evidence/owlmlx/model-release-candidates/` with
   `lane=flagship_experimental` and `visibility_status=not_registered`
4. Do **not** merge the PR-branch dependency into the mainline `runtime` extra

This path is optional. The main bring-up gate is upstream merge.

### 3.3 Memory Budget Constraint

Corrected (2026-05-11): The 2-bit-DQ variant requires approximately 96–100 GB
peak unified memory (not 14–16 GB as originally estimated). The model has ~284 B
total parameters; at 2 bits/param ≈ 71 GB weights + KV cache + activations ≈ 96 GB.
The 4-bit variant (≈ 142 GB) exceeds this host's 128 GB capacity.

Bring-up uses the 2-bit-DQ variant exclusively with `memory_gb=100`.

## 4. Blocked Scope

Until upstream merges, the following are explicitly deferred:

- Any measured TPS comparison against reference runtimes for DeepSeek
- Any visibility registration on `GET /v1/openai/models`
- Any claim of DeepSeek support in external communication

The `BANNED_VERDICT_VOCABULARY` enforcement in `owlmlx.comparative_evidence_schema`
ensures no premature parity or replacement claim can pass schema validation.

## 5. Test Contract

`tests/test_mlx_native_backend.py` includes a test verifying the historical
generic clean rejection behavior: loading `DeepSeek-V4-Flash-2bit-DQ` through
an unsupported native model-family path returns an error event with
`error_code=unsupported_model_family` without dirtying backend health state.

`tests/test_deepseek_v4_d1_repeatability.py` now also covers the MTP-specific
D4 gate: when D3 evidence says `missingReason=mtp_weights_absent_or_stripped`,
the D4 runner emits `decision=rejected_pre_load`, keeps
`load_attempted=false` and `child_process_started=false`, and fails if runtime
health changes. This D4 path is about absent MTP checkpoint weights, not an
absent `deepseek_v4` loader.

When the bring-up is complete, a new test in
`tests/test_mlx_native_backend_real_smoke.py` (env-gated) should verify the
full lifecycle.

## 6. Update Rule

This document is updated when:

- `mlx_lm.models.deepseek_v4` is available in a released version
- A full-lifecycle Model RC record exists for any DeepSeek variant
- The memory budget constraint changes (larger or smaller variant available)
