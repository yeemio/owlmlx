# Session KV Cache Experimental Contract

> Status: authoritative
> Updated: 2026-05-12
> Implementation: `owlmlx/session_kv_cache.py`,
> `owlmlx/runtime/mlx_native_backend.py`

## 1. Scope

Session KV cache is an experimental native-backend capability for explicit
single-session prompt-cache reuse.

It is intentionally narrow:

- only `MlxNativeBackend`
- only when `OWLMLX_SESSION_CACHE_ENABLED=1`
- only when the caller sends `X-Owlmlx-Session-Id`
- only within the same `session_id` and `model_id`
- no implicit prefix matching
- no paged KV
- no continuous batching
- no subprocess cache-handle transport

The supported subprocess backend remains unchanged.

## 2. Runtime Behavior

When enabled, the native backend stores the cache object returned by
`mlx_lm.models.cache.make_prompt_cache(model)` for the explicit
`(session_id, model_id)` pair. A later request with the same pair reuses that
object through the existing `prompt_cache=` argument.

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

## 5. Status Surface

`GET /v1/runtime/session-kv-cache` returns the backend-exposed
`owlmlx.session_kv_cache` diagnostic payload when the backend supports it.
For non-native backends, the route returns an experimental disabled fallback
instead of fabricating capability support.

The same payload is also visible at:

```text
/v1/runtime/status -> backend.detail.session_kv_cache
```

## 6. Promotion Gate

The capability remains `experimental` until all of the following are true:

- 24h soak with `OWLMLX_SESSION_CACHE_ENABLED=1` and mixed 1-10 sessions
- settle-barrier failed reclaim count is zero
- active-memory drift is bounded against the cache-disabled baseline
- 4k+ multi-turn prompt TTFT p50 improves by at least 5x
- abort and unload paths leave no retained session cache entries

Until then, the default remains off.
