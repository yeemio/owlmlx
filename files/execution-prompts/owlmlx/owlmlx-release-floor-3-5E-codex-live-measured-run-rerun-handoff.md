# owlmlx Release Floor 3.5E Codex Live Measured Run Rerun Handoff

> Date: 2026-04-28
> Outcome label: `owlmlx_release_floor_3_5E_live_measured_record_closed_recommended`
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Evidence directory: `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/`

## Verdict

3.5E produced a fresh, closeout-grade `verdict_grade = "measured"` record for
`owlmlx + omlx` on the same host, with process-tree / external-PID RSS and
token-aware first-token detection.

Floor `3.5` closeout is recommended. This handoff does not start floors `3.6`
or `3.7` and does not make release, parity, replacement, or production-grade
claims.

## Host / Ports / PIDs / Python

- Host class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- macOS: `26.4.1`
- Machine: `arm64`
- RAM: `137438953472` bytes
- CPU count: `18`
- Python path: `/opt/homebrew/opt/python@3.14/bin/python3.14`
- OMLX port: `8063`
- OMLX server PID: `84730`
- HTTP verification port: `8064`
- Uvicorn PID during verification: `86178`

## Evidence Directory

```text
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/
```

Key files:

```text
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/runner-config.json
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/omlx-server.pid
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-run-notes.md
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/manifest.json
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/commands.json
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/summary.md
```

## Runner Config

```json
{
  "owlmlx": {
    "runtime_version": "unknown-local-checkout",
    "argv": [
      "python3",
      "scripts/runtime_large_weight_first_smoke.py",
      "--specimen-path",
      "{model_path}",
      "--memory-gb",
      "80",
      "--prompt",
      "{prompt}",
      "--max-tokens",
      "{max_tokens}",
      "--include-known-venvs"
    ],
    "env": {
      "PYTHONPATH": "."
    },
    "cwd": "/Users/yeemio/AI/gitrep/owlmlx",
    "tokens_method": "max_tokens",
    "first_token_strategy": "regex:\"text\":\\s*\"[^\"]+\"",
    "timeout_s": 240.0
  },
  "reference": {
    "runtime_id": "omlx",
    "runtime_version": "0.3.5-probe-venv",
    "argv": [
      "python3",
      "-c",
      "import json, sys, urllib.request; model=sys.argv[1]; prompt=sys.argv[2]; max_tokens=int(sys.argv[3]); temperature=float(sys.argv[4]); payload=dict(model=model,messages=[dict(role='user',content=prompt)],max_tokens=max_tokens,temperature=temperature,stream=False); req=urllib.request.Request('http://127.0.0.1:8063/v1/chat/completions', data=json.dumps(payload).encode(), headers=dict([('Content-Type','application/json')])); data=json.loads(urllib.request.urlopen(req, timeout=180).read().decode()); print(data['choices'][0]['message']['content'] or '')",
      "{model_id}",
      "{prompt}",
      "{max_tokens}",
      "{temperature}"
    ],
    "env": {},
    "cwd": "/Users/yeemio/AI/gitrep/owlmlx",
    "tokens_method": "max_tokens",
    "first_token_strategy": "first_nonempty_chunk",
    "external_pid_file": "files/evidence/owlmlx/comparative-evidence/20260428T004500Z/omlx-server.pid",
    "timeout_s": 180.0
  }
}
```

## Commands And Results

Stable checks:

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
# 27 passed in 0.18s

pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
# 37 passed in 4.19s

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
# printed help successfully
```

OMLX server:

```bash
/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/omlx serve \
  --model-dir /Users/yeemio/AI/Agent/models \
  --host 127.0.0.1 \
  --port 8063 \
  --no-cache \
  --max-process-memory disabled \
  --max-model-memory disabled \
  --log-level warning
```

Readiness:

```text
lsof -n -iTCP:8063 -sTCP:LISTEN
Python 84730 ... TCP 127.0.0.1:8063 (LISTEN)

curl -sS http://127.0.0.1:8063/v1/models
returned Qwen3.6-27B, Qwen3.6-35B-A3B, gemma-4-31B-it, gpt-oss-120b-MXFP4-Q4
```

Measured runner:

```bash
python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl \
  run-measured-short-prompt \
  --evidence-dir files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run \
  --runner-config files/evidence/owlmlx/comparative-evidence/20260428T004500Z/runner-config.json \
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

```text
recorded_at = 2026-04-28T00:46:35Z
surface = owlmlx.comparative_evidence_record
version = v1
verdict_grade = measured
verdict_text = measured: owlmlx tokens_per_second 0.1613 vs omlx tokens_per_second 0.5778 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short
runtimes = owlmlx, omlx
evidence_pointer = files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/manifest.json
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

Stdout:

```text
owlmlx attempt 1 text = " OK."
owlmlx attempt 2 text = " OK."
omlx attempt 1 stdout = OK
omlx attempt 2 stdout = OK
```

## HTTP Curl Summary

Served with:

```bash
PYTHONPATH=. \
OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH=files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl \
python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
  --factory --host 127.0.0.1 --port 8064 --log-level warning
```

Both fresh-ledger routes returned `HTTP/1.1 200 OK`:

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

Captured curl output:

```text
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt
files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt
```

## Sanity Checks

1. `omlx.peak_resident_set_bytes` is GB-scale and includes the live server:
   `53823569920` bytes. Peak RSS sample includes PID `84730` at
   `53795536896` bytes plus the HTTP client.
2. `owlmlx.peak_resident_set_bytes` includes wrapper plus descendants:
   `59764850688` bytes. Peak sample includes wrapper PID `85266` and child
   PID `85353` at `59728084992` bytes.
3. `owlmlx.first_token_latency_ms` is not diagnostic JSON timing; config uses
   `regex:"text":\s*"[^"]+"`, and stdout line 162 contains `"text": " OK."`.
4. Both runtimes have `completed_request_count = 2` and `failure_count = 0`.
5. `run/*.rss.jsonl` contains per-PID process-tree samples with
   `tracked_root_pids`, `per_pid_rss_bytes`, and `tick_total_rss_bytes`.
6. `run/commands.json` records `external_pid_file` for `omlx` and the
   regex first-token strategy for `owlmlx`.
7. `run/summary.md` states the measured verdict and GB-scale process-tree
   peak RSS values.

## Cleanup Evidence

After verification, all live ports were released:

```text
lsof -n -iTCP:8063 -sTCP:LISTEN || true
# no output

lsof -n -iTCP:8064 -sTCP:LISTEN || true
# no output
```

No lane-owned `runtime_large_weight_first_smoke.py`, `mlx_lm_runner`,
`runtime_comparative_evidence.py`, `omlx serve`, or uvicorn process remained
after cleanup.

## Closeout Recommendation

Real closeout-grade `verdict_grade = "measured"` exists and is served by both
fresh-ledger HTTP routes.

Recommendation:

```text
proceed_to_3_5_closeout_review_and_ledger_flip
```

This 3.5E lane did not itself edit `release-readiness-backlog.md`; it provides
the closeout-grade live evidence for the coordinator/reviewer closeout step.

No release, parity, replacement, or production-grade claim was made.
