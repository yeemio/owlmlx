# owlmlx Native MLX Backend — Capability Matrix

> Status: authoritative
> Updated: 2026-05-08
> Scope: capability entry points exposed by the experimental
> `MlxNativeBackend` adapter at `owlmlx/runtime/mlx_native_backend.py`,
> compared against the existing `MlxLmSubprocessBackend` baseline.

## 1. Purpose

This matrix records **which process-internal capability entry points are
reachable** from each owlmlx backend adapter. It does **not** claim that
owlmlx itself supports any of these capabilities yet. The native adapter is
experimental and parallel; no capability listed below is wired into a
published serving path.

The matrix exists so that subsequent rounds (continuous batching, prefix
cache, speculative decoding, scheduler admission) can decide where to build
based on actual entry-point availability rather than assumed parity.

Status legend:

- `supported` — the upstream library exposes the entry point via stable
  public API; the native adapter can reach it without patching upstream
- `partial` — the entry point is reachable but with caveats (unstable API,
  version drift, behavioral gaps)
- `experimental` — the entry point exists in the upstream surface but is
  itself flagged experimental, in flux, or undocumented
- `not_in_scope` — the entry point is not exposed by the upstream surface
  in the form owlmlx would need; reaching it requires forking or replacing
  upstream

Because this round deliberately avoids a real model lifecycle smoke, every
native row below is still scaffold-grade. A `supported` label would require
the follow-up smoke round to prove the entry point under an installed
`runtime` extra.

## 1a. Promotion Gate (Anti-Pollution Contract)

Native rows are promoted from `partial` to `supported` **only on declared-
provenance real-candidate evidence**. A promotion is rejected, regardless of
how many tests are green, when any of the following hold:

- the smoke artifact is a sub-2B-parameter "toy" model selected ad-hoc to
  produce a green check, with no entry in
  `native-mlx-backend-local-candidate-admissibility.md`
- the smoke artifact's provenance form is not on the acceptable list in
  `native-mlx-backend-local-candidate-admissibility.md` §4.1
- the promoting round's checkpoint does not record the artifact's provenance
  (HF revision SHA for HF-sourced artifacts; convert command + mlx_lm
  version for self-converted artifacts)
- the promoted row's evidence relies on a quantization-variant distinction
  that does not exist at runtime — for example, claiming a separate
  promotion for "4bit-DWQ" vs "4bit affine" when
  `native-mlx-backend-input-contract.md` §6 records that they are
  indistinguishable at `mlx_lm.load` time

A promotion that meets the gate must:

1. cite the candidate row in
   `native-mlx-backend-local-candidate-admissibility.md` whose verdict has
   been advanced to `admissible`
2. record provenance in the round's coordinator-checkpoint document
3. update the relevant row's `Notes` column with the load and lifecycle
   evidence (test file + revision)

Toy-grade smoke runs may still be performed for quick adapter
sanity-checks, but their output is **not** valid promotion evidence and
must not appear in §3a of this matrix.

## 2. Environment Notes

- `mlx_lm` and `mlx` are listed as the optional `runtime` extra in
  `pyproject.toml`; they are not installed in every dev / CI environment
- the native adapter defers all `mlx_lm` imports to first call site and
  returns `RuntimeErrorCode.backend_error` with `reason=mlx_lm_not_installed`
  when the extra is absent
- this matrix reflects the upstream `mlx-lm >= 0.22` API surface that the
  optional dependency pins; specific entry-point names below are treated as
  scaffold-grade entry-point assumptions until lifecycle smoke testing runs
  under an installed runtime extra
- the `experimental_native_mlx` adapter is **not** invoked by
  `MlxLmSubprocessBackend`, by the production runner, or by any published
  serving path

## 3. Capability Entry-Point Matrix

| Capability entry point                         | Native MLX backend | Subprocess backend | Notes |
|------------------------------------------------|--------------------|--------------------|-------|
| In-process model handle                        | `experimental`     | `not_in_scope`     | Native: `_NativeSession.model` stores the object returned by `mlx_lm.load`. Subprocess: only stdout JSON visible. Real `mlx_lm` smoke is still pending. |
| In-process tokenizer handle                    | `experimental`     | `not_in_scope`     | Native: `_NativeSession.tokenizer` stores the object returned by `mlx_lm.load`. Subprocess: tokenization happens in child process. Real `mlx_lm` smoke is still pending. |
| Token-level `decode_step` iterator             | `experimental`     | `not_in_scope`     | Native: adapter is wired to `mlx_lm.stream_generate` and fake tests prove token events are forwarded. Subprocess: per-token events arrive as JSON lines, no in-process Python hook. |
| Per-step finish-reason inspection              | `experimental`     | `partial`          | Native: adapter reads `finish_reason` from each stream payload when present. Subprocess: only terminal `done` payload is visible to parent. |
| KV cache handle (`make_prompt_cache`)          | `partial`          | `not_in_scope`     | Native: adapter resolves `mlx_lm.models.cache.make_prompt_cache` through the live module attribute walk (`_resolve_make_prompt_cache`), creates a **fresh per-request** cache via `_make_fresh_prompt_cache`, threads it into `mlx_lm.stream_generate` / `mlx_lm.generate` via `prompt_cache=` kwarg, and records `last_prompt_cache` / `last_prompt_cache_id` / `prompt_cache_call_count` on `_NativeSession` for observability. Verified against real `mlx_lm 0.31.2` by `tests/test_mlx_native_backend_real_upstream_binding.py` — including identity check that consecutive calls produce **distinct** cache objects (single-request only, no cross-request reuse). Real-model lifecycle smoke (env-gated) deferred. |
| KV cache reuse across requests                 | `not_in_scope`     | `not_in_scope`     | Single-request semantics deliberately enforced by the binding: `_make_fresh_prompt_cache` creates a new cache on every call and overwrites `last_prompt_cache`. No cross-request prefix-cache reuse claim. Opening this lawfully requires a follow-up round whose only job is to prove cohort-member correctness. |
| Sampler injection (`make_sampler`)             | `experimental`     | `not_in_scope`     | Native: upstream path is recorded as an entry-point assumption (`mlx_lm.sample_utils.make_sampler`) and requires real-smoke verification. Subprocess: only request-level params. |
| Logits hook (per-step logits inspection)       | `partial`          | `not_in_scope`     | Native: likely reachable via a custom sampler that captures logits before sampling, but no first-class `on_logits` callback is owned by owlmlx yet. |
| Speculative drafter slot                       | `experimental`     | `not_in_scope`     | Native: `mlx_lm` exposes a speculative-decoding path with a draft model parameter; the API is in flux across `0.22.x`. owlmlx makes no speculative claim yet; the entry point is reachable. |
| Scheduler admission hook                       | `partial`          | `partial`          | Neither upstream provides a multi-request scheduler. Both backends now have owlmlx-side ticketed FIFO + serial gate proved against the post-claim invariants. Native: `_TicketedAdmission` on `MlxNativeBackend` proved by `tests/test_mlx_native_backend_post_claim_invariants.py` (max_concurrent=1, FIFO order, queue marker correctness, ticket released on error and on generator close, mixed generate/stream serialized). Subprocess: owlmlx-side admission proved by phase45 sentinel chain. Both columns are `partial` because no upstream multi-request scheduler exists; owlmlx owns admission on both paths. |
| In-process model residency / pinning           | `experimental`     | `partial`          | Native: model lives in adapter's process once loaded; pinning can be represented by retaining the session entry. Subprocess: model lives in child process; pinning works but residency is one-process-removed. |
| Cooperative token-level cancellation           | `partial`          | `partial`          | Native: dropping the `stream_generate` iterator releases the admission ticket via the generator's `finally` clause, proved by `test_native_backend_admission_releases_on_generator_close`; behavior under real `mlx_lm` token-stream cancellation has not been proved yet. Subprocess: cancellation arrives at the next `stream_done` boundary measured by phase45 sentinel chain. |
| Structured output / grammar enforcement        | `not_in_scope`     | `not_in_scope`     | Upstream `mlx_lm` does not ship a first-class grammar enforcer in 0.22; integrations with Outlines / lm-format-enforcer are community-side. Reaching this in either backend requires explicit external dependency choice. |
| Prefill / decode separation                    | `partial`          | `not_in_scope`     | Native: prefill happens implicitly inside `stream_generate`'s first yield; no separate `prefill()` call in the public surface. A future round can split it by walking the model's KV cache manually. Subprocess: not visible. |
| Multi-stream true interleaving                 | `not_in_scope`     | `not_in_scope`     | Both backends preserve post-claim `max_concurrent = 1` + ticketed FIFO + serial safety. Lawful reopening of this invariant is the explicit subject of the redirected main line, not this matrix. |

## 3a. Verified Rows in This Round

Rows whose **native adapter-side** behavior is now backed by focused test
evidence inside this scaffold round. These tests use fake `mlx_lm` because
the behavior under test is owlmlx's admission/cancellation contract, not the
upstream model runtime:

| Capability entry point                         | Native column | Evidence |
|------------------------------------------------|---------------|----------|
| Scheduler admission hook                       | `partial`     | `tests/test_mlx_native_backend_post_claim_invariants.py` — six tests: serial safety (`test_native_backend_admission_serializes_concurrent_streams`), ticketed FIFO order (`test_native_backend_admission_preserves_ticketed_fifo_order`), uncontested queue-marker correctness (`test_native_backend_uncontested_requests_are_not_marked_queued`), error-path release (`test_native_backend_admission_releases_on_error_path`), generator-close release (`test_native_backend_admission_releases_on_generator_close`), mixed generate/stream serialization (`test_native_backend_generate_is_also_admission_serialized`). Adapter implements `_TicketedAdmission` with monotonic ticket counter + condition variable; plain `threading.Lock` would not pass these tests. |
| Cooperative token-level cancellation           | `partial`     | `test_native_backend_admission_releases_on_generator_close` — proves generator `finally` releases the admission ticket on early caller close, so subsequent waiters are not deadlocked. |
| KV cache handle (`make_prompt_cache`)          | `partial`     | **real-installed-mlx_lm upstream binding** — `tests/test_mlx_native_backend_real_upstream_binding.py` four tests: `_resolve_make_prompt_cache` returns the canonical upstream symbol; `make_prompt_cache` accepts a minimal `mlx.nn.Module` and produces an iterable cache; `MlxNativeBackend._make_fresh_prompt_cache` populates `_NativeSession.last_prompt_cache` and consecutive calls produce **distinct** cache objects (single-request semantics locked); `status().detail.upstream_make_prompt_cache_reachable` is truthful. Verified against `mlx_lm 0.31.2` as installed in `.venv`. |

The first two rows (admission, cancellation) are not `supported` because
they were proved with fake-injected `mlx_lm`; the upstream stream-runtime
binding has not been smoke-tested. The KV cache handle row crosses an
evidence-kind threshold: it is the first native row whose binding is
verified against the **real installed upstream library**, not a fake
stub. It is still `partial` rather than `supported` because real-model
lifecycle smoke (`load → stream_generate → unload` on an actual model)
is deferred to env-gated `tests/test_mlx_native_backend_real_smoke.py`
which is opt-in and not run by default. Promotion to `supported` for any
of these rows requires the env-gated real-model smoke to have been run
on a CI lane.

Other rows remain `experimental` / `partial` / `not_in_scope` per the
Section 3 matrix.

## 4. Native-Only Delta (Reasons The Main Line Switched)

The capability deltas where the native adapter exposes a process-internal
entry point shape that the subprocess adapter cannot expose are the hard
evidence for the main-line switch recorded in the chain-closed checkpoint:

1. **In-process model and tokenizer handles** — the prerequisite for every
   subsequent row
2. **Token-level stream iterator with per-step finish_reason access when
   upstream emits it** — needed
   for any future scheduler that reasons about token boundaries within a
   request rather than across requests
3. **KV cache handle partial upstream binding** — the real installed
   `mlx_lm.models.cache.make_prompt_cache` path is now bound and recorded
   on `_NativeSession` with fresh single-request semantics; prefix cache
   reuse across requests remains explicitly not in scope
4. **Sampler injection entry-point assumption** — needed for any
   structured-output or grammar integration that owlmlx might land
5. **Speculative drafter slot** — entry point for MTP / draft-model rounds
6. **A plausible cooperative cancellation boundary at generator close / next
   yield** — this is a candidate improvement over the subprocess transport
   boundary that the phase45 sentinel chain measured, but it must still be
   proved against real `mlx_lm`

## 5. What This Matrix Does Not Claim

- It does not claim owlmlx has continuous batching, prefix cache reuse,
  speculative decoding, structured output, or multi-stream interleaving.
- It does not claim the native adapter is production-ready or wired into
  any serving path.
- It does not claim parity with the subprocess adapter on a live
  `mlx_lm`-backed multi-request workload — native adapter-side admission is
  now proved with fake `mlx_lm`, while real upstream binding remains scope
  for a later round.
- It does not claim any upstream capability listed above is yet **owned** by
  owlmlx; only the adapter-side ticketed admission contract is owned, and it
  remains `partial` until real `mlx_lm` smoke extends the proof.

## 6. Feasibility Verdict

`feasible` — the native MLX backend adapter holds the scaffold lifecycle
contract (`load` / `generate` / `stream_generate` / `unload` / `status`) in
fake-module and missing-extra tests, exposes a strictly better process-
internal handle shape than the subprocess adapter, and gracefully fails when
the optional `runtime` extra is missing.

Lifecycle smoke testing under a real `mlx_lm` install is deferred to a
follow-up round whose only job is to wire one minimal `mlx_lm`-backed
session through the adapter and extend the native post-claim invariant proof
to a real upstream-bound session.

## 7. Recommended Next Round

`Native MLX Backend Lifecycle Smoke + KV Cache Handle Owned`:

- install the optional `runtime` extra in a CI lane
- drive one small model through `MlxNativeBackend.load → stream_generate →
  unload`
- expose the KV cache handle as a first-class attribute on `_NativeSession`
  without yet claiming reuse
- extend the native post-claim serial-safety invariant tests to a real
  `mlx_lm`-backed session where practical
- explicitly forbid claiming continuous batching, prefix cache reuse, or
  speculative decoding in that round
