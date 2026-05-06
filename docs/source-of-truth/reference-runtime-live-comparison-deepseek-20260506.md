# Reference Runtime Live Comparison - DeepSeek 2026-05-06

> Status: authoritative live evidence note
> Scope: same-host short-prompt comparison attempt for
> `DeepSeek-V4-Flash-2bit-DQ` against local `oMLX` and `vMLX` reference
> runtimes
> Non-goal: parity claim, replacement claim, DeepSeek loader adoption, long
> context coverage, or using the official FP8 reference weights as a runnable
> local artifact

## Summary

This round extends the live comparative harness to the practical DeepSeek V4
MLX artifact that exists on this host:

`/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ`

Shared workload:

- host: `darwin-arm64-m3-ultra-128gb`
- prompt: `In one short sentence, define local AI.`
- prompt hash:
  `sha256:d394e1ea7857e2ca0bb2859ed62a4fc7782534cbbab9aca64c9f7f9fd38090e4`
- decode: `max_tokens=64`, `temperature=0`
- repeats: `2`
- cumulative ledger:
  `files/evidence/owlmlx/comparative-evidence/cumulative-ledger.jsonl`
- evidence root:
  `files/evidence/owlmlx/comparative-evidence/20260506T053916Z-deepseek-reference-closure/`

The honest outcome is:

| Model | Reference | Verdict | owlmlx measurement | Reference measurement | Read |
|---|---|---:|---:|---:|---|
| `DeepSeek-V4-Flash-2bit-DQ` | `oMLX` | `rejected` | completed `0/2`; peak RSS `183205888` | completed `0/2`; peak RSS `177389568` | Both lanes failed before observable first token; Homebrew oMLX `0.3.4` sidecar reached the model directory but failed with `Model type deepseek_v4 not supported.` |
| `DeepSeek-V4-Flash-2bit-DQ` | `vMLX` | `rejected` | completed `0/2`; peak RSS `189677568` | completed `0/2`; peak RSS `169328640` | vMLX exited before ready with the same `deepseek_v4` loader unsupported failure. |

This supports saying:

- DeepSeek is no longer an untested `reference_runtime_comparison_missing`
  bucket; it has same-harness rejection evidence.
- The local DeepSeek 2bit-DQ artifact is present and structurally inspectable.
- Current stock `owlmlx`, Homebrew `oMLX 0.3.4`, and the local `vMLX` probe
  environment all lack active `deepseek_v4` loader support for this artifact.
- The blocker is runtime-loader support, not artifact integrity.
- Unsupported-load attempts currently dirty 8066 backend health until the
  service is restarted; this is a lifecycle stability gap.

This does not support saying:

- DeepSeek performance was measured.
- DeepSeek replacement coverage is closed.
- The official FP8/mixed DeepSeek artifact is runnable on this host.
- oMLX or vMLX can never support DeepSeek V4; the statement is limited to the
  current local reference environments used here.

## Evidence Roots

Primary evidence root:

`files/evidence/owlmlx/comparative-evidence/20260506T053916Z-deepseek-reference-closure/`

Important sub-runs:

- `deepseek-omlx-run/run/`
  - `manifest.json`
  - `commands.json`
  - `summary.md`
  - `owlmlx_attempt*.stdout.txt`
  - `omlx_attempt*.stderr.txt`
  - `omlx_attempt*.rss.jsonl`
  - `omlx-server.log`
- `deepseek-vmlx-run/run/`
  - `manifest.json`
  - `commands.json`
  - `summary.md`
  - `vmlx_attempt*.stderr.txt`
  - `vmlx_attempt*.rss.jsonl`
  - `vmlx-server.log`
- post-run probes:
  - `post-run-8066-healthz-dirty.json`
  - `post-run-8066-runtime-status-dirty.json`
  - `post-restart-8066-healthz.json`
  - `post-restart-8066-runtime-status.json`
  - `post-run-8063-listeners.txt`
  - `post-run-8064-listeners.txt`
  - `post-run-8001-models.json`
  - `post-run-8001-listeners.txt`

## Local Artifact Boundary

The local DeepSeek candidates found on this host are:

- `/Users/yeemio/AI/Agent/model-candidates/deepseek-ai/DeepSeek-V4-Flash`
  - official FP8/mixed reference artifact
  - useful for patch/reference work
  - not the local runnable MLX comparison target in this round
- `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ`
  - practical MLX pressure candidate
  - `90G`, 19 safetensor shards
  - selected for this evidence round
- `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-4bit`
  - `141G`, 33 safetensor shards
  - known host-pressure/size risk and not selected for this closure round

The 2bit-DQ config reports `model_type=deepseek_v4`. The current owlmlx
runtime venv has `mlx_lm.models.deepseek_v3` and `mlx_lm.models.deepseek`, but
not `mlx_lm.models.deepseek_v4`.

## oMLX Result

The already-running port `8001` Homebrew oMLX service does not expose DeepSeek;
its `/v1/models` list contains:

- `Qwen3.6-27B`
- `Qwen3.6-35B-A3B`
- `gemma-4-31B-it`

To avoid disturbing that service, this run used a sidecar Homebrew oMLX process
on `8063` pointed at:

`/Users/yeemio/AI/Agent/model-candidates/mlx-community`

The sidecar discovered enough to attempt loading
`DeepSeek-V4-Flash-2bit-DQ`, but both attempts failed with:

`ValueError: Model type deepseek_v4 not supported.`

This is an original Homebrew oMLX `0.3.4` result, not an owlmlx fork result.

## vMLX Result

The local vMLX probe environment can inspect the artifact metadata, but the
actual serve path fails before readiness:

`ValueError: Model type deepseek_v4 not supported.`

The sidecar investigation also found:

- `vmlx 1.3.35`
- `mlx-lm 0.31.2`
- `mlx 0.31.1`
- `mlx_lm.models.deepseek_v4` missing
- vMLX registry lookup for the 2bit path resolves to `family=unknown`

This is a reference-runtime loader blocker, not a measured comparison.

## owlmlx Lifecycle Finding

The owlmlx attempts also failed before observable first token. The immediate
post-run health was dirty:

- `/healthz`: `ok=false`
- `readiness=blocked`
- `backend_error=ValueError: Model type deepseek_v4 not supported.`

An explicit `/v1/unload` for the failed path returned `model_not_loaded`, so it
did not clear backend error state. 8066 was restarted and returned to clean
idle:

- `/healthz`: `ok=true`
- `readiness=degraded`
- `active_model_id=null`
- `backend_error=null`

The restarted 8066 process is running under tmux session
`owlmlx-8066-runtime-monitor` with the comparative, Model RC, runtime-test, and
runtime-monitor trend ledgers attached.

This lifecycle behavior is a real gap. Unsupported model-family loads should
be rejected as unsupported without dirtying post-run backend health.

## Operational Read

For DeepSeek V4 on this host:

- the right current MLX artifact for runtime pressure is
  `mlx-community/DeepSeek-V4-Flash-2bit-DQ`;
- the current reference comparison result is `rejected`, not `measured`;
- the next useful runtime-owned closure is not performance tuning, but an
  explicit DeepSeek V4 loader/support gate:
  - either adopt/prove a licensed `deepseek_v4` loader path;
  - or reject the family pre-load with a clean `unsupported_model_family`
    verdict that keeps 8066 health clean.
