# Coordinator Checkpoint — Repeatability Stream Terminal Integrity Closed

Date: 2026-05-10

Verdict: `repeatability_stream_terminal_integrity_closed_for_qwen27_n20`

## Scope

This round only addressed the dominant blocker
`repeatability_stream_terminal_integrity`.

It did not claim replacement-grade, public readiness, continuous batching,
cache reuse, TTFT optimization, or output-quality parity.

## Root Cause

The N=20 Qwen27 campaign exposed stdout framing corruption while the model was
still streaming terminal records. The decisive diagnostic was a malformed line
where runtime-owned terminal JSON was joined with a health/status `ping`
response:

- `runtime_owned_terminal_boundary` joined with terminal notice JSON
- `terminal_notice` joined with `{"action": "ping", ...}`

This proved the bug was not a model problem. It was shared child stdout reader
contention: stream generation held `stream_stdout_lock`, but ordinary
`_exchange()` calls used by status/health probes did not.

## Fix

`MlxLmSubprocessBackend._exchange()` now acquires
`session.stream_stdout_lock` before writing a non-stream request and reading
the child response. Stream and non-stream exchanges now share one stdout
reader discipline.

The prior broad non-JSON skip path was also tightened:

- benign non-JSON child stdout is capped and skipped with diagnostics
- JSON-looking transport corruption becomes an error, not success
- a malformed prefix with an embedded complete terminal payload can be
  recovered only when the embedded payload parses exactly
- diagnostics are stored in capped ring buffers, not an unbounded list

## Regression

Focused regression:

```bash
uv run pytest tests/test_mlx_lm_subprocess_backend.py tests/test_repeatability_campaign_harness.py -q
```

Result:

- `74 passed`

New targeted coverage includes:

- benign non-JSON stdout remains skippable
- corrupt JSON terminal records are not marked success
- recoverable embedded terminal payloads are classified and recovered
- diagnostics are capped
- status/health probes wait for `stream_stdout_lock` during stream terminal
  drain

## Live Evidence

8066 was restarted on the patched worktree.

Pre-fix N=20 attempt:

- `18/20 repeats succeeded`
- `failure_count=2`
- `verdict=blocked`
- `blockers=["generation_error", "live_repeated_run_incomplete"]`
- transport diagnostics showed terminal JSON joined with `ping`
- post-run health clean

Post-fix N=20 attempt:

- `20/20 repeats succeeded`
- `failure_count=0`
- `post_health_clean=True`
- `transport diagnostics=[]`
- `verdict=needs_optimization`
- `blockers=["high_variance_unstable"]`

Ledger:

`files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`

Runtime after campaign:

- `/healthz`: `ok=true`, `readiness=degraded`, `model_count=0`
- `/v1/runtime/status`: backend healthy, no loaded model, no stream transport
  diagnostics

## Current Boundary

Closed:

- token-after-terminal-before JSON/framing error for Qwen27 N=20 campaign
- health/status probe stdout contention during stream terminal drain
- unbounded non-JSON line accumulation
- silent success on JSON-looking stdout corruption

Still not closed:

- high TTFT/TPS variance
- stable repeatability label
- output quality/profile parity
- cache scheduler depth beyond `serial_single_worker`
- native backend promotion into serving path

## Next Dominant Gap

`repeatability_variance_stabilization`

Recommended next execution goal:

1. Fix repeatability timing math so per-repeat TPS cannot be inflated by
   terminal bookkeeping artifacts.
2. Record per-repeat TTFT/TPS samples in a campaign evidence artifact, not only
   aggregate ledger fields.
3. Separate cold first-run, warm child reuse, and health-probe interference in
   the N=20 campaign.
4. Re-run Qwen27 N=20 and require:
   - `20/20 repeats succeeded`
   - `failure_count=0`
   - `post_health_clean=True`
   - transport diagnostics empty
   - stability label no worse than `acceptable`, or an explicit remaining
     variance blocker with per-repeat evidence.
