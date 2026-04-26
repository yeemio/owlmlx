# owlmlx Execution Prompt 3.2C: Independent Closure Review And Ledger Decision

> Date: 2026-04-26
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Lane: single active executor; independent closeout review
> Recommended executor: `gpt-5.4`
> Forbidden executor: the same `opus-4.7` instance that authored 3.2A and the
> 3.2B self-audit
> Active release floor: `3.2 Memory-Pressure Decision Closure`
> Role: independent verification, closure decision, and truth-ledger update

## 1. Objective

Decide whether release floor `3.2` can be honestly closed.

The immediate reason this round exists is that the available 3.2B review is a
self-audit: the same Opus executor authored both 3.2A and the B review after an
explicit one-round override. That B handoff recommends closure, but also states
that a non-Opus second review should run before the coordinator flips
`release-readiness-backlog.md` section 5.

This C lane must independently answer:

**Does the 3.2 implementation really provide a runtime-owned memory-pressure
eviction decision plus execution path that updates residency,
loadability/lineage, and eviction-history truth without weakening serial
runtime invariants?**

Do not work on floor `3.4` or any later floor in this round. There is no
parallel A/B allocation for this step; this prompt is the whole active round.

## 2. Required Read Order

Read these before deciding:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/memory-pressure-contract.md`
5. `docs/source-of-truth/memory-pressure-eviction-policy.md`
6. `docs/source-of-truth/model-residency-policy.md`
7. `docs/source-of-truth/nonresident-loadability-lineage.md`
8. `docs/source-of-truth/nonresident-model-admission-policy.md`
9. `docs/source-of-truth/phase45-multi-model-eviction-history-governance.md`
10. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution.md`
11. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`
12. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review.md`
13. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review-handoff.md`
14. `owlmlx/memory_pressure_eviction_policy.py`
15. `owlmlx/runtime/kernel.py`
16. `owlmlx/runtime/server.py`
17. `tests/test_memory_pressure_eviction_policy.py`

Do not inherit the B handoff's final stale sentence about `3.3` being merely
progressed. Current coordinator truth is that `3.3` is closed via B3.

## 3. Hard Rules

1. Do not write runtime code in this C lane.
2. Do not mark any floor except `3.2` closed.
3. Do not mark `3.2` closed unless both decision and execution requirements in
   `release-readiness-backlog.md` section 3.2 are satisfied.
4. Treat the 3.2B handoff as useful evidence, not as independent review.
5. Preserve `GenerationGate`, post-claim serial execution, `ticketed_fifo`, and
   `max_concurrent=1` truth.
6. Do not claim release readiness, parity, replacement-grade, or production
   readiness.
7. Keep unrelated dirty/staged work untouched.
8. If evidence is missing, return `needs_fix` or `blocked`, not an optimistic
   closeout.

## 4. Closure Questions

Answer every question directly:

1. Does `owlmlx.memory_pressure_eviction_policy` exist as a runtime-owned
   decision surface?
2. Does it consume `memory_pressure_contract`, `model_residency_policy`, and
   recovery hard-barrier truth rather than recomputing ad hoc truth?
3. Does it return only `evict / defer / reject / unknown`, with deterministic
   reason codes?
4. Is candidate ordering deterministic and tested?
5. Are pinned models and protected active models excluded from unsafe eviction?
6. Does `near_budget` defer rather than evict?
7. Does `over_budget` select a safe victim or reject with a named blocker?
8. Does `RuntimeKernel.execute_memory_pressure_eviction(...)` refuse execution
   unless the decision is `evict`?
9. On successful execution, are residency after-state and eviction-history
   after-state observable together?
10. Is loadability/lineage after-state honest: present when registry-backed,
    absent rather than fabricated when not connected?
11. Does a repeated-pressure test prove observable residency change?
12. Did the implementation avoid automatic background reclaim, broad scheduler
    rewrites, and cross-repo edits?
13. Did docs avoid release/parity/replacement/production-grade claims?
14. Does section 3.2 of `release-readiness-backlog.md` now close?

## 5. Required Verification

Run at minimum:

```bash
pytest -q tests/test_memory_pressure_eviction_policy.py
pytest -q tests/test_memory_pressure_contract.py tests/test_model_residency_policy.py tests/test_multi_model_eviction_history_governance.py
pytest -q tests/test_nonresident_loadability_lineage.py tests/test_nonresident_model_admission_policy.py
pytest -q tests/test_runtime_kernel.py -k "pressure or eviction or unload or ttl"
pytest -q tests/test_runtime_server.py
python3 -m py_compile \
  owlmlx/memory_pressure_eviction_policy.py \
  owlmlx/memory_pressure_contract.py \
  owlmlx/model_residency_policy.py \
  owlmlx/runtime/kernel.py \
  owlmlx/runtime/server.py
git diff --check
```

If a command is substituted, record the exact substitution and why. If a test
filter matches zero tests, run the unfiltered relevant file and record that
fact.

## 6. Allowed Documentation Updates

If and only if the review confirms closure, update:

- `docs/source-of-truth/release-readiness-backlog.md`
  - move section 5 row `3.2 memory-pressure decision` from `open` to
    `closed (runtime-owned pressure eviction decision and execution)`
  - set closed date to `2026-04-26`
  - reference:
    - `memory-pressure-contract.md`
    - `memory-pressure-eviction-policy.md`
    - `model-residency-policy.md`
    - `nonresident-loadability-lineage.md`
    - `tests/test_memory_pressure_eviction_policy.py`
    - `owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`
    - `owlmlx-release-floor-3-2B-memory-pressure-eviction-review-handoff.md`
    - this 3.2C handoff
- `docs/source-of-truth/release-readiness-execution-plan.md`
  - update the release-floor count from `2 / 7` to `3 / 7`
  - record the 3.2C outcome
  - set the next active floor to `3.4 Recovery Policy Closure`

If closure is not confirmed, do not update the ledger. Instead, write the exact
missing requirement and keep `3.2` active.

Do not edit runtime code, tests, or unrelated docs in this lane.

## 7. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2C-independent-closure-review-and-ledger-decision-handoff.md`

The handoff must include:

- outcome label
- verdict: `closed`, `needs_fix`, `blocked`, or `still_blocked`
- exact commands and results
- answers to all closure questions
- changed files
- whether the self-audit caveat is resolved
- whether section 5 ledger moved
- if closed, the next active floor
- if not closed, the exact 3.2 blocker
- confirmation that no other floor was marked closed
- confirmation that no release/parity/replacement claim was made

## 8. Allowed Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_2C_independent_closeout_closed`
- `owlmlx_release_floor_3_2C_independent_closeout_needs_fix`
- `owlmlx_release_floor_3_2C_independent_closeout_still_blocked`
- `owlmlx_release_floor_3_2C_independent_closeout_blocked_missing_evidence`

Use `closed` only if the independent review resolves the self-audit caveat and
the release ledger can honestly move.

## 9. Next Floor Selection

If this C round closes floor `3.2`, the next active floor is:

- `3.4 Recovery Policy Closure`

Do not start `3.4` inside this C round. The coordinator should issue the
separate `3.4A` implementation prompt after the ledger is updated.
