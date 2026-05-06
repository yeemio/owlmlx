# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `Qwen3.6-35B-A3B`
- repeats per runtime: `2`
- started_at: `2026-05-06T04:09:56Z`
- completed_at: `2026-05-06T04:11:25Z`
- verdict_grade: `measured`
- verdict_text: `measured: owlmlx tokens_per_second 3.5349 vs omlx tokens_per_second 2.4400 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/cumulative-ledger.jsonl`

## Runtimes

### `owlmlx` (12ee7b7-dirty-current-8066-comparative-ledger)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `18107.2971`
- first_token_latency_ms (mean of successes): `16655.8041`
- throughput_tokens_per_second (mean of successes): `3.5349`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `47860367360`

### `omlx` (0.3.4-homebrew-jundot-omlx-livepid-portpid)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `26231.9451`
- first_token_latency_ms (mean of successes): `16347.2927`
- throughput_tokens_per_second (mean of successes): `2.4400`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `47785541632`
