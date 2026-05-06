# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it`
- repeats per runtime: `2`
- started_at: `2026-05-06T03:18:19Z`
- completed_at: `2026-05-06T03:19:14Z`
- verdict_grade: `rejected`
- verdict_text: `rejected: omlx_runtime_invocation_failed:harness_runtime_invocation_error_non_zero_exit on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/20260506T030122Z-gemma-current-reference-comparison/omlx-livepid-run/live-ledger.jsonl`

## Runtimes

### `owlmlx` (3e14497-dirty-current-8066)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `17202.8010`
- first_token_latency_ms (mean of successes): `8365.6575`
- throughput_tokens_per_second (mean of successes): `3.7212`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `53963571200`

### `omlx` (0.3.5-probe-venv-d3c328f)

- completed_request_count: `0`
- failure_count: `2`
- failure_causes: `['harness_runtime_invocation_error_non_zero_exit']`
- wall_clock_ms (mean of successes): `0.0000`
- first_token_latency_ms (mean of successes): `0.0000`
- throughput_tokens_per_second (mean of successes): `0.0000`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `53200093184`
