# owlmlx Model RC A1 Qwen3.6-27B Live Record Handoff

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

Outcome:

`owlmlx_model_release_candidate_a1_qwen36_27b_live_record_introduced`

## 1. Verdict

`Qwen3.6-27B` now has the first non-dry-run
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
Qwen3.6-27B
```

Artifact path:

```text
/Users/yeemio/AI/Agent/models/Qwen3.6-27B
```

Evidence directory:

```text
files/evidence/owlmlx/model-release-candidates/20260505T071836Z-qwen36-27b
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
first_token_latency_ms = 1145.8
tokens_per_second = 5.395
wall_clock_ms = 19759.742
peak_resident_set_bytes = 54348431360
memory_headroom_bytes = 83090522112
output_sanity_label = valid_text
```

Known caveat:

The short prompt generation used `max_tokens = 16`. The model returned valid
text, but the output was length-truncated inside a reasoning trace. This record
proves the live runtime path and measurements; it does not prove model answer
quality.

## 4. HTTP Surface

The technical-preview server was restarted in tmux session
`owlmlx-8066-preview` with:

```text
--model-release-candidate-ledger-path files/evidence/owlmlx/model-release-candidates/20260505T071836Z-qwen36-27b/ledger.jsonl
```

Live checks:

```text
GET /v1/runtime/model-release-candidates
latest_model = Qwen3.6-27B
latest_verdict = needs_optimization
latest_repeat_count = 2
latest_failure_count = 0

GET /v1/runtime/model-release-candidates/history
history_surface = owlmlx.model_release_candidate_record_history
history_status = available
history_count = 1
```

Post-run runtime state:

```text
active_model_id = None
model_count = 0
readiness = degraded
```

## 5. Code Changes

This lane added the live operator path:

- `scripts/runtime_model_release_candidate.py`
  - `run-live-http-mainline`
  - live HTTP load/generate/unload/reload runner
  - process-tree RSS sampler
  - artifact writing
- `owlmlx/runtime/technical_preview.py`
  - mounts `OWLMLX_MODEL_RELEASE_CANDIDATE_LEDGER_PATH`
- `scripts/runtime_technical_preview_server.py`
  - adds `--model-release-candidate-ledger-path`
- `tests/test_model_release_candidate_surface.py`
  - fake HTTP live runner coverage
- `tests/test_runtime_technical_preview_server.py`
  - technical-preview ledger env coverage

## 6. Verification

```text
pytest -q tests/test_model_release_candidate_surface.py
14 passed

pytest -q tests/test_runtime_technical_preview_server.py tests/test_model_release_candidate_surface.py
18 passed

python3 -m py_compile scripts/runtime_model_release_candidate.py
OK

python3 -m py_compile owlmlx/runtime/technical_preview.py scripts/runtime_technical_preview_server.py scripts/runtime_model_release_candidate.py
OK

git diff --check
clean
```

## 7. Remaining Gaps

- OwlOps B1 must consume/render this live record.
- Same-host reference comparison for this model is still missing.
- A2 should run the next memory-exclusive mainline lane:
  `Qwen3.6-35B-A3B`.
- DeepSeek pressure lane must still wait until the mainline observation loop is
  stable.

## 8. Non-Goals Preserved

This lane did not:

- run DeepSeek
- run or restore `gpt-oss-120b-MXFP4-Q4`
- kill `8001` or `8009`
- modify OwlOps or OwlCoda
- claim release-ready, parity, replacement, equivalent, or production-grade
