# Reference Runtime Live Comparison - Qwen27 and Qwen35 2026-05-06

> Status: authoritative live evidence note
> Scope: same-host short-prompt comparison for `Qwen3.6-27B` and
> `Qwen3.6-35B-A3B` against local `oMLX` and `vMLX` reference runtimes
> Non-goal: parity claim, replacement claim, DeepSeek coverage, long-context
> coverage, or final-answer quality closure

## Summary

This round extends the live comparative harness from the Gemma-only run to the
two Qwen mainline models. It also hardens the runner so external reference RSS
sampling can follow PID drift through both refreshed PID files and live listener
ports.

Shared workload:

- host: `Mac17,6-arm64-macOS-26.4.1-128GB`
- prompt: `In one short sentence, define local AI.`
- prompt hash:
  `sha256:d394e1ea7857e2ca0bb2859ed62a4fc7782534cbbab9aca64c9f7f9fd38090e4`
- decode: `max_tokens=64`, `temperature=0`
- repeats: `2`
- cumulative ledger:
  `files/evidence/owlmlx/comparative-evidence/cumulative-ledger.jsonl`
- evidence root:
  `files/evidence/owlmlx/comparative-evidence/20260506T040009Z-qwen27-qwen35-reference-closure/`

The honest outcome is:

| Model | Reference | Verdict | owlmlx measurement | Reference measurement | Read |
|---|---|---:|---:|---:|---|
| `Qwen3.6-27B` | `oMLX` | `measured` | TPS `5.4482`, TTFT `4143.916ms`, peak RSS `54420045824` | TPS `2.8127`, TTFT `4848.995ms`, peak RSS `55013818368` | Clean two-repeat measured oMLX comparison; owlmlx post-run health returned clean idle |
| `Qwen3.6-27B` | `vMLX` | `rejected` | TPS `5.5997`, TTFT `4207.586ms`, peak RSS `54434840576` | reference completed `0/2`; peak RSS `54751936512` before failure | vMLX serve selected multimodal path and failed because `mlx-vlm` is not installed in the reference environment |
| `Qwen3.6-35B-A3B` | `oMLX` | `measured` | TPS `3.5349`, TTFT `16655.804ms`, peak RSS `47860367360` | TPS `2.4400`, TTFT `16347.293ms`, peak RSS `47785541632` | Clean two-repeat measured oMLX comparison; Qwen35 TTFT is high for both runtimes |
| `Qwen3.6-35B-A3B` | `vMLX` | `rejected` | TPS `3.4772`, TTFT `16911.368ms`, peak RSS `47738159104` | reference completed `0/2`; peak RSS `58454884352` before failure | Same vMLX multimodal/`mlx-vlm` reference blocker |

This supports saying:

- Qwen27 and Qwen35 no longer belong in a generic
  `reference_runtime_comparison_missing` bucket for `oMLX`.
- `vMLX` comparison is still blocked for these local Qwen model directories
  because `vMLX serve` treats them as multimodal due `vision_config` and the
  local reference venv lacks `mlx-vlm`.
- Qwen35 TTFT is not proven to be an owlmlx-only platform defect on this short
  workload: the measured oMLX TTFT is in the same 16s band.
- Qwen27 TTFT is materially lower than Qwen35 on the same prompt, and owlmlx is
  slightly lower than oMLX in this run.

This does not support saying:

- `parity`
- `replacement-ready`
- `equivalent`
- `matches oMLX`
- `matches vMLX`
- final-answer quality is solved

## Evidence Roots

Primary evidence root:

`files/evidence/owlmlx/comparative-evidence/20260506T040009Z-qwen27-qwen35-reference-closure/`

Important sub-runs:

- `qwen27-omlx-run/run/`
  - `manifest.json`
  - `commands.json`
  - `summary.md`
  - `owlmlx_attempt*.stdout.txt`
  - `omlx_attempt*.stdout.txt`
  - `owlmlx_attempt*.rss.jsonl`
  - `omlx_attempt*.rss.jsonl`
- `qwen27-vmlx-run/rerun-after-8066-ready/`
  - clean rerun manifest for the vMLX reference blocker
  - the earlier `qwen27-vmlx-run/run/` record is preserved in the ledger as an
    initial startup/ready-window contaminated attempt and should not be used as
    the representative Qwen27/vMLX read
- `qwen35-omlx-run/run/`
  - measured Qwen35 oMLX comparison
- `qwen35-vmlx-run/run/`
  - vMLX reference blocker evidence
- post-run probes:
  - `post-run-8066-healthz.json`
  - `post-run-8066-runtime-status.json`
  - `post-run-8066-comparative-evidence-latest.json`
  - `post-run-8066-comparative-evidence-history.json`
  - `post-run-8064-listeners.txt`
  - `post-run-8001-models.json`

## Runner Hardening

The measured runner now supports dynamic external service attribution through:

- `external_pid_file`: refreshed during the attempt, not only at attempt start
- `external_listener_ports`: refreshed during RSS sampling and recorded in
  `*.rss.jsonl`
- macOS fallback from `psutil.net_connections()` to `lsof -nP -iTCP:<port>
  -sTCP:LISTEN -t` when process connection inspection is denied

RSS sample rows now include:

- `dynamic_pid_files`
- `dynamic_listener_ports`
- `resolved_root_pids`

This matters because long-running references such as `oMLX` can restart or
move behind the same port while the wrapper client PID remains stable.

## oMLX Result

The controlled oMLX runs used the already-running local service:

`python -m omlx.cli serve --model-dir /Users/yeemio/AI/Agent/models --port 8001 --paged-ssd-cache-dir /Users/yeemio/AI/Agent/.omlx-cache --hot-cache-max-size 8GB`

Live process verification after the run showed this service was the Homebrew
installed upstream package:

- tap/formula: `jundot/omlx/omlx`
- installed package: `omlx 0.3.4`
- loaded package path:
  `/opt/homebrew/Cellar/omlx/0.3.4/libexec/lib/python3.11/site-packages/omlx`
- upstream URL reported by Homebrew: `https://github.com/jundot/omlx`

So the oMLX comparison target was not an `owlmlx` fork and not the local
`runtime-probes/omlx-probe` checkout. The staged evidence labels use
`0.3.4-homebrew-jundot-omlx-livepid-portpid` to preserve that distinction.

Both Qwen models produced schema-valid `measured` records.

For `Qwen3.6-27B`:

- owlmlx: TPS `5.4482`, TTFT `4143.916ms`, peak RSS `54420045824`
- oMLX: TPS `2.8127`, TTFT `4848.995ms`, peak RSS `55013818368`

For `Qwen3.6-35B-A3B`:

- owlmlx: TPS `3.5349`, TTFT `16655.804ms`, peak RSS `47860367360`
- oMLX: TPS `2.4400`, TTFT `16347.293ms`, peak RSS `47785541632`

The Qwen35 TTFT result is the most important operational signal in this round:
the high latency appears on both owlmlx and oMLX for the same short prompt, so
the immediate root-cause read is model-family/profile/prefill/template behavior
or shared workload shape, not a proven owlmlx-only scheduling regression.

## vMLX Result

Both Qwen vMLX runs rejected before serving was ready.

The local vMLX doctor command passes for both models, but reports them as
multimodal:

- `Qwen3.6-27B`: `Multimodal: Yes (vision)`
- `Qwen3.6-35B-A3B`: `Multimodal: Yes (vision)`

During `vMLX serve`, the reference runtime selects the multimodal loader and
fails with:

`ImportError: mlx-vlm is required for multimodal inference. Install with: pip install mlx-vlm`

This is a reference-runtime environment/loader blocker for these local Qwen
model directories. It is not evidence that `vMLX` cannot run Qwen in a correctly
configured environment, and it is not an owlmlx performance comparison.

## Output Quality Caveat

The Qwen owlmlx outputs still surface reasoning-style text such as:

`Here's a thinking process:`

That keeps final-answer quality separate from throughput/lifecycle evidence.
The next final-answer closure should be a dedicated profile/template/stop/parser
round, not a generic output-cleaning patch.

## Operational Read

For Qwen27 and Qwen35 on this host:

- `oMLX` is now a live measured peer reference for this narrow short-prompt
  workload.
- `vMLX` remains blocked by local reference environment/model-loader behavior
  for these Qwen directories.
- owlmlx met the important lifecycle floor in the representative Qwen runs:
  `load -> generate -> unload -> health clean`.
- Qwen35 TTFT is the sharpest remaining performance signal; it should be
  investigated as a Qwen35/profile/prefill/template path first, because oMLX
  shows the same high-latency band.

Next executable closure should split:

1. Qwen final-answer/profile/template/stop/parser behavior.
2. DeepSeek comparative evidence.
3. Longer/multi-request scheduler-cache-batching stress.
