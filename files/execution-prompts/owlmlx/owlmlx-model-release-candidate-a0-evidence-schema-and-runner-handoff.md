# owlmlx Model Release Candidate A0 Handoff

Outcome:
`owlmlx_model_release_candidate_a0_evidence_schema_introduced_pending_live_runs`

## Verdict

`surface_closed_pending_live_runs`

A0 closed the evidence-schema gap for the Model RC gate. It did not run any
heavy live model test and did not mark any model as `pass`.

## What Landed

- Goal contract:
  `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-goal-contract.md`
- Source-of-truth program:
  `docs/source-of-truth/model-release-candidate-program.md`
- DeepSeek lane truth:
  `docs/source-of-truth/deepseek-v4-flash-adapter-optimization-candidate.md`
- Schema:
  `owlmlx/model_release_candidate_schema.py`
- Record builder:
  `owlmlx/model_release_candidate_record.py`
- Append-only JSONL ledger:
  `owlmlx/model_release_candidate_ledger.py`
- Operator:
  `scripts/runtime_model_release_candidate.py`
- HTTP:
  - `GET /v1/runtime/model-release-candidates`
  - `GET /v1/runtime/model-release-candidates/history`
- Tests:
  `tests/test_model_release_candidate_surface.py`

## A0 Matrix Semantics

The dry-run matrix emits four records:

- `Qwen3.6-27B`: `lane = mainline`, `verdict = needs_optimization`
- `Qwen3.6-35B-A3B`: `lane = mainline`, `verdict = needs_optimization`
- `gemma-4-31B-it`: `lane = mainline`, `verdict = needs_optimization`
- `DeepSeek-V4-Flash-2bit-DQ`: `lane = flagship_experimental`,
  `visibility_status = not_registered`, `verdict = experimental_only`

`gpt-oss-120b-MXFP4-Q4` is not emitted in the active gate matrix. It has been
removed from local model assets and runtime visibility, and does not block the
RC goal.

All operation result blocks are `not_run` in A0. This is intentional: A0 is the
schema and ledger round, not a live performance round.

## Verification

Commands run:

```bash
python3 -m py_compile \
  owlmlx/model_release_candidate_schema.py \
  owlmlx/model_release_candidate_record.py \
  owlmlx/model_release_candidate_ledger.py \
  scripts/runtime_model_release_candidate.py \
  owlmlx/runtime/server.py

python3 scripts/runtime_model_release_candidate.py dry-run-matrix \
  --created-at 2026-05-05T00:00:00Z

pytest -q tests/test_model_release_candidate_surface.py
pytest -q tests/test_runtime_server.py -k "model_release_candidate or runtime_status"
pytest -q tests/test_public_surface_contract.py

python3 scripts/runtime_model_release_candidate.py \
  --ledger-path /tmp/owlmlx-model-rc-a0-ledger.jsonl \
  append-dry-run-matrix --created-at 2026-05-05T00:00:00Z
python3 scripts/runtime_model_release_candidate.py \
  --ledger-path /tmp/owlmlx-model-rc-a0-ledger.jsonl latest
python3 scripts/runtime_model_release_candidate.py \
  --ledger-path /tmp/owlmlx-model-rc-a0-ledger.jsonl history

git diff --check
```

Results:

- `tests/test_model_release_candidate_surface.py`: 13 passed
- `tests/test_runtime_server.py -k "model_release_candidate or runtime_status"`:
  1 passed, 40 deselected
- `tests/test_public_surface_contract.py`: 12 passed
- py_compile: passed
- operator append/latest/history smoke: passed
- `git diff --check`: clean

## Discipline

- No OwlOps, OwlCoda, or `/Users/yeemio/AI/Agent` files were modified.
- No listener on `8001` or `8009` was stopped.
- No DeepSeek live generation was run.
- No release-ready / parity / replacement / equivalent / production-grade claim
  was made.
- DeepSeek remains experimental-only.

## Next Recommended Lane

`owlmlx-model-release-candidate-a1-live-mainline-qwen36-27b`

Purpose:

- run a real repeated live `load -> generate -> unload -> reload` sequence for
  `Qwen3.6-27B`
- append a non-dry-run Model RC record to the ledger
- expose it through the new latest/history HTTP surfaces
- hand the same ledger to OwlOps for first observation rendering

Do not start with DeepSeek; begin with the smallest useful visible mainline
model to validate the live record path.
