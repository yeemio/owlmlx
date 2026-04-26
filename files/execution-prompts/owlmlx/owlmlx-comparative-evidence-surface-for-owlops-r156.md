# owlmlx Execution Prompt: Comparative Evidence Surface For OwlOps R156

> Date: 2026-04-26
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active external blocker: OwlOps R156 live upstream proof
> Single executor: one owlmlx executor only
> Do not assign OwlOps in this round
> Required verdict: `surface_closed` or `still_blocked`

## 1. Mission

Implement and mount the `owlmlx` comparative evidence HTTP surface that OwlOps
R156 is blocked on.

The required endpoints are:

- `GET /v1/runtime/comparative-evidence`
- `GET /v1/runtime/comparative-evidence/history`

The runtime-owned product is:

- `owlmlx.comparative_evidence_record`
- `version = "v1"`

This is an `owlmlx` task. Do not edit `owlops`, `owlcoda`, or
`/Users/yeemio/AI/Agent`.

## 2. Current Coordination Truth

OwlOps is currently in waiting state:

- local comparison workspace wiring is not the narrow blocker
- R156 needs live upstream proof from a real mounted `owlmlx`
  `/v1/runtime/comparative-evidence` surface
- assigning an OwlOps executor now creates noise; OwlOps should wait until this
  `owlmlx` surface exists and is live-curl verified

Existing owlmlx contracts:

- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/comparative-evidence-schema-stub.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5-comparative-evidence-schema-and-record-surface.md`

This prompt supersedes the older broad 3.5 prompt for the immediate OwlOps
R156 blocker because the older prompt allowed the history endpoint to remain
file-ledger-only. This round requires both HTTP endpoints.

## 3. Required Read Order

Read before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/comparative-evidence-harness-contract.md`
3. `docs/source-of-truth/comparative-evidence-schema-stub.md`
4. `docs/source-of-truth/release-readiness-backlog.md`
5. `docs/source-of-truth/release-readiness-execution-plan.md`
6. `docs/source-of-truth/runtime-status-schema.md`
7. `docs/source-of-truth/reference-runtime-comparison-matrix.md`
8. `owlmlx/runtime/server.py`
9. `tests/test_runtime_server.py`
10. Existing runtime-owned evidence surface modules and tests for style:
    `owlmlx/customer_runtime_evidence.py`,
    `tests/test_customer_runtime_evidence.py`,
    `owlmlx/memory_pressure_eviction_policy.py`,
    `tests/test_memory_pressure_eviction_policy.py`

## 4. Implementation Target

Prefer this owned shape:

- `owlmlx/comparative_evidence_schema.py`
  - single authority for field names, enums, measurement keys, and banned
    verdict vocabulary
- `owlmlx/comparative_evidence_record.py`
  - `COMPARATIVE_EVIDENCE_RECORD_SURFACE =
    "owlmlx.comparative_evidence_record"`
  - `build_comparative_evidence_record(...)`
  - `comparative_evidence_record_to_dict(...)`
- `owlmlx/comparative_evidence_ledger.py` or equivalent
  - append/read latest/history from a repo-local or configured ledger path
- `scripts/runtime_comparative_evidence.py`
  - operator entry that can emit/append a real record
- `docs/source-of-truth/comparative-evidence-ledger.md`
  - append-only ledger truth if a doc ledger is introduced

Mount both endpoints in `owlmlx/runtime/server.py`.

## 5. Required HTTP Shape

`GET /v1/runtime/comparative-evidence` must return the latest complete
`comparative_evidence_record` v1 or an explicit machine-readable
`still_blocked` payload that names the missing owlmlx-owned signal.

Preferred success shape:

```json
{
  "surface": "owlmlx.comparative_evidence_record",
  "version": "v1",
  "recorded_at": "2026-04-26T00:00:00Z",
  "evidence_pointer": "docs/source-of-truth/comparative-evidence-ledger.md#...",
  "host_class": "...",
  "workload_class": "single_prompt_short",
  "workload_invariants": {
    "model_id": "...",
    "model_quantization": "...",
    "decode_max_tokens": 16,
    "decode_temperature": 0.0,
    "prompt_set_hash": "...",
    "serving_budget_bytes": 0
  },
  "runtimes": [
    {
      "runtime_id": "owlmlx",
      "runtime_version": "...",
      "measurement": {
        "throughput_tokens_per_second": 0.0,
        "first_token_latency_ms": 0.0,
        "peak_resident_set_bytes": 0,
        "wall_clock_ms": 0.0,
        "completed_request_count": 0,
        "failure_count": 1,
        "failure_causes": ["reference_runtime_unavailable"]
      }
    }
  ],
  "verdict_text": "rejected: ...",
  "verdict_grade": "rejected"
}
```

`GET /v1/runtime/comparative-evidence/history` must return a stable envelope:

```json
{
  "surface": "owlmlx.comparative_evidence_record_history",
  "version": "v1",
  "records": [ ... full v1 records ... ],
  "ledger_status": "available"
}
```

If no record exists yet, the endpoint must fail visibly as `still_blocked`.
Do not return a fake empty success that OwlOps could misread as closed.

## 6. Verdict Discipline

This round has two different closure concepts. Keep them separate:

- OwlOps R156 HTTP surface:
  - may return `surface_closed` when both endpoints are mounted, live-curl
    verified, and expose a real v1 record or honest blocked payload exactly as
    specified
- Release floor `3.5`:
  - remains open unless
    `comparative-evidence-harness-contract.md` section 8 is fully satisfied,
    including at least one honest same-host `measured` record

Do not mark release floor `3.5` closed merely because the HTTP endpoints exist.

Allowed final verdicts:

- `surface_closed`
- `still_blocked`

Use `still_blocked` if:

- either HTTP endpoint is absent
- the response omits required v1 fields
- the history endpoint is not mounted
- the record is synthetic or uses fake measured data
- live uvicorn/curl proof cannot be produced

## 7. Hard Rules

1. Do not edit OwlOps in this round.
2. Do not assign a second executor.
3. Do not emit `verdict_grade = "measured"` from synthetic data.
4. Do not use banned verdict words:
   `parity`, `equivalent`, `replaces`, `replacement`, `production-ready`,
   `superior`, `wins`, `beats`, `matches`.
5. Do not compute or render OwlOps UI state locally in owlmlx.
6. Do not declare release readiness, replacement-grade, or production-grade.
7. Do not change unrelated staged/dirty files.
8. Do not broaden into 3.2/3.4 scheduling/recovery work.

## 8. Required Tests

Add or update tests covering:

- schema enum values match `comparative-evidence-schema-stub.md`
- required top-level fields exist
- required `workload_invariants` keys exist
- required measurement fields exist
- invalid `workload_class`, `runtime_id`, and `verdict_grade` fail visibly
- banned verdict vocabulary fails visibly
- latest endpoint returns complete v1 record or explicit `still_blocked`
- history endpoint returns stable envelope and full records
- no platform/OwlOps imports enter owlmlx modules

Suggested test files:

- `tests/test_comparative_evidence_schema.py`
- `tests/test_comparative_evidence_record.py`
- `tests/test_runtime_server.py` with comparative endpoint coverage

## 9. Required Verification

Run pytest:

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
pytest -q tests/test_runtime_server.py -k "comparative_evidence"
```

Run compile checks:

```bash
python3 -m py_compile \
  owlmlx/comparative_evidence_schema.py \
  owlmlx/comparative_evidence_record.py \
  owlmlx/runtime/server.py \
  scripts/runtime_comparative_evidence.py
```

Run live HTTP proof against a real uvicorn process. Prefer a temporary port:

```bash
python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
  --factory --host 127.0.0.1 --port 8056
```

Then curl:

```bash
curl -sS http://127.0.0.1:8056/v1/runtime/comparative-evidence
curl -sS http://127.0.0.1:8056/v1/runtime/comparative-evidence/history
```

Capture decisive fields from both responses:

- `surface`
- `version`
- `verdict_grade`
- `host_class`
- `workload_class`
- `records` count for history

Finally:

```bash
git diff --check
lsof -n -iTCP:8056 -sTCP:LISTEN
```

Stop the uvicorn process and confirm no listener remains on the port.

## 10. Documentation Updates

Update only the truth surfaces required by this work:

- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/comparative-evidence-schema-stub.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/release-readiness-backlog.md` only if the floor status
  honestly changes
- `docs/source-of-truth/master-outline.md` only if a new authoritative doc is
  added

If `docs/source-of-truth/comparative-evidence-ledger.md` is added, index it in
`master-outline.md`.

## 11. Output Handoff

Write:

- `files/execution-prompts/owlmlx/owlmlx-comparative-evidence-surface-for-owlops-r156-handoff.md`

The handoff must include:

- final verdict: `surface_closed` or `still_blocked`
- changed files
- exact pytest results
- exact live uvicorn/curl results
- endpoint response decisive fields
- whether a real v1 record exists
- whether a `measured` record exists
- whether release floor `3.5` remains open
- exact remaining blocker if `still_blocked`
- confirmation OwlOps was not edited
- confirmation no second executor was assigned
