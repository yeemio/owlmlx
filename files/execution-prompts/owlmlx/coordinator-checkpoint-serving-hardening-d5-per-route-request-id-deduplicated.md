# owlmlx Coordinator Checkpoint — Serving Hardening D-5 Per-Route Request-Id Deduplicated

## Verdict

- `serving_hardening_d5_per_route_request_id_deduplicated_middleware_sole_source`

The D-5 cleanup round is closed. The four compat routes on the real
owlmlx FastAPI app (`/v1/chat/completions`, `/v1/messages`,
`/v1/completions`, `/v1/openai/models`) no longer regenerate their own
`request_id = f"req_{uuid.uuid4().hex}"` locally; each route now reads
`request.state.request_id` — the value written by the D-1
`RequestIdMiddleware` once per inbound request.

Concretely: the middleware honors an inbound `x-request-id` header
verbatim, otherwise generates `req_<uuid4hex>` (32 hex chars) and
writes that single value to `request.state.request_id` plus the
outbound `x-request-id` response header. After D-5, the same value is
also the source of:

- the body `id` field on OpenAI compat error responses
  (`_compat_error_response`)
- the `request_id` keyword argument passed to
  `_anthropic_error_response`
- the `headers={"x-request-id": ...}` value attached to compat
  success responses (chat completions, completions, messages SSE)
- the `headers={"x-request-id": ...}` value attached to the
  `/v1/openai/models` GET response

There is **one** request id per request now, and it is the
middleware-set id. Inbound `x-request-id` round-trips into the body
of compat error responses verbatim — previously it survived only on
the outbound header.

The remaining hardening primitives (timeout, idempotent-load helper
class) are **NOT** wired in this round; each is a separate operator
decision in its own future D-* round.

## What This Checkpoint Is

A cleanup-wiring marker for one specific behavior change: the per-route
local `request_id` generation in `owlmlx/runtime/server.py` is removed
and replaced with `request.state.request_id` reads. Five
`f"req_{uuid.uuid4().hex}"` generation sites — actually four
generation sites in compat routes plus one in the `/v1/openai/models`
GET — collapse to a single source: D-1's `RequestIdMiddleware`.

It says: every compat route on the FastAPI app that `create_app(...)`
returns now has

- a `request: Request` parameter in its handler signature (FastAPI
  auto-injection — no parsing or middleware change required),
- a `request_id = request.state.request_id` line in place of the prior
  `request_id = f"req_{uuid.uuid4().hex}"` generation, and
- response shapes that are byte-identical to the prior round on the
  field set, but whose `request_id` value is now sourced from the
  middleware (and therefore is whatever the inbound caller supplied,
  if any).

It does **not** say:

- the runtime now has full distributed tracing or "production-grade"
  observability — D-5 is a single-source-of-truth cleanup, not a tracing
  feature
- structured logging emits the request id on every operation — that
  would belong to a D-3.1 logging round
- the `/v1/messages/count_tokens` route or any `/v1/runtime/*` route
  has been touched
- `/v1/generate/stream` has been touched (it never had a per-route
  generation site; the streaming error path emits no `request_id`
  field today)
- the C-4 scaffold's `IdempotentLoadHelper` is wired
- per-request timeouts are enforced
- `import uuid` is removed from `owlmlx/runtime/server.py` (it is still
  used for `completion_id` / `message_id` — different identifiers)

## What Is Now Frozen Exact

### Modified file: `owlmlx/runtime/server.py`

Five locations changed (by route handler), each a signature extension
plus a generation-line replacement:

#### 1. `/v1/chat/completions`

Handler signature:

```python
async def chat_completions(payload: ChatCompletionRequest, request: Request):
```

(prior: `async def chat_completions(payload: ChatCompletionRequest):` —
no `request: Request`).

Generation line:

```python
# D-5: request_id sourced from D-1 RequestIdMiddleware-set
# ``request.state.request_id`` rather than locally regenerated.
# The middleware honors inbound ``x-request-id`` and otherwise
# generates ``req_<uuid4hex>`` — that single source is the
# value compat responses now carry.
request_id = request.state.request_id
```

(prior: `request_id = f"req_{uuid.uuid4().hex}"`).

The `completion_id = f"chatcmpl-{uuid.uuid4().hex}"` line above it is
**unchanged** — that is a different identifier (the OpenAI
chat-completion id) and remains locally generated.

#### 2. `/v1/messages` (Anthropic compat)

Handler signature:

```python
async def anthropic_messages(payload: AnthropicMessagesRequest, request: Request):
```

(prior: no `request: Request`).

Generation line:

```python
# D-5: request_id sourced from RequestIdMiddleware (see D-1).
request_id = request.state.request_id
```

(prior: `request_id = f"req_{uuid.uuid4().hex}"`).

The `message_id = f"msg_{uuid.uuid4().hex[:24]}"` line above it is
**unchanged** — that is a different identifier (the Anthropic message
id, format-pinned by the Anthropic SDK) and remains locally generated.

#### 3. `/v1/completions`

Handler signature:

```python
async def completions(payload: CompletionRequest, request: Request):
```

(prior: no `request: Request`).

Generation line:

```python
# D-5: request_id sourced from RequestIdMiddleware (see D-1).
request_id = request.state.request_id
```

(prior: `request_id = f"req_{uuid.uuid4().hex}"`).

The `completion_id = f"cmpl-{uuid.uuid4().hex}"` line above it is
**unchanged** — that is a different identifier (the OpenAI
text-completion id) and remains locally generated.

#### 4. `/v1/openai/models`

Handler signature:

```python
def openai_models(request: Request):
```

(prior: `def openai_models():` — no `request: Request`).

Generation line:

```python
# D-5: request_id sourced from RequestIdMiddleware (see D-1).
request_id = request.state.request_id
```

(prior: `request_id = f"req_{uuid.uuid4().hex}"`).

#### 5. (sentinel — no fifth generation site)

A `grep -n "request_id = f\"req_" owlmlx/runtime/server.py` after the
edits returns **zero** results. The "five locations" framing in the
round prompt mapped onto four generation sites in handler bodies plus
the four signature extensions — the round prompt-and-spec reading was
explicit that line numbers were estimates and grep was the source of
truth. No additional `f"req_{uuid.uuid4().hex}"` site exists in
`server.py`. The `_request_id_from_request(...)` helper added in D-3
already reads `request.state.request_id` and is the canonical
adapter for the D-3 native error envelope path; D-5 brings the compat
routes onto the same canonical source.

### Helpers and surfaces NOT changed

- `_compat_error_response(request_id=, message=, code=, status_code=)`
  function body — unchanged. The function still places `request_id` in
  the body's `id` field and on the `x-request-id` response header.
  Only the **value** flowing into the `request_id=` kwarg has changed
  (now from middleware, previously a fresh local uuid).
- `_anthropic_error_response(request_id=, message=, code=, status_code=)`
  function body — unchanged. Anthropic envelope body does not carry
  `request_id` (Anthropic SDK convention); only the
  `x-request-id` response header is set, and it is now the
  middleware-set value.
- D-1 `app.add_middleware(RequestIdMiddleware)` registration line —
  unchanged.
- D-2 graceful-shutdown registration block — unchanged.
- D-3 unified-error-envelope wiring block
  (`error_envelope_builder`, `_unhandled_exception_handler`,
  `app.add_exception_handler(...)`,
  `_NATIVE_ERROR_CODE_TO_HTTP_STATUS`,
  `_native_runtime_response(...)`) — unchanged.
- D-4 `/metrics` route — unchanged.
- All `/v1/load` / `/v1/generate` / `/v1/unload` / `/v1/generate/stream`
  / `/v1/messages/count_tokens` / `/v1/models` / `/v1/runtime/*`
  handlers — unchanged.
- Top-level `import uuid` — **kept** (still used for `completion_id`
  / `message_id`).

Diff scope: roughly `+18 -8` lines on `server.py` (four signature
expansions and four generation-line replacements; comments add a few
lines per site).

### Compat Response Contract — Frozen

| Surface | Where `request_id` is rendered | Value source after D-5 |
| ------- | ------------------------------ | ---------------------- |
| `/v1/chat/completions` (success) | response header `x-request-id` | `request.state.request_id` |
| `/v1/chat/completions` (error compat envelope) | header + body `id` | `request.state.request_id` |
| `/v1/messages` (success) | response header `x-request-id` | `request.state.request_id` |
| `/v1/messages` (error Anthropic envelope) | response header `x-request-id` (body has no `request_id`) | `request.state.request_id` |
| `/v1/completions` (success) | response header `x-request-id` | `request.state.request_id` |
| `/v1/completions` (error compat envelope) | header + body `id` | `request.state.request_id` |
| `/v1/openai/models` (GET success) | response header `x-request-id` | `request.state.request_id` |
| Native lifecycle (D-3) | header + envelope `request_id` field | `request.state.request_id` (already since D-3) |

Inbound `x-request-id` round-trips verbatim across **all** rows of the
table; auto-generation falls back to `req_<uuid4hex>` (32 hex chars,
per the D-1 `RequestIdMiddleware` contract).

### New file: `tests/test_serving_hardening_request_id_dedup.py`

Six integration tests using `fastapi.testclient.TestClient` against
the real `create_app()`-constructed app:

- `test_inbound_request_id_propagates_to_chat_completions_response_id`
  — POST `/v1/chat/completions` with an inbound `x-request-id:
  req_test-inbound-123` and an unknown model triggers the
  `model_not_loaded` compat error path. The response body's `id` and
  the response's `x-request-id` header both equal the inbound id —
  they no longer diverge.
- `test_inbound_request_id_propagates_to_messages_response_id` — same
  for `/v1/messages`. Anthropic body shape does not carry `request_id`,
  so the test pins the header round-trip only.
- `test_inbound_request_id_propagates_to_completions_response_id` —
  same for `/v1/completions`. Body `id` and header round-trip the
  inbound value.
- `test_no_inbound_id_uses_middleware_generated_id_in_compat_response`
  — POST `/v1/chat/completions` with no inbound header. The
  middleware autogenerates `req_<uuid4hex>`. The response body's `id`
  equals the response's `x-request-id` header — single source proven
  on the autogen path as well.
- `test_compat_error_response_carries_inbound_request_id` — POST
  `/v1/completions` with an inbound id and an unknown model. Compat
  error envelope body's `id` equals the inbound id.
- `test_openai_models_route_uses_middleware_request_id` — GET
  `/v1/openai/models` with an inbound id. Outbound header echoes
  inbound (happy-path 200).

No uvicorn process is started. No model is loaded. The default
`FakeBackend` is used; calls against an unloaded model surface
`model_not_loaded` from the kernel, which the compat handlers map
through `_compat_error_response` / `_anthropic_error_response`. The
C-4 scaffold tests (`test_serving_hardening.py`), the D-1 wiring tests
(`test_serving_hardening_wired.py`), the D-2 wiring tests
(`test_serving_hardening_graceful_shutdown_wired.py`), the D-3 wiring
tests (`test_serving_hardening_error_envelope_wired.py`), and the D-4
wiring tests (`test_serving_hardening_metrics_wired.py`) are
untouched and remain passing.

### Round prompt: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d5-per-route-request-id-deduplication.md`

Records the executor-phase discipline (four signature expansions, four
generation-line replacements; no compat-error-helper modification; no
D-1 / D-2 / D-3 / D-4 modification; no doc modification; `import uuid`
NOT removed because `completion_id` / `message_id` still use it;
`TestClient` only) and the four-deliverable contract.

## Test Counts

The combined sweep
`.venv/bin/python -m pytest tests/test_serving_hardening.py
tests/test_serving_hardening_wired.py
tests/test_serving_hardening_graceful_shutdown_wired.py
tests/test_serving_hardening_error_envelope_wired.py
tests/test_serving_hardening_metrics_wired.py
tests/test_serving_hardening_request_id_dedup.py -q`
covers:

- `tests/test_serving_hardening.py` — 23 unit tests (C-4 scaffold,
  unchanged)
- `tests/test_serving_hardening_wired.py` — 5 integration tests
  (D-1, unchanged)
- `tests/test_serving_hardening_graceful_shutdown_wired.py` — 5
  integration tests (D-2, unchanged)
- `tests/test_serving_hardening_error_envelope_wired.py` — 9
  integration tests (D-3, unchanged)
- `tests/test_serving_hardening_metrics_wired.py` — 7 integration
  tests (D-4, unchanged)
- `tests/test_serving_hardening_request_id_dedup.py` — 6 integration
  tests (D-5, new)

Total D-5 sweep: 55 tests across the six files (the D-1..D-4 49
remain passing; the new D-5 file adds 6).

## What This Checkpoint Closes

- the per-route ad-hoc `request_id = f"req_{uuid.uuid4().hex}"`
  generation in `/v1/chat/completions`, `/v1/messages`,
  `/v1/completions`, and `/v1/openai/models` is removed; each handler
  now reads `request.state.request_id`
- the inbound `x-request-id` header round-trips into the **body** of
  the compat OpenAI / completions error envelopes (the body's `id`
  field), not just the response header
- the loop request id → outbound header → response body's `id` (where
  the body shape has an id slot) is closed with a single
  middleware-set id; before D-5 the body and header could disagree on
  which id they carried
- the round prompt + checkpoint pair is landed for audit

## What This Checkpoint Does Not Claim

- the runtime now has distributed tracing — D-5 is a single-source-of-
  truth cleanup, not a tracing feature; no W3C Trace Context, no
  parent_span_id propagation, no span emission
- structured logging emits `request_id` on every operation — there is
  no logging change in this round; that belongs to a future D-3.1
- the `/v1/messages/count_tokens`, `/v1/generate/stream`,
  `/v1/runtime/*`, `/v1/load`, `/v1/generate`, `/v1/unload`, `/v1/models`,
  `/healthz`, or `/metrics` route was modified — none were
- the streaming SSE error event for `/v1/generate/stream` carries
  `request_id` — it does not, that remains a separate streaming-
  envelope wiring round
- per-route `completion_id` / `message_id` generation has been changed
  — those are different identifiers and remain locally generated
- the C-4 scaffold's `IdempotentLoadHelper` class integration is wired
- per-request timeouts are enforced
- `import uuid` is removed from `server.py` — it is still used by
  `completion_id` / `message_id`
- the response body shape on any route has changed — only the **value**
  of the `request_id` / `id` slot has changed source; the slot itself
  is in the same place with the same type
- Line 4 of the seven-line architectural assessment has been promoted
  from `partial` to a higher posture — D-5 is one of several
  remaining wiring rounds whose collective completion is the
  precondition for any posture promotion
- `docs/source-of-truth/serving-hardening-architecture.md` has been
  refreshed to reflect this change — that refresh is a separate
  doc-cleanup round
- the capability matrix has any row promoted / demoted (it does not)

## Side Effects

### Zero observable behavior change for clients on the autogen path

When a client sends no inbound `x-request-id`, the middleware
generates `req_<uuid4hex>` (32 hex chars). Before D-5 the response
body's `id` field and the response header's `x-request-id` value were
both `req_<uuid4hex>` but with **different** uuid values (one from
middleware, one from handler). After D-5 they share the same uuid
value. The body shape is unchanged, the header shape is unchanged,
and the format is unchanged — only the multi-source generation
collapses to single-source. Clients that parsed either field
independently see no change.

### Visible behavior change for clients on the inbound-id path

When a client sends `x-request-id: <inbound>`, the response header
already echoed `<inbound>` (D-1 contract). After D-5, the response
body's `id` field also reflects `<inbound>` on the compat OpenAI /
completions error envelope. Clients that previously assumed the body
`id` was a fresh autogen value should re-key on the response header
or accept that the body now mirrors their own inbound id. This is
explicitly the cleanup the round delivers; any client that depended
on the old multi-source divergence was depending on a bug.

### Other side effects

- `owlmlx/runtime/server.py` is the only existing source file
  modified in this round
- no documentation file is modified
- no test file other than the one new test is added
- `pyproject.toml`, `uv.lock`, `.python-version`, `conftest.py`,
  `README.md`, `tests/test_serving_hardening.py`,
  `tests/test_serving_hardening_wired.py`,
  `tests/test_serving_hardening_graceful_shutdown_wired.py`,
  `tests/test_serving_hardening_error_envelope_wired.py`,
  `tests/test_serving_hardening_metrics_wired.py`, and
  `owlmlx/runtime/serving_hardening.py` are unmodified
- the existing dirty tree on `main` (Gemma MTP probe, runtime monitor
  changes, heavy-weight repeatability, native MLX adapter
  modifications, etc.) is untouched
- no new dependency is introduced; the round is a pure refactor of
  existing flow paths

## Notable Implementation Choices

- **`import uuid` is kept.** A `grep -n "uuid\\." owlmlx/runtime/server.py`
  after the edits shows three remaining usages: `completion_id =
  f"chatcmpl-{uuid.uuid4().hex}"` (chat completions), `message_id =
  f"msg_{uuid.uuid4().hex[:24]}"` (Anthropic messages), and
  `completion_id = f"cmpl-{uuid.uuid4().hex}"` (text completions).
  These are different identifiers governed by the OpenAI / Anthropic
  SDK contracts and are out of scope for D-5. Removing the `import
  uuid` would break them.

- **Each compat route is now a `(payload: ..., request: Request)`
  signature.** FastAPI auto-injects `Request` whenever a handler
  parameter declares the `Request` type — there is no manual
  middleware extraction or `await request._receive(...)` involved.
  The signature change adds zero parsing cost; the framework already
  has the `Request` instance in scope from the middleware chain.

- **`_compat_error_response` and `_anthropic_error_response`
  signatures are unchanged.** Both still take a `request_id: str`
  keyword argument. D-5 is purely a change at the **call site**: the
  argument is now `request.state.request_id` instead of a
  freshly-generated uuid string. Helper internals stay frozen so
  later doc / test rounds can pin them without churn.

- **Body shape pin for compat OpenAI error envelope.**
  `_compat_error_response` writes `{"id": request_id, "object":
  "error", "error": {"message": ..., "code": ...}}`. The `id` field
  is therefore the canonical place where the inbound request id now
  lands in the OpenAI compat error response body. Tests pin this.

- **Anthropic error envelope body has no `request_id` slot.**
  `_anthropic_error_response` writes `{"type": "error", "error":
  {"type": code, "message": message}}` and only the response
  `x-request-id` header carries the request id. This matches the
  Anthropic SDK convention. The D-5 test for `/v1/messages` therefore
  pins the header round-trip only.

- **`/v1/openai/models` is included even though it is a GET.** The
  route also generated its own `req_<uuid4hex>` locally before D-5;
  the cleanup is symmetric to the POST routes. The route returns
  the model list and an `x-request-id` header that is now sourced
  from the middleware.

- **No streaming error path was changed.** `/v1/generate/stream` and
  the SSE source inside `/v1/chat/completions` / `/v1/messages` /
  `/v1/completions` do not contain a `request_id` slot in their
  emitted `data:` frames today; emitting one is its own deferred
  streaming-envelope wiring round, not D-5.

- **Defensive read of `request.state.request_id` is unnecessary.** The
  D-1 `RequestIdMiddleware.dispatch` contract guarantees
  `request.state.request_id` is a non-empty string for every
  request. The compat handlers therefore read it directly without
  fallback. The D-3 `_request_id_from_request(...)` helper does
  defensive reading only because the unhandled-exception handler
  may run before a route handler has executed; that is a different
  invariant.

## Capability Matrix State

`docs/source-of-truth/native-mlx-backend-capability-matrix.md` is
**unmodified** in this round. The matrix records MLX backend
capability entry points; per-route request-id deduplication does not
fit its vocabulary, and serving-surface ownership is governed by
`docs/source-of-truth/serving-hardening-architecture.md` plus the
existing `single-host-orchestration-architecture.md`. No row is
promoted. No row is demoted.

## Seven-line Architectural Assessment

Line 4 — Serving surface (`partial`) remains `partial`. D-5 is one of
several remaining wiring rounds whose collective completion is the
precondition for moving Line 4 to a higher posture. Lines 1, 2, 3, 5,
6, 7 are unchanged in this round.

## Next Authorized Round

Two parallel candidates, both deliberate single-item rounds:

### Path D-6 (recommended): Per-Request Timeout + Client-Disconnect Detection Wiring

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d6-timeout-and-disconnect-wiring.md`
  (to be authored)
- attach `RequestTimeoutHelper` + `RequestDisconnectedError` (both
  defined in the C-4 scaffold) to selected native routes; map
  disconnect to HTTP 499 (per the C-4 scaffold's static mapping) via
  the unified envelope
- evidence: tests that assert (a) a slow handler is interrupted by
  the timeout policy, and (b) a synthetic client disconnect raises
  `RequestDisconnectedError` and is converted to a 499 + unified
  envelope
- evidence-language: "RequestTimeoutPolicy enforced on selected native
  routes; client disconnect mapped to 499 + unified envelope"

### Path D-7 (parallel): Idempotent-Load Helper Class Integration

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d7-idempotent-load-helper-class-integration.md`
  (to be authored)
- promote the inlined `model_already_loaded` branch in
  `_native_runtime_response` to use the full `IdempotentLoadHelper`
  class, exposing the `IdempotentLoadOutcome.to_response_body()`
  shape on the `/v1/load` success-with-detail path
- evidence: a wired test asserting the `/v1/load`
  success-with-detail body matches `IdempotentLoadOutcome.to_response_body()`
  exactly when the same `model_id` is loaded twice

The remaining hardening (streaming-error envelope is its own deferred
round; structured logging on the unhandled-exception path is the
deferred D-3.1) each warrant their own dedicated wiring round so that
operator review is per-item.

## Independent / Deferrable Parallel Lanes

- **C-1 cache_manager scaffold** — moves Line 5; landscape map exists
- **C-2 repeatability harness** — moves Line 6; landscape map exists
- **C-3 memory_actuator** — moves Line 3; landscape map exists
- **B-2** sibling candidate admissibility (Qwen3.6-27B / gemma-4-31B-it)
- **B-4** cooperative cancellation real-stream evidence

I recommend the **next round be D-6** because timeout + disconnect is
the last C-4 primitive without a wiring round; D-7 is a strong second
because the helper class promotion is a small natural follow-on to
D-3 and D-5.
