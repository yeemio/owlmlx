# owlmlx Goal Contract: Mainstream Prefix-Cache Compatibility Closure

> Status: active goal contract
> Updated: 2026-06-01 after operator-paused B-1c section 2 topoff

## goal_id

`owlmlx-mainstream-prefix-cache-compatibility-closure`

## title

Close the OwlMLX-owned gap between experimental session KV reuse and mainstream
OpenAI / Anthropic prefix-cache compatibility without shifting private-header
adaptation burden to OwlCoda, Codex, or other consumers.

## success_definition

This goal succeeds only when OwlMLX has an evidence-backed, runtime-owned
prefix-cache compatibility lane with all of the following properties:

1. Mainstream OpenAI / Anthropic compatibility callers do not need to send
   `X-Owlmlx-Session-Id` as a stable product contract in order to receive the
   target prefix-cache behavior.
2. Any automatic reuse path is gated by proven token-prefix equivalence for the
   same model, tokenizer, runtime profile, template boundary, and isolation
   policy.
3. Cache-hit observability is surfaced through a compatibility-visible field
   only when it is backed by real runtime accounting, or is explicitly marked as
   absent and diagnostic-only.
4. The existing explicit `X-Owlmlx-Session-Id` path remains available as an
   experimental dogfood/control lane and is not renamed into a supported
   mainstream consumer contract.
5. No `supported` promotion is made until the B-1c section-2 aggregate gate and
   the new B-2 compatibility gate both pass.
6. The source-of-truth documents, design spec, tests, and evidence agree on the
   same capability label and the same consumer boundary.

## blocked_definition

This goal is blocked only if the next executable slice cannot be completed
because of one of these exact blockers:

- the runtime cannot prove safe token-prefix equivalence without upstream
  cache-clone or cache-trim semantics that are not available on the admitted
  model path;
- B-1c section-2 aggregate stability remains insufficient to permit any real
  cache-handle reuse beyond classifier/diagnostic work;
- OpenAI / Anthropic compatibility fields cannot be populated without
  fabricating cached-token counts not produced by the runtime;
- no local model/backend path is available to verify the next compatibility
  slice.

If blocked, preserve the last verified explicit-session baseline and record the
missing primitive precisely. Do not reframe the private header as the solution.

## hard_rules

1. Do not require OwlCoda, Codex, OpenAI-style clients, or Anthropic-style
   clients to learn `X-Owlmlx-Session-Id` as the mainstream contract.
2. Do not claim automatic prefix cache, cross-request reuse, `cached_tokens`, or
   Anthropic cache-read counters until implemented and evidenced.
3. Do not silently merge unrelated conversations, users, runtime profiles, model
   versions, tokenizers, or chat-template boundaries.
4. Do not make session KV default-on while the capability remains
   `experimental`.
5. Do not promote B-1 session KV to `supported` until B-1a, B-1b, B-1c section
   1, and B-1c section 2 all pass under their existing gates.
6. Keep B-2 separate from B-1c: B-1c proves cache stability; B-2 proves
   mainstream compatibility semantics.
7. Do not create new spec-as-code modules or banned module patterns under
   `owlmlx/`.
8. Leave unrelated dirty files untouched.

## out_of_scope

- paged KV cache
- continuous batching
- true cross-user shared prefix reuse
- subprocess/default serving cache-handle transport
- making `X-Owlmlx-Session-Id` the long-term consumer integration requirement
- default-on production rollout
- source-of-truth promotion to `supported`
- OwlCoda-side product integration work

## current_truth

- OwlMLX already has a real session KV cache store and native streaming reuse
  path.
- That path is `experimental`, default-off, native-backend only, and requires
  `OWLMLX_SESSION_CACHE_ENABLED=1`.
- Reuse currently depends on an explicit `X-Owlmlx-Session-Id` and the same
  `model_id`.
- Non-stream `generate` remains fresh single-request cache today.
- The current OpenAI / Anthropic compatibility routes can forward the explicit
  header, but they do not derive a mainstream cache scope by themselves.
- B-2.1 adds a read-only prefix-candidate classifier with stable reason codes;
  it proves eligibility/ineligibility for future reuse but does not return or
  mutate cache handles.
- B-2.2 maps OpenAI `usage.prompt_tokens_details.cached_tokens` and Anthropic
  `cache_read_input_tokens` only when backend event/result detail carries real
  `session_kv_cache.cached_prompt_tokens` metadata for the current request.
- `/v1/runtime/session-kv-cache` remains the diagnostic truth surface for the
  explicit session lane.
- B-1c section 2 has one recent gap-free swap-bearing segment, but the
  aggregate requirement remains 24h / 6 swaps / zero cache drops, expirations,
  and rejects.
- The 2026-06-01 `20260601T074541Z` topoff was operator-paused before the
  planned 4h / 1-swap boundary. Its ledger reached `last_elapsed_s=8298.33`
  with zero drops / expirations / rejects and `max_drift_bytes=171704320`, but
  `swap_count=0` and no segment rollup exists. It is useful diagnostic evidence
  only, not clean B-1c section 2 aggregate input. See
  `files/evidence/owlmlx/bench/session-kv-soak/20260601T100445Z-b1c2-partial-interrupted-topoff-summary.json`.
- Correction: the immediate way to test the remaining boundary question is a
  short forced-swap canary with a 5-minute swap cadence. A 4h wall-clock wait is
  not intrinsically valuable when the specific question is whether unload /
  settle / load boundaries are cache-clean.
- The 2026-06-01 `20260601T125751Z` forced canary used that shape: 20 minutes,
  4 swaps, 5-minute cadence. It met duration and swap requirements, had clean
  swap boundaries, `measurement_wall_clock_gap_free=true`, and zero session
  cache drops / expirations / rejects. The old rollup failed on global drift
  (`max_drift_bytes=46801784452`), but re-audit shows that number compares
  Gemma active memory against the first Qwen27 measurement. Same-model load
  epoch accounting narrows the actionable blocker to Gemma drift of
  `751370240` bytes, with `max_same_model_load_epoch_unaccounted_session_kv_drift_bytes=0`.
- The 2026-06-01 `20260601T134131Z` cache-object resident canary used the same
  5-minute boundary-stress shape for 10 minutes / 2 swaps after runtime status
  began recording direct upstream cache-object `nbytes` when available. It had
  clean boundaries and zero drops / expirations / rejects. Every measurement
  row used `resident_bytes_estimate_mode=cache_object_nbytes`; Gemma raw
  same-model drift remained `751370240` bytes, but direct cache-object resident
  bytes reached `1054965760` and same-model unaccounted drift stayed `0`.

## remaining_gaps

1. B-1c section 2 still needs aggregate stability: the current clean evidence
   volume is below the 24h / 6-swap gate required before real cache-handle reuse
   can be considered. The operator-paused `20260601T074541Z` ledger does not
   reduce this gap because it ended before any swap boundary.
2. The immediate executable gap is no longer passive duration. It is fast-swap
   same-model drift-gate triage: decide whether the raw 751MB Gemma drift
   remains a hard promotion blocker, or whether direct `cache_object_nbytes`
   resident working-set accounting with zero unaccounted same-model drift is
   the correct gate before B-2.3 consumes this evidence.
3. B-2.3 automatic safe prefix reuse is not implemented and must remain blocked
   until B-1c section 2 aggregate stability passes.
4. The explicit `X-Owlmlx-Session-Id` lane is still the only runtime path that
   can physically reuse a cache handle today; it remains experimental and must
   not be presented as the mainstream consumer contract.
5. Source-of-truth docs must continue to distinguish three separate facts:
   classifier diagnostics, compatibility-visible real cached-token accounting,
   and actual automatic reuse.

## dominant_next_gap

`B-1c-section-2-fast-swap-same-model-drift-triage-for-B-2.3`

The next executable closure is not another consumer-side adapter and not F-3
runtime work. B-2.1 and B-2.2 are already landed; the dominant blocker is the
B-1c section 2 fast-swap drift failure that B-2.3 explicitly depends on. Do not
run another passive 4h topoff to answer this question. First triage the
`20260601T125751Z` 5-minute-cadence canary: boundaries were clean, the legacy
46.8GB number was a cross-model baseline artifact, and the actionable raw
same-model drift is 751MB on Gemma. Keep B-2.3 automatic reuse blocked as a
capability claim until this blocker is closed and the 24h / 6-swap prerequisite
is honestly met. The `20260601T134131Z` follow-up proves the resident working
set can now be measured directly (`cache_object_nbytes`) and fully accounts for
the Gemma drift; it does not by itself relax the raw gate.
