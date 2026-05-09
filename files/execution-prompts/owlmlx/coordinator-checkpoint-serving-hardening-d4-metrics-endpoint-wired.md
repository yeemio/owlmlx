# owlmlx Coordinator Checkpoint — Serving Hardening D-4 Metrics Endpoint Wired

## Verdict

- `serving_hardening_d4_metrics_endpoint_wired_prometheus_text`

The D-4 wiring round is closed. The C-4 scaffold's
`MetricsSnapshotExporter` is now installed on the real owlmlx FastAPI
app constructed by `owlmlx.runtime.server.create_app(...)` along one
new surface:

1. **`GET /metrics` route** registered at the end of `create_app(...)`.
   The route reads `runtime.status_dict()` per scrape, slices out the
   `generation_gate` dict and the optional
   `backend.detail.admission` dict (which the native MLX backend
   populates and the `FakeBackend` does not), and renders a
   Prometheus text-exposition snapshot via the C-4 scaffold's
   `MetricsSnapshotExporter.render_prometheus_text(...)`. The
   response carries `Content-Type: text/plain; version=0.0.4` and
   HTTP 200.

The route is **not** wrapped by the D-3 unified error envelope —
Prometheus scrapers reject JSON envelopes; the response shape must be
the line-based plain-text exposition format. If the exporter itself
raises during render, the route falls back to the literal text line
`# owlmlx_metrics_render_error 1\n` with HTTP 200 so the scrape does
not fail outright. The `/metrics` route is **unauthenticated** by
design (Prometheus scrapers do not carry auth in typical scrape
configs); operators are responsible for network-level access control
(firewall, reverse proxy, mTLS at the ingress, etc.).

The remaining two C-4 hardening primitives (timeout, idempotent-load
helper class) are **NOT** wired in this round; each is a separate
operator decision in its own future D-* round.

## What This Checkpoint Is

A wiring marker for one specific primitive (`MetricsSnapshotExporter`).
It says: the FastAPI app that `create_app(...)` returns now has

- a one-time `_metrics_exporter = MetricsSnapshotExporter(namespace="owlmlx_native")`
  instance constructed inside `create_app(...)`,
- a `GET /metrics` route registered on the app that reads
  `runtime.status_dict()` per scrape and renders a Prometheus
  text-exposition snapshot, returning `text/plain; version=0.0.4`,

and an integration test file backs this behavior end-to-end against
the real app surface.

It does **not** say:

- the entire serving surface emits Prometheus metrics (no compat
  route, no `/v1/runtime/*` route emits its own metric labels)
- the runtime now has full observability (no histograms, no per-route
  request-rate counters, no decode-tokens-per-second gauge, no
  process / OS-level metrics)
- a Prometheus-style alerting rule has been authored (alert authoring
  is operator responsibility)
- a Grafana dashboard has been authored
- the C-4 scaffold's `IdempotentLoadHelper` is wired
- per-request timeouts are enforced
- a background metrics sampler is running (the exporter is pure;
  every scrape produces a fresh snapshot from the current runtime
  status)
- the existing per-route ad-hoc `req_<uuid4hex>` generation in the
  compat routes has been removed (D-1.1's responsibility)

## What Is Now Frozen Exact

### Modified file: `owlmlx/runtime/server.py`

Three additions:

1. The relative-import line is extended to include
   `MetricsSnapshotExporter`:
   ```python
   from .serving_hardening import (
       ErrorEnvelopeBuilder,
       GracefulShutdown,
       GracefulShutdownConfig,
       MetricsSnapshotExporter,
       RequestIdMiddleware,
       UnifiedErrorEnvelope,
   )
   ```
   No other top-level import is touched.

2. Inside `create_app(...)`, immediately after the existing line
   `error_envelope_builder = ErrorEnvelopeBuilder(namespace="owlmlx_native")`,
   a new D-4 wiring block is inserted that:
   - documents (in a comment block) that the exporter is pure, that
     each scrape consults `runtime.status_dict()` directly, that
     the route is plain text rather than a JSON envelope, and that
     the route is unauthenticated by default
   - constructs `_metrics_exporter = MetricsSnapshotExporter(namespace="owlmlx_native")`
     once per app

3. At the end of `create_app(...)`, immediately before `return app`
   and after the `/v1/unload` route, a new `@app.get("/metrics")`
   route is registered. The route:
   - performs a function-local `from starlette.responses import Response`
     (so the top-level import block stays unchanged beyond the
     `MetricsSnapshotExporter` addition)
   - reads `runtime.status_dict()` and slices `generation_gate` plus
     `backend.detail.admission` defensively (None / non-dict values
     coerced safely)
   - calls
     `_metrics_exporter.render_prometheus_text(gate_status=...,
     native_admission_snapshot=...)`
   - on any exception, falls back to the literal text line
     `# owlmlx_metrics_render_error 1\n` (HTTP 200)
   - returns `Response(content=text, media_type="text/plain; version=0.0.4")`

The D-1 `RequestIdMiddleware` registration line is **untouched**. The
D-2 graceful-shutdown registration block is **untouched**. The D-3
unified-error-envelope wiring block (`error_envelope_builder`,
`_unhandled_exception_handler`,
`app.add_exception_handler(Exception, _unhandled_exception_handler)`,
`_NATIVE_ERROR_CODE_TO_HTTP_STATUS`, `_native_runtime_response`) is
**untouched**. All `/v1/load` / `/v1/generate` / `/v1/unload` /
compat / `/v1/runtime/*` route handlers are **untouched**.

Diff summary: roughly `+71 -0` lines on `server.py` (one import
extended by one symbol, ~17 lines for the exporter instantiation +
docstring comment, ~52 lines for the `/metrics` route handler with
docstring).

### `/metrics` Route Contract — Frozen

| Field | Value |
| ----- | ----- |
| Method | `GET` |
| Path | `/metrics` |
| Auth | unauthenticated (operator network-level access control) |
| Status (success) | 200 |
| Status (exporter render failure) | 200 (with diagnostic text line) |
| Content-Type | `text/plain; version=0.0.4` |
| Body shape | Prometheus text-exposition format — `# HELP`, `# TYPE`, value line per metric |
| Namespace prefix | `owlmlx_native_` |
| Gate metrics emitted (always when populated) | `owlmlx_native_waiters` (gauge), `owlmlx_native_total_served_total` (counter), `owlmlx_native_total_queued_total` (counter), `owlmlx_native_longest_wait_seconds` (gauge), `owlmlx_native_longest_exec_seconds` (gauge) |
| Native admission metrics (only when `backend.detail.admission` present) | `owlmlx_native_native_max_observed_concurrency` (gauge), `owlmlx_native_native_in_critical_section` (gauge), `owlmlx_native_native_serving_ticket` (gauge) |
| Unified error envelope on this route | **NOT applied** — would break Prometheus scraper expectations |
| D-1 request-id middleware | applied (echoes inbound `x-request-id`) |

### New file: `tests/test_serving_hardening_metrics_wired.py`

Seven integration tests using `fastapi.testclient.TestClient` against
the real `create_app()`-constructed app:

- `test_metrics_endpoint_returns_200_with_prometheus_text_media_type`
  — GET `/metrics` returns 200; the `Content-Type` header starts
  with `text/plain` and contains the `version=0.0.4` Prometheus
  text-format marker
- `test_metrics_endpoint_includes_owlmlx_native_namespace_prefix` —
  the body carries the `owlmlx_native_` namespace prefix configured
  on the exporter constructor
- `test_metrics_endpoint_includes_gate_counters` — the body contains
  the gate-counter metric names emitted by the C-4 scaffold's
  `render_prometheus_text` whenever the gate-status dict carries the
  corresponding source fields (`waiters`, `total_served_total`,
  `total_queued_total`, `longest_wait_seconds`, `longest_exec_seconds`)
- `test_metrics_endpoint_includes_TYPE_HELP_lines` — every metric
  block in the body is preceded by the Prometheus-required `# HELP`
  and `# TYPE` lines (`gauge` for gauges, `counter` for the `_total`
  cumulative counters)
- `test_metrics_endpoint_idempotent_on_repeated_get` — two consecutive
  scrapes return 200 and produce the same set of metric names; the
  exporter is pure and does not introduce drift between scrapes
- `test_metrics_endpoint_works_with_no_native_admission_snapshot` —
  with the default `FakeBackend` (which does not populate
  `backend.detail.admission`), the route still renders successfully;
  the body contains the gate-counter block but does **not** contain
  any `native_max_observed_concurrency` / `native_in_critical_section`
  / `native_serving_ticket` line
- `test_metrics_endpoint_carries_request_id_propagation` — an inbound
  `x-request-id` header is echoed on the `/metrics` response header,
  closing the D-1 + D-4 loop

No uvicorn process is started. No model is loaded. The `FakeBackend`
default is used. The C-4 scaffold tests
(`test_serving_hardening.py`), the D-1 wiring tests
(`test_serving_hardening_wired.py`), the D-2 wiring tests
(`test_serving_hardening_graceful_shutdown_wired.py`), and the D-3
wiring tests (`test_serving_hardening_error_envelope_wired.py`) are
untouched and remain passing.

### Round prompt: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d4-metrics-endpoint-wiring.md`

Records the executor-phase discipline (one import extension + one
exporter instantiation block + one route registration; no compat-route
modification; no D-1 / D-2 / D-3 modification; no doc modification;
`TestClient` only) and the four-deliverable contract.

## Test Counts

The combined sweep
`.venv/bin/python -m pytest tests/test_serving_hardening.py
tests/test_serving_hardening_wired.py
tests/test_serving_hardening_graceful_shutdown_wired.py
tests/test_serving_hardening_error_envelope_wired.py
tests/test_serving_hardening_metrics_wired.py -q`
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
  tests (D-4, new)

Total D-4 sweep: 49 tests across the five files (all passing on
Python 3.11 / FakeBackend; observed sweep duration ~0.6s).

## What This Checkpoint Closes

- `MetricsSnapshotExporter` is the construction path for the
  Prometheus text-exposition body served at `GET /metrics` on the
  real owlmlx FastAPI app
- the gate counters from `runtime.status_dict()['generation_gate']`
  (waiters, total_served, total_queued, longest_wait_s, longest_exec_s)
  are now exposed to Prometheus scrapers via the
  `owlmlx_native_<name>` namespace
- the native MLX backend's admission snapshot (when the runtime is
  bound to the native backend and `backend.detail.admission` is
  populated) is exposed under
  `owlmlx_native_native_max_observed_concurrency`,
  `owlmlx_native_native_in_critical_section`,
  `owlmlx_native_native_serving_ticket`
- the diagnostic loop (request id → error envelope → metrics
  snapshot) is closed for the native namespace: a Prometheus scrape
  carrying `x-request-id` is symmetrically echoed in the response
  header per D-1, the unified error envelope continues to be the
  shape of any unhandled exception per D-3, and the metrics endpoint
  exposes the gate counters that drove D-2's graceful-shutdown drain
- the round prompt + checkpoint pair is landed for audit

## What This Checkpoint Does Not Claim

- the entire serving surface emits Prometheus metrics — only the new
  `/metrics` route does; no compat or `/v1/runtime/*` route emits
  its own labeled metric blocks
- the runtime has "production-ready monitoring" or "complete
  observability" — D-4 is one wiring of one primitive; histograms,
  per-route latency labels, decode tokens-per-second gauges, OS /
  process metrics (RSS, CPU, FD count, etc.) are all explicitly
  out of scope
- a Prometheus alerting rule or Grafana dashboard ships with this
  round — those are operator-side artifacts authored separately
- the C-4 scaffold's `IdempotentLoadHelper` is wired
- request timeouts are enforced
- background sampling of the runtime status occurs as a side effect
  of the metrics endpoint — there is no sampler task; each scrape
  is a fresh read of `runtime.status_dict()`
- per-route ad-hoc `req_<uuid4hex>` generation in the compat routes
  has been removed (D-1.1's responsibility)
- Line 4 of the seven-line architectural assessment has been
  promoted from `partial` to a higher posture — D-4 is one of
  several remaining wiring rounds whose collective completion is
  the precondition for any posture promotion
- `docs/source-of-truth/serving-hardening-architecture.md` has been
  refreshed to reflect this wiring — that refresh is a separate
  doc-cleanup round
- the capability matrix has any row promoted / demoted (it does not;
  HTTP-side metrics surface is governed by
  `single-host-orchestration-architecture.md` plus the
  serving-hardening architecture doc, not the matrix)

## Side Effects

### New unauthenticated route surface

The `/metrics` route is registered without any authentication or
authorization check. This matches the typical Prometheus scrape
configuration (the Prometheus server itself does not carry caller
credentials on its scrape requests). Operators rolling D-4 out
should ensure that the runtime's network exposure of the `/metrics`
route is restricted to the Prometheus scraper itself — typically by:

- binding the runtime to a loopback interface and using a host-local
  Prometheus
- placing a reverse proxy in front of the runtime that strips
  `/metrics` from the public-facing surface, or
- using firewall rules to allow only the Prometheus host's IP to
  reach `/metrics`

The runtime does **not** ship any of these access-control
mechanisms; that is the operator's lane.

### Other side effects

- `owlmlx/runtime/server.py` is the only existing source file
  modified in this round
- no documentation file is modified
- no test file other than the one new test is added
- `pyproject.toml`, `uv.lock`, `.python-version`, `conftest.py`,
  `README.md`, `tests/test_serving_hardening.py`,
  `tests/test_serving_hardening_wired.py`,
  `tests/test_serving_hardening_graceful_shutdown_wired.py`,
  `tests/test_serving_hardening_error_envelope_wired.py`, and
  `owlmlx/runtime/serving_hardening.py` are unmodified
- the existing dirty tree on `main` (Gemma MTP probe, runtime monitor
  changes, heavy-weight repeatability, native MLX adapter
  modifications, etc.) is untouched
- no new dependency is introduced; `MetricsSnapshotExporter` is a
  plain-Python class imported from `serving_hardening.py` that
  renders text via `io.StringIO` (stdlib only). `prometheus_client`,
  `psutil`, and similar are explicitly NOT added to `pyproject.toml`
- the response body shape on every existing route is unchanged; the
  `/metrics` route is purely additive

## Notable Implementation Choices

- **Function-local `Response` import.** The route handler imports
  `Response` from `starlette.responses` inside the function body
  rather than at the top of the module. The top-level import block
  is therefore extended by exactly one symbol
  (`MetricsSnapshotExporter`) — the minimal change consistent with
  the round's discipline. Starlette is already a transitive
  dependency of FastAPI; no new dependency is introduced.

- **`/metrics` is NOT wrapped by the unified error envelope.** D-3
  installs a generic `Exception` handler that converts unhandled
  exceptions into a JSON unified envelope. Prometheus scrapers reject
  JSON envelopes — they expect `text/plain` line-based exposition
  format. If the metrics route bubbled an exception up to the D-3
  handler, the scrape would receive a JSON body with the wrong
  Content-Type and would mark the target as down. Therefore, the
  metrics route catches every internal exception itself and falls
  back to the literal text line `# owlmlx_metrics_render_error 1\n`
  (HTTP 200). The diagnostic line lets operators see the failure on
  their dashboard while keeping the scrape successful from the
  Prometheus server's point of view.

- **`/metrics` is unauthenticated by design.** Prometheus scrape
  configurations do not typically carry auth credentials; the
  scraper makes a plain HTTP GET. Adding authentication here would
  break the standard scrape contract. Operators are responsible
  for network-level access control (loopback bind, firewall, reverse
  proxy, mTLS at the ingress, etc.). This is documented above under
  "New unauthenticated route surface".

- **The exporter is pure; no background sampler.** Each scrape
  produces a fresh snapshot from `runtime.status_dict()`. There is no
  cached metrics buffer, no aggregation window, no rate-limiter on
  the route. This keeps the wiring minimal and matches the C-4
  scaffold's contract (the scaffold's `MetricsSnapshotExporter`
  documents itself as a pure renderer over its two input dicts).
  Aggregation, sampling, and trend recording are governed elsewhere
  — the runtime monitor's own sampler loop already exists for that
  purpose and writes its own JSONL store.

- **`_metrics_exporter` is constructed inside `create_app(...)`.**
  The exporter is stateless beyond the namespace string, but
  constructing it inside `create_app(...)` keeps the per-app scope
  consistent with how `error_envelope_builder` is constructed (D-3)
  and avoids any module-global state that would persist across
  `create_app(...)` invocations in tests.

- **Defensive slicing of `runtime.status_dict()`.** The route guards
  against `None` and non-dict values for `generation_gate` and for
  `backend.detail.admission`. The C-4 scaffold's
  `render_prometheus_text` already tolerates a missing field on its
  inputs (it omits the corresponding metric block), but the route
  cannot assume the runtime status surface always populates the
  expected dict shape — defensive slicing keeps the route stable
  even if a future kernel change produces a different shape on these
  diagnostic sections.

- **Render failure falls back to a 200 with a diagnostic line, not
  to a 5xx.** Returning HTTP 5xx from `/metrics` causes Prometheus
  to mark the scrape as failed and the target as down, which loses
  the very signal operators most want during a failure (they cannot
  see the diagnostic counter line if the scrape itself failed). The
  fallback line `# owlmlx_metrics_render_error 1\n` is intentionally
  shaped like a Prometheus comment line; downstream scrapers that
  surface comment lines (Grafana's "raw" panel, for example) will
  show the diagnostic.

- **The D-1 `RequestIdMiddleware` covers `/metrics` as well.** The
  middleware is registered at the app level and therefore wraps
  every route, including `/metrics`. An inbound `x-request-id`
  header is echoed on the metrics response header even though the
  metrics route itself never reads `request.state`. This is asserted
  by the `test_metrics_endpoint_carries_request_id_propagation`
  test.

- **No new metric beyond what the C-4 scaffold already emits.** The
  wiring round does not introduce any new metric name; it only
  exposes the metrics the scaffold already emits over an HTTP
  surface. New metric names (e.g. decode tokens-per-second,
  per-model histograms, OS-level RSS) would belong in a separate C-*
  scaffold round followed by a D-* wiring round, with operator
  review of metric cardinality and label space.

## Capability Matrix State

`docs/source-of-truth/native-mlx-backend-capability-matrix.md` is
**unmodified** in this round. The matrix records MLX backend
capability entry points; HTTP metrics endpoint wiring does not fit
its vocabulary, and serving-surface ownership is governed by
`docs/source-of-truth/serving-hardening-architecture.md` plus the
existing `single-host-orchestration-architecture.md`. No row is
promoted. No row is demoted.

## Seven-line Architectural Assessment

Line 4 — Serving surface (`partial`) remains `partial`. D-4 is one of
several remaining wiring rounds whose collective completion is the
precondition for moving Line 4 to a higher posture. Lines 1, 2, 3, 5,
6, 7 are unchanged in this round.

## Next Authorized Round

Two parallel candidates, both deliberate single-item rounds:

### Path D-5 (recommended): Per-Route Request Id Deduplication / Idempotent-Load Helper Class Integration

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
- evidence-language: "RequestIdMiddleware-set request_id consumed
  by compat routes; IdempotentLoadHelper renders /v1/load
  success-with-detail body"

### Path D-6 (parallel): Per-Request Timeout + Client-Disconnect Detection Wiring

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d6-timeout-and-disconnect-wiring.md`
  (to be authored)
- attach `RequestTimeoutHelper` + `RequestDisconnectedError` to
  selected native routes; map disconnect to HTTP 499 (per the C-4
  scaffold's static mapping) via the unified envelope
- evidence: tests that assert (a) a slow handler is interrupted by
  the timeout policy, and (b) a synthetic client disconnect raises
  `RequestDisconnectedError` and is converted to a 499 + unified
  envelope

The remaining hardening (`IdempotentLoadHelper` class integration is
covered in D-5, structured logging on the unhandled-exception path
is the deferred D-3.1, and the streaming-error envelope is its own
deferred round) each warrant their own dedicated wiring round so that
operator review is per-item.

## Independent / Deferrable Parallel Lanes

- **C-1 cache_manager scaffold** — moves Line 5; landscape map exists
- **C-2 repeatability harness** — moves Line 6; landscape map exists
- **C-3 memory_actuator** — moves Line 3; landscape map exists
- **B-2** sibling candidate admissibility (Qwen3.6-27B / gemma-4-31B-it)
- **B-4** cooperative cancellation real-stream evidence

I recommend the **next round be D-5** because the per-route id
deduplication closes the "caller-correlated request id" contract that
D-1 + D-3 already provides on the native namespace and extends it to
the compat namespace; the idempotent-load helper class integration
is a small natural follow-on. D-6 is a strong second because timeout
+ disconnect is the last C-4 primitive without a wiring round.
