# owlmlx Model Release Candidate A0 - Evidence Schema And Runner

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

## Objective

Introduce the first runtime-owned model release-candidate evidence layer for
the post-technical-preview phase.

This round must make the model adaptation / performance program executable
without pretending any model has already passed the release-candidate gate.

## Required Context

Read first:

1. `docs/source-of-truth/model-release-candidate-program.md`
2. `docs/source-of-truth/deepseek-v4-flash-adapter-optimization-candidate.md`
3. `docs/source-of-truth/public-surface.md`
4. `docs/source-of-truth/runtime-status-schema.md`
5. `docs/source-of-truth/release-readiness-execution-plan.md`

Current expected live server:

- `owlmlx` technical preview may be running at `http://127.0.0.1:8066`
- legacy services on `8001` / `8009` must not be killed by this lane

## Scope

Build the smallest honest evidence surface for model release-candidate work.

The surface should be able to represent:

- mainline candidate models:
  - `Qwen3.6-27B`
  - `Qwen3.6-35B-A3B`
  - `gemma-4-31B-it`
- flagship experimental model:
  - `DeepSeek-V4-Flash-2bit-DQ`

## Implementation Requirements

Add a runtime-owned schema/module for model release-candidate records.

The record must include at minimum:

- `surface`
- `version`
- `created_at`
- `model_id`
- `lane`
- `runtime_url`
- `host_class`
- `artifact_path`
- `visibility_status`
- `load_result`
- `generation_result`
- `unload_result`
- `reload_result`
- `repeat_count`
- `failure_count`
- `first_token_latency_ms`
- `tokens_per_second`
- `wall_clock_ms`
- `peak_resident_set_bytes`
- `memory_headroom_bytes`
- `output_sanity_label`
- `owlops_observation_path`
- `verdict`
- `blockers`

Allowed `lane` values:

- `mainline`
- `flagship_experimental`

Allowed `visibility_status` values:

- `visible`
- `blocked`
- `not_registered`
- `unknown`

Allowed `verdict` values:

- `pass`
- `needs_optimization`
- `blocked`
- `experimental_only`

Forbidden verdict vocabulary:

- `parity`
- `replacement`
- `equivalent`
- `production_ready`
- `beats`
- `wins`

Add an operator entry under `scripts/` that can:

- emit a dry-run matrix record for the current candidate list
- append records to a repo-local JSONL ledger under `files/evidence/owlmlx/model-release-candidates/`
- read the latest record
- print a history envelope

If you add an HTTP surface, it must be read-only and must return either:

- the latest validated model release-candidate record/history, or
- an explicit `still_blocked` / empty-ledger envelope

## DeepSeek Rules

Do not run a heavy DeepSeek live generation in A0 unless the coordinator
explicitly re-authorizes a live desktop lane.

A0 should only encode the current DeepSeek truth:

- artifact exists under
  `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ`
- `total_parameters = 284333146519`
- `total_size = 96520315996`
- current technical-preview visibility is not exposed on `8066`
- verdict must be `experimental_only`, `needs_optimization`, or `blocked`
- never mark DeepSeek as mainline `pass`

## gpt-oss-120b Rule

`gpt-oss-120b-MXFP4-Q4` is removed from the active Model RC gate. Do not emit
an A0 dry-run record for it and do not keep a `mainline_heavy` lane only for
that model. Its local base artifact has been deleted and it is no longer in the
runtime visibility registry.

## OwlOps Contract

The schema names in this round become the upstream contract for OwlOps.

Do not make OwlOps compute hidden metrics locally. OwlOps should consume the
wire/schema fields and render them. If a field is unknown, preserve `unknown`
instead of inventing a value.

## Tests

Add focused tests for:

- schema validation
- allowed enum values
- forbidden verdict vocabulary rejection
- mainline model record serialization
- DeepSeek experimental record serialization
- empty ledger / missing ledger behavior
- operator dry-run output
- any HTTP route you add

Run at minimum:

```bash
pytest -q tests/test_model_release_candidate*
python3 -m py_compile <new modules and scripts>
git diff --check
```

If you touch `owlmlx/runtime/server.py`, also run:

```bash
pytest -q tests/test_runtime_server.py -k "model_release_candidate or runtime_status"
```

## Out Of Scope

Do not:

- run long DeepSeek live generation
- mark any model release-ready
- touch OwlOps, OwlCoda, or `/Users/yeemio/AI/Agent`
- kill listeners on `8001` or `8009`
- change existing comparative-evidence verdict semantics
- weaken public-surface banned vocabulary rules

## Required Final Report

Report:

- outcome label
- changed files
- exact records/surfaces introduced
- tests and command results
- whether OwlOps can consume the schema
- whether any model is actually `pass` (expected answer for A0: no, unless a
  real repeated live run was explicitly authorized and completed)
- next recommended live lane

Expected honest A0 outcome:

`owlmlx_model_release_candidate_a0_evidence_schema_introduced_pending_live_runs`
