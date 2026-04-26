# owlmlx Execution Prompt 3.3B2: Post-A Non-Resident Policy Review

> Date: 2026-04-25
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Reviewer B2
> Active release floor: `3.3 Model Residency Non-Resident Path`
> Role: post-implementation scoped review and next-blocker confirmation

## 1. Objective

Review Executor A's non-resident admission policy implementation after the A
handoff exists.

This round must answer one narrow question:

**Is floor `3.3` now closed, progressed, or still blocked after A introduced
`owlmlx.nonresident_model_admission_policy`?**

The expected honest outcome may be `progressed`, not `closed`, if the runtime
still lacks a runtime-owned non-resident loadability lineage surface.

## 2. Required Read Order

Read these before judging:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/model-residency-policy.md`
5. `docs/source-of-truth/memory-pressure-contract.md`
6. `docs/source-of-truth/recovery-supervisor-contract.md`
7. `docs/source-of-truth/scheduler-admission-contract.md`
8. `docs/source-of-truth/nonresident-model-admission-policy.md`
9. `docs/source-of-truth/runtime-status-schema.md`
10. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy.md`
11. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy-handoff.md`
12. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B-residency-pressure-review-handoff.md`
13. `owlmlx/nonresident_model_admission_policy.py`
14. `owlmlx/runtime/server.py`
15. `tests/test_nonresident_model_admission_policy.py`
16. Any adjacent files A touched

## 3. Important Context

B's earlier handoff was a **Pre-A** audit map:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B-residency-pressure-review-handoff.md`

It is useful as a checklist, but it was written before A's implementation
existed. Do not treat its `blocked_waiting_for_A` verdict as current truth.

Also resolve one checklist drift carefully:

- the A prompt allowed `unknown` when required input truth is absent or too weak
- missing runtime-owned loadability lineage may therefore produce `unknown`
  when it is explicitly named as a blocker
- that is acceptable for honest **progress**
- it is not enough for floor `3.3` **closure**, because the backlog requires
  round-trip through lineage

## 4. Review Scope

Review only floor `3.3`.

You may write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B2-post-A-review-handoff.md`
- optionally `docs/source-of-truth/release-floor-3-3-nonresident-path-review.md`
  if a durable review finding or closure/progress rationale needs source-of-
  truth anchoring

If you create a new source-of-truth doc, add it to
`docs/source-of-truth/master-outline.md`.

Do not edit runtime code unless explicitly authorized later.
Do not edit floor `3.2`, `3.4`, `3.5`, `3.6`, or `3.7` surfaces.

## 5. Review Questions

Answer each directly:

1. Does `owlmlx.nonresident_model_admission_policy` exist as a stable
   runtime-owned surface?
2. Does the HTTP route
   `GET /v1/runtime/nonresident-model-admission-policy` return the policy
   payload?
3. Are decision values exactly
   `admit_and_load`, `defer`, `reject`, `unknown`?
4. Are decisive reasons, required preconditions, blocking signals, preserved
   invariants, and missing signals present?
5. Does the policy consume `model_residency_policy`, `memory_pressure_contract`,
   and `recovery_supervisor_contract` rather than re-deriving their truth
   ad hoc?
6. Does `over_budget` avoid admission and name the floor `3.2` eviction-policy
   blocker?
7. Do hard recovery barriers fail closed?
8. Does the policy avoid automatic loader execution and post-claim gate bypass?
9. Is `scheduler_admission_contract` integration explicitly deferred, with a
   clear reason and missing signal?
10. Is runtime-owned non-resident loadability lineage still missing, and if so
    is it named as the exact next blocker?

## 6. Blocking Findings

Return `needs_fix` if any of these are true:

- `admit_and_load` can occur without either runtime-owned loadability truth or
  an explicitly labeled operator-supplied lineage hint
- the payload hides missing lineage truth without a blocking/missing signal
- `over_budget` admits or silently defers without naming floor `3.2`
- recovery hard barriers do not reject
- the route fabricates runtime truth from docs, config guesses, or path strings
- the policy weakens `GenerationGate` invariants
- tests do not cover the decisive branches A claimed
- docs or handoff claim release, parity, replacement, production-grade, or
  floor `3.3` closure without the lineage round-trip

## 7. Required Verification

Run at minimum:

```bash
pytest -q tests/test_nonresident_model_admission_policy.py
pytest -q tests/test_model_residency_policy.py tests/test_memory_pressure_contract.py tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py
pytest -q tests/test_orchestration_status.py tests/test_runtime_server.py
python3 -m py_compile owlmlx/nonresident_model_admission_policy.py owlmlx/runtime/server.py
git diff --check
```

If you find that a narrower command is more accurate due current worktree
state, record the substituted command and why.

## 8. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B2-post-A-review-handoff.md`

The handoff must include:

- outcome label
- review verdict: `pass`, `needs_fix`, or `blocked`
- floor `3.3` recommendation: `closed`, `progressed`, or `still_blocked`
- blocking findings first, with file/line references where possible
- exact commands and results
- whether A's `progressed` verdict is confirmed
- whether the next blocker is exactly
  `runtime_owned_non_resident_loadability_lineage`
- whether coordinator should authorize A2 lineage work or send A back for fixes
- confirmation that no other release floor was modified or claimed closed

## 9. Allowed Outcome Labels

Use one:

- `owlmlx_release_floor_3_3B2_post_A_review_pass_progressed_confirmed`
- `owlmlx_release_floor_3_3B2_post_A_review_needs_fix`
- `owlmlx_release_floor_3_3B2_post_A_review_blocked`

Use `pass_progressed_confirmed` only when A's implementation is valid but floor
`3.3` remains open because runtime-owned loadability lineage is still missing.

