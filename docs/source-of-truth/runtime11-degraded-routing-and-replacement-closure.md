# Runtime-11 Degraded Routing And Replacement Closure

> Status: Runtime-11 complete
> Updated: 2026-04-12

## 1. Goal

Runtime-11 closes the remaining replacement-grade ambiguity left after
Runtime-10:

- when `owlcoda` is in `localRuntimeProtocol=auto`
- and only `/healthz` is reachable
- and the target model is local

the system must not silently guess `openai_chat` and route requests to
`/v1/chat/completions`.

Runtime-11 is complete only if this state becomes explicit, fail-closed, and
visible in both preflight and request handling.

## 2. What Changed

### 2.1 Local protocol ambiguity now fails closed

`owlcoda/src/model-registry.ts` now treats unresolved local protocol as a real
error condition.

New behavior:

- endpoint-based models still route directly to `${endpoint}/v1/messages`
- explicit `localRuntimeProtocol=anthropic_messages` still routes local models
  to `${routerUrl}/v1/messages`
- explicit `localRuntimeProtocol=openai_chat` still routes local models to
  `${routerUrl}/v1/chat/completions`
- `localRuntimeProtocol=auto` with no richer runtime surface no longer falls
  through to `/v1/chat/completions`

Instead, route resolution raises a dedicated
`LocalRuntimeProtocolUnresolvedError`.

### 2.2 Preflight now blocks healthz-only local routing

`owlcoda/src/preflight.ts` now distinguishes:

- runtime truth known enough to route
- router merely alive

If the router is reachable only via `/healthz` and local model routing still
depends on `auto`, preflight returns:

- router status: `blocked`
- overall status: `blocked`
- summary: `Cannot proceed: Local runtime protocol unresolved`

This upgrades the Runtime-10 liveness-only rule into a replacement-grade launch
decision.

### 2.3 `/v1/messages` now reports unresolved protocol explicitly

If request handling reaches route resolution without an explicit local runtime
protocol, `owlcoda` now returns a structured Anthropic-style API error instead
of silently targeting the OpenAI chat surface.

This preserves the Runtime-10 rule at request time, not only at probe time.

## 3. Verification

### 3.1 Focused regression tests

Verified:

- `owlcoda`: `npm test -- tests/model-registry.test.ts tests/runtime-probe.test.ts`
  - result: `39 passed`

These tests prove:

- `anthropic_messages` still routes to `/v1/messages`
- `auto` now throws for unresolved local routing
- `/healthz` fallback still leaves protocol unknown

### 3.2 Build verification

Verified:

- `owlcoda`: `npm run build`
  - result: success

### 3.3 Explicit degraded-routing check

A direct Node verification against built output confirmed:

- `/v1/runtime/status` unavailable
- `/v1/models` unavailable
- `/healthz` reachable
- local model present

Result:

- `checkRouterHealth(...)` returned `status = blocked`
- detail reported `local runtime protocol unresolved`

This is the exact replacement-grade downgrade case Runtime-11 was meant to
close.

## 4. Runtime-11 Verdict

### 4.1 Degraded routing

**Verdict: closed**

`owlcoda` no longer silently invents a transport protocol when only liveness is
known.

### 4.2 Source-first parity

**Verdict: stronger, still not full**

Source-first is now protected from the specific degraded-routing misroute that
could previously send local traffic down the wrong compatibility path.

This is a routing-closure improvement, not a claim of full feature parity.

### 4.3 Control-plane closure

**Verdict: stronger**

The control-plane now distinguishes:

- runtime alive
- runtime routeable

That distinction is necessary for an honest replacement decision.

### 4.4 Old platform replacement

**Verdict: still not yet replaceable**

Runtime-11 removes one of the remaining downgrade ambiguities, but does not yet
prove:

1. full source-first parity
2. full production control-plane closure
3. production backend quality parity
4. old platform replacement at operations level

## 5. What Runtime-11 Proves

- `healthz` alone is no longer enough to cause an implicit OpenAI route
- replacement-grade routing now fails closed instead of guessing
- the replacement verdict remains honest and better defended

## 6. Next Gap

Runtime-12 should target final replacement-grade closure:

- remaining source-first parity gaps
- fuller control-plane replacement criteria
- final replaceable / not-replaceable verdict with explicit blocker list
