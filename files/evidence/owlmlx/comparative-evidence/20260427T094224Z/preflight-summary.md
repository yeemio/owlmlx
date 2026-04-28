# owlmlx 3.5A0 Comparative Evidence Preflight Summary

> Date: 2026-04-27
> Outcome label: `owlmlx_release_floor_3_5A0_harness_runner_missing`
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Evidence directory: `files/evidence/owlmlx/comparative-evidence/20260427T094224Z/`

## Host And Python

- Host class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- `sysctl hw.memsize`: `137438953472`
- `sysctl hw.model`: `Mac17,6`
- `sysctl hw.machine`: `arm64`
- `sysctl hw.ncpu`: `18`
- `python3`: `/opt/homebrew/opt/python@3.14/bin/python3.14`
- `platform`: `macOS-26.4.1-arm64-arm-64bit-Mach-O`

## Stable Checks

- `pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py`
  - `27 passed in 0.12s`
- `pytest -q tests/test_runtime_server.py -k "comparative_evidence"`
  - `4 passed, 37 deselected in 0.29s`
- `python3 -m py_compile owlmlx/comparative_evidence_schema.py owlmlx/comparative_evidence_record.py owlmlx/comparative_evidence_ledger.py scripts/runtime_comparative_evidence.py owlmlx/runtime/server.py`
  - passed with no output

## Reference Runtime Availability

| Runtime | Command | Python module | Repo / venv | Live result |
| --- | --- | --- | --- | --- |
| `omlx` | `/opt/homebrew/bin/omlx` exists; Homebrew script points at `0.3.4` | current `python3.14`: `ModuleNotFoundError`; probe venv imports `omlx 0.3.5` | `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/omlx` | `omlx serve --model-dir /Users/yeemio/AI/Agent/models --port 8059 ...` served `/v1/models` and returned chat completion `OK` for `gemma-4-31B-it` |
| `vmlx` | not on global PATH, but probe venv has `vmlx`, `vmlx-engine`, `vmlx-serve` | probe venv imports `vmlx_engine 1.0.3` and `mlx_lm 0.31.2` | `/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe/.venv/` and `/Users/yeemio/AI/gitrep/vmlx` | `vmlx list` found 4 models; `vmlx info` identified `gemma-4-31B-it`; `vmlx doctor` passed inference test and generated 10 tokens |

Current `python3.14` import probe:

```text
omlx import_failed ModuleNotFoundError No module named 'omlx'
vmlx import_failed ModuleNotFoundError No module named 'vmlx'
mlx_lm import_failed ModuleNotFoundError No module named 'mlx_lm'
```

Probe venv import evidence:

```text
/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python
omlx import_ok 0.3.5
mlx_lm import_ok 0.31.2
mlx import_ok unknown

/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe/.venv/bin/python
vmlx_engine import_ok 1.0.3
mlx_lm import_ok 0.31.2
mlx import_ok unknown
```

## Selected Workload

- `workload_class`: `single_prompt_short`
- prompt: `Reply with exactly OK.`
- `prompt_set_hash`: `sha256:b4d50a67a784a449e0c763c401bb9f95fb37804dff5765d8b4f95fd202eb7d77`
- `decode_max_tokens`: `2`
- `decode_temperature`: `0.0`
- `model_id`: `gemma-4-31B-it`
- `model_quantization`: `full_precision_unquantized`
- model path: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- model size: `58G`
- serving budget used for preflight record: `85899345920` bytes

Local model inventory under `/Users/yeemio/AI/Agent/models`:

```text
gemma-4-31B-it        58G
Qwen3.6-27B           52G
Qwen3.6-35B-A3B       67G
gpt-oss-120b-MXFP4-Q4 58G
```

## Live Runtime Evidence

`omlx`:

```text
curl http://127.0.0.1:8059/v1/models
{"object":"list","data":[{"id":"Qwen3.6-27B",...},{"id":"Qwen3.6-35B-A3B",...},{"id":"gemma-4-31B-it",...},{"id":"gpt-oss-120b-MXFP4-Q4",...}]}

curl http://127.0.0.1:8059/v1/chat/completions ...
... "content":"OK" ...
```

`vmlx`:

```text
vmlx list /Users/yeemio/AI/Agent/models
Found 4 model(s) in /Users/yeemio/AI/Agent/models:
  Qwen3.6-27B
  Qwen3.6-35B-A3B
  gemma-4-31B-it
  gpt-oss-120b-MXFP4-Q4

vmlx doctor /Users/yeemio/AI/Agent/models/gemma-4-31B-it
Inference: PASS - Generated 10 tokens: 'world! world! world! world! world!'
ALL CHECKS PASSED
```

`owlmlx`:

```text
PYTHONPATH=. python3 scripts/runtime_large_weight_specimen_gate.py --specimen-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it --include-known-venvs
summary.smoke_ready=true
selected mlx environment: omlx-probe-venv (/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python, default_metal)
```

An owlmlx first-smoke attempt was started with:

```text
PYTHONPATH=. perl -e 'alarm shift; exec @ARGV' 600 python3 scripts/runtime_large_weight_first_smoke.py --specimen-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it --memory-gb 80 --prompt 'Reply with exactly OK.' --max-tokens 2 --include-known-venvs
```

After about `133s`, the process had not returned generated output and was stopped by the operator. Observed process evidence before stop:

```text
86724 ... scripts/runtime_large_weight_first_smoke.py ... elapsed 02:13
87791 ... python -m owlmlx.runtime.mlx_lm_runner ... RSS 2587568 KB elapsed 02:12
```

## Comparative Evidence Surface

An isolated preflight ledger was written at:

```text
files/evidence/owlmlx/comparative-evidence/20260427T094224Z/preflight-ledger.jsonl
```

It contains one honest `verdict_grade = "inconclusive"` record:

```text
verdict_text = inconclusive: harness_runner_missing on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short
```

The record was served through a real uvicorn process:

```text
PYTHONPATH=. OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH=files/evidence/owlmlx/comparative-evidence/20260427T094224Z/preflight-ledger.jsonl python3 -m uvicorn owlmlx.runtime.server:create_fake_app --factory --host 127.0.0.1 --port 8060 --log-level warning

lsof -n -iTCP:8060 -sTCP:LISTEN
Python 5289 ... TCP 127.0.0.1:8060 (LISTEN)

curl -sS http://127.0.0.1:8060/v1/runtime/comparative-evidence
... "verdict_grade":"inconclusive" ...

curl -sS http://127.0.0.1:8060/v1/runtime/comparative-evidence/history
... "ledger_status":"available" ...
```

After verification, port `8060` was released:

```text
lsof -n -iTCP:8060 -sTCP:LISTEN
# no output
```

The temporary `omlx` server on port `8059` was also stopped and the port released.

## Verdict

No `verdict_grade = "measured"` record exists from this preflight.

Reference runtime availability is no longer the dominant blocker on this host: `omlx` and `vmlx` can both reach the selected local model path. The dominant blocker is that `scripts/runtime_comparative_evidence.py` only exposes `append-rejected-record`, `latest`, and `history`; it has no measured-run subcommand that can execute two repeat runs per runtime, collect first-token latency / throughput / peak RSS / wall-clock, preserve raw artifacts, and append a valid measured record.

Smallest next executor recommendation:

- implement a narrow `append-measured-record` or `run-measured-short-prompt` harness path for one model and one prompt, using the existing schema and ledger
- include two repeat runs each for `owlmlx` plus either `omlx` or `vmlx`
- record stdout/stderr, process samples, commands, first-token latency, throughput, wall-clock, peak RSS, completed count, and failure causes
- only then consider `verdict_grade = "measured"`
