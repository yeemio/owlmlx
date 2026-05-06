# owlmlx Model RC Remaining Lanes Coordinator Packet

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

Outcome target:

`owlmlx_model_release_candidate_remaining_lanes_packet_ready`

## 1. Current State

A1 is complete:

- `Qwen3.6-27B`
- `repeat_count = 2`
- `failure_count = 0`
- verdict `needs_optimization`
- live ledger:
  `files/evidence/owlmlx/model-release-candidates/20260505T071836Z-qwen36-27b/ledger.jsonl`

B1 OwlOps consumer lane may still be running. Do not disrupt B1 by remounting
`8066` unless the coordinator confirms B1 has consumed A1 or can read the
cumulative ledger.

## 2. Remaining Model Lanes

The remaining work is:

- A2: `Qwen3.6-35B-A3B`
- A3: `gemma-4-31B-it`
- D1: `DeepSeek-V4-Flash-2bit-DQ`

`gpt-oss-120b-MXFP4-Q4` is retired and must not re-enter.

## 3. Execution Order

Recommended order:

1. Finish B1 consumer read of A1.
2. Run A2 `Qwen3.6-35B-A3B`.
3. Merge A1 + A2 into
   `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`.
4. Run A3 `gemma-4-31B-it`.
5. Merge A1 + A2 + A3 into the cumulative ledger.
6. Run D1 DeepSeek pressure/adaptation lane only after no mainline model is
   loaded and no OwlOps latest-view validation is in flight.

## 4. Memory Rule

Only one heavyweight live model lane may run at a time.

Never overlap:

- Qwen live runs
- Gemma live runs
- DeepSeek pressure runs
- comparative evidence runs

OwlOps B lanes may run in parallel only if they stay read-only and do not load
models.

## 5. Prompt Paths

Use these archived prompts:

- `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a2-live-mainline-qwen36-35b-a3b.md`
- `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a3-live-mainline-gemma-4-31b-it.md`
- `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-d1-deepseek-v4-flash-2bit-dq-pressure-adapter.md`

## 6. Closeout Target

The mainline Model RC loop is closeout-ready when:

- A1, A2, and A3 all have live records
- OwlOps renders all three mainline records from the cumulative ledger
- each mainline record is `pass` or `needs_optimization` with explicit blockers
- no record hides failures or null metrics

DeepSeek D1 remains pressure/adaptation evidence and does not block mainline
Model RC closeout unless the coordinator explicitly changes the gate.
