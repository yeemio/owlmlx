# owlmlx Native MLX Backend — Capability Matrix

> Status: authoritative
> Updated: 2026-05-07
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
| KV cache handle (`make_prompt_cache`)          | `experimental`     | `not_in_scope`     | Native: upstream path is recorded as an entry-point assumption (`mlx_lm.models.cache.make_prompt_cache`), but the adapter does **not** yet import or thread a cache handle through the public surface. No cache-reuse claim. |
| KV cache reuse across requests                 | `experimental`     | `not_in_scope`     | The handle exists; the *invariant* (correctness when reused across cohort members) has not yet been verified by a harness. Reopening this lawfully requires a follow-up round; see redirected main line in chain-closed checkpoint. |
| Sampler injection (`make_sampler`)             | `experimental`     | `not_in_scope`     | Native: upstream path is recorded as an entry-point assumption (`mlx_lm.sample_utils.make_sampler`) and requires real-smoke verification. Subprocess: only request-level params. |
| Logits hook (per-step logits inspection)       | `partial`          | `not_in_scope`     | Native: likely reachable via a custom sampler that captures logits before sampling, but no first-class `on_logits` callback is owned by owlmlx yet. |
| Speculative drafter slot                       | `experimental`     | `not_in_scope`     | Native: `mlx_lm` exposes a speculative-decoding path with a draft model parameter; the API is in flux across `0.22.x`. owlmlx makes no speculative claim yet; the entry point is reachable. |
| Scheduler admission hook                       | `not_in_scope`     | `partial`          | Neither upstream provides a multi-request scheduler. Subprocess backend has owlmlx-side ticketed FIFO + serial gate (the post-claim invariants); native has *no* scheduler yet — a future round must build it on top. The "subprocess `partial`" column reflects the owlmlx-built admission, not anything from upstream. |
| In-process model residency / pinning           | `experimental`     | `partial`          | Native: model lives in adapter's process once loaded; pinning can be represented by retaining the session entry. Subprocess: model lives in child process; pinning works but residency is one-process-removed. |
| Cooperative token-level cancellation           | `partial`          | `partial`          | Native: dropping the `stream_generate` iterator should stop at generator close / next yield, but this has not been proved against real `mlx_lm`. Subprocess: cancellation arrives at the next `stream_done` boundary measured by phase45 sentinel chain. |
| Structured output / grammar enforcement        | `not_in_scope`     | `not_in_scope`     | Upstream `mlx_lm` does not ship a first-class grammar enforcer in 0.22; integrations with Outlines / lm-format-enforcer are community-side. Reaching this in either backend requires explicit external dependency choice. |
| Prefill / decode separation                    | `partial`          | `not_in_scope`     | Native: prefill happens implicitly inside `stream_generate`'s first yield; no separate `prefill()` call in the public surface. A future round can split it by walking the model's KV cache manually. Subprocess: not visible. |
| Multi-stream true interleaving                 | `not_in_scope`     | `not_in_scope`     | Both backends preserve post-claim `max_concurrent = 1` + ticketed FIFO + serial safety. Lawful reopening of this invariant is the explicit subject of the redirected main line, not this matrix. |

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
3. **KV cache handle entry-point assumption** — needed for prefix cache reuse
   and continuous batching, but not yet owned by owlmlx
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
- It does not claim parity with the subprocess adapter on the post-claim
  serial invariants on a live multi-request workload — the native adapter
  has not been driven through the existing harnesses, and that is
  deliberately scope for a later round.
- It does not claim any capability listed above is yet **owned** by owlmlx;
  it only records the scaffold-grade entry-point shape.

## 6. Feasibility Verdict

`feasible` — the native MLX backend adapter holds the scaffold lifecycle
contract (`load` / `generate` / `stream_generate` / `unload` / `status`) in
fake-module and missing-extra tests, exposes a strictly better process-
internal handle shape than the subprocess adapter, and gracefully fails when
the optional `runtime` extra is missing.

Lifecycle smoke testing under a real `mlx_lm` install is deferred to a
follow-up round whose only job is to wire one minimal `mlx_lm`-backed
session through the adapter and re-run the existing post-claim invariant
harnesses against the native path.

## 7. Recommended Next Round

`Native MLX Backend Lifecycle Smoke + KV Cache Handle Owned`:

- install the optional `runtime` extra in a CI lane
- drive one small model through `MlxNativeBackend.load → stream_generate →
  unload`
- expose the KV cache handle as a first-class attribute on `_NativeSession`
  without yet claiming reuse
- re-run the existing post-claim serial-safety invariant harnesses against
  the native path
- explicitly forbid claiming continuous batching, prefix cache reuse, or
  speculative decoding in that round
