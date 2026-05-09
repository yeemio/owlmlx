# owlmlx Coordinator Checkpoint — Memory Actuator Scaffold: landed (scaffold-grade)

## Verdict

- `memory_actuator_scaffold_landed_scaffold_grade`

This checkpoint records the close of the C-3 round on the seven-line
architectural assessment. The memory actuator surface — the missing
**execution layer** that the existing judgment layer
(`memory_budget.py`, `model_inventory.py`,
`memory_pressure_eviction_policy.py`) cannot provide — is now defined
in `owlmlx/memory_actuator.py`. Line 3 (Memory governance) of the
seven-line architectural assessment remains `partial`; this round
lands the actuator surface but does not close or promote the line.

This is **not** a promotion of any
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` row.
The scaffold landed against fake-injected mlx-shaped modules only. A
follow-up wiring round must inject a real `mx` module from a
production caller and produce measured before/after byte deltas
before any §1a Anti-Pollution Contract walkthrough can advance a
row's status.

## What This Checkpoint Is

This is a **surface-freeze marker** for the actuator layer. It says:
the shape of the actuator-vs-judgment boundary holds, the five
capabilities (release, coordinate, floor, pressure-event seam,
observability) are defined as a single ownership surface, and the
two frozen invariants (`pinned_models_never_evicted`,
`no_automatic_background_eviction_loop`) are honored at the
execution layer in a literal-text sense (no daemon, no thread,
no scheduler). It does **not** say any production caller has been
modified to inject a real `mx` module.

## What Is Now Frozen Exact

- `owlmlx/memory_actuator.py` exists and exports the public surface:
  - `MemoryActuator` class with constructor
    `__init__(self, *, mlx_module: object | None = None)` — no
    auto-import of `mlx`.
  - five capabilities:
    - **A** `release_single_model(*, model_id, declared_freed_gb) -> ReclaimReceipt`
      — sole `mlx_module.clear_cache()` call site in owlmlx; no-op
      when `mlx_module is None`.
    - **B** `coordinate_reclamation(*, eviction_decision) -> Sequence[ReclaimReceipt]`
      — accepts a dict-shape policy decision, honors
      `pinned_models_never_evicted`.
    - **C** `configure_allocator_floor(*, cache_limit_bytes,
      wired_limit_bytes) -> AllocatorFloorConfig` — wraps
      `set_cache_limit` + (when reachable) `set_wired_limit`.
    - **D** `register_pressure_listener(...)` /
      `notify_pressure(...)` — caller-driven only, no thread.
    - **E** `read_active_memory_bytes()`,
      `read_cache_memory_bytes()`, `read_peak_memory_bytes()`,
      `status_dict()`.
  - frozen records (`@dataclass(frozen=True, slots=True)` with
    `to_dict()`):
    - `ReclaimReceipt` with measure-not-declare fields
      (`active_memory_before/after_bytes`,
      `cache_memory_before/after_bytes`,
      `actuator_invoked_clear_cache`, `mlx_module_available`).
    - `AllocatorFloorConfig` with
      `wired_limit_supported: bool` (presence detected via
      `hasattr` on the injected module).
    - `PressureEventSubscription` with `subscriber_name`,
      `registered_at`, `condition`.
  - module-level constants: `MEMORY_ACTUATOR_SURFACE`,
    `MEMORY_ACTUATOR_VERSION`, `HONORED_INVARIANTS`.
- `docs/source-of-truth/memory-actuator-architecture.md` exists and
  records the ownership boundaries, mlx primitive map,
  measure-not-declare contract, no-op-when-no-mlx pattern,
  caller-driven pressure-event seam, promotion-gate coupling, and
  three deferred extension points.
- `tests/test_memory_actuator.py` exists. All tests use
  fake-injected mlx-shaped modules; none import real `mlx`, the
  native backend, or any model. Coverage spans all five
  capabilities, the no-op path, the pinned-skip path (top-level
  + residency_summary fallback), and the no-thread guarantee
  (`threading.active_count()` before/after construction +
  registration + notify must match).
- `files/execution-prompts/owlmlx/owlmlx-memory-actuator-scaffold-landing.md`
  exists and records the round's hard rules and acceptance shape.
- This checkpoint exists.

## What Is Read-Only This Round

The scaffold lands behind a strict read-only boundary on:

- `owlmlx/memory_budget.py`
- `owlmlx/model_inventory.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/memory_pressure_contract.py`
- `owlmlx/multi_model_eviction_history_governance.py`
- `owlmlx/host_pressure.py`
- `owlmlx/runtime/mlx_native_backend.py`
- `owlmlx/runtime/mlx_lm_subprocess_backend.py`
- `owlmlx/runtime/server.py`
- `pyproject.toml`, `uv.lock`, `.python-version`
- `conftest.py`, `README.md`
- every existing test file under `tests/`

No file in that set was modified by this round.

## Frozen Invariants Honored

- `pinned_models_never_evicted` — `coordinate_reclamation` skips
  victims whose `model_id` appears in the decision dict's `pinned`
  list or under `residency_summary.pinned_model_ids` before
  invoking `release_single_model`. Test
  `test_coordinate_reclamation_skips_pinned_models` and
  `test_coordinate_reclamation_skips_pinned_via_residency_summary`
  lock this contract.
- `no_automatic_background_eviction_loop` — the actuator scaffold
  contains no `threading.Thread`, no `asyncio.create_task`, no
  `concurrent.futures` executor, no `signal` handler, no `atexit`
  hook, no `sched`-style scheduler, no daemon-style `while True:`
  loop. Test `test_actuator_does_not_spawn_thread_or_daemon`
  asserts `threading.active_count()` is identical before and after
  construction, registration, and notify.

## What This Checkpoint Closes

The C-3 round lands the Line 3 actuator surface in scaffold-grade
form:

- the missing actuator surface exists,
- it honors the two execution-relevant invariants from the policy
  layer,
- callers can now thread a `MemoryActuator` instance to receive
  shaped receipts without committing the runtime path to actual
  release,
- the architecture doc and round prompt record what is and is not
  claimed.

This checkpoint does not move the active phase45 seam. The actuator
is a parallel new module; it is not invoked from any published
serving path or from the native backend's `unload`.

## What This Checkpoint Does NOT Claim

- the actuator releases memory (requires real injected `mx` module
  in a follow-up wiring round)
- the native backend's `unload` has been modified (it has not;
  `freed_gb` still reports the declared `session.info.memory_gb`)
- any matrix row has been promoted (none has; matrix is read-only
  this round)
- `pinned_models_never_evicted` is enforced end-to-end against any
  production path (no production path calls
  `coordinate_reclamation` this round)
- the pressure-event seam is hooked up to host pressure
  (`host_pressure.py` is read-only; no caller invokes
  `notify_pressure` from a host-pressure observer)
- `gc.collect()` plus `clear_cache()` is sufficient to release model
  memory in all cases (release semantics are governed by mlx core)
- training memory governance is in scope (training stays deferred
  per the program contract recorded in `memory_budget.py`)

## Promotion-Gate Coupling

Per the §1a Anti-Pollution Contract in
`docs/source-of-truth/native-mlx-backend-capability-matrix.md`,
declared-provenance real-candidate evidence is required to advance
any row from `partial` to `supported`. This scaffold round produces
fake-injected evidence only and therefore makes no row-level claim.

A future round that wires the native backend's `unload` to inject a
real `mx` module and run a real-admitted candidate through
`load → stream_generate → unload` may propose a new row (e.g.,
"Memory release actuator wiring") or argue for an existing row's
promotion on the strength of measured `ReclaimReceipt` byte deltas.
That round must run the §1a walkthrough; this scaffold does not.

## Next Authorized Round

The next authorized round on this main line is:

- **Memory Actuator — Native Unload Wiring**

That round modifies `owlmlx/runtime/mlx_native_backend.py:314-335`
to:

1. accept an injected `MemoryActuator` (constructor argument),
2. call `release_single_model(...)` after dropping session
   references in `unload`,
3. attach the resulting `ReclaimReceipt.to_dict()` to the
   `UnloadResult.detail`,
4. record real before/after byte deltas against an admitted
   candidate (legend-eligible artifact only),
5. run the §1a Anti-Pollution Contract walkthrough.

It does not claim continuous batching, prefix cache reuse,
speculative decoding, or any other native row beyond what its
real-injection evidence supports.

## Current Frozen Active Seam

This checkpoint does not move the phase45 active seam.
`summary.seam_rung`, `selected_seam.seam`,
`selected_seam.status`, `preserved_secondary_runtime_branch`, and
the top-level customer-runtime-evidence label remain at their values
from
`coordinator-checkpoint-native-mlx-backend-lifecycle-smoke-and-kv-cache-handle-owned-partial-promoted.md`.

## Round Output Summary

Five files added, no files modified outside the deliverable list, no
staging, no commit, and no new dependencies in the executor phase.
Coordinator review later ran the combined C-x/native scoped pytest
sweep and observed `83 passed, 3 skipped` (plus upstream warnings);
`tests/test_memory_actuator.py` contributed 19 passed tests.
