# Comparative Evidence Run Summary

- host_class: `darwin-arm64-m3-ultra-128gb`
- workload_class: `single_prompt_short`
- model_id: `DeepSeek-V4-Flash-2bit-DQ`
- repeats per runtime: `2`
- started_at: `2026-05-06T05:40:46Z`
- completed_at: `2026-05-06T05:40:50Z`
- verdict_grade: `rejected`
- verdict_text: `rejected: owlmlx_runtime_invocation_failed:first_token_latency_unobservable on host_class=darwin-arm64-m3-ultra-128gb, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/cumulative-ledger.jsonl`

## Runtimes

### `owlmlx` (9389cad-current-8066-comparative-ledger)

- completed_request_count: `0`
- failure_count: `2`
- failure_causes: `['first_token_latency_unobservable']`
- wall_clock_ms (mean of successes): `0.0000`
- first_token_latency_ms (mean of successes): `0.0000`
- throughput_tokens_per_second (mean of successes): `0.0000`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `183205888`

### `omlx` (0.3.4-homebrew-jundot-omlx-sidecar-model-candidates-portpid)

- completed_request_count: `0`
- failure_count: `2`
- failure_causes: `['harness_runtime_invocation_error_non_zero_exit']`
- wall_clock_ms (mean of successes): `0.0000`
- first_token_latency_ms (mean of successes): `0.0000`
- throughput_tokens_per_second (mean of successes): `0.0000`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `177389568`
