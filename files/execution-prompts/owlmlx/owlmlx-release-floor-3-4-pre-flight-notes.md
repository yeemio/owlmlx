# owlmlx Release Floor 3.4 Pre-Flight Notes

> Status: pre-flight notes only — NOT the 3.4A execution prompt
> Updated: 2026-04-26
> Author lane: Opus (during 3.2C wait, while gpt-5.4 runs independent
> closure review on 3.2)
> Scope: read-only verification of two coordination questions surfaced in
> the 3.4 preview, before authoring the 3.4A prompt

This document does not author the 3.4A prompt, does not edit any runtime
code, does not change tests, and does not move any release ledger row.
Its only purpose is to keep the eventual 3.4A prompt honest by verifying
two assumptions in the preview.

## 1. Question 1: Is `restart_exhausted_models` Real Or A Dead Branch?

**Real, but indirect.** The data path is:

1. `owlmlx/runtime/mlx_lm_subprocess_backend.py` tracks per-model
   `restart_count` against `max_restart_attempts` (default 1; see line
   `581-590`).
2. When `restart_count >= self.max_restart_attempts` and
   `auto_restart_dead_session` is not allowed, the subprocess backend
   appends the model_id to a local `restart_exhausted_models: list[str]`
   (lines `2285`, `2290-2293`).
3. The same backend exposes that list under
   `status().detail["recoverability"]["restart_exhausted_models"]`
   (line `2372`).
4. `RuntimeKernel.status_dict()` forwards it into the runtime status
   payload at `restart.restart_exhausted_models`
   (`owlmlx/runtime/kernel.py:1047-1052` reading from
   `backend_detail["recoverability"]`).
5. `recovery_supervisor_contract.build_recovery_supervisor_contract`
   reads `restart.restart_exhausted_models` and triggers
   `recovery_state = "restart_exhausted"` /
   `barrier_decision = "operator_recovery_required"`
   (`owlmlx/recovery_supervisor_contract.py:64-71, 121-128`).

**What 3.4A must know:**

- The signal is populated only by the subprocess backend's session-death
  + auto-restart-disabled path. **`FakeBackend` never populates it.**
  All current unit tests exercising `restart_exhausted` recovery branches
  use injected raw `runtime_status` payloads (see
  `tests/test_recovery_supervisor_contract.py`,
  `tests/test_memory_pressure_contract.py`,
  `tests/test_orchestration_status.py`), not real backend behavior.
- `RuntimeKernel.restart_model` itself does **not** append to
  `restart_exhausted_models`. The kernel-level restart helper does not
  have its own attempt counter; the subprocess backend owns that.
- A 3.4 termination-cause class for "load failure" therefore cannot rely
  solely on `restart_exhausted_models` to detect repeated load attempts
  failing. The 3.4 policy must either:
  - extend the kernel/backend to track explicit load-stage failure
    events for FakeBackend-equivalent paths, OR
  - explicitly scope "load failure" to `LoadResult.ok == False` at the
    operation boundary (single-shot, no retry counter), and record it as
    a termination-cause event there.

The honest framing: `restart_exhausted_models` is a real but
**session-death-specific** restart-exhaustion signal, not a general
load-failure signal.

## 2. Question 2: Does The Parked `failed-unload-reclaim-barrier-event` Prompt Overlap With 3.4?

**Yes, as a prerequisite/sub-component of 3.4, not a competitor.** The
parked prompt covers a strict subset of 3.4's required termination-cause
vocabulary.

Mapping the parked prompt's barrier-state vocabulary against the 3.4
backlog's four required termination cause classes:

| Backlog termination cause | Parked-prompt coverage |
| --- | --- |
| graceful unload (when it fails) | ✓ `failed_unload` (explicit `RuntimeKernel.unload_model` reaching `backend.unload` with `ok=False`) |
| load failure | ✗ not covered (parked prompt explicitly says restart load-stage failure is "context only") |
| OOM-class failure | ✗ not covered |
| host forensics anomaly | ✗ not covered |

Additionally, the parked prompt's outcome labels are
`*_barrier_event_introduced` / `*_still_blocked`. It produces an event
recording surface, not a frozen four-action policy
(`retry / quarantine / surface_to_coordinator / drop`). It also covers
two extra reclaim-context events (`failed_reclaim`, `restart_unload_failed`)
which 3.4's policy will plausibly map under
"graceful unload (when it fails)" plus "load failure" depending on stage.

Two honest sequencing options:

- **Option A: absorb into 3.4A.** Author 3.4A so the first deliverable is
  the failed-unload/reclaim event surface (the parked prompt's contract),
  and the second deliverable is the four-class termination-cause →
  four-action mapping plus exercised tests. One A round produces both.
  Risk: A round is large; B reviewer must check both layers in one pass.
- **Option B: run parked prompt as 3.4A0, then 3.4A on top.** The parked
  prompt becomes a sub-round that closes only the event-recording
  contract. 3.4A then layers the policy on top, consuming the events for
  graceful-unload-failure and load-failure cause classes.
  Risk: two rounds instead of one; ledger row stays open longer; but
  each round is smaller and B-review boundary is cleaner.

Coordinator should pick A or B before authoring 3.4A. Either is honest.

## 3. Boundary Watch (Carry-Forward For 3.4A Or 3.4A0+3.4A)

These constraints from the 3.4 preview hold under either sequencing
option:

- do not introduce `automatic_recovery_supervisor_loop`
  (`recovery_supervisor_contract.py` section 7 explicitly disclaims it;
  3.4 closure requires a frozen policy + exercised tests, not a daemon)
- preserve `abort_recovery.py` self-containment (no `httpx`, no
  `asyncio` deps; Phase 42 R3A truth)
- preserve `GenerationGate` invariants (`max_concurrent = 1`,
  `ticketed_fifo`, no post-claim bypass)
- preserve `pinned_models_never_evicted` invariant (carried forward
  from `memory-pressure-eviction-policy.md`)
- 4 termination cause classes minimum: load failure, OOM-class failure,
  host forensics anomaly, graceful unload (per backlog 3.4 literal)
- 4 action vocabulary: `retry / quarantine / surface_to_coordinator /
  drop` (per backlog 3.4 literal)
- policy must be exercised in tests, not only described
- TerminationCause likely needs first-class identity (extending
  `RuntimeErrorCode` is risky given many existing consumers; a new
  `TerminationCause` enum next to `RuntimeErrorCode` is cleaner
  separation)

## 4. What This Note Is Not

- not the 3.4A execution prompt
- not authorization to start 3.4 work
- not a ledger move
- not a runtime-code change

The correct sequencing remains:

1. `gpt-5.4` runs `3.2C` independent closure review and (if pass) flips
   the `3.2` ledger row
2. coordinator authors `3.4A` (or `3.4A0` + `3.4A`) per Option A vs B
   above
3. only then does executor work begin on 3.4

## 5. Files Read For This Note

Read-only:

- `owlmlx/runtime/kernel.py` (lines around 1040-1062)
- `owlmlx/runtime/mlx_lm_subprocess_backend.py` (greps at 581, 1643,
  2285-2293, 2372)
- `owlmlx/recovery_supervisor_contract.py` (lines 52-71, 121-128)
- `owlmlx/memory_pressure_contract.py` (line 198)
- `owlmlx/multi_model_governance_status.py` (lines 19, 50, 130, 199)
- `files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`
  (full)

No files were edited.
