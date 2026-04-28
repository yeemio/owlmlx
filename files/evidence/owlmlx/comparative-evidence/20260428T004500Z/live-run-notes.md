# owlmlx 3.5E Live Measured Run Rerun Notes

> Date: 2026-04-28
> Evidence directory: `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/`
> OMLX port: `8063`
> HTTP verification port: `8064`

## Stable Checks

```text
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
27 passed in 0.18s

pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
37 passed in 4.19s

pytest -q tests/test_runtime_server.py -k "comparative_evidence"
4 passed, 37 deselected in 0.40s

python3 -m py_compile owlmlx/comparative_evidence_schema.py owlmlx/comparative_evidence_record.py owlmlx/comparative_evidence_ledger.py owlmlx/comparative_evidence_runner.py scripts/runtime_comparative_evidence.py owlmlx/runtime/server.py
passed with no output

python3 scripts/runtime_comparative_evidence.py run-measured-short-prompt --help
printed help successfully
```

## Workload

- `workload_class`: `single_prompt_short`
- prompt: `Reply with exactly OK.`
- `prompt_set_hash`: `sha256:b4d50a67a784a449e0c763c401bb9f95fb37804dff5765d8b4f95fd202eb7d77`
- `model_id`: `gemma-4-31B-it`
- `model_path`: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- `model_quantization`: `full_precision_unquantized`
- `decode_max_tokens`: `2`
- `decode_temperature`: `0.0`
- `serving_budget_bytes`: `85899345920`
- `host_class`: `Mac17,6-arm64-macOS-26.4.1-128GB`

## Config Requirements

- `omlx` uses `external_pid_file = files/evidence/owlmlx/comparative-evidence/20260428T004500Z/omlx-server.pid`.
- `owlmlx.first_token_strategy = regex:"text":\s*"[^"]+"`, so diagnostic JSON before the generated text is skipped.
- `omlx.first_token_strategy = first_nonempty_chunk`, because the helper prints only assistant content.

## Live Result

The runner emitted a fresh closeout-grade `measured` record:

```text
recorded_at = 2026-04-28T00:46:35Z
evidence_pointer = files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/manifest.json
verdict_grade = measured
verdict_text = measured: owlmlx tokens_per_second 0.1613 vs omlx tokens_per_second 0.5778 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short
```

Metrics:

```text
owlmlx completed_request_count = 2
owlmlx failure_count = 0
owlmlx first_token_latency_ms = 12562.1948960179
owlmlx peak_resident_set_bytes = 59764850688
owlmlx throughput_tokens_per_second = 0.16129696700190332

omlx completed_request_count = 2
omlx failure_count = 0
omlx first_token_latency_ms = 6643.867458493332
omlx peak_resident_set_bytes = 53823569920
omlx throughput_tokens_per_second = 0.5777615125446283
```

Sanity checks:

- `omlx.peak_resident_set_bytes` is GB-scale and includes external PID
  `84730`; RSS samples show `{84730: 53795536896, client: 28033024}` at peak.
- `owlmlx.peak_resident_set_bytes` includes the wrapper plus MLX child process
  tree; RSS samples show `{85266: 36765696, 85353: 59728084992}` at peak.
- `owlmlx.first_token_strategy` uses regex matching on the generated
  `"text": " OK."` stdout line, not the leading diagnostic JSON.
- Both runtimes have `completed_request_count = 2` and `failure_count = 0`.
- `commands.json` records `external_pid_file` for `omlx` and the regex
  first-token strategy for `owlmlx`.

HTTP verification:

```text
GET /v1/runtime/comparative-evidence -> HTTP/1.1 200 OK
GET /v1/runtime/comparative-evidence/history -> HTTP/1.1 200 OK
```

Captured output:

```text
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt
```

Cleanup:

```text
lsof -n -iTCP:8063 -sTCP:LISTEN || true
# no output

lsof -n -iTCP:8064 -sTCP:LISTEN || true
# no output
```
