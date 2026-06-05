# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `multi_prompt_serial`
- model_id: `gemma-4-31B-it-4bit`
- repeats per runtime: `5`
- started_at: `2026-06-05T14:04:22Z`
- completed_at: `2026-06-05T14:07:15Z`
- verdict_grade: `measured`
- verdict_text: `measured: owlmlx tokens_per_second 20.5102 vs omlx tokens_per_second 22.4831 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=multi_prompt_serial`
- ledger_path: `data/comparative-evidence-ledger.jsonl`

## Runtimes

### `owlmlx` (local-checkout-warm-8067-benchmark-only-4bit-visible)

- completed_request_count: `5`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `11807.3667`
- first_token_latency_ms (mean of successes): `1833.9661`
- throughput_tokens_per_second (mean of successes): `20.5102`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `18082299904`

### `omlx` (0.3.5-warm-8063)

- completed_request_count: `5`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `22772.9772`
- first_token_latency_ms (mean of successes): `22765.7077`
- throughput_tokens_per_second (mean of successes): `22.4831`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `18304303104`
