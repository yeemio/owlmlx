# owlmlx Serving Hardening Architecture

> Status: scaffold-grade contract
> Updated: 2026-05-08
> Authorship: C-4 scaffold landing round (this round)
> Owns: `owlmlx/runtime/serving_hardening.py`

## 1. Purpose, Scope, and Authorship

This document describes the *primitives* that the C-4 scaffold round
defines for serving-surface hardening on the `owlmlx` runtime. It is
the source of truth for ownership boundaries between
`owlmlx/runtime/serving_hardening.py` (this scaffold), the HTTP
application factory in `owlmlx/runtime/server.py`, the
`GenerationGate` in `owlmlx/serving.py`, and the `_TicketedAdmission`
inside `owlmlx/runtime/mlx_native_backend.py`.

The scaffold round produces *primitives* only: middleware classes,
async helpers, immutable result/policy dataclasses, and a stdlib-only
Prometheus text renderer. It does NOT modify `runtime/server.py` and
does NOT install any of these primitives onto a FastAPI app. Wiring
each primitive onto the serving path is the explicit responsibility of
a follow-up round, executed one item at a time with operator review
per hardening so that no `app.add_middleware(...)` call lands without
a deliberate decision.

## 2. Why This Module Exists

The seven-line architectural assessment recorded in
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` §7
identifies **Line 4 — Serving surface (`partial`)** as the lane the
C-4 scaffold begins to close. Line 4 is `partial` today because the
HTTP serving surface in `owlmlx/runtime/server.py` (a 2343-line
FastAPI application built via `create_app(...)` at line 496, launched
through `uvicorn.run(..., factory=True, ...)` in
`scripts/runtime_technical_preview_server.py:101-107`) currently has
**zero serving-surface hardening primitives installed**:

- no middleware of any kind
- no exception handlers (typed runtime errors today resolve to the
  ambiguous "ok=False, HTTP 200" mismatch)
- no auth dependency, no CORS policy, no body-size limit, no rate
  limit
- no `/metrics` endpoint and no Prometheus exposition surface
- no graceful shutdown drain — the process can `SIGTERM`-exit while
  the `GenerationGate` is mid-stream
- no unified `x-request-id` propagation — caller-supplied ids are
  invisible to the runtime's own logs
- no per-request timeout, no client-disconnect detection — the
  `Condition.wait()` on `owlmlx/serving.py:417` is unbounded

The six minimum hardenings the scaffold defines, in the order this
document discusses them, are:

1. Inbound `x-request-id` propagation as middleware
2. Per-request timeout + client-disconnect detection (via
   `asyncio.wait_for` and `Request.is_disconnected()`)
3. Graceful shutdown that drains the gate (a lifespan handler awaits
   `GenerationGate.is_active` falling to idle, then unloads models)
4. Unified structured error envelope (HTTP status code reflects
   `ok=False`)
5. Promotion of `admission` to a first-class status section, plus a
   Prometheus-format `/metrics` exporter rendered via `io.StringIO`
6. Idempotent `/v1/load` returning `already_loaded` as
   success-with-detail rather than HTTP 409

None of these require batching, none touch the post-claim
`max_concurrent = 1` invariant, and none depend on the orchestration
posture documents being lifted from `partial` to `supported`.

## 3. Non-Goals (Explicit)

The serving-hardening scaffold is bounded. It does NOT:

- add continuous batching, prefix cache reuse across requests, or any
  other capability that would change the post-claim ticketed-FIFO
  contract on `GenerationGate`
- change `GenerationGate` concurrency. `MAX_GENERATION_CONCURRENCY`
  remains 1; pre-gate cohort waiting defaults to `0 ms` and does not
  reopen post-claim parallel generation
- add a request scheduler, queue priority system, or fair-share
  arbiter. Admission remains ticketed FIFO
- alter `docs/source-of-truth/single-host-orchestration-architecture.md`
  in any way. Admission control / scheduler / residency manager /
  memory governor / recovery supervisor remain at the `partial`
  posture-and-reporting state recorded there; lifting them is the
  scope of separate rounds
- add a new Python dependency. Specifically `prometheus_client` and
  `psutil` are NOT added; the Prometheus text-format snapshot is
  rendered manually via `io.StringIO`
- promote any row in
  `docs/source-of-truth/native-mlx-backend-capability-matrix.md`. The
  matrix records MLX backend *capability entry points*; HTTP serving
  primitives do not fit its vocabulary

## 4. Ownership Boundaries

| Hardening                       | This scaffold owns                                                          | `runtime/server.py` today                                          | `GenerationGate`                                              | `_TicketedAdmission`                                         |
|---------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------|---------------------------------------------------------------|---------------------------------------------------------------|
| Request-id propagation          | `RequestIdMiddleware` + `RequestIdContext` + header constant                | not installed                                                       | not involved                                                  | not involved                                                  |
| Timeout + disconnect            | `RequestTimeoutHelper` + `RequestTimeoutPolicy` + `RequestDisconnectedError`| no per-request timeout, no disconnect polling                      | unbounded `Condition.wait()` at line 417                      | uses `Condition.wait()` for FIFO; not bounded by timeout      |
| Graceful shutdown               | `GracefulShutdown` + `GracefulShutdownConfig`                                | no lifespan-installed drain                                         | observed via `is_active` (read-only)                          | observed via `snapshot()` (read-only)                         |
| Unified error envelope          | `UnifiedErrorEnvelope` + `ErrorEnvelopeBuilder`                              | typed `RuntimeErrorCode` is shaped by `runtime/types.py`           | not involved                                                  | surfaces `RuntimeErrorCode` for backend-level errors          |
| Prometheus metrics              | `MetricsSnapshotExporter`                                                    | no `/metrics` route                                                 | exposes `status` dict the exporter reads                      | exposes `snapshot()` dict the exporter reads (when present)   |
| Idempotent load                 | `IdempotentLoadHelper` + `IdempotentLoadOutcome`                             | `/v1/load` returns native backend result as-is                      | not involved                                                  | not involved                                                  |

The scaffold does not import `GenerationGate` or `_TicketedAdmission`.
It accepts dict-shaped status surfaces via callable injection so that
the wiring round decides at install time which gate is observed.

## 5. Six Hardenings — Detail

### 5.1 Request-id Propagation (`x-request-id`)

**Current state.** `owlmlx/runtime/server.py` lines 1-2343 install no
middleware. Caller-supplied `x-request-id` headers are visible inside
individual handlers via `request.headers.get(...)`, but no centralized
propagation exists, so structured runtime logs and error envelopes
cannot reliably reference a single id field. Generated ids do not
exist; the runtime never produces one.

**Scaffold defines.** `RequestIdMiddleware`, a Starlette
`BaseHTTPMiddleware` subclass that reads the `x-request-id` header on
the inbound side, generates `req_<uuid4hex>` when absent or empty,
attaches both the bare id (`request.state.request_id`) and the
`RequestIdContext` (with `inbound: bool`) to request state, and on
the outbound side ensures the response header is set. It NEVER
overrides an inbound id; that is the lossless contract.

**Wiring round responsibility.** A single line in
`runtime/server.py`'s `create_app(...)`:

```python
app.add_middleware(RequestIdMiddleware)
```

Plus per-route adoption inside structured logging calls to read
`request.state.request_id`.

**Observable behavior change.** Every response carries
`x-request-id`. Operator dashboards can correlate caller-visible ids
with runtime structured logs without needing to thread them by hand.

### 5.2 Per-request Timeout + Client-disconnect Detection

**Current state.** No timeout on any handler. `GenerationGate`'s
`Condition.wait()` at `owlmlx/serving.py:417` is unbounded; a caller
that hangs the connection cannot release the gate until the in-flight
generation finishes naturally. Streaming responses cannot cancel
mid-token if the caller has gone away.

**Scaffold defines.** `RequestTimeoutPolicy` with sensible defaults
(60.0 s default, 600.0 s streaming, 0.5 s disconnect-check cadence).
`RequestTimeoutHelper.await_with_timeout` wraps `asyncio.wait_for`;
the timeout is *async-native* — no thread or process spawn.
`RequestTimeoutHelper.poll_disconnect` is an async generator that
yields periodically and raises `RequestDisconnectedError` once
`Request.is_disconnected()` returns truthy.

**Wiring round responsibility.** Each generation handler wraps its
inner `await` in `await helper.await_with_timeout(...)` and runs
`poll_disconnect(...)` as a sibling task that, on raise, cancels the
generation task. The exception handler converts
`asyncio.TimeoutError` into the unified envelope with
`error_code = "request_timeout"` and HTTP 504, and
`RequestDisconnectedError` into `client_disconnected` and HTTP 499.

**Observable behavior change.** Hung callers no longer pin gate
admission indefinitely. Long-running streams can be cleanly cancelled
when the caller's TCP connection closes.

### 5.3 Graceful Shutdown That Drains the Gate

**Current state.** `scripts/runtime_technical_preview_server.py`
launches `uvicorn.run(..., factory=True, ...)` with no `lifespan`
shutdown handler. `SIGTERM` cuts mid-generation; in-flight cohort
windows are abandoned without drain.

**Scaffold defines.** `GracefulShutdownConfig` carrying
`gate_idle_timeout_s` (30.0 s default), `unload_models_on_shutdown`
(True), and `poll_interval_s` (50 ms). `GracefulShutdown.drain_gate`
polls a caller-supplied `gate_status_callable()` until
`is_active` is False or the deadline trips, and returns a structured
report. `GracefulShutdown.on_shutdown` orchestrates drain, then
optionally invokes a sync-or-async `unload_models_callable`.

The drain is observation-only. It does NOT call any gate method, does
NOT cancel in-flight generations, does NOT mutate gate state. Forced
cancellation is a separate primitive whose wiring is also deferred.

**Wiring round responsibility.** Either an `app.router.on_shutdown`
hook or a FastAPI `lifespan` async context that awaits
`GracefulShutdown().on_shutdown(gate_status_callable=lambda:
{"is_active": gate.is_active, **gate.status},
unload_models_callable=lambda: kernel.unload_all())`. The wiring
round decides whether shutdown delays exceed the deployment's SLA;
the scaffold only commits to the drain shape.

**Observable behavior change.** Shutdowns drain in-flight generations
where possible; structured shutdown logs record poll count, elapsed
time, and final gate status so post-mortem operators can distinguish
a clean shutdown from a forced one.

### 5.4 Unified Structured Error Envelope

**Current state.** Several handlers in `owlmlx/runtime/server.py`
return `{"ok": False, ...}` with HTTP 200, because the typed runtime
contract carries `RuntimeErrorCode` in the body but not in the HTTP
status. Caller-facing HTTP semantics therefore disagree with the
runtime's own `ok` field.

**Scaffold defines.** `UnifiedErrorEnvelope` (frozen dataclass with
`id`, `object="error"`, `error_code`, `message`, `request_id`,
`http_status`) and `ErrorEnvelopeBuilder`. The builder maps
`error_code` to HTTP status via a static table:

- `invalid_request` → 400
- `model_not_loaded`, `model_already_loaded` → 409
- `backend_error` → 502
- `memory_pressure` → 503
- `request_timeout` → 504
- `client_disconnected` → 499
- unknown / unexpected → 500

`from_unexpected(exc, request_id=...)` deliberately strips the
exception's class name, message, and traceback from any field that
ships in the response body. The wiring round logs the underlying
exception via the structured logger; the response surface only carries
an opaque `unexpected_error` token. This is the no-leak contract.

**Wiring round responsibility.** `app.add_exception_handler(...)` for
`RuntimeError`/typed runtime errors and a catch-all for everything
else. Each handler returns
`Response(content=envelope.to_json(), status_code=envelope.http_status,
media_type="application/json")`.

**Observable behavior change.** HTTP status reflects success vs
failure; caller-supplied `request_id` is echoed; unknown internal
errors no longer leak Python class names.

### 5.5 Prometheus-format `/metrics` Exporter

**Current state.** `owlmlx/runtime/server.py` exposes structured
posture status surfaces (admission policy, residency policy, etc.) as
JSON GET endpoints, but no Prometheus exposition format and no
`/metrics` route. Operator dashboards must scrape the JSON surfaces
manually.

**Scaffold defines.** `MetricsSnapshotExporter`, a stdlib-only renderer
that takes a `gate_status` dict (shaped like `GenerationGate.status`)
and an optional `native_admission_snapshot` dict (shaped like
`MlxNativeBackend.status().detail.admission`) and emits Prometheus
text-format with `# HELP`, `# TYPE`, and value lines. Counters use
the `_total` suffix per Prometheus convention; gauges do not.

The seven exposed metrics are:

- `owlmlx_native_waiters` (gauge)
- `owlmlx_native_total_served_total` (counter)
- `owlmlx_native_total_queued_total` (counter)
- `owlmlx_native_longest_wait_seconds` (gauge)
- `owlmlx_native_longest_exec_seconds` (gauge)
- `owlmlx_native_native_max_observed_concurrency` (gauge, only when
  `native_admission_snapshot` is supplied)
- `owlmlx_native_native_in_critical_section` (gauge, conditional)
- `owlmlx_native_native_serving_ticket` (gauge, conditional)

The exporter never fabricates a zero for a missing input field —
omitting the metric on missing input keeps the boundary between "no
data" and "actually zero" visible.

**Wiring round responsibility.** A `@app.get("/metrics")` route that
calls `exporter.render_prometheus_text(gate_status=gate.status,
native_admission_snapshot=...)` and returns it with
`media_type="text/plain; version=0.0.4"`.

**Observable behavior change.** Prometheus scrapers can ingest gate
and admission counters via the standard text format without owlmlx
adopting `prometheus_client`.

### 5.6 Idempotent `/v1/load`

**Current state.** When a caller asks `/v1/load` to load a model that
is already resident, the backend returns
`error_code = "model_already_loaded"`. The runtime today surfaces this
as a failure response even though the *caller's intent* — "this model
should be resident" — is satisfied. The current behavior breaks
load-balanced deployments where multiple operators may issue the
same warm-up call.

**Scaffold defines.** `IdempotentLoadOutcome` (frozen dataclass with
`model_id`, `already_loaded`, `memory_gb`, `ok`) and
`IdempotentLoadHelper.interpret_backend_result`. The helper rewrites
the one specific case `error_code == "model_already_loaded"` into
`already_loaded = True, ok = True`. All other failure codes pass
through unchanged (`ok = False`).

**Wiring round responsibility.** The `/v1/load` handler in
`runtime/server.py` calls
`IdempotentLoadHelper().interpret_backend_result(backend_result_dict=
asdict(load_result))` and returns
`outcome.to_response_body()` with HTTP 200 when `outcome.ok` is
True.

**Observable behavior change.** Repeated warm-up calls succeed with a
detail flag instead of failing.

## 6. Wiring Round Responsibilities (Deferred)

A future round, executed deliberately one hardening at a time, would
land changes in `owlmlx/runtime/server.py`:

- `app.add_middleware(RequestIdMiddleware)` — section 5.1
- A new exception handler block built on `ErrorEnvelopeBuilder` —
  section 5.4
- A new `lifespan` async context (or `app.router.on_shutdown` hook)
  built on `GracefulShutdown.on_shutdown(...)` — section 5.3
- A new `@app.get("/metrics")` route built on
  `MetricsSnapshotExporter.render_prometheus_text(...)` — section 5.5
- Per-handler adoption of `RequestTimeoutHelper.await_with_timeout`
  and `poll_disconnect` — section 5.2
- `/v1/load` rewrite to use `IdempotentLoadHelper` — section 5.6

Each of these can be wired independently. The scaffold does not impose
an ordering. Operator review per item is the documented requirement so
that, for instance, a `gate_idle_timeout_s` value chosen for a 7B
deployment is not silently inherited by a 70B deployment whose
streaming completions legitimately exceed 30 s.

## 7. Promotion-gate Coupling

This scaffold does NOT promote any row in
`docs/source-of-truth/native-mlx-backend-capability-matrix.md`. The
matrix is about MLX backend capability entry points (KV cache handle,
sampler injection, decode-step iterator, etc.). Serving-surface
primitives do not fit the matrix's vocabulary; "serving surface" is
neither a `mlx_lm` upstream API entry point nor an `mlx` library
feature. No row is upgraded; no row is demoted; the matrix is read
only for the seven-line architectural assessment line numbering.

The serving-surface lane is governed by:

- this document (`serving-hardening-architecture.md`) — primitive
  ownership boundaries
- `docs/source-of-truth/single-host-orchestration-architecture.md` —
  admission/scheduler/residency posture (separate scope, not modified)
- a future *serving-surface contract* document, to be produced by the
  first wiring round, that records which primitives have been
  installed onto which routes and which haven't

## 8. No-new-dependency Contract

The scaffold uses only the standard library plus Starlette pieces that
are *already in the dependency closure of FastAPI*. Specifically:

- `asyncio`, `dataclasses`, `io`, `json`, `time`, `uuid`, `typing` —
  stdlib
- `starlette.middleware.base.BaseHTTPMiddleware`,
  `starlette.requests.Request`, `starlette.responses.Response` — already
  installed via FastAPI

The scaffold does NOT add:

- `prometheus_client` — Prometheus text exposition is rendered via
  `io.StringIO` and manual `# HELP` / `# TYPE` line formatting
- `psutil` — no system-level resource sampling is performed by the
  scaffold; system metrics are out of scope
- `httpx`, `requests`, or any other HTTP client — the scaffold does
  not make outbound HTTP calls
- `opentelemetry-*` — trace context is listed under §9 extension
  points, not implemented

This keeps the scaffold install-footprint zero-delta. `pyproject.toml`
and `uv.lock` are NOT modified by this round.

## 9. Extension Points (Not Implemented)

The following are deliberately out of scope for the C-4 scaffold round
and are listed so future rounds can plan against them rather than
re-discover them:

- **Auth dependency.** Bearer-token / API-key dependency injectable
  per route; needs an operator decision on storage and rotation.
- **CORS policy.** `CORSMiddleware` with a deployment-specific
  origin allow-list; needs a deployment policy doc.
- **Body-size limits.** `Content-Length`-aware middleware that 413s
  oversized requests; coupling to `request_context_length_truth.py`
  is the cleanest path.
- **Rate limiting.** Per-caller-id token bucket; needs decision on
  whether the token bucket is in-process or backed by a shared store.
- **OpenTelemetry trace context.** Inbound `traceparent` header
  propagation; needs `opentelemetry-api` dependency, which the
  no-new-dependency contract above declines this round.
- **Structured request logging.** A logging adapter that joins
  `request_id`, gate ticket, and (when present) admission ticket on
  one structured line per request; the request-id middleware in this
  scaffold is the prerequisite for that adapter.
- **Force-cancel on shutdown.** Cooperative cancellation primitives
  for in-flight generations; depends on coupling to
  `_TicketedAdmission.release()` semantics that the scaffold
  deliberately does not import.

Each of these can be added by extending `serving_hardening.py` (or
spinning out a sibling module) without modifying the primitives this
scaffold round defines.

## 10. What This Doc Does Not Claim

- it does NOT claim the serving surface is hardened; the surface is
  hardened only after the wiring round lands and the relevant
  primitives are installed
- it does NOT claim Line 4 of the seven-line assessment has moved
  from `partial` to `supported`; closing Line 4 requires the wiring
  round plus an evidence round on a real deployment
- it does NOT claim any HTTP status mapping is final; the table in
  section 5.4 is scaffold-grade and may be narrowed by the wiring
  round per route
- it does NOT replace `single-host-orchestration-architecture.md`;
  admission/scheduler/residency/memory/recovery remain governed by
  that document, which is unmodified by this round
- it does NOT add or remove a Python dependency; `pyproject.toml`
  and `uv.lock` are read-only in this round
- it does NOT modify `runtime/server.py`, `serving.py`,
  `mlx_native_backend.py`, `kernel.py`, `types.py`, or any test file
  outside `tests/test_serving_hardening.py`
