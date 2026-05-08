# owlmlx Coordinator Checkpoint — Native MLX Backend Lifecycle Smoke + KV Cache Handle Owned: partial_promoted

## Verdict

- `native_mlx_backend_lifecycle_smoke_and_kv_cache_handle_partial_promoted`

KV cache handle binding is now **owned by owlmlx against real installed
`mlx_lm`** (not a fake stub). Real-model lifecycle smoke is wired and
gate-ready, but deferred to opt-in env-var execution because no
sub-2B-parameter model is currently cached on the local machine and this
round explicitly does not download new models.

## What This Checkpoint Is

This is a partial-promotion marker for the redirected main line's second
round. One capability matrix row (KV cache handle) crosses the
evidence-kind threshold from "fake-stub adapter-side" to "real-installed
upstream binding." Two prior rows (scheduler admission, cooperative
cancellation) remain at `partial` (fake-stub) pending real-stream
verification. No row reaches `supported` in this round, by design — that
requires env-gated real-model smoke to actually run on a CI lane.

## What Is Now Frozen Exact

- `_NativeSession` carries three new observable cache fields:
  `last_prompt_cache`, `last_prompt_cache_id`, `prompt_cache_call_count`,
  cleared on `unload`
- `_resolve_make_prompt_cache(mlx_lm_module)` walks the passed-in module
  attribute path (`models.cache.make_prompt_cache`) rather than re-importing
  through `sys.modules`, so fake-injected stubs honestly report
  "no cache surface" even when real `mlx_lm.models.cache` is cached from
  prior tests
- `MlxNativeBackend._make_fresh_prompt_cache(mlx_lm, session)` is called
  on every `generate` and `stream_generate` entry; produces a fresh cache
  per request via `make_prompt_cache(model)`, threads it into upstream
  via the `prompt_cache=` kwarg, records it on the session for
  observability; consecutive calls produce **distinct** cache objects
  (single-request semantics locked by test, not just by convention)
- `MlxNativeBackend.capability_entry_points(model_id)` now reports the
  cache binding state per loaded model:
  `bound_per_request_single_request_only` when upstream reachable,
  `upstream_not_reachable` when not, with explicit
  `cross_request_reuse_claimed: False`
- `MlxNativeBackend.status().detail` now exposes
  `upstream_make_prompt_cache_reachable: bool`
- when upstream `mlx_lm.models.cache` is unreachable (fake-injected
  stubs, older mlx-lm versions), the adapter silently skips cache
  binding rather than failing — the lifecycle still runs

### New tests
- `tests/test_mlx_native_backend_real_upstream_binding.py` — four
  tests, **passes against real installed `mlx_lm 0.31.2`** in `.venv`:
  - canonical-symbol resolution check
  - `make_prompt_cache(MinimalModule)` real call
  - `_make_fresh_prompt_cache` distinct-object identity across consecutive
    calls
  - `status().detail.upstream_make_prompt_cache_reachable` truthful
- `tests/test_mlx_native_backend_real_smoke.py` — two env-gated tests
  (skipped by default unless `OWLMLX_NATIVE_SMOKE_MODEL_PATH` is set):
  - full lifecycle: `load → stream_generate → unload` with token /
    finish_reason / completion_tokens assertions and cache-binding
    confirmation
  - real-stream concurrency: two parallel real `stream_generate` calls,
    must observe `max_observed_concurrency == 1` (the post-claim
    invariant on the real upstream stream path)

### Test counts
- `tests/test_mlx_native_backend.py`: 13 passed + 1 skipped
  (missing-extra graceful path correctly skipped because `mlx_lm`
  installed)
- `tests/test_mlx_native_backend_post_claim_invariants.py`: 6 passed
- `tests/test_mlx_native_backend_real_upstream_binding.py`: 4 passed
- `tests/test_mlx_native_backend_real_smoke.py`: 2 skipped (env-gated)
- combined with active-seam + customer-runtime-evidence: 94 passed +
  3 skipped, no whitespace issues

### Capability matrix changes
- KV cache handle (`make_prompt_cache`): `experimental` → **`partial`**
  with real-installed-mlx_lm upstream binding evidence
- KV cache reuse across requests: `experimental` → **`not_in_scope`**
  (the binding deliberately enforces single-request fresh cache; reuse
  is unstated, not deferred)
- Section 3a expanded to distinguish "fake-mlx_lm adapter-side" evidence
  from "real-installed-mlx_lm upstream binding" evidence

### Post-claim invariants (preserved)
- `max_concurrent_1_after_gate_claim` — held on subprocess and native
- `ticketed_fifo_after_gate_claim` — held on subprocess and native
- `serial_safety_validated_only_after_gate_claim` — held on subprocess
  and native
- adapter-local `_TicketedAdmission` continues to serialize
  `generate` / `stream_generate` even with the new cache-binding code
  path; six fake-mlx_lm invariant tests still pass

## Current Frozen Active Seam

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- `preserved_secondary_runtime_branch = turboquant_preconditions`
- `preserved_secondary_runtime_branch.status = preconditions_exact`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

This checkpoint does not move the active phase45 seam. The native
adapter is parallel and is not invoked by any published serving path.

## What This Checkpoint Closes

The native-MLX-backend lifecycle-smoke / KV-cache-handle round is closed
in **partial-promoted** form:

- KV cache handle binding is verified against real installed `mlx_lm`
- the binding deliberately commits to single-request semantics; reuse
  across requests is structurally absent, not merely undocumented
- env-gated real-model smoke is wired and ready; running it requires
  setting `OWLMLX_NATIVE_SMOKE_MODEL_PATH` to a `mlx_lm.load`-resolvable
  model id and provisioning a CI lane that has the optional `runtime`
  extra installed
- promotion of any native row from `partial` to `supported` is deferred
  to a follow-up that runs the env-gated smoke on a CI lane

## What This Checkpoint Does Not Claim

- continuous batching exists
- prefix cache reuse across requests exists
- KV cache reuse across requests is verified
- cache parity exists
- stream interleaving exists
- speculative decoding is supported
- structured output / grammar enforcement is supported
- multi-stream true interleaving has been reopened
- the native adapter is wired into any serving path
- any native capability matrix row has been promoted to `supported`
- the env-gated real-model smoke has been run (it has not — it requires
  a model on disk and explicit operator opt-in)
- the subprocess sentinel chain has been resumed

## What Crossed The Threshold

The KV cache handle row is the first native row whose evidence is
"real-installed-upstream binding" rather than "fake-stub adapter-side."
This matters because the redirected main line's whole premise is that
the native path can reach process-internal capability entry points the
subprocess path cannot. With this round, that premise is no longer
inferred from upstream documentation — it is now **directly verified**
against the installed library, on the installed adapter, in this
codebase.

## Notable Implementation Choice

`_resolve_make_prompt_cache(mlx_lm_module)` resolves through the passed
module's attribute walk, not via `from mlx_lm.models.cache import …`.
This is a deliberate test-isolation choice: in mixed-test runs where a
prior test already imported the real `mlx_lm.models.cache` (caching it
in `sys.modules`), a fake-injected `mlx_lm` stub for a later test would
otherwise see the real cache module sneak through the top-level import.
The attribute walk binds resolution to the module reference the adapter
was given, which honestly returns `None` for fake stubs.

## Next Authorized Round

Two parallel candidates, both inside the redirected main line:

### Path B-1 (recommended): Native MLX Backend — Real-Model Smoke On A CI Lane

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-real-model-smoke-on-ci-lane.md`
  (to be authored)
- prerequisite: a CI lane with Python 3.11 + `uv sync --extra runtime` +
  one cached small mlx model (e.g. `mlx-community/Qwen2.5-0.5B-Instruct-4bit`
  or any 1-2B 4-bit quant)
- run `OWLMLX_NATIVE_SMOKE_MODEL_PATH=<model> .venv/bin/python -m pytest
  tests/test_mlx_native_backend_real_smoke.py`
- promote KV cache handle / decode_step iterator / per-step finish_reason
  / cooperative cancellation rows from `partial` to `supported` based on
  the smoke output
- explicitly does **not** claim batching / parity / reuse-across-requests
- explicitly does **not** modify `pyproject.toml`'s `requires-python`
- explicitly does **not** depend on the env-unification landing round
  having merged

### Path B-2 (parallel): Sampler Injection Binding

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-sampler-injection-binding.md`
  (to be authored)
- mirror the KV-cache-handle round shape: bind
  `mlx_lm.sample_utils.make_sampler` per request, record on
  `_NativeSession.last_sampler`, single-request semantics, real-upstream
  binding test, env-gated real-sampler smoke deferred
- this expands the native adapter's owned entry-point surface without
  promoting any existing row

I recommend executing **Path B-1 first** because it cashes in the
already-deferred real-model smoke that this round wired and gate-ready.
B-2 can wait one more round; the matrix value of B-2 is smaller until
real-model smoke has unlocked at least one `partial → supported`
promotion.
