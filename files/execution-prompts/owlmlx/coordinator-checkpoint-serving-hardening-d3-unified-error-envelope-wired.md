# owlmlx Coordinator Checkpoint — Serving Hardening D-3 Unified Error Envelope Wired

## Verdict

- `serving_hardening_d3_unified_error_envelope_wired_native_namespace`

The D-3 wiring round is closed. The C-4 scaffold's
`UnifiedErrorEnvelope` plus `ErrorEnvelopeBuilder` are now installed
on the real owlmlx FastAPI app constructed by
`owlmlx.runtime.server.create_app(...)` along two surfaces:

1. **Generic `Exception` handler** registered via
   `app.add_exception_handler(Exception, _unhandled_exception_handler)`.
   Any unhandled exception is rendered as a unified error envelope
   with HTTP 500 and **no leak** of the raw exception class name or
   message; the `request_id` is read from
   `request.state.request_id` (set by the D-1 middleware) when
   present.
2. **Native lifecycle route promotion**. The three native lifecycle
   routes — `/v1/load`, `/v1/generate`, `/v1/unload` — now map a
   typed `ok=False` `error_code` to a proper HTTP status (400 / 404 /
   409 / 500) via the `_native_runtime_response(...)` adapter. The
   `model_already_loaded` case for `/v1/load` is treated as
   success-with-detail (HTTP 200) per the C-4 scaffold's
   idempotent-load policy. Success bodies are unchanged.

The compat namespace (`/v1/chat/completions`, `/v1/messages`,
`/v1/completions`, OpenAI / Anthropic SDK surfaces) is **untouched**.
The OpenAI SDK and Anthropic SDK callers continue to receive their
existing error shapes via `_compat_error_response` /
`_anthropic_error_response`.

The remaining three C-4 hardening primitives (timeout, metrics
endpoint, idempotent-load helper class) and per-route id deduplication
are **NOT** wired in this round; each is a separate operator decision
in its own future D-* round.

## What This Checkpoint Is

A wiring marker for one specific primitive pair (`UnifiedErrorEnvelope`
+ `ErrorEnvelopeBuilder`). It says: the FastAPI app that
`create_app(...)` returns now has

- a generic `Exception` handler that produces the unified envelope on
  every unhandled exception, and
- a native lifecycle route adapter that maps typed `error_code`
  values to proper HTTP status codes and renders the unified
  envelope on `ok=False` paths,

and an integration test file backs both behaviors end-to-end against
the real app surface.

It does **not** say:

- the entire serving surface uses the unified envelope (compat routes
  do not — by design)
- `/v1/generate/stream` mid-stream errors use the envelope (NDJSON
  stream error wiring is a separate round)
- FastAPI's own 422 request-validation responses use the envelope
  (the validator runs before any route body and returns FastAPI's
  built-in shape; envelope translation for 422 is a deferred round)
- request timeouts are enforced
- a `/metrics` route exists
- `/v1/load` exposes the full `IdempotentLoadHelper` surface — the
  wiring inlines just the `model_already_loaded` → success-with-detail
  branch via `_native_runtime_response(idempotent_already_loaded=True)`
- the existing per-route ad-hoc `req_<uuid4hex>` generation in the
  compat routes has been removed (D-1.1's responsibility)

## What Is Now Frozen Exact

### Modified file: `owlmlx/runtime/server.py`

Three additions:

1. The relative-import line is rewritten from
   ```python
   from .serving_hardening import GracefulShutdown, GracefulShutdownConfig, RequestIdMiddleware
   ```
   to a multi-line import:
   ```python
   from .serving_hardening import (
       ErrorEnvelopeBuilder,
       GracefulShutdown,
       GracefulShutdownConfig,
       RequestIdMiddleware,
       UnifiedErrorEnvelope,
   )
   ```

2. Inside `create_app(...)`, immediately after the existing line
   `app.router.on_shutdown.append(_graceful_shutdown_drain)`, a new
   D-3 wiring block is inserted that:
   - constructs `error_envelope_builder = ErrorEnvelopeBuilder(namespace="owlmlx_native")`
   - defines `_request_id_from_request(request) -> str | None`,
     reading `request.state.request_id` defensively
   - defines async `_unhandled_exception_handler(request, exc)`
     which builds an envelope via
     `error_envelope_builder.from_unexpected(...)` and returns a
     `JSONResponse(status_code=envelope.http_status,
     content=envelope.to_response_body())`; falls back to a literal
     dict + status 500 if the builder itself somehow fails (the
     handler MUST NEVER raise)
   - calls `app.add_exception_handler(Exception, _unhandled_exception_handler)`
   - defines the native error_code -> HTTP status mapping
     `_NATIVE_ERROR_CODE_TO_HTTP_STATUS` (see matrix below)
   - defines `_native_runtime_response(result, *, request,
     success_status=200, idempotent_already_loaded=False)` — the
     adapter used by the three native lifecycle routes

3. Three native route handlers gain a `request: Request` parameter
   and route their return through `_native_runtime_response(...)`:
   - `/v1/load` — `idempotent_already_loaded=True`
   - `/v1/generate` — default (no idempotent special case)
   - `/v1/unload` — default

The `_compat_error_response` / `_anthropic_error_response` functions
and all their callers in the compat routes are **untouched**. No
`/v1/runtime/*` route is touched. `/v1/generate/stream` is
**untouched**. The D-1 `RequestIdMiddleware` registration line is
untouched. The D-2 graceful-shutdown registration block is untouched.

Diff summary: roughly `+110 -10` lines on `server.py` (one import
rewritten, ~95 lines added for the D-3 wiring block, three route
handlers retouched to take `Request` and return via the adapter).

### HTTP Status Matrix — Native Namespace (Frozen)

| Surface                                     | Before D-3 | After D-3 |
| ------------------------------------------- | ---------- | --------- |
| `POST /v1/load` (`ok=True`)                 | 200        | 200       |
| `POST /v1/load` (`model_already_loaded`)    | 200 + `ok=false` body | 200 (success-with-detail; idempotent) |
| `POST /v1/load` (`invalid_request`)         | 200 + `ok=false` body | 400 + unified envelope |
| `POST /v1/load` (`memory_budget_exceeded`)  | 200 + `ok=false` body | 400 + unified envelope |
| `POST /v1/load` (`unsupported_model_family`)| 200 + `ok=false` body | 400 + unified envelope |
| `POST /v1/load` (`backend_error`)           | 200 + `ok=false` body | 500 + unified envelope |
| `POST /v1/generate` (`ok=True`)             | 200        | 200       |
| `POST /v1/generate` (`model_not_loaded`)    | 200 + `ok=false` body | 404 + unified envelope |
| `POST /v1/generate` (`backend_error`)       | 200 + `ok=false` body | 500 + unified envelope |
| `POST /v1/unload` (`ok=True`)               | 200        | 200       |
| `POST /v1/unload` (`model_not_loaded`)      | 200 + `ok=false` body | 404 + unified envelope |
| `POST /v1/unload` (`model_pinned`)          | 200 + `ok=false` body | 409 + unified envelope |
| `POST /v1/unload` (`backend_error`)         | 200 + `ok=false` body | 500 + unified envelope |
| Any unhandled exception (any route)         | uvicorn / FastAPI default 500 + raw traceback shape | 500 + unified envelope (no leak) |
| `POST /v1/chat/completions` (any error)     | `_compat_error_response` shape | **unchanged** — `_compat_error_response` shape |
| `POST /v1/messages` (any error)             | `_anthropic_error_response` shape | **unchanged** |
| `POST /v1/completions` (any error)          | `_compat_error_response` shape | **unchanged** |
| `POST /v1/generate/stream` (any error)      | NDJSON stream + `error_code` field in event | **unchanged** |
| `POST /v1/load` with empty `model_id`       | 422 (FastAPI/pydantic min_length validation) | 422 (still FastAPI shape — envelope translation is deferred) |

### New file: `tests/test_serving_hardening_error_envelope_wired.py`

Nine integration tests using `fastapi.testclient.TestClient` against
the real `create_app()`-constructed app:

- `test_load_unknown_model_arg_returns_400_or_appropriate_status` —
  pins that `POST /v1/load` with `model_id=""` is rejected at the
  pydantic-validation phase (422), proving envelope translation for
  FastAPI 422 is **not** part of D-3
- `test_load_unhealthy_backend_returns_500_with_unified_envelope` —
  with `FakeBackend(healthy=False)`, `/v1/load` returns 500 + the
  unified envelope shape with `error_code="backend_error"`
- `test_generate_unknown_model_returns_404` — `/v1/generate` against
  an unloaded `model_id` returns 404 + unified envelope with
  `error_code="model_not_loaded"`
- `test_unload_unknown_model_returns_404` — `/v1/unload` against an
  unloaded `model_id` returns 404 + unified envelope with
  `error_code="model_not_loaded"`
- `test_unhandled_exception_returns_500_with_clean_envelope` —
  attach a synthetic route that raises
  `_SecretInternalProbeError("a leaky-looking secret message")`;
  assert 500, `error_code="unexpected_error"`,
  `message="unexpected internal error"`, and that neither the class
  name nor the secret message string appears anywhere in the
  serialized response body
- `test_envelope_carries_request_id_from_middleware` — inbound
  `x-request-id: req_test123_d3_envelope_wiring` is reflected in
  `body["request_id"]` of the error envelope
- `test_envelope_response_has_x_request_id_header` — the same
  inbound id is present in the outbound `x-request-id` response
  header on the error path (closing the loop on D-1's middleware
  contract)
- `test_envelope_shape_matches_unifiederrorenvelope_to_response_body`
  — structural pin: the JSON keys of the envelope returned over
  HTTP exactly match the keys of
  `UnifiedErrorEnvelope.to_response_body()`
- `test_compat_routes_keep_their_own_error_shape` — `POST
  /v1/chat/completions` with `model="compat-model-not-loaded"`
  returns the existing `_compat_error_response` shape `{id, object,
  error: {message, code}}`; the unified envelope's `error_code` /
  `http_status` top-level keys must NOT appear in the compat body

No uvicorn process is started. No model is loaded. The `FakeBackend`
default is used (and `FakeBackend(healthy=False)` for the unhealthy
case). The C-4 scaffold tests
(`test_serving_hardening.py`), the D-1 wiring tests
(`test_serving_hardening_wired.py`), and the D-2 wiring tests
(`test_serving_hardening_graceful_shutdown_wired.py`) are untouched
and remain passing.

### Round prompt: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d3-unified-error-envelope-wiring.md`

Records the executor-phase discipline (one import re-write + one
exception-handler-and-adapter block + three route signature retouches;
no compat-route modification; no doc modification; `TestClient` only)
and the four-deliverable contract.

## Test Counts

The combined sweep
`.venv/bin/python -m pytest tests/test_serving_hardening.py
tests/test_serving_hardening_wired.py
tests/test_serving_hardening_graceful_shutdown_wired.py
tests/test_serving_hardening_error_envelope_wired.py -q`
covers:

- `tests/test_serving_hardening.py` — 23 unit tests (C-4 scaffold,
  unchanged)
- `tests/test_serving_hardening_wired.py` — 5 integration tests
  (D-1, unchanged)
- `tests/test_serving_hardening_graceful_shutdown_wired.py` — 5
  integration tests (D-2, unchanged)
- `tests/test_serving_hardening_error_envelope_wired.py` — 9
  integration tests (D-3, new)

Total D-3 sweep: 42 tests across the four files (all passing on
Python 3.11 / FakeBackend; observed sweep duration ~0.6s).

## What This Checkpoint Closes

- `UnifiedErrorEnvelope` is the response shape for any unhandled
  exception escaping any route on the real owlmlx FastAPI app
- `ErrorEnvelopeBuilder.from_unexpected(...)` is the construction
  path for the unhandled-exception envelope; the response **does not
  leak** the raw exception class name or message
- `ErrorEnvelopeBuilder.from_runtime_error_code(...)` is the
  construction path for native lifecycle (`/v1/load`, `/v1/generate`,
  `/v1/unload`) `ok=False` envelope responses
- the native error namespace's `ok=False but HTTP 200` mismatch is
  closed for the three lifecycle routes
- the request-id field on every error envelope is sourced from
  `request.state.request_id` (the D-1 middleware's contract); the
  outbound `x-request-id` header is symmetrically preserved on the
  error response
- the compat namespace contract is preserved — the OpenAI / Anthropic
  SDK callers see no behavior change
- the round prompt + checkpoint pair is landed for audit

## What This Checkpoint Does Not Claim

- the entire serving surface uses the unified envelope — compat
  routes do not, by design; the OpenAI / Anthropic SDK contracts
  remain
- `/v1/generate/stream` mid-stream error events use the envelope —
  NDJSON stream error wiring is a separate future round
- FastAPI's own 422 request-validation responses use the envelope —
  the validator runs before any route body and returns FastAPI's
  built-in shape; envelope translation for 422 is a deferred round
- request timeouts are enforced anywhere in the runtime
- a `/metrics` route exists
- the full `IdempotentLoadHelper` surface is wired — only the
  `model_already_loaded` → success-with-detail branch is inlined via
  `_native_runtime_response(idempotent_already_loaded=True)`
- per-route ad-hoc `req_<uuid4hex>` generation in the compat routes
  has been removed (D-1.1's responsibility)
- Line 4 of the seven-line architectural assessment has been
  promoted from `partial` to a higher posture — D-3 is one of
  several remaining wiring rounds whose collective completion is
  the precondition for any posture promotion
- `docs/source-of-truth/serving-hardening-architecture.md` has been
  refreshed to reflect this wiring — that refresh is a separate
  doc-cleanup round

## Side Effects

### Behavior change on native error paths

This is the round's most material side effect. **Existing automated
callers** of `/v1/load`, `/v1/generate`, `/v1/unload` that

- ignore the HTTP status code and only read `body.ok` continue to
  work unchanged. A successful call (HTTP 200) still has `body.ok ==
  True`. This is the dominant pattern in owlmlx's own scripts and
  fixture suites.
- check the HTTP status code (e.g. raise on 4xx/5xx) **must be
  updated**. Before D-3 they would never raise on a typed runtime
  error because the runtime returned HTTP 200 with `ok=False` in the
  body. After D-3 they will see 400 / 404 / 409 / 500 on those
  paths, with the unified envelope shape in the body. Operators
  rolling D-3 out should audit any caller that wraps these routes
  with `requests.raise_for_status()` or similar.

### Other side effects

- `owlmlx/runtime/server.py` is the only existing source file
  modified in this round
- no documentation file is modified
- no test file other than the one new test is added
- `pyproject.toml`, `uv.lock`, `.python-version`, `conftest.py`,
  `README.md`, `tests/test_serving_hardening.py`,
  `tests/test_serving_hardening_wired.py`,
  `tests/test_serving_hardening_graceful_shutdown_wired.py`, and
  `owlmlx/runtime/serving_hardening.py` are unmodified
- the existing dirty tree on `main` (Gemma MTP probe, runtime monitor
  changes, heavy-weight repeatability, native MLX adapter
  modifications, etc.) is untouched
- no new dependency is introduced; `ErrorEnvelopeBuilder` and
  `UnifiedErrorEnvelope` are plain Python dataclasses / classes
  imported from `serving_hardening.py`
- the response body shape on **success** paths is unchanged for the
  three native routes — only error paths gain the envelope

## Notable Implementation Choices

- **HTTP status mapping for `model_not_loaded` is 404, not 409.**
  The C-4 scaffold's static
  `_RUNTIME_ERROR_CODE_TO_HTTP_STATUS` dict maps `model_not_loaded`
  to 409 ("conflict — the named model is not currently in a
  loaded state"). The D-3 wiring round overrides this to 404 ("the
  named resource does not exist on this runtime") via the explicit
  `http_status=...` parameter on
  `from_runtime_error_code(...)`, which the scaffold's docstring
  explicitly authorizes ("The wiring round may extend or override
  this mapping at install time"). 404 better matches operator
  intuition for the native namespace: a caller asking for a model
  that is not loaded is in the same posture as a caller asking for
  a route that does not exist. The 409 default in the scaffold is
  preserved for any future surface that imports the scaffold's
  helpers but does not pass an explicit status.
- **`model_already_loaded` is success-with-detail, not 409.** This
  is the idempotent-load policy from C-4. Operators expect
  `/v1/load` to be idempotent: calling it for an already-loaded
  model is a no-op, not an error. The wiring inlines this branch
  via `_native_runtime_response(idempotent_already_loaded=True)`
  rather than instantiating the full `IdempotentLoadHelper` class —
  full helper integration is a deferred D-5 round.
- **Generic `Exception` handler does not leak the class name.** This
  is the no-leak contract the C-4 scaffold's
  `from_unexpected(...)` docstring records. The handler logs nothing
  in this round; structured logging of the underlying exception is a
  separate D-3.1 follow-on. The handler's most important property
  is that **it never raises**: if `from_unexpected(...)` itself
  fails for any reason, the handler returns a literal dict
  `{"id": "err_owlmlx_native_fallback", ..., "http_status": 500}`
  with status 500.
- **`_native_runtime_response` is a closure, not a top-level
  function.** It is defined inside `create_app(...)` so it can
  close over `error_envelope_builder` (which carries a per-app
  monotonic envelope counter). Making it a top-level function would
  require either threading the builder through every call site or
  using a module-global builder (which would leak counter state
  across `create_app(...)` invocations in tests). The closure is
  the right scope.
- **Three native handlers gain a `request: Request` parameter.**
  FastAPI's dependency-injection resolves this from the active
  request scope without touching the route body or signature
  ordering. This is how the route wiring reads the
  D-1-middleware-set `request.state.request_id`.
- **Compat routes are explicitly out of scope.** A reviewer running
  `git diff -- owlmlx/runtime/server.py` should see edits only at
  (a) the import line, (b) the D-3 wiring block immediately after
  `_graceful_shutdown_drain`, and (c) the three native lifecycle
  route handlers. No edit lands inside the
  `/v1/chat/completions` / `/v1/messages` / `/v1/completions`
  bodies, and `_compat_error_response` /
  `_anthropic_error_response` are untouched.
- **Tests use `TestClient(..., raise_server_exceptions=False)` for
  the unhandled-exception path.** Without this flag,
  `httpx.Client.send` re-raises the exception in the test before the
  registered exception handler runs, defeating the test's purpose.
  The flag is the documented Starlette idiom for exercising
  `app.add_exception_handler(Exception, ...)` end-to-end.

## Capability Matrix State

`docs/source-of-truth/native-mlx-backend-capability-matrix.md` is
**unmodified** in this round. The matrix records MLX backend
capability entry points; HTTP error envelope wiring does not fit its
vocabulary, and serving-surface ownership is governed by
`docs/source-of-truth/serving-hardening-architecture.md` plus the
existing `single-host-orchestration-architecture.md`. No row is
promoted. No row is demoted.

## Seven-line Architectural Assessment

Line 4 — Serving surface (`partial`) remains `partial`. D-3 is one of
several remaining wiring rounds whose collective completion is the
precondition for moving Line 4 to a higher posture. Lines 1, 2, 3, 5,
6, 7 are unchanged in this round.

## Backwards-Compatibility Warning

| Caller pattern | Pre-D-3 behavior | Post-D-3 behavior | Action required |
| -------------- | ---------------- | ----------------- | --------------- |
| Reads only `body.ok`, ignores HTTP status | success: `body.ok=True`; error: `body.ok=False` (HTTP 200) | success: `body.ok=True`; error: HTTP 4xx/5xx + `body.error_code` (no `body.ok` field on error) | minor — error responses now carry `error_code` instead of `ok=false`; callers that switched on `body.ok` and then read `body.error_code` may need to switch on the unified envelope's `error_code` directly |
| Calls `requests.raise_for_status()` (or equivalent HTTP-status check) | never raises on typed runtime errors (HTTP 200 even on `ok=false`) | raises on typed runtime errors (4xx/5xx) | **caller must update** — wrap in try/except and read the unified envelope from the response body |
| Reads `body.message`, `body.error_code` | available on both success and `ok=false` paths under the prior contract | success body is unchanged; error body now carries `body.error_code` and `body.message` directly inside the unified envelope | none — both fields remain present on the error path |
| Compat (OpenAI / Anthropic SDK) callers | `_compat_error_response` / `_anthropic_error_response` shape | **unchanged** | none |

Operators rolling D-3 out should audit any caller that wraps the
three native lifecycle routes with `requests.raise_for_status()` or
similar HTTP-status-aware error handling.

## Next Authorized Round

Two parallel candidates, both deliberate single-item rounds:

### Path D-4 (recommended): Metrics Endpoint Wiring

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d4-metrics-endpoint-wiring.md`
  (to be authored)
- attach `MetricsSnapshotExporter` (already in
  `serving_hardening.py`) to a `/metrics` route on the FastAPI app;
  the route returns a Prometheus-text snapshot of the gate counters
  (waiters, total_served, total_queued, longest_wait_s,
  longest_exec_s) and, when the runtime backend is the native MLX
  backend, also the admission snapshot fields
  (max_observed_concurrency, in_critical_section, serving)
- evidence: focused tests that assert the metrics route exists,
  returns the expected `text/plain; version=0.0.4` content-type and
  a stable subset of metric names with correct `# HELP` / `# TYPE`
  preambles
- evidence-language: "MetricsSnapshotExporter wired on a /metrics
  route returning Prometheus text-exposition format; gate counters
  and native admission fields covered"

### Path D-5 (parallel): Per-Route Request Id Deduplication / Idempotent-Load Helper Class Integration

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d5-per-route-id-dedup-and-idempotent-load.md`
  (to be authored)
- two adjacent items:
  1. remove the per-route ad-hoc `request_id = f"req_{uuid.uuid4().hex}"`
     allocation in compat routes; route those callers to the
     middleware-provided `request.state.request_id` (the D-1
     contract)
  2. promote the inlined `model_already_loaded` branch in
     `_native_runtime_response` to use the full
     `IdempotentLoadHelper` class, exposing the
     `IdempotentLoadOutcome.to_response_body()` shape on the
     `/v1/load` success-with-detail path
- evidence: tests that assert (a) the compat routes preserve an
  inbound `x-request-id` end-to-end (no per-route regeneration), and
  (b) the `/v1/load` success-with-detail body matches
  `IdempotentLoadOutcome.to_response_body()` exactly

The remaining hardening (D-6 timeout) and the deferred D-3.1 (
structured logging on the unhandled-exception path) each warrant
their own dedicated wiring round so that operator review is per-item.

## Independent / Deferrable Parallel Lanes

- **C-1 cache_manager scaffold** — moves Line 5; landscape map exists
- **C-2 repeatability harness** — moves Line 6; landscape map exists
- **C-3 memory_actuator** — moves Line 3; landscape map exists
- **B-2** sibling candidate admissibility (Qwen3.6-27B / gemma-4-31B-it)
- **B-4** cooperative cancellation real-stream evidence

I recommend the **next round be D-4** because the metrics endpoint
exposes the gate counters that the D-2 graceful-shutdown drain
already reads, completing the diagnostic loop (request id → error
envelope → metrics snapshot) on the serving surface. D-5 is a
strong second because per-route id deduplication closes the
"caller-correlated request id" contract that D-1 + D-3 already
provides on the native namespace and extends it to the compat
namespace.
