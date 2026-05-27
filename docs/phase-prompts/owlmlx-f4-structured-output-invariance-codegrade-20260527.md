# owlmlx F-4 Structured-Output Invariance — Code-Grade Round Prompt

> **Use after review of**:
> - `docs/architect/08-campaign-F4-structured-output-invariance-plan.md`
> - `docs/architect/design/F-4-structured-output-invariance-spec.md`
>
> **Goal**: implement F-4.0 validator fixtures and, if clean, the smallest F-4.1 smoke runner. Do not start the ≥1000 stratified matrix in this round.

## Goal

Build the first executable structured-output invariance harness for owlmlx:

1. deterministic validator
2. fixture tests
3. JSONL evidence capture for validator fixtures
4. smoke runner scaffold capable of model/chunk/temperature/family rows

## Hard Rules

- Do not edit `session_kv_cache.py`, `cache_manager.py`, `scheduler_admission.py`, or `memory_*`.
- Do not revive F-2 n-gram serving integration.
- Do not implement JSON repair or grammar-constrained decoding.
- Do not change public OpenAI / Anthropic protocol schemas.
- Do not claim `supported`.
- Leave unrelated dirty/untracked files untouched.
- Do not add a new `owlmlx/*.py` validator module in this round; keep validator helpers inside `scripts/bench/structured_output_invariance.py` unless a real runtime consumer exists.

## Required Files

Expected new files:

```text
tests/test_structured_output_invariance.py
tests/fixtures/structured_output_invariance/f4_validator_fixtures.jsonl
scripts/bench/structured_output_invariance.py
files/evidence/owlmlx/bench/structured-output-invariance/<ts>-f4-validator-fixtures.jsonl
files/evidence/owlmlx/bench/structured-output-invariance/<ts>-f4-validator-fixtures-rollup.jsonl
```

Only add F-4.1 smoke evidence if F-4.0 is clean.

## Required Tests

```bash
python -m pytest tests/test_structured_output_invariance.py -q
python -m py_compile scripts/bench/structured_output_invariance.py
git diff --check
```

If the smoke runner touches subprocess backend plumbing, also run the nearest `tests/test_mlx_lm_subprocess_backend.py` cases. The preferred first round should avoid backend plumbing changes.

## Evidence Rules

Each validator fixture row must include:

- `case_id`
- `family`
- `parse_ok`
- `schema_ok`
- `hard_break`
- `failure_codes`
- `diagnostic_codes`

Rollup must include:

- `sample_count`
- `hard_break_count`
- `hard_break_rate`
- `failure_code_counts`
- `graduates.validator_contract`
- `graduates.measurement_harness`

## Stop Conditions

Stop and report instead of expanding scope if:

- validator classifications are ambiguous
- the fixture set cannot be made deterministic
- smoke generation requires new runtime protocol surface
- the matrix threatens to become a long-running full reliability run

## Final Output

Summarize:

- files changed
- fixture count
- validator verdict
- smoke verdict if run
- tests
- commit id if committed
- remaining gaps before F-4.2
