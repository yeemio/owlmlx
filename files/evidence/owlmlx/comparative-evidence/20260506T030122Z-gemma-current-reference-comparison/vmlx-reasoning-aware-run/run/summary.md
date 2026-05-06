# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it`
- repeats per runtime: `2`
- started_at: `2026-05-06T03:24:17Z`
- completed_at: `2026-05-06T03:25:25Z`
- verdict_grade: `measured`
- verdict_text: `measured: owlmlx tokens_per_second 3.7468 vs vmlx tokens_per_second 3.8304 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/20260506T030122Z-gemma-current-reference-comparison/vmlx-reasoning-aware-run/live-ledger.jsonl`

## Runtimes

### `owlmlx` (3e14497-dirty-current-8066)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `17088.5202`
- first_token_latency_ms (mean of successes): `8225.9886`
- throughput_tokens_per_second (mean of successes): `3.7468`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `54586949632`

### `vmlx` (vmlx-engine-probe-venv-9fe1bb7-reasoning-aware-client)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `16712.1857`
- first_token_latency_ms (mean of successes): `8306.4983`
- throughput_tokens_per_second (mean of successes): `3.8304`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `55705976832`
