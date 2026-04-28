# owlmlx Release Floor 3.5A0 Codex Live Comparative Evidence Preflight Handoff

> Date: 2026-04-27
> Outcome label: `owlmlx_release_floor_3_5A0_harness_runner_missing`
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Evidence: `files/evidence/owlmlx/comparative-evidence/20260427T094224Z/preflight-summary.md`

## Verdict

No `verdict_grade = "measured"` record exists.

This host can see and partly run the reference-runtime side: `omlx` served the selected model and returned `OK`; `vmlx` identified the same model and passed its doctor inference test. The measured closure still cannot be emitted because the current runtime-owned operator entry, `scripts/runtime_comparative_evidence.py`, only supports `append-rejected-record`, `latest`, and `history`; it does not run measured workloads or collect the required repeat-run metrics/artifacts.

## Host / Python / Repo

- Host class: `Mac17,6-arm64-macOS-26.4.1-128GB`
- Repo path: `/Users/yeemio/AI/gitrep/owlmlx`
- `python3`: `/opt/homebrew/opt/python@3.14/bin/python3.14`
- `platform`: `macOS-26.4.1-arm64-arm-64bit-Mach-O`
- `machine`: `arm64`
- RAM: `137438953472` bytes

## Runtime Availability Matrix

| Runtime | Availability | Evidence |
| --- | --- | --- |
| `owlmlx` | partial | specimen gate says `smoke_ready=true` and selects `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python`; first-smoke attempt did not return generated output before operator stop at about `133s` |
| `omlx` | available via command and probe venv | `/opt/homebrew/bin/omlx`; `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/omlx`; probe venv imports `omlx 0.3.5`; server returned `OK` for `gemma-4-31B-it` |
| `vmlx` | available via probe venv, not global PATH | `/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe/.venv/bin/vmlx`; imports `vmlx_engine 1.0.3`; `vmlx doctor` passed inference on `gemma-4-31B-it` |

## Workload

- `workload_class`: `single_prompt_short`
- prompt: `Reply with exactly OK.`
- `prompt_set_hash`: `sha256:b4d50a67a784a449e0c763c401bb9f95fb37804dff5765d8b4f95fd202eb7d77`
- `model_id`: `gemma-4-31B-it`
- model path: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- `model_quantization`: `full_precision_unquantized`
- `decode_max_tokens`: `2`
- `decode_temperature`: `0.0`
- `serving_budget_bytes`: `85899345920`

## Commands And Key Output

Stable checks:

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
# 27 passed in 0.12s

pytest -q tests/test_runtime_server.py -k "comparative_evidence"
# 4 passed, 37 deselected in 0.29s

python3 -m py_compile \
  owlmlx/comparative_evidence_schema.py \
  owlmlx/comparative_evidence_record.py \
  owlmlx/comparative_evidence_ledger.py \
  scripts/runtime_comparative_evidence.py \
  owlmlx/runtime/server.py
# passed
```

Availability checks:

```bash
python3 scripts/runtime_comparative_evidence.py --help
# subcommands: append-rejected-record, latest, history

command -v omlx
# /opt/homebrew/bin/omlx

command -v vmlx
# no output

python3 import probe
# omlx import_failed ModuleNotFoundError
# vmlx import_failed ModuleNotFoundError
# mlx_lm import_failed ModuleNotFoundError
```

Reference live checks:

```bash
/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/omlx serve --model-dir /Users/yeemio/AI/Agent/models --host 127.0.0.1 --port 8059 --no-cache --max-process-memory disabled --max-model-memory disabled --log-level warning

curl -sS http://127.0.0.1:8059/v1/models
# returned Qwen3.6-27B, Qwen3.6-35B-A3B, gemma-4-31B-it, gpt-oss-120b-MXFP4-Q4

curl -sS http://127.0.0.1:8059/v1/chat/completions ...
# returned assistant content "OK"

/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe/.venv/bin/vmlx doctor /Users/yeemio/AI/Agent/models/gemma-4-31B-it
# Inference: PASS - Generated 10 tokens
```

HTTP surface check:

```bash
PYTHONPATH=. OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH=files/evidence/owlmlx/comparative-evidence/20260427T094224Z/preflight-ledger.jsonl \
  python3 -m uvicorn owlmlx.runtime.server:create_fake_app --factory --host 127.0.0.1 --port 8060 --log-level warning

curl -sS http://127.0.0.1:8060/v1/runtime/comparative-evidence
# returned verdict_grade=inconclusive

curl -sS http://127.0.0.1:8060/v1/runtime/comparative-evidence/history
# returned ledger_status=available
```

Port cleanup:

```bash
lsof -n -iTCP:8059 -sTCP:LISTEN || true
# no output after cleanup

lsof -n -iTCP:8060 -sTCP:LISTEN || true
# no output after cleanup
```

## Ledger / HTTP Record

An isolated preflight ledger exists:

```text
files/evidence/owlmlx/comparative-evidence/20260427T094224Z/preflight-ledger.jsonl
```

It contains one honest record:

```text
verdict_grade = "inconclusive"
verdict_text = "inconclusive: harness_runner_missing on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short"
```

This is not a release-floor closure record. It is a preflight record proving the HTTP surface can serve the latest ledger entry while preserving that measured evidence is still missing.

## Blocker

Exact blocker:

```text
harness_runner_missing
```

Why:

- reference runtime availability is sufficient for a next measured attempt
- local weights are present for the selected shared model
- HTTP ledger serving works
- but the runtime-owned comparative evidence operator has no measured runner path and no required repeat-run metric/artifact collection

## Smallest Next Executor

Assign one code-lane executor for floor `3.5B`:

- add a narrow measured runner for `single_prompt_short`
- support exactly one local model path and one prompt set first
- run two repeats for `owlmlx` plus one reference runtime (`omlx` first, `vmlx` optional second)
- capture raw stdout/stderr, process samples, re-run commands, first-token latency, throughput, wall-clock, peak RSS, completed count, and failure causes
- append `verdict_grade="measured"` only if all measured-record criteria in `comparative-evidence-harness-contract.md` are satisfied
