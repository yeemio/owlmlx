# Runtime-9 Source-First And Replacement Verdict

> Status: Runtime-9 complete
> Updated: 2026-04-12

## 1. Goal

Runtime-9 closes the gap left open after Runtime-8:

- prove whether `owlcoda` source-first can actually cut over to `owlmlx`
- deepen the first control-plane seam into an operable surface
- freeze a harder replacement verdict instead of another "seam proved" claim

Runtime-9 is complete only if it can answer three questions plainly:

1. can source-first cut over?
2. is the control-plane operable against `owlmlx`?
3. is the old platform replaceable yet?

## 2. Code Changes

Runtime-9 changed `owlcoda`, not `owlmlx` runtime execution semantics.

### 2.1 Local runtime route protocol is now explicit

`owlcoda` local model routing no longer assumes that every local runtime speaks
OpenAI chat completions.

New behavior:

- `localRuntimeProtocol=anthropic_messages`
  - local models route to `${routerUrl}/v1/messages`
  - request body stays in Anthropic Messages format
  - `translate=false`
- `localRuntimeProtocol=openai_chat`
  - local models route to `${routerUrl}/v1/chat/completions`
  - request body is translated to OpenAI chat completions
  - `translate=true`

`auto` remains the default. Runtime-9 sets the effective protocol from runtime
surface probing.

### 2.2 Runtime probe is now authoritative for local runtime detection

`probeRuntimeSurface()` now derives:

- source (`runtime_status`, `models`, `healthz`, `none`)
- model ids
- readiness
- backend health
- inferred local runtime protocol

For `owlmlx`:

- `/v1/runtime/status` succeeds
- inventory entries provide model ids
- effective local runtime protocol becomes `anthropic_messages`

### 2.3 Preflight and server health now consume runtime truth

`owlcoda` preflight and server startup no longer assume that `/v1/models` is
the only meaningful local runtime surface.

They now consume runtime truth in this order:

1. `/v1/runtime/status`
2. `/v1/models`
3. `/healthz`

This lets `owlcoda` treat direct `owlmlx` as a first-class local runtime,
instead of forcing it through old router assumptions.

## 3. Verification Setup

Runtime-9 verification used a real temporary stack:

- temporary `owlmlx` FastAPI server on `127.0.0.1:8041`
- temporary `owlcoda serve` proxy on `127.0.0.1:8042`
- source-first execution via upstream Claude Code source tree
- isolated temporary config pointed at `owlmlx`
- local model route protocol left at `auto` so runtime probe had to decide

The `owlmlx` server used `FakeBackend` and a pre-loaded model id:

- configured model id: `runtime9-local`
- backend model id: `runtime9-backend`

## 4. What Was Verified

### 4.1 Source-first prompt path can cut over to `owlmlx`

A real source-first print invocation completed successfully through the full
stack:

`upstream source-first -> owlcoda serve -> owlmlx /v1/messages`

Verified result:

- command exited `0`
- request returned a JSON result payload
- response came back through the source-first path, not native/headless

This is the first verified source-first cutover into `owlmlx`.

### 4.2 Control-plane is operable against direct `owlmlx`

`owlcoda launch --dry-run --config <temp-config>` was run against direct
`owlmlx`.

Verified result:

- doctor detected `http://127.0.0.1:8041` via `runtime_status`
- doctor reported readiness and model count correctly
- dry-run concluded:
  - environment looks good
  - ready to launch

This proves the first control-plane layer is operable against direct `owlmlx`,
not only against the old router topology.

## 5. Runtime-9 Verdict

### 5.1 Source-first cutover verdict

**Verdict: can cut over**

Meaning:

- source-first prompt path is verified against direct `owlmlx`
- local route selection can use Anthropic Messages semantics for `owlmlx`
- the path is no longer blocked by old `/v1/chat/completions` assumptions

Non-claim:

- Runtime-9 does **not** claim full source-first tool-loop parity was
  independently proven in this round

### 5.2 Control-plane verdict

**Verdict: operable**

Meaning:

- runtime probe, preflight, doctor, and dry-run can reason about direct
  `owlmlx`
- direct `owlmlx` no longer looks like a broken router just because
  `/v1/runtime/status` is the richer truth surface

Non-claim:

- Runtime-9 does **not** claim full production control-plane closure

### 5.3 Old platform replacement verdict

**Verdict: not yet replaceable**

Reasons:

1. source-first prompt path is proven, but full source-first parity is not yet
   frozen as complete across all interaction shapes
2. control-plane is operable, but not yet complete enough to call production
   replacement done
3. production backend reasoning quality, SLO posture, and old platform
   replacement closure are still outside the verified boundary

This is a real verdict, not a soft stage label.

## 6. What Runtime-9 Proves

- `owlcoda` can route local Anthropic Messages traffic to direct `owlmlx`
- `owlcoda` source-first prompt path can run against `owlmlx`
- `owlcoda` control-plane can operate against direct `owlmlx`
- Runtime-9 closes the question "can source-first reach owlmlx at all?" with a
  yes

## 7. What Runtime-9 Does Not Prove

- full source-first parity across every interaction pattern
- production backend quality parity
- full control-plane migration
- old platform production replacement

## 8. Next Gap

Runtime-10 should target the remaining replacement-grade questions:

- fuller source-first parity
- deeper control-plane closure
- explicit old-platform replacement decision on production criteria
