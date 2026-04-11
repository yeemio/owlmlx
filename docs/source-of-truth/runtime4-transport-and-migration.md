# Runtime-4 Transport And Migration Seam

> Status: authoritative
> Updated: 2026-04-11
> Scope: Runtime-4 transport semantics hardening and platform-facing API seam

## 1. Purpose

Runtime-4 starts where Runtime-3 ended:

- Runtime-3 proved restart surface, serialized serving, real streaming, and
  same-model comparison truth
- Runtime-4 begins the move toward a more deployable serving runtime

Runtime-4 adds:

- OpenAI-style `chat/completions` compatibility surface
- OpenAI-style model discovery seam
- explicit SSE transport for streaming compatibility
- backend reliability-path consolidation for persistent child sessions

## 2. New Surface

New endpoint:

- `POST /v1/chat/completions`
- `GET /v1/openai/models`

Supported modes:

| Mode | Transport | Meaning |
|---|---|---|
| non-stream | JSON | minimal OpenAI-style chat completion response |
| stream | SSE | `text/event-stream` with `data:` chunks and terminal `[DONE]` |

Model discovery:

| Path | Meaning |
|---|---|
| `GET /v1/openai/models` | migration seam exposing currently loaded models in OpenAI-style list shape |

This is a migration seam, not a full OpenAI server.

## 3. Scope Of Compatibility

Runtime-4 currently supports:

- `model`
- `messages`
- `max_tokens`
- `temperature`
- `stream`
- request-id response headers on compatibility endpoints
- OpenAI-style HTTP status/error object on `chat/completions` failures

Runtime-4 does not yet claim support for:

- tools / function calling
- logprobs
- response-format enforcement
- multi-choice sampling
- full OpenAI error object parity

## 4. Reliability Consolidation

`MlxLmSubprocessBackend` now centralizes dead-child / missing-session recovery
through one shared `_ensure_session()` path.

This reduces duplication between:

- `generate()`
- `stream_generate()`

Runtime-4 truth:

- missing session and dead child checks must not diverge by operation type
- recovery policy belongs to the backend lifecycle seam, not ad hoc per method

## 5. Why This Matters

This is the first direct platform-facing migration seam in owlmlx runtime:

- upper layers can target a familiar `chat/completions` shape
- upper layers can discover loaded models through a familiar list shape
- streaming transport is no longer only owlmlx-specific NDJSON
- migration can begin without forcing full platform rewrite on day one

## 6. Non-Claims

This document does not claim:

- full OpenAI API parity
- production auth / rate limiting / tracing
- tools / function calling support
- platform migration is complete
- Runtime-5 is complete
