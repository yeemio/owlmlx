# owlmlx Coordinator Checkpoint — Serving Hardening D-6 Structured Request Logging Wired

## Verdict

- `serving_hardening_d6_structured_request_logging_inline_middleware_wired_correlatable_to_request_id`

`runtime/server.py` gains an inline `@app.middleware("http")` request
lifecycle logger that emits structured INFO `request.start` /
`request.finish` (or WARNING `request.exception`) records on the
`owlmlx.runtime.server.request` logger, every record correlatable to
the D-1 `RequestIdMiddleware`-set `request.state.request_id`.

## What Is Now Frozen Exact

### `owlmlx/runtime/server.py` — three-part diff

1. **Import addition**: `import logging` (stdlib only)
2. **Middleware ordering swap**: `app.add_middleware(RequestIdMiddleware)`
   moved from BEFORE the new logging middleware to AFTER it. Per
   Starlette's middleware stacking model, later-registered middleware
   becomes outer (runs first on inbound). The swap makes
   `RequestIdMiddleware` outer and the logging middleware inner —
   guaranteeing `request.state.request_id` is populated before the
   logging middleware reads it
3. **Logging middleware definition**: a single `@app.middleware("http")`
   decorator wraps `_request_lifecycle_log_middleware(request, call_next)`:
   - At entry: read method / path / `request.state.request_id`; record
     `time.monotonic()` start; emit INFO `request.start`
   - try/except `await call_next(request)`:
     - exception: emit WARNING `request.exception` with
       `owlmlx_exception_class` field + `owlmlx_duration_ms`; re-raise
     - normal: emit INFO `request.finish` with `owlmlx_http_status`
       and `owlmlx_duration_ms`
   - All records carry the `owlmlx_event` / `owlmlx_request_id` /
     `owlmlx_http_method` / `owlmlx_http_path` field set so operators
     can filter by them in any structured-log sink

Net change to server.py: ~52 lines added (mostly comment + 3 log
calls), 1 line moved.

### New test file `tests/test_serving_hardening_request_logging_wired.py` — 6 tests

All tests use pytest's `caplog` fixture against the real owlmlx app
(constructed via `create_app()`):

- `test_healthz_emits_request_start_and_request_finish_records` — one
  request → exactly one start + one finish record
- `test_request_finish_record_carries_method_path_status_duration` —
  finish record's `owlmlx_http_method == "GET"`,
  `owlmlx_http_path == "/healthz"`, `owlmlx_http_status == 200`,
  `owlmlx_duration_ms` is non-negative float
- `test_request_records_carry_inbound_request_id` — inbound
  `x-request-id` header propagates to both start AND finish records
  (the ordering swap proves itself here)
- `test_request_records_carry_middleware_generated_id_when_no_inbound`
  — without inbound header, autogen id starts with `req_` per
  RequestIdMiddleware contract
- `test_404_path_still_emits_lifecycle_records` — 404 path emits
  start + finish; finish carries `owlmlx_http_status == 404`
- `test_lifecycle_records_use_owlmlx_runtime_server_request_logger` —
  all lifecycle records are on the documented logger name so operator
  filter rules are stable

## Test Counts

After D-6:

- `tests/test_serving_hardening_request_logging_wired.py`: **6 passed**
  (new this round)
- `tests/test_serving_hardening*` combined: **61 passed** (was 55 in
  Batch 5)
- combined regression on the C-x bundle + native MLX adapter set +
  full serving hardening chain: **145 passed, 3 skipped, 2 warnings
  in 2.38 s** (was 139 in Batch 5)

## What This Checkpoint Closes

- the visibility gap "owlmlx HTTP serving has no per-request log" —
  every request lifecycle now produces structured records on a
  dedicated logger
- the precondition for any external structured-log sink (Datadog,
  CloudWatch, Loki) — owlmlx now emits a stable schema operators can
  filter on
- the latent middleware-ordering subtlety: documented in code comment
  and locked by `test_request_records_carry_inbound_request_id`

## What This Checkpoint Does Not Claim

- **no log sink configuration.** Operator must configure the Python
  logging system (handlers, formatters, level) externally. Default
  Python `logging` config sends INFO to stderr if root logger is set
  up; otherwise records may be lost. owlmlx does not configure root
  handlers
- **no JSON formatter.** Records carry structured `extra` fields, but
  the formatter is operator's choice. A stdlib `json.dumps`-based
  formatter or a third-party (structlog, python-json-logger) would
  produce JSON; owlmlx makes no opinion
- **no sampling, no rate limit on log volume.** Every request gets
  logged. Operators with high QPS may want to add a sampling filter
- **no body / header logging.** Only metadata (method, path, status,
  duration, request_id, exception_class). Privacy-by-default
- **no capability matrix promotion.** Wiring is an observability
  primitive, not a capability claim
- **no integration with Prometheus /metrics endpoint (D-4).** Logs and
  metrics are separate observability channels by design — duration
  histograms are a separate (deferred) round
- **no scaffold extension.** `serving_hardening.py` was not modified;
  the logging middleware is inline because the C-4 scaffold did not
  include a logging primitive and adding one would be scaffold-grade
  work outside this round's scope
- **no environment / dependency change**

## Notable Implementation Choices

1. **Middleware order swap.** The most subtle change in this round:
   `app.add_middleware(RequestIdMiddleware)` moved from BEFORE to
   AFTER the inline logging middleware. Starlette's "later-registered
   middleware is outer" rule means RequestIdMiddleware now runs FIRST
   on inbound (outer) and the logging middleware runs SECOND (inner)
   — guaranteeing `request.state.request_id` is set when the logging
   middleware reads it. The swap is documented in two places: the
   comment block above the logging middleware definition, and a
   comment above the new `add_middleware` call. Test
   `test_request_records_carry_inbound_request_id` would have caught
   the wrong order (and did, during development)
2. **Inline `@app.middleware("http")`, not scaffold.** D-6 does not
   add a class to `serving_hardening.py`. Rationale: the C-4 scaffold
   round did not include a logging primitive (six hardenings landed,
   logging wasn't one of them), so adding it would be scaffold work
   not wiring work. Inline is the honest separation
3. **`owlmlx_*` field prefix.** All structured `extra` fields use the
   `owlmlx_` prefix to avoid collision with Python `logging`'s
   built-in record attributes (`name`, `msg`, `args`, etc.) and with
   common third-party log enrichers (e.g. uvicorn's access log adds
   client_addr / etc.)
4. **No body / header capture.** Privacy-by-default. A future round
   could add a configurable header allowlist if operators need it,
   but defaulting to logging headers is a security footgun
5. **Exception path re-raises.** The logging middleware logs the
   exception then re-raises so the D-3 unified error envelope
   exception handler can produce the response. The log line is the
   forensic breadcrumb; the response shape is D-3's responsibility

## Side Effects

- one new logger name: `owlmlx.runtime.server.request`. Operators
  filter / route / silence by it. Default Python logging behavior
  applies (propagate to root unless configured otherwise)
- three log records per HTTP request (in non-exception path: start +
  finish = 2; exception path: start + exception = 2). Volume
  proportional to QPS
- middleware order in server.py is now "logging inner / RequestId
  outer" — observable via `app.user_middleware` introspection if
  operators care
- D-1's wiring line moved by ~50 lines in server.py (now positioned
  after the logging middleware definition)

## Current Frozen Active Seam (No Change)

- phase45 sentinel chain unchanged
- top-level customer-runtime-evidence label remains
  `early_formal_runtime`

## Seven-Line Movement

After D-6, Line 4 (Serving surface) gains an observability primitive
but the label does not advance. The label measures **delivered
serving capability**, not log infrastructure. owlmlx now has six D-x
hardening primitives all wired (D-1 RequestId / D-2 GracefulShutdown
/ D-3 ErrorEnvelope / D-4 Metrics / D-5 PerRouteIdDedup / D-6
RequestLogging) — the serving surface is materially more credible
than at session start, but the label is still `partial` because no
batching, no scheduler, no auth.

## Next Authorized Round (operator decision required)

D-6 is the last cleanly parallelizable wiring round in the current
chain. Subsequent candidates all require **explicit operator
decision**:

- **C-2.1** repeatability harness real implementation. Largest
  leverage (moves Line 6 from `behind`). Cost: ~67 GB RAM + multi-
  hour campaign. Direction-change decision
- **B-1.3** matrix promotion staged commit (~3 unstaged files, simple
  one-commit cleanup of the native-MLX matrix line)
- **B-2** Qwen3.6-27B / gemma-4-31B-it sibling admissibility.
  Operator chooses whether to load 50–65 GB models for admissibility
  evidence
- **C-1.3** session field deprecation. **NOT cosmetic** — removes
  fields read by B-1.2 env-gated smoke's
  `kv_cache_factory.prompt_cache_call_count` assertion. Scope-up
  required
- **C-3.4** pressure subscription wiring. Actuator scaffold's
  `notify_pressure` is a counter without callbacks; wiring value is
  thin
- **D-7+** further serving hardenings (per-request timeout, idempotent
  load, auth, CORS, body size limit, etc.) — each a small wiring
  round

The recommendation is to **pause for operator direction** rather than
auto-continue. The micro-wiring rounds have hit diminishing returns;
the next moves require strategic choice.
