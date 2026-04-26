# owlmlx Execution Handoff 3.3A: Non-Resident Admission Policy

> Lane: Executor A (3.3A — implementation, tests, docs, runtime transport)
> Updated: 2026-04-25
> Active release floor: `3.3 Model Residency Non-Resident Path`

## 1. Outcome Label

`owlmlx_release_floor_3_3A_nonresident_admission_policy_progressed`

## 2. Floor 3.3 Verdict

**`progressed`**, not `closed`.

A runtime-owned non-resident admission decision surface now exists with the
required decision vocabulary (`admit_and_load`, `defer`, `reject`, `unknown`)
and round-trips through residency, memory pressure, and recovery contracts.
Two requirements of the backlog's section 3.3 are met:

- one runtime-owned decision surface for non-resident targets exists
- the decision is deterministic given inputs and round-trips through residency
  and pressure surfaces

One requirement remains unmet for honest closure:

- the backlog requires the round trip to also flow through a *lineage* surface.
  Runtime does not yet own a non-resident loadability lineage signal. The
  policy treats `known_loadable_model_ids` as an explicit operator-supplied
  hint and freezes the lineage gap as a named blocker per the 3.3A prompt rule
  (do not invent loadability).

Therefore floor `3.3` is **progressed**: the admission decision surface is in
place, but the lineage round-trip is staged as the next sub-blocker rather
than closed.

## 3. Changed Files

New runtime module:

- `owlmlx/nonresident_model_admission_policy.py`

New runtime transport endpoint (added to existing file):

- `owlmlx/runtime/server.py`
  - `from owlmlx.nonresident_model_admission_policy import ...`
  - `from fastapi import FastAPI, Query` (added `Query`)
  - new route: `GET /v1/runtime/nonresident-model-admission-policy`
    with query params `model_id`, `request_context_class`,
    `known_loadable_model_ids`

New tests:

- `tests/test_nonresident_model_admission_policy.py`

New source-of-truth doc:

- `docs/source-of-truth/nonresident-model-admission-policy.md`

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy-handoff.md`

No other release floor's runtime/test/doc files were modified. Existing
contracts (`scheduler_admission_contract`, `model_residency_policy`,
`memory_pressure_contract`, `recovery_supervisor_contract`) were not edited;
the new policy is a read-only consumer.

## 4. Commands and Results

```text
$ pytest -q tests/test_nonresident_model_admission_policy.py
... 13 passed in 0.22s

$ pytest -q tests/test_model_residency_policy.py \
         tests/test_memory_pressure_contract.py \
         tests/test_recovery_supervisor_contract.py \
         tests/test_scheduler_admission_contract.py
... 35 passed in 0.27s

$ pytest -q tests/test_orchestration_status.py tests/test_runtime_server.py
... 43 passed in 0.87s

$ python3 -m py_compile \
    owlmlx/nonresident_model_admission_policy.py \
    owlmlx/runtime/server.py
(compile OK)

$ git diff --check
(clean)
```

## 5. Endpoint And Decisive Fields

`GET /v1/runtime/nonresident-model-admission-policy?model_id=fake-b&known_loadable_model_ids=fake-b`

Sample decisive fields under a small in-budget runtime:

```json
{
  "contract": {
    "surface": "owlmlx.nonresident_model_admission_policy",
    "version": "v1",
    "stable_sections": [
      "summary",
      "reason",
      "required_preconditions",
      "blocking_signals",
      "preserved_invariants",
      "inputs",
      "decision_support",
      "policy_boundaries",
      "missing_signals"
    ]
  },
  "summary": {
    "status": "partial",
    "decision": "admit_and_load",
    "target_model_id": "fake-b",
    "confidence": "medium",
    "supported_decisions": ["admit_and_load", "defer", "reject", "unknown"],
    "policy_depth": "non_resident_target_pre_claim_admission"
  },
  "reason": {
    "code": "non_resident_target_known_loadable_admit",
    "message": "..."
  },
  "required_preconditions": [
    "memory_budget_preflight_must_still_hold_at_load_time",
    "no_hard_recovery_barrier_at_load_time",
    "no_concurrent_competing_non_resident_load_for_same_target",
    "post_claim_serial_invariants_must_remain_owned_by_GenerationGate"
  ],
  "preserved_invariants": [
    "max_concurrent_1_after_gate_claim",
    "ticketed_fifo_after_gate_claim",
    "no_post_claim_gate_bypass",
    "pre_claim_decision_only"
  ]
}
```

Decision branches verified by tests:

- `admit_and_load` — non-resident target in `known_loadable_model_ids`,
  pressure `within_budget`, no recovery barrier
- `defer` — pressure `near_budget` (no pressure-action policy), or recovery
  `probing` for `high_context`
- `reject` — no `model_id`, target already resident, recovery hard barrier,
  pressure `over_budget` with no eviction policy
- `unknown` — pressure truth missing, or target non-resident with no lineage
  hint

## 6. Scheduler Admission Integration

Scheduler admission does **not** yet consume the new policy. The integration
is deferred on purpose, with the reason recorded both in
`docs/source-of-truth/nonresident-model-admission-policy.md` section 7 and in
the policy payload's `missing_signals` under
`scheduler_admission_integration`:

- `scheduler_admission_contract` already has dense behavior tests
  (`tests/test_scheduler_admission_contract.py`, 35 tests in the adjacent
  suite). A cross-contract change in the same lane risks regressing those
  tests and blurring the 3.3 verdict.
- The new contract should stabilize on its own surface before another
  contract depends on it.
- The new contract already exposes a stable shape (`decision`, `reason.code`,
  `blocking_signals`) suitable for a thin pre-claim defer-to-load consumer in
  a later round.

No post-claim gate bypass was introduced. The policy explicitly records
`pre_claim_decision_only` and `no_post_claim_gate_bypass` under
`preserved_invariants`.

## 7. Lineage / Loadability Truth Status

Runtime does not yet own a non-resident loadability discovery surface. The
policy honestly treats this as a missing signal:

- `inputs.known_loadable_truth_status` reports `operator_supplied` when the
  caller supplies `known_loadable_model_ids`, otherwise `missing`
- when the hint is absent, the policy returns `unknown`
  (`reason.code = lineage_loadability_truth_missing`) rather than fabricating
  `admit_and_load`
- `missing_signals` always lists
  `runtime_owned_non_resident_loadability_lineage` as a layered gap

The existing `owlmlx/model_lineage.py` describes served-weight provenance
(base model, quantizer, conversion path, runtime version), not non-resident
loadability discovery; reusing it for loadability would be a different
contract. Authoring that contract is the next sub-step toward floor `3.3`
honest closure.

## 8. Deferred Scope

Explicitly deferred, with named owners:

- floor `3.2` pressure-ranked eviction execution policy — consumed only as a
  blocker named in `blocking_signals` and `missing_signals`; no eviction
  victim selection or execution introduced in this lane
- runtime-owned non-resident loadability lineage signal — staged as the next
  sub-blocker for floor `3.3` closure
- `scheduler_admission_contract` integration — recorded under
  `missing_signals.scheduler_admission_integration`, no behavior change
- automatic non-resident loader — out of scope; load remains explicit
  operator action through `/v1/load`
- background recovery loop — remains owned by floor `3.4`
- continuous batching, multi-worker scheduling — out of scope per Hard Rule
  3 / 4 of the 3.3A prompt

## 9. Lane Constraints Confirmation

- No floor-3.2 pressure-ranked eviction was implemented.
- No broad automatic loader was implemented.
- `GenerationGate` serial invariants were not weakened: the policy is a
  pre-claim decision surface and explicitly records `pre_claim_decision_only`
  and `no_post_claim_gate_bypass` under `preserved_invariants`.
- No release readiness, parity, replacement, or production-grade claim was
  made.
- No work moved into `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent`.
- Pre-existing staged/dirty changes outside this lane were preserved.
- The handoff records honest "still missing" signals rather than narrating
  future policy as current behavior.

## 10. Recommended Next Step (Coordinator, Not Applied)

- Authorize Executor B (`opus-4.7`) to run
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B-residency-pressure-review.md`
  against this handoff.
- B should verify:
  - the `progressed` verdict, not `closed`
  - that no `3.2` eviction logic leaked into this lane
  - that `scheduler_admission_contract` was not silently bypassed
  - that the lineage gap is recorded as a missing signal, not as a fabricated
    admission

After B's review, the next sub-step toward `3.3` closure is the lineage
contract: a runtime-owned discovery surface for non-resident loadability that
this policy can round-trip through, replacing the operator-supplied
`known_loadable_model_ids` hint.
