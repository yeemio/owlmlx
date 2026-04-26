# owlmlx Execution Prompt: Release Floor 3.5 Comparative Evidence Schema And Record Surface

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes`
> Coordination note: this is a parallel schema/surface preparation lane. It does
> not supersede the floor `3.1` cache-scheduler burn-down lane.

## Mission

Turn the newly frozen comparative-evidence contract from docs-only truth into a
runtime-owned schema and record surface that `owlops` can consume without field
drift.

Do not fake benchmark readiness.
Do not emit a `measured` verdict unless an identical workload actually ran
against `owlmlx` and at least one reference runtime on the same host with the
required artifacts.

## Coordination Truth

Read these first:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/comparative-evidence-schema-stub.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
- `docs/source-of-truth/reference-runtime-comparison-matrix.md`
- `owlmlx/runtime/server.py`
- `scripts/runtime_customer_runtime_evidence.py`
- `tests/test_runtime_server.py`
- `tests/test_customer_runtime_evidence.py`

Cross-repo consumer truth:

- `owlops` must consume `host_class`, `workload_class`, and `verdict_grade`
  from the `owlmlx` wire/schema truth
- `owlops` must not locally recalculate verdicts or redeclare enum authority

## Objective

Implement the first runtime-owned comparative-evidence surface:

- a single authoritative code schema source for field names and enumerations
- `build_comparative_evidence_record(...)`
- `comparative_evidence_record_to_dict(...)`
- a read-only HTTP surface for latest/current record shape
- an operator script that can emit or append a record honestly
- tests that prove required fields, enum values, banned verdict vocabulary, and
  HTTP shape

Allowed outcome labels:

- `owlmlx_release_floor_3_5_comparative_evidence_schema_surface_introduced`
- `owlmlx_release_floor_3_5_comparative_evidence_record_surface_progressed`
- `owlmlx_release_floor_3_5_comparative_evidence_surface_closed`
- `owlmlx_release_floor_3_5_comparative_evidence_still_blocked`

Use `surface_closed` only if every criterion in
`comparative-evidence-harness-contract.md` section 8 is true, including at
least one honest `measured` ledger record and stable HTTP consumption.

## Hard Rules

1. Do not claim release readiness, parity, replacement, production-grade, or
   superiority.
2. Do not use banned verdict words from `comparative-evidence-schema-stub.md`
   section 4.8 or harness contract section 5.1.
3. Do not emit `verdict_grade = "measured"` without a real same-host
   owlmlx-vs-reference workload run and raw artifacts.
4. Do not silently skip missing reference runtimes; emit `rejected` or
   `inconclusive` with a frozen reason.
5. Do not implement scheduled continuous benchmarking.
6. Do not implement quality / accuracy evaluation.
7. Do not change release floor `3.1` files or cache scheduler tests in this
   round.
8. Do not import `owlops`, desktop UI code, or `/Users/yeemio/AI/Agent` modules.
9. Keep unrelated dirty worktree changes untouched.
10. Keep floor `3.5` open unless the measured-record closure criteria are met.

## Required Design Shape

Prefer this module split:

- `owlmlx/comparative_evidence_schema.py`
  - single authoritative location for field names, enumerations, banned verdict
    tokens, and required measurement keys
- `owlmlx/comparative_evidence_record.py`
  - dataclass or typed builder for the record
  - `COMPARATIVE_EVIDENCE_RECORD_SURFACE =
    "owlmlx.comparative_evidence_record"`
  - `build_comparative_evidence_record(...)`
  - `comparative_evidence_record_to_dict(...)`

Suggested script:

- `scripts/runtime_comparative_evidence.py`

Suggested ledger:

- `docs/source-of-truth/comparative-evidence-ledger.md`

Suggested HTTP endpoints:

- `GET /v1/runtime/comparative-evidence`
- `GET /v1/runtime/comparative-evidence/history`

If the current server shape makes the history endpoint awkward, implement only
the current/latest endpoint and state that history remains file-ledger only.

## Required Semantics

### Schema Source

The runtime builder must import field names and enumerations from one
authoritative code location. Do not scatter literal enum sets across tests,
server, script, and module.

Initial enum sets must match `comparative-evidence-schema-stub.md`:

- `workload_class`
  - `single_prompt_short`
  - `single_prompt_long`
  - `multi_prompt_serial`
  - `multi_prompt_aggregated`
- `runtime_id`
  - `owlmlx`
  - `omlx`
  - `vmlx`
- `verdict_grade`
  - `measured`
  - `inconclusive`
  - `rejected`

### Record Validation

The builder must reject or fail visibly when:

- required top-level fields are missing
- required `workload_invariants` keys are missing
- required measurement fields are missing
- `verdict_grade` is outside the frozen enum
- `verdict_text` contains banned vocabulary
- `host_class` mismatches inside a same-record comparison
- `workload_invariants` do not match across runtimes

### Honest Verdicts

For this first implementation, it is acceptable to emit:

- `inconclusive`
  - when the harness surface exists but no reference run has completed
- `rejected`
  - when a configured reference runtime cannot be invoked, weights are missing,
    or host/workload invariants mismatch

It is not acceptable to emit `measured` from synthetic data or from one-sided
owlmlx-only data.

### Ledger

If adding `docs/source-of-truth/comparative-evidence-ledger.md`, keep it
append-only in structure and mark it `surface_open` until a measured record
exists.

Do not write a fake measured entry just to close the ledger.

## Required Documentation Updates

Update only what this surface needs:

- `docs/source-of-truth/comparative-evidence-schema-stub.md`
- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/master-outline.md` if a new authoritative doc is added

If floor `3.5` is not fully closed, the closure ledger in
`release-readiness-backlog.md` must remain open.

## Required Tests

Add tests for:

- schema enum values match the stub
- builder emits all required fields
- builder rejects invalid `workload_class`, `runtime_id`, and `verdict_grade`
- builder rejects banned verdict vocabulary
- builder rejects missing measurement fields
- builder rejects mismatched workload invariants across runtimes
- builder allows honest `inconclusive` / `rejected` records
- route returns the full record shape or an explicit upstream-not-ready payload
- no platform/ops dependency enters the modules

Suggested test files:

- `tests/test_comparative_evidence_schema.py`
- `tests/test_comparative_evidence_record.py`
- route coverage in `tests/test_runtime_server.py`

## Required Checks

Run at minimum:

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
pytest -q tests/test_runtime_server.py -k "comparative_evidence"
python3 -m py_compile owlmlx/comparative_evidence_schema.py owlmlx/comparative_evidence_record.py owlmlx/runtime/server.py scripts/runtime_comparative_evidence.py
git diff --check
```

If a named test file is not needed because tests are folded into existing
files, state that explicitly in the final report.

## Final Report

Return:

- outcome label
- changed files
- exact commands and results
- schema authority location
- HTTP endpoint shape
- ledger status
- whether any `measured` record exists
- whether floor `3.5` remains open or is surface-closed
- exact blocker if not surface-closed
- confirmation that no release/parity/replacement claim was made
- confirmation that floor `3.1` files were not touched

If this round is still blocked, do not broaden into scheduler or ops work.
Report the smallest missing owlmlx-owned surface or host/reference-runtime
condition.
