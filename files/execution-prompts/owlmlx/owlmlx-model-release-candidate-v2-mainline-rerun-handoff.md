# owlmlx Model RC v2 Mainline Rerun Handoff

> Status: handoff
> Updated: 2026-05-05
> Outcome: `owlmlx_model_release_candidate_v2_mainline_records_published`
> Scope: rerun the three mainline Model RC candidates after OwlOps consumed the
> observability v2 contract

## 1. Verdict

The v2 observability loop is now live on owlmlx.

`GET /v1/runtime/model-release-candidates/history` on `127.0.0.1:8066` returns
seven records:

- four previous records without v2 fields
- three new mainline records with v2 fields

All three new mainline records remain `needs_optimization`. No model is marked
`pass`.

## 2. Published v2 Records

### Qwen3.6-27B

Evidence:

`files/evidence/owlmlx/model-release-candidates/20260505T130906Z-qwen36-27b-v2-rerun`

Metrics:

- `repeat_count = 2`
- `failure_count = 0`
- `load_time_ms = 10188.202`
- `reload_time_ms = 9435.728`
- `unload_time_ms = 530.493`
- `queue_wait_ms = 56.1`
- `ttft_ms = 2890.414`
- `decode_tokens_per_second = 4.135`
- `end_to_end_tokens_per_second = 3.105`
- `peak_resident_set_bytes = 50064687104`
- `memory_headroom_bytes = 87374266368`
- `memory_peak_source = process_tree_rss`
- `output_sanity_label = valid_text`

Interpretation:

This run shows slow decode as well as end-to-end latency. TTFT contributes, but
decode itself is not fast enough to dismiss the issue as TTFT-only.

### Qwen3.6-35B-A3B

Evidence:

`files/evidence/owlmlx/model-release-candidates/20260505T131002Z-qwen36-35b-a3b-v2`

Metrics:

- `repeat_count = 2`
- `failure_count = 0`
- `load_time_ms = 15680.213`
- `reload_time_ms = 17496.333`
- `unload_time_ms = 818.888`
- `queue_wait_ms = 48.0`
- `ttft_ms = 6187.685`
- `decode_tokens_per_second = 29.941`
- `end_to_end_tokens_per_second = 7.718`
- `peak_resident_set_bytes = 47793684480`
- `memory_headroom_bytes = 89645268992`
- `memory_peak_source = process_tree_rss`
- `output_sanity_label = reasoning_trace_truncated`

Interpretation:

Decode is much faster than end-to-end throughput. The dominant visible issues
are high TTFT / prefill latency and reasoning-template behavior.

### gemma-4-31B-it

Evidence:

`files/evidence/owlmlx/model-release-candidates/20260505T131334Z-gemma-4-31b-it-v2-rerun`

Metrics:

- `repeat_count = 2`
- `failure_count = 0`
- `load_time_ms = 10957.576`
- `reload_time_ms = 10946.711`
- `unload_time_ms = 705.492`
- `queue_wait_ms = 87.55`
- `ttft_ms = 4220.365`
- `decode_tokens_per_second = 3.009`
- `end_to_end_tokens_per_second = 2.544`
- `peak_resident_set_bytes = 43041095680`
- `memory_headroom_bytes = 94397857792`
- `memory_peak_source = process_tree_rss`
- `output_sanity_label = repetitive_output`

Interpretation:

The first Gemma v2 run exposed prompt echo repetition that the classifier
initially labeled `valid_text`. The classifier was narrowed and Gemma was
rerun. The latest cumulative record now carries
`quality_caveats = ["output_sanity:repetitive_output", ...]`.

## 3. Excluded Local Evidence

The first `Qwen3.6-27B` v2 attempt failed before generation because
`--memory-gb` was omitted:

`files/evidence/owlmlx/model-release-candidates/20260505T130835Z-qwen36-27b-v2`

It is preserved as local evidence and is not included in the cumulative
ledger.

## 4. Cumulative Ledger

The cumulative ledger was rebuilt at:

`files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`

It includes:

- old A1 `Qwen3.6-27B`
- old A2 `Qwen3.6-35B-A3B`
- old A3 `gemma-4-31B-it`
- old D1 `DeepSeek-V4-Flash-2bit-DQ`
- new v2 `Qwen3.6-27B`
- new v2 `Qwen3.6-35B-A3B`
- new v2 `gemma-4-31B-it`

`latest` is now the new Gemma v2 record. Consumers should still use
`history.records` for the matrix.

## 5. Verification

Commands run:

```bash
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile owlmlx/model_release_candidate_schema.py owlmlx/model_release_candidate_record.py scripts/runtime_model_release_candidate.py
.venv/bin/python scripts/runtime_model_release_candidate.py --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl history
curl -sS http://127.0.0.1:8066/v1/runtime/model-release-candidates/history
curl -sS http://127.0.0.1:8066/v1/runtime/model-release-candidates
curl -sS http://127.0.0.1:8066/healthz
git diff --check
```

Observed live state:

- `history.records` count is `7`
- `latest.model_id = gemma-4-31B-it`
- `latest.output_sanity_label = repetitive_output`
- `healthz.ok = true`
- `active_model_id = null`
- `model_count = 0`
- `/tmp/owlmlx-model-rc-heavy.lock` absent after runs

## 6. Next Work

OwlOps:

- render the seven-record history and verify v2-present rows are shown as
  bottleneck-readable while old rows are `upstream_missing`

owlmlx:

- Qwen3.6-27B: investigate low decode speed
- Qwen3.6-35B-A3B: investigate TTFT / reasoning-template behavior
- Gemma: investigate prompt-template repetition

## 7. Non-Claims

This handoff does not claim release-ready, parity, replacement, production
grade, or superiority against oMLX / vMLX.
