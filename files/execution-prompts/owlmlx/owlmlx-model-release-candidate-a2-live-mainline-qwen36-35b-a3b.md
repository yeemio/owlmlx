# owlmlx Model Release Candidate A2 - Live Mainline Qwen3.6-35B-A3B Record

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

## Objective

Produce the second non-dry-run Model RC evidence record for a visible mainline
model.

Target model:

- `Qwen3.6-35B-A3B`

Expected outcome:

`owlmlx_model_release_candidate_a2_qwen36_35b_a3b_live_record_introduced`

## Required Context

Read first:

1. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-goal-contract.md`
2. `docs/source-of-truth/model-release-candidate-program.md`
3. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a1-qwen36-27b-live-record-handoff.md`
4. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-parallel-a1-b1-coordinator-packet.md`
5. `docs/source-of-truth/release-readiness-execution-plan.md`

Current runtime expectation:

- `owlmlx` technical preview may already be listening at `127.0.0.1:8066`
- B1 OwlOps may still be consuming the A1 `Qwen3.6-27B` latest/history surface
- old `8001` and `8009` listeners must not be killed

## Coordination Gate

Do not start this live run while OwlOps B1 is actively validating the A1 latest
surface unless the coordinator explicitly confirms that B1 no longer needs the
A1-only latest view.

Once B1 confirms it has consumed A1, A2 may remount `8066` to the A2 ledger or
to a cumulative Model RC ledger.

## Scope

Run one focused live mainline lane:

`Qwen3.6-35B-A3B` repeated `load -> generate -> unload -> reload`.

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
EVIDENCE_DIR="files/evidence/owlmlx/model-release-candidates/<timestamp>-qwen36-35b-a3b"

.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path "$EVIDENCE_DIR/ledger.jsonl" \
  run-live-http-mainline \
  --runtime-url http://127.0.0.1:8066 \
  --model-id Qwen3.6-35B-A3B \
  --artifact-path /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B \
  --prompt "Write one short sentence about local AI." \
  --max-tokens 64 \
  --repeats 2 \
  --memory-gb 67 \
  --evidence-dir "$EVIDENCE_DIR" \
  --http-timeout-s 1200 \
  --rss-sample-interval-s 0.5
```

Use `max_tokens = 64` rather than `16` so the output-sanity label is less
likely to be dominated by a truncated reasoning trace. If the model still
returns a length-truncated `<think>` trace, preserve
`output_sanity_label = reasoning_trace_truncated` and do not claim answer
quality.

## HTTP Mount

After the run, build or refresh a cumulative ledger so OwlOps can see A1 and
A2 in one history view:

```bash
.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl \
  merge-ledgers \
  files/evidence/owlmlx/model-release-candidates/20260505T071836Z-qwen36-27b/ledger.jsonl \
  "$EVIDENCE_DIR/ledger.jsonl" \
  --replace
```

Then restart `8066` with the cumulative ledger path:

```bash
--model-release-candidate-ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl
```

Then capture:

```bash
curl -sS http://127.0.0.1:8066/v1/runtime/model-release-candidates
curl -sS http://127.0.0.1:8066/v1/runtime/model-release-candidates/history
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

- `curl http://127.0.0.1:8066/v1/openai/models` includes `Qwen3.6-35B-A3B`
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
- HTTP latest/history result
- post-run loaded-model state
- tests and command results
- next recommended lane
