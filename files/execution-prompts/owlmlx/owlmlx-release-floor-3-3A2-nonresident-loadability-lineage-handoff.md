# owlmlx Execution Handoff 3.3A2: Non-Resident Loadability Lineage

> Lane: Executor A2 (3.3A2 — runtime-owned loadability lineage contract +
> admission-policy integration)
> Updated: 2026-04-25
> Active release floor: `3.3 Model Residency Non-Resident Path`

## 1. Outcome Label

`owlmlx_release_floor_3_3A2_loadability_lineage_candidate_closed_pending_review`

## 2. Floor 3.3 Verdict

**`candidate_closed_pending_review`**, not `closed` and not `progressed`.

The implementation now satisfies every literal section-3.3 requirement of
`release-readiness-backlog.md`:

- a runtime-owned decision surface for non-resident targets exists
  (`owlmlx.nonresident_model_admission_policy`)
- decisions are deterministic given inputs and round-trip through
  **residency**, **lineage**, and **pressure** surfaces — the lineage round
  trip is now real, supplied by the new
  `owlmlx.nonresident_loadability_lineage` contract that itself round-trips
  through the runtime-owned visibility registry, the local artifact gate,
  and `model_lineage.validate_model_lineage`
- `admit_and_load` no longer requires the legacy
  `known_loadable_model_ids` query hint when the runtime-owned loadability
  lineage registry is connected at `create_app(...)` construction time

Per the A2 prompt's Hard Rule 6, the release ledger is **not** moved by this
round. `release-readiness-backlog.md` section 5 row for floor `3.3` remains
`open` until B review confirms the lineage round trip and the coordinator
flips the ledger.

## 3. Changed Files

New runtime module:

- `owlmlx/nonresident_loadability_lineage.py`

Modified runtime module (integration only — no contract weakening):

- `owlmlx/nonresident_model_admission_policy.py`
  - new `loadability_lineage: NonResidentLoadabilityLineage | None = None`
    parameter on `build_nonresident_model_admission_policy(...)`
  - `_classify(...)` now consumes `loadability_lineage` and returns
    `admit_and_load` for `known_loadable`, `reject` for `not_loadable`, and
    falls back to the operator-supplied hint only on `unknown`
  - `_missing_signals(...)` drops
    `runtime_owned_non_resident_loadability_lineage` only when the contract
    is connected and decisive
  - `inputs.loadability_lineage` makes the source of every decision
    inspectable
  - `policy_boundaries.round_trip_surfaces` now lists
    `owlmlx.nonresident_loadability_lineage` as a fourth surface

Modified runtime transport (added new endpoint + connection points,
preserved existing endpoints):

- `owlmlx/runtime/server.py`
  - `create_app(..., loadability_lineage_records=None)` parameter; the
    registry is connected at construction time, not as a query hint
  - new route: `GET /v1/runtime/nonresident-loadability-lineage`
  - existing `GET /v1/runtime/nonresident-model-admission-policy` now
    builds the loadability lineage when records are connected and passes
    it into the admission policy

New tests:

- `tests/test_nonresident_loadability_lineage.py`

Existing tests (extended, no removals):

- `tests/test_nonresident_model_admission_policy.py`
  - vocabulary-stable assertion updated to expect the fourth round-trip
    surface
  - new tests for: admit-via-runtime-owned-lineage-without-operator-hint,
    reject-when-runtime-owned-lineage-says-not-loadable,
    fall-back-to-operator-hint-when-lineage-unknown

New source-of-truth doc:

- `docs/source-of-truth/nonresident-loadability-lineage.md`

Updated source-of-truth doc:

- `docs/source-of-truth/nonresident-model-admission-policy.md`
  (section 6 now reflects the runtime-owned lineage source)

Updated execution plan:

- `docs/source-of-truth/release-readiness-execution-plan.md`
  (Stage 2 `3.3` block records the A2 outcome and what blocks ledger move)

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A2-nonresident-loadability-lineage-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not** modified;
section 5 row for `3.3` remains `open` per Hard Rule 6.

`docs/source-of-truth/master-outline.md` was not modified; the existing
master outline does not index per-contract docs, so adding two new entries
would be inconsistent with the existing convention.

`docs/source-of-truth/runtime-status-schema.md` was not modified; the new
endpoint payload is per-endpoint, not part of `runtime.status_dict()`.

`scheduler_admission_contract.py` was not modified. Integration with that
contract remains deferred and is still recorded in
`missing_signals.scheduler_admission_integration` as before.

## 4. Commands and Results

```text
$ pytest -q tests/test_nonresident_loadability_lineage.py
... 12 passed in 0.22s

$ pytest -q tests/test_nonresident_model_admission_policy.py
... 16 passed in 0.23s

$ pytest -q tests/test_nonresident_loadability_lineage.py \
            tests/test_nonresident_model_admission_policy.py \
            tests/test_model_lineage.py \
            tests/test_runtime_model_visibility.py
... 52 passed in 0.27s

$ pytest -q tests/test_runtime_server.py -k "nonresident or visibility or models"
... 2 passed, 35 deselected in 0.25s

$ pytest -q tests/test_model_residency_policy.py \
            tests/test_memory_pressure_contract.py \
            tests/test_recovery_supervisor_contract.py \
            tests/test_scheduler_admission_contract.py \
            tests/test_orchestration_status.py
... 41 passed in 0.26s

$ python3 -m py_compile \
    owlmlx/nonresident_loadability_lineage.py \
    owlmlx/nonresident_model_admission_policy.py \
    owlmlx/runtime/server.py
(compile OK)

$ git diff --check
(clean)
```

The A2 prompt's suggested verification command set ran as written. No
substituted commands.

## 5. Endpoint And Sample Decisive Fields

`GET /v1/runtime/nonresident-loadability-lineage?model_id=fake-target`

Sample payload (with runtime-owned lineage_records and visibility registry
connected at app construction):

```json
{
  "contract": {
    "surface": "owlmlx.nonresident_loadability_lineage",
    "version": "v1",
    "stable_sections": [
      "summary", "reason", "visibility", "lineage",
      "blocking_signals", "decision_support", "inputs", "missing_signals"
    ]
  },
  "summary": {
    "status": "partial",
    "decision": "known_loadable",
    "target_model_id": "fake-target",
    "confidence": "medium",
    "supported_decisions": ["known_loadable", "not_loadable", "unknown"]
  },
  "reason": {
    "code": "target_visible_lineage_valid_and_aligned_with_local_artifact"
  },
  "visibility": {
    "registered": true,
    "visible": true,
    "block_reason": null,
    "local_model_dir": "/tmp/.../fake-target",
    "config_path": "/tmp/.../fake-target/config.json"
  },
  "lineage": {
    "record_present": true,
    "validation_valid": true,
    "validation_missing_fields": [],
    "target_alignment": "aligned"
  },
  "inputs": {
    "visibility_truth_status": "runtime_owned_connected",
    "loadability_lineage_truth_status": "runtime_owned_connected"
  }
}
```

`GET /v1/runtime/nonresident-model-admission-policy?model_id=fake-target`
(no `known_loadable_model_ids` query) under the same connected registry:

```json
{
  "summary": {"decision": "admit_and_load", "target_model_id": "fake-target"},
  "reason": {"code": "non_resident_target_runtime_owned_loadability_lineage_admit"},
  "inputs": {
    "known_loadable_model_ids": [],
    "known_loadable_truth_status": "missing",
    "loadability_lineage": {
      "decision": "known_loadable",
      "loadability_lineage_truth_status": "runtime_owned_connected",
      "policy_surface": "owlmlx.nonresident_loadability_lineage"
    }
  }
}
```

## 6. Does `admit_and_load` Still Require `known_loadable_model_ids`?

**No.** When `loadability_lineage` is connected at `create_app(...)` and
returns `known_loadable`, `nonresident_model_admission_policy` returns
`admit_and_load` with reason code
`non_resident_target_runtime_owned_loadability_lineage_admit`, with
`inputs.known_loadable_model_ids == []` and
`inputs.known_loadable_truth_status == "missing"`. Verified by:

- `tests/test_nonresident_model_admission_policy.py
  ::test_nonresident_admission_admits_via_runtime_owned_loadability_lineage_without_operator_hint`
- `tests/test_nonresident_loadability_lineage.py
  ::test_runtime_endpoint_returns_known_loadable_and_admits_without_operator_hint`
  (HTTP integration test using `tmp_path` to create a real model_id config
  artifact)

The legacy `known_loadable_model_ids` path is preserved only as a labeled
fallback when the runtime-owned lineage source is not connected.

## 7. Status Of `runtime_owned_non_resident_loadability_lineage`

**Closed at the contract level, pending B-review for floor closure.**

The signal is now produced by a runtime-owned contract
(`owlmlx.nonresident_loadability_lineage`) rather than a request hint. The
admission policy's `missing_signals` removes
`runtime_owned_non_resident_loadability_lineage` whenever the new contract
is connected and decisive (`known_loadable` or `not_loadable`). It only
remains visible when the contract returns `unknown` (registry not
connected), which is the honest unconnected state.

## 8. Release Backlog Section 5 Movement

**Not moved.** The row for `3.3 residency non-resident path` in
`docs/source-of-truth/release-readiness-backlog.md` still reads:

```text
| 3.3 residency non-resident path | open | -- | model-residency-policy.md |
```

Per A2 prompt Hard Rule 6, the ledger move waits for B review.

## 9. Lane Constraints Confirmation

- No automatic loader was implemented. `/v1/load` and `/v1/unload` remain
  the explicit operator surfaces for actually changing residency.
- No floor `3.2` eviction-ordering or eviction-execution work was
  introduced. `over_budget` still rejects with the named eviction-policy
  blocker pointing at floor `3.2`.
- No `GenerationGate` invariants were weakened. The admission policy
  preserves `max_concurrent_1_after_gate_claim`,
  `ticketed_fifo_after_gate_claim`, `no_post_claim_gate_bypass`, and
  `pre_claim_decision_only` under `preserved_invariants`. The new
  loadability contract does not touch `serving.py` or `runtime/kernel.py`
  claim-side code.
- `model_lineage.py` was not replaced. The new contract consumes
  `validate_model_lineage` and `normalize_model_lineage` only.
- No work moved into `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent`.
- Floor `3.3` is **not** marked closed in
  `release-readiness-backlog.md`. Outcome label is
  `candidate_closed_pending_review`.
- Pre-existing staged/dirty changes outside this lane were preserved.

## 10. Exact Next Step For B Review

Authorize a B-review round (recommended model: `opus-4.7`) to:

1. Re-run the A2 verification command set above and confirm clean output.
2. Read `owlmlx/nonresident_loadability_lineage.py`,
   `owlmlx/nonresident_model_admission_policy.py` (integration changes),
   and the two HTTP routes in `owlmlx/runtime/server.py`.
3. Verify that the prompt's Tripwires hold: no automatic loader, no
   `3.2` eviction logic, no post-claim gate bypass, no request-level hint
   smuggled in as runtime truth.
4. Confirm that the round trip in admission policy now flows through
   residency + pressure + recovery + loadability lineage.
5. Recommend either:
   - `closed` — coordinator flips `release-readiness-backlog.md` section 5
     row `3.3` from `open` to `closed (via runtime-owned loadability
     lineage)` and updates section 2 floor count from `1/7` to `2/7`, or
   - `still_progressed` with the exact remaining sub-blocker if any
     literal section-3.3 requirement is still unmet.
