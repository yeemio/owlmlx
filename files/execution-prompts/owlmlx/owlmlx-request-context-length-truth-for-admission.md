# owlmlx Execution Prompt: Request Context-Length Truth For Recovery-Aware Admission

> Target repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Coordinator decision: do request context-length truth before failed unload/reclaim barrier events or stream-hold counters.

## Coordination Truth

The current staged baseline already owns these runtime surfaces:

- `owlmlx.scheduler_admission_contract`
- `owlmlx.model_residency_policy`
- `owlmlx.memory_pressure_contract`
- `owlmlx.recovery_supervisor_contract`
- `owlmlx.orchestration_status`

The latest admission round made hard recovery barriers fail closed:

- `contaminated`
- `restart_exhausted`
- `backend_unhealthy`

It also kept `probing` honest: `probing` is a high-context-only recovery
barrier signal, but it cannot reject or defer ordinary requests until admission
owns request context-length truth.

This round closes that specific semantic gap.

## Objective

Introduce a narrow runtime-owned request context-length truth layer and make
`scheduler_admission_contract` consume it so recovery `probing` becomes
decisive only for known high-context requests.

Allowed outcome labels:

- `owlmlx_request_context_length_truth_for_admission_introduced`
- `owlmlx_request_context_length_truth_for_admission_still_blocked`

## Hard Rules

1. Do not implement failed unload/reclaim barrier events in this round.
2. Do not implement stream-hold counters or duration tracking in this round.
3. Do not implement continuous batching, multi-worker scheduling, or hidden
   post-claim parallelism.
4. Do not change `max_concurrent=1`, `ticketed_fifo`, or whole-request
   `GenerationGate` claim semantics.
5. Do not call a model tokenizer in a way that forces model load or changes
   runtime residency.
6. Do not claim exact token accounting unless the token count is explicitly
   supplied or is produced by an already-owned tokenizer path with tests.
7. Do not import `llm_router`, `ops_dashboard`, desktop UI code, or
   `/Users/yeemio/AI/Agent` modules.
8. Unknown context length must stay explicit as `unknown`; it must not be
   narrated as short, safe, exact, or replacement-ready.

## Required Read Order

Read these current files before editing:

1. `owlmlx/scheduler_admission_contract.py`
2. `owlmlx/recovery_supervisor_contract.py`
3. `owlmlx/context_concurrency.py`
4. `owlmlx/runtime/server.py`
5. `docs/source-of-truth/scheduler-admission-contract.md`
6. `docs/source-of-truth/recovery-supervisor-contract.md`
7. `docs/source-of-truth/runtime-status-schema.md`
8. `tests/test_scheduler_admission_contract.py`
9. `tests/test_recovery_supervisor_contract.py`
10. `tests/test_runtime_server.py`

## Required Design Shape

Add a narrow runtime-owned contract, preferably:

- `owlmlx/request_context_length_truth.py`
- `REQUEST_CONTEXT_LENGTH_TRUTH_SURFACE = "owlmlx.request_context_length_truth"`

The contract should answer only:

**Given a request's runtime-visible context-length signal, is this request known
high-context, known non-high-context, or unknown for admission purposes?**

Use existing runtime truth from `owlmlx/context_concurrency.py`:

- `HIGH_CONTEXT_THRESHOLD_TOKENS`
- `is_high_context(...)`
- `gate_entry_for_context(...)`
- `concurrency_gate_snapshot()`

Suggested stable sections:

- `summary`
- `classification`
- `thresholds`
- `source`
- `policy_boundaries`
- `missing_signals`

Suggested classification vocabulary:

- `high_context`
  - only when an owned or explicitly supplied token count is greater than
    `HIGH_CONTEXT_THRESHOLD_TOKENS`
- `non_high_context`
  - only when an owned or explicitly supplied token count is at or below
    `HIGH_CONTEXT_THRESHOLD_TOKENS`
- `unknown`
  - when no trustworthy token count exists

If you add an estimate based on characters or payload shape, mark it as an
estimate with low confidence. Do not call it exact token truth.

## Admission Semantics To Implement

Refresh `owlmlx.scheduler_admission_contract` so it consumes the context-length
truth.

Decision ordering must remain:

1. Unknown request class and unsupported maintenance semantics stay as currently
   defined.
2. Backend unhealthy and hard recovery barriers still reject before ordinary
   admission checks.
3. `probing` high-context-only recovery barrier becomes decisive only when
   request context is known `high_context`.
4. Known `high_context` + recovery `probing` should defer admission with a new
   explicit reason code, for example:
   `recovery_probing_high_context_deferred`.
5. Known `non_high_context` + recovery `probing` must not be rejected or
   deferred just because probing exists.
6. `unknown` context + recovery `probing` must surface the missing signal but
   must not become a fake global rejection of ordinary requests.

Do not use `rejected` for `probing`; reserve `rejected` for hard barriers such
as `contaminated`, `restart_exhausted`, and `backend_unhealthy`.

## Runtime Transport

The existing transport is:

- `GET /v1/runtime/scheduler-admission-contract`

Extend it narrowly enough to exercise this contract, for example with optional
query parameters such as:

- `context_tokens`
- `request_context_class`

Choose the smallest clean shape that fits the existing FastAPI route and tests.
If you add a separate diagnostic endpoint such as
`GET /v1/runtime/request-context-length-truth`, keep it read-only and side-effect
free.

Do not wire this into full generation enforcement unless the current runtime
path already has a clean contract hook for doing so. This round is about
runtime-owned truth and admission contract correctness, not a broad dispatcher
rewrite.

## Required Documentation Updates

Update or add source-of-truth docs so the new boundary is reconstructible:

- `docs/source-of-truth/request-context-length-truth.md`
- `docs/source-of-truth/scheduler-admission-contract.md`
- `docs/source-of-truth/recovery-supervisor-contract.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/orchestration-status-surface.md` if the composed
  status changes
- `docs/source-of-truth/runtime-capability-matrix.md` only if a capability label
  changes

The docs must explicitly state:

- request context-length truth is admission support, not full tokenizer parity
- `probing` is high-context-only and defers only known high-context requests
- unknown context remains unknown
- failed reclaim/unload and stream-hold counters remain out of scope

## Required Tests

Add or update tests for:

- request context-length contract classifies explicit low token counts as
  `non_high_context`
- request context-length contract classifies explicit high token counts as
  `high_context`
- missing context length remains `unknown`
- recovery `probing` + known `high_context` defers admission
- recovery `probing` + known `non_high_context` does not reject/defer solely
  because of probing
- recovery `probing` + `unknown` context preserves the previous non-global
  behavior and surfaces the missing signal
- hard recovery barriers still reject regardless of context length
- route-level coverage for the updated scheduler admission transport
- no platform dependency enters the new module

## Required Checks

Run at minimum:

```bash
pytest -q tests/test_request_context_length_truth.py
pytest -q tests/test_scheduler_admission_contract.py tests/test_recovery_supervisor_contract.py
pytest -q tests/test_orchestration_status.py tests/test_runtime_server.py -k "scheduler_admission_contract or recovery_supervisor or orchestration_status or request_context"
python3 -m py_compile owlmlx/request_context_length_truth.py owlmlx/scheduler_admission_contract.py owlmlx/runtime/server.py
git diff --check
```

If a named new test file is not needed because the executor folds tests into an
existing file, state that explicitly in the final report.

## Final Report

Return:

- outcome label
- changed files
- exact commands and results
- new context-length truth vocabulary
- how `probing` now affects high-context admission
- what remains unknown
- confirmation that failed unload/reclaim barrier events and stream-hold
  counters were not implemented in this round

If the round is still blocked, do not broaden scope. Report the smallest
blocking signal needed to make context-length truth honest.
