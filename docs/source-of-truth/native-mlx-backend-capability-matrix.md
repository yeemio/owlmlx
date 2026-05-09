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
| In-process model handle                        | `partial`          | `not_in_scope`     | Native: `_NativeSession.model` stores the object returned by `mlx_lm.load`. Subprocess: only stdout JSON visible. **B-1 (2026-05-08) confirmed real `mlx_lm.load` returns `mlx_lm.models.qwen3_5_moe.Model` on the Qwen3.6-35B-A3B local candidate** (admissibility §3 row; provenance HF `Qwen/Qwen3.6-35B-A3B@53c43178`). **B-1.2 then routed the admitted candidate through `MlxNativeBackend.load → stream_generate → unload`**; row remains `partial` until B-1.3 walks the `supported` gate. |
| In-process tokenizer handle                    | `partial`          | `not_in_scope`     | Native: `_NativeSession.tokenizer` stores the object returned by `mlx_lm.load`. Subprocess: tokenization happens in child process. **B-1 (2026-05-08) confirmed real `mlx_lm.load` returns `mlx_lm.tokenizer_utils.TokenizerWrapper` on the same admitted candidate** (provenance as above). **B-1.2 exercised the adapter-routed lifecycle on the same candidate**; row remains `partial` until B-1.3 walks the `supported` gate. |
| Token-level `decode_step` iterator             | `partial`          | `not_in_scope`     | Native: adapter is wired to `mlx_lm.stream_generate` and fake tests prove token events are forwarded. Subprocess: per-token events arrive as JSON lines, no in-process Python hook. **B-1 (2026-05-08) confirmed real `mlx_lm.stream_generate` yields per-token chunks on the admitted candidate** — 8 chunks observed in 7.93 s, decode ~76 tok/s. **B-1.2 confirmed 8 token events through `MlxNativeBackend.stream_generate` on the same admitted candidate**; row remains `partial` until B-1.3 walks the `supported` gate. |
| Per-step finish-reason inspection              | `partial`          | `partial`          | Native: adapter reads `finish_reason` from each stream payload when present. Subprocess: only terminal `done` payload is visible to parent. **B-1 (2026-05-08) confirmed real `mlx_lm.stream_generate` chunks carry the `finish_reason` field** (`None` while in-progress; terminal value at the last chunk) on the admitted candidate. **B-1.2 confirmed the adapter terminal `done` event carried `finish_reason = "length"`**; row remains `partial` until B-1.3 walks the `supported` gate. |
| KV cache handle (`make_prompt_cache`)          | `partial`          | `not_in_scope`     | Native: adapter resolves `mlx_lm.models.cache.make_prompt_cache` through the live module attribute walk (`_resolve_make_prompt_cache`), creates a **fresh per-request** cache via `_make_fresh_prompt_cache`, threads it into `mlx_lm.stream_generate` / `mlx_lm.generate` via `prompt_cache=` kwarg, and records `last_prompt_cache` / `last_prompt_cache_id` / `prompt_cache_call_count` on `_NativeSession` for observability. Verified against real `mlx_lm 0.31.2` by `tests/test_mlx_native_backend_real_upstream_binding.py` — including identity check that consecutive calls produce **distinct** cache objects (single-request only, no cross-request reuse). **B-1.2 confirmed `prompt_cache_call_count >= 1` after a real-model adapter stream**; row remains `partial` until B-1.3 walks the `supported` gate. |
| KV cache reuse across requests                 | `not_in_scope`     | `not_in_scope`     | Single-request semantics deliberately enforced by the binding: `_make_fresh_prompt_cache` creates a new cache on every call and overwrites `last_prompt_cache`. No cross-request prefix-cache reuse claim. Opening this lawfully requires a follow-up round whose only job is to prove cohort-member correctness. |
| Sampler injection (`make_sampler`)             | `experimental`     | `not_in_scope`     | Native: upstream path is recorded as an entry-point assumption (`mlx_lm.sample_utils.make_sampler`) and requires real-smoke verification. Subprocess: only request-level params. |
| Logits hook (per-step logits inspection)       | `partial`          | `not_in_scope`     | Native: likely reachable via a custom sampler that captures logits before sampling, but no first-class `on_logits` callback is owned by owlmlx yet. |
| Speculative drafter slot                       | `experimental`     | `not_in_scope`     | Native: `mlx_lm` exposes a speculative-decoding path with a draft model parameter; the API is in flux across `0.22.x`. owlmlx makes no speculative claim yet; the entry point is reachable. |
| Scheduler admission hook                       | `partial`          | `partial`          | Neither upstream provides a multi-request scheduler. Both backends now have owlmlx-side ticketed FIFO + serial gate proved against the post-claim invariants. Native: `_TicketedAdmission` on `MlxNativeBackend` proved by `tests/test_mlx_native_backend_post_claim_invariants.py` (max_concurrent=1, FIFO order, queue marker correctness, ticket released on error and on generator close, mixed generate/stream serialized). **B-1.2 additionally confirmed two real upstream streams serialize with `max_observed_concurrency = 1`, `next_ticket = 2`, `serving = 2`, `in_critical_section = 0`**. Subprocess: owlmlx-side admission proved by phase45 sentinel chain. Both columns remain `partial` until B-1.3 decides whether the real-stream evidence satisfies the `supported` gate. |
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
was deferred in that scaffold round. B-1.2 later activated
`tests/test_mlx_native_backend_real_smoke.py` locally on the admitted
Qwen3.6-35B-A3B candidate; promotion to `supported` for any of these
rows now requires a separate B-1.3 §1a walkthrough, not another implicit
"green test means supported" jump.

Other rows remain `experimental` / `partial` / `not_in_scope` per the
Section 3 matrix.

## 3b. Promotion-Gate-Compliant Promotions (B-1.1 Round)

B-1.1 (2026-05-08) is the first round to advance row state under the §1a
Promotion Gate. Four rows advance from `experimental` to `partial` on
declared-provenance real-candidate evidence produced by B-1.

**Provenance (cited from B-1 checkpoint
`coordinator-checkpoint-native-mlx-backend-local-candidate-real-load-admissible.md`):**

- candidate: Qwen3.6-35B-A3B local mirror at
  `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B` — admissibility §3
  verdict `admissible` (B-1, 2026-05-08)
- upstream HF repo: `Qwen/Qwen3.6-35B-A3B`
- upstream commit SHA: `53c43178507d69762986fbfa314f6e8d4d859409`
- mlx_lm version of admission: 0.31.2
- evidence script: temporary `/tmp/owlmlx_local_candidate_load_attempt.py`
  (deleted post-round; full output transcribed in B-1 checkpoint)

### Promoted rows (4)

For each row, all four §1a gate conditions are walked explicitly:

**1. In-process model handle** (`experimental` → `partial`):

- gate 1 (admissibility): cited via Qwen3.6-35B-A3B §3 row, verdict
  `admissible`
- gate 2 (provenance): HF commit `53c43178` cited above
- gate 3 (Notes column updated): §3 row Notes column extended with
  B-1 evidence sentence and B-1.2 cap statement
- gate 4 (no quantization-subclass dependency): the candidate is bf16
  (no quantization block); evidence does not depend on any
  load-indistinguishable variant

**2. In-process tokenizer handle** (`experimental` → `partial`):

- gate 1: same admissibility row
- gate 2: same provenance
- gate 3: §3 row Notes column extended
- gate 4: bf16 candidate, no quantization-subclass dependency

**3. Token-level `decode_step` iterator** (`experimental` → `partial`):

- gate 1: same admissibility row
- gate 2: same provenance
- gate 3: §3 row Notes column extended with the 8-chunk / 7.93 s /
  ~76 tok/s decode observation
- gate 4: bf16 candidate, no quantization-subclass dependency

**4. Per-step finish-reason inspection** (`experimental` → `partial`):

- gate 1: same admissibility row
- gate 2: same provenance
- gate 3: §3 row Notes column extended with confirmation that chunks
  carry the `finish_reason` field
- gate 4: bf16 candidate, no quantization-subclass dependency

### Rows explicitly **not** promoted in B-1.1

The following rows had B-1 evidence reviewed and were declined for
promotion in this round, with stated reason:

| Row | Current | Reason for declining promotion |
|---|---|---|
| KV cache handle (`make_prompt_cache`) | `partial` | promotion to `supported` requires the **adapter's** `_make_fresh_prompt_cache` binding to fire under real load. B-1 smoke ran directly against `mlx_lm`, bypassing the adapter binding. B-1.2 later collected this evidence; promotion remains deferred to B-1.3 |
| Sampler injection (`make_sampler`) | `experimental` | B-1 used the default sampler; no `mlx_lm.sample_utils.make_sampler` injection was exercised. No new evidence |
| Speculative drafter slot | `experimental` | B-1 did not use a draft model. No new evidence |
| Scheduler admission hook | `partial` | B-1 was a single request; no admission queueing was exercised on a real model. B-1.2 later collected real-stream serialization evidence; promotion remains deferred to B-1.3 |
| In-process model residency / pinning | `experimental` | the session holding the model in memory during the smoke is incidental, not a separate capability claim. No standalone pinning evidence |
| Cooperative token-level cancellation | `partial` | B-1 ran to `max_tokens=8` without cancellation. No new evidence |
| Logits hook | `partial` | B-1 chunks carry a `logprobs` array, but this is `mlx_lm`'s default output — not an owlmlx logits-hook surface |
| Prefill / decode separation | `partial` | B-1 invoked `stream_generate` end-to-end, not separate prefill / decode. No new evidence |
| Structured output / multi-stream / KV reuse | `not_in_scope` | unchanged; B-1 produced no relevant evidence |

This decline list is part of the §1a Promotion Gate audit trail. A
future round that wants to promote any of these must produce its own
declared-provenance evidence and walk the gate independently.

## 3c. B-1.2 Real Adapter Lifecycle Evidence (2026-05-08)

B-1.2 is the first round to drive the **native adapter itself**
(`MlxNativeBackend`, not `mlx_lm` directly) through `load → stream_generate
→ unload` against the admitted Qwen3.6-35B-A3B candidate. This section
records the evidence; **no §3 row state changes in B-1.2**. Promotion of
specific rows from `partial` to `supported` is deferred to a separate
B-1.3 round that walks §1a Promotion Gate row-by-row.

### Evidence-collection driver

- existing env-gated test module:
  `tests/test_mlx_native_backend_real_smoke.py` (no edits in this round)
- env activation:
  `OWLMLX_NATIVE_SMOKE_MODEL_PATH=/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`
  `OWLMLX_NATIVE_SMOKE_MAX_TOKENS=8`
- result: **2 passed, 2 warnings, 44.00 s** wall

### Provenance (per §1a gate 2)

Same as B-1.1, cited again here for B-1.3's convenience:

- candidate: Qwen3.6-35B-A3B local mirror (admissibility §3 row,
  verdict `admissible`)
- upstream HF repo: `Qwen/Qwen3.6-35B-A3B`
- upstream commit SHA: `53c43178507d69762986fbfa314f6e8d4d859409`
- mlx_lm version: 0.31.2

### Test 1 — `test_real_model_lifecycle_load_stream_unload`

Drives `MlxNativeBackend.load → stream_generate → unload` end-to-end.

Observed:

- `backend.load(model_id)` → `LoadedModelInfo.backend = "mlx-native"`,
  `model_id` matches; load wall-time **12.34 s**
- `backend.stream_generate(...)` yielded 9 events (8 × `token`, 1 ×
  `done`); stream wall-time **6.92 s**
- `done` event carried `finish_reason = "length"` (max_tokens=8 cap),
  `completion_tokens = 8`
- `backend.capability_entry_points(model_id)` returned:
  - `kv_cache_factory.status = "bound_per_request_single_request_only"`
  - `kv_cache_factory.prompt_cache_call_count >= 1`
  - `kv_cache_factory.cross_request_reuse_claimed = False`
- `backend.unload(model_id)` succeeded; the model id no longer present
  in `backend.status().loaded_models`

This is the first B-1.x evidence with the **adapter's own
`_make_fresh_prompt_cache` actually firing on a real model**. Prior
rounds had it bound against real `mlx_lm` (B-2 of the original native
sequence) but never invoked under a real lifecycle.

### Test 2 — `test_real_model_two_streams_serialize_under_admission`

Two real `stream_generate` threads on the same loaded model, asserting
the post-claim invariants on the real upstream stream path.

Observed:

- both threads reached terminal `done` event
- `backend.status().detail['admission']` snapshot:
  - `max_observed_concurrency = 1`
  - `next_ticket = 2`
  - `serving = 2`
  - `in_critical_section = 0`

This is the first B-1.x evidence with **ticketed FIFO admission
serializing real upstream streams** rather than fake-injected stubs.

### B-1.3 promotion candidates (informative, decided in B-1.3 not here)

The §1a Promotion Gate walkthrough that B-1.3 is expected to perform
will consider the following rows for `partial → supported` based on
evidence above:

| Row | Lifts the prior cap on |
|---|---|
| In-process model handle | "B-1 ran outside the adapter" — Test 1 ran through the adapter and asserted `LoadedModelInfo.backend = "mlx-native"` |
| In-process tokenizer handle | same |
| Token-level `decode_step` iterator | "fake tests prove forwarding" — Test 1 saw 8 token events through the adapter on real upstream |
| Per-step finish-reason inspection | same |
| KV cache handle (`make_prompt_cache`) | "binding never invoked under real load" — Test 1 confirmed `prompt_cache_call_count ≥ 1` after a real-model `stream_generate` |
| Scheduler admission hook | "real upstream stream path not proved" — Test 2 confirmed serial admission on real streams |

Rows that do **not** acquire B-1.2 evidence and so **cannot** be
promoted in B-1.3:

| Row | Reason no B-1.2 evidence |
|---|---|
| Cooperative token-level cancellation | both tests ran to terminal events; no mid-stream cancellation was exercised. A separate round (B-4) is needed |
| Sampler injection | default sampler used; `make_sampler` not injected |
| Speculative drafter slot | no draft model configured |
| Logits hook | `logprobs` arrays come from `mlx_lm` defaults, not an owlmlx logits-hook surface |
| Prefill / decode separation | end-to-end `stream_generate`, not split |
| In-process model residency / pinning | model loading is incidental to the lifecycle test, not pinned independently |
| Structured output / multi-stream / KV reuse | unchanged `not_in_scope` |

### What B-1.2 explicitly does not change

- no §3 row state changed in B-1.2
- §3 Notes column edits may cross-reference B-1.2 evidence, but they do
  not change any row state
- no test file added or modified
- no runtime code modified
- promotion to `supported` for any row is **not** authorized by this
  section alone — B-1.3 must walk §1a row-by-row to authorize it

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
  now proved with fake `mlx_lm` and with two B-1.2 real upstream streams
  on one admitted candidate, but no true batching, interleaving, or
  broader workload class is claimed.
- It does not claim any upstream capability listed above is yet **owned** by
  owlmlx; owlmlx owns the adapter-side ticketed admission contract, while
  upstream model loading, tokenization, cache creation, and generation remain
  borrowed entry points. B-1.2 extends the proof to a real adapter lifecycle,
  but `supported` labels still require an explicit §1a promotion round.

## 6. Feasibility Verdict

`feasible` — the native MLX backend adapter holds the scaffold lifecycle
contract (`load` / `generate` / `stream_generate` / `unload` / `status`) in
fake-module and missing-extra tests, exposes a strictly better process-
internal handle shape than the subprocess adapter, and gracefully fails when
the optional `runtime` extra is missing.

B-1 admitted the local Qwen3.6-35B-A3B candidate through real `mlx_lm.load`.
B-1.2 then drove that admitted candidate through
`MlxNativeBackend.load → stream_generate → unload` and through a two-stream
serial-admission smoke. This keeps the matrix at `feasible`; it does not
wire the native adapter into any published serving path or claim production
readiness.

## 7. Recommended Next Round

`B-1.3 — Capability Matrix Promotion from B-1.2 Evidence`:

- walk §1a Promotion Gate row-by-row for the B-1.2 candidates: in-process
  model handle, in-process tokenizer handle, token-level stream iterator,
  per-step finish-reason inspection, KV cache handle, and scheduler admission
  hook
- decide whether each row moves from `partial` to `supported`, and record
  explicit decline reasons for any row that does not promote
- do not promote cancellation, sampler injection, speculative drafter, logits
  hook, prefill/decode separation, model pinning, structured output,
  multi-stream interleaving, or KV reuse; B-1.2 produced no evidence for
  those rows
- keep the round doc-only: no runtime code, no tests, no environment changes,
  no model download, and no conversion
