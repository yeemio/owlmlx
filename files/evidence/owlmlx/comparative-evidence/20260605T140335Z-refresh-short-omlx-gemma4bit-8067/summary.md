# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it-4bit`
- repeats per runtime: `5`
- started_at: `2026-06-05T14:03:35Z`
- completed_at: `2026-06-05T14:04:06Z`
- verdict_grade: `measured`
- verdict_text: `measured: owlmlx tokens_per_second 9.6570 vs omlx tokens_per_second 24.5576 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `data/comparative-evidence-ledger.jsonl`

## Runtimes

### `owlmlx` (local-checkout-warm-8067-benchmark-only-4bit-visible)

- completed_request_count: `5`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `1067.1697`
- first_token_latency_ms (mean of successes): `1060.3388`
- throughput_tokens_per_second (mean of successes): `9.6570`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `18781896704`

### `omlx` (0.3.5-warm-8063)

- completed_request_count: `5`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `5212.4238`
- first_token_latency_ms (mean of successes): `5205.5068`
- throughput_tokens_per_second (mean of successes): `24.5576`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `18303057920`
