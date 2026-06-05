# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it-4bit`
- repeats per runtime: `5`
- started_at: `2026-06-05T13:58:41Z`
- completed_at: `2026-06-05T13:59:13Z`
- verdict_grade: `rejected`
- verdict_text: `rejected: owlmlx_runtime_invocation_failed:harness_runtime_invocation_error_non_zero_exit on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `data/comparative-evidence-ledger.jsonl`

## Runtimes

### `owlmlx` (local-checkout-warm-8066)

- completed_request_count: `0`
- failure_count: `5`
- failure_causes: `['harness_runtime_invocation_error_non_zero_exit']`
- wall_clock_ms (mean of successes): `0.0000`
- first_token_latency_ms (mean of successes): `0.0000`
- throughput_tokens_per_second (mean of successes): `0.0000`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `353419264`

### `omlx` (0.3.5-warm-8063)

- completed_request_count: `5`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `6238.4085`
- first_token_latency_ms (mean of successes): `6228.6963`
- throughput_tokens_per_second (mean of successes): `21.8380`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `18841894912`
