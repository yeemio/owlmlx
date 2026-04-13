# owlmlx Stabilization-1 Upstream Contract Freeze

> Status: Stabilization-1 complete
> Updated: 2026-04-13

## 1. Goal

Stabilization-1 does not reopen replacement-grade staging.

Its purpose is narrower:

- freeze the upstream runtime contract that `owlcoda` and `owlops` can rely on
- harden runtime-only status and restart semantics
- add targeted reliability verification for child-death / restartability failure modes

This round does **not** move control-plane ownership back into `owlmlx`.

## 2. Frozen Consumer Contract Surface

The upstream contract surface now freezes as:

- `GET /v1/runtime/status`
- `GET /healthz`
- `POST /v1/messages`
- runtime-owned truth embedded inside status:
  - inventory
  - budget
  - health
  - restartability

### 2.1 Stable Contract Sections

The following `/v1/runtime/status` sections are now treated as stable upstream contract:

- `contract`
- `summary`
- `health`
- `inventory`
- `budget`
- `restart`

These sections are what `owlcoda` / `owlops` should consume as long-lived runtime truth.

For `GET /healthz`, the stable contract now includes:

- `contract.surface = "owlmlx.healthz"`
- `contract.version = "stabilization1"`
- `runtime`
- `backend_name`
- `ok`
- `readiness`
- `active_model_id`
- `model_count`

### 2.2 Diagnostic Detail Sections

The following sections remain diagnostic detail rather than long-term schema promises:

- `backend.detail`
- `generation_gate`

They remain useful for debugging and operator diagnosis, but should not be treated as
frozen field-by-field compatibility surfaces.

## 3. Dominant Runtime-Only Gaps Closed

### 3.1 `/v1/runtime/status` was useful but not explicit as a frozen contract

Before Stabilization-1, the endpoint returned internal runtime state in a practical but
still implicit shape.

Stabilization-1 adds explicit contract metadata:

- `contract.surface = "owlmlx.runtime.status"`
- `contract.version = "stabilization1"`
- stable vs diagnostic section split

This turns the status surface from "inspectable snapshot" into "explicit upstream contract".

### 3.2 Dead-child restartability existed but was not surfaced as stable runtime truth

Before Stabilization-1, child restart behavior existed inside backend logic, but upstream
consumers had to infer restartability from backend detail.

Stabilization-1 freezes explicit restartability truth:

- `restart.restartable_models`
- `restart.restart_exhausted_models`
- `restart.auto_restart_dead_session`

This lets upper layers distinguish:

- currently healthy
- currently degraded but restartable
- degraded with restart budget exhausted

without re-deriving backend internals.

### 3.3 Restart action results are now machine-readable

`POST /v1/runtime/restart` no longer relies on human-readable message parsing alone.

The result now exposes stable fields:

- `stage`
  - `preflight`
  - `unload`
  - `load`
  - `completed`
- `retryable`

This lets upstream consumers distinguish:

- request was invalid / model not loaded
- restart failed during unload
- restart failed during reload
- restart completed successfully

## 4. Reliability Harness Added

Targeted runtime-only reliability verification now explicitly covers:

- dead child with remaining restart budget -> `restartable_models`
- dead child with exhausted restart budget -> `restart_exhausted_models`
- `/v1/runtime/status` contract presence and versioning
- repeated load -> generate -> restart -> unload cycles
- `/v1/messages` streaming error path returning structured `event: error`
- `/v1/runtime/restart` returning stable `stage` and `retryable` semantics

These are runtime-owned failure modes, not control-plane policy.

## 5. Verification

Verified:

- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py -q`
  - result: `33 passed`
- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_kernel.py -q`
  - result: `15 passed`
- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_status.py -q`
  - result: `6 passed`
- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_mlx_lm_subprocess_backend.py -q`
  - result: `17 passed`

## 6. What Stabilization-1 Proves

- `owlmlx` now exposes an explicit upstream runtime-status contract rather than only an
  implementation snapshot
- restartability is now operator-consumable runtime truth, not only backend internals
- child-death / restart-budget failure modes are now formally pinned by tests

## 7. What Stabilization-1 Does Not Claim

Stabilization-1 does **not** claim:

- control-plane closure
- lifecycle daemon ownership
- operator dashboard ownership
- replacement verdict change
- old platform replaceability flip

Those remain above `owlmlx`.

## 8. Final Verdict

### 8.1 Upstream runtime contract freeze

**Verdict: complete**

### 8.2 Runtime-only reliability hardening

**Verdict: stronger**

### 8.3 Old platform replacement

**Verdict: unchanged — still not yet replaceable**

## 9. Gate Record

### 9.1 What Stabilization-1 actually closed

- `/v1/runtime/status` is now an explicit upstream runtime contract
- `/healthz` is now a small but frozen liveness/readiness contract
- `/v1/runtime/restart` now returns machine-readable failure-stage semantics
- persistent-child restartability is now stable runtime truth rather than backend-only detail
- runtime-only failure modes now have targeted tests:
  - dead child with restart budget remaining
  - dead child with restart budget exhausted
  - repeated restart/load/unload cycles
  - streaming error path

### 9.2 What remains outside owlmlx

The following are still intentionally outside `owlmlx` ownership:

- control-plane policy
- lifecycle daemon and TTL orchestration
- operator dashboard / operator UX
- replacement verdict flip
- old-platform production replacement
