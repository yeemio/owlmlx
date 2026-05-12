# owlmlx Public Release Standard

> Status: authoritative release gate
> Created: 2026-05-12
> Scope: public release reopen standard for `owlmlx` after the runtime-spine
> refactor and OwlCoda packaging boundary change

## 1. One-Line Standard

`owlmlx` public release is reopened only when the OwlCoda npm package can use a
local model through `owlmlx` to complete the self-training data accumulation and
learning loop.

This is the public release standard. Earlier developer-preview floor closure,
HTTP surface freeze, and benchmark evidence remain useful engineering evidence,
but they are no longer sufficient to justify public release by themselves.

## 2. Product Boundary Change

Current public distribution boundary:

- `OwlCoda` is released as an npm package only.
- `owlmlx` is the local runtime behind the model path.
- OwlCoda consumes `owlmlx`; OwlCoda does not define `owlmlx` runtime truth.
- `owlmlx` public release is judged by an end-to-end OwlCoda workflow, not by
  standalone runtime endpoints alone.

## 3. Required End-To-End Loop

The required public-release proof is:

```text
OwlCoda npm package
  -> local model served through owlmlx
  -> user/task interaction produces training data
  -> training-data accumulation is persisted with provenance
  -> learning / fine-tuning / adaptation step consumes that data
  -> resulting artifact or learning state is registered back into the runtime truth path
  -> OwlCoda can use the updated local-model path again
```

The loop must be real. It cannot be replaced by:

- a static demo transcript
- an offline-only script with no OwlCoda path
- a runtime-only benchmark
- a standalone training run that is not connected back to OwlCoda consumption
- an OwlOps dashboard display without the learning loop

## 4. Acceptance Criteria

All of the following must be true before public release can be reopened:

| Gate | Required proof |
|---|---|
| OwlCoda package boundary | OwlCoda runs as an npm package and invokes the local runtime path without requiring a separate app shell release |
| Local-model serving | OwlCoda requests go through `owlmlx` local model serving, not a mocked or remote-only path |
| Data accumulation | Interaction data is stored with provenance, model id, timestamp or run id, and enough context to train or adapt safely |
| Learning consumption | A learning/fine-tuning/adaptation step consumes the accumulated data |
| Runtime registration | The resulting artifact, adapter, learned state, or explicit no-op learning verdict is registered into `owlmlx` truth surfaces |
| Re-consumption | OwlCoda can consume the updated path again through `owlmlx` |
| Evidence | The run produces source-of-truth evidence: commands, versions, model id, paths, health, and failure modes |
| No manual gap hiding | Any manual step must be documented; a hidden manual copy/paste bridge fails the gate |

## 5. Relationship To Existing Public Docs

This standard supersedes the earlier "public developer preview" decision
threshold.

The following remain valid but insufficient:

- all seven historical release floors being closed
- `public-surface.md` freezing supported HTTP routes
- `public-claim-matrix.md` allowed claims
- short-prompt reference-runtime performance evidence
- OwlOps consuming live runtime truth

Those prove that `owlmlx` has a serious runtime surface. They do not prove the
new public product story.

The new public product story is:

```text
Local model runtime + OwlCoda npm package + self-training data loop.
```

## 6. Protection Rationale

This gate protects both projects:

- It protects `owlmlx` from being released as a raw runtime before it has a
  concrete user-facing learning workflow.
- It protects OwlCoda from being judged as a shell over a runtime that has not
  proven the learning path that makes local models compound in value.
- It prevents the public narrative from drifting back to "benchmarks and API
  routes" when the actual product differentiation is local learning feedback.

## 7. Allowed Claims Before The Gate

Before this gate is met, external copy may describe `owlmlx` only with scoped
engineering language:

- "internal runtime milestone"
- "runtime-spine refactor"
- "local MLX runtime surface"
- "OwlCoda integration target"
- "not yet publicly released"

Do not use:

- "public release"
- "developer preview release"
- "production-ready"
- "replacement-grade public runtime"
- "OwlCoda learning loop complete"

## 8. Next Execution Direction

The next execution direction is not generic public packaging. It is:

```text
OwlCoda npm package integration with owlmlx local-model learning loop.
```

Work should split into two coordinated lanes:

1. `owlmlx` lane: expose/verify the runtime truth needed for local-model
   learning artifacts, model lineage, training data provenance, and post-learning
   registration.
2. `OwlCoda` lane: prove the npm package can drive the interaction, data
   capture, learning handoff, and re-consumption path.

The release decision is made only after both lanes meet the end-to-end proof.
