# owlmlx 3.5C Live Measured Run Notes

> Date: 2026-04-27
> Evidence directory: `files/evidence/owlmlx/comparative-evidence/20260427T133207Z/`
> OMLX port: `8061`
> HTTP verification port: `8062`

## Initial State

- Stable checks passed before live run:
  - `pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py`
  - `pytest -q tests/test_runtime_comparative_evidence_measured_runner.py`
  - `pytest -q tests/test_runtime_server.py -k "comparative_evidence"`
  - `python3 -m py_compile owlmlx/comparative_evidence_schema.py owlmlx/comparative_evidence_record.py owlmlx/comparative_evidence_ledger.py owlmlx/comparative_evidence_runner.py scripts/runtime_comparative_evidence.py owlmlx/runtime/server.py`
  - `python3 scripts/runtime_comparative_evidence.py run-measured-short-prompt --help`
- Host:
  - `hw.memsize = 137438953472`
  - `hw.model = Mac17,6`
  - `hw.machine = arm64`
  - `hw.ncpu = 18`
  - `macOS 26.4.1`
- Fresh ports checked before use:
  - `8061`: no listener
  - `8062`: no listener

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
- `repeats`: `2`

## Commands

OMLX server:

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

Measured runner:

```bash
python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/20260427T133207Z/live-ledger.jsonl \
  run-measured-short-prompt \
  --evidence-dir files/evidence/owlmlx/comparative-evidence/20260427T133207Z/run \
  --runner-config files/evidence/owlmlx/comparative-evidence/20260427T133207Z/runner-config.json \
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
