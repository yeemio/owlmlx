# owlmlx Execution Prompt 3.2A: Memory-Pressure Eviction Decision And Execution

> Date: 2026-04-26
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Executor A
> Recommended executor: `opus-4.7` or another implementation-heavy executor
> Active release floor: `3.2 Memory-Pressure Decision Closure`
> Role: implementation, tests, docs, and runtime transport

## 1. Objective

Close or materially progress release floor `3.2` by introducing the smallest
honest runtime-owned memory-pressure eviction loop.

The required question is:

**Given the current memory-pressure classification and residency snapshot, which
resident model should `owlmlx` evict first, and can `owlmlx` execute that
transition while updating residency, lineage/loadability, and eviction-history
truth without weakening serial runtime invariants?**

This is not a general reclaim engine.
It is the first runtime-owned pressure decision plus execution path.

## 2. Required Read Order

Read these before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/memory-pressure-contract.md`
5. `docs/source-of-truth/model-residency-policy.md`
6. `docs/source-of-truth/nonresident-loadability-lineage.md`
7. `docs/source-of-truth/nonresident-model-admission-policy.md`
8. `docs/source-of-truth/phase45-multi-model-eviction-history-governance.md`
9. `docs/source-of-truth/recovery-supervisor-contract.md`
10. `owlmlx/memory_pressure_contract.py`
11. `owlmlx/model_residency_policy.py`
12. `owlmlx/nonresident_loadability_lineage.py`
13. `owlmlx/nonresident_model_admission_policy.py`
14. `owlmlx/multi_model_eviction_history_governance.py`
15. `owlmlx/runtime/kernel.py`
16. `owlmlx/runtime/server.py`
17. Related tests:
    `tests/test_memory_pressure_contract.py`,
    `tests/test_model_residency_policy.py`,
    `tests/test_nonresident_loadability_lineage.py`,
    `tests/test_nonresident_model_admission_policy.py`,
    `tests/test_multi_model_eviction_history_governance.py`,
    `tests/test_runtime_kernel.py`,
    `tests/test_runtime_server.py`

## 3. Implementation Target

Preferred new contract:

- module: `owlmlx/memory_pressure_eviction_policy.py`
- surface: `owlmlx.memory_pressure_eviction_policy`
- transport: `GET /v1/runtime/memory-pressure-eviction-policy`
- execution transport: `POST /v1/runtime/memory-pressure-eviction`
- docs: `docs/source-of-truth/memory-pressure-eviction-policy.md`
- tests: `tests/test_memory_pressure_eviction_policy.py`

If codebase naming points to a better exact name, keep the meaning and explain
the rename in the handoff.

## 4. Required Decision Semantics

The decision surface must return exactly one of:

- `evict`
- `defer`
- `reject`
- `unknown`

Required meaning:

- `evict`
  - memory pressure is `over_budget` or a stronger runtime-owned pressure
    trigger is present
  - at least one resident candidate is unload-eligible
  - candidate ordering is deterministic
  - the selected candidate is not pinned and is not the only safe active model
    unless the policy explicitly freezes active reassignment behavior
- `defer`
  - pressure is `near_budget`
  - pressure is not yet strong enough to unload, or a required precondition must
    resolve before eviction
- `reject`
  - pressure is over budget but no safe candidate exists
  - every candidate is pinned or otherwise protected
  - recovery hard barrier makes eviction unsafe
- `unknown`
  - the runtime lacks required budget, residency, or candidate truth

Do not use `unknown` to hide deterministic `reject`.

## 5. Candidate Ordering

The policy must emit a deterministic ordered candidate list.

Acceptable first-round ordering inputs:

- unpinned before pinned
- TTL-expired unpinned before merely manual-unload-eligible
- non-active before active
- larger memory footprint before smaller memory footprint if otherwise tied
- stable `model_id` lexical tie-breaker

If the implementation chooses a different ordering, document it and test it.

The policy must not claim OS-level pressure, fairness scheduling, or global
optimal placement unless those signals are actually owned.

## 6. Execution Requirement

Add one runtime-owned execution path that performs the selected eviction.

Preferred shape:

- a `RuntimeKernel` method that:
  - builds the current memory-pressure eviction policy
  - refuses execution unless the decision is `evict`
  - unloads the selected model through existing unload semantics
  - records a new eviction-history event with a source such as
    `memory_pressure_policy`
  - leaves pinned models untouched
  - keeps active model state honest after eviction
  - returns a structured result with decision snapshot, selected victim,
    unload result, residency after-state, lineage/loadability after-state, and
    eviction-history event
- a route:
  - `POST /v1/runtime/memory-pressure-eviction`

The execution path must be atomic at the runtime truth level: either the unload
and history/governance after-state are visible together, or the failure result
names the failed stage and does not claim eviction success.

## 7. Lineage / Loadability Requirement

Floor `3.2` says execution must update residency, lineage, and eviction-history
governance surfaces atomically.

Do not mutate `model_lineage.py` records merely because a model is evicted.
Instead, ensure the after-state is machine-readable:

- residency shows the victim no longer resident
- loadability lineage still says whether the now-nonresident model is
  loadable, not loaded
- eviction history contains the pressure-eviction event

If this cannot be wired honestly in one round, return `progressed` and name the
exact missing after-state signal.

## 8. Hard Rules

1. Do not implement a broad reclaim engine.
2. Do not implement automatic background eviction loops.
3. Do not weaken `GenerationGate`, post-claim serial execution, or
   `ticketed_fifo`.
4. Do not touch `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent`.
5. Do not claim release readiness, parity, replacement, or production-grade.
6. Do not mark floor `3.2` closed unless both decision and execution
   requirements are met and tests prove an observable residency change.
7. Preserve unrelated staged/dirty work.

## 9. Minimum Acceptance Criteria

A successful A-lane result must include:

- memory-pressure eviction decision contract
- runtime execution path and endpoint
- source-of-truth doc
- tests covering:
  - `within_budget` does not evict
  - `near_budget` defers
  - `over_budget` selects deterministic candidate order
  - pinned candidates are protected
  - no safe candidate produces `reject`
  - execution unloads the selected candidate and records an eviction-history
    event
  - residency after-state no longer includes the victim
  - loadability lineage after-state remains inspectable for the evicted model
  - repeated-load or repeated-pressure scenario causes observable residency
    change
- docs updated:
  - `memory-pressure-eviction-policy.md`
  - `memory-pressure-contract.md`
  - `model-residency-policy.md` if pressure evictability semantics change
  - `runtime-status-schema.md` if the new payload is upper-layer consumable
  - `release-readiness-execution-plan.md`
  - `release-readiness-backlog.md` only if the floor state honestly changes

## 10. Suggested Verification

Run the focused tests first:

```bash
pytest -q tests/test_memory_pressure_eviction_policy.py
pytest -q tests/test_memory_pressure_contract.py tests/test_model_residency_policy.py tests/test_multi_model_eviction_history_governance.py
pytest -q tests/test_nonresident_loadability_lineage.py tests/test_nonresident_model_admission_policy.py
pytest -q tests/test_runtime_kernel.py -k "pressure or eviction or unload or ttl"
pytest -q tests/test_runtime_server.py -k "pressure or eviction or residency or nonresident"
python3 -m py_compile \
  owlmlx/memory_pressure_eviction_policy.py \
  owlmlx/memory_pressure_contract.py \
  owlmlx/model_residency_policy.py \
  owlmlx/runtime/kernel.py \
  owlmlx/runtime/server.py
git diff --check
```

If you substitute commands, record the exact substitution and why.

## 11. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`

The handoff must include:

- outcome label
- floor `3.2` verdict:
  - `candidate_closed_pending_review`
  - `progressed`
  - `still_blocked`
- changed files
- exact commands and results
- endpoint paths and sample decisive fields
- selected victim ordering rule
- whether execution updates residency, lineage/loadability, and eviction
  history together
- whether repeated-load or repeated-pressure evidence produced observable
  residency change
- whether release backlog section 5 changed; if not, state that it remains open
- exact next B review target

## 12. Allowed Outcome Labels

Use one:

- `owlmlx_release_floor_3_2A_memory_pressure_eviction_candidate_closed_pending_review`
- `owlmlx_release_floor_3_2A_memory_pressure_eviction_progressed`
- `owlmlx_release_floor_3_2A_memory_pressure_eviction_still_blocked`

Use `candidate_closed_pending_review` only if the implementation appears to
satisfy all floor-`3.2` requirements but still needs B review before the
coordinator marks the release ledger closed.

