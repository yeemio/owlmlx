# Comparative Evidence Run Summary

- host_class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- workload_class: `single_prompt_short`
- model_id: `Qwen3.6-27B`
- repeats per runtime: `2`
- started_at: `2026-05-06T04:06:34Z`
- completed_at: `2026-05-06T04:07:43Z`
- verdict_grade: `measured`
- verdict_text: `measured: owlmlx tokens_per_second 5.4482 vs omlx tokens_per_second 2.8127 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short`
- ledger_path: `files/evidence/owlmlx/comparative-evidence/cumulative-ledger.jsonl`

## Runtimes

### `owlmlx` (12ee7b7-dirty-current-8066-comparative-ledger)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `11767.5345`
- first_token_latency_ms (mean of successes): `4143.9156`
- throughput_tokens_per_second (mean of successes): `5.4482`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `54420045824`

### `omlx` (0.3.4-homebrew-jundot-omlx-livepid-portpid)

- completed_request_count: `2`
- failure_count: `0`
- failure_causes: `[]`
- wall_clock_ms (mean of successes): `22832.5488`
- first_token_latency_ms (mean of successes): `4848.9954`
- throughput_tokens_per_second (mean of successes): `2.8127`
- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `55013818368`
