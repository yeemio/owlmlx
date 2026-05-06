# owlmlx Model RC Observability Contract v2 Handoff

> Date: 2026-05-05
> Scope: runtime-owned Model RC observability fields for OwlOps consumption
> Status: implemented at schema / builder / HTTP-runner / unit-test / docs layer

## Outcome

This round adds optional, stable observability v2 fields to
`owlmlx.model_release_candidate_record` without changing the record version or
requiring migration of older cumulative-ledger rows.

OwlOps should consume these fields from owlmlx records when present. OwlOps
should not infer decode speed, queue wait, or phase timings locally from v1
coarse metrics.

## Added Fields

- `load_time_ms`
- `reload_time_ms`
- `unload_time_ms`
- `queue_wait_ms`
- `ttft_ms`
- `decode_tokens_per_second`
- `end_to_end_tokens_per_second`
- `resident_mode`
- `prompt_template_id`
- `quality_caveats`
- `memory_peak_source`

## Semantics

- `ttft_ms` currently uses the same runtime source as
  `first_token_latency_ms`, but gives OwlOps an explicit bottleneck field.
- `end_to_end_tokens_per_second` preserves the current `tokens_per_second`
  meaning: completion tokens divided by full stream wall time, including TTFT.
- `decode_tokens_per_second` is post-first-token speed:
  `completion_tokens_after_first_token / (stream_wall_time - ttft)`, guarded
  against zero and missing values.
- `queue_wait_ms` is derived from stream `done.wait_time_s` when the runtime
  reports it.
- `quality_caveats` are derived from blockers and `output_sanity_label`; they
  are caveats, not model-quality claims.
- `memory_peak_source` is `process_tree_rss` for the current HTTP runner.

## Compatibility

Older v1 records without these fields remain schema-valid. New dry-run records
populate nullable timing/speed fields as `null`, string provenance as
`unknown`, and caveats as `[]`.

## Verification

Required lightweight checks for this round:

```bash
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile owlmlx/model_release_candidate_schema.py owlmlx/model_release_candidate_record.py scripts/runtime_model_release_candidate.py
git diff --check
```

## Deferred Scope

- No OwlOps consumer implementation in this repo.
- No historical cumulative-ledger backfill or mutation.
- No heavy model live run.
- No DeepSeek isolated `mlx_reported_peak` or `mixed` memory source until a
  future isolated runner actually emits that measurement.
- No `pass`, release-ready, parity, replacement, or production-grade claim.
