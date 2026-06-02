# owlmlx Goal Contract: Mainstream Prefix-Cache Compatibility Closure

> Status: active goal contract
> Updated: 2026-06-02 after B-2.3 prompt-only refresh real-hit probe

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
- Explicit reuse depends on `X-Owlmlx-Session-Id` and the same `model_id`.
- B-2.3 adds a first opt-in no-header automatic prefix slice behind
  `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`. It is native-streaming only,
  default-off, and falls back to fresh cache when the prefix classifier rejects
  the candidate.
- The automatic no-header lane is stricter than the explicit session lane:
  edited-prefix reuse is rejected unless the existing prompt is a full token
  prefix of the requested prompt, and generated-token-extended entries are not
  retained as reusable automatic state. When completion trim is unavailable,
  current code attempts a prompt-only refresh for the remembered prompt; if that
  refresh is unavailable, it evicts/falls back.
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
- B-1c section 2 has clean load/switch evidence, but the base gate has been
  re-founded on four count-based axes: load, throughput, switch, concurrency.
  Duration is now a reported byproduct, not the pass bar.
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
- The 2026-06-01 `20260601T141659Z` 2h / 24-swap high-frequency run proved the
  user point: 5-minute switching finds real issues. It kept swap boundaries,
  drops, expirations, rejects, and wall-clock continuity clean, but failed the
  reviewed resident gate because Gemma resident bytes reached `2768240640`
  against the `2147483648` budget.
- The follow-up `20260601T162203Z` 40m / 8-swap validation after adding
  `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES` LRU cap support stayed clean:
  `drift_gate.mode=cache_object_resident_accounted`, `hard_failure=false`,
  `clean_for_interrupted_aggregate=true`, drops / expirations / rejects all 0,
  4 LRU evictions, and `max_session_cache_resident_bytes=2144829440` within the
  `2147483648` budget. It remains `blocked` only because it is not the canonical
  aggregate duration.
- The `20260601T172007Z` no-header automatic-prefix run used the user-requested
  5-minute switch cadence for 20 minutes / 4 swaps. It stayed boundary-clean and
  cache-clean: `swap_boundaries_clean=true`,
  `measurement_wall_clock_gap_free=true`, drops / expirations / rejects all 0,
  `max_same_model_load_epoch_drift_bytes=54067200`, and resident working set
  `358481920 <= 2147483648`. This validates automatic-lane safety/fallback
  under fast switching, not real cache-hit performance.
- The `20260602T004000Z` Qwen3.6-27B-4bit no-header hit probe loaded, generated,
  and unloaded successfully, but failed the real-hit gate with
  `usable_hit_count=0`, `hits_total=0`, and
  `known_blocker=auto_prefix_completion_trim_unavailable`. That blocker is now
  historical evidence: current code adds prompt-only refresh for the automatic
  scope.
- The `20260602T011000Z` Qwen3.6-27B-4bit no-header hit probe passed under
  current code with `usable_hit_count=1`, `hits_total=1`, drops / expirations /
  rejects all `0`, `completion_trim_unavailable_count=0`, and two safe
  non-prefix fallbacks recorded as
  `auto_prefix_ineligible_not_token_prefix`.
- The `20260602T002448Z` current-code 20-minute / 4-swap validation used the
  5-minute switch cadence with `--session-cache-auto-prefix`. It was
  boundary-clean and cache-clean (`swap_boundaries_clean=true`,
  `measurement_wall_clock_gap_free=true`, drops / expirations / rejects all `0`,
  `max_same_model_load_epoch_drift_bytes=60620800`,
  `max_session_cache_resident_bytes=364216320`) and audit reports
  `clean_for_interrupted_aggregate=true`; it remains `blocked` because the
  current §2 runner still under-measures throughput decay and concurrency
  breadth.
- Route-level OpenAI and Anthropic streaming tests now prove that ordinary
  no-header compatibility requests can receive cached-token usage when backend
  stream events carry real per-request `session_kv_cache.cached_prompt_tokens`
  metadata. The tests also assert the route does not pass a private `session_id`
  kwarg.
- The `20260602T015245Z` real Qwen27 compat-route probe passed through
  no-header OpenAI SSE and Anthropic SSE with cached-token usage surfaced from
  runtime metadata (`openai_cached_tokens=26`,
  `anthropic_cache_read_input_tokens=26`), `hits_total=2`, and drops /
  expirations / rejects all `0`.
- The `20260602T015559Z` Qwen35 and Gemma31 compat-route probes passed the same
  no-header OpenAI/Anthropic surface gate. Qwen35 surfaced `26` cached/read
  tokens; Gemma31 surfaced `25`; both had `hits_total=2` and drops /
  expirations / rejects all `0`.

## remaining_gaps

1. B-1c section 2 still needs four-axis evidence: load/switch are countable, but
   throughput decay and concurrency breadth are under-measured. The operator-
   paused `20260601T074541Z` ledger does not reduce this gap because it ended
   before any swap boundary and measured neither missing axis.
2. The immediate false blocker is closed: raw 751MB Gemma same-model drift is
   accepted only when direct `cache_object_nbytes` resident working-set
   accounting is available, resident cache bytes stay within budget, and
   unaccounted same-model drift stays within the raw drift budget. Do not carry
   this forward as a generic raw-RSS leak claim.
3. Resident pressure now has a runtime control and first validation; the first
   B-2.3 opt-in implementation can consume it, but any broader claim still
   needs an explicit aggregate / policy decision.
4. B-2.3 automatic safe prefix reuse is implemented only as a narrow
   native-streaming, no-header, default-off slice. It now proves strict admission,
   safe fallback, and one real Qwen27 no-header cached-token hit via prompt-only
   refresh. It must remain an `experimental` capability claim until B-1c section
   2 aggregate / policy evidence and broader B-2 coverage justify anything
   wider.
5. The explicit `X-Owlmlx-Session-Id` lane is no longer the only physical reuse
   path, but it remains the dogfood/control lane and must not be presented as
   the mainstream consumer contract.
6. Source-of-truth docs must continue to distinguish three separate facts:
   classifier diagnostics, compatibility-visible real cached-token accounting,
   and actual automatic reuse.

## dominant_next_gap

`B-1c-section-2-high-frequency-swap-aggregate-policy-for-B-2.3`

The next executable closure is not another consumer-side adapter and not F-3
runtime work. B-2.1, B-2.2, and the first B-2.3 automatic slice are already
landed. The remaining closure has two concrete blockers:

1. B-1c section 2 count-based evidence is still required for any broader
   stability claim. Do not run another passive 4h topoff with one switch. Keep
   the 5-minute cadence for switch stress, but add throughput-decay sampling and
   breadth/concurrency pressure so the two previously empty axes are measured.
2. The prior real-hit blocker
   (`auto_prefix_completion_trim_unavailable` on Qwen27) is resolved by
   prompt-only refresh. Route-level tests now cover OpenAI/Anthropic streaming
   metadata propagation without a private session header, and real-model route
   evidence now passes for Qwen27, Qwen35, and Gemma31 on OpenAI SSE and
   Anthropic SSE. The remaining implementation/evidence gap is B-1c aggregate /
   policy coverage under the same narrow safety contract, not another
   consumer-side private-header adapter.

Keep B-2.3 broader promotion blocked until both blockers are honestly resolved.
