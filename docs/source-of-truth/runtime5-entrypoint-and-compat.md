# Runtime-5 Entrypoint And Compat Closure

> Status: complete
> Updated: 2026-04-11
> Scope: Runtime-5 entrypoint handling, fuller compatibility semantics, and migration-closure groundwork

## 1. Position

Runtime-4 established the first migration seam:

- `POST /v1/chat/completions`
- `GET /v1/openai/models`
- SSE compatibility streaming

Runtime-5 moves beyond a thin seam. The key transition is:

- chat/message handling is no longer assembled only at the HTTP server edge
- structured messages now pass through `RuntimeKernel` and backend adapters
- backend execution layers own message rendering / chat templating decisions
- compat surface expands to include `POST /v1/completions`

This is still not full OpenAI parity. It is the first stage where upper layers
can treat `owlmlx` as a serious runtime entrypoint rather than a demo-shaped
compat wrapper.

## 2. What Runtime-5 Adds

### 2.1 Structured Message Path

Structured chat messages now flow through:

- `server.py` request parsing
- `RuntimeKernel.generate_messages()`
- `RuntimeKernel.generate_stream_messages()`
- backend-native `generate_messages()` / `stream_generate_messages()`

This replaces the earlier Runtime-4 pattern where the HTTP server flattened
messages into a prompt string before entering runtime logic.

### 2.2 Backend-Owned Chat Rendering

`FakeBackend` now uses fallback role/content rendering for tests.

`MlxLmBackend` and `MlxLmSubprocessBackend` now own message rendering at the
backend layer. The child runner prefers tokenizer-native
`apply_chat_template(..., tokenize=False, add_generation_prompt=True)` when it
exists, and falls back only when tokenizer templating is unavailable.

This is the correct architectural boundary:

- HTTP layer owns transport
- RuntimeKernel owns dispatch and gate discipline
- backend/tokenizer layer owns prompt shaping for chat messages

### 2.3 Fuller Compat Surface

Runtime-5 compatibility surface now includes:

- `POST /v1/chat/completions`
- `POST /v1/completions`
- `GET /v1/openai/models`

Both chat and text completion endpoints support:

- non-stream JSON responses
- streaming `text/event-stream`
- structured error objects
- request-id headers

## 3. Why This Matters

Runtime-4 proved that a migration seam existed.

Runtime-5 proves that the seam is no longer purely server-shaped:

- runtime can accept structured message input
- backend layers can apply model-native chat templating
- migration can target both chat-style and prompt-style entrypoints

That is the first point where upper layers can begin replacing old entrypoints
without forcing all prompt construction policy to live outside `owlmlx`.

## 4. Verified Runtime-5 Truth

- `ChatTurn` is now a runtime-native contract.
- `RuntimeKernel` now has chat-native generate and stream methods.
- `MlxLmSubprocessBackend` supports persistent-child chat/message generation.
- `mlx_lm_runner.py` supports `generate_messages` and
  `stream_generate_messages`.
- `POST /v1/completions` now exists as a second compatibility entrypoint.
- server tests cover:
  - chat non-stream
  - chat stream SSE
  - completions non-stream
  - completions stream SSE
- subprocess backend tests cover:
  - persistent child `generate_messages`
  - persistent child `stream_generate_messages`

## 5. Non-Claims

Runtime-5 does not claim:

- full OpenAI API parity
- tools / function calling
- JSON schema constrained decoding
- full responses API parity
- production control-plane integration
- platform migration closure

Those remain future work.

## 6. Runtime-5 Outcome

Runtime-5 is complete.

`owlmlx` has now progressed from:

- Runtime-0: executable kernel
- Runtime-1: real local model isolation
- Runtime-2: persistent child lifecycle
- Runtime-3: streaming + benchmark comparison
- Runtime-4: migration seam
- Runtime-5: runtime-native message handling + fuller compat entrypoints

The next phase should move from entrypoint compatibility into deeper runtime
replacement and control-plane integration.
