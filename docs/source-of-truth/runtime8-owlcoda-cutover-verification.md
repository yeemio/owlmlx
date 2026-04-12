# Runtime-8 OwlCoda Cutover Verification

> Status: Runtime-8 complete
> Updated: 2026-04-12

## 1. Goal

Validate that `owlcoda` native/headless can consume `owlmlx /v1/messages` as a
real Anthropic-shaped runtime endpoint, not just a mocked schema surface.

Runtime-8 was split into two execution steps:

- Runtime-8A: `owlcoda` native/headless direct cutover
- Runtime-8B: `owlcoda --native` REPL cutover + state/recovery proof + first control-plane seam

The work intentionally starts from the narrowest real path and then expands.

Runtime-8A targeted:

- `owlcoda` native/headless
- direct HTTP to `owlmlx /v1/messages`
- Anthropic streaming path
- one non-tool completion
- one minimal tool loop

It did **not** claim full `owlcoda` REPL cutover or production replacement.

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

## 5. Runtime-8B Verification

### 5.1 `owlcoda --native` REPL cutover

`owlcoda` native REPL was pointed directly at a temporary `owlmlx` FastAPI
server on `127.0.0.1:8041` using a real PTY session.

Verified paths:

- non-tool turn completed successfully
- tool loop completed successfully:
  1. assistant emitted `tool_use`
  2. REPL executed the native tool
  3. REPL sent `tool_result`
  4. `owlmlx` returned final text

Result:

- outcome: success
- REPL session exited cleanly
- tool loop iterations: `2`

This is the first verified `owlcoda --native` REPL cutover into `owlmlx`.

### 5.2 Stateful multi-turn and recovery verification

Runtime-8B then verified that the REPL cutover was not single-turn only.

An isolated `HOME` / `OWLCODA_HOME` was used so that session persistence could
be inspected without touching the user's real session store.

Verification flow:

1. start a fresh `owlcoda --native` REPL against `owlmlx`
2. complete one non-tool turn
3. inspect and record the session id
4. exit the REPL cleanly
5. start a second REPL with `resumeSession=<same id>`
6. verify the restored conversation state
7. run a resumed tool loop:
   - `tool_use`
   - tool execution
   - `tool_result`
   - final assistant continuation

Verified facts:

- resumed session id remained stable across both REPL runs
- resumed REPL started with the prior turn history already present
- post-resume tool loop completed successfully
- persisted session file contained the expected sequence:
  - initial user turn
  - initial assistant turn
  - resumed user turn
  - assistant `tool_use`
  - user `tool_result`
  - final assistant continuation

Result:

- session id: stable
- turns before resume: `2`
- turns after resumed tool loop: `6`
- outcome: success
This is the first verified state/recovery proof for direct `owlcoda` REPL
consumption of `owlmlx`.

### 5.3 Runtime-8B protocol cleanup

Runtime-8B exposed one protocol cleanliness issue in `owlmlx` streaming:

- streamed `tool_use` previously emitted an empty `text` block before the real
  `tool_use` block

This did not block `owlcoda`, because the consumer tolerates empty text blocks,
but it was still wrong for a clean Anthropic event sequence.

Fix:

- `owlmlx` now starts a streamed text block lazily on first token
- streamed `tool_use` no longer emits an empty preceding text block
- regression is covered in `tests/test_runtime_server.py`

### 5.4 First control-plane seam

`owlcoda` previously treated `/v1/models` as the only runtime reachability
surface in native REPL preflight and `/doctor`.

That was too narrow for direct `owlmlx` runtime usage, because `owlmlx`
exposes stronger runtime truth at `/v1/runtime/status`.

Fix:

- `owlcoda` now probes runtime surfaces in this order:
  1. `/v1/runtime/status`
  2. `/v1/models`
  3. `/healthz`
- REPL preflight now accepts direct `owlmlx` runtime status
- `owlcoda /doctor` now reports direct runtime readiness instead of assuming a
  router-only topology

This is the first verified control-plane seam between `owlcoda` and `owlmlx`.

## 6. What Runtime-8 Proves

- `owlcoda` native/headless can directly consume `owlmlx /v1/messages`
- `owlcoda --native` REPL can directly consume `owlmlx /v1/messages`
- `owlcoda --native` REPL can resume a persisted session and continue through a
  resumed tool loop against `owlmlx`
- `owlmlx` Anthropic streaming surface is compatible with `owlcoda`'s
  native consumer for:
  - text streaming
  - `tool_use`
  - `tool_result` continuation
- `owlcoda` control-plane checks can now recognize direct `owlmlx` runtime
  surfaces instead of assuming `/v1/models` only
- the cutover path is no longer hypothetical

## 7. What Runtime-8 Does Not Yet Prove

- source-first mode cutover
- production backend reasoning quality
- full control-plane integration
- production replacement of the old platform

## 8. Runtime-8 Status

- Runtime-8A: complete
- Runtime-8B: complete
- Runtime-8 overall: complete

## 9. Next Runtime-8 Work

Runtime-8 is the point where `owlmlx` stops being only an internally verified
runtime and becomes a runtime directly consumed by both Owl ecosystem clients:

- Runtime-7: `owlcc`
- Runtime-8: `owlcoda`

The next phase should move from verified cutover into deeper integration and
replacement work:

1. source-first parity and cutover judgment
2. deeper control-plane integration
3. production-backend validation under OwlCoda consumption
4. replacement verdicts instead of seam-only proof
