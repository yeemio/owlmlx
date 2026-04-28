# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `gemma-4-31B-it`
- repeats per runtime: `2`
- started_at: `2026-04-28T00:45:57Z`
- completed_at: `2026-04-28T00:46:35Z`
- verdict_grade: `measured`
- verdict_text: `measured: owlmlx tokens_per_second 0.1613 vs omlx tokens_per_second 0.5778 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl`

## Runtimes

### `owlmlx` (unknown-local-checkout)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `12579.1417`
- first_token_latency_ms (mean of successes): `12562.1949`
- throughput_tokens_per_second (mean of successes): `0.1613`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `59764850688`

### `omlx` (0.3.5-probe-venv)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `6660.3726`
- first_token_latency_ms (mean of successes): `6643.8675`
- throughput_tokens_per_second (mean of successes): `0.5778`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `53823569920`
