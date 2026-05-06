# OwlOps R167 Model RC Profile-Aware Observability Consumer Prompt

> External repo: `/Users/yeemio/AI/gitrep/owlops`
> Depends on: owlmlx profile-aware Model RC records
> Suggested outcome: `owlops_model_rc_profile_aware_observability_ready`

## 1. Goal

Prepare OwlOps to consume profile-aware Model RC evidence from owlmlx without
inferring runtime facts locally.

This is an OwlOps consumer lane. OwlOps must render owlmlx-provided truth, not
derive model runtime behavior by guessing from model names.

## 2. Start Gate

Before implementation, probe owlmlx:

```bash
curl -s http://127.0.0.1:8066/v1/runtime/model-release-candidates/history
```

Proceed only if at least one fresh record or evidence payload exposes
profile-aware fields such as:

- `profile_id`
- `effective_generation_policy`
- `prompt_template_id`
- `quality_caveats`
- `decode_tokens_per_second`
- `ttft_ms`
- `memory_peak_source`
- `output_sanity_label`

If these fields are missing, implement only a narrow fallback display that says
`runtime_missing` or the existing OwlOps missing-field equivalent. Do not infer
profile IDs from model names.

## 3. Required Behavior

OwlOps should show:

- latest Model RC record per model
- whether the record is profile-aware
- effective generation policy when supplied by owlmlx
- output sanity and quality caveats
- optimization bottleneck candidates supplied by owlmlx, if present
- missing profile-aware fields as missing runtime truth

OwlOps must not:

- compute runtime profile identity locally
- classify model quality locally
- infer oMLX/vMLX comparative standing
- hide `needs_optimization`
- upgrade DeepSeek V4 from experimental/pressure lane

## 4. Suggested Tests

Add fixtures for:

- old v1/v2 records with missing profile fields
- new profile-aware records with explicit profile fields
- DeepSeek experimental record excluded from mainline summary
- unknown/missing profile fields rendered as missing runtime truth
- no local inference from model name

Run the existing Model RC and AppState focused suites.

## 5. Wording Rules

- In OwlOps, owlmlx is the runtime truth provider for this workspace.
- oMLX and vMLX are peer reference runtimes, not upstreams.
- Do not make current release-ready, parity, production-grade, superior, or
  equivalent claims.
- Keep `needs_optimization` visible.

## 6. Final Response

Report:

- outcome label
- whether the start gate was open or missing
- files changed
- tests/build run
- live probe result
- exactly which fields are displayed and which remain missing
