# Runtime-8 OwlCoda Cutover Verification

> Status: partial cutover verified
> Updated: 2026-04-11

## 1. Goal

Validate that `owlcoda` native/headless can consume `owlmlx /v1/messages` as a
real Anthropic-shaped runtime endpoint, not just a mocked schema surface.

This round intentionally targets the narrowest real path:

- `owlcoda` native/headless
- direct HTTP to `owlmlx /v1/messages`
- Anthropic streaming path
- one non-tool completion
- one minimal tool loop

It does **not** claim full `owlcoda` REPL cutover or production replacement.

## 2. Verification Setup

- Consumer: `owlcoda` native headless (`dist/native/headless.js`)
- Runtime: temporary `owlmlx` FastAPI server on `127.0.0.1:8041`
- Backend during verification: `FakeBackend`
- Loaded model id: `fake-a`

Verification commands were run against a real HTTP server, not `TestClient`.

## 3. What Was Verified

### 3.1 Direct native/headless non-tool request

`owlcoda` native headless successfully sent an Anthropic Messages request to
`owlmlx /v1/messages` and received a streamed assistant response.

Result:

- request path: `owlcoda native/headless -> owlmlx /v1/messages`
- outcome: success
- exit code: `0`
- iterations: `1`

### 3.2 Direct native/headless tool loop

`owlcoda` native headless successfully completed a two-iteration loop through
`owlmlx`:

1. assistant emitted `tool_use`
2. `owlcoda` executed the native tool
3. `owlcoda` sent `tool_result`
4. `owlmlx` returned final text

Result:

- outcome: success
- exit code: `0`
- iterations: `2`

This is the first verified `owlcoda` native/headless tool-loop cutover into
`owlmlx`.

## 4. Runtime-8A Compatibility Fixes

This cutover exposed two real Anthropic compatibility gaps in `owlmlx`.

### 4.1 Structured `system` blocks

`owlcoda` sends Anthropic-style structured `system` blocks with
`cache_control`.

Before this fix, `owlmlx` accepted `system` as a plain string only.

Fix:

- `AnthropicMessagesRequest.system` now accepts `str | list[AnthropicTextBlock]`
- `owlmlx` now extracts text from structured `system` blocks instead of
  depending on string coercion

### 4.2 Streaming `tool_use` input semantics

`owlcoda` native streaming parser reconstructs tool input from
`input_json_delta`.

Before this fix, `owlmlx` streaming `tool_use` emitted only
`content_block_start`, which caused `owlcoda` to see tool input as `{}`.

Fix:

- `owlmlx` now emits `content_block_delta` with `type=input_json_delta`
  for streamed `tool_use`

### 4.3 FakeBackend streaming delta semantics

`owlcoda` native parser expects token deltas, not cumulative text.

Before this fix, `FakeBackend` streamed cumulative text, which duplicated
content on the consumer side.

Fix:

- `FakeBackend.stream_generate()` now emits per-token deltas

## 5. What Runtime-8A Proves

- `owlcoda` native/headless can directly consume `owlmlx /v1/messages`
- `owlmlx` Anthropic streaming surface is now compatible with `owlcoda`'s
  native consumer for:
  - text streaming
  - `tool_use`
  - `tool_result` continuation
- the cutover path is no longer hypothetical

## 6. What Runtime-8A Does Not Yet Prove

- full `owlcoda --native` REPL cutover
- source-first mode cutover
- production backend reasoning quality
- full control-plane integration
- production replacement of the old platform

## 7. Next Runtime-8 Work

The next Runtime-8 step should expand from native/headless proof into the more
complete `owlcoda` runtime surfaces:

1. `owlcoda --native` REPL verification
2. stronger stateful multi-turn verification
3. first control-plane integration seam
4. final Runtime-8 cutover verdict
