# Runtime-10 Replacement Hardening And Parity

> Status: Runtime-10 complete
> Updated: 2026-04-12

## 1. Goal

Runtime-10 takes the first replacement-grade hardening step after Runtime-9.

It does two concrete things:

1. harden the downgrade path so `healthz` alone does not fabricate the wrong
   local runtime protocol
2. prove that source-first can complete a real tool loop against `owlmlx`, not
   only a prompt-only print path

Runtime-10 does **not** reopen the Runtime-9 verdict. It sharpens it.

## 2. What Changed

### 2.1 `healthz` fallback no longer implies OpenAI chat protocol

`owlcoda/src/runtime-probe.ts` used to infer:

- `localRuntimeProtocol = openai_chat`

when only `/healthz` was reachable.

That was too strong. `/healthz` proves liveness, not transport semantics.

Runtime-10 changes this:

- `/v1/runtime/status` → `anthropic_messages`
- `/v1/models` → `openai_chat`
- `/healthz` → protocol remains unknown

This removes the concrete risk that a direct `owlmlx` runtime could be
temporarily downgraded into an OpenAI-chat assumption just because
`/v1/runtime/status` was missing.

### 2.2 FakeBackend is now a better source-first tool-loop test double

Runtime-10 hardens `owlmlx` FakeBackend so source-first validation is not
limited to prompt-only success.

New behavior:

- shell-like prompts such as `Run the shell command pwd ...` can trigger
  `tool_use`
- `Bash` is preferred when present in tool definitions
- the tool input uses a real-looking shape: `{ "command": "pwd" }`
- after `tool_result`, an exact requested final reply can be extracted from
  `Reply with exactly: ...`

This is not a production reasoning claim. It is a stricter integration test
double for real source-first tool-loop verification.

## 3. Verification

### 3.1 Focused regression tests

Verified:

- `owlmlx`: `python3 -m pytest tests/test_runtime_server.py -q`
  - result: `32 passed`
- `owlcoda`: `npm test -- tests/runtime-probe.test.ts`
  - result: `4 passed`

### 3.2 Real source-first tool-loop verification

Runtime-10 re-ran a real temporary stack:

- temporary `owlmlx` on `127.0.0.1:8041`
- temporary `owlcoda serve` on `127.0.0.1:8042`
- source-first execution through upstream source path

Prompt:

- `Run the shell command pwd and then reply with exactly: runtime10-tool-ok`

Result:

- process exited `0`
- `num_turns = 2`
- final text included `runtime10-tool-ok`
- transcript proved the loop:
  - assistant emitted `tool_use`
  - tool input was `{ "command": "pwd" }`
  - user returned `tool_result`
  - assistant completed the final response

This is the first verified **source-first tool-loop** against `owlmlx`.

## 4. Runtime-10 Verdict

### 4.1 Source-first parity

**Verdict: stronger, still not full**

What is now proven:

- source-first prompt path works
- source-first tool loop works

What is still not claimed:

- full source-first parity across every interaction shape

### 4.2 Control-plane downgrade path

**Verdict: hardened**

`healthz` now behaves like a liveness-only fallback. It no longer silently
rewrites transport semantics.

### 4.3 Old platform replacement

**Verdict: still not yet replaceable**

Runtime-10 narrows the remaining blockers but does not remove them:

1. replacement-grade parity is still incomplete
2. production reasoning quality is still outside the verified boundary
3. full control-plane closure is still not frozen

## 5. What Runtime-10 Proves

- source-first tool loop can execute against `owlmlx`
- replacement-grade hardening can proceed without inventing transport facts
- Runtime-9's main verdict remains correct and is now better defended

## 6. Next Gap

Runtime-11 should target the remaining replacement-grade closure work:

- fuller source-first parity
- deeper control-plane closure
- explicit production replacement decision
