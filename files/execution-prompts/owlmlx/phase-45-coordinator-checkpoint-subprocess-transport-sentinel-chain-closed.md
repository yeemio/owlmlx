# owlmlx Phase 45 Coordinator Checkpoint — Subprocess-Transport Sentinel Chain Closed

## Verdict

- `subprocess_transport_sentinel_chain_closed_in_current_paradigm`

This checkpoint does not introduce new runtime behavior. It records a
deliberate end of the phase45 subprocess-transport sentinel narrowing chain
inside the current packaging paradigm and redirects the cache_scheduler_depth
main line.

## What This Checkpoint Is

This is a closure marker, not an abandonment marker. The work the chain has
produced is preserved as live truth and is reclassified as the baseline that
any future native runtime must meet or exceed.

## What The Chain Has Already Cashed In

- a bounded pre-gate request-aggregation/cohort window before whole-request
  gate claim
- one non-stream child exchange that supports aggregated dispatch
- a non-stream main serving path that hands the bounded cohort into the
  aggregated child exchange
- stream gate release decoupled from outer consumer completion
- a multi-rung machine-readable proof that, on the current subprocess stdout
  transport, the second backend stream request can be written progressively
  earlier on the first stream's terminal-window, all the way up to the
  current frozen seam
- one distinct earlier runtime-owned terminal record
  (`runtime_owned_terminal_earlier_boundary`) ahead of the original boundary
  record, with the existing earlier-boundary trigger tightened from the
  shared `_e` prefix to the honest unique stem `_earlier_b`
- one distinct earlier-earlier runtime-owned terminal record
  (`runtime_owned_terminal_earlier_earlier_boundary`) ahead of the existing
  earlier-boundary record, with the new earlier-earlier trigger `_earlier_e`
  used as the current live detection trigger and verified by live harness
  before the existing earlier-boundary trigger
- the production runner (`owlmlx/runtime/mlx_lm_runner.py`) actually emits
  these sentinel records in the required order, locked by a runner-source
  ordering test
- post-claim serial invariants preserved at every rung:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`
- a customer/runtime evidence surface that routes each rung to a distinct
  recommended-next-step branch

## Current Frozen Active Seam

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- `preserved_secondary_runtime_branch = turboquant_preconditions`
- `preserved_secondary_runtime_branch.status = preconditions_exact`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

## What This Checkpoint Closes

The phase45 subprocess-transport sentinel chain — both same-shape branches —
is closed in the current paradigm:

- **A-type rungs (metadata first-unique-boundary freezes)**: not authorized
  for further rounds. The pattern has been executed twice
  (`stem_first_unique_boundary` Apr 23, `earlier_boundary_first_unique_boundary`
  this round). Any further A-type freeze is documentation symmetry only and
  does not contribute to runtime capability.
- **B-type rungs (real new sentinel records ahead of the current frozen
  seam)**: not authorized for further rounds inside the subprocess-stdout
  transport paradigm. The pattern has been executed twice
  (`earlier_boundary` introduction May 6, `earlier_earlier_boundary`
  introduction this round). Each new rung shrinks the second-stream-request
  write window by a microsecond-scale slice while permanently increasing the
  per-stream sentinel emission cost on the production runner. The marginal
  capability gain is below the engineering cost.

These closures hold unless and until an external audit or customer obligation
explicitly requires another rung at this granularity. In that case the chain
re-opens with that obligation as its scope, not on its own momentum.

## What This Checkpoint Does Not Claim

- stream interleaving exists
- continuous batching exists
- cache parity exists
- KV cache reuse exists
- customer-ready / replacement-ready status exists
- this checkpoint itself moves the active phase45 seam beyond the already
  frozen `earlier_earlier_boundary_dependency`

The cache_scheduler_depth dominant gap remains open and active. What changes
is only how it will be advanced.

## Redirected Main Line

The next main-line precondition for cache_scheduler_depth is no longer
"narrow further inside the subprocess-stdout transport sentinel chain". It is:

- **leave the subprocess-stdout transport paradigm**
- enter a native MLX backend path that exposes process-internal lifecycle and
  state hooks (load / generate / stream / unload, KV cache handle, prefill /
  decode step, scheduler admission, speculative drafter slot)
- treat all forbids on the current chain (no batching / no parity / no stream
  interleaving) as **constraints of the subprocess-wrap paradigm**, not
  intrinsic invariants of owlmlx; their lawful reopening depends on native
  backend feasibility being established first

## How The Sentinel Chain Is Reclassified

The chain output becomes a **baseline contract** that any native backend must
preserve or replace honestly:

- post-claim `max_concurrent = 1`, ticketed FIFO, and serial safety must
  remain achievable in any native path
- the bounded pre-gate cohort window and non-stream main-path handoff must
  remain achievable in any native path
- the second-stream-request progressive-earliness property already proved on
  subprocess transport must be matched or replaced (not silently regressed)
- the customer/runtime evidence surface must continue to route the active
  seam to a single honest recommended-next-step

Native backend rounds will produce their own active-seam vocabulary; the
subprocess sentinel chain stops growing but stays alive as live preserved
truth on the existing transport.

## Next Authorized Round

The next authorized round is no longer A-type or B-type. It is:

- **Native MLX Backend Feasibility / Scaffold**

See:
`files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-feasibility-scaffold.md`

This round does not replace the subprocess backend, does not move the active
phase45 seam, and does not claim batching / parity / interleaving. It only
establishes whether a parallel native backend adapter can hold the lifecycle
contract on a small / lightweight MLX path, and what capability entry points
that adapter would expose.
