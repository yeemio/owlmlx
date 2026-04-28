# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it`
- repeats per runtime: `2`
- started_at: `2026-04-27T13:35:32Z`
- completed_at: `2026-04-27T13:36:12Z`
- verdict_grade: `measured`
- verdict_text: `measured: owlmlx tokens_per_second 0.1544 vs omlx tokens_per_second 0.7785 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/20260427T133443Z/live-ledger.jsonl`

## Runtimes

### `owlmlx` (unknown-local-checkout)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `13005.6082`
- first_token_latency_ms (mean of successes): `12985.7429`
- throughput_tokens_per_second (mean of successes): `0.1544`
- peak_resident_set_bytes (max across attempts): `36978688`

### `omlx` (0.3.5-probe-venv)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `7231.0167`
- first_token_latency_ms (mean of successes): `7213.2195`
- throughput_tokens_per_second (mean of successes): `0.7785`
- peak_resident_set_bytes (max across attempts): `28065792`
