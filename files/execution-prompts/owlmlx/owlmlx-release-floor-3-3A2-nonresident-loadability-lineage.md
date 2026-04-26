# owlmlx Execution Prompt 3.3A2: Non-Resident Loadability Lineage

> Date: 2026-04-25
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor A2
> Active release floor: `3.3 Model Residency Non-Resident Path`
> Role: implement the confirmed next blocker after B2 review

## 1. Objective

Close or materially progress the confirmed floor-`3.3` blocker:

```text
runtime_owned_non_resident_loadability_lineage
```

B2 has confirmed that A's non-resident admission policy is valid and
`progressed`, but floor `3.3` is not closed because `admit_and_load` still
depends on request/operator-supplied `known_loadable_model_ids` rather than a
runtime-owned loadability lineage surface.

This round must introduce the smallest honest runtime-owned contract that can
answer:

**For a non-resident target model, does `owlmlx` own enough model visibility,
artifact, and lineage truth to call the target loadable before gate claim?**

## 2. Required Read Order

Read these before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy-handoff.md`
5. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B2-post-A-review-handoff.md`
6. `docs/source-of-truth/nonresident-model-admission-policy.md`
7. `docs/source-of-truth/model-lineage-schema.md`
8. `docs/source-of-truth/runtime-model-visibility-contract.md` if present in
   the checkout
9. `docs/source-of-truth/model-residency-policy.md`
10. `docs/source-of-truth/memory-pressure-contract.md`
11. `docs/source-of-truth/recovery-supervisor-contract.md`
12. `owlmlx/nonresident_model_admission_policy.py`
13. `owlmlx/model_lineage.py`
14. `owlmlx/runtime_model_visibility.py` if present in the checkout
15. `owlmlx/runtime/server.py`
16. `tests/test_nonresident_model_admission_policy.py`
17. `tests/test_model_lineage.py`
18. `tests/test_runtime_model_visibility.py` if present in the checkout

## 3. Implementation Target

Preferred new contract:

- module: `owlmlx/nonresident_loadability_lineage.py`
- surface: `owlmlx.nonresident_loadability_lineage`
- transport: `GET /v1/runtime/nonresident-loadability-lineage`
- docs: `docs/source-of-truth/nonresident-loadability-lineage.md`
- tests: `tests/test_nonresident_loadability_lineage.py`

If the codebase already has a better exact naming convention, keep the meaning
and explain the name in the handoff.

## 4. Stable Semantics

The new contract should classify the target with exactly one of:

- `known_loadable`
- `not_loadable`
- `unknown`

Required meaning:

- `known_loadable`
  - target is non-resident
  - target passes an owlmlx-owned visibility or artifact-presence gate
  - target has a valid served-model lineage record under `owlmlx.model_lineage`
  - lineage and local artifact truth point at the same target
- `not_loadable`
  - target is missing from the runtime-owned registry
  - required local artifact/config truth is absent
  - lineage is invalid for the target lifecycle
  - lineage points at a different model/artifact than the requested target
- `unknown`
  - the runtime has no loadability lineage registry/source available
  - the inputs are too weak to distinguish missing registry from missing target

Do not use `unknown` to hide a deterministic `not_loadable`.

## 5. Runtime-Owned Source Rule

The contract must not reintroduce request-level hints as the source of truth.

Acceptable runtime-owned sources include:

- the existing owlmlx visibility registry and artifact gate exposed through
  `runtime_model_visibility`
- a new runtime-owned loadability-lineage registry passed at app/kernel
  construction time, not per request as an admission hint
- `owlmlx.model_lineage` validation for served-weight provenance records
- local artifact/config checks already frozen by owlmlx visibility truth

Not acceptable as closure evidence:

- only `known_loadable_model_ids` query parameters
- deriving loadability from the string value of `model_id`
- assuming that every visible model is loadable without lineage validation
- executing a speculative load probe as the definition of lineage

If no runtime-owned source can be honestly connected in this round, return
`progressed` or `still_blocked` and freeze the exact missing source.

## 6. Required Integration

Integrate the new contract into `owlmlx.nonresident_model_admission_policy`.

After integration, the policy should be able to return `admit_and_load` for a
non-resident target **without** `known_loadable_model_ids`, when the new
runtime-owned loadability-lineage contract returns `known_loadable`.

Keep the existing `known_loadable_model_ids` path only as an explicitly
labeled legacy/operator-supplied fallback if needed. It must not be presented as
runtime-owned lineage closure.

The admission policy payload should make the source visible, for example:

- `inputs.loadability_lineage.decision`
- `inputs.loadability_lineage.truth_status`
- `inputs.known_loadable_truth_status`
- `missing_signals` updated so
  `runtime_owned_non_resident_loadability_lineage` disappears only when the new
  contract is actually connected

## 7. Hard Rules

1. Do not implement automatic loading as part of this round.
2. Do not implement floor `3.2` eviction ordering or eviction execution.
3. Do not weaken `GenerationGate` invariants.
4. Do not replace `model_lineage.py`; consume and extend around it if needed.
5. Do not move work into `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent`.
6. Do not mark floor `3.3` closed in the release ledger unless every
   `release-readiness-backlog.md` section-3.3 requirement is met and tests ran.
   Prefer `candidate_closed_pending_review` if the implementation appears to
   satisfy the floor but B review has not yet happened.
7. Preserve unrelated dirty/staged changes.

## 8. Minimum Acceptance Criteria

The round must produce:

- the new loadability-lineage contract module
- a stable serializer payload with reason codes and missing/blocking signals
- a runtime endpoint
- source-of-truth doc
- tests covering:
  - known visible + valid lineage target -> `known_loadable`
  - missing registry/source -> `unknown`
  - registered target missing config/artifact -> `not_loadable`
  - invalid lineage -> `not_loadable`
  - lineage target mismatch -> `not_loadable`
  - nonresident admission can return `admit_and_load` without
    `known_loadable_model_ids` when loadability lineage is `known_loadable`
  - nonresident admission still returns `unknown` or `reject` when loadability
    lineage is absent or invalid
- docs updated:
  - `nonresident-loadability-lineage.md`
  - `nonresident-model-admission-policy.md`
  - `runtime-status-schema.md` if the payload is upper-layer consumable
  - `release-readiness-execution-plan.md`
  - `release-readiness-backlog.md` only if the floor state changes honestly

## 9. Suggested Verification

Run the focused tests first:

```bash
pytest -q tests/test_nonresident_loadability_lineage.py
pytest -q tests/test_nonresident_model_admission_policy.py
pytest -q tests/test_model_lineage.py
pytest -q tests/test_runtime_model_visibility.py
pytest -q tests/test_runtime_server.py -k "nonresident or visibility or models"
python3 -m py_compile \
  owlmlx/nonresident_loadability_lineage.py \
  owlmlx/nonresident_model_admission_policy.py \
  owlmlx/runtime/server.py
git diff --check
```

If a listed test file does not exist in the current checkout, replace it with
the nearest actual test and state the substitution.

## 10. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A2-nonresident-loadability-lineage-handoff.md`

The handoff must include:

- outcome label
- floor `3.3` verdict:
  - `candidate_closed_pending_review`
  - `progressed`
  - `still_blocked`
- changed files
- exact commands and results
- endpoint path and sample decisive fields
- whether `admit_and_load` no longer requires `known_loadable_model_ids`
- whether `runtime_owned_non_resident_loadability_lineage` is closed,
  progressed, or still blocked
- whether release backlog section 5 changed; if not, state that it remains open
- exact next step for B review

## 11. Allowed Outcome Labels

Use one:

- `owlmlx_release_floor_3_3A2_loadability_lineage_candidate_closed_pending_review`
- `owlmlx_release_floor_3_3A2_loadability_lineage_progressed`
- `owlmlx_release_floor_3_3A2_loadability_lineage_still_blocked`

Use `candidate_closed_pending_review` only if the implementation appears to
satisfy all floor-`3.3` requirements but still needs B review before the
coordinator marks the release ledger closed.

