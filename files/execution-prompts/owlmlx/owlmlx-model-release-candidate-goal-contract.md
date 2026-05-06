# Goal Contract

## Goal ID

`owlmlx-model-release-candidate-gate`

## Title

Move `owlmlx` from technical-preview runtime to model release-candidate gate.

## Success Definition

- The mainline model set has runtime-owned, OwlOps-consumable evidence for
  repeated `load -> generate -> unload -> reload`.
- The mainline model set is:
  - `Qwen3.6-27B`
  - `Qwen3.6-35B-A3B`
  - `gemma-4-31B-it`
- OwlOps records and renders TTFT, throughput, wall time, peak RSS, memory
  headroom, and failure count for the model matrix.
- Reference-runtime comparison against `oMLX` / `vMLX` exists where a same-host
  same-model path is available.
- Failures, degraded readiness, memory reclaim issues, and runtime blockers are
  ledgered rather than explained only in chat.
- OwlCoda remains a consumer of frozen runtime truth and does not become the
  owner of runtime capability claims.

## Blocked Definition

- A mainline model cannot produce repeated live runtime evidence on this host
  and the failure is narrowed to a concrete artifact, adapter, memory, or
  runtime blocker.
- OwlOps cannot consume the upstream evidence schema because the schema or
  transport is missing from `owlmlx`.
- A required reference-runtime comparison is impossible on this host and the
  unavailable reference path is recorded explicitly.

## Hard Rules

- Do not claim release-ready, parity, replacement, equivalent, production-grade,
  wins, beats, or matches.
- Do not kill legacy listeners on `8001` or `8009`.
- Do not mark `DeepSeek-V4-Flash-2bit-DQ` as supported or mainline pass.
- Do not let OwlCoda own runtime truth.
- Do not promote test-only or chat-only evidence into the model matrix.
- Preserve unknown and blocked states when runtime evidence is missing.

## Out Of Scope

- Public marketing release.
- OwlCoda launch UX implementation.
- Killing or migrating old services.
- Long DeepSeek V4 generation unless a live desktop lane explicitly authorizes
  it.
- Turning all downloaded model artifacts into supported models.

## Current Truth

- `release-readiness-backlog.md` is closed at `7 / 7`, which permits
  technical-preview operation but does not prove application release readiness.
- `owlmlx` technical preview has served on `127.0.0.1:8066` and currently
  exposes a runtime-owned model visibility surface.
- `GET /v1/openai/models` on the technical-preview surface previously exposed
  `Qwen3.6-27B`, `Qwen3.6-35B-A3B`, `gemma-4-31B-it`, and
  `gpt-oss-120b-MXFP4-Q4`; the `gpt-oss-120b-MXFP4-Q4` base artifact has since
  been intentionally deleted.
- `gpt-oss-120b-MXFP4-Q4` is removed from the active RC gate and the runtime
  visibility registry; it is neither a mainline capability target nor the
  heavyweight pressure canary.
- `DeepSeek-V4-Flash-2bit-DQ` is a local 284.3B-parameter, about-90G
  experimental adapter optimization candidate, not a mainline supported model.
- `model-release-candidate-program.md` defines the post-technical-preview
  model RC gate.

## Remaining Gaps

- No runtime-owned model release-candidate evidence schema exists yet.
- No model release-candidate JSONL ledger exists yet.
- No operator entry exists for dry-run or repeated model RC records.
- OwlOps does not yet have an upstream Model RC wire/schema surface to consume.
- The three mainline candidates have not yet completed the repeated live
  `load -> generate -> unload -> reload` matrix.
- DeepSeek V4 is not yet registered on the technical-preview visibility surface
  and must remain in an experimental lane.

## Dominant Next Gap

Introduce the smallest runtime-owned Model RC evidence schema, ledger, operator
entry, and read-only latest/history surface so OwlOps can consume the same
fields before live performance runs begin.
