# owlmlx Model RC A3 gemma-4-31B-it Live Record Handoff

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

Outcome:

`owlmlx_model_release_candidate_a3_gemma_4_31b_it_live_record_introduced`

## 1. Verdict

`gemma-4-31B-it` now has a non-dry-run
`owlmlx.model_release_candidate_record`.

Record verdict:

```text
needs_optimization
```

This is intentionally not `pass` because OwlOps observation and same-host
reference runtime comparison remain open.

## 2. Live Run

Runtime:

```text
http://127.0.0.1:8066
```

Model:

```text
gemma-4-31B-it
```

Artifact path:

```text
/Users/yeemio/AI/Agent/models/gemma-4-31B-it
```

Evidence directory:

```text
files/evidence/owlmlx/model-release-candidates/20260505T074135Z-gemma-4-31b-it
```

Operation sequence:

```text
load -> stream generate -> unload -> reload -> stream generate -> unload
```

Result:

```text
repeat_count = 2
failure_count = 0
load_result.status = pass
generation_result.status = pass
unload_result.status = pass
reload_result.status = pass
```

## 3. Metrics

Measured:

```text
first_token_latency_ms = 2179.717
tokens_per_second = 6.178
wall_clock_ms = 36577.866
peak_resident_set_bytes = 56211668992
memory_headroom_bytes = 81227284480
output_sanity_label = valid_text
```

## 4. HTTP Surface

The A3 lane did not remount or restart `8066`, per coordination override.
Therefore, the live `GET /v1/runtime/model-release-candidates` and
`GET /v1/runtime/model-release-candidates/history` probes returned HTTP 200
against the currently mounted A1 ledger, not the A3 local ledger.

Captured current-mounted surface:

```text
http-latest.json latest_model = Qwen3.6-27B
http-history.json history_count = 1
```

Captured local A3 ledger surface through the operator:

```text
local-ledger-latest.json latest_model = gemma-4-31B-it
local-ledger-history.json history_count = 1
```

Coordinator action still needed:

```text
merge A1/A2/A3 ledgers, then remount 8066 with the cumulative ledger
```

## 5. Post-Run Runtime State

Post-run `GET /healthz`:

```text
active_model_id = null
model_count = 0
readiness = degraded
```

Port check:

```text
8001 listening, untouched
8009 listening, untouched
8066 listening, untouched
```

Stale process check:

```text
no A3 runtime_model_release_candidate process remained after completion
no gemma-4-31B-it command remained in the post-run process capture
```

## 6. Verification

```text
pytest -q tests/test_model_release_candidate_surface.py
17 passed

pytest -q tests/test_runtime_technical_preview_server.py
4 passed

pytest -q tests/test_runtime_server.py -k "model_release_candidate or runtime_status"
1 passed, 40 deselected

python3 -m py_compile \
  owlmlx/model_release_candidate_schema.py \
  owlmlx/model_release_candidate_record.py \
  owlmlx/model_release_candidate_ledger.py \
  scripts/runtime_model_release_candidate.py \
  owlmlx/runtime/server.py \
  owlmlx/runtime/technical_preview.py \
  scripts/runtime_technical_preview_server.py
OK

git diff --check
clean
```

## 7. Non-Goals Preserved

This lane did not:

- run DeepSeek
- run or restore `gpt-oss-120b-MXFP4-Q4`
- touch OwlOps / OwlCoda / `/Users/yeemio/AI/Agent`
- kill `8001` or `8009`
- restart or remount `8066`
- edit shared docs, cumulative ledger, execution plan, or code
- claim release-ready, parity, replacement, equivalent, or production-grade
