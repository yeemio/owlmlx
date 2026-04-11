# Runtime-7 OwlCC Cutover Verification

> Status: complete
> Updated: 2026-04-11
> Scope: first real `owlcc` cutover verification against `owlmlx /v1/messages`

## 1. Why Runtime-7 Exists

Runtime-6 completed the first Anthropic-compatible entrypoint seam:

- `POST /v1/messages`
- `POST /v1/messages/count_tokens`
- Anthropic SSE event semantics
- minimal output-side `tool_use`

That was still protocol-level proof. It did not yet prove that a real Owl
consumer could point at `owlmlx` and complete an actual tool loop.

Runtime-7 closes that gap by verifying `owlcc` against `owlmlx` directly.

## 2. What Was Verified

`owlcc run` was executed with a temporary direct-endpoint config:

- `routerUrl = http://127.0.0.1:8037`
- model endpoint = `http://127.0.0.1:8037`
- model id = `owlmlx-fake-cutover`

`owlmlx` was started locally from `owlmlx.runtime.server:create_fake_app` and
the model was preloaded through `POST /v1/load`.

The real verification path was:

`owlcc run --config ... --model owlmlx-fake-cutover --prompt ... --json`

This exercised:

- `owlcc` preflight against `owlmlx /healthz`
- `owlcc` direct endpoint routing to `owlmlx /v1/messages`
- Anthropic non-stream request shape
- Anthropic `tool_use -> tool_result -> continue` loop
- final response return to `owlcc`

## 3. Verification Result

The cutover request completed successfully with `exit_code = 0`.

Observed transcript shape:

- first assistant response: `tool_use`
- `owlcc` executed the requested tool
- tool execution returned a structured `tool_result`
- second assistant response completed normally

The concrete observed result was intentionally minimal:

- `FakeBackend` emitted a deterministic `tool_use` for `Bash`
- the generated tool input did not satisfy OwlCC's `Bash` contract
- OwlCC still executed the tool path, captured the resulting tool error, sent
  back `tool_result`, and `owlmlx` completed the loop

This is sufficient to prove:

- Anthropic request compatibility is real, not synthetic
- `tool_use` stop semantics are understood by `owlcc`
- `tool_result` return traffic is accepted by `owlmlx`
- `owlcc` can complete one full assistant/tool/assistant cycle against
  `owlmlx`

## 4. Required Runtime-7 Hardening

One small Runtime-7 hardening step was required for realistic cutover
verification:

- `FakeBackend` now stops returning `tool_use` once a prompt already contains a
  `[tool_result:...]` marker

Without that behavior, a real `owlcc` tool loop would have remained stuck in a
fake infinite `tool_use` cycle and the cutover test would not have been
meaningful.

This is not a claim of real backend tool reasoning. It is a cutover-valid test
double behavior.

## 5. What Runtime-7 Proves

Runtime-7 proves:

- `owlmlx` is no longer only Anthropic-compatible in shape
- `owlmlx` can now serve as a real direct endpoint for `owlcc`
- the first Owl ecosystem consumer can complete a real tool-loop cutover path

## 6. What Runtime-7 Does Not Yet Prove

Runtime-7 does not yet claim:

- `owlcoda` full interactive cutover
- full Claude Code compatibility
- full Anthropic beta surface parity
- real-backend tool selection and tool argument reasoning
- production cutover of the old platform

Runtime-7 is the first real consumer cutover verdict, not final platform
replacement.
