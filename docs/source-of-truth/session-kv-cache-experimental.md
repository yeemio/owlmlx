# Session KV Cache Experimental Contract

> Status: authoritative
> Updated: 2026-06-01
> Implementation: `owlmlx/session_kv_cache.py`,
> `owlmlx/runtime/mlx_native_backend.py`

## 1. Scope

Session KV cache is an experimental native-backend capability for explicit
single-session prompt-prefix reuse.

It is intentionally narrow:

- only `MlxNativeBackend`
- only when `OWLMLX_SESSION_CACHE_ENABLED=1`
- only when the caller sends `X-Owlmlx-Session-Id`
- only within the same `session_id` and `model_id`
- append-only reuse is supported when the upstream cache cannot be trimmed
- tail-edit reuse is attempted only when `mlx_lm.models.cache.trim_prompt_cache`
  can trim the concrete cache object
- no implicit prefix matching
- no paged KV
- no continuous batching
- no subprocess cache-handle transport

The supported subprocess backend remains unchanged.

## 2. Runtime Behavior

When enabled, the native backend stores the cache object returned by
`mlx_lm.models.cache.make_prompt_cache(model)` for the explicit
`(session_id, model_id)` pair. A later stream request with the same pair reuses
that object through the existing `prompt_cache=` argument and sends only the
token suffix after the remembered prompt prefix.

The concrete reuse mode depends on the upstream cache type:

- if the cache can be trimmed, the backend trims generated tokens after a
  stream completes and can also trim an old prompt tail before sending the new
  suffix
- if the cache cannot be trimmed, the backend remembers the prompt plus
  generated token ids and only reuses the cache when the next prompt extends
  that exact prefix; edited or repeated prompts fall back to a fresh
  single-request cache

Non-stream `generate` remains on the fresh single-request cache path in this
experimental slice because it does not expose generated token ids needed to
keep a persistent cache prefix honest.

When disabled or when no session id is present, the native backend keeps its
prior single-request behavior through `CacheManager.acquire_for_request(...)`.

## 3. Memory Discipline

Session cache reuse must never bypass memory discipline:

- unload drops all session cache entries for the unloaded model before the
  native memory actuator clears allocator cache
- TTL expiry removes idle session entries
- LRU eviction removes entries when the store exceeds its configured entry
  count
- yellow/red/fatal pressure watermark hints reject persistent session-cache
  reuse and evict live session entries before falling back to the
  single-request cache path

This first slice does not sample host pressure on the generate hot path.
Pressure hints are passed explicitly by runtime-owned callers that already
possess pressure truth.

## 4. Operator Knobs

| Env var | Default | Meaning |
|---|---:|---|
| `OWLMLX_SESSION_CACHE_ENABLED` | `0` | Enables explicit session cache reuse on the native backend |
| `OWLMLX_SESSION_CACHE_TTL_S` | `60` | Idle TTL for session cache entries |
| `OWLMLX_SESSION_CACHE_MAX_ENTRIES` | `64` | Maximum active session cache entries before LRU eviction |

No body schema changes are required. HTTP compatibility routes use the
`X-Owlmlx-Session-Id` header.

## 5. Compatibility Boundary And OwlMLX-Owned Gap

This section is the current OwlMLX-owned answer for upper-layer consumers such
as OwlCoda.

`X-Owlmlx-Session-Id` is a narrow experimental control for OwlMLX native-backend
diagnostics and internal dogfood. It is **not** the target mainstream consumer
contract. Upper-layer products such as OwlCoda, Codex, or other OpenAI /
Anthropic-compatible clients should not have to learn an OwlMLX-specific session
header to get normal prefix-cache behavior.

The replacement-grade target is OwlMLX-owned mainstream compatibility:

- OpenAI / Anthropic compatibility routes should eventually benefit from safe
  automatic prefix reuse without product-specific session-header plumbing.
- Cache observability should eventually appear in the appropriate compatibility
  usage or documented runtime status fields instead of forcing consumers to
  scrape an experimental diagnostic route.
- The compatibility path must remain isolation-safe: reuse may only occur when
  OwlMLX can prove token-prefix equivalence for the same model/runtime profile,
  and it must not merge unrelated conversations by hidden session id.

Until that target exists, OwlMLX must honestly report this as a local runtime
gap, not as an OwlCoda integration requirement.

This surface does **not** imply any of the following:

- automatic cross-request prefix cache without an explicit session id
- subprocess/default serving prefix reuse
- non-stream `generate` cross-request reuse
- paged KV
- continuous batching
- automatic OpenAI `usage.prompt_tokens_details.cached_tokens`
- automatic Anthropic `cache_read_input_tokens`

The current experimental observability source is:

```text
GET /v1/runtime/session-kv-cache
/v1/runtime/status -> backend.detail.session_kv_cache
```

As of B-2.2, compatibility routes may mirror cached-token counts into OpenAI
`usage.prompt_tokens_details.cached_tokens` or Anthropic
`cache_read_input_tokens` only when the backend event/result carries real
per-request `session_kv_cache.cached_prompt_tokens` metadata. They must not
infer request-level cache hits from aggregate `/v1/runtime/session-kv-cache`
counters. Automatic safe prefix reuse remains a separate B-2.3 gap, not
something upper layers should normalize as their permanent integration burden.

As of the 2026-06-01 B-1c §2 fast-swap drift triage, the diagnostic payload
also reports resident-cache accounting mode. When upstream prompt-cache objects
expose `nbytes`, OwlMLX records `resident_bytes_estimate_mode=cache_object_nbytes`
and `resident_bytes_estimate_modes` rather than relying only on positive
active-memory delta upper bounds. This is stronger operator evidence for the
held cache working set, but it remains diagnostic and does not relax B-1c or
B-2 promotion gates by itself.

Session lifetime and cleanup are currently runtime-side TTL / unload / pressure
behaviors, not a stable external clear-session API. If a future release adds an
explicit clear-session endpoint, or promotes automatic prefix reuse, it must be
documented here before upper layers rely on it.

## 6. Status Surface

`GET /v1/runtime/session-kv-cache` returns the backend-exposed
`owlmlx.session_kv_cache` diagnostic payload when the backend supports it.
For non-native backends, the route returns an experimental disabled fallback
instead of fabricating capability support.

Because this surface is still experimental, the `contract.surface` /
`surface` string is allowed to change before promotion to `supported`.
Clients that need a stable compatibility contract must wait for the promotion
gate rather than keying release logic on the experimental string.

The same payload is also visible at:

```text
/v1/runtime/status -> backend.detail.session_kv_cache
```

## 7. Promotion Gate

> **⚠️ Gate superseded (flagged 2026-05-30 audit).** The flat gate below predates
> the B-1c framework. The live promotion gate is **B-1a + B-1b + B-1c §1 + B-1c §2**
> together (the §1a Promotion Gate). B-1c §2 (≥24h aggregate soak + ≥6 model
> swaps, every segment wall-clock-gap-free) is currently **`blocked` on
> aggregate volume**: the 2026-06-01 repeat produced one gap-free 4h / 1-swap
> aggregate-clean segment, but 24h / 6 swaps are still unmet. See
> `runtime-capability-matrix.md` (session-KV row) +
> `docs/architect/design/B-1c-section-2-spec.md` §11. The `experimental` label
> below is still correct; the *criteria* below are not the current ones.

The capability remains `experimental` until all of the following are true:

- 24h soak with `OWLMLX_SESSION_CACHE_ENABLED=1` and mixed 1-10 sessions
- settle-barrier failed reclaim count is zero
- active-memory drift is bounded against the cache-disabled baseline
- 4k+ multi-turn prompt TTFT p50 improves by at least 5x, measured by
  `scripts/bench/session_kv_cache_ttft.py` in native mode
- abort and unload paths leave no retained session cache entries

Until then, the default remains off.

Current real-model evidence:

- Qwen baseline:
  `files/evidence/owlmlx/bench/session-kv-cache/20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl`
  on native `MlxNativeBackend`, `Qwen3.6-27B-4bit`.
- B-1a Gemma RuntimeKernel evidence:
  `files/evidence/owlmlx/bench/session-kv-cache/20260516T151100Z-b1a-gemma4-31b-it-session-kv-ttft.jsonl`
  on native `MlxNativeBackend` through `RuntimeKernel`, `Gemma 4-31B-it`.
- Shape: 4k system prompt, append-only multi-turn stream, `max_tokens=2`.
- Formula: `disabled.warm_p50_first_token_ms /
  enabled.warm_p50_first_token_ms`, where warm means rounds 2-4.
- Results:
  - Qwen disabled warm TTFT min/p50/max
    `3397.977 / 4026.099 / 4419.626 ms`; enabled warm TTFT min/p50/max
    `536.325 / 543.389 / 652.471 ms`; improvement ratio `7.409x`;
    session cache counters end at `entries_created=1`, `hits=3`, `drops=0`.
  - Gemma disabled warm TTFT min/p50/max
    `1537.596 / 1542.972 / 1558.077 ms`; enabled warm TTFT min/p50/max
    `679.811 / 687.102 / 695.413 ms`; improvement ratio `2.246x`;
    session cache counters end at `entries_created=1`, `hits=3`, `drops=0`.
