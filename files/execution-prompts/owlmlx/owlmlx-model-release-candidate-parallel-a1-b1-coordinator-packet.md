# owlmlx Model RC Parallel A1/B1 Coordinator Packet

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

Outcome target:

`owlmlx_model_release_candidate_parallel_a1_b1_started`

## 1. Goal

Advance `owlmlx` from Model RC A0 schema/dry-run status to the first live
mainline Model RC record plus an OwlOps consumer workspace that can render the
same evidence.

This packet intentionally uses two lanes only.

## 2. Parallelism Rule

Parallel work is allowed only when it does not create unified-memory contention.

Therefore:

- Lane A may load and unload `Qwen3.6-27B`.
- Lane B must not load any model, start any heavy runtime, or run DeepSeek.
- No lane may run `DeepSeek-V4-Flash-2bit-DQ` while Lane A is executing a
  live mainline run.
- `8001` and `8009` must not be killed.

## 3. Lane A - owlmlx Live Mainline Record

Prompt:

`files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a1-live-mainline-qwen36-27b.md`

Owner:

owlmlx executor, preferably Codex when Computer Use or live process monitoring
is useful.

Objective:

Produce the first non-dry-run `owlmlx.model_release_candidate_record` for
`Qwen3.6-27B`.

Required result:

- live repeated `load -> generate -> unload -> reload`
- at least two repeats unless the lane hard-blocks honestly
- Model RC JSONL ledger append
- HTTP latest/history surfaces return the record
- artifact directory under
  `files/evidence/owlmlx/model-release-candidates/`
- exact measured/null metric split preserved

## 4. Lane B - OwlOps Consumer Workspace

Prompt:

`files/execution-prompts/owlmlx/owlops-model-release-candidate-b1-consumer-workspace.md`

Owner:

OwlOps executor. The prompt is archived here because owlmlx is the upstream
truth owner; the implementation belongs in `/Users/yeemio/AI/gitrep/owlops`.

Objective:

Build the first OwlOps Model RC consumer surface against owlmlx Model RC
latest/history or the JSONL ledger.

Required result:

- no model loading
- no local metric recomputation that overwrites owlmlx truth
- render dry-run / missing-live / live-record states distinctly
- preserve `pass`, `needs_optimization`, `blocked`, and `experimental_only`
  labels as upstream truth
- display TTFT, tok/s, wall time, RSS, headroom, failure count, and blockers
  when present
- show `gpt-oss-120b-MXFP4-Q4` as retired/absent if it appears only in
  historical evidence

## 5. Coordination Gate

Lane A and Lane B may start together.

Closeout requires both:

- Lane A produces a live or honestly blocked Qwen3.6-27B record.
- Lane B can consume and render the current owlmlx Model RC record/history
  without inventing runtime truth.

DeepSeek pressure lane starts only after this closeout.

## 6. Forbidden Claims

No lane may claim:

- release-ready
- parity
- replacement
- equivalent
- production-grade
- supported DeepSeek

The honest near-term status remains Model RC in progress.
