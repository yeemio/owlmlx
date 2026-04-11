# Runtime-6 Anthropic Entrypoint

> Status: complete
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

Runtime-6 now also accepts additional Anthropic input block shapes on
`POST /v1/messages`:

- text blocks
- `tool_result` blocks
- assistant-side historical `tool_use` blocks

These are currently flattened into runtime-native message text before backend
execution. This is an input-side cutover seam, not a claim of full tool
protocol parity.

Runtime-6 now also has a minimal output-side `tool_use` seam:

- Anthropic requests may include `tools`
- the runtime surface can now return `tool_use` blocks from `/v1/messages`
- Anthropic streaming can now emit `tool_use`-shaped `content_block_start`
  followed by `message_delta.stop_reason = tool_use`

This currently proves protocol shape, not full backend tool reasoning parity.

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

- full tool_use output parity across real backends
- true tool_result semantic execution parity
- thinking block parity
- full Claude / Anthropic beta surface
- direct owlcoda production cutover
- control-plane integration closure

This is an entrypoint seam, not final platform replacement.

Runtime-7 then extended this from protocol seam to first real `owlcc` cutover
verification.
