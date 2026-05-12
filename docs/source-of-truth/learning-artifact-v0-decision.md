# owlmlx Learning Artifact v0 Decision

> Status: narrow decision
> Created: 2026-05-12
> Scope: future OwlCoda public-release gate; not current OwlCoda work

## Decision

`learning_artifact_v0` is a runtime registration shape, not a new product lane.

Data shape:

- primary: conversation trace with tool-use events and final outcome
- required provenance: model id, base artifact id, timestamp or run id, caller,
  prompt/task context, tool calls/results, and acceptance or rejection signal
- preference pairs are derived later only when two comparable outcomes exist

Learning shape:

- v0 supported path: LoRA adapter over an existing base model
- v0 fallback path: explicit no-op adapter verdict with reason and evidence path
- DPO, RLHF, and continual pretrain are not in scope for v0

Runtime registration shape:

- register the result through the existing artifact metadata layout under
  `$MODELS_ROOT/{model-id}/tuned/{run-id}/metadata.json`
- bridge serving truth through `lineage_from_artifact_metadata()`
- expose lineage as base model plus one adapter artifact
- no multi-adapter routing claim in v0

Current capability label:

- `partial`: artifact layout and lineage bridge exist; the OwlCoda-driven data
  accumulation and learning loop are not proven yet

Blocked until:

- an OwlCoda npm run produces real accumulated traces
- a LoRA run or explicit no-op verdict consumes those traces
- the resulting adapter or verdict is registered and re-consumed through
  `owlmlx`
