# owlmlx Coordinator Checkpoint — Serving Hardening Scaffold Landed (C-4)

## Verdict

- `serving_hardening_scaffold_landed_primitives_only`

The C-4 scaffold round is closed in **scaffold-grade** form. Six
serving-surface hardening primitives are defined, four supporting
files are landed, and zero changes touched
`owlmlx/runtime/server.py`, `owlmlx/serving.py`, the native MLX
backend adapter, the runtime kernel, the runtime types, the entry
script, `pyproject.toml`, `uv.lock`, or any existing test file.

This is a scaffold foothold for **Line 4 — Serving surface
(`partial`)** in the seven-line architectural assessment recorded at
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` §7.
"Scaffold foothold" is the right word: the scaffold defines the
ownership domain. Closure of Line 4 from `partial` to a higher
posture remains conditional on a follow-up *wiring round* that
actually installs each primitive onto the FastAPI app, plus an
*evidence round* that exercises the wired surface against operator
traffic.

## What This Checkpoint Is

A primitive-ownership marker. It says: there is now a Python module
that holds the middleware/helper/dataclass shapes for six serving
hardenings, and a source-of-truth document that says where those
shapes live, who owns them, and what the deferred wiring round is
expected to do.

It does **not** say:

- the serving surface is hardened
- any HTTP handler in `owlmlx/runtime/server.py` has been changed
- any FastAPI app has had `add_middleware` called on it
- any `lifespan` shutdown drain has been installed
- a `/metrics` route exists
- caller-supplied `x-request-id` is propagated through the runtime
  today
- in-flight generations can be cleanly cancelled today
- HTTP status codes today reflect runtime error semantics
- `/v1/load` is idempotent today

All of those are true only after a wiring round lands on top of this
scaffold.

## What Is Now Frozen Exact

### Module: `owlmlx/runtime/serving_hardening.py`

Pure-stdlib + Starlette-only scaffold module that defines:

- `REQUEST_ID_HEADER = "x-request-id"`
- `RequestIdContext` (frozen dataclass: `request_id`, `inbound`,
  `to_dict`)
- `RequestIdMiddleware(BaseHTTPMiddleware)` — inbound generation,
  state attachment, outbound write; lossless inbound preservation
- `derive_request_id_context(...)` pure helper
- `RequestDisconnectedError(Exception)`
- `RequestTimeoutPolicy` (frozen dataclass: 60.0/600.0/0.5 default
  ceilings)
- `RequestTimeoutHelper.await_with_timeout` — `asyncio.wait_for`
  wrapper, async-native
- `RequestTimeoutHelper.poll_disconnect` — async generator that
  raises `RequestDisconnectedError` on observed disconnect
- `GracefulShutdownConfig` (frozen dataclass: 30.0 / True / 0.05)
- `GracefulShutdown.drain_gate` — observation-only polling of a
  caller-supplied `gate_status_callable`
- `GracefulShutdown.on_shutdown` — drain-then-optional-unload
  orchestrator; accepts sync or async unload callable
- `UnifiedErrorEnvelope` (frozen dataclass: `id`, `error_code`,
  `message`, `request_id`, `http_status`, `object="error"`,
  `to_response_body`, `to_json`)
- `ErrorEnvelopeBuilder.from_runtime_error_code` — static map
  including `invalid_request → 400`, `model_not_loaded → 409`,
  `model_already_loaded → 409`, `backend_error → 502`,
  `memory_pressure → 503`, `request_timeout → 504`,
  `client_disconnected → 499`; unknown codes default to 500
- `ErrorEnvelopeBuilder.from_unexpected` — leak-proof: the
  exception's class name and message do NOT appear in the response
  body
- `MetricsSnapshotExporter.render_prometheus_text` — `io.StringIO`
  rendered Prometheus text-exposition format with `# HELP` /
  `# TYPE` / value lines; counters carry `_total` suffix; missing
  input fields are omitted, NOT zero-filled
- `IdempotentLoadOutcome` (frozen dataclass: `model_id`,
  `already_loaded`, `memory_gb`, `ok`, `to_response_body`)
- `IdempotentLoadHelper.interpret_backend_result` — rewrites
  `error_code == "model_already_loaded"` to
  `already_loaded=True, ok=True`, all other failures pass through

The module imports only stdlib + Starlette pieces that FastAPI
already pulls into the dependency closure. It does NOT import
`fastapi`, `owlmlx.serving`, `owlmlx.runtime.server`, or
`owlmlx.runtime.mlx_native_backend`. The graceful-shutdown drain
takes the gate's status as a callable parameter so that the wiring
round decides at install time which gate is observed.

### Doc: `docs/source-of-truth/serving-hardening-architecture.md`

Ten-section architecture document recording: scope/authorship; why
this module exists (Line 4 of seven-line assessment); explicit
non-goals; ownership boundaries table; per-hardening detail in six
sub-sections; wiring round responsibilities (deferred); explicit
non-coupling to the native-MLX-backend capability matrix; the
no-new-dependency contract; extension points (auth / CORS /
body-size / rate limit / OTel / structured logging / force-cancel);
and what the doc does not claim.

### Tests: `tests/test_serving_hardening.py`

Eighteen tests across six sections, covering middleware behavior
(generation / inbound passthrough / state attach / outbound header /
blank-input handling), timeout helper (timeout raise / under-timeout
return / disconnect polling), graceful shutdown (immediate idle / N
polls until idle / timeout / orchestration order), error envelope
(response shape / runtime error code carries request id /
unknown-code defaults to 500 / unexpected does not leak class), and
the metrics exporter (HELP/TYPE/value lines / native admission
inclusion / native admission omission / missing-field omission).
Tests use `asyncio.run()` for async bodies because the project does
not declare `pytest-asyncio`.

### Round prompt: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-scaffold-landing.md`

Records the executor-phase discipline (no `runtime/server.py`
modification, no new dependency, no wiring, `asyncio.wait_for` only,
`io.StringIO` only) and the five-deliverable contract. Coordinator
review later ran the combined C-x/native scoped pytest sweep and
observed `83 passed, 3 skipped` (plus upstream warnings);
`tests/test_serving_hardening.py` contributed 18 passed tests.

## Capability Matrix State

`docs/source-of-truth/native-mlx-backend-capability-matrix.md` is
**unmodified** in this round. The matrix records MLX backend
capability entry points (KV cache handle, sampler injection, decode
step iterator, etc.); HTTP serving primitives do not fit its
vocabulary, and serving-surface ownership is governed by the new
`serving-hardening-architecture.md` plus the existing
`single-host-orchestration-architecture.md`.

No row is promoted. No row is demoted. Section 3 of the matrix is
read-only.

## Seven-line Architectural Assessment

This round produces a scaffold foothold for **Line 4 — Serving surface
(`partial`)**. Closure to a higher posture is contingent on:

- a *wiring round* that lands `app.add_middleware(...)`,
  `app.add_exception_handler(...)`, `app.router.on_shutdown` (or a
  FastAPI `lifespan` handler), `@app.get("/metrics")`, per-handler
  adoption of `RequestTimeoutHelper`, and `/v1/load` rewrite to use
  `IdempotentLoadHelper` — each landed independently with operator
  review
- an *evidence round* that exercises the wired serving surface
  against either operator traffic or a representative load harness,
  recording `request-id` propagation, shutdown drain timing, and
  `/metrics` ingestion correctness

Lines 1, 2, 3, 5, 6, 7 of the seven-line assessment are unchanged in
this round. Lines 5 (cache/scheduler depth, C-1) and 6 (host-stable
execution confidence, C-2) and 3 (memory governance, C-3) remain
parallel high-leverage candidates for follow-up rounds.

## What This Checkpoint Closes

The serving-hardening *scaffold* round is closed in scaffold-grade
form:

- the module exists, holds the six primitive shapes, and degrades
  gracefully on missing-field inputs (e.g. metrics exporter omits
  rather than zero-fills)
- the architecture document records the ownership boundary
  authoritatively
- the test file backs the module with focused unit tests that do
  not start any real server
- the round prompt and checkpoint are landed for audit

## What This Checkpoint Does Not Claim

- Line 4 of the seven-line assessment has moved from `partial` to
  any higher posture
- the wiring round is scheduled
- any operator deployment has consumed the new primitives
- `prometheus_client` will eventually be added (the no-new-dep
  contract is an ongoing constraint, not a deferred one)
- the HTTP status mapping in `ErrorEnvelopeBuilder` is final; the
  wiring round may narrow per-route
- `GracefulShutdownConfig.gate_idle_timeout_s = 30.0` is suitable
  for every deployment; that is an operator decision per fleet
- the serving surface today supports `/metrics`,
  `x-request-id` propagation, structured error envelopes, idempotent
  load, request timeouts, or graceful shutdown — none of these are
  installed by this round

## Side Effects

- no Python files outside `owlmlx/runtime/serving_hardening.py` and
  `tests/test_serving_hardening.py` were modified
- no documentation files outside
  `docs/source-of-truth/serving-hardening-architecture.md` and the
  two execution-prompt files were modified
- `pyproject.toml`, `uv.lock`, `.python-version`, `conftest.py`,
  `README.md` are unmodified
- the existing dirty tree on `main` (Gemma MTP probe, runtime
  monitor changes, heavy-weight repeatability, native MLX adapter
  modifications, etc.) is untouched

## Next Authorized Round

Two parallel candidates, both deliberate single-item rounds:

### Path D-1 (recommended): Serving Hardening Wiring — Request-id Middleware

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-wiring-request-id.md`
  (to be authored)
- single line in `owlmlx/runtime/server.py`'s `create_app(...)`:
  `app.add_middleware(RequestIdMiddleware)`
- per-handler structured log adoption (read
  `request.state.request_id`)
- evidence: a focused test that asserts a real owlmlx app round-trips
  `x-request-id` correctly
- explicitly does NOT install timeout, shutdown drain, metrics, or
  error envelope in the same round; those are separate operator
  decisions

### Path D-2 (parallel): Serving Hardening Wiring — Graceful Shutdown Drain

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-wiring-graceful-shutdown.md`
  (to be authored)
- attach `GracefulShutdown.on_shutdown(...)` to a FastAPI `lifespan`
  in `create_app(...)` so that `SIGTERM` waits for the
  `GenerationGate` to drain before terminating uvicorn
- evidence: a focused test that simulates `SIGTERM` mid-generation
  and asserts the shutdown report includes `drained=True` after
  generation completes

The remaining four hardenings (timeout, error envelope, metrics,
idempotent load) each warrant their own dedicated wiring round so
that operator review is per-item.

## Independent / Deferrable Parallel Lanes

- **C-1 cache_manager scaffold** — moves Line 5; landscape map exists
- **C-2 repeatability harness** — moves Line 6; landscape map exists
- **C-3 memory_actuator** — moves Line 3; landscape map exists
- **B-2** sibling candidate admissibility (Qwen3.6-27B / gemma-4-31B-it)
- **B-4** cooperative cancellation real-stream evidence

I recommend the **next round be D-1** because it cashes in the most
operator-visible improvement (`x-request-id` round-trip) at the
smallest wiring cost (a single `add_middleware` line plus structured
log adoption) and produces immediate diagnostic value before any
larger wiring lands. D-2 is a strong second because graceful shutdown
is the highest-impact correctness improvement on the serving surface
and benefits every subsequent wiring round by ensuring tests can
reset cleanly.
