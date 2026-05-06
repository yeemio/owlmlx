# DeepSeek V4 Flash Adapter Optimization Candidate

> Status: authoritative
> Updated: 2026-05-05
> Capability: experimental adapter optimization candidate

## Purpose

This record freezes the first local DeepSeek V4 Flash MLX adapter result for
`owlmlx`.

It does not promote DeepSeek V4 Flash into the stable model set. It records that
the model line is now an optimization candidate because this host can run a
minimal DeepSeek V4 smoke through an isolated MLX PR runtime.

## Local Artifacts

| Artifact | Path | Status |
|---|---|---|
| MLX 4bit | `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-4bit` | downloaded; complete; too large for this host's first real generation smoke |
| MLX 2bit-DQ | `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ` | downloaded; complete; first short generation smoke passed |

The 2bit-DQ artifact has:

- `model.safetensors.index.json` metadata total size: `96520315996`
- `model.safetensors.index.json` metadata total parameters:
  `284333146519`
- safetensors shards: `19/19`
- index weight keys: `2610`
- safetensors header check: passed
- missing indexed shards: none
- extra safetensors shards: none

## Runtime Used

The passing smoke used an isolated experimental runtime, not the default
production runtime:

- Python: `/Users/yeemio/AI/gitrep/owlmlx/.runtime-deepseek-v4-mlx/bin/python`
- MLX: `0.31.2`
- `mlx-lm`: editable DeepSeek V4 PR branch from `machiabeli/mlx-lm-1`
- PR branch commit observed locally: `7d20c1d`
- DeepSeek V4 model module: `mlx_lm.models.deepseek_v4`

The default stock `mlx-lm` line is still not enough for this model line because
public `mlx-lm 0.31.3` does not include `deepseek_v4.py`.

## Smoke Result

Command shape:

```bash
/Users/yeemio/AI/gitrep/owlmlx/.runtime-deepseek-v4-mlx/bin/python -m mlx_lm.generate \
  --model /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ \
  --prompt 'Write one short sentence about local AI.' \
  --max-tokens 16 \
  --temp 0.0 \
  --max-kv-size 512 \
  --kv-bits 4 \
  --kv-group-size 64
```

Observed result:

- prompt tokens: `12`
- generated tokens: `16`
- prompt throughput: `0.341 tokens/sec`
- generation throughput: `33.706 tokens/sec`
- peak memory: `96.574 GB`
- output was valid text, not tokenizer garbage

## Current Label

`DeepSeek-V4-Flash-2bit-DQ` is:

- `experimental`
- `adapter optimization candidate`
- `downloaded`
- `complete`
- `first short generation smoke passed`

It is not:

- `supported`
- `stable`
- a default route target
- visible on the current `owlmlx` technical-preview model surface
  (`GET /v1/openai/models` on `127.0.0.1:8066`, observed 2026-05-05)
- evidence that 4bit DeepSeek V4 fits this 128 GB host
- evidence that long prompts, tool use, repetition behavior, or cache reuse are
  healthy

## Known Caveats

- The 4bit artifact was killed by the host during real generation smoke with
  exit code `137`; its index metadata total size is about `151.5 GB`, which is
  too close to or above the practical memory boundary for this host.
- The passing 2bit-DQ smoke uses a PR branch, not merged stock `mlx-lm`.
- Transformers still falls back to a generic tokenizer/config path for
  `deepseek_v4`.
- Long-query repetition was reported in community discussion and remains
  unverified locally.
- The first passing smoke is intentionally tiny and does not prove task quality.
- The artifact currently lives under `model-candidates`, not the active
  `models_root` consumed by the technical-preview visibility gate.

## Next Optimization Questions

The next local optimization round should answer:

- whether PR-branch `deepseek_v4` can serve repeated prompts without process
  restart
- whether generation remains coherent beyond 128 tokens
- whether the tokenizer/config fallback can be narrowed or eliminated
- whether `owlmlx` should wrap this runtime as an isolated experimental backend
- whether 2bit-DQ quality is good enough to justify further integration work

## Release-Candidate Program Placement

This model is part of
`docs/source-of-truth/model-release-candidate-program.md` section `4.2` as the
flagship pressure and adapter optimization lane.

It must remain separate from the mainline release-candidate lane until a
runtime-owned adapter, repeated-run evidence, and OwlOps observation record
exist.

The 4bit artifact stays `experimental_only` and must not be used as the active
pressure line until a separate host-fit proof replaces the current exit-137
truth.
