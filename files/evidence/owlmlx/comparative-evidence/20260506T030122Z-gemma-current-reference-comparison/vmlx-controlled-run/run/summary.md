# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it`
- repeats per runtime: `2`
- started_at: `2026-05-06T03:21:39Z`
- completed_at: `2026-05-06T03:22:48Z`
- verdict_grade: `rejected`
- verdict_text: `rejected: vmlx_runtime_invocation_failed:first_token_latency_unobservable on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/20260506T030122Z-gemma-current-reference-comparison/vmlx-controlled-run/live-ledger.jsonl`

## Runtimes

### `owlmlx` (3e14497-dirty-current-8066)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `17115.3663`
- first_token_latency_ms (mean of successes): `8421.2757`
- throughput_tokens_per_second (mean of successes): `3.7398`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `52920385536`

### `vmlx` (vmlx-engine-probe-venv-9fe1bb7)

- completed_request_count: `0`
- failure_count: `2`
- failure_causes: `['first_token_latency_unobservable']`
- wall_clock_ms (mean of successes): `0.0000`
- first_token_latency_ms (mean of successes): `0.0000`
- throughput_tokens_per_second (mean of successes): `0.0000`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `54904782848`
