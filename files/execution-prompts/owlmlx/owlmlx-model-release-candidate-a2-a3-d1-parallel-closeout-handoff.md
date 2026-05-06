# owlmlx Model Release Candidate A2/A3/D1 Parallel Closeout Handoff

> Status: handoff
> Updated: 2026-05-05
> Outcome: `owlmlx_model_release_candidate_a2_a3_d1_parallel_lanes_integrated`
> Scope: coordinator integration of A2 `Qwen3.6-35B-A3B`, A3 `gemma-4-31B-it`,
> and D1 `DeepSeek-V4-Flash-2bit-DQ` evidence after single-heavy-lane execution
> completed.

## 1. Verdict

The parallel remaining-lane round is integrated, but the Model RC gate is not
closed.

Current model verdicts:

- `Qwen3.6-27B`: `needs_optimization`
- `Qwen3.6-35B-A3B`: `needs_optimization`
- `gemma-4-31B-it`: `needs_optimization`
- `DeepSeek-V4-Flash-2bit-DQ`: `experimental_only`

No model is marked `pass`.

## 2. Integrated Records

The cumulative ledger is:

`files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`

It contains four records:

- `20260505T071836Z-qwen36-27b/ledger.jsonl`
- `20260505T073902Z-qwen36-35b-a3b/ledger.jsonl`
- `20260505T074135Z-gemma-4-31b-it/ledger.jsonl`
- `20260505T073943Z-deepseek-v4-flash-2bit-dq/ledger.jsonl`

`history.records` is the matrix view. `latest` returns the newest appended
record, which is the DeepSeek experimental record. Upper layers must not treat
`latest` as the mainline matrix verdict.

## 3. A2 Result

`Qwen3.6-35B-A3B` completed two live HTTP repeated runs through:

`load -> stream generate -> unload -> reload -> stream generate -> unload`

Metrics:

- `repeat_count = 2`
- `failure_count = 0`
- `first_token_latency_ms = 3315.486`
- `tokens_per_second = 14.666`
- `wall_clock_ms = 37299.247`
- `peak_resident_set_bytes = 54570254336`
- `memory_headroom_bytes = 82868699136`
- `output_sanity_label = reasoning_trace_truncated`

Blockers:

- `owlops_observation_pending`
- `reference_runtime_comparison_missing`
- `short_generation_quality_inconclusive`

## 4. A3 Result

`gemma-4-31B-it` completed two live HTTP repeated runs through the same
mainline sequence.

Metrics:

- `repeat_count = 2`
- `failure_count = 0`
- `first_token_latency_ms = 2179.717`
- `tokens_per_second = 6.178`
- `wall_clock_ms = 36577.866`
- `peak_resident_set_bytes = 56211668992`
- `memory_headroom_bytes = 81227284480`
- `output_sanity_label = valid_text`

Blockers:

- `owlops_observation_pending`
- `reference_runtime_comparison_missing`

## 5. D1 Result

`DeepSeek-V4-Flash-2bit-DQ` completed one isolated
`.runtime-deepseek-v4-mlx` / `mlx_lm.generate` pressure run. It did not run as
an owlmlx HTTP adapter and must remain `experimental_only`.

Metrics:

- `repeat_count = 1`
- `failure_count = 0`
- `tokens_per_second = 31.804`
- `wall_clock_ms = 43665`
- `sampled peak_resident_set_bytes = 58170621952`
- `sampled memory_headroom_bytes = 79268331520`
- `output_sanity_label = valid_text`

Preserved caveat:

- MLX stdout reported `96.574 GB` peak memory while the process-tree sampler
  captured `58170621952` bytes. This discrepancy is evidence for the next
  pressure-lane instrumentation pass and must not be normalized away.

Blockers:

- `technical_preview_visibility_not_registered`
- `isolated_pr_runtime_not_integrated_as_owlmlx_http_adapter`
- `unload_reload_adapter_not_exposed`
- `first_token_latency_missing_from_cli_output`
- `repeat_prompt_adapter_evidence_missing`
- `owlops_observation_missing`
- `transformers_deepseek_v4_config_tokenizer_fallback_warning`

## 6. Commands Run By Coordinator

Merged the cumulative ledger:

```bash
.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl \
  merge-ledgers \
  --replace \
  files/evidence/owlmlx/model-release-candidates/20260505T071836Z-qwen36-27b/ledger.jsonl \
  files/evidence/owlmlx/model-release-candidates/20260505T073902Z-qwen36-35b-a3b/ledger.jsonl \
  files/evidence/owlmlx/model-release-candidates/20260505T074135Z-gemma-4-31b-it/ledger.jsonl \
  files/evidence/owlmlx/model-release-candidates/20260505T073943Z-deepseek-v4-flash-2bit-dq/ledger.jsonl
```

Local operator checks:

```bash
.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl \
  history

.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl \
  latest
```

## 7. Next Dominant Gaps

OwlOps:

- consume `history.records` from the cumulative ledger and render the full
  matrix without upgrading verdicts
- display DeepSeek as `experimental_only`, not supported

owlmlx:

- reduce `reference_runtime_comparison_missing` for mainline models through a
  same-host oMLX / vMLX comparison lane
- decide whether `latest` should remain single-record semantics or whether a
  dedicated mainline-summary endpoint is needed for upper-layer UX

## 8. Non-Claims

This handoff does not claim release-ready, parity, replacement, production
grade, or superiority against oMLX / vMLX.
