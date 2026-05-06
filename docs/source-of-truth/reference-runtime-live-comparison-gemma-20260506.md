# Reference Runtime Live Comparison - Gemma 2026-05-06

> Status: authoritative live evidence note
> Scope: Gemma-only same-host short-prompt comparison against local `oMLX` and
> `vMLX` reference runtimes
> Non-goal: parity claim, replacement claim, or Qwen/DeepSeek coverage

## Summary

This run closes one real execution loop for the current
`reference_runtime_comparison_missing` blocker, but only for a narrow Gemma
workload:

- host: `Mac17,6-arm64-macOS-26.4.1-128GB`
- model: `gemma-4-31B-it`
- model path: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- prompt: `In one short sentence, define local AI.`
- prompt hash:
  `sha256:d394e1ea7857e2ca0bb2859ed62a4fc7782534cbbab9aca64c9f7f9fd38090e4`
- decode: `max_tokens=64`, `temperature=0`
- repeats: `2`

The honest outcome is:

| Reference | Verdict | owlmlx measurement | Reference measurement | Read |
|---|---:|---:|---:|---|
| `oMLX` | `rejected` | TPS `3.7212`, TTFT `8365.658ms`, peak RSS `53963571200` | reference completed `0/2`; peak RSS `53200093184` before failure | oMLX generated tokens in attempt 1, then the server disconnected/restarted around unload/lifecycle; no clean two-repeat measured record |
| `vMLX` | `measured` | TPS `3.7468`, TTFT `8225.989ms`, peak RSS `54586949632` | TPS `3.8304`, TTFT `8306.498ms`, peak RSS `55705976832` | vMLX is essentially neck-and-neck on this narrow reasoning-aware Gemma stream workload |

This supports saying:

- `owlmlx` can stand in the same short-prompt Gemma arena as `vMLX` on this
  host/workload.
- `oMLX` remains a lifecycle/reference-run blocker for this exact controlled
  two-repeat run, despite producing visible text in attempt 1.
- This does not remove the broader `reference_runtime_comparison_missing`
  blocker for Qwen27, Qwen35, DeepSeek, longer prompts, multi-turn workloads,
  or final-answer quality.

This does not support saying:

- `parity`
- `replacement-ready`
- `equivalent`
- `matches oMLX`
- `matches vMLX` outside this narrow workload

## Evidence Roots

Primary evidence root:

`files/evidence/owlmlx/comparative-evidence/20260506T030122Z-gemma-current-reference-comparison/`

Important sub-runs:

- `omlx-livepid-run/`
  - `live-ledger.jsonl`
  - `run/manifest.json`
  - `run/omlx_attempt1.stdout.txt`
  - `run/omlx_attempt1.stderr.txt`
  - `run/omlx_attempt2.stderr.txt`
  - `omlx-home-server-log-tail.txt`
  - `omlx-home-crash-log.txt`
  - `post-run-omlx-models-status.json`
  - `post-run-owlmlx-healthz.json`
- `vmlx-controlled-run/`
  - content-only client rejected with `first_token_latency_unobservable`
  - useful as proof that default vMLX Gemma parser does not surface `content`
    for this prompt through the original client
- `vmlx-reasoning-aware-run/`
  - `live-ledger.jsonl`
  - `run/manifest.json`
  - `run/vmlx_attempt1.stdout.txt`
  - `run/vmlx_attempt2.stdout.txt`
  - `vmlx-server.log`
  - `post-run-owlmlx-healthz.json`
  - `post-run-8064-listeners.txt`

## oMLX Result

The controlled oMLX live-PID run used the already-running local oMLX service:

`python -m omlx.cli serve --model-dir /Users/yeemio/AI/Agent/models --port 8001 --paged-ssd-cache-dir /Users/yeemio/AI/Agent/.omlx-cache --hot-cache-max-size 8GB`

The first oMLX attempt produced visible streamed text:

`Local AI is artificial intelligence that runs directly on a user's own hardware rather than on a remote cloud server.`

But the attempt exited non-zero:

- attempt 1 stderr: `RemoteDisconnected: Remote end closed connection without response`
- attempt 2 stderr: `URLError: <urlopen error [Errno 61] Connection refused>`
- oMLX PID changed during the run, indicating service restart
- oMLX server log recorded repeated swap-safe settle barrier warnings
- oMLX crash log recorded `Fatal Python error: Aborted` around scheduler /
  unload / shutdown paths

Therefore the official record is correctly `verdict_grade=rejected`, not
`measured`.

This is a reference-runtime lifecycle failure for this workload, not proof that
oMLX cannot generate Gemma text.

## vMLX Result

The vMLX model preflight was real:

- `vmlx_engine.cli doctor /Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- model detected as `Gemma4ForConditionalGeneration (gemma4)`
- `30.1B` parameters
- `58.3GB` weight files
- inference check passed

The first content-only comparative run rejected because the client did not see
`delta.content`. The vMLX server log showed the default parser selection:

- tool parser: `gemma4`
- reasoning parser: `gemma4`

The reasoning-aware rerun consumed `delta.reasoning_content` / `delta.reasoning`
as observable stream output and produced a schema-valid `measured` record.

Important caveat: the observed vMLX stdout is reasoning-style trace text, not a
clean final answer. The performance measurement is valid for stream mechanics,
but answer-quality parity is not established.

## Operational Read

For Gemma short prompt on this host:

- `vMLX` is the best currently measured peer reference.
- `oMLX` needs a lifecycle-stable rerun before it can be used as a clean
  measured reference for this workload.
- `owlmlx` is not obviously behind vMLX on this narrow measurement, but still
  has Gemma final-channel / reasoning cleanup caveats.

Next executable closure should not jump to mechanism claims. It should run
the same controlled evidence pattern for:

1. `Qwen3.6-27B`
2. `Qwen3.6-35B-A3B`
3. one longer Gemma prompt that requires final-answer quality validation
