# owlmlx Coordinator Checkpoint — Native MLX Backend Feasibility / Scaffold: feasible (scaffold-grade)

## Verdict

- `native_mlx_backend_feasibility_scaffold_feasible_scaffold_grade`

This checkpoint records the close of the first round on the redirected main
line. The native MLX backend adapter holds the lifecycle interface contract
and defines process-internal handle slots / introspection shapes that the
subprocess adapter cannot expose, but every native row in the capability matrix remains
**scaffold-grade** until a follow-up round drives a real `mlx_lm` model
through the lifecycle.

## What This Checkpoint Is

This is a feasibility marker, not a capability-claim marker. It says: the
shape of the native path holds, and the intended entry points are recorded
as scaffold-grade assumptions for the next smoke round. It does **not** say
the cache / sampler / speculative entry points have been bound against a
real installed upstream surface. No row has been promoted from
`experimental` to `supported` yet, because no row has been verified under
an installed `runtime` extra.

## What Is Now Frozen Exact

- a parallel adapter at `owlmlx/runtime/mlx_native_backend.py` (`MlxNativeBackend`)
  that mirrors the public surface of `MlxLmSubprocessBackend`:
  `load`, `unload`, `generate`, `generate_messages`, `generate_cohort`,
  `stream_generate`, `stream_generate_messages`, `status`,
  plus a read-only `capability_entry_points(model_id)` introspection method
- `mlx_lm` is imported only via `_import_mlx_lm()` deferred at first call
  site; missing optional extra returns
  `RuntimeErrorCode.backend_error` with `detail.reason="mlx_lm_not_installed"`
- in-process `_NativeSession` (model + tokenizer + lock + last_error)
  carries the per-model state for any future capability round to attach to
- `generate_cohort` is honest serial — the native path makes no batching
  claim
- the scoped test file `tests/test_mlx_native_backend.py` runs to **14
  passed** without `mlx_lm` installed:
  - interface shape / status / load missing-extra graceful path / empty
    model_id rejection / unload of unknown model / generate of unloaded
    model / stream_generate of unloaded model yields error
  - **fake-mlx_lm-injected lifecycle**: `load → status →
    capability_entry_points → unload` runs end to end
  - **fake-mlx_lm-injected stream_generate**: yields `token, token, done`
    with `finish_reason` and `completion_tokens` populated
  - source-side guards: adapter source must not contain `import subprocess`,
    `subprocess.Popen`, `_STREAM_TERMINAL_NOTICE`, `runtime_owned_terminal_`,
    or any sentinel-parser symbol
- the capability matrix at
  `docs/source-of-truth/native-mlx-backend-capability-matrix.md` lists 15
  capability entry points × Native / Subprocess columns, with status legend
  `supported / partial / experimental / not_in_scope`, and explicitly
  records that every native row is scaffold-grade until lifecycle smoke runs
- master outline and replacement-grade-stability-gaps now reference the
  matrix and record the main-line switch from sentinel chain to native
  feasibility
- post-claim serial invariants remain preserved on the subprocess path:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`
- the native path has not yet been driven through any post-claim invariant
  harness; that is deliberately scope for the follow-up round

## Current Frozen Active Seam

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- `preserved_secondary_runtime_branch = turboquant_preconditions`
- `preserved_secondary_runtime_branch.status = preconditions_exact`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

This checkpoint does not move the active phase45 seam. The native adapter
is parallel and is not invoked by any published serving path.

## What This Checkpoint Closes

The native-MLX-backend feasibility / scaffold round is closed in
scaffold-grade form:

- the adapter exists, holds the interface, and degrades gracefully without
  the optional `runtime` extra
- the capability matrix is the **source of truth** for which entry points
  the native path is even *expected* to expose; subsequent rounds promote
  rows from `experimental` to `supported` only via real-smoke evidence
- no Native-MLX entry-point claim is yet **owned** by owlmlx; the matrix
  is read-only documentation of reachability assumptions

## What This Checkpoint Does Not Claim

- continuous batching exists
- prefix cache reuse exists
- KV cache reuse across requests is verified
- cache parity exists
- stream interleaving exists
- speculative decoding is supported
- structured output / grammar enforcement is supported
- multi-stream true interleaving has been reopened
- the native adapter is wired into any serving path
- any native capability matrix row has been promoted beyond
  `experimental` / `partial`
- the subprocess sentinel chain has been resumed

## Next Authorized Round

The next authorized round on the redirected main line is:

- **Native MLX Backend — Lifecycle Smoke + KV Cache Handle Owned**

See:
`files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-lifecycle-smoke-and-kv-cache-handle-owned.md`

That round installs the optional `runtime` extra in a CI lane, drives one
small `mlx_lm` model through `load → stream_generate → unload`, promotes
the KV cache handle from an entry-point assumption to a first-class
attribute on `_NativeSession` with a within-request reuse correctness
harness, and runs the existing post-claim serial-safety invariant harnesses
against the native path. It explicitly does **not** claim batching, prefix
cache reuse across requests, or speculative decoding. Its job is to upgrade
the relevant capability-matrix rows from `experimental` to `supported` on
real evidence, not to ship new capabilities.
