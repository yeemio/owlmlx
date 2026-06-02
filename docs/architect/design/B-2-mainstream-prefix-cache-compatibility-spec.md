# B-2 Mainstream Prefix-Cache Compatibility Spec

> Status: design-grade spec; B-2.1 classifier, B-2.2 metadata plumbing, and first B-2.3 opt-in automatic prefix slice landed; prompt-only refresh now produces real no-header Qwen27 hits, while broader promotion remains blocked on B-1c aggregate / policy evidence
> Updated: 2026-06-02
> Campaign: B-2
> Parent goal:
> `files/goals/owlmlx/mainstream-prefix-cache-compatibility-closure-goal-contract.md`

## 1. Purpose

B-2 closes the gap between OwlMLX's current experimental session KV cache and
the behavior mainstream OpenAI / Anthropic compatibility consumers expect from a
runtime-owned prefix-cache lane.

The current explicit session header is useful as a dogfood/control path. It is
not the target contract. OwlCoda, Codex, and other OpenAI-compatible clients
should not need to learn an OwlMLX-private header to benefit from safe
prefix-cache behavior.

This spec freezes the B-2 design and tracks its staged implementation. B-2.1
was classifier/diagnostic-only; B-2.2 added real cached-token metadata plumbing;
B-2.3 now has a first opt-in native-streaming automatic prefix slice. None of
these slices promotes the capability beyond `experimental`.

## 2. Current Truth

Current verified truth:

- Explicit session KV cache exists.
- It is `experimental`, default-off, native-backend only, and enabled by
  `OWLMLX_SESSION_CACHE_ENABLED=1`.
- The explicit lane requires `X-Owlmlx-Session-Id`.
- Native streaming can reuse an explicit `(session_id, model_id)` prompt cache.
- Non-stream `generate` still uses a fresh single-request cache.
- `/v1/runtime/session-kv-cache` is the diagnostic status surface.
- B-2.2 now maps OpenAI `prompt_tokens_details.cached_tokens` and Anthropic
  `cache_read_input_tokens` only when backend event/result detail carries real
  `session_kv_cache.cached_prompt_tokens` metadata for the current request.
- B-2.3 now adds `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`, an opt-in
  no-header native streaming lane. It derives a runtime-owned automatic prefix
  scope only when no explicit session header is present, reuses only classifier
  eligible token-prefix candidates, and falls back to fresh cache with an
  ineligible reason instead of merging unrelated prompts.
- B-1c section 2 remains blocked: short clean forced-swap canaries validate
  unload / settle / load boundaries, but the base gate now requires four
  count-based axes and still under-measures throughput decay and concurrency
  breadth.
- The operator-paused `20260601T074541Z` topoff is not aggregate input: its
  partial ledger reached about 2h18m with zero drops / expirations / rejects,
  but `swap_count=0` and no rollup exists. It cannot unlock B-2.3 because the
  required unload / settle / load boundary was not exercised.
- Correction: when the question is whether the swap boundary itself is clean,
  the right next step is a short forced-swap canary with high-frequency swaps
  such as one swap every 5 minutes, not another passive 4h wait.
- The `20260601T125751Z` 20-minute / 4-swap forced canary exercised a
  5-minute swap cadence and found the useful blocker: all four swap boundaries
  were clean and session-cache drops / expirations / rejects stayed zero. The
  old rollup reported `max_drift_bytes=46801784452`, but that was a legacy
  global-baseline artifact caused by comparing Gemma active memory against the
  first Qwen27 measurement. Re-audit with same-model load-epoch accounting
  reports `max_same_model_load_epoch_drift_bytes=751370240` on Gemma and
  `max_same_model_load_epoch_unaccounted_session_kv_drift_bytes=0`. The
  actionable blocker is therefore same-model fast-swap drift over the raw 200MiB
  B-1c section 2 gate, not a 46GB leak and not a consumer-header problem.
- The follow-up `20260601T134131Z` 10-minute / 2-swap canary ran after the
  runtime began recording direct upstream cache-object bytes
  (`cache_object_nbytes`) in the session KV status surface. It again kept swap
  boundaries clean and drops / expirations / rejects at 0. Every measurement row
  used `resident_bytes_estimate_mode=cache_object_nbytes`; Gemma still had raw
  same-model drift `751370240` bytes, but direct cache-object resident bytes
  reached `1054965760` and same-model unaccounted drift remained `0`. B-2.3 is
  therefore no longer blocked on missing metadata or a raw-RSS false-fail. It
  remains blocked until B-1c §2 has enough high-frequency swap evidence under
  the reviewed resident-accounted drift gate.
- The `20260601T141659Z` 2h / 24-swap high-frequency run found a real resident
  pressure blocker: boundaries and drops stayed clean, but Gemma resident bytes
  grew to `2768240640`, over the reviewed `2147483648` working-set budget.
  OwlMLX then added `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES` LRU cap support;
  the `20260601T162203Z` 40m / 8-swap validation stayed within budget
  (`2144829440 <= 2147483648`) with 4 LRU evictions and no drops / expirations /
  rejects. This was enough to land the first opt-in B-2.3 code slice, but not
  enough to promote the capability claim beyond `experimental`.
- The `20260601T172007Z` no-header automatic-prefix 20-minute / 4-swap run kept
  the 5-minute switch cadence and stayed clean: `swap_boundaries_clean=true`,
  `measurement_wall_clock_gap_free=true`, drops / expirations / rejects all `0`,
  `max_same_model_load_epoch_drift_bytes=54067200`, and resident working set
  `358481920 <= 2147483648`. This validates the safety/fallback side of the
  opt-in automatic lane under boundary stress, not a cache-hit claim.
- The `20260602T004000Z` B-2 automatic-prefix hit probe used Qwen3.6-27B-4bit
  on the no-header native streaming path and exposed the old real-hit blocker:
  `usable_hit_count=0` with
  `known_blocker=auto_prefix_completion_trim_unavailable`.
- OwlMLX then added a prompt-only refresh primitive for the automatic no-header
  scope. Instead of retaining a generated-token-extended cache entry when
  completion trim is unavailable, the backend rebuilds a prompt-only cache for
  the remembered prompt and stores that object for later eligible prefix reuse.
- The `20260602T011000Z` Qwen3.6-27B-4bit no-header hit probe passed with
  `usable_hit_count=1`, `hits_total=1`, drops / expirations / rejects all `0`,
  `completion_trim_unavailable_count=0`, and two safe non-prefix fallbacks
  recorded as `auto_prefix_ineligible_not_token_prefix`.
- The `20260602T002448Z` current-code 20-minute / 4-swap safety validation used
  the same 5-minute cadence under `--session-cache-auto-prefix`. It was
  functionally clean (`swap_boundaries_clean=true`,
  `measurement_wall_clock_gap_free=true`, drops / expirations / rejects all `0`,
  `max_same_model_load_epoch_drift_bytes=60620800`,
  `max_session_cache_resident_bytes=364216320`), and audit reports
  `clean_for_interrupted_aggregate=true`; it remains `blocked` because the base
  B-1c §2 gate now requires four count-based axes and still under-measures
  throughput decay and concurrency breadth.
- Route-level tests now cover the no-header compatibility surface: ordinary
  OpenAI `/v1/chat/completions` SSE and Anthropic `/v1/messages` SSE requests do
  not pass `session_id`, and when backend stream events carry real
  `session_kv_cache.cached_prompt_tokens`, the routes emit
  `usage.prompt_tokens_details.cached_tokens` and `usage.cache_read_input_tokens`
  respectively. This is route-contract proof, not a real-model route benchmark.
- Real route evidence now covers the three primary local models through the
  native backend. The `20260602T015245Z` Qwen27 run, `20260602T015559Z` Qwen35
  run, and `20260602T015559Z` Gemma31 run each issued no-header OpenAI SSE and
  Anthropic SSE requests through FastAPI `TestClient`; each model produced one
  cached-token hit on each surface, `hits_total=2`, drops / expirations /
  rejects all `0`, and verdict `passed`.

## 3. Design Goal

B-2 defines an OwlMLX-owned mainstream compatibility lane with these end-state
properties:

1. A caller using ordinary OpenAI / Anthropic compatibility payloads can receive
   safe prefix-cache behavior without supplying `X-Owlmlx-Session-Id`.
2. Automatic reuse is considered only when OwlMLX can prove token-prefix
   equivalence for the same model, tokenizer, runtime profile, template
   boundary, and isolation policy.
3. Cache usage is visible through compatibility payloads only when the runtime
   has real cache-hit accounting for that request.
4. The explicit session header remains an experimental control lane, not a
   supported mainstream consumer contract.

## 4. Non-Goals

B-2 does not implement or promise:

- paged KV;
- continuous batching;
- cross-user shared prefix reuse;
- subprocess cache-handle transport;
- non-stream cache reuse before the native path can report real cache metadata;
- default-on cache behavior;
- B-1 promotion to `supported`;
- OwlCoda product integration work.

## 5. Staged Gates

### 5.1 B-2.0 Source-Of-Truth And Contract Freeze

Scope:

- Correct stale source-of-truth rows that deny the existing explicit session
  cache lane.
- Archive the goal contract and design-grade spec.
- Record that mainstream compatibility is OwlMLX-owned.

Pass:

- `native-mlx-backend-capability-matrix.md` distinguishes explicit
  session-scoped reuse (`experimental`) from mainstream implicit prefix reuse
  (not implemented in B-2.0; later B-2.3 updates are tracked below).
- `public-surface.md` distinguishes the experimental diagnostic route from
  compatibility usage fields that remain absent.
- `01-mainline-roadmap.md` introduces B-2 as a near-term Campaign B goal, while
  keeping B-1c section 2 separate.

### 5.2 B-2.1 Prefix-Candidate Classifier

Scope:

- Add a read-only classifier that accepts:
  - `model_id`;
  - tokenized prompt;
  - tokenizer/runtime profile identity;
  - chat-template/profile boundary identity;
  - isolation scope.
- Return `eligible` / `ineligible` plus reason.
- Do not return, clone, mutate, trim, or reuse a cache object.

Required reasons:

| Reason | Meaning |
|---|---|
| `same_model_token_prefix` | Same model/runtime profile and exact token-prefix relation proven. |
| `different_model` | Model identity differs. |
| `different_runtime_profile` | Tokenizer/template/runtime profile differs. |
| `not_token_prefix` | Prompt tokens do not form a prefix relation. |
| `unsafe_isolation_scope` | Reuse would cross the configured isolation boundary. |
| `trim_unavailable_for_edit` | The request needs edited-prefix reuse but trim support is unavailable. |

Pass:

- The classifier can prove same-token-prefix eligibility.
- It rejects different models and runtime profiles.
- It rejects tokenizer/template boundary mismatches.
- It rejects unsafe isolation.
- It emits stable reason codes.
- Tests prove no cache handle is reused and no reuse claim is emitted.

### 5.3 B-2.2 Real Cache Metadata Plumbing

Status: landed on 2026-06-01.

Scope:

- Thread runtime cache decision metadata through existing result/event types.
- Expose cached-token counts to compatibility payloads only when produced by
  the runtime for the current request.

Target OpenAI shape:

```json
{
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 10,
    "total_tokens": 110,
    "prompt_tokens_details": {
      "cached_tokens": 64
    }
  }
}
```

Target Anthropic shape:

```json
{
  "usage": {
    "input_tokens": 100,
    "output_tokens": 10,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 64
  }
}
```

Pass:

- Cached-token fields are absent or zero when the runtime reports no hit.
- Cached-token fields are positive only when the runtime reports a real hit.
- Tests prevent fabricated cache counts.

### 5.4 B-2.3 Automatic Safe Reuse

Scope:

- First code slice may run behind an explicit runtime flag after B-2.1/B-2.2
  and the resident-accounted 5-minute swap evidence show no cache correctness
  failures.
- Uses the classifier as an admission gate.
- Reuses a cache only under proven prefix equivalence and configured isolation.

Pass:

- B-1c section 2 aggregate / policy evidence is sufficient for the claim being
  made; otherwise the stage remains `experimental` and default-off.
- Reuse is opt-in or guarded behind a clearly named runtime flag.
- It does not merge unrelated conversations.
- It emits real cache metadata.
- On the automatic no-header lane, a generated-token-extended cache entry is
  not retained as the reusable entry. If completion trim cannot return the
  concrete upstream cache to prompt-only state, OwlMLX must either rebuild and
  persist a prompt-only cache for the remembered prompt or evict/fallback with
  an explicit blocker reason.

## 6. Safety Contract

Automatic prefix reuse must be rejected unless all of these are true:

1. same `model_id`;
2. same tokenizer identity;
3. same chat-template/runtime profile identity;
4. same cache implementation/version identity;
5. exact token-prefix relation;
6. compatible isolation scope;
7. cache object supports the needed operation:
   - append-only exact-prefix reuse; or
   - safe trim for edited-prefix reuse.

If any check is unknown, the classifier returns `ineligible`. Unknown must not be
treated as eligible.

## 7. Consumer Boundary

`X-Owlmlx-Session-Id` remains:

- allowed for dogfood and diagnosis;
- useful for explicit native session experiments;
- visible in `/v1/runtime/session-kv-cache`.

It is not:

- the target mainstream consumer contract;
- something OwlCoda must hard-code to get normal prefix-cache behavior;
- evidence of OpenAI / Anthropic compatible cache usage by itself.

## 8. Implementation Constraints

- No new `*_contract.py`, `*_harness.py`, `*_evidence.py`, `*_ledger.py`, or
  other banned spec-as-code modules under `owlmlx/`.
- Prefer extending existing runtime modules when a runtime consumer will read
  the fields/functions.
- Classifier-only code may live in the existing cache/runtime area only if
  production runtime code calls it.
- Design and source-of-truth documents must not be imported by runtime code.

## 9. Test Plan

B-2.1 tests:

- same token-prefix candidate accepted;
- different model rejected;
- different runtime profile rejected;
- tokenizer/template boundary mismatch rejected;
- unsafe isolation rejected;
- trim-unavailable edited-prefix request rejected;
- no cache object reused;
- no compatibility usage count emitted.

B-2.2 tests:

- OpenAI non-stream usage remains unchanged when no cache metadata exists;
- OpenAI usage includes `prompt_tokens_details.cached_tokens` when a real hit is
  reported;
- Anthropic usage uses real `cache_read_input_tokens`;
- streaming final usage never fabricates cached-token counts.

B-2.3 tests:

- automatic reuse remains disabled until the configured flag/gate is enabled;
- enabled path reuses only eligible prefix candidates;
- ineligible cases fall back to fresh cache and emit an ineligible reason;
- runtime status counters match compatibility usage counters.
- OpenAI and Anthropic streaming compatibility routes map real no-header backend
  cache metadata without requiring `X-Owlmlx-Session-Id`.

## 10. Evidence Paths

Expected future evidence root:

`files/evidence/owlmlx/bench/prefix-cache-compatibility/`

Expected row families:

- `b2.prefix_candidate_classifier.v1`
- `b2.compat_usage_accounting.v1`
- `b2.automatic_prefix_reuse.v1`
- `b2.compat_route_automatic_prefix_reuse.v1`

No evidence file in this design round promotes the capability.

## 11. Promotion Ceiling

After B-2.0:

- explicit session KV remains `experimental`;
- mainstream automatic prefix cache was not yet implemented in that stage;
- compatibility cache usage remains absent.

After B-2.1:

- OwlMLX may claim classifier-level eligibility diagnostics only.

After B-2.2:

- OwlMLX may claim compatibility-visible cache accounting only for runtime paths
  that report real cached-token counts. It must not claim automatic safe prefix
  reuse or infer per-request counts from aggregate status counters.

After B-2.3:

- OwlMLX may claim a narrow, opt-in automatic prefix-cache implementation
  exists for native streaming. Current Qwen27 evidence shows a real no-header
  hit is possible through prompt-only refresh, with safe fallback for non-prefix
  prompts; route evidence now extends the no-header OpenAI/Anthropic metadata
  path to Qwen27, Qwen35, and Gemma31. It may claim a broader automatic
  prefix-cache lane only if B-1c section 2 aggregate stability / policy and
  wider B-2 compatibility evidence both pass.

No stage in this spec independently promotes B-1 to `supported`.

## 12. Next Handoff

The first B-2.3 code-grade slice has landed, the first Qwen27 no-header real-hit
blocker has been resolved by prompt-only refresh, and no-header OpenAI/Anthropic
route evidence now passes on Qwen27, Qwen35, and Gemma31. The next round should
not run longer passive soaks hoping for a different result; it should decide the
B-1c aggregate / policy evidence needed for the already-working narrow automatic
prefix lane, then expand coverage only where the same safety contract can be
measured.

Immediate handoff:

1. Preserve the `20260601T125751Z` / `20260601T134131Z` finding: the boundary is
   clean; the legacy 46.8GB global drift is a cross-model baseline artifact; the
   Gemma raw same-model load-epoch drift is real but explained by direct
   cache-object resident bytes.
2. Keep the reviewed B-1c §2 drift gate narrow: raw drift can be accepted only
   when `drift_gate.mode=cache_object_resident_accounted`, the estimate kind is
   `cache_object_nbytes`, resident working set is within budget, and
   unaccounted same-model drift is within budget.
3. Keep the 5-minute forced-swap canary as the boundary-stress shape. Do not
   replace it with passive long runs that perform only one switch.
4. Keep resident pressure capped with
   `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES`; count LRU evictions separately
   from drops.
5. Treat forced canaries as boundary diagnostics only, not as B-1c §2 promotion
   evidence unless they satisfy the current four-axis gate.
6. Aggregate only completed segments with `measurement_wall_clock_gap_free=true`
   and clean
   cache/drop/swap-boundary audit results.
7. Keep automatic prefix reuse disabled by default and guarded by
   `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`.
8. Do not treat partial measurement-only ledgers as B-1c section 2 aggregate
   input. The segment must reach its planned swap boundary and produce a rollup.
9. Refresh this spec when B-1c section 2 either passes the aggregate gate,
   accepts a revised high-frequency aggregate policy, or produces a new blocker
   that changes B-2.3 feasibility.
10. Preserve the `20260602T004000Z` blocker as historical evidence only:
    automatic no-header reuse could not produce real `cached_tokens` while
    completion trim returned `0`. The `20260602T011000Z` prompt-only-refresh
    probe supersedes it for current code.

The implemented B-2.3 slice proves the key software boundary in unit tests and
real Qwen27 evidence: enabled no-header requests reuse only full-prefix
candidates after prompt-only refresh, disabled requests keep fresh-cache
behavior, ineligible requests fall back to fresh cache with an explicit reason,
and trim-unavailable automatic requests do not retain generated-token-extended
entries. Broader claims still require aggregate / policy acceptance and wider
B-2 coverage.

## 13. Change Log

- 2026-06-01: Initial design-grade spec for B-2 mainstream prefix-cache
  compatibility closure.
- 2026-06-01: B-2.1 read-only prefix-candidate classifier landed with focused
  tests; automatic reuse and cached-token usage fields remain future stages.
- 2026-06-01: B-2.2 real cache metadata plumbing landed. Native stream events
  carry per-request `session_kv_cache.cached_prompt_tokens`, and
  OpenAI/Anthropic compatibility usage maps that field only when present.
- 2026-06-01: Updated next handoff after B-2.1/B-2.2 landed. B-2.3 automatic
  reuse remains blocked on B-1c section 2 aggregate stability, so the dominant
  execution path returns to clean gap-free prompt-reset swap segments.
- 2026-06-01: Recorded operator-paused `20260601T074541Z` topoff as partial
  diagnostic evidence only. It was cache-clean through `8298.33s`, but had
  `swap_count=0` and no segment rollup, so it does not change the B-2.3 blocker.
- 2026-06-01: Corrected the next executable step: for swap-boundary mechanics,
  use a short forced-swap canary with a 5-minute swap cadence instead of
  passively waiting for another 4h segment.
- 2026-06-01: Recorded `20260601T125751Z` 20-minute / 4-swap forced canary.
  It proved swap boundaries can be clean under 5-minute cadence. Follow-up
  re-audit split the legacy global 46.8GB inter-model baseline artifact from the
  actionable same-model Gemma drift (`751370240` bytes, unaccounted upper bound
  `0`). B-2.3 is blocked on this metric decision/root cause, not on another
  passive soak duration.
- 2026-06-01: Recorded `20260601T134131Z` cache-object resident accounting
  canary. Runtime status now reports direct upstream cache-object `nbytes` when
  available; the canary shows all measurement rows using `cache_object_nbytes`,
  Gemma raw same-model drift `751370240`, resident cache bytes `1054965760`,
  and same-model unaccounted drift `0`.
- 2026-06-01: Closed the B-1c §2 raw-drift false-fail with a reviewed
  `cache_object_resident_accounted` drift gate. Automatic reuse remains blocked
  until aggregate / policy evidence exists under the 5-minute swap cadence.
- 2026-06-01: Recorded the 2h / 24-swap high-frequency resident-pressure
  failure (`20260601T141659Z`) and the follow-up resident-cap validation
  (`20260601T162203Z`). The runtime now has opt-in LRU resident cap support via
  `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES`; B-2.3 promotion remains blocked
  pending aggregate / policy review.
- 2026-06-01: Landed the first B-2.3 opt-in automatic prefix slice behind
  `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`. It is native-streaming only,
  no-header, classifier-gated, and default-off; ineligible requests fall back
  to fresh cache.
- 2026-06-02: Tightened B-2.3 automatic no-header safety. The automatic lane now
  requires the existing prompt tokens to be the full prefix of the requested
  prompt, does not count a reuse as a hit when trim later fails, and evicts
  automatic entries when completion trim is unavailable after generation. The
  `20260602T004000Z` Qwen27 probe documents the first real-hit blocker:
  `auto_prefix_completion_trim_unavailable`.
- 2026-06-02: Added prompt-only refresh for the automatic no-header scope. The
  `20260602T011000Z` Qwen27 probe passed with one usable no-header hit, safe
  non-prefix fallbacks, and zero drops / expirations / rejects. The
  `20260602T002448Z` 20-minute / 4-swap current-code validation stayed
  cache-clean and boundary-clean under 5-minute cadence, but remains blocked for
  canonical graduation because throughput/concurrency axes are still
  under-measured.
- 2026-06-02: Added route-level no-header compatibility tests for OpenAI SSE
  `cached_tokens` and Anthropic SSE `cache_read_input_tokens`. These tests prove
  metadata propagation through compatibility surfaces when the backend supplies
  real per-request cache metadata; they do not replace real-model route evidence
  or B-1c aggregate / policy gates.
- 2026-06-02: Added and ran the real-model `compat-route-hit` probe. The
  `20260602T015245Z` Qwen27 route run passed on both OpenAI SSE and Anthropic
  SSE without `X-Owlmlx-Session-Id`, with cached-token counts surfaced from
  runtime metadata and zero drops / expirations / rejects.
- 2026-06-02: Extended `compat-route-hit` to Qwen35 and Gemma31
  (`20260602T015559Z`). Both passed on OpenAI SSE and Anthropic SSE without
  `X-Owlmlx-Session-Id`, with one cached-token hit per surface and drops /
  expirations / rejects all `0`. This closes the three-primary-model route
  evidence gap, not the B-1c aggregate / policy gate.
