# owlmlx Model Release Candidate A1 - Live Mainline Qwen3.6-27B Record

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

## Objective

Produce the first non-dry-run Model RC evidence record for a visible mainline
model.

Target model:

- `Qwen3.6-27B`

Expected outcome:

`owlmlx_model_release_candidate_a1_qwen36_27b_live_record_introduced`

## Required Context

Read first:

1. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-goal-contract.md`
2. `docs/source-of-truth/model-release-candidate-program.md`
3. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a0-evidence-schema-and-runner-handoff.md`
4. `docs/source-of-truth/runtime-status-schema.md` section `19`
5. `docs/source-of-truth/public-surface.md`

Current runtime expectation:

- `owlmlx` technical preview may already be listening at `127.0.0.1:8066`
- old `8001` and `8009` listeners must not be killed
- this is the only lane allowed to load a model while the parallel OwlOps B1
  consumer lane is running

## Scope

Run one focused live mainline lane:

`Qwen3.6-27B` repeated `load -> generate -> unload -> reload`.

The lane must append at least one validated
`owlmlx.model_release_candidate_record` to the Model RC ledger and serve it
through:

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
- first-token latency if available; otherwise preserve `null` and explain why
- tokens/sec if available; otherwise preserve `null` and explain why
- wall-clock time
- process-tree peak RSS if available; otherwise preserve `null` and explain why
- memory headroom if available; otherwise preserve `null` and explain why
- output sanity label
- artifact directory under `files/evidence/owlmlx/model-release-candidates/`

## Implementation Guidance

Prefer extending `scripts/runtime_model_release_candidate.py` with a narrow
live command rather than hand-editing JSONL records.

Suggested command shape:

```bash
python3 scripts/runtime_model_release_candidate.py \
  --ledger-path files/evidence/owlmlx/model-release-candidates/live-ledger.jsonl \
  run-live-http-mainline \
  --runtime-url http://127.0.0.1:8066 \
  --model-id Qwen3.6-27B \
  --prompt "Write one short sentence about local AI." \
  --max-tokens 16 \
  --repeats 2 \
  --evidence-dir files/evidence/owlmlx/model-release-candidates/<timestamp>-qwen36-27b
```

If the current HTTP surface cannot expose true TTFT or process-tree RSS, do not
invent those values. Preserve `null` and record the blocker. This round may
still be valuable as a live record if it proves load/generate/unload/reload and
records the missing metric signals honestly.

## OwlOps Boundary

Do not modify OwlOps in this lane.

The output must be consumable by OwlOps by reading the Model RC latest/history
surface or the JSONL ledger.

## Tests And Verification

Run:

```bash
pytest -q tests/test_model_release_candidate_surface.py
pytest -q tests/test_runtime_server.py -k "model_release_candidate or runtime_status"
python3 -m py_compile \
  owlmlx/model_release_candidate_schema.py \
  owlmlx/model_release_candidate_record.py \
  owlmlx/model_release_candidate_ledger.py \
  scripts/runtime_model_release_candidate.py \
  owlmlx/runtime/server.py
git diff --check
```

Live verification:

- `curl http://127.0.0.1:8066/v1/openai/models` includes `Qwen3.6-27B`
- live run appends a validated Model RC record
- latest/history surfaces return HTTP 200 against the live ledger
- no stale process owned by this lane remains after completion

## Out Of Scope

Do not:

- run DeepSeek
- run or optimize `gpt-oss-120b-MXFP4-Q4`
- touch OwlOps / OwlCoda / `/Users/yeemio/AI/Agent`
- run concurrently with any other heavyweight model load
- kill `8001` or `8009`
- claim release-ready, parity, replacement, equivalent, or production-grade

## Final Report

Report:

- outcome label
- changed files
- artifact directory
- exact appended record verdict
- which metrics are measured vs null/blocked
- HTTP latest/history result
- tests and command results
- next recommended lane
