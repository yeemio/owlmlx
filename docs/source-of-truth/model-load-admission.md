# owlmlx Model Load Admission

> Status: authoritative
> Updated: 2026-05-05
> Scope: runtime-owned model-level load admission projection from visibility,
> model profile, latest Model RC peak RSS, current budget, host pressure, and
> recovery barriers.

## 1. Purpose

This surface answers one narrow question:

**Given current runtime truth, should `owlmlx` attempt to load a specific
model now?**

It exists because same-host model optimization cannot be managed from global
budget status alone. OwlOps needs model-specific admission truth that explains
whether a model is blocked by visibility, recent Metal-OOM cooldown, host
pressure, missing peak-RSS evidence, or known peak-RSS budget pressure.

## 2. Owned Surface

Runtime module:

- `owlmlx/model_load_admission.py`

HTTP surface:

- `GET /v1/runtime/model-load-admission`
- optional query: `model_id=<id>`
- `POST /v1/runtime/host-pressure-sample`
  - explicit operator action that refreshes the cached host-pressure sample
    without loading a model

Contract:

- `surface = "owlmlx.model_load_admission"`
- `version = "v1"`

## 3. Inputs

The builder consumes only runtime-owned truth:

- `/v1/runtime/status`
  - budget headroom
  - host-pressure diagnostic sample
  - Metal-OOM cooldown state
  - stale subprocess registration recovery barrier
  - current loaded models
- `owlmlx.runtime.model_visibility`
  - registered and visible model ids
  - visibility block reasons
- `owlmlx.model_profile`
  - profile id and family for the model id
- `owlmlx.model_release_candidate_record`
  - latest known `peak_resident_set_bytes` for the model id
  - latest evidence pointer and caveats

## 4. Admission Decisions

Supported decisions:

- `admit`
  - model is visible
  - no recovery / cooldown / host-pressure hard barrier is active
  - latest known peak RSS fits current budget headroom
  - a host-pressure sample is present and not blocking
- `warn`
  - the load can be attempted, but host pressure is near warning threshold or
    projected headroom is low
- `blocked`
  - visibility is blocked, known peak exceeds current budget, Metal-OOM
    cooldown is active, host pressure is blocked, or stale registrations must
    be cleaned
- `already_loaded`
  - no new load admission is required
- `unknown`
  - required truth is missing, most commonly latest peak RSS or current
    host-pressure sample

Supported budget projections:

- `fits`
- `fits_warning`
- `exceeds`
- `already_loaded`
- `unknown`

## 5. Honest Boundary

This surface does not:

- load a model
- sample private Metal allocator state
- run pressure-ranked eviction
- retry, restart, quarantine, or remediate
- make any release-ready / parity / replacement / production-grade claim

It is a projection layer. The actual safety gate remains in
`RuntimeKernel.load_model(...)`, which still performs load-time host-pressure
sampling before backend load begins.

## 6. Why Host Pressure Can Stay Unknown

`/v1/runtime/status` does not shell out on every read. The host-pressure sample
is cached from load-admission time. Therefore, if no recent load attempt has
sampled host pressure, the admission surface must return `unknown` rather than
pretending that budget-only projection is enough.

That is intentional. OwlOps may display:

- budget projection: `fits` / `fits_warning` / `exceeds`
- admission decision: `unknown`
- reason: `host_pressure_sample_missing`

## 7. Operator Sampling Rule

Before a supervised large-model Model RC run, operators should call:

- `POST /v1/runtime/host-pressure-sample`
- `GET /v1/runtime/model-load-admission?model_id=<id>`

The Model RC runner records these as per-repeat evidence artifacts:

- `repeat-XX-host-pressure-sample.json`
- `repeat-XX-model-load-admission-before.json`

If the admission decision is `blocked`, the runner must stop before
`POST /v1/load`. If the decision is `unknown`, the runner may continue only as
an explicitly supervised evidence run and must preserve the unknown blocker in
the ledger.

## 8. OwlOps Consumption Rule

OwlOps may render this surface as an optimization radar, but must not convert
`admit` or `warn` into a user-facing release claim. `admit` only means:

> the runtime-owned load-admission projection says a load attempt is currently
> allowed under known truth.

It does not say the model is fast enough, high quality enough, or broadly
application-ready.
