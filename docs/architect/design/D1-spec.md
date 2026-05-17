# D1 · Design-Grade Spec

> **Gate**: Campaign D1 · DeepSeek V4 Flash isolated repeatability
> **Plan-grade source**: [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D
> **Status**: design-grade draft · 2026-05-16
> **Prerequisite**: B-1a passed, so D1 may start in parallel with B-1b as long as it does not pollute the main runtime venv or default model surface.
> **Non-goal**: this spec does not claim `owlmlx supports DeepSeek V4`.

## 1. Purpose

D1 moves `DeepSeek-V4-Flash-2bit-DQ` from a one-off isolated smoke to a
repeatable experimental lifecycle proof:

```text
isolated runtime preflight
  -> load
  -> 5 consecutive prompts without process restart
  -> progressive max_tokens 128 / 512 / 1024
  -> unload
  -> clean health
```

This remains an isolated DeepSeek V4 adapter lane. It must not change the stock
`owlmlx` runtime venv, the default model visibility surface, or the supported
capability matrix label.

## 2. Scope

### In

| Item | Requirement |
|---|---|
| Runtime environment | Existing isolated `.runtime-deepseek-v4-mlx` / DeepSeek V4 PR runtime only |
| Model artifact | `DeepSeek-V4-Flash-2bit-DQ` |
| Repeat count | 5 consecutive prompts in the same isolated runtime session |
| Token ladder | `max_tokens` in `{128, 512, 1024}` |
| Lifecycle | preflight -> load -> generate repeats -> unload -> clean health |
| Evidence | JSONL ledger under `files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/` |
| Capability label | `experimental` / `experimental_only` |

### Out

- No default `GET /v1/openai/models` visibility for DeepSeek V4.
- No public release or supported capability promotion.
- No adoption of `ds4.c` as an owlmlx backend.
- No stock `mlx-lm` venv mutation.
- No MTP claim; D3 owns MTP checkpoint/weights inspection.
- No 4bit DeepSeek V4 claim on this 128GB host.

## 3. Run Shape

### 3.1 Preflight

The runner must record:

```yaml
preflight:
  isolated_runtime_path: .runtime-deepseek-v4-mlx
  mlx_lm_source:
    origin: <module path>
    package_version: <version or null>
    git_root: <best-effort checkout root or null>
    git_commit: <best-effort commit or null>
    git_branch: <best-effort branch or null>
    git_remote: <best-effort remote or null>
  runtime_source:
    mlx_lm: <same shape as mlx_lm_source>
    deepseek_v4:
      origin: <module path>
      git_commit: <best-effort commit or null>
  model_path: <absolute path>
  model_type: deepseek_v4
  stock_runtime_untouched: true
  default_model_surface_unchanged: true
```

If the isolated runtime is missing, D1 must fail as `blocked`, not silently fall
back to the stock `.venv`.

Preflight provenance is best-effort and non-mutating: missing git metadata does
not fail preflight, but the module origin and package version should be recorded
whenever import succeeds.

### 3.2 Prompt Set

Use five deterministic prompts with distinct failure modes:

| Prompt | Purpose |
|---|---|
| `p1_short_cn` | basic Chinese short answer |
| `p2_short_en` | basic English short answer |
| `p3_code` | code-like formatting stability |
| `p4_long_context` | prefill pressure |
| `p5_stop_marker` | stop-marker / repetition behavior |

Each prompt runs once per token ladder level unless host pressure aborts the
round. That yields up to 15 generations in one loaded session.

### 3.3 Acceptance

```yaml
D1_deepseek_v4_isolated_repeatability:
  preflight: passed | blocked | failed
  five_prompt_same_session: passed | failed
  token_ladder:
    max_tokens_128: passed | failed
    max_tokens_512: passed | failed
    max_tokens_1024: passed | failed
  lifecycle:
    load: passed | failed
    unload: passed | failed
    clean_health_after_unload: passed | failed
  overall_conclusion: passed | blocked | failed
```

Passing requires:

- all five prompts return a non-empty completion at every enabled token level;
- no child process/runtime restart between prompt 1 and prompt 5 within a token
  level;
- no fatal host-pressure event;
- no dirty stock runtime health after failure or unload;
- final unload succeeds and clean health is observable.

## 4. Evidence Schema

Minimum JSONL record:

```json
{
  "schema_version": "d1.v1",
  "gate": "D1",
  "runtime": "owlmlx",
  "model_id": "DeepSeek-V4-Flash-2bit-DQ",
  "isolation": {
    "isolated_runtime_path": ".runtime-deepseek-v4-mlx",
    "stock_runtime_untouched": true,
    "default_model_surface_unchanged": true
  },
  "token_ladder": [128, 512, 1024],
  "coverage": {
    "expected_generation_count": 15,
    "completed_generation_count": 15,
    "passed_generation_count": 15,
    "full_ladder_completed": true,
    "prompt_token_matrix": {
      "p1_short_cn": {
        "128": "passed",
        "512": "passed",
        "1024": "passed"
      }
    }
  },
  "prompt_results": [
    {
      "prompt_id": "p1_short_cn",
      "max_tokens": 128,
      "ok": true,
      "completion_chars": 0,
      "stop_reason": "stop",
      "restart_observed": false,
      "repetition_flag": false
    }
  ],
  "lifecycle": {
    "load_ok": true,
    "unload_ok": true,
    "clean_health_after_unload": true
  },
  "metrics": {
    "load_time_s": null,
    "ttft_ms_by_prompt": {},
    "decode_tps_by_prompt": {},
    "peak_rss_gb": null
  },
  "verdict": "passed"
}
```

D2 will promote the `metrics` section from optional to required. D1 records it
when cheaply available but does not fail only because a metric is absent.

The summary-level `coverage` section is the authoritative check that D1 ran the
requested prompt set across the requested token ladder. A run that stops after a
failed prompt must keep the completed row evidence but set
`full_ladder_completed = false` and list any unrun pairs in `missing_pairs`.

Default D1 execution stops on the first failed row. Diagnostic reruns may use
`--continue-on-failure` to fill the remaining prompt/token matrix after a
failure; this improves attribution only and does **not** let the run pass unless
every requested pair passes.

## 5. Harness Requirements

Prefer extending the existing model-release-candidate tooling over adding a new
spec-as-code module:

| Surface | Minimal change |
|---|---|
| `scripts/runtime_model_release_candidate.py` | Add an isolated DeepSeek repeat mode if existing flags are close enough |
| `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl` | Append only if D1 produces a valid lifecycle result |
| `files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/` | Store raw D1 records |

If the existing runner cannot express "same isolated session, five prompts, no
restart", add a `scripts/bench/deepseek_v4_d1_repeatability.py` script. Do not
add `*_contract.py`, `*_evidence.py`, `*_harness.py`, or `*_ledger.py` modules.

## 6. Failure Semantics

| Failure | Classification | Next action |
|---|---|---|
| isolated runtime missing | `blocked` | recreate isolated env; do not mark model failed |
| unsupported `deepseek_v4` loader | `blocked` | keep experimental adapter lane; do not dirty main health |
| process restart during five prompts | `failed` | D1 fails; D2 cannot start |
| repetition / no stop at 1024 | `failed` | record prompt id + token level |
| `--continue-on-failure` records later successful rows after an earlier failure | overall remains `failed` | use only to localize repetition / stop-policy boundaries |
| host pressure fatal | `failed` | stop run; record host pressure snapshot |
| unload fails | `failed` | record clean-health failure; do not run further prompts |

## 7. Review Checklist

- [ ] Isolated runtime path is explicit and stock `.venv` is not mutated.
- [ ] DeepSeek V4 remains `experimental_only`.
- [ ] Five prompts run in one loaded session without restart.
- [ ] 128 / 512 / 1024 token ladder is recorded independently.
- [ ] Unload and clean-health evidence are present.
- [ ] Evidence path is under `files/evidence/owlmlx/deepseek-v4/`.
- [ ] No new spec-as-code Python modules are introduced.

## 8. Next Round

After D1 design review:

1. inspect current isolated `.runtime-deepseek-v4-mlx` availability;
2. implement or extend the runner;
3. run D1 only when B-1b is not actively using the GPU-heavy host window;
4. write the D1 verdict as `passed`, `blocked`, or `failed`;
5. start D2 only after D1 passes.
