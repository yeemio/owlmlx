# owlmlx Execution Prompt 3.3B3: Loadability Lineage Closure Review

> Date: 2026-04-25
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Reviewer B3
> Recommended executor: `gpt-5.4` or another reviewer that did not author A2
> Active release floor: `3.3 Model Residency Non-Resident Path`
> Role: independent closure review after A2 candidate closure

## 1. Objective

Review A2's candidate closure for release floor `3.3`.

This round must decide one narrow thing:

**Can the coordinator honestly move `release-readiness-backlog.md` section 5
row `3.3 residency non-resident path` from `open` to `closed`, or does A2 need
fixes first?**

A2 reported:

```text
owlmlx_release_floor_3_3A2_loadability_lineage_candidate_closed_pending_review
```

Do not re-run implementation work unless a blocking finding requires a fix
round later. This is a scoped review and ledger recommendation.

## 2. Required Read Order

Read these before judging:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A2-nonresident-loadability-lineage.md`
5. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A2-nonresident-loadability-lineage-handoff.md`
6. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B2-post-A-review-handoff.md`
7. `docs/source-of-truth/nonresident-loadability-lineage.md`
8. `docs/source-of-truth/nonresident-model-admission-policy.md`
9. `docs/source-of-truth/model-lineage-schema.md`
10. `docs/source-of-truth/runtime-model-visibility-contract.md`
11. `docs/source-of-truth/model-residency-policy.md`
12. `docs/source-of-truth/memory-pressure-contract.md`
13. `owlmlx/nonresident_loadability_lineage.py`
14. `owlmlx/nonresident_model_admission_policy.py`
15. `owlmlx/runtime_model_visibility.py`
16. `owlmlx/model_lineage.py`
17. `owlmlx/runtime/server.py`
18. `tests/test_nonresident_loadability_lineage.py`
19. `tests/test_nonresident_model_admission_policy.py`
20. `tests/test_runtime_server.py`

## 3. Review Questions

Answer each directly:

1. Does `owlmlx.nonresident_loadability_lineage` exist as a stable
   runtime-owned surface?
2. Does it return exactly one of:
   `known_loadable`, `not_loadable`, `unknown`?
3. Does `known_loadable` require all of:
   runtime visibility/artifact gate, valid `owlmlx.model_lineage`, and target
   alignment?
4. Does `not_loadable` cover deterministic failure cases instead of hiding them
   as `unknown`?
5. Does the new endpoint
   `GET /v1/runtime/nonresident-loadability-lineage` return the contract
   payload?
6. Does `nonresident_model_admission_policy` now consume the lineage contract?
7. Can `admit_and_load` happen without `known_loadable_model_ids` when the
   runtime-owned lineage contract returns `known_loadable`?
8. Does missing or invalid loadability lineage prevent `admit_and_load`?
9. Are `GenerationGate` invariants untouched?
10. Did A2 avoid automatic loading, floor `3.2` eviction, scheduler-admission
    rewrites, and cross-repo work?
11. Is the release ledger still open pending this review, rather than moved by
    A2 before review?

## 4. Blocking Findings

Return `needs_fix` if any of these are true:

- `known_loadable` can be produced without a runtime-owned visibility/artifact
  gate
- `known_loadable` can be produced without valid `model_lineage` validation
- lineage target mismatch still admits
- missing registry/source is mislabeled as closed truth
- `admit_and_load` still requires `known_loadable_model_ids` when runtime-owned
  lineage is connected
- `known_loadable_model_ids` is still presented as runtime-owned closure rather
  than legacy/operator fallback
- A2 implemented automatic loading or pressure eviction
- hard recovery/pressure boundaries from the earlier policy were weakened
- docs claim release/parity/replacement/production-grade
- tests do not reproduce A2's decisive claim

## 5. Required Verification

Run at minimum:

```bash
pytest -q tests/test_nonresident_loadability_lineage.py
pytest -q tests/test_nonresident_model_admission_policy.py
pytest -q tests/test_nonresident_loadability_lineage.py tests/test_nonresident_model_admission_policy.py tests/test_model_lineage.py tests/test_runtime_model_visibility.py
pytest -q tests/test_runtime_server.py -k "nonresident or visibility or models"
pytest -q tests/test_model_residency_policy.py tests/test_memory_pressure_contract.py tests/test_recovery_supervisor_contract.py tests/test_scheduler_admission_contract.py tests/test_orchestration_status.py
python3 -m py_compile owlmlx/nonresident_loadability_lineage.py owlmlx/nonresident_model_admission_policy.py owlmlx/runtime/server.py
git diff --check
```

If any command must be substituted due the current checkout, record the exact
substitution and why.

## 6. Ledger Recommendation

If review passes, recommend that the coordinator move:

```text
| 3.3 residency non-resident path | open | -- | `model-residency-policy.md` |
```

to a closed row with references to:

- `nonresident-model-admission-policy.md`
- `nonresident-loadability-lineage.md`
- `tests/test_nonresident_model_admission_policy.py`
- `tests/test_nonresident_loadability_lineage.py`
- the A2 and B3 handoffs

Do not edit the ledger in B3 unless explicitly authorized by the coordinator
prompt or unless this review prompt is being executed by the coordinator.
For this lane, prefer a precise recommendation over mutating the ledger.

## 7. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B3-loadability-lineage-closure-review-handoff.md`

The handoff must include:

- outcome label
- review verdict: `pass`, `needs_fix`, or `blocked`
- floor `3.3` recommendation:
  - `closed_recommended`
  - `progressed_needs_fix`
  - `still_blocked`
- blocking findings first, with file/line references where possible
- exact commands and results
- whether A2's candidate closure is confirmed
- whether `admit_and_load` no longer requires `known_loadable_model_ids`
- whether the coordinator may move the section-5 ledger row
- confirmation that no other floor was worked or claimed closed

## 8. Allowed Outcome Labels

Use one:

- `owlmlx_release_floor_3_3B3_closure_review_pass_closed_recommended`
- `owlmlx_release_floor_3_3B3_closure_review_needs_fix`
- `owlmlx_release_floor_3_3B3_closure_review_blocked`

Use `pass_closed_recommended` only if A2's implementation satisfies the full
literal floor-`3.3` requirement and the ledger is ready for coordinator closeout.

