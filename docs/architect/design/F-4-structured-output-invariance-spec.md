# F-4 · Structured-Output Invariance Design-Grade Spec

> **Gate**: Campaign F · F-4 — structured-output invariance matrix
> **Layer**: design-grade, downstream of [`../08-campaign-F4-structured-output-invariance-plan.md`](../08-campaign-F4-structured-output-invariance-plan.md), upstream of code-grade (validator + smoke harness)
> **Plan-grade source**: [`../08-campaign-F4-structured-output-invariance-plan.md`](../08-campaign-F4-structured-output-invariance-plan.md)
> **Status**: F-4.1 smoke matrix implemented 2026-05-28; measurement harness passed with 59/60 hard breaks, so no promotion candidate
> **Prerequisite**: F-1 landed; F-2 serving integration is not required; B prefill chunking closeout provides chunk-size knobs but no speed claim
> **Non-goal**: this spec does not implement grammar-constrained decoding, JSON repair, tool-call protocol changes, or speculative serving

---

## 1. Purpose

F-4 turns roadmap dimension #10, **Structured-Output Invariance**, into an executable measurement gate.

It answers:

```text
Q1 Does the runtime preserve strict structured-output contracts under normal
   generation settings?
Q2 Which model / chunk-size / temperature conditions break JSON, tool-call
   arguments, nested objects, enum values, or thinking-tag closure?
Q3 Can owlmlx produce a durable breakage-rate ledger that later guards
   speculative decoding and OwlCoda tool loops?
```

F-4 is not a performance campaign. It is a reliability campaign.

---

## 2. Prerequisites

F-4.0 and F-4.1 may start when all are true:

- F-1 diagnostic status surface is landed (done)
- B prefill chunking `prefill_chunk_tokens` and `prefill_progress` are landed (done)
- the code-grade round avoids cache / trim / memory ownership files
- structured prompts can run through the existing owlmlx subprocess path or runtime kernel path without adding a new public API

Not required:

- F-2 n-gram serving integration
- resident MTP / assistant drafter serving promotion
- B-1c §2 soak-plus-swap closure
- OwlCoda live integration

---

## 3. Scope

### In scope

- `tests/fixtures/structured_output_invariance/f4_validator_fixtures.jsonl`
- `tests/fixtures/structured_output_invariance/f4_cases.jsonl` (F-4.1 smoke cases, if the same round proceeds beyond validator fixtures)
- `tests/test_structured_output_invariance.py`
- `scripts/bench/structured_output_invariance.py`
- JSONL evidence under `files/evidence/owlmlx/bench/structured-output-invariance/`
- failure taxonomy, per-sample classification, and rollup break rates
- chunk-size / temperature / model matrix controls

### Out of scope

- any `session_kv_cache.py`, `cache_manager.py`, `scheduler_admission.py`, or `memory_*` edit
- grammar-constrained decoding
- model fine-tuning or prompt tuning
- changing OpenAI / Anthropic HTTP tool-call schemas
- making OwlCoda the first harness
- promoting structured-output reliability to source-of-truth without evidence
- repairing invalid output automatically; F-4 measures breakage first

---

## 4. Phase Definition

F-4 is staged so the first code-grade round stays small.

### 4.1 F-4.0 — Validator Fixtures

Goal: prove the validator classifies known-good and known-bad structured outputs deterministically.

**Artifacts**:

```text
tests/fixtures/structured_output_invariance/f4_validator_fixtures.jsonl
tests/test_structured_output_invariance.py
scripts/bench/structured_output_invariance.py
```

**Pass criteria**:

| Check | Requirement |
|---|---|
| valid JSON fixture | parse_ok=true, hard_break=false |
| invalid JSON fixture | failure includes `json_parse_failed` |
| missing required field | failure includes `schema_required_missing` |
| wrong type | failure includes `schema_type_mismatch` |
| invalid enum | failure includes `enum_value_invalid` |
| invalid tool arguments | failure includes `tool_arguments_invalid` |
| unclosed thinking tag | failure includes `thinking_tag_unclosed` |
| extra prose outside envelope | failure includes `extra_prose_outside_envelope` |
| deterministic classification | same fixture set run twice produces byte-identical result rows except timestamps |

**Evidence**:

```text
files/evidence/owlmlx/bench/structured-output-invariance/<ts>-f4-validator-fixtures.jsonl
files/evidence/owlmlx/bench/structured-output-invariance/<ts>-f4-validator-fixtures-rollup.jsonl
```

### 4.2 F-4.1 — Smoke Matrix

Goal: prove the runner can generate real model outputs and classify failures across the five families.

**Minimum matrix**:

```text
3 models × 5 families × 2 temperatures × 1 chunk candidate × 2 samples
= 60 outputs
```

Use chunk `2048` for the first smoke because B evidence currently marks it as the best default candidate for Qwen35/Gemma 64k and it is the mlx-lm default shape.

**Pass criteria**:

| Check | Requirement |
|---|---|
| output count | `sample_count >= 60` |
| model coverage | all 3 primary models represented |
| family coverage | all 5 structured families represented |
| temperature coverage | temp=0 and temp=0.3 represented |
| row durability | every generation row appended before validation |
| validator coverage | every row has `parse_ok`, `hard_break`, `failure_codes`, `diagnostic_codes` |
| rollup | includes hard break rate by model / family / temperature |
| capability wording | no supported claim, regardless of result |

F-4.1 can pass even with hard breaks, as long as the harness correctly measures them. It is a measurement-harness gate, not a reliability-promotion gate.

### 4.3 F-4.2 — Stratified Matrix

Goal: produce the first replacement-grade reliability distribution.

**Minimum matrix**:

```text
3 models × 3 chunks × 2 temperatures × 5 families × sampled cases >= 1000 outputs
```

The sampler must write:

- `sample_seed`
- `case_id`
- `case_family`
- `model_id`
- `chunk_tokens`
- `temperature`
- `run_idx`

**Candidate pass threshold**:

| Metric | Threshold |
|---|---|
| `sample_count` | `>=1000` |
| `hard_break_count` | `0` for strict `<0.1%` wording at N=1000 |
| `hard_break_rate` | `<0.001` |
| `diagnostic_variant_rate` | recorded, not a hard gate |

If `hard_break_count > 0`, F-4 still succeeds as a diagnostic campaign but does not produce a promotion candidate.

### 4.4 F-4.3 — Fresh Repeat

Only if F-4.2 has zero hard breaks:

- rerun a fresh matrix with a different seed
- keep models/chunks/temperatures the same
- require zero hard breaks again before source-of-truth promotion review

---

## 5. Structured Families

### 5.1 `json_schema_flat`

Prompt asks for JSON only:

```json
{
  "task_id": "string",
  "category": "bugfix|feature|docs|test",
  "priority": 1,
  "requires_review": true
}
```

Checks:

- JSON parse
- exact required fields
- type match
- enum match
- no prose outside envelope

### 5.2 `function_call_arguments`

Prompt asks for a tool-call style argument object:

```json
{
  "tool_name": "apply_patch|run_tests|inspect_logs",
  "arguments": {
    "target": "string",
    "risk_level": "low|medium|high"
  }
}
```

Checks:

- outer object parse
- `tool_name` enum
- nested `arguments` object
- required argument keys

### 5.3 `nested_object`

Prompt asks for nested runtime diagnosis:

```json
{
  "diagnosis": {
    "root_cause": "string",
    "evidence": [{"source": "string", "summary": "string"}],
    "next_action": {"kind": "retry|fix|escalate", "owner": "runtime|operator"}
  }
}
```

Checks:

- nested object integrity
- array item shape
- nested enum

### 5.4 `enum_constrained`

Prompt asks for a single strict status:

```json
{
  "capability_label": "supported|partial|experimental|not_in_scope",
  "reason_code": "string"
}
```

Checks:

- enum exactness
- no invented capability label

### 5.5 `thinking_tag_closed`

Prompt asks for a controlled tag block plus JSON:

```text
<thinking>...</thinking>
{"final": "...", "confidence": "low|medium|high"}
```

Checks:

- opening and closing tag both present
- no nested unclosed tag
- JSON after tag parses
- enum exactness

This family is included because roadmap Campaign F explicitly names thinking-tag closure as part of spec/tool reliability.

---

## 6. Validator Contract

The validator returns one record per model output:

```json
{
  "case_id": "f4-json-flat-001",
  "family": "json_schema_flat",
  "parse_ok": true,
  "schema_ok": true,
  "hard_break": false,
  "failure_codes": [],
  "diagnostic_codes": ["format_variant"],
  "extracted_json": {"...": "..."}
}
```

Allowed failure codes:

| Code | Hard break |
|---|---|
| `json_parse_failed` | yes |
| `schema_required_missing` | yes |
| `schema_type_mismatch` | yes |
| `enum_value_invalid` | yes |
| `tool_arguments_invalid` | yes |
| `thinking_tag_unclosed` | yes |
| `extra_prose_outside_envelope` | yes |
| `semantic_value_mismatch` | yes |
| `refusal_or_safety_text` | yes |

Allowed diagnostic codes:

| Code | Meaning |
|---|---|
| `format_variant` | valid but differs in whitespace/key order/string escaping |
| `extra_optional_key` | valid object includes extra keys not required by the case |
| `case_insensitive_enum_match` | enum matches only after case normalization; diagnostic, not accepted for strict gate unless case permits it |

---

## 7. Runner Contract

### 7.1 CLI

Expected code-grade script:

```bash
python scripts/bench/structured_output_invariance.py \
  --phase smoke \
  --models qwen3.6-27b-4bit qwen3.6-35b-a3b-4bit gemma-4-31b-it-4bit \
  --chunks 2048 \
  --temperatures 0 0.3 \
  --samples-per-family 2
```

For F-4.2:

```bash
python scripts/bench/structured_output_invariance.py \
  --phase stratified \
  --models qwen3.6-27b-4bit qwen3.6-35b-a3b-4bit gemma-4-31b-it-4bit \
  --chunks 512 2048 8192 \
  --temperatures 0 0.3 \
  --min-samples 1000 \
  --sample-seed 4242 \
  --resume
```

### 7.2 Evidence schema

Cell row:

```json
{
  "schema_version": "f4.structured_output_invariance.cell.v1",
  "run_id": "<ts>-f4-smoke-matrix",
  "case_id": "f4-json-flat-001",
  "family": "json_schema_flat",
  "model_id": "qwen3.6-27b-4bit",
  "chunk_tokens": 2048,
  "temperature": 0.0,
  "run_idx": 1,
  "status": "ok",
  "output_hash": "sha256...",
  "parse_ok": true,
  "schema_ok": true,
  "hard_break": false,
  "failure_codes": [],
  "diagnostic_codes": []
}
```

Rollup row:

```json
{
  "schema_version": "f4.structured_output_invariance.rollup.v1",
  "run_id": "<ts>-f4-smoke-matrix",
  "phase": "smoke",
  "sample_count": 60,
  "hard_break_count": 0,
  "hard_break_rate": 0.0,
  "diagnostic_variant_rate": 0.0,
  "by_model": {},
  "by_family": {},
  "by_temperature": {},
  "by_chunk_tokens": {},
  "graduates": {
    "validator_contract": true,
    "measurement_harness": true,
    "structured_output_invariance_promotion_candidate": false
  }
}
```

---

## 8. Capability Labels

F-4 uses labels for the measurement property, not for model capability:

| Condition | Label |
|---|---|
| validator fixtures pass | `validator=scaffold_only` |
| smoke matrix produces durable rollup | `structured_output_invariance=experimental` |
| stratified matrix has `sample_count>=1000` and `hard_break_count=0` | `structured_output_invariance=partial_candidate` |
| fresh repeat also has zero hard breaks and §1a review accepts | eligible for source-of-truth promotion |

No F-4 design/code round may write `supported` by itself.

---

## 9. Failure Handling

| Failure | Action |
|---|---|
| validator fixture mismatch | fix validator/tests; do not run model matrix |
| all models fail same family | inspect prompt/validator first; likely case design issue |
| one model fails one family | keep evidence; that model/family becomes next triage gap |
| temp=0.3 fails but temp=0 passes | record sampling fragility; do not hide under deterministic path |
| chunk-size-specific break | record under `by_chunk_tokens`; this is exactly what F-4 is meant to reveal |
| hard break in F-4.2 | no promotion; write the failure taxonomy and select the dominant failing family |

---

## 10. Tests

Code-grade F-4.0/F-4.1 must run:

```bash
python -m pytest tests/test_structured_output_invariance.py -q
python -m py_compile scripts/bench/structured_output_invariance.py
git diff --check
```

If the runner touches runtime subprocess plumbing, also run the nearest existing subprocess backend tests. F-4.0/F-4.1 should not need that.

Do **not** add a new `owlmlx/*.py` validator module in F-4.0/F-4.1. The first
round is a bench harness, and AGENTS.md requires new package modules to have a
real runtime consumer. Keep validator helpers inside the bench script until a
runtime module genuinely needs to consume them.

---

## 11. Evidence Paths

```text
files/evidence/owlmlx/bench/structured-output-invariance/
  <ts>-f4-validator-fixtures.jsonl
  <ts>-f4-validator-fixtures-rollup.jsonl
  <ts>-f4-smoke-matrix.jsonl
  <ts>-f4-smoke-matrix-rollup.jsonl
  <ts>-f4-stratified-matrix.jsonl
  <ts>-f4-stratified-matrix-rollup.jsonl
```

F-4.0/F-4.1 code-grade should commit fixtures, tests, runner, and evidence together only after tests pass. It should not push unless requested.

---

## 12. Status / Next Step

Current status: F-4.1 smoke matrix implemented and green as a measurement harness.

F-4.0 evidence:

- `files/evidence/owlmlx/bench/structured-output-invariance/20260528T025514Z-f4-validator-fixtures.jsonl`
- `files/evidence/owlmlx/bench/structured-output-invariance/20260528T025514Z-f4-validator-fixtures-rollup.jsonl`

F-4.0 rollup:

- `sample_count=10`
- `hard_break_count=7`
- `fixture_mismatch_count=0`
- `graduates.validator_contract=true`
- `graduates.measurement_harness=false` (expected for validator-fixtures phase)

F-4.1 evidence:

- `files/evidence/owlmlx/bench/structured-output-invariance/20260528T030803Z-f4-smoke-matrix.jsonl`
- `files/evidence/owlmlx/bench/structured-output-invariance/20260528T030803Z-f4-smoke-matrix-rollup.jsonl`

F-4.1 rollup:

- `sample_count=60`
- `generation_error_count=0`
- `hard_break_count=59`
- `hard_break_rate=0.9833333333333333`
- `graduates.validator_contract=true`
- `graduates.measurement_harness=true`
- `graduates.structured_output_invariance_promotion_candidate=false`

F-4.1 family/model summary:

| Dimension | Result |
|---|---|
| By model | Qwen27B 20/20 hard breaks; Qwen35B-A3B 19/20; Gemma31B 20/20 |
| By family | json_schema_flat 12/12; function_call_arguments 11/12; nested_object 12/12; enum_constrained 12/12; thinking_tag_closed 12/12 |
| By temperature | temp=0.0 30/30; temp=0.3 29/30 |
| Dominant failures | `json_parse_failed=47`, `extra_prose_outside_envelope=8`, `thinking_tag_unclosed=4` |

This is not a reliability pass. It is a successful measurement-harness pass that
shows the current prompt-only structured-output path is not promotion-ready.

Next code-grade round:

1. Do not start F-4.2 as a promotion campaign from the current prompts.
2. Decide whether F-4.2 should test prompt-only strictness again, add a
   grammar-constrained baseline, or split tool-call JSON into a dedicated
   repair/constrained-decoding campaign.
3. Preserve F-4 wording as `experimental`; no `partial_candidate` claim is
   supported by the smoke data.

---

## 13. References

- [`../08-campaign-F4-structured-output-invariance-plan.md`](../08-campaign-F4-structured-output-invariance-plan.md)
- [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign F and G3
- [`F-1-spec.md`](F-1-spec.md)
- [`F-2-ngram-suffix-spec.md`](F-2-ngram-suffix-spec.md)
- [`B-prefill-chunking-spec.md`](B-prefill-chunking-spec.md)

---

## 14. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Initial design-grade spec for F-4 validator + smoke + stratified matrix; keeps measurement separate from grammar-constrained decoding or speculative serving | Codex architect loop |
| 2026-05-28 | F-4.0 validator fixtures implemented. Evidence `20260528T025514Z-f4-validator-fixtures*` records 10 fixtures, 7 expected hard breaks, 0 fixture mismatches, and `validator_contract=true`; measurement harness is false for the validator-fixtures phase. | Codex code-grade loop |
| 2026-05-28 | F-4.1 smoke matrix implemented. Evidence `20260528T030803Z-f4-smoke-matrix*` records 60 samples across 3 models, 5 families, 2 temperatures, and chunk 2048; `measurement_harness=true`, `hard_break_count=59`, and no promotion candidate. | Codex code-grade loop |
