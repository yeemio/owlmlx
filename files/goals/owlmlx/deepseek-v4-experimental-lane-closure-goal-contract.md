# Goal Contract: DeepSeek V4 Experimental Lane Closure

> Status: active goal contract
> Created: 2026-05-17
> Loop driver: `goal-driven-project-loop`

## Goal ID

`owlmlx-deepseek-v4-experimental-lane-closure`

## Title

Close the DeepSeek V4 experimental lane honestly without promoting it to
supported serving.

## Success Definition

This goal succeeds when the DeepSeek V4 lane has evidence for:

1. D1 repeatability under the adopted `messages` prompt policy.
2. D2 metrics ledger over the selected prompt/token ladder.
3. D3 checkpoint/MTP inspection with explicit capability conclusion.
4. D4 clean pre-load rejection / failure isolation when MTP is unavailable.

Success does not mean `owlmlx supports DeepSeek V4`; it means the experimental
lane is bounded, measurable, and honest.

## Blocked Definition

The goal is blocked only if:

- the local DeepSeek V4 artifact is unavailable,
- the isolated adapter fork is unavailable,
- 8066 runtime health cannot be observed for D4 when health-stability proof is
  required, or
- a D4 reject would require loading the model before the missing checkpoint is
  known.

## Hard Rules

- Do not register DeepSeek V4 on the default model surface.
- Do not claim DeepSeek V4 supported serving.
- Do not adopt `ds4.c` in this lane.
- Do not run MTP load/generate when D3 says the checkpoint is absent/stripped.
- Keep evidence under `files/evidence/owlmlx/deepseek-v4/`.

## Out Of Scope

- 24h Session KV soak.
- Gemma 4 resident MTP.
- Qwen native MTP / NextN evaluation.
- Public release claims.

## Current Truth

- D1 passed: `20260517T-d1-full-ladder-adopted-messages-policy.jsonl`.
- D2 passed: `20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl`.
- D3 passed as inspection gate:
  `20260517T-d3-mtp-checkpoint-inspection.jsonl`.
- D3 conclusion: `capability_conclusion=mtp_checkpoint_not_available`,
  `missingReason=mtp_weights_absent_or_stripped`.
- 8066 health is observable on the current host and currently has no active
  model.

## Remaining Gaps

1. D4 clean pre-load reject / failure isolation.
2. Optional D4 source-of-truth closeout after evidence lands.
3. Later D5 only if a new artifact or adapter fork changes D3.

## Dominant Next Gap

`D4 clean pre-load reject / failure isolation`

D4 is the dominant gap because D3 proved the MTP checkpoint is unavailable. The
next truthful behavior is not another generation benchmark; it is proving that
the unavailable MTP path is rejected before load and does not dirty runtime
health.
