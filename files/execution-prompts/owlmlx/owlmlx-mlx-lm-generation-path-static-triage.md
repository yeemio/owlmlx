# owlmlx MLX-LM Generation Path Static Triage

> Executor: B
> Date: 2026-05-05
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Outcome target: `owlmlx_mlx_lm_generation_path_static_triage_closed`

## 1. Goal

Explain which local `mlx_lm` generation knobs are relevant to the current Model
RC gap without loading heavy models.

The Qwen3.6-27B direct baseline showed that direct `mlx_lm.stream_generate` can
also be slow. This round should inspect local APIs and source behavior to
separate:

- owlmlx wrapper/generation-path concerns
- shared `mlx_lm` decode/sampler/template behavior
- profile policy knobs that owlmlx can safely own

## 2. Scope

Docs-only or test-light lane.

Owned files may include:

- `docs/source-of-truth/mlx-lm-generation-baseline-triage.md`
- `docs/source-of-truth/master-outline.md`
- one handoff under `files/execution-prompts/owlmlx/`

You may inspect installed package source under the repo `.venv`, but do not
modify external package files.

Do not run model loads. Static imports, `inspect.signature`, `python -c`
introspection, and grep over installed package files are allowed.

## 3. Questions To Answer

Answer with file/function references where possible:

1. What are the effective call shapes for `mlx_lm.load`,
   `mlx_lm.generate`, and `mlx_lm.stream_generate` in the installed runtime?
2. Which sampler fields are accepted locally: `temperature`, `top_p`,
   `min_p`, repetition penalty, top_k, seed, or others?
3. How does chat-template application happen in local `mlx_lm`, and can a
   direct baseline apply the same template path as owlmlx HTTP chat?
4. What API or helper exposes stop-token or stop-string behavior, if any?
5. What timing surfaces are available locally for load, prefill, TTFT, decode,
   and total wall clock?
6. Which levers should become owlmlx `ModelProfile` policy now?
7. Which levers require live proof before becoming supported profile behavior?
8. Which peer-reference mechanisms remain useful only as test or design
   inputs, not code to copy?

## 4. Required Checks

Run:

```bash
.venv/bin/python - <<'PY'
import inspect
import mlx_lm
print("mlx_lm", getattr(mlx_lm, "__file__", None))
for name in ("load", "generate", "stream_generate"):
    fn = getattr(mlx_lm, name, None)
    print(name, inspect.signature(fn) if fn else None)
PY
git diff --check -- docs/source-of-truth/mlx-lm-generation-baseline-triage.md docs/source-of-truth/master-outline.md
```

Run a forbidden-claim grep on touched docs. Banned words may appear only in
negative rule lists, not as current claims.

## 5. Hard Rules

- No heavy model load.
- No external repo edit.
- No peer-runtime code vendoring.
- Do not describe oMLX, vMLX, or vllm-mlx as upstreams.
- Do not make current release-ready, parity, production-grade, superior, or
  equivalent claims.
- Preserve unrelated dirty/staged work.
- Stage only lane-owned files.

## 6. Final Response

Report:

- outcome label
- files changed
- checks and results
- concrete ModelProfile levers recommended
- exact blockers/deferred live proof
- whether staged
- confirmation that no heavy model load or external repo edit occurred
