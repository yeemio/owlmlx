# Gemma4 MTP Drafter Probe - 2026-05-06

> Status: authoritative local probe note
> Scope: confirm whether local `gemma-4-31B-it` can be used as the target for
> the Gemma4 assistant MTP drafter through `mlx-vlm`
> Non-goal: owlmlx serving support, reference-runtime parity, throughput
> optimization claim, or default product behavior

## Summary

The local Gemma4 target does not need a new download or conversion before the
Gemma4 assistant MTP path can be tested.

Target:

- path: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- `model_type`: `gemma4`
- architecture: `Gemma4ForConditionalGeneration`
- text model type: `gemma4_text`
- vision model type: `gemma4_vision`
- text layers: `60`
- vocab size: `262144`

Draft model:

- path:
  `/Users/yeemio/AI/Agent/model-candidates/mlx-community/gemma-4-31B-it-assistant-bf16`
- `model_type`: `gemma4_assistant`
- architecture: `Gemma4AssistantForCausalLM`
- text model type: `gemma4_text`
- layers: `4`
- shared KV layers: `4`
- vocab size: `262144`

This confirms the downloaded assistant is a drafter sidecar, not a standalone
Gemma4 serving target.

## Toolchain Finding

The already-available local `mlx-vlm 0.4.4` installations did not expose the
required MTP CLI flags:

- `--draft-model`
- `--draft-kind`
- `--draft-block-size`

`mlx-vlm>=0.4.5` was required by the upstream model card, but PyPI did not
resolve that version during this probe. An isolated probe environment was
therefore created at:

`/Users/yeemio/AI/gitrep/runtime-probes/mlx-vlm-mtp-probe/`

It installed `mlx-vlm 0.5.0` from GitHub main:

`git+https://github.com/Blaizzy/mlx-vlm.git@8c9e560bebbeccbd5fbeb46dcd426bc5d80159b0`

The resulting probe versions were:

- `mlx-vlm=0.5.0`
- `mlx-lm=0.31.3`
- `mlx=0.31.2`

Naming and adapter boundary:

- `mlx` is the lower-level Apple Silicon tensor / ML runtime substrate.
- `mlx-lm` is the text-generation adapter family used for pure text LLM
  paths such as Qwen, Llama-like models, DeepSeek-family text paths, and
  GPT-OSS-style text generation.
- `mlx-vlm` is the vision-language / multimodal adapter family used for VLM
  paths such as Gemma4, Qwen-VL, LLaVA-style models, and multimodal
  generation. These models can still serve text-only prompts.
- Gemma4 is often used as a text model in owlmlx evidence, but its local
  architecture is multimodal. Its current MTP assistant route is therefore an
  `mlx-vlm` adapter concern, not an `mlx-lm` adapter concern.

That CLI exposes the MTP arguments and accepts:

```bash
python -m mlx_vlm generate \
  --model /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --draft-model /Users/yeemio/AI/Agent/model-candidates/mlx-community/gemma-4-31B-it-assistant-bf16 \
  --draft-kind mtp \
  --draft-block-size 6
```

## Live Probe Results

Evidence root:

`files/evidence/owlmlx/gemma-mtp-draft-probe/20260506T132604Z/`

The two-token load smoke loaded the target and drafter:

- log: `smoke.log`
- output: `Private intelligence`
- speculative summary: `0.0 accepted tokens over 1 rounds`
- max resident set size: `52917960704`
- peak memory footprint: `64463910464`

The longer acceptance smoke showed the drafter actually participating:

- log: `acceptance-smoke.log`
- output:
  `Local AI refers to artificial intelligence models that run directly on a user's own hardware rather than on a remote cloud server.`
- speculative summary: `2.86 accepted tokens over 7 rounds`
- max resident set size: `45872496640`
- peak memory footprint: `64677705304`

Post-run `owlmlx` 8066 health remained clean idle:

- `ok=true`
- `readiness=degraded`
- `active_model_id=null`
- `model_count=0`
- `backend_error=null`

## Verdict

The local `gemma-4-31B-it` directory is compatible enough to serve as the
Gemma4 target for the upstream `mlx-vlm` MTP drafter path.

The next blocker is no longer asset acquisition. It is runtime ownership:

- add or wrap an `mlx-vlm` execution path inside owlmlx, or explicitly keep it
  as a reference/probe-only path
- define the profile/template/parser contract for Gemma4 MTP output
- measure speed against the non-MTP Gemma path with identical prompt,
  `max_tokens`, post-run health, and RSS accounting
- only then decide whether this becomes `supported` rather than
  `experimental`

Current owlmlx capability label:

`experimental`

## Runtime-Owned Wrapper Return

A first owlmlx-owned experimental wrapper now exists:

- module: `owlmlx/gemma4_mtp_drafter.py`
- operator entry: `scripts/runtime_gemma4_mtp_drafter.py`
- tests: `tests/test_gemma4_mtp_drafter.py`

This layer does not import `mlx-vlm` into owlmlx's normal package import path.
It owns:

- Gemma4 target / assistant drafter config inspection
- assistant-as-drafter, not standalone-target, classification
- required `mlx-vlm` MTP CLI flag inspection
- canonical `python -m mlx_vlm generate ... --draft-kind mtp` argv
  construction
- parsing of `Speculative decoding: <mean> accepted tokens over <rounds>
  rounds`
- extraction of clean generated text from combined probe logs

Live local inspect result:

- `status=ready`
- `capability_label=experimental`
- target / draft pair blockers: none
- toolchain flags present:
  `--draft-model`, `--draft-kind`, `--draft-block-size`

Verification:

- `pytest -q tests/test_gemma4_mtp_drafter.py` passed with `8 passed`
- `python3 -m py_compile owlmlx/gemma4_mtp_drafter.py
  scripts/runtime_gemma4_mtp_drafter.py` passed
- `scripts/runtime_gemma4_mtp_drafter.py parse-log` correctly parsed the
  existing acceptance smoke into clean final text plus
  `mean_accepted_tokens=2.86`, `rounds=7`

This is still not 8066 serving support. The next closure round is the backend
bridge decision: either add a child-runner bridge that can be selected by
`OWLMLX_BACKEND_RUNNER_MODULE`, or keep the MTP path as a standalone
experimental operator until `mlx-vlm` exposes a more stable programmatic API.

## Experimental Backend Bridge Return

The first backend bridge is now implemented:

- runner: `owlmlx/runtime/mlx_vlm_mtp_runner.py`
- tests: `tests/test_mlx_vlm_mtp_runner.py`
- evidence:
  `files/evidence/owlmlx/gemma-mtp-backend-bridge/20260506T134444Z/manifest.json`

It speaks the existing `MlxLmSubprocessBackend` JSONL child protocol and is
selected with:

```bash
OWLMLX_RUNTIME_PYTHON=/Users/yeemio/AI/gitrep/runtime-probes/mlx-vlm-mtp-probe/.venv/bin/python
OWLMLX_BACKEND_RUNNER_MODULE=owlmlx.runtime.mlx_vlm_mtp_runner
OWLMLX_GEMMA4_MTP_DRAFT_MODEL=/Users/yeemio/AI/Agent/model-candidates/mlx-community/gemma-4-31B-it-assistant-bf16
OWLMLX_GEMMA4_MTP_DRAFT_BLOCK_SIZE=6
```

Bridge mode:

`deferred_cli_per_request`

That means load validates the target/drafter/toolchain but generation still
shells out to `python -m mlx_vlm generate` per request. This is intentionally
not a resident `mlx-vlm` backend claim.

The direct backend smoke used:

- backend: `MlxLmSubprocessBackend`
- runner module: `owlmlx.runtime.mlx_vlm_mtp_runner`
- target:
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- prompt: `Answer in two words: local AI.`
- `max_tokens=2`
- output: `Private intelligence`
- load: ok
- generate: ok
- unload: ok

Post-run checks:

- no residual `mlx_vlm` / Gemma MTP runner processes
- 8066 stayed clean idle with `active_model_id=null`, `model_count=0`,
  `backend_error=null`

The capability label remains:

`experimental`

This now supports saying:

- Gemma4 MTP is no longer only a shell command remembered by an operator.
- owlmlx owns an experimental wrapper and a selectable child-runner bridge.
- owlmlx needs at least two MLX adapter lines: `mlx-lm adapter` for text LLM
  serving and `mlx-vlm adapter` for Gemma4 / multimodal / MTP drafter serving.

This still does not support saying:

- supported serving
- resident MTP backend
- speedup
- parity
- replacement-ready

The runtime architecture consequence is that owlmlx should not treat
`mlx-vlm` as a one-off Gemma workaround. The owned runtime surface needs one
unified model discovery, loading, health, cache, draft-model, and routing
story across both `mlx-lm` and `mlx-vlm` adapters while keeping each adapter's
capability labels honest.

## A/B Timing Return

Same-host A/B timing evidence now exists:

`files/evidence/owlmlx/gemma-mtp-ab-timing/20260506T135656Z/summary.json`

Workload:

- adapter family: `mlx-vlm`
- target: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- prompt: `Write one concise sentence explaining local AI.`
- `max_tokens=48`
- `temperature=0`
- timing scope: fresh `mlx-vlm` CLI process per request, including model load
  and process startup cost

The A/B was run in both orders:

| Pair | Order | non-MTP elapsed | MTP elapsed | Delta MTP - non-MTP | MTP speculative summary |
|---|---|---:|---:|---:|---|
| 1 | non-MTP then MTP | `22525.247ms` | `19957.138ms` | `-2568.109ms` | `2.86 accepted tokens over 7 rounds` |
| 2 | MTP then non-MTP | `22852.033ms` | `19940.919ms` | `-2911.114ms` | `2.86 accepted tokens over 7 rounds` |

Aggregate:

- MTP mean: `19949.029ms`
- non-MTP mean: `22688.640ms`
- mean delta: `-2739.611ms`
- MTP / non-MTP ratio: `0.8793`

Both MTP and non-MTP generated the same clean final sentence:

`Local AI refers to artificial intelligence models that run directly on a user's own hardware rather than on a remote cloud server.`

Post-run checks:

- after both A/B pairs, 8066 remained clean idle with `active_model_id=null`,
  `model_count=0`, and `backend_error=null`
- no residual `mlx_vlm` / Gemma MTP runner processes remained after the
  reverse-order pair

Current verdict:

`mtp_measured_faster`

Claim boundary:

This verdict is limited to the current experimental `deferred_cli_per_request`
path. It measures fresh `mlx-vlm` CLI process timing, not resident decode
speedup, not supported serving, and not replacement parity.

The next dominant Gemma4 MTP gap is therefore no longer "does MTP run?" or
"does the bridge select?". It is resident `mlx-vlm adapter` ownership: model
load should become persistent enough to separate load cost from decode speed,
and runtime health should expose MTP/drafter state without parsing ad hoc logs.
