# owlmlx Goal Contract: Mainstream Prefix-Cache Compatibility Closure

> Status: active goal contract
> Updated: 2026-06-01 after B-2.1/B-2.2 landed

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

## remaining_gaps

1. B-1c section 2 still needs aggregate stability: the current clean evidence
   volume is below the 24h / 6-swap gate required before real cache-handle reuse
   can be considered.
2. B-2.3 automatic safe prefix reuse is not implemented and must remain blocked
   until B-1c section 2 aggregate stability passes.
3. The explicit `X-Owlmlx-Session-Id` lane is still the only runtime path that
   can physically reuse a cache handle today; it remains experimental and must
   not be presented as the mainstream consumer contract.
4. Source-of-truth docs must continue to distinguish three separate facts:
   classifier diagnostics, compatibility-visible real cached-token accounting,
   and actual automatic reuse.

## dominant_next_gap

`B-1c-section-2-aggregate-stability-for-B-2.3`

The next executable closure is not another consumer-side adapter and not F-3
runtime work. B-2.1 and B-2.2 are already landed; the dominant blocker is the
B-1c section 2 aggregate gate that B-2.3 explicitly depends on. Continue
gap-free 4h/one-swap prompt-reset segments, aggregate only clean
`measurement_wall_clock_gap_free=true` segments, and keep B-2.3 automatic reuse
blocked until the 24h / 6-swap prerequisite is honestly met.
