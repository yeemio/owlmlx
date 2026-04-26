# owlmlx Execution Handoff 3.2A: Memory-Pressure Eviction Decision And Execution

> Lane: Executor A (3.2A — implementation, tests, docs, runtime transport)
> Updated: 2026-04-26
> Active release floor: `3.2 Memory-Pressure Decision Closure`

## 1. Outcome Label

`owlmlx_release_floor_3_2A_memory_pressure_eviction_candidate_closed_pending_review`

## 2. Floor 3.2 Verdict

**`candidate_closed_pending_review`**, not `closed`.

The implementation now satisfies every literal section-3.2 requirement of
`release-readiness-backlog.md`:

- one runtime-owned decision surface ranks eviction candidates
  deterministically given pressure classification and residency snapshot
  (`owlmlx.memory_pressure_eviction_policy`)
- one runtime-owned execution path performs the eviction and updates
  residency and eviction-history governance surfaces together
  (`RuntimeKernel.execute_memory_pressure_eviction(...)`)
- both surfaces are tested and a repeated-pressure scenario produces an
  observable residency change

Per the 3.2A prompt's Hard Rule 6, the release ledger is **not** moved by
this round. `release-readiness-backlog.md` section 5 row for `3.2` remains
`open` until B review confirms closure and the coordinator flips the row.

## 3. Changed Files

New runtime module:

- `owlmlx/memory_pressure_eviction_policy.py`

Modified runtime modules (integration only):

- `owlmlx/runtime/kernel.py`
  - `_record_eviction_history(...)` now accepts `source: str = "ttl_policy"`
    so non-TTL eviction sources can record themselves honestly
  - new public method `execute_memory_pressure_eviction(*,
    abort_recovery_snapshot=None, protect_active=True)` builds the policy,
    refuses execution unless `decision == "evict"`, unloads the victim,
    records a `memory_pressure_evicted` event with
    `source = "memory_pressure_policy"`, and returns a structured result
  - `from typing import Any, Mapping` (added `Mapping`)

- `owlmlx/runtime/server.py`
  - new imports for `build_memory_pressure_eviction_policy`,
    `memory_pressure_eviction_policy_to_dict`
  - new request body `MemoryPressureEvictionRequest`
  - new route `GET /v1/runtime/memory-pressure-eviction-policy?protect_active=...`
  - new route `POST /v1/runtime/memory-pressure-eviction`; when the
    loadability lineage registry is connected at `create_app(...)`, the
    POST response also includes `loadability_lineage_after` for the evicted
    model

New tests:

- `tests/test_memory_pressure_eviction_policy.py` (16 tests covering all
  decision branches, candidate ordering, pinned protection, recovery hard
  barrier, kernel execution path, repeated-pressure observable residency
  change, both endpoints, and a no-platform-dependency check)

New source-of-truth doc:

- `docs/source-of-truth/memory-pressure-eviction-policy.md`

Updated source-of-truth doc:

- `docs/source-of-truth/memory-pressure-contract.md` (section 7 cross-
  references the new eviction policy and clarifies that the classification
  contract remains read-only)

Updated execution plan:

- `docs/source-of-truth/release-readiness-execution-plan.md` (section 6
  records the A round result and what blocks ledger move)

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not** modified
per Hard Rule 6. `model-residency-policy.md`,
`runtime-status-schema.md`, and `master-outline.md` were not modified —
pressure evictability semantics are unchanged for the residency contract,
the new endpoints are per-endpoint not part of `runtime.status_dict()`,
and master-outline does not index per-contract docs.

## 4. Commands and Results

```text
$ pytest -q tests/test_memory_pressure_eviction_policy.py
... 16 passed in 0.36s

$ pytest -q tests/test_memory_pressure_eviction_policy.py \
            tests/test_memory_pressure_contract.py \
            tests/test_model_residency_policy.py \
            tests/test_multi_model_eviction_history_governance.py
... 32 passed in 0.39s

$ pytest -q tests/test_nonresident_loadability_lineage.py \
            tests/test_nonresident_model_admission_policy.py
... 28 passed in 0.36s

$ pytest -q tests/test_runtime_kernel.py -k "pressure or eviction or unload or ttl"
... 8 passed, 17 deselected in 0.12s

$ pytest -q tests/test_runtime_server.py -k "pressure or eviction or residency or nonresident"
... 37 deselected in 0.29s
  (no test names match the filter in test_runtime_server.py; the new
   eviction-policy endpoint tests live in test_memory_pressure_eviction_policy.py
   and pass under the first command above. No substitution required for the
   policy proof itself.)

$ python3 -m py_compile \
    owlmlx/memory_pressure_eviction_policy.py \
    owlmlx/memory_pressure_contract.py \
    owlmlx/model_residency_policy.py \
    owlmlx/runtime/kernel.py \
    owlmlx/runtime/server.py
(compile OK)

$ git diff --check
(clean)
```

The 3.2A prompt's suggested verification matrix ran as written.

## 5. Endpoint And Sample Decisive Fields

`GET /v1/runtime/memory-pressure-eviction-policy?protect_active=true`

Sample payload under `over_budget`:

```json
{
  "contract": {
    "surface": "owlmlx.memory_pressure_eviction_policy",
    "version": "v1"
  },
  "summary": {
    "decision": "evict",
    "confidence": "medium",
    "pressure_classification": "over_budget",
    "selected_victim_model_id": "fake-c",
    "supported_decisions": ["evict", "defer", "reject", "unknown"]
  },
  "reason": {
    "code": "over_budget_with_safe_unpinned_candidate",
    "message": "..."
  },
  "selected_victim": {
    "model_id": "fake-c",
    "memory_gb": 40.0,
    "pinned": false,
    "active": false,
    "ttl_expired_unpinned": true,
    "eligible": true,
    "ordering_reason": "ttl_expired_unpinned"
  },
  "candidate_order": [
    {"model_id": "fake-c", "ordering_reason": "ttl_expired_unpinned", "eligible": true},
    {"model_id": "fake-b", "ordering_reason": "manual_unload_eligible", "eligible": true},
    {"model_id": "fake-a", "ordering_reason": "active_model_protected", "eligible": false}
  ],
  "preserved_invariants": [
    "max_concurrent_1_after_gate_claim",
    "ticketed_fifo_after_gate_claim",
    "no_post_claim_gate_bypass",
    "pinned_models_never_evicted",
    "no_automatic_background_eviction_loop"
  ]
}
```

`POST /v1/runtime/memory-pressure-eviction` body `{"protect_active": true}`
(under the same over_budget conditions):

```json
{
  "ok": true,
  "executed": true,
  "decision": "evict",
  "selected_victim": {"model_id": "fake-c", ...},
  "unload_result": {"ok": true, "model_id": "fake-c", "freed_gb": 40.0},
  "residency_after": {
    "evicted_model_id": "fake-c",
    "victim_still_resident": false,
    "active_model_id": "fake-a"
  },
  "eviction_history_event": {
    "sequence": N,
    "model_id": "fake-c",
    "event": "memory_pressure_evicted",
    "source": "memory_pressure_policy",
    "recorded_at_s": ...
  }
}
```

When the loadability lineage registry is connected, the POST response also
includes `loadability_lineage_after` reporting the evicted model's
post-eviction loadability decision.

## 6. Selected Victim Ordering Rule

Sort key in priority order (lower = higher priority):

1. `pinned == False` before pinned (`pinned_models_never_evicted`
   invariant; pinned candidates remain visible in `candidate_order` with
   `ordering_reason = "blocked_by_pin"`)
2. `ttl_expired_unpinned == True` before manual-unload-eligible
3. `active_protected == False` before active-protected (under
   `protect_active=True`, default)
4. larger `memory_gb` before smaller
5. lexical `model_id` ascending tie-break

## 7. Residency, Lineage, And Eviction-History After-State

`RuntimeKernel.execute_memory_pressure_eviction(...)` returns a single
structured snapshot containing:

- `decision_snapshot` — the full read-only policy payload at the moment of
  execution
- `selected_victim` — model_id, memory_gb, ordering_reason
- `unload_result` — ok/error, model_id, freed_gb
- `residency_after` — `evicted_model_id`, `victim_still_resident` (bool),
  `active_model_id`, `loaded_model_ids`
- `eviction_history_event` — the recorded
  `{event: "memory_pressure_evicted", source: "memory_pressure_policy", ...}`
  entry

`POST /v1/runtime/memory-pressure-eviction` additionally returns
`loadability_lineage_after` (the evicted model's
`nonresident_loadability_lineage` decision) when the loadability lineage
registry is connected. Lineage records themselves are not mutated by
eviction; the after-state simply reports whether the now-non-resident
model is still `known_loadable`, which is what floor 3.2 requires.

## 8. Repeated-Load / Repeated-Pressure Evidence

`tests/test_memory_pressure_eviction_policy.py
::test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`
loads four models, runs `execute_memory_pressure_eviction(...)` twice, and
asserts:

- both rounds produce `decision == "evict"` and `executed == True`
- two distinct victims are selected
- post-loaded set equals `initial_loaded - {victim_1, victim_2}`
- governance eviction history accumulates two events with
  `source == "memory_pressure_policy"` and the recorded model ids match
  the selected victims

This is the literal "repeated-load test showing pressure causes observable
residency change" requirement of release-readiness-backlog `3.2`.

## 9. Release Backlog Section 5 Movement

**Not moved.** Per 3.2A prompt Hard Rule 6 and section 11.

The row for `3.2 memory-pressure decision` in
`docs/source-of-truth/release-readiness-backlog.md` still reads:

```text
| 3.2 memory-pressure decision | open | -- | memory-pressure-contract.md |
```

Coordinator may flip after B review.

## 10. Lane Constraints Confirmation

- No broad reclaim engine implemented.
- No automatic background eviction loop introduced; eviction is operator-
  driven via the explicit `POST /v1/runtime/memory-pressure-eviction`
  endpoint or kernel method.
- `GenerationGate` invariants preserved. `preserved_invariants` records
  `max_concurrent_1_after_gate_claim`, `ticketed_fifo_after_gate_claim`,
  `no_post_claim_gate_bypass`, `pinned_models_never_evicted`, and
  `no_automatic_background_eviction_loop`. No edits to claim-side code in
  `serving.py` or to gate-claim flow in `runtime/kernel.py`.
- `model_lineage.py`, `runtime_model_visibility.py`, and
  `nonresident_loadability_lineage.py` were not edited; the eviction
  policy consumes them through existing builders.
- `scheduler_admission_contract.py` was not edited. Integration is
  deferred and recorded in `missing_signals.scheduler_admission_integration`.
- No work moved into `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent`.
- Floor `3.2` is **not** marked closed in
  `release-readiness-backlog.md`. Outcome label is
  `candidate_closed_pending_review`.
- Pre-existing staged/dirty changes outside this lane preserved.
- No release/parity/replacement/production-grade claim made.

## 11. Exact Next B Review Target

Authorize a B-review round (recommended model: `gpt-5.4`, or any reviewer
that did not author 3.2A) to:

1. Re-run the verification matrix in §4 above.
2. Read `owlmlx/memory_pressure_eviction_policy.py` and the kernel-side
   `execute_memory_pressure_eviction(...)` method.
3. Verify that pinned candidates are double-protected (policy
   ineligibility plus unload-side pin check) and that the pinned-only test
   indeed produces `reject`.
4. Verify that the repeated-pressure test produces two distinct victims
   and accumulates two `memory_pressure_policy` eviction-history events.
5. Verify that recovery hard barriers fail closed.
6. Recommend either:
   - `closed_recommended` — coordinator flips
     `release-readiness-backlog.md` section 5 row `3.2` from `open` to
     `closed (via runtime-owned memory-pressure eviction policy)` and
     updates section 2 floor count from `2/7` to `3/7`, or
   - `still_progressed` / `needs_fix` with the exact remaining sub-blocker
     if any literal section-3.2 requirement is still unmet.

The B-review prompt is at
`files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review.md`.
