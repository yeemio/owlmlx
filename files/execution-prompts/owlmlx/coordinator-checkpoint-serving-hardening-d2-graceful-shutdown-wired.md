# owlmlx Coordinator Checkpoint — Serving Hardening D-2 Graceful Shutdown Wired

## Verdict

- `serving_hardening_d2_graceful_shutdown_lifespan_wired`

The D-2 wiring round is closed. The C-4 scaffold's `GracefulShutdown`
plus `GracefulShutdownConfig` are now installed on the real owlmlx
FastAPI app constructed by `owlmlx.runtime.server.create_app(...)` as
a second `app.router.on_shutdown` handler. The handler is appended
**after** the pre-existing `_stop_runtime_monitor_sampler`
registration. FIFO order on the `app.router.on_shutdown` list means
that on a lifespan shutdown (or real `SIGTERM` against uvicorn) the
background sampler task is stopped first, and only then is
`GracefulShutdown.on_shutdown(...)` awaited to drain the
`GenerationGate` and unload models.

Drain target is the kernel-level `GenerationGate` snapshot exposed at
`runtime.status_dict()["generation_gate"]`. Unload target is the
backend-level `loaded_models` list at
`runtime.status_dict()["backend"]["loaded_models"]`, iterated by
`model_id` through `runtime.unload_model(...)`.

The remaining four C-4 hardening primitives (timeout, error envelope,
metrics endpoint, idempotent `/v1/load`) are **NOT** wired in this
round; each is a separate operator decision in its own future D-*
round.

## What This Checkpoint Is

A wiring marker for one specific primitive. It says: the FastAPI app
that `create_app(...)` returns now has a second `on_shutdown`
lifespan handler — `_graceful_shutdown_drain` — which awaits
`GracefulShutdown.on_shutdown(...)` against runtime-derived gate and
unload callables, and an integration test backs that fact end-to-end
against the real app surface.

It does **not** say:

- the gate ever actually had to drain in production (the lifespan
  handler is now installed; observation of a real long-running
  generation being drained on `SIGTERM` is still the operator
  ergonomics evidence and is not collected here)
- the `gate_idle_timeout_s=30.0` scaffold default is the correct
  fleet-wide value (it is the scaffold default; an operator-tunable
  configuration knob is a deferred D-2.1 round)
- request timeouts are enforced
- a `/metrics` route exists
- error responses use the unified envelope
- `/v1/load` is idempotent
- the existing per-route ad-hoc `req_<uuid4hex>` generation has been
  removed (D-1.1's responsibility)

## What Is Now Frozen Exact

### Modified file: `owlmlx/runtime/server.py`

Two additions:

1. The existing relative-import line
   ```python
   from .serving_hardening import RequestIdMiddleware
   ```
   becomes
   ```python
   from .serving_hardening import GracefulShutdown, GracefulShutdownConfig, RequestIdMiddleware
   ```

2. Inside `create_app(...)`, immediately after the existing two
   lines
   ```python
   app.router.on_startup.append(_start_runtime_monitor_sampler)
   app.router.on_shutdown.append(_stop_runtime_monitor_sampler)
   ```
   a new block is inserted that:
   - constructs `graceful_shutdown = GracefulShutdown(config=GracefulShutdownConfig())`
     using the scaffold defaults
   - defines `_graceful_shutdown_gate_status()`, returning a dict
     copy of `runtime.status_dict()["generation_gate"]`
   - defines `_graceful_shutdown_unload_models()`, iterating
     `runtime.status_dict()["backend"]["loaded_models"]` by
     `model_id` and calling `runtime.unload_model(model_id)`,
     bucketing results into `{"unloaded_model_ids": [...], "failed":
     [...]}`
   - defines `async def _graceful_shutdown_drain()` which awaits
     `graceful_shutdown.on_shutdown(gate_status_callable=...,
     unload_models_callable=...)`
   - calls `app.router.on_shutdown.append(_graceful_shutdown_drain)`

The `_stop_runtime_monitor_sampler` body, signature, and registration
line are **untouched**. No route handler is touched. No other
middleware is added. No exception handler is added. No
`app.state.*` field is renamed, removed, or added.

Diff summary: roughly `+30 -1` lines on `server.py` (one import line
re-written, ~30 lines added for the wiring block and the local
helper definitions).

### New file: `tests/test_serving_hardening_graceful_shutdown_wired.py`

Five integration tests using `fastapi.testclient.TestClient` against
the real `create_app()`-constructed app:

- `test_create_app_succeeds_with_graceful_shutdown_wired` — smoke;
  the app constructs and serves `/healthz` with the new on_shutdown
  handler in place
- `test_graceful_shutdown_handler_is_registered_on_router` —
  `_graceful_shutdown_drain` is in `app.router.on_shutdown` and is a
  coroutine function (so the lifespan runner can `await` it)
- `test_graceful_shutdown_handler_registered_after_sampler_stopper`
  — FIFO sequencing assertion: index of
  `_stop_runtime_monitor_sampler` is strictly less than index of
  `_graceful_shutdown_drain`
- `test_lifespan_shutdown_invokes_graceful_shutdown_on_idle_gate` —
  with `GracefulShutdown.on_shutdown` patched, entering and exiting
  `TestClient(app)` triggers exactly one await on the patched
  coroutine; the recorded gate snapshot is a dict whose `is_active`
  is False under the default FakeBackend
- `test_unload_callable_iterates_loaded_models_via_status_dict` —
  exercises the wiring shape against a stub runtime: iterates
  `status_dict()['backend']['loaded_models']` by `model_id`, calls
  `unload_model(...)` for each, and tolerates a non-ok unload result
  without raising

No uvicorn process is started. No model is loaded. The `FakeBackend`
default is used. The C-4 scaffold's behavior tests
(`test_serving_hardening.py`) and the D-1 wiring tests
(`test_serving_hardening_wired.py`) are untouched and remain
passing.

### Round prompt: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d2-graceful-shutdown-wiring.md`

Records the executor-phase discipline (one import re-write + one
on_shutdown registration block; no removal of the existing sampler
stopper; no other hardening wired; scaffold-default config only; no
doc modification; `TestClient` only) and the four-deliverable
contract.

## Test Counts

The combined sweep
`.venv/bin/python -m pytest tests/test_serving_hardening.py tests/test_serving_hardening_wired.py tests/test_serving_hardening_graceful_shutdown_wired.py -q`
covers:

- `tests/test_serving_hardening.py` — 18 unit tests (C-4 scaffold,
  unchanged)
- `tests/test_serving_hardening_wired.py` — 5 integration tests
  (D-1, unchanged)
- `tests/test_serving_hardening_graceful_shutdown_wired.py` — 5
  integration tests (D-2, new)

Total D-2 sweep: 28 tests across the three files.

## What This Checkpoint Closes

- `GracefulShutdown` is installed as a lifespan `on_shutdown`
  handler on the real owlmlx FastAPI app constructed by
  `create_app(...)`
- the new handler is registered after `_stop_runtime_monitor_sampler`
  on `app.router.on_shutdown`, preserving FIFO order so the
  background sampler task dies first
- the drain reads `runtime.status_dict()["generation_gate"]` as the
  gate snapshot source, and the unload reads
  `runtime.status_dict()["backend"]["loaded_models"]` as the model
  iteration source — both are existing kernel surfaces, not new ones
- the round prompt + checkpoint pair is landed for audit
- `GracefulShutdownConfig` knob exposure (operator-tunable timeout,
  optional unload skip) is **deferred** to D-2.1 (so the wiring round
  itself stays at scaffold-default behavior)

## What This Checkpoint Does Not Claim

- a real long-running generation has been observed surviving
  `SIGTERM` end-to-end on a uvicorn server — that is the operator
  ergonomics evidence and is not collected by this round
- the `gate_idle_timeout_s=30.0` scaffold default is the correct
  fleet-wide value — operators may need to raise it for fleets that
  deliberately allow very long completions
- failed unloads on shutdown are surfaced anywhere outside the
  drain's own return value — the report dict is currently only
  returned to the lifespan runner (and discarded by Starlette's
  default lifespan shape). A structured-log write or
  reclaim-barrier-event hook is a separate D-2.2 follow-on
- Line 4 of the seven-line architectural assessment has moved from
  `partial` to a higher posture — D-2 is one of five remaining
  wiring rounds whose collective completion is the precondition for
  any posture promotion
- any other C-4 primitive (timeout, error envelope, metrics,
  idempotent load) has been wired
- `docs/source-of-truth/serving-hardening-architecture.md` has been
  refreshed to reflect this wiring — that refresh is a separate
  doc-cleanup round

## Side Effects

- `owlmlx/runtime/server.py` is the only existing source file
  modified in this round
- no documentation file is modified
- no test file other than the one new test is added
- `pyproject.toml`, `uv.lock`, `.python-version`, `conftest.py`,
  `README.md`, `tests/test_serving_hardening.py`,
  `tests/test_serving_hardening_wired.py`, and
  `owlmlx/runtime/serving_hardening.py` are unmodified
- the existing dirty tree on `main` (Gemma MTP probe, runtime monitor
  changes, heavy-weight repeatability, native MLX adapter
  modifications, etc.) is untouched
- no new dependency is introduced; `GracefulShutdown` is a plain
  Python class operating only on stdlib `asyncio` and runtime
  callables

## Notable Implementation Choices

- **Import style**: relative import
  `from .serving_hardening import GracefulShutdown, GracefulShutdownConfig, RequestIdMiddleware`
  mirrors the D-1 import shape; we re-wrote one line rather than
  adding a second import line so the relative-import block stays
  single-line and alphabetically grouped.
- **Placement of the registration block**: directly after the
  existing two lines that register the sampler start/stop handlers
  — same locality, easier to audit. Doing it later in `create_app`
  would still be FIFO-correct but harder to spot for reviewers.
- **FIFO ordering relies on `app.router.on_shutdown` being a list
  with `.append` for tail-insertion**. Starlette's `Router` exposes
  `on_shutdown` as a Python `list`, and the lifespan runner iterates
  it in registration order at shutdown. This is asserted directly in
  the new test
  `test_graceful_shutdown_handler_registered_after_sampler_stopper`
  by reading `app.router.on_shutdown` and comparing the indices of
  the two named handlers. If a future Starlette release changes the
  iteration order, the test will catch it; the wiring would need to
  be rebuilt against an explicit `lifespan` context-manager shape.
- **Gate snapshot source**: we read
  `runtime.status_dict()["generation_gate"]` rather than threading
  a direct `GenerationGate` reference through the closure. This
  keeps the wiring decoupled from the gate object's identity and
  makes the wiring testable against a stub runtime that returns a
  synthetic dict.
- **Unload surface choice**: the kernel public method is
  `unload_model(model_id)`, not `unload(model_id)`. The wiring uses
  `unload_model` to match the kernel's actual public surface. The
  iteration source is `status_dict()["backend"]["loaded_models"]`,
  which exists on every backend (FakeBackend or MlxNativeBackend) as
  `[asdict(m) for m in BackendStatus.loaded_models]`.
- **Scaffold defaults preserved**: `GracefulShutdownConfig()` uses
  `gate_idle_timeout_s=30.0`, `unload_models_on_shutdown=True`, and
  `poll_interval_s=0.05`. No new operator knob is exposed in this
  round; the round's discipline forbids a config-knob escalation
  inside a wiring round.
- **Tests use TestClient lifespan only**: no real uvicorn process is
  started; no real `GenerationGate` is observed; the scaffold's
  behavior tests (in `test_serving_hardening.py`) cover that. The
  D-2 wiring tests prove only the registration side effects on the
  real app and the FIFO ordering against the existing handler.

## Capability Matrix State

`docs/source-of-truth/native-mlx-backend-capability-matrix.md` is
**unmodified** in this round. The matrix records MLX backend
capability entry points; HTTP lifespan-handler wiring does not fit
its vocabulary, and serving-surface ownership is governed by
`docs/source-of-truth/serving-hardening-architecture.md` plus the
existing `single-host-orchestration-architecture.md`. No row is
promoted. No row is demoted.

## Seven-line Architectural Assessment

Line 4 — Serving surface (`partial`) remains `partial`. D-2 is one of
five remaining wiring rounds (D-3 error envelope, D-4 metrics, D-5
idempotent load, D-6 timeout, plus D-1.1 per-route id dedup) whose
collective completion is the precondition for moving Line 4 to a
higher posture. Lines 1, 2, 3, 5, 6, 7 are unchanged in this round.

## Next Authorized Round

Two parallel candidates, both deliberate single-item rounds:

### Path D-3 (recommended): Unified Error Envelope Wiring

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d3-unified-error-envelope-wiring.md`
  (to be authored)
- attach `UnifiedErrorEnvelope` (already in
  `serving_hardening.py`) to the FastAPI app's exception-handler
  registry so the native namespace returns the OpenAI-mirroring
  error shape with `request_id` populated from
  `request.state.request_id` for `ok=False` paths
- evidence: focused tests that assert a representative `ok=False`
  path (e.g. unloading a non-loaded model, generating against a
  non-active model) returns the unified envelope shape with the
  expected `error_code`/`http_status`
- evidence-language: "UnifiedErrorEnvelope wired on native error
  paths; `ok=False but HTTP 200` mismatch closed for those routes"

### Path D-4 (parallel): Metrics Endpoint Wiring

- file: `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d4-metrics-endpoint-wiring.md`
  (to be authored)
- attach `MetricsSnapshotExporter` to a `/metrics` route on the
  FastAPI app; the route returns a snapshot of the runtime
  surfaces (gate counters, host pressure, recent generations) in a
  Prometheus-text or stable-JSON shape
- evidence: focused tests that assert the metrics route exists,
  returns the expected content-type and a stable subset of keys

The remaining three hardenings (timeout, idempotent load, per-route
id dedup) each warrant their own dedicated wiring round so that
operator review is per-item.

## Independent / Deferrable Parallel Lanes

- **C-1 cache_manager scaffold** — moves Line 5; landscape map exists
- **C-2 repeatability harness** — moves Line 6; landscape map exists
- **C-3 memory_actuator** — moves Line 3; landscape map exists
- **B-2** sibling candidate admissibility (Qwen3.6-27B / gemma-4-31B-it)
- **B-4** cooperative cancellation real-stream evidence

I recommend the **next round be D-3** because the unified error
envelope is the highest-leverage diagnostic improvement on the
serving surface — paired with the now-installed
`RequestIdMiddleware` (D-1) and `GracefulShutdown` (D-2), it closes
the "operator can correlate a failed inbound request to a specific
in-process error code with a stable shape" loop. D-4 is a strong
second because the metrics endpoint surfaces the gate counters that
the now-installed shutdown drain reads.
