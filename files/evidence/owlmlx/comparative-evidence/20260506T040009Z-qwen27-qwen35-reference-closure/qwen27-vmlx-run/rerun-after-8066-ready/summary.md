# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `Qwen3.6-27B`
- repeats per runtime: `2`
- started_at: `2026-05-06T04:05:35Z`
- completed_at: `2026-05-06T04:06:08Z`
- verdict_grade: `rejected`
- verdict_text: `rejected: vmlx_runtime_invocation_failed:harness_runtime_invocation_error_non_zero_exit on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/cumulative-ledger.jsonl`

## Runtimes

### `owlmlx` (12ee7b7-dirty-current-8066-comparative-ledger)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `11430.0951`
- first_token_latency_ms (mean of successes): `4207.5861`
- throughput_tokens_per_second (mean of successes): `5.5997`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `54434840576`

### `vmlx` (vmlx-engine-probe-venv-9fe1bb7-reasoning-aware-client-portpid)

- completed_request_count: `0`
- failure_count: `2`
- failure_causes: `['harness_runtime_invocation_error_non_zero_exit']`
- wall_clock_ms (mean of successes): `0.0000`
- first_token_latency_ms (mean of successes): `0.0000`
- throughput_tokens_per_second (mean of successes): `0.0000`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `54751936512`
