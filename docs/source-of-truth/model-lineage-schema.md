# owlmlx Model Lineage Schema

> Status: authoritative
> Updated: 2026-04-11
> Capability: R16 — Model lineage schema

## 1. Purpose

`owlmlx` owns the runtime truth for served-model lineage:

- what base weights a served model came from
- what format and quantization are actually served
- what conversion path produced the local artifact
- what runtime and runtime version verified it
- what verification truth can carry over after a change

The platform owns catalog storage and API transport. `owlmlx` owns the schema
and pure validation / inheritance rules.

## 2. Owned Implementation

Implementation:

- `owlmlx/model_lineage.py`

Tests:

- `tests/test_model_lineage.py`

Export surface:

- `ModelLineage`
- `LineageValidationResult`
- `LineageChangeType`
- `TruthInheritance`
- `normalize_model_lineage()`
- `validate_model_lineage()`
- `derive_lineage_change_type()`
- `derive_truth_inheritance()`
- `lineage_from_artifact_metadata()`

## 3. Required Fields

The canonical lineage schema follows the platform lineage contract:

- `base_model`
- `base_format`
- `quantizer`
- `quant_method`
- `served_format`
- `conversion_path`
- `conversion_patches`
- `local_path`
- `file_size_gb`
- `sha256`
- `runtime`
- `runtime_version`
- `verified_date`
- `verified_context`
- `known_caveats`

For `stable` and `backup` models, all fields are required.

For `candidate` and lower lifecycle states, these fields may be omitted:

- `conversion_patches`
- `sha256`
- `known_caveats`

The lifecycle state itself remains platform-owned. `owlmlx` only uses it as
validation context.

## 4. Normalization Rules

- `file_size_gb` is clamped to a non-negative float.
- `verified_context` is clamped to a non-negative integer.
- `conversion_patches` and `known_caveats` normalize to tuples of strings.
- empty `sha256` normalizes to `None`.

Normalization does not perform disk I/O, hash calculation, HTTP calls, or
catalog reads.

## 5. Truth Inheritance Rules

Default: verification truth is not inherited.

| Change Type | Inheritance | Must Re-verify |
|---|---|---|
| Same model, same runtime, same quant | Full | Nothing |
| Same model, runtime version bump | Most | R1 + R3 |
| Same model, different quant | None | Q1 + Q2 + Q3 |
| Same base, different conversion path | None | Full gate G1–G7 |
| Different base model | None | Full gate G1–G7 |
| Same model, different runtime | None | Backup gate B1–B4 |

These rules are implemented as pure functions. The platform decides whether to
promote, demote, block, or display a model based on those results.

## 6. Platform Consumption

Current consumption:

- `llm_router/primary_line_status.py`

The platform now normalizes catalog lineage through `owlmlx.model_lineage`
before exposing it in `model_lineage`, and includes a
`model_lineage_validation` section showing validation status.

The platform still owns:

- catalog file storage
- API endpoint transport
- upgrade gate execution
- runtime probing
- user-facing remediation

## 7. Known Debt Exposed By R16

The current catalog contains stable/backup lineage records with missing
`sha256`. `owlmlx` does not hide this. The validation layer reports missing
fields honestly; filling hashes is a platform catalog maintenance task.
