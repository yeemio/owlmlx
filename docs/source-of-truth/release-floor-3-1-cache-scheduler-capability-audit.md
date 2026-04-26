# owlmlx Release Floor 3.1: Cache Scheduler Capability Audit (B Lane)

> Status: authoritative audit, read-only
> Updated: 2026-04-25
> Lane: Executor B (parallel to Executor A red-gate restoration)
> Scope: independent evidence map of non-exactness scheduler capability on the
> active runtime path

## 1. Purpose

Answer one narrow question independently of A's red-gate work:

**Does `owlmlx` already own a non-exactness cache scheduler capability on the
active runtime path, and if not, what is the smallest missing runtime/test
gap?**

This document is evidence mapping, not floor closure. It cannot mark floor 3.1
closed and does not state any release/parity/replacement claim.

## 2. Files Inspected (Read-Only)

Truth docs:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/phase45-dominant-gap-reselection.md`
- `docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
- `docs/source-of-truth/phase45-request-aggregation-active-seam.md`
- `docs/source-of-truth/replacement-grade-stability-gaps.md`

Runtime code:

- `owlmlx/serving.py` (`GenerationGate.execute_cohort_with_admission`,
  `execute_async_cohort_with_admission`,
  `stage_admission`, `stream_session_with_admission*`,
  `status.pre_gate_admission` block)
- `owlmlx/runtime/kernel.py` (`RuntimeKernel.generate` cohort dispatch path
  via `backend.generate_cohort`)
- `owlmlx/cache_request_aggregation_active_seam.py` (frozen seam record only)
- `owlmlx/cache_cohort_to_child_exchange_handoff_harness.py` (live runtime
  harness)
- `owlmlx/cache_child_exchange_aggregated_dispatch_harness.py` (backend-only
  harness)

Tests:

- `tests/test_serving_pre_gate_admission_hook.py`
- `tests/test_cache_cohort_to_child_exchange_handoff_harness.py`
- `tests/test_cache_child_exchange_aggregated_dispatch_harness.py`
- `tests/test_runtime_kernel.py`
- `tests/test_cache_request_aggregation_active_seam.py`
- `tests/test_cache_pre_gate_admission_window_seam.py`
- `tests/test_customer_runtime_evidence.py`
- `tests/test_dominant_gap_reselection.py`

## 3. Changed Files

None. This lane is read-only audit.

The only write performed is this audit report itself (allowed by the prompt's
optional write scope).

## 4. Commands and Results

```text
$ pytest -q tests/test_cache_request_aggregation_active_seam.py
... 15 passed in 0.08s

$ pytest -q tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py
... 27 passed in 0.75s

$ pytest -q tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py
... 60 passed in 19.05s

$ pytest -q tests/test_cache_cohort_to_child_exchange_handoff_harness.py \
         tests/test_cache_child_exchange_aggregated_dispatch_harness.py
... 3 passed in 0.15s

$ pytest -q tests/test_cache_pre_gate_admission_window_seam.py
... 5 passed in 0.08s

$ git diff --check
(clean)
```

Note on the A-owned red-gate baseline: in the current worktree the staged
restoration of `tests/test_cache_pre_gate_admission_window_seam.py` and
`owlmlx/cache_request_aggregation_active_seam.py` is already present, so the
five tests in that file currently pass. B does not modify either file. A's
final verdict is the authoritative one for that gate.

## 5. Audit Question Answers

### Q1. Does a bounded request-aggregation cohort form before whole-request gate claim on the active runtime path?

**Yes, on the active runtime path.**

Evidence:

- `GenerationGate.stage_admission` reserves a ticket without claiming the
  whole-request gate, joins an open cohort window if available, and seals the
  cohort via `_seal_expired_open_cohort_locked` before any claim.
- `GenerationGate.status["pre_gate_admission"]["hook_boundary"]` is
  `"before_whole_request_gate_claim"` and `cohort_window_status` advances
  through `open_for_join` -> `closed_waiting_gate_claim`.
- `tests/test_serving_pre_gate_admission_hook.py
  ::test_pre_gate_hook_exists_before_claim_without_reopening_post_claim_invariants`
  proves a midflight observation with `peak_cohort_size >= 2`,
  `total_staged >= 2`, `cohort_count >= 1`, `hook_boundary` ==
  `before_whole_request_gate_claim`, while final state preserves
  `max_concurrent == 1`, `queue_policy == ticketed_fifo`, `total_served == 2`.

### Q2. Does any test or live path prove one child exchange carries multiple requests in a repeated or runtime-like run?

**Yes for a single concurrent pair under one runtime-kernel-driven run; not
yet proven across repeated runs in a loop.**

Evidence:

- `tests/test_cache_child_exchange_aggregated_dispatch_harness.py
  ::test_cache_child_exchange_aggregated_dispatch_harness_exposes_single_exchange_batch`
  asserts `exchange_count == 1`, `batch_size == 2`,
  `aggregated_request_count == 2`, `aggregated_dispatch_visible is True`,
  `child_exchange_mode == "aggregated_non_stream_child_exchange_visible"`,
  with the real `MlxLmSubprocessBackend` and a probe runner. This is
  backend-level proof.
- `tests/test_cache_cohort_to_child_exchange_handoff_harness.py
  ::test_cache_cohort_to_child_exchange_handoff_harness_observes_main_path_handoff`
  asserts the **main runtime path through `RuntimeKernel`** (two concurrent
  `kernel.generate(prompt)` via `asyncio.gather`) lands in one aggregated
  child exchange: `aggregated_batch_count >= 1`,
  `aggregated_request_count >= 2`, `max_aggregated_batch_size >= 2`,
  `gate_total_served == 2`, `gate_total_queued == 2`, `max_concurrent == 1`,
  `queue_discipline == "serial"`, `handoff_request_count >= 2`. This is the
  smoking-gun runtime-path proof.

Gap:

- The harness runs the gather pair **once** with N=2. Floor 3.1 language
  ("under repeated load", "in tests under repeated runs") is therefore not
  yet matched by an explicit repeated-iteration test.

### Q3. Is aggregated dispatch observable as behavior, not just as a frozen seam record?

**Yes, as behavior.**

Evidence:

- `MlxLmSubprocessBackend.status().detail["cache_runtime_observations"]`
  exposes runtime-observed counters used by both harnesses:
  - `aggregated_child_exchange_visible`
  - `aggregated_child_exchange_batch_count`
  - `aggregated_child_exchange_request_count`
  - `max_aggregated_child_batch_size`
  - `child_exchange_mode`
- `GenerationGate.status["pre_gate_admission"]` also exposes runtime-observed
  counters: `cohort_handoff_status` ==
  `active_to_aggregated_child_exchange` while a cohort handoff is live,
  `total_handoffs`, `last_handoff_request_count`,
  `active_handoff_request_count`.
- The frozen seam record at `owlmlx.cache_request_aggregation_active_seam` is
  documentation of marker exactness, not where the capability proof lives.
  The capability proof lives in the two harnesses cited under Q2.

### Q4. Does stream hold still prevent dispatch-level closure?

**On the stream branch, yes; on the non-stream main path, no.**

Evidence:

- `stream_secondary_status` in both harnesses is hard-coded as
  `stream_session_holds_gate_until_completion`. This matches
  `phase45-request-aggregation-active-seam.md` section 3 selected-seam
  status (stream exchange holds serial boundary at the runtime-owned
  boundary-stem detection point).
- `RuntimeKernel.generate_stream` and `generate_stream_messages` use
  `stream_session_with_admission_sync`, which holds the gate for the full
  streaming turn after pre-gate cohort admission. There is no aggregated
  child-exchange path on the stream branch yet.
- The active blocker named by source-of-truth remains
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`.

So stream dispatch-level closure is still open. Non-stream dispatch-level
closure on the main runtime path is functionally already present and tested.

### Q5. What is the smallest missing runtime signal or test needed for floor 3.1 to progress after Executor A restores the red gate?

**Smallest missing piece is a repeated-load test, not new runtime code.**

Recommended (do not implement here; coordinator-assigned after A's gate is
final):

- A new test, e.g.
  `tests/test_cache_cohort_to_child_exchange_handoff_repeated_load.py`, that
  runs `run_cache_cohort_to_child_exchange_handoff_harness()` in a loop
  (suggested 3 iterations, each with 2-3 prompts) and asserts:
  - `aggregated_batch_count` increments by at least 1 per iteration
  - `aggregated_request_count` accumulates monotonically (≥ N_iters · prompts)
  - `total_handoffs` (from `kernel.status_dict()["generation_gate"]
    ["pre_gate_admission"]["total_handoffs"]`) ≥ N_iters
  - `max_concurrent == 1`, `queue_discipline == "serial"` preserved across
    every iteration
  - `child_exchange_mode == "aggregated_non_stream_child_exchange_visible"`
    observed each iteration

Optional secondary deliverable (still test-only, no new runtime code):

- One test asserting that `GenerationGate.status["pre_gate_admission"]
  ["cohort_handoff_status"]` is observed as
  `active_to_aggregated_child_exchange` mid-flight (not only `visible`),
  proving handoff is concurrent rather than after-the-fact.

No new runtime implementation appears necessary to satisfy the
**non-stream** language of floor 3.1. The runtime path already exists at
`RuntimeKernel.generate -> GenerationGate.execute_async_cohort_with_admission
-> backend.generate_cohort` and is observable through both gate and backend
runtime status.

## 6. Does Current Evidence Satisfy Release Floor 3.1?

**No, by audit rules; substantively close on the non-stream branch.**

Floor 3.1 in `release-readiness-backlog.md` requires:

- one closed non-exactness scheduler capability on the active runtime path
- closure visible in `tests/` under repeated runs
- failing seam tests reach green or are honestly downgraded

What is in place:

- bounded request-aggregation cohort before gate claim — present and tested
- aggregated child-exchange dispatch on the non-stream main path — present
  and tested at single-iteration N=2 via main-path RuntimeKernel
- runtime-observable counters proving behavior, not only frozen records
- A's red-gate work for `test_cache_pre_gate_admission_window_seam.py` is
  staged in the current worktree and the file currently shows 5/5 green; A
  remains the authoritative owner of that verdict

What is missing for honest closure:

- explicit repeated-run instrumentation in `tests/` (per release-floor
  language)
- stream-branch dispatch-level closure remains open (still active blocker
  per phase45 source-of-truth)

Therefore floor 3.1 is **substantively progressed** but not closed by audit
alone, per Hard Rule 1.

## 7. Lane Constraints Confirmation

- No other release floor was worked or claimed reduced by this audit.
- No release, parity, replacement, or production-grade claim was made.
- No A-owned red-test or runtime files were modified by B.
- Only this audit document was written.

## 8. Outcome Label

`owlmlx_release_floor_3_1B_scheduler_capability_audit_completed`
