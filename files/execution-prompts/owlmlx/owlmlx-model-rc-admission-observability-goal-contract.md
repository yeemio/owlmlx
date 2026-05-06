# Goal Contract

## Goal ID

`owlmlx-model-rc-admission-observability`

## Title

Move Model RC runs from budget-only evidence to supervised model-level
admission evidence.

## Success Definition

- `owlmlx` exposes an explicit host-pressure sample action that does not load a
  model.
- `model-load-admission` can move from `host_pressure_sample_missing` to a
  concrete `admit`, `warn`, or `blocked` projection after sampling.
- The Model RC runner records host-pressure and admission-before-load artifacts
  before each supervised repeat load.
- A blocked admission stops before `/v1/load`.
- OwlOps can consume the distinction between budget projection and live
  admission decision without inventing runtime truth.

## Blocked Definition

- Runtime cannot refresh host-pressure truth without executing a model load.
- The runner cannot call the sampler before `/v1/load`.
- A live route returns malformed or unavailable admission truth and the exact
  missing signal is recorded.

## Hard Rules

- Do not kill legacy listeners on `8001` or `8009`.
- Do not claim release-ready, parity, replacement, equivalent,
  production-grade, wins, beats, or matches.
- Do not run heavy model loads in this contract round.
- Do not make status reads shell out implicitly.
- Do not sample private Metal allocator state; this is host-visible pressure
  only.

## Out Of Scope

- OwlOps UI changes.
- OwlCoda release entry work.
- DeepSeek long generation.
- Pressure-ranked eviction.
- Automatic restart, quarantine, or remediation.

## Current Truth

- `RuntimeKernel.load_model(...)` samples host pressure before backend load.
- `/v1/runtime/status` exposes cached `host_pressure`.
- `/v1/runtime/model-load-admission` projects per-model admission from
  visibility, profile, Model RC peak RSS, budget, host pressure, and recovery
  barriers.
- Live 8066 showed Qwen35/Gemma budget projection could be `fits` while
  admission stayed `unknown` because host pressure had not been sampled.

## Remaining Gaps

- No explicit operator action refreshes host-pressure truth without loading a
  model.
- The Model RC runner does not record host-pressure/admission preflight
  artifacts before each repeat load.
- OwlOps cannot distinguish stale/unknown admission from sampled admission in
  live runner evidence.

## Dominant Next Gap

Introduce explicit host-pressure sampling plus Model RC runner pre-load
admission artifacts, without running heavy models.
