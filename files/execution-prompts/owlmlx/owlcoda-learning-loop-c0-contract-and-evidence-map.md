# OwlCoda Learning Loop C0 — Contract And Evidence Map

## Role

You are the C0 contract executor for `owlmlx`.

Your job is to define the runtime-owned contract for the new public release
gate:

```text
OwlCoda npm package
  -> owlmlx local model
  -> self-training data accumulation
  -> learning / adaptation step
  -> learned artifact or state registered back into owlmlx truth
  -> OwlCoda consumes the updated local-model path again
```

This is a contract and evidence-mapping round. Do not implement runtime code.

## Starting Point

Repository:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
git switch refactor/runtime-spine-stage-1-to-3.1
git switch -c refactor/owlcoda-learning-loop-c0-contract
```

Read first:

- `AGENTS.md`
- `docs/source-of-truth/public-release-standard.md`
- `docs/source-of-truth/owlcoda-learning-loop-coordination.md`
- `docs/source-of-truth/training-substrate-contract.md`
- `docs/source-of-truth/training-to-serving-contract.md`
- `docs/source-of-truth/artifact-layout-contract.md`
- `docs/source-of-truth/model-lineage-schema.md`
- `docs/source-of-truth/runtime-spine-architecture-blueprint.zh.md`

## Goal

Produce the first authoritative contract map for the OwlCoda npm local-learning
loop.

The output must answer:

1. What is a valid OwlCoda training-data record?
2. What provenance is mandatory?
3. What learning/adaptation step consumes it?
4. What does `owlmlx` need to register after learning?
5. Which existing runtime truth surface carries the result?
6. Which missing surface, if any, blocks the first end-to-end smoke?
7. What exact evidence proves the loop without a hidden manual bridge?

## Write Scope

Allowed:

- new `docs/source-of-truth/owlcoda-learning-loop-contract.md`
- update `docs/source-of-truth/public-release-standard.md` only to point to the
  new contract
- update `docs/source-of-truth/master-outline.md` only to add the new contract
  pointer
- optional checkpoint under `files/execution-prompts/owlmlx/`

Forbidden:

- any `owlmlx/*.py`
- any `owlmlx/runtime/*.py`
- tests
- OwlCoda repo files
- OwlOps repo files
- `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`

## Required Sections

The new contract must include:

1. `Loop Definition`
2. `Training Data Record`
3. `Mandatory Provenance`
4. `Learning Step Contract`
5. `Runtime Registration Contract`
6. `OwlCoda Re-consumption Contract`
7. `Evidence Bundle`
8. `Existing owlmlx Surfaces`
9. `Missing Surfaces / Blockers`
10. `First Smoke Acceptance Criteria`
11. `Non-Goals`

## Hard Rules

- Do not claim the loop is implemented.
- Do not add module-as-spec Python files.
- Do not invent an OwlCoda implementation detail; mark unknowns as unknown and
  hand them to the OwlCoda C1 discovery lane.
- Do not describe runtime benchmarks as release proof.
- Do not require OwlOps UI for release proof. OwlOps may observe; it is not the
  loop owner.

## Verification

Run:

```bash
git diff --check
git status --short
```

No pytest is required unless code is changed. Code changes are forbidden.

## Final Status Wording

Use:

```text
owlcoda_learning_loop_c0_contract_mapped
```

Do not use:

```text
public_release_ready
learning_loop_complete
training_supported
owlcoda_runtime_integration_done
```
