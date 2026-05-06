# OwlOps Model RC B1 Consumer Workspace

Repo: `/Users/yeemio/AI/gitrep/owlops`

Upstream repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

Expected outcome:

`owlops_model_release_candidate_b1_consumer_workspace_introduced`

## 1. Objective

Create the first OwlOps consumer workspace for owlmlx Model RC evidence.

This lane does not produce runtime truth. It consumes owlmlx truth from:

- `GET /v1/runtime/model-release-candidates`
- `GET /v1/runtime/model-release-candidates/history`
- the JSONL ledger when explicitly configured

## 2. Required Context

Read in owlmlx first:

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/model-release-candidate-program.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a0-evidence-schema-and-runner-handoff.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/owlmlx-model-release-candidate-gpt-oss-120b-retirement-handoff.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/owlmlx-model-release-candidate-parallel-a1-b1-coordinator-packet.md`

Then inspect the OwlOps source-of-truth and existing comparative-evidence or
runtime-truth consumer patterns before editing.

## 3. Scope

Build a lightweight Model RC observation surface that can render:

- model id
- lane
- visibility status
- verdict
- load / generation / unload / reload result status
- repeat count
- failure count
- first-token latency
- tokens per second
- wall-clock time
- peak RSS
- memory headroom
- output sanity label
- blockers
- artifact path or upstream evidence path

## 4. Honest State Handling

Render these states distinctly:

- `upstream_unavailable`
- `dry_run_only`
- `live_record_available`
- `live_record_blocked`
- `metric_missing`
- `retired_model_absent`

`gpt-oss-120b-MXFP4-Q4` must not be resurrected as a current row. If historical
evidence mentions it, label it as retired / historical only.

## 5. Hard Rules

- Do not load models.
- Do not start `owlmlx`.
- Do not kill `8001`, `8009`, or `8066`.
- Do not calculate replacement metrics locally and present them as runtime
  truth.
- Do not mark a model `pass` unless upstream owlmlx record says `pass`.
- Do not claim release-ready, parity, replacement, equivalent, or
  production-grade.
- Do not edit `/Users/yeemio/AI/gitrep/owlmlx` from this lane.

## 6. Acceptance Criteria

The lane is complete when OwlOps has:

- a documented Model RC consumer surface or workspace
- tests or smoke checks for the unavailable and available upstream cases
- sample rendering against current owlmlx A0 data
- ability to refresh after Lane A publishes a live Qwen3.6-27B record
- a handoff that states exactly which upstream fields are consumed and which
  remain missing

## 7. Verification

Run the narrow OwlOps tests that cover the new consumer surface.

If a live owlmlx server is reachable at `127.0.0.1:8066`, run one read-only
HTTP smoke:

```bash
curl -sS http://127.0.0.1:8066/v1/runtime/model-release-candidates
curl -sS http://127.0.0.1:8066/v1/runtime/model-release-candidates/history
```

If the server is not reachable, preserve `upstream_unavailable`; do not start
the server from this lane.

## 8. Final Report

Report:

- outcome label
- changed files
- tests / smoke checks
- upstream source used
- rendered states
- whether Lane A live record is already visible
- exact blockers for B2
