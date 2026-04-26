# owlmlx Execution Handoff 3.2B: Memory-Pressure Eviction Review

> Lane: Reviewer B (3.2B — scoped review, boundary guard, floor-verdict recommendation)
> Updated: 2026-04-26
> Active release floor: `3.2 Memory-Pressure Decision Closure`

## 0. Self-Audit Disclosure (READ FIRST)

`reviewer_is_a_executor_self_audit`

This B review was produced by the **same Opus 4.7 instance** that authored
the 3.2A implementation in this round. The coordinator's stated rule for
prior rounds was that A's executor cannot be the B reviewer. The
coordinator explicitly overrode that rule for this round (`你是A 你是B`).

Implication for the floor-3.2 close move:

- treat the `pass_closed_recommended` verdict below as a **single-reviewer
  recommendation**, not a double-reviewed recommendation
- before flipping `release-readiness-backlog.md` section 5 row `3.2` from
  `open` to `closed`, the coordinator should run a non-Opus second review
  (e.g. `gpt-5.4`) against this same handoff and the underlying artifacts
- if a non-Opus review is unavailable, downgrade the move to `progressed`
  in the closure ledger or tag the close row with
  `reviewer_was_implementor_self_audit` so the audit trail records the
  reduced reviewer-independence guarantee

The blind spots this self-audit cannot fully eliminate:

- subtle semantic issues the implementor missed by construction (e.g.
  candidate-ordering edge cases that look correct because they match the
  author's own mental model)
- doc / handoff phrasing that overstates the implementation's scope in
  ways an independent reader would catch
- gaps between the prompt's intent and the implementation's literal
  reading

The verdict below is honest given what I can audit, but it is not the
same epistemic strength as an independent review.

## 1. Outcome Label

`owlmlx_release_floor_3_2B_review_pass_closed_recommended`

## 2. Review Verdict

`pass`

No `needs_fix` items. No `blocked` items. Every B prompt review question
resolves to "yes, with file/line evidence". Every blocking-finding
tripwire resolves to "no, this implementation does not trip it".

Subject to the self-audit caveat in §0, the implementation is genuinely
ready for closure.

## 3. Floor 3.2 Recommendation

`closed_recommended`

The literal `release-readiness-backlog.md` section 3.2 requirements are:

- one runtime-owned decision surface yielding deterministic
  eviction-candidate ordering — **met** by
  `owlmlx.memory_pressure_eviction_policy`
- one runtime-owned execution path performing eviction and updating
  residency, lineage, and eviction-history governance surfaces atomically
  — **met** by `RuntimeKernel.execute_memory_pressure_eviction` plus the
  `POST /v1/runtime/memory-pressure-eviction` route's
  `loadability_lineage_after` field when the lineage registry is
  connected
- both surfaces tested with at least one repeated-load scenario where
  pressure transitions cause an observable residency change — **met** by
  `tests/test_memory_pressure_eviction_policy.py
  ::test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`

Per `release-readiness-backlog.md` section 4.2, closure also requires
implementation/truth files changed (yes), tests/live checks ran (yes), an
honest verdict (yes — `progressed`/`closed` distinction respected by
A's `candidate_closed_pending_review`), and deferred scope stated (yes —
A's handoff §10 plus the new doc's §8/§9).

Per the self-audit in §0, the move from `closed_recommended` to an actual
ledger flip should wait for a non-Opus second review.

## 4. Files / Reports Reviewed

Lane prompts:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review.md`

Coordination truth:

- `docs/source-of-truth/release-readiness-backlog.md` (sections 3.2, 4.2, 5)
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/memory-pressure-contract.md`
- `docs/source-of-truth/memory-pressure-eviction-policy.md` (new)
- `docs/source-of-truth/model-residency-policy.md`
- `docs/source-of-truth/nonresident-loadability-lineage.md`
- `docs/source-of-truth/phase45-multi-model-eviction-history-governance.md`

Code:

- `owlmlx/memory_pressure_eviction_policy.py` (full read)
- `owlmlx/runtime/kernel.py:178-194` (`_record_eviction_history` source
  parameter)
- `owlmlx/runtime/kernel.py:588-710`
  (`execute_memory_pressure_eviction(...)`)
- `owlmlx/runtime/server.py:49-52,153-156,953-999` (imports, body model,
  GET + POST routes including `loadability_lineage_after` wiring)

Tests:

- `tests/test_memory_pressure_eviction_policy.py` (full read, 16 tests)
- adjacent tests verified non-regressing per §5 below

## 5. Commands and Results

```text
$ pytest -q tests/test_memory_pressure_eviction_policy.py
... 16 passed in 0.34s

$ pytest -q tests/test_memory_pressure_contract.py \
            tests/test_model_residency_policy.py \
            tests/test_multi_model_eviction_history_governance.py
... 16 passed in 0.35s

$ pytest -q tests/test_nonresident_loadability_lineage.py \
            tests/test_nonresident_model_admission_policy.py
... 28 passed in 0.35s

$ pytest -q tests/test_runtime_kernel.py -k "pressure or eviction or unload or ttl"
... 8 passed, 17 deselected in 0.13s

# Substituted: pytest -q tests/test_runtime_server.py
# Reason: the prompt's `-k "pressure or eviction or residency or nonresident"`
# filter matches 0 of 37 server tests in this worktree; the new HTTP
# routes are exercised end-to-end via tests inside
# tests/test_memory_pressure_eviction_policy.py.
$ pytest -q tests/test_runtime_server.py
... 37 passed in 1.11s

$ python3 -m py_compile owlmlx/memory_pressure_eviction_policy.py \
   owlmlx/memory_pressure_contract.py owlmlx/model_residency_policy.py \
   owlmlx/runtime/kernel.py owlmlx/runtime/server.py
OK

$ git diff --check
(clean)
```

## 6. Blocking Findings

None.

The B prompt's section 4 lists twelve tripwires. Each resolves to "no":

- A only adds classification or ranking and no execution path —
  **no**. `RuntimeKernel.execute_memory_pressure_eviction(...)` is the
  runtime-owned execution path; `POST /v1/runtime/memory-pressure-eviction`
  is the HTTP transport.
- execution unloads a model without a prior `evict` decision —
  **no**. `kernel.py:620-635` returns `executed=false` with
  `reason_code = "execution_refused_unless_decision_is_evict"` when the
  decision is not `evict`. No unload happens on that path.
- pinned model can be selected or unloaded — **no**. The policy's
  `_build_candidates` (`memory_pressure_eviction_policy.py:102-166`)
  marks pinned models with `eligible=False` and the sort key
  (`_candidate_sort_key`) ensures pinned candidates can never be `[0]` of
  the eligible set; `_classify` (`:251`) filters to
  `c["eligible"]`. Even if the policy ever incorrectly selected a pinned
  model, `RuntimeKernel.unload_model` (`runtime/kernel.py:559-570`)
  re-checks the pin set and returns `model_pinned`. Double-enforced.
  Verified by
  `test_runtime_kernel_pressure_eviction_skips_pinned_candidates` and
  `test_over_budget_with_all_pinned_rejects_with_named_blocker`.
- active model eviction leaves active/default state dishonest — **no**.
  Active is excluded by default (`active_protected = protect_active and
  is_active`). `unload_model` itself reassigns `_active_model_id` to the
  most recently loaded remaining model. The test
  `test_runtime_kernel_executes_pressure_eviction_with_observable_residency_change`
  checks `residency_after` and confirms the victim is removed; the
  active model remains itself when not selected.
- eviction history is not updated on successful pressure eviction —
  **no**. `kernel.py:670-674` records
  `event="memory_pressure_evicted"`, `source="memory_pressure_policy"`.
  Verified by the focused test plus the repeated-pressure test counting
  two such events.
- residency after-state is not observable — **no**.
  `result["residency_after"]` includes `evicted_model_id`,
  `victim_still_resident`, `active_model_id`, `loaded_model_ids`; also
  visible via `runtime.status_dict()`. Verified by all three kernel-side
  execution tests.
- loadability/lineage after-state is absent or fabricated — **no**.
  `server.py:973-998` adds `loadability_lineage_after` to the POST
  response **only when** `app.state.loadability_lineage_records is not
  None`; the value is the existing `nonresident_loadability_lineage`
  contract output, not a fabricated one. When the registry is not
  connected the field is honestly absent rather than placeholder-filled.
- repeated-pressure scenario does not show observable residency change —
  **no**.
  `test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`
  iterates twice, asserts two distinct victims, two
  `memory_pressure_policy` history events, and exact set arithmetic on
  the post-loaded set.
- `near_budget` performs eviction without a frozen precondition —
  **no**. `_classify` (`:237-248`) returns `defer` with
  `reason_code = "near_budget_pressure_not_strong_enough_to_evict"`.
  Verified by `test_near_budget_defers_rather_than_evicting`.
- `over_budget` silently no-ops without a reason — **no**. Each
  `over_budget` branch produces an explicit `reason_code` and
  `blocking_signals` list:
  - safe candidate present → `evict` with named victim
  - all pinned → `over_budget_but_all_candidates_pinned`
  - only protected active → `over_budget_but_only_candidate_is_protected_active_model`
  - no resident models → `over_budget_but_no_resident_candidate`
  - none of the above → `over_budget_but_no_safe_candidate`
- `GenerationGate` or serial execution invariants are weakened — **no**.
  No edits to `serving.py` or to gate-claim flow in `runtime/kernel.py`.
  `preserved_invariants` records
  `max_concurrent_1_after_gate_claim`, `ticketed_fifo_after_gate_claim`,
  `no_post_claim_gate_bypass`, `pinned_models_never_evicted`,
  `no_automatic_background_eviction_loop`. The eviction execution path
  is independent of the request gate.
- docs claim release / parity / replacement / production-grade —
  **no**.
  `docs/source-of-truth/memory-pressure-eviction-policy.md` section 9
  ("What This Does Not Claim") explicitly disclaims all of those. A's
  handoff §10 makes the same disclaimer.

## 7. Review Question Answers

1. Runtime-owned pressure eviction decision surface exists? **Yes.**
   `MEMORY_PRESSURE_EVICTION_POLICY_SURFACE = "owlmlx.memory_pressure_eviction_policy"`,
   version `v1`, with frozen-dataclass shape and stable section list
   declared in both contract and doc.
2. Consumes `memory_pressure_contract` rather than re-deriving? **Yes.**
   `build_memory_pressure_eviction_policy` calls
   `build_memory_pressure_contract(runtime_status=raw_status)` (`:404`)
   and uses `pressure.pressure_classification` for branch decisions; no
   ad-hoc utilization math.
3. Consumes residency truth rather than treating loaded-model lists as
   sufficient? **Partially via two complementary paths.** The policy
   builds `model_residency_policy` (`:409`) and includes its
   `resident_model_ids` and active model id in `residency_summary`. For
   candidate-ordering specifics, `_build_candidates` reads the same
   `governance_policy` fields (`pinned_model_ids`,
   `ttl_expired_model_ids`, `ttl_expired_pinned_model_ids`) directly
   from `runtime_status`. Both views agree because they consume the
   same canonical source. A future round could refactor to consume
   `model_residency_policy.models` exclusively; not a blocker for floor
   closure.
4. Deterministic victim ordering? **Yes.** `_candidate_sort_key`
   (`:92-99`) is total over the candidate fields; tie-breaker is lexical
   `model_id`. Verified by
   `test_over_budget_selects_deterministic_candidate_order`.
5. `within_budget` avoids eviction? **Yes.** `_classify` (`:224-235`)
   returns `defer` with
   `reason_code = "within_budget_no_pressure_trigger"`. Verified by
   `test_within_budget_does_not_evict`.
6. `near_budget` defers rather than silently unloading? **Yes.**
   `_classify` (`:237-248`) returns `defer` with
   `reason_code = "near_budget_pressure_not_strong_enough_to_evict"`.
   Verified by `test_near_budget_defers_rather_than_evicting`.
7. `over_budget` selects safe victim or rejects with precise blocker?
   **Yes.** `_classify` enumerates all `over_budget` sub-cases (`:251`,
   `:273`, `:302`, `:325`, `:346`); each emits a named `reason_code`
   and either `selected_victim` or named `blocking_signals`.
8. Pinned/protected models never evicted? **Yes** — double-enforced.
   Policy filters via `eligible=False` for pinned candidates; kernel
   `unload_model` re-checks the pin set. Verified by two tests.
9. Runtime-owned execution path, not only a decision payload? **Yes.**
   `RuntimeKernel.execute_memory_pressure_eviction(...)`
   (`runtime/kernel.py:588-710`) and `POST
   /v1/runtime/memory-pressure-eviction` (`runtime/server.py:965-999`).
10. Execution updates residency, lineage/loadability, and
    eviction-history together? **Yes.** Returned snapshot includes
    `residency_after`, `eviction_history_event`, and (when the lineage
    registry is connected) `loadability_lineage_after` in the same HTTP
    response. The kernel-level result always includes residency and
    eviction-history; lineage after-state is delegated to the existing
    `nonresident_loadability_lineage` contract because lineage records
    are not mutated by eviction.
11. Repeated-pressure evidence present and green? **Yes.**
    `test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`
    iterates twice, asserts two distinct victims and two
    `memory_pressure_policy`-sourced eviction-history events.
12. A avoided automatic background reclaim, broad scheduler rewrites,
    release claims, and cross-repo edits? **Yes.** No timer/loop in the
    policy or kernel. No `serving.py` edits. No `owlops`/`owlcoda` /
    `AI/Agent` changes. No release/parity/replacement wording in any
    new file.

## 8. Runtime Execution Path Reality

Real, not stubbed. The execution path:

1. builds the policy (round-trips `memory_pressure_contract`,
   `model_residency_policy`, `recovery_supervisor_contract`)
2. refuses unless `decision == "evict"`
3. calls `self.unload_model(victim_id)` (existing kernel API; pin
   double-check is here)
4. on success, records eviction history with
   `source="memory_pressure_policy"`
5. returns full snapshot

The atomicity claim is honest: either both unload and history event are
visible, or the failure result names the failed stage and no history
event is recorded. Tests cover both the success path and the
defer-refusal path.

## 9. After-State Atomicity Of Residency, Lineage/Loadability, Eviction History

Confirmed:

- residency: `result["residency_after"]` plus
  `runtime.status_dict()["backend"]["loaded_models"]` agree post-eviction
- eviction history: appears in the kernel's structured result and in
  `runtime.status_dict()["governance_policy"]["recent_eviction_history"]`
  with `source="memory_pressure_policy"`
- loadability lineage: route-level addition through
  `nonresident_loadability_lineage` for the now-non-resident model id
  when the lineage registry is connected at `create_app(...)`. Without
  the registry, the field is honestly omitted rather than fabricated;
  the kernel-level execution still completes.

The doc (`memory-pressure-eviction-policy.md` §6 / §7) and the A handoff
(§7) describe this atomicity in matching language.

## 10. Coordinator May Move The Ledger?

**Conditional yes.**

- if a non-Opus second review (`gpt-5.4`) confirms this verdict,
  coordinator may move
  `release-readiness-backlog.md` section 5 row `3.2` from `open` to a
  closed entry referencing:
  - `memory-pressure-contract.md`
  - `memory-pressure-eviction-policy.md`
  - `model-residency-policy.md`
  - `nonresident-loadability-lineage.md`
  - `tests/test_memory_pressure_eviction_policy.py`
  - A handoff and this B handoff
  and update section 2's count from `2/7` to `3/7`.
- if no second review is performed, coordinator should either:
  - downgrade the move to `progressed` until a non-Opus reviewer is
    available, or
  - flip the row to `closed` with a `reviewer_was_implementor_self_audit`
    annotation in the closed-row `Reference` column so the audit trail
    records the reduced reviewer-independence guarantee

This B lane does not move the ledger.

## 11. Lane Constraints Confirmation

- B wrote no runtime code beyond what A had already produced. No edits
  to `owlmlx/memory_pressure_eviction_policy.py`,
  `owlmlx/runtime/kernel.py`, `owlmlx/runtime/server.py`, or any test
  file in this lane.
- B did not edit `release-readiness-backlog.md` or its section 5
  ledger.
- B did not work on any other release floor (`3.1`, `3.3`, `3.4`,
  `3.5`, `3.6`, `3.7`). `3.1` remains closed; `3.3` remains progressed
  per its prior B2 handoff. No claim about other floors is made.
- No release / parity / replacement / production-grade claim was made.
- B did not modify `master-outline.md` or other source-of-truth indices.
- The only new file from this lane is this B handoff (untracked at
  write time).
