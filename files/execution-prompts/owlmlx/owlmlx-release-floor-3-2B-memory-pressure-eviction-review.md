# owlmlx Execution Prompt 3.2B: Memory-Pressure Eviction Review

> Date: 2026-04-26
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: Reviewer B
> Recommended executor: `gpt-5.4` or another executor that did not author A
> Active release floor: `3.2 Memory-Pressure Decision Closure`
> Role: scoped review, boundary guard, and floor-verdict recommendation

## 1. Objective

Review A's memory-pressure eviction decision/execution work.

This round must decide:

**Did A honestly close release floor `3.2`, or did it only progress pressure
observability / candidate ranking without a runtime-owned execution closure?**

Do not perform implementation work in this lane unless the coordinator later
authorizes a fix round.

## 2. Required Read Order

Read these before judging:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/memory-pressure-contract.md`
5. `docs/source-of-truth/memory-pressure-eviction-policy.md` if A created it
6. `docs/source-of-truth/model-residency-policy.md`
7. `docs/source-of-truth/nonresident-loadability-lineage.md`
8. `docs/source-of-truth/phase45-multi-model-eviction-history-governance.md`
9. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution.md`
10. A's handoff:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`
11. A's changed runtime, docs, and tests

If A's handoff is absent, return `blocked_waiting_for_A` after producing the
review checklist.

## 3. Review Questions

Answer each directly:

1. Does a runtime-owned pressure eviction decision surface exist?
2. Does it consume `memory_pressure_contract` rather than re-deriving pressure
   ad hoc?
3. Does it consume residency truth rather than treating loaded-model lists as
   sufficient?
4. Does it emit deterministic victim ordering?
5. Does `within_budget` avoid eviction?
6. Does `near_budget` defer rather than silently unload?
7. Does `over_budget` either select a safe victim or reject with a precise
   blocker?
8. Are pinned/protected models never evicted?
9. Is there a runtime-owned execution path, not only a decision payload?
10. Does execution update residency after-state, loadability/lineage after-state,
    and eviction-history governance together?
11. Is repeated-load or repeated-pressure evidence present and green?
12. Did A avoid automatic background reclaim, broad scheduler rewrites,
    release claims, and cross-repo edits?

## 4. Blocking Findings

Return `needs_fix` if any of these are true:

- A only adds classification or ranking and no execution path
- execution unloads a model without a prior `evict` decision
- pinned model can be selected or unloaded
- active model eviction leaves active/default state dishonest
- eviction history is not updated on successful pressure eviction
- residency after-state is not observable
- loadability/lineage after-state is absent or fabricated
- repeated-pressure scenario does not show observable residency change
- `near_budget` performs eviction without a frozen precondition
- `over_budget` silently no-ops without a reason
- `GenerationGate` or serial execution invariants are weakened
- docs claim release/parity/replacement/production-grade

## 5. Required Verification

At minimum, run A's focused tests and these review suites:

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

If a command must be substituted, record the exact substitution and why.

## 6. Ledger Recommendation

If review passes and A's implementation satisfies both decision and execution
requirements, recommend that the coordinator move:

```text
| 3.2 memory-pressure decision | open | -- | `memory-pressure-contract.md` |
```

to a closed row referencing:

- `memory-pressure-contract.md`
- `memory-pressure-eviction-policy.md`
- `model-residency-policy.md`
- `nonresident-loadability-lineage.md`
- `tests/test_memory_pressure_eviction_policy.py`
- A and B handoffs

Do not move the ledger in this B lane unless explicitly authorized by the
coordinator. Return a recommendation first.

## 7. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review-handoff.md`

The handoff must include:

- outcome label
- review verdict: `pass`, `needs_fix`, `blocked_waiting_for_A`, or `blocked`
- floor `3.2` recommendation:
  - `closed_recommended`
  - `progressed_needs_fix`
  - `still_blocked`
- blocking findings first, with file/line references where possible
- exact commands and results
- whether the runtime execution path is real
- whether residency, lineage/loadability, and eviction-history after-state are
  updated together
- whether the coordinator may move the ledger
- confirmation that no other floor was worked or claimed closed

## 8. Allowed Outcome Labels

Use one:

- `owlmlx_release_floor_3_2B_review_pass_closed_recommended`
- `owlmlx_release_floor_3_2B_review_needs_fix`
- `owlmlx_release_floor_3_2B_blocked_waiting_for_A`
- `owlmlx_release_floor_3_2B_review_blocked`

Use `pass_closed_recommended` only if floor `3.2` is genuinely ready for
coordinator closeout.

