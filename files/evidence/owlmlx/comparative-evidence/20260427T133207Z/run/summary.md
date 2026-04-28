# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it`
- repeats per runtime: `2`
- started_at: `2026-04-27T13:33:19Z`
- completed_at: `2026-04-27T13:33:46Z`
- verdict_grade: `rejected`
- verdict_text: `rejected: omlx_runtime_invocation_failed:harness_runtime_invocation_error_non_zero_exit on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/20260427T133207Z/live-ledger.jsonl`

## Runtimes

### `owlmlx` (unknown-local-checkout)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `13605.5849`
- first_token_latency_ms (mean of successes): `13588.8128`
- throughput_tokens_per_second (mean of successes): `0.1477`
- peak_resident_set_bytes (max across attempts): `37224448`

### `omlx` (0.3.5-probe-venv)

- completed_request_count: `0`
- failure_count: `2`
- failure_causes: `['harness_runtime_invocation_error_non_zero_exit']`
- wall_clock_ms (mean of successes): `0.0000`
- first_token_latency_ms (mean of successes): `0.0000`
- throughput_tokens_per_second (mean of successes): `0.0000`
- peak_resident_set_bytes (max across attempts): `26443776`
