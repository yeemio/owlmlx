# owlmlx Release Floor 3.5C Codex Live Measured Run Review Handoff

> Date: 2026-04-27
> Outcome label: `owlmlx_release_floor_3_5C_measured_runner_needs_fix`
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Evidence directory: `files/evidence/owlmlx/comparative-evidence/20260427T133443Z/`

## Verdict

The 3.5B runner can execute the live `owlmlx + omlx` workload and can append a
schema-valid HTTP-served record with `verdict_grade = "measured"`.

However, this live review rejects the record as 3.5 closeout evidence because
the runner's measured fields are not measuring the actual runtime processes:

- `peak_resident_set_bytes` samples only the immediate subprocess PID, not the
  runtime child process or external server process.
- `omlx` is invoked through a short HTTP client while the real `omlx` server is
  already running on port `8061`; the record therefore reports the client RSS
  instead of the server RSS.
- `owlmlx` uses `scripts/runtime_large_weight_first_smoke.py`, whose first
  stdout chunk is diagnostic gate JSON, so `first_token_latency_ms` is not the
  latency to the first generated token.

Floor `3.5` should remain open. Do not flip `release-readiness-backlog.md`.

## Host / Ports / Python

- Host class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- RAM: `137438953472` bytes
- Machine: `arm64`
- CPU count: `18`
- macOS: `26.4.1`
- Repo: `/Users/yeemio/AI/gitrep/owlmlx`
- `python3`: `/opt/homebrew/opt/python@3.14/bin/python3.14`
- `omlx` live port: `8061`
- HTTP verification port: `8062`

## Stable Checks

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
# 27 passed in 0.15s

pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
# 28 passed in 3.03s

pytest -q tests/test_runtime_server.py -k "comparative_evidence"
# 4 passed, 37 deselected in 0.40s

python3 -m py_compile \
  owlmlx/comparative_evidence_schema.py \
  owlmlx/comparative_evidence_record.py \
  owlmlx/comparative_evidence_ledger.py \
  owlmlx/comparative_evidence_runner.py \
  scripts/runtime_comparative_evidence.py \
  owlmlx/runtime/server.py
# passed with no output

python3 scripts/runtime_comparative_evidence.py run-measured-short-prompt --help
# subcommand help printed successfully
```

## Evidence Directories

First attempt with invalid reference argv:

```text
files/evidence/owlmlx/comparative-evidence/20260427T133207Z/
```

The first attempt produced `verdict_grade = "rejected"` because the Python
client command contained JSON braces that prevented placeholder substitution:

```text
ValueError: invalid literal for int() with base 10: '{max_tokens}'
```

Corrected fair live attempt:

```text
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/
```

Key files:

```text
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/runner-config.json
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/live-run-notes.md
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/live-ledger.jsonl
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/run/manifest.json
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/run/summary.md
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/run/commands.json
```

## Runner Config

The corrected config is:

```text
files/evidence/owlmlx/comparative-evidence/20260427T133443Z/runner-config.json
```

It runs:

- `owlmlx`: `python3 scripts/runtime_large_weight_first_smoke.py --specimen-path {model_path} --memory-gb 80 --prompt {prompt} --max-tokens {max_tokens} --include-known-venvs`
- `omlx`: a short Python HTTP client against `http://127.0.0.1:8061/v1/chat/completions`, with `{model_id}`, `{prompt}`, `{max_tokens}`, and `{temperature}` passed as separate argv tokens

## Live Commands

`omlx` server:

```bash
/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/omlx serve \
  --model-dir /Users/yeemio/AI/Agent/models \
  --host 127.0.0.1 \
  --port 8061 \
  --no-cache \
  --max-process-memory disabled \
  --max-model-memory disabled \
  --log-level warning
```

Port and model readiness:

```text
lsof -n -iTCP:8061 -sTCP:LISTEN
Python 59803 ... TCP 127.0.0.1:8061 (LISTEN)

curl -sS http://127.0.0.1:8061/v1/models
returned Qwen3.6-27B, Qwen3.6-35B-A3B, gemma-4-31B-it, gpt-oss-120b-MXFP4-Q4
```

Measured runner:

```bash
python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/20260427T133443Z/live-ledger.jsonl \
  run-measured-short-prompt \
  --evidence-dir files/evidence/owlmlx/comparative-evidence/20260427T133443Z/run \
  --runner-config files/evidence/owlmlx/comparative-evidence/20260427T133443Z/runner-config.json \
  --host-class Mac17,6-arm64-macOS-26.4.1-128GB \
  --workload-class single_prompt_short \
  --model-id gemma-4-31B-it \
  --model-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --model-quantization full_precision_unquantized \
  --prompt "Reply with exactly OK." \
  --prompt-set-hash sha256:b4d50a67a784a449e0c763c401bb9f95fb37804dff5765d8b4f95fd202eb7d77 \
  --decode-max-tokens 2 \
  --decode-temperature 0.0 \
  --serving-budget-bytes 85899345920 \
  --repeats 2
```

## Ledger Record Summary

The corrected attempt appended this record:

```text
recorded_at = 2026-04-27T13:36:12Z
surface = owlmlx.comparative_evidence_record
version = v1
verdict_grade = measured
verdict_text = measured: owlmlx tokens_per_second 0.1544 vs omlx tokens_per_second 0.7785 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short
runtimes = owlmlx, omlx
```

Runtime fields in the record:

```text
owlmlx completed_request_count = 2
owlmlx failure_count = 0
owlmlx first_token_latency_ms = 12985.742937482428
owlmlx throughput_tokens_per_second = 0.154445778966152
owlmlx peak_resident_set_bytes = 36978688

omlx completed_request_count = 2
omlx failure_count = 0
omlx first_token_latency_ms = 7213.219500015839
omlx throughput_tokens_per_second = 0.7784931366077724
omlx peak_resident_set_bytes = 28065792
```

Stdout confirms the actual generation succeeded:

```text
owlmlx attempt 1 text = " OK."
owlmlx attempt 2 text = " OK."
omlx attempt 1 stdout = OK
omlx attempt 2 stdout = OK
```

## HTTP Curl Summary

The isolated ledger was served with:

```bash
PYTHONPATH=. \
OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH=files/evidence/owlmlx/comparative-evidence/20260427T133443Z/live-ledger.jsonl \
python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
  --factory --host 127.0.0.1 --port 8062 --log-level warning
```

Both routes returned `HTTP/1.1 200 OK`:

```text
GET /v1/runtime/comparative-evidence
surface = owlmlx.comparative_evidence_record
version = v1
verdict_grade = measured
runtimes = owlmlx, omlx

GET /v1/runtime/comparative-evidence/history
surface = owlmlx.comparative_evidence_record_history
version = v1
ledger_status = available
records[0].verdict_grade = measured
```

## Live Review Finding

The record is schema-valid and HTTP-served, but it is not a closeout-grade
runtime measurement.

Process evidence:

```text
omlx server process:
PID 59803 ... RSS 47906992 KB ... /Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/omlx serve ... --port 8061

HTTP verification process:
PID 69906 ... RSS 65568 KB ... python3 -m uvicorn owlmlx.runtime.server:create_fake_app ... --port 8062
```

Mismatch:

- record `omlx.peak_resident_set_bytes = 28065792` bytes, but live `omlx`
  server RSS was `47906992 KB`; the runner measured the small client command,
  not the serving runtime process
- record `owlmlx.peak_resident_set_bytes = 36978688` bytes, but `owlmlx`
  generation stdout shows persistent child PIDs (`68767`, `68973`) and the
  runner only sampled the wrapper command PID
- record `owlmlx.first_token_latency_ms` starts at first non-empty stdout;
  for this command, that is gate JSON, not generated token text

## Cleanup Evidence

After verification, both live ports were released:

```text
lsof -n -iTCP:8061 -sTCP:LISTEN || true
# no output

lsof -n -iTCP:8062 -sTCP:LISTEN || true
# no output
```

No runner, first-smoke, MLX child, `omlx serve`, or uvicorn process remained
after cleanup.

## Decision

Real `verdict_grade = "measured"` exists on disk and was served by HTTP, but it
is not accepted as a truthful closeout record because key metrics do not
measure the actual runtime processes.

Closeout recommendation:

```text
do_not_close_floor_3_5_yet
```

Exact blocker:

```text
measured_runner_process_tree_sampling_invalid
first_token_latency_observed_from_diagnostic_stdout_not_generation_token
```

Next executor recommendation:

- send back to code lane to fix the measured runner before another blind live
  run
- runner must sample the real process tree or accept explicit runtime PIDs
  for `owlmlx` child and `omlx` server
- runner must make first-token timing observe generated-token output, not
  diagnostic preamble stdout
- after that, rerun Codex desktop live measurement using the same workload
  invariants and isolated ledger

No release, parity, replacement, or production-grade claim was made.
