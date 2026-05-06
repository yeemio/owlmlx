# owlmlx Model Release Candidate A3 - Live Mainline gemma-4-31B-it Record

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

## Objective

Produce the third mainline non-dry-run Model RC evidence record.

Target model:

- `gemma-4-31B-it`

Expected outcome:

`owlmlx_model_release_candidate_a3_gemma_4_31b_it_live_record_introduced`

## Required Context

Read first:

1. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-goal-contract.md`
2. `docs/source-of-truth/model-release-candidate-program.md`
3. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a1-qwen36-27b-live-record-handoff.md`
4. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a2-live-mainline-qwen36-35b-a3b.md`
5. `docs/source-of-truth/release-readiness-execution-plan.md`

Current runtime expectation:

- `owlmlx` technical preview may already be listening at `127.0.0.1:8066`
- old `8001` and `8009` listeners must not be killed
- only one heavyweight live run may execute at a time

## Coordination Gate

Do not start A3 until A2 has either:

- produced a valid `Qwen3.6-35B-A3B` Model RC record, or
- hard-blocked with a written ledger and handoff.

If OwlOps is consuming a specific latest view, coordinate before remounting
`8066`.

## Scope

Run one focused live mainline lane:

`gemma-4-31B-it` repeated `load -> generate -> unload -> reload`.

Append at least one validated `owlmlx.model_release_candidate_record` and serve
it through:

- `GET /v1/runtime/model-release-candidates`
- `GET /v1/runtime/model-release-candidates/history`

## Required Measurements

Capture and preserve:

- load result
- generation result
- unload result
- reload result
- repeat count
- failure count
- first-token latency
- tokens/sec
- wall-clock time
- process-tree peak RSS
- memory headroom
- output sanity label
- artifact directory under `files/evidence/owlmlx/model-release-candidates/`

## Suggested Command Shape

Use the live runner introduced in A1:

```bash
EVIDENCE_DIR="files/evidence/owlmlx/model-release-candidates/<timestamp>-gemma-4-31b-it"

.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path "$EVIDENCE_DIR/ledger.jsonl" \
  run-live-http-mainline \
  --runtime-url http://127.0.0.1:8066 \
  --model-id gemma-4-31B-it \
  --artifact-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --prompt "Write one short sentence about local AI." \
  --max-tokens 64 \
  --repeats 2 \
  --memory-gb 58 \
  --evidence-dir "$EVIDENCE_DIR" \
  --http-timeout-s 1200 \
  --rss-sample-interval-s 0.5
```

If Gemma uses a different answer style than Qwen, preserve the observed output
shape rather than forcing it into a Qwen-style sanity label.

## Cumulative Ledger

After the run, merge the mainline records into one cumulative ledger:

```bash
.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl \
  merge-ledgers \
  files/evidence/owlmlx/model-release-candidates/20260505T071836Z-qwen36-27b/ledger.jsonl \
  files/evidence/owlmlx/model-release-candidates/<a2-dir>/ledger.jsonl \
  "$EVIDENCE_DIR/ledger.jsonl" \
  --replace
```

Then restart `8066` with:

```bash
--model-release-candidate-ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl
```

## Tests And Verification

Run:

```bash
pytest -q tests/test_model_release_candidate_surface.py
pytest -q tests/test_runtime_technical_preview_server.py
pytest -q tests/test_runtime_server.py -k "model_release_candidate or runtime_status"
python3 -m py_compile \
  owlmlx/model_release_candidate_schema.py \
  owlmlx/model_release_candidate_record.py \
  owlmlx/model_release_candidate_ledger.py \
  scripts/runtime_model_release_candidate.py \
  owlmlx/runtime/server.py \
  owlmlx/runtime/technical_preview.py \
  scripts/runtime_technical_preview_server.py
git diff --check
```

Live verification:

- `curl http://127.0.0.1:8066/v1/openai/models` includes `gemma-4-31B-it`
- live run appends a validated Model RC record
- latest/history surfaces return HTTP 200 against the mounted ledger
- no stale loaded model remains after completion
- `8001` and `8009` remain untouched

## Out Of Scope

Do not:

- run DeepSeek
- run or restore `gpt-oss-120b-MXFP4-Q4`
- touch OwlOps / OwlCoda / `/Users/yeemio/AI/Agent`
- run concurrently with any other heavyweight model load
- kill `8001` or `8009`
- claim release-ready, parity, replacement, equivalent, or production-grade

## Final Report

Report:

- outcome label
- changed files
- artifact directory
- appended record verdict
- measured metrics
- output sanity label
- cumulative ledger state
- HTTP latest/history result
- post-run loaded-model state
- tests and command results
- next recommended lane
