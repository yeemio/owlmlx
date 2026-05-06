# owlmlx Model RC D1 DeepSeek V4 Flash 2bit-DQ Pressure Adapter Handoff

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

Outcome:

`owlmlx_model_release_candidate_d1_deepseek_v4_flash_2bit_dq_pressure_record_introduced`

## 1. Verdict

`DeepSeek-V4-Flash-2bit-DQ` has a D1 pressure/adaptation evidence record.

Record verdict:

```text
experimental_only
```

This is intentionally not `pass`. The lane remains:

```text
lane = flagship_experimental
visibility_status = not_registered
```

## 2. Evidence Directory

```text
files/evidence/owlmlx/model-release-candidates/20260505T073943Z-deepseek-v4-flash-2bit-dq
```

Key files:

- `record.json`
- `ledger.jsonl`
- `generation-summary.json`
- `generate.stdout`
- `generate.stderr`
- `generate-metrics.env`
- `process-tree-rss.jsonl`
- `final-stale-and-port-check.txt`

The local `ledger.jsonl` is inside the D1 evidence directory only. No shared
ledger or shared docs were edited by this lane.

## 3. Runtime Command

The run used the isolated DeepSeek runtime:

```bash
/Users/yeemio/AI/gitrep/owlmlx/.runtime-deepseek-v4-mlx/bin/python -m mlx_lm.generate \
  --model /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ \
  --prompt "Write one short sentence about local AI." \
  --max-tokens 64 \
  --temp 0.0 \
  --max-kv-size 512 \
  --kv-bits 4 \
  --kv-group-size 64
```

Memory coordination lock:

```text
LOCK=/tmp/owlmlx-model-rc-heavy.lock
```

Observed lock result:

```text
lock_wait_start_utc=2026-05-05T07:40:09Z
lock_acquired_utc=2026-05-05T07:40:09Z
```

## 4. Measured Result

```text
exit_code = 0
wall_clock_ms = 43665
prompt_tokens = 12
generation_tokens = 32
generation_tokens_per_second = 31.804
mlx_reported_peak_memory_gb = 96.574
sampled_process_tree_peak_rss_bytes = 58170621952
sampled_process_tree_peak_rss_gib = 54.176
sampled_process_tree_memory_headroom_bytes = 79268331520
sampled_process_tree_memory_headroom_gib = 73.824
output_sanity_label = valid_text
```

Output preview:

```text
Local AI refers to artificial intelligence systems deployed on local devices, enabling real-time, privacy-focused, and low-l latency processing without relying on centralized cloud servers.
```

## 5. Record Summary

```text
model_id = DeepSeek-V4-Flash-2bit-DQ
lane = flagship_experimental
visibility_status = not_registered
verdict = experimental_only
repeat_count = 1
failure_count = 0
load_result.status = pass
generation_result.status = pass
unload_result.status = not_applicable
reload_result.status = not_applicable
tokens_per_second = 31.804
wall_clock_ms = 43665
peak_resident_set_bytes = 58170621952
memory_headroom_bytes = 79268331520
```

## 6. Adapter Blockers

- `technical_preview_visibility_not_registered`
- `isolated_pr_runtime_not_integrated_as_owlmlx_http_adapter`
- `unload_reload_adapter_not_exposed`
- `first_token_latency_missing_from_cli_output`
- `repeat_prompt_adapter_evidence_missing`
- `owlops_observation_missing`
- `transformers_deepseek_v4_config_tokenizer_fallback_warning`

Runtime warnings preserved in `generate.stderr`:

- `mlx_lm.generate` direct module invocation is deprecated
- Transformers still warns about generic `deepseek_v4` config/tokenizer fallback
- tokenizer fallback remains active because Transformers does not recognize the
  model config enough to expose `max_position_embeddings`

## 7. Stale Process And Port Check

Post-run stale process check:

```text
current_deepseek_generate_processes: none
```

Lock recheck:

```text
/tmp/owlmlx-model-rc-heavy.lock absent after final investigation
```

Ports:

```text
8001 listener remained present
8009 listener remained present
8066 listener remained present
```

D1 did not kill `8001` or `8009`, and did not remount/restart `8066`.

## 8. Verification

```text
python3 scripts/runtime_model_release_candidate.py --ledger-path files/evidence/owlmlx/model-release-candidates/20260505T073943Z-deepseek-v4-flash-2bit-dq/ledger.jsonl append-record-file files/evidence/owlmlx/model-release-candidates/20260505T073943Z-deepseek-v4-flash-2bit-dq/record.json
append_exit = 0

pytest -q tests/test_model_release_candidate_surface.py
17 passed in 1.94s

python3 -m py_compile scripts/runtime_model_release_candidate.py
py_compile_exit = 0

git diff --check
git_diff_check_exit = 0
```

## 9. Recommendation

D2 should build a narrow isolated HTTP adapter only if the coordinator wants to
turn this PR-runtime CLI proof into runtime-owned operation evidence. It should
not register DeepSeek as supported, should not use the 4bit artifact as the
pressure line, and should continue using exclusive memory coordination.
