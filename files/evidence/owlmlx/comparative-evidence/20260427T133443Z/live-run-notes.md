# owlmlx 3.5C Live Measured Run Notes - Corrected Config Attempt

> Date: 2026-04-27
> Evidence directory: `files/evidence/owlmlx/comparative-evidence/20260427T133443Z/`
> OMLX port: `8061`
> HTTP verification port: `8062`

This is the fair live attempt after the first `20260427T133207Z` runner-config
attempt failed because the one-token Python `-c` command contained JSON braces
that prevented runner placeholder substitution. The corrected reference argv
passes `{model_id}`, `{prompt}`, `{max_tokens}`, and `{temperature}` as
separate argv tokens.

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

## Measured Runner Command

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

## Result

The corrected runner invocation appended and printed a
`verdict_grade = "measured"` record:

```text
recorded_at = 2026-04-27T13:36:12Z
evidence_pointer = files/evidence/owlmlx/comparative-evidence/20260427T133443Z/run/manifest.json
owlmlx completed_request_count = 2
omlx completed_request_count = 2
verdict_text = measured: owlmlx tokens_per_second 0.1544 vs omlx tokens_per_second 0.7785 on host_class=Mac17,6-arm64-macOS-26.4.1-128GB, workload_class=single_prompt_short
```

HTTP verification against the isolated ledger returned `200 OK` for both:

```text
GET /v1/runtime/comparative-evidence
GET /v1/runtime/comparative-evidence/history
```

## Live Review Caveat

The emitted measured-grade record is **not recommended for 3.5 closeout**.
The live process monitor showed the runner measurement does not cover the
actual runtime processes:

- `omlx` serving process on port `8061` was observed at `RSS 47906992 KB`
  during verification, while the ledger's `omlx.peak_resident_set_bytes`
  is only `28065792` bytes; the runner measured the short Python HTTP client,
  not the long-lived `omlx` server.
- `owlmlx` generation spawns a persistent child such as `pid=68767` /
  `pid=68973`; the ledger's `owlmlx.peak_resident_set_bytes` is only around
  `36 MB`, while the live process view in the earlier attempt observed the
  MLX runner child in the tens of GB. The runner sampled only the wrapper
  subprocess PID.
- `owlmlx.first_token_latency_ms` is based on the first non-empty stdout chunk.
  For `scripts/runtime_large_weight_first_smoke.py`, the first stdout chunk is
  diagnostic gate JSON, not the first generated token.

This means the runner can emit a schema-valid `measured` record, but the record
does not yet satisfy the harness contract's runtime measurement intent for peak
RSS and first-token latency.

## Cleanup

Both live ports were released after verification:

```text
lsof -n -iTCP:8061 -sTCP:LISTEN || true
# no output

lsof -n -iTCP:8062 -sTCP:LISTEN || true
# no output
```
