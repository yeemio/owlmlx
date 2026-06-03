# Session KV Cache Experimental Contract

> Status: authoritative
> Updated: 2026-06-02
> Implementation: `owlmlx/session_kv_cache.py`,
> `owlmlx/runtime/mlx_native_backend.py`

## 1. Scope

Session KV cache is an experimental native-backend capability for explicit
single-session prompt-prefix reuse plus a narrower opt-in automatic prefix
reuse slice.

It is intentionally narrow:

- only `MlxNativeBackend`
- only when `OWLMLX_SESSION_CACHE_ENABLED=1`
- explicit reuse still requires `X-Owlmlx-Session-Id`
- opt-in automatic reuse additionally requires
  `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`
- reuse is scoped to the same model and either the explicit session id or the
  runtime-owned automatic prefix scope
- append-only reuse is supported when the upstream cache cannot be trimmed
  in the explicit session lane
- tail-edit reuse is attempted only when `mlx_lm.models.cache.trim_prompt_cache`
  can trim the concrete cache object
- automatic no-header reuse must keep a prompt-only entry; if generated-token
  completion trim is unavailable, OwlMLX rebuilds a prompt-only cache for the
  remembered prompt when it can, otherwise evicts the automatic entry and falls
  back to fresh cache rather than retaining a generated-token-extended prefix
- no default-on implicit prefix matching
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

When disabled, or when no session id is present and automatic prefix reuse is
not explicitly enabled, the native backend keeps its prior single-request
behavior through `CacheManager.acquire_for_request(...)`.

When `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`, a streaming request without
`X-Owlmlx-Session-Id` may enter the runtime-owned automatic prefix scope. The
backend reuses only when the remembered prompt is the complete token prefix of
the requested prompt. Ineligible requests evict the prior automatic entry and
fall back to a fresh cache object; they do not silently merge unrelated prompts.
The automatic lane is stricter than the explicit session lane: it does not keep
append-only generated-token-extended entries as the reusable state when the
upstream cache cannot be trimmed back to prompt-only state after generation.
Current code instead attempts a prompt-only refresh for the remembered prompt;
if that refresh is unavailable, it evicts the automatic entry and falls back.

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
| `OWLMLX_SESSION_CACHE_MAX_PROMPT_TOKENS` | `0` | Optional prompt-token window; `0` leaves it unbounded |
| `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES` | `0` | Optional resident-cache byte cap; `0` leaves it unbounded |
| `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED` | `0` | Enables the opt-in automatic prefix scope for no-header native streaming requests |

No body schema changes are required. HTTP compatibility routes may still use
the `X-Owlmlx-Session-Id` header for the explicit lane, but the automatic lane
does not require that private header.

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

As of B-2.3, the first opt-in automatic prefix slice exists behind
`OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1` for native streaming. OwlMLX must
still report it as experimental and default-off until the B-1c section 2 policy
gate and B-2 compatibility evidence justify a broader claim.

The first B-2.3 real-hit blocker was documented by
`files/evidence/owlmlx/bench/prefix-cache-compatibility/20260602T004000Z-b2-auto-prefix-qwen27-real-hit-summary.json`.
That Qwen3.6-27B-4bit probe loaded and generated successfully, but produced
`usable_hit_count=0` with `known_blocker=auto_prefix_completion_trim_unavailable`.
Current code supersedes that blocker with prompt-only refresh:
`files/evidence/owlmlx/bench/prefix-cache-compatibility/20260602T011000Z-b2-auto-prefix-qwen27-real-hit-summary.json`
passed with `usable_hit_count=1`, `hits_total=1`, drops / expirations / rejects
all `0`, and two safe non-prefix fallbacks. This proves a narrow opt-in
no-header cached-token hit on the Qwen27 native streaming path; it does not make
automatic prefix reuse default-on or supported.
The corresponding JSONL can be re-audited offline with
`scripts/bench/prefix_cache_compatibility.py audit-auto-prefix-ledger`, which
requires the `strict_prefix_extension` row to be the reuse hit, requires a
non-prefix ineligible fallback, and rejects the old trim-unavailable blockers.

Focused compatibility-route tests cover the consumer-facing metadata boundary:
OpenAI `/v1/chat/completions` SSE and Anthropic `/v1/messages` SSE requests can
receive cached-token usage from backend stream-event detail without sending
`X-Owlmlx-Session-Id`. The routes still must not fabricate these fields; they
appear only when the current backend event carries real
`session_kv_cache.cached_prompt_tokens` metadata.

Real route evidence extends that proof beyond a fake backend on the three
primary local models:
`files/evidence/owlmlx/bench/prefix-cache-compatibility/20260602T015245Z-b2-compat-route-qwen27-real-hit-summary.json`
passed with one no-header cached-token hit on OpenAI SSE and one on Anthropic
SSE (`openai_cached_tokens=26`, `anthropic_cache_read_input_tokens=26`);
`20260602T015559Z-b2-compat-route-qwen35-real-hit-summary.json` passed with the
same cached-token counts; and
`20260602T015559Z-b2-compat-route-gemma31-real-hit-summary.json` passed with
`openai_cached_tokens=25` and `anthropic_cache_read_input_tokens=25`. All three
runs report `hits_total=2` and drops / expirations / rejects all `0`.
The current route harness accepts this evidence shape only when the
strict-prefix extension row on each compatibility surface carries the positive
cached/read token count. A cached-token parser hit on a seed row alone is
diagnostic, not route-hit proof. Existing route ledgers can be re-audited with
`scripts/bench/prefix_cache_compatibility.py audit-compat-route-ledger` without
starting the native backend.

This surface does **not** imply any of the following:

- default-on or supported automatic cross-request prefix cache
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

For live consumer validation, use the native preview server rather than the
fake-backend quick-start or the subprocess technical-preview server:

```bash
uv run python scripts/runtime_native_preview_server.py \
  --port 8066 \
  --models-root /Users/yeemio/AI/Agent/models \
  --enable-session-cache \
  --enable-auto-prefix \
  --session-cache-max-resident-bytes 2147483648
```

This preserves public model ids through a local model-path resolver and mounts
`MlxNativeBackend`, so OwlCoda can validate OpenAI/Anthropic streaming usage
metadata without hard-coding OwlMLX-specific session headers or absolute model
paths. The flags above still keep the capability experimental and operator
opt-in; they do not make automatic prefix reuse default-on.

As of B-2.2, compatibility routes may mirror cached-token counts into OpenAI
`usage.prompt_tokens_details.cached_tokens` or Anthropic
`cache_read_input_tokens` only when the backend event/result carries real
per-request `session_kv_cache.cached_prompt_tokens` metadata. They must not
infer request-level cache hits from aggregate `/v1/runtime/session-kv-cache`
counters. As of B-2.3, automatic safe prefix reuse is implemented only as an
opt-in native-streaming slice; upper layers should not normalize the private
session header as their permanent integration burden, and they must not infer
cache hits unless the current request carries real
`session_kv_cache.cached_prompt_tokens` metadata. A runtime result that reports
`auto_prefix_completion_trim_unavailable` remains a safe fallback/no-hit row, not
a hit.

As of the 2026-06-01 B-1c §2 fast-swap drift triage, the diagnostic payload
also reports resident-cache accounting mode. When upstream prompt-cache objects
expose `nbytes`, OwlMLX records `resident_bytes_estimate_mode=cache_object_nbytes`
and `resident_bytes_estimate_modes` rather than relying only on positive
active-memory delta upper bounds. This is stronger operator evidence for the
held cache working set. B-1c §2 now accepts this as the narrow functional drift
gate only when the estimate kind is `cache_object_nbytes`, resident cache bytes
stay within budget, and unaccounted same-model drift stays within the raw drift
budget. It does not relax the aggregate / supported promotion gate by itself.

The 2026-06-01 high-frequency swap tests also added an experimental resident
pressure control: `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES`. When set, the
session cache uses LRU eviction to keep the held cache working set under the
configured byte budget. Evictions are counted as `evictions`, not `drops`; they
may reduce reuse but should not be treated as correctness failures.

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
> together (the §1a Promotion Gate). B-1c §2 has been re-founded on four
> count-based axes: load, throughput, switch, and concurrency. The
> `20260603T031832Z` native fast-count segment passed the canonical 24-swap
> threshold with cache-eviction pressure and independent
> `--require-canonical --require-cache-eviction` audit acceptance; this is not
> continuous 24h evidence and not a standalone promotion. The earlier
> `20260602T095334Z` native smoke remains threshold-path evidence only because
> it stopped at 3 swaps. See
> `runtime-capability-matrix.md` (session-KV row) +
> `docs/architect/design/B-1c-section-2-spec.md` §11. The `experimental` label
> below is still correct; the *criteria* below are not the current ones. Do not
> schedule a continuous 24h current-Mac test from the superseded flat gate; any
> repeat B-1c §2 execution lane must fit inside a 3-4 hour operator window.

The capability remains `experimental` until the live §1a Promotion Gate accepts
B-1a + B-1b + B-1c §1 + B-1c §2 together. The historical flat criteria below
are retained only as superseded context, not as the current runbook:

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
