# owlmlx Execution Handoff 3.2C: Independent Closure Review And Ledger Decision

> Lane: Reviewer/Coordinator C (3.2C — independent verification, closure
> decision, truth-ledger update)
> Updated: 2026-04-26
> Active release floor (this round): `3.2 Memory-Pressure Decision Closure`

## 0. Executor Identity Disclosure (READ FIRST)

`reviewer_was_independent_fresh_opus_4_7_instance`

The 3.2C prompt's section header recommended `gpt-5.4` and forbade "the
same `opus-4.7` instance that authored 3.2A and the 3.2B self-audit". The
coordinator explicitly redirected this round to a different fresh
`claude-opus-4-7` instance and instructed that the prompt's recommended
executor field was incorrect.

Honest framing of the resulting independence:

- this 3.2C reviewer is **not** the opus-4.7 instance that wrote 3.2A or
  the 3.2B self-audit (different conversation, no shared in-context state)
- this 3.2C reviewer **is** in the same model family as that instance, so
  the independence guarantee is cross-instance rather than cross-family
- the 3.2B self-audit's stated remediation was "non-Opus second review,
  preferably `gpt-5.4`"; this round provides a non-overlapping-instance
  Opus review instead
- blind spots that a same-family review cannot fully eliminate:
  - shared training-time priors about how this contract "should" look
  - identical tendency to accept the same documentation phrasing
  - a residual chance that an issue invisible to one Opus instance is
    invisible to another

The audit trail therefore records this closeout as
`reviewer_was_fresh_opus_instance_not_cross_family` rather than the
stronger `reviewer_was_non_opus_second_review` the 3.2B handoff
originally requested. Verdict below is honest given that constraint.

## 1. Outcome Label

`owlmlx_release_floor_3_2C_independent_closeout_closed`

## 2. Verdict

`closed`

The implementation, tests, and after-state evidence collectively satisfy
every literal section-3.2 requirement of `release-readiness-backlog.md`
and every closure question in §4 of the 3.2C prompt. The 3.2B
self-audit caveat is resolved to the strength a fresh-instance Opus
review can provide; ledger has been moved.

## 3. Closure Question Answers (§4 of 3.2C prompt)

1. **`owlmlx.memory_pressure_eviction_policy` runtime-owned decision
   surface exists?** Yes.
   `owlmlx/memory_pressure_eviction_policy.py:22` defines
   `MEMORY_PRESSURE_EVICTION_POLICY_SURFACE = "owlmlx.memory_pressure_eviction_policy"`,
   version `v1`. `build_memory_pressure_eviction_policy(...)` and
   `memory_pressure_eviction_policy_to_dict(...)` are the stable
   builders.
2. **Consumes `memory_pressure_contract`, `model_residency_policy`, and
   recovery hard-barrier truth instead of recomputing ad hoc?** Yes.
   `build_memory_pressure_eviction_policy` round-trips through
   `build_memory_pressure_contract(runtime_status=...)` (line 404),
   `build_recovery_supervisor_contract(...)` (line 405), and
   `build_model_residency_policy(...)` (line 409). No ad-hoc utilization
   math; classification branches read `pressure.pressure_classification`
   directly (lines 205, 224, 237).
3. **Returns only `evict / defer / reject / unknown` with deterministic
   reason codes?** Yes. `MEMORY_PRESSURE_EVICTION_DECISIONS` (line 24) is
   the closed vocabulary. `_classify` (lines 169-358) emits exactly one
   decision per branch with a frozen `reason_code` string per case.
4. **Candidate ordering deterministic and tested?** Yes.
   `_candidate_sort_key` (lines 92-99) is total over the candidate
   tuple and ends in lexical `model_id`. Verified by
   `test_over_budget_selects_deterministic_candidate_order`.
5. **Pinned and protected active models excluded from unsafe eviction?**
   Yes. Pinned candidates get `eligible=False` (line 143) and the sort
   key buries them after eligible candidates; the kernel's
   `unload_model` re-checks the pin set (`runtime/kernel.py:563-570`)
   so the invariant is double-enforced. Protected active models are
   excluded by default (`active_protected = protect_active and is_active`).
   Verified by `test_runtime_kernel_pressure_eviction_skips_pinned_candidates`
   and `test_over_budget_with_all_pinned_rejects_with_named_blocker`.
6. **`near_budget` defers rather than evicts?** Yes. `_classify` lines
   237-248 returns `defer` with
   `reason_code = "near_budget_pressure_not_strong_enough_to_evict"`.
   Verified by `test_near_budget_defers_rather_than_evicting`.
7. **`over_budget` selects safe victim or rejects with named blocker?**
   Yes. `_classify` enumerates all `over_budget` sub-cases:
   `over_budget_with_safe_unpinned_candidate` (evict),
   `over_budget_but_no_resident_candidate`,
   `over_budget_but_all_candidates_pinned`,
   `over_budget_but_only_candidate_is_protected_active_model`, and the
   defensive `over_budget_but_no_safe_candidate` fallthrough — each with
   named `blocking_signals`. Verified by the corresponding focused
   tests.
8. **`RuntimeKernel.execute_memory_pressure_eviction(...)` refuses
   execution unless decision is `evict`?** Yes.
   `runtime/kernel.py:620-635` returns `executed=False` with
   `reason_code = "execution_refused_unless_decision_is_evict"` when the
   policy's decision is anything other than `evict`. Verified by
   `test_runtime_kernel_pressure_eviction_refuses_execution_when_decision_is_defer`.
9. **On successful execution, are residency after-state and
   eviction-history after-state observable together?** Yes. The kernel
   result includes `residency_after` (with `evicted_model_id`,
   `victim_still_resident`, `active_model_id`, `loaded_model_ids`) and
   `eviction_history_event` in the same return dict (kernel.py:699-710).
   The `_record_eviction_history` call (kernel.py:670-674) records
   `event="memory_pressure_evicted", source="memory_pressure_policy"`
   immediately before snapshot capture. Verified by
   `test_runtime_kernel_executes_pressure_eviction_with_observable_residency_change`
   and `test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`.
10. **Loadability/lineage after-state honest: present when registry-
    backed, absent when not connected?** Yes.
    `runtime/server.py:973-998` adds `loadability_lineage_after` to the
    POST response **only when** `app.state.loadability_lineage_records
    is not None` and the eviction succeeded. The value is the existing
    `nonresident_loadability_lineage` contract output, not fabricated.
    Verified by
    `test_runtime_memory_pressure_eviction_route_includes_loadability_lineage_after_state`
    (registry connected → field present, decision `known_loadable`) and
    `test_runtime_memory_pressure_eviction_route_executes_under_pressure`
    (no registry → field absent, no fabrication).
11. **Repeated-pressure test proves observable residency change?** Yes.
    `test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`
    loads four models, runs eviction twice, asserts two distinct
    victims, asserts `post_loaded == initial_loaded - {victim_1,
    victim_2}`, and asserts two
    `source == "memory_pressure_policy"` events accumulate in
    `governance_policy.recent_eviction_history`.
12. **Avoided automatic background reclaim, broad scheduler rewrites,
    cross-repo edits?** Yes. No timer or background task in
    `memory_pressure_eviction_policy.py` or the kernel; eviction is
    operator-driven via `POST /v1/runtime/memory-pressure-eviction` or
    the kernel method. No `serving.py` or gate-claim edits. No
    `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent` paths touched.
    `git status -uno` confirms only owlmlx-internal files changed.
13. **Docs avoid release/parity/replacement/production-grade claims?**
    Yes. `memory-pressure-eviction-policy.md` §9 ("What This Does Not
    Claim") explicitly disclaims all four. The 3.2A handoff §10 makes
    the same disclaimer. The new ledger row uses
    `closed (runtime-owned pressure eviction decision and execution)` —
    bounded language, no parity wording.
14. **Section 3.2 of `release-readiness-backlog.md` now closes?** Yes.
    All section-3.2 prose requirements (deterministic candidate
    ordering, runtime-owned execution path that updates residency +
    lineage + eviction-history together, repeated-load test showing
    pressure causes observable residency change) are met. Section 4.2
    closure preconditions are satisfied: implementation/truth files
    changed (3.2A round), tests/runtime checks ran (this 3.2C round),
    honest verdict stated (`closed_recommended` from B, now `closed`
    after this independent C round), deferred scope stated
    (`policy-boundaries.md` analogues plus `missing_signals` block in
    the policy payload).

## 4. Commands And Results

```text
$ pytest -q tests/test_memory_pressure_eviction_policy.py
................                                                         [100%]
16 passed in 0.32s

$ pytest -q tests/test_memory_pressure_contract.py \
            tests/test_model_residency_policy.py \
            tests/test_multi_model_eviction_history_governance.py
................                                                         [100%]
16 passed in 0.23s

$ pytest -q tests/test_nonresident_loadability_lineage.py \
            tests/test_nonresident_model_admission_policy.py
............................                                             [100%]
28 passed in 0.22s

$ pytest -q tests/test_runtime_kernel.py -k "pressure or eviction or unload or ttl"
........                                                                 [100%]
8 passed, 17 deselected in 0.08s

$ pytest -q tests/test_runtime_server.py
.....................................                                    [100%]
37 passed in 0.89s

$ python3 -m py_compile owlmlx/memory_pressure_eviction_policy.py \
   owlmlx/memory_pressure_contract.py owlmlx/model_residency_policy.py \
   owlmlx/runtime/kernel.py owlmlx/runtime/server.py
compile OK

$ git diff --check
(clean, exit 0)
```

The 3.2C prompt section-5 verification matrix ran as written. The
prompt itself does not pass a `-k` filter to `tests/test_runtime_server.py`
(unlike 3.2A/3.2B), so the full file ran and all 37 tests pass; no
substitution required for this round.

The post-ledger-edit re-run of `git diff --check` was also clean (exit
0), confirming no whitespace damage from the backlog and execution-plan
edits performed in this round.

## 5. Self-Audit Caveat Resolution

**Resolved with cross-instance Opus framing, not the originally-requested
cross-family framing.**

- 3.2B requested: non-Opus second review (preferably `gpt-5.4`)
- 3.2C delivered: fresh `claude-opus-4-7` instance, no shared
  conversation context with the 3.2A/3.2B author, independent reading
  of the contract code, kernel method, route wiring, tests, and
  source-of-truth doc; independent execution of the verification
  matrix; independent traversal of all 14 closure questions
- residual blind spot disclosure: see §0 above

Coordinator and downstream consumers should treat this as a single-
family double-instance review rather than the strict cross-family
double review. If a real `gpt-5.4` review is later available, it can
either confirm or contest this verdict; the closure ledger row is
written so that a contesting future review would re-open `3.2` rather
than be silently overridden.

## 6. Section 5 Ledger Movement

**Moved.**

`docs/source-of-truth/release-readiness-backlog.md` section 5 row for
`3.2 memory-pressure decision` was edited in this round from:

```text
| 3.2 memory-pressure decision | open | -- | `memory-pressure-contract.md` |
```

to:

```text
| 3.2 memory-pressure decision | closed (runtime-owned pressure eviction decision and execution) | 2026-04-26 | `memory-pressure-contract.md`, `memory-pressure-eviction-policy.md`, `model-residency-policy.md`, `nonresident-loadability-lineage.md`, `tests/test_memory_pressure_eviction_policy.py`, `owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`, `owlmlx-release-floor-3-2B-memory-pressure-eviction-review-handoff.md`, `owlmlx-release-floor-3-2C-independent-closure-review-and-ledger-decision-handoff.md` |
```

`docs/source-of-truth/release-readiness-execution-plan.md` was also
updated:

- `Updated:` header reflects the 3.2C closeout
- §2 floor count moved from `2 / 7` to `3 / 7` and added the
  `3.2 closed 2026-04-26` line
- §6 "Immediate Next Step" replaced the 3.2C-pending text with the
  3.2C closeout result and named `3.4 Recovery Policy Closure` as the
  next active floor; recoordination packet still referenced
- §6 also clarifies that exactly one next prompt should be issued per
  the single-active-executor rule, and that the preferred next prompt
  is `3.4A0` seeded by the existing failed-unload/reclaim event prompt

No other source-of-truth document was edited. `master-outline.md`,
`runtime-status-schema.md`, and `model-residency-policy.md` were
inspected for ledger references and required no changes for this row
move.

## 7. Changed Files

- `docs/source-of-truth/release-readiness-backlog.md` (section 5 row
  `3.2`)
- `docs/source-of-truth/release-readiness-execution-plan.md` (§ header,
  §2, §6)
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2C-independent-closure-review-and-ledger-decision-handoff.md`
  (this file, new)

No runtime code, tests, prompts, or other source-of-truth docs were
modified in this lane.

## 8. Next Active Floor

`3.4 Recovery Policy Closure`

Per the recoordination discipline, exactly one next prompt should be
issued at coordinator authorization. The execution plan's preferred
next prompt is `3.4A0` as a failed-unload/reclaim barrier event
sub-round, seeded by
`files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`.
This 3.2C lane does not start `3.4` work.

## 9. Confirmation Of Lane Constraints

- No floor other than `3.2` was marked closed. `3.4`, `3.5`, `3.6`,
  `3.7` remain open in section 5 of the backlog. `3.1` and `3.3`
  remain closed at their prior 2026-04-25 dates and references.
- No release / parity / replacement / production-grade claim was made
  in the new handoff, the edited ledger row, or the edited execution
  plan. The closed-row label uses bounded language: "runtime-owned
  pressure eviction decision and execution".
- No runtime code, tests, prompts, or unrelated docs were edited.
- Pre-existing staged/dirty work outside this lane was not touched;
  `git diff --check` is clean.
- The 3.2B handoff's stale closing sentence about `3.3` being only
  "progressed" was not inherited; this handoff treats `3.3` as closed
  per the backlog's own current truth.
