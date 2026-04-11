# Runtime-6 Anthropic Entrypoint

> Status: in progress
> Updated: 2026-04-11
> Scope: Anthropic-compatible entrypoints for owlcoda/owlcc cutover

## 1. Why Runtime-6 Exists

Runtime-5 completed OpenAI-style compatibility entrypoints and runtime-native
message handling.

That was not sufficient for the Owl ecosystem, because `owlcc` and `owlcoda`
primarily target Anthropic-shaped APIs:

- `POST /v1/messages`
- `POST /v1/messages/count_tokens`
- Anthropic streaming event semantics
- `x-api-key` + `anthropic-version` request shape

Runtime-6 therefore begins with a direct Anthropic-compatible serving surface.

## 2. What Is Now Implemented

`owlmlx` now provides:

- `POST /v1/messages`
  - non-streaming Anthropic message response shape
  - streaming SSE event sequence
- `POST /v1/messages/count_tokens`
  - estimated `input_tokens`

The streaming event sequence now includes:

- `message_start`
- `content_block_start`
- `content_block_delta`
- `content_block_stop`
- `message_delta`
- `message_stop`

This is the first `owlmlx` entrypoint directly shaped for `owlcoda` /
`owlcc`-style consumers.

## 3. Architecture Truth

Runtime-6 does not reintroduce the old server-layer prompt hack.

Anthropic input messages now flow through:

- HTTP request parsing
- `ChatTurn`
- `RuntimeKernel.generate_messages()`
- backend-native message handling
- tokenizer `apply_chat_template(...)` where available

That means Anthropic compatibility is built on the Runtime-5 message-native
path, not bolted on as a separate translation-only path.

## 4. Current Limits

Runtime-6 does not yet claim:

- tool_use output parity
- tool_result input parity
- thinking block parity
- full Claude / Anthropic beta surface
- direct owlcoda production cutover
- control-plane integration closure

This is an entrypoint seam, not final platform replacement.
