# owlmlx Comparative Evidence Schema Stub

> Status: authoritative
> Updated: 2026-04-25
> Scope: minimum frozen field names and value enumerations for the `comparative_evidence_record` surface; serves as single source of truth for cross-repo consumers

## 1. Purpose

This document freezes the runtime-owned answer to one narrow question:

**Which field names and value enumerations on the `comparative_evidence_record`
surface are stable enough that downstream consumers (notably `owlops`) may
depend on them without re-typing?**

It is intentionally minimum. It is not the full schema. It is the part that,
once promised, cannot drift between `owlmlx` and `owlops` without coordinated
review.

## 2. Authority

This document is the single source of truth for the field names and
enumerations listed in section 4. The following is enforced:

- `comparative-evidence-harness-contract.md` may extend, but may not rename,
  any field listed here without a coordinated update
- `owlops/.../comparison-workspace-contract.md` consumers must read these
  field names from the wire response, not re-declare them in the operator
  app code as literal duplicates of authoritative truth
- if any other doc disagrees with this stub on a field name or enumerator,
  this stub wins until amended here

## 3. Surface Identity

- `surface = "owlmlx.comparative_evidence_record"`
- `version = "v1"`

The `version` value is bumped whenever a section-4 field is renamed,
retired, or has its enumeration narrowed. Adding a new field or extending
an enumeration is an additive change and does not bump `version`.

## 4. Frozen Field Set

### 4.1 Identity Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `surface` | string literal | yes | `"owlmlx.comparative_evidence_record"` |
| `version` | string | yes | currently `"v1"` |
| `recorded_at` | ISO 8601 string | yes | UTC, second precision minimum |
| `evidence_pointer` | string | yes | repo-relative path to raw artifacts |

### 4.2 Classification Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `host_class` | string | yes | stable host fingerprint identifier |
| `workload_class` | string enum | yes | see section 4.5 |
| `workload_invariants` | object | yes | see section 4.6 |

### 4.3 Per-Runtime Measurement

`runtimes` is an ordered list. Each element:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `runtime_id` | string enum | yes | see section 4.7 |
| `runtime_version` | string | yes | upstream-reported version string |
| `measurement` | object | yes | fields below |

`measurement` object:

| Field | Type | Required |
| --- | --- | --- |
| `throughput_tokens_per_second` | number (float) | yes |
| `first_token_latency_ms` | number (float) | yes |
| `peak_resident_set_bytes` | integer | yes |
| `wall_clock_ms` | number (float) | yes |
| `completed_request_count` | integer | yes |
| `failure_count` | integer | yes |
| `failure_causes` | list of string | required if `failure_count > 0` |

### 4.4 Verdict

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `verdict_text` | string | yes | shape rules in harness contract §5.1 |
| `verdict_grade` | string enum | yes | see section 4.8 |

### 4.5 `workload_class` Enumeration (initial set)

- `single_prompt_short`
- `single_prompt_long`
- `multi_prompt_serial`
- `multi_prompt_aggregated`

Adding a class is additive. Renaming or removing a class is a `version` bump.

### 4.6 `workload_invariants` Required Keys

- `model_id` (string)
- `model_quantization` (string)
- `decode_max_tokens` (integer)
- `decode_temperature` (number)
- `prompt_set_hash` (string)
- `serving_budget_bytes` (integer)

Two records are comparable only when these six keys match exactly across all
runtimes in the same record.

### 4.7 `runtime_id` Enumeration (initial set)

- `owlmlx`
- `omlx`
- `vmlx`

Adding a new reference runtime is additive at the schema level but requires
review under harness contract §5.5.

### 4.8 `verdict_grade` Enumeration

Exactly one of:

- `measured`
- `inconclusive`
- `rejected`

The following values are explicitly banned and may not be added without
amending this stub and `release-readiness-backlog.md` §4.3:

- `parity`
- `equivalent`
- `replaces`
- `replacement`
- `production_ready`
- `superior`

## 5. Cross-Repo Consumption Rule

`owlops` (and any other consumer) must:

1. read field names off the wire response from the runtime-owned HTTP
   surface, not from a hard-coded local duplicate of section 4
2. tolerate additive fields gracefully (unknown fields are kept, not
   rejected)
3. fail visibly when `version` does not match its expected major version,
   rather than silently rendering partial data

`owlops` must not:

- redeclare the enumerations in section 4.5 / 4.7 / 4.8 as the source of
  truth in the operator app code
- back-fill missing required fields with defaults; missing required fields
  must surface as a `Missing upstream signal` row

## 6. Versioning Rule

A `version` bump (`v1` → `v2`) is required when any of the following is
true:

- a required field is renamed
- a required field is retired
- a `workload_class`, `runtime_id`, or `verdict_grade` enumerator is removed
- the meaning of any existing field changes

Additive changes (new optional fields, new enumerators) keep `version`
stable.

## 7. Closure Criteria

This stub is considered surface-closed when:

- the runtime-owned module that builds the record imports its field names
  from a single authoritative location (Python module, JSON schema file, or
  equivalent), not literal strings scattered across the codebase
- at least one record exists on the wire that conforms to every required
  field in section 4
- `owlops` consumes the surface without local enumeration drift

Until all three are true, this stub is `surface_open`, and both
`comparative-evidence-harness-contract.md` §8 and
`owlops/.../comparison-workspace-contract.md` §7 remain blocked on it.

### 7.1 Authoritative Module (2026-04-26)

`owlmlx/comparative_evidence_schema.py` is the single Python authority
for the field names, enumerations, required field sets, and banned
verdict vocabulary listed in section 4. Both
`owlmlx/comparative_evidence_record.py` and the runtime HTTP routes at
`/v1/runtime/comparative-evidence` and
`/v1/runtime/comparative-evidence/history` import from it directly, so
the schema/wire/contract triple stays in lockstep. Cross-repo consumers
must continue to read field names off the wire response — they may not
re-declare these enumerations as the source of truth in operator-app
code.

## 8. Restart Condition

This stub is reopened only when:

- a field is renamed or retired (forces `version` bump)
- the banned-vocabulary list in §4.8 is challenged
- a downstream consumer reports drift between this stub and the wire

Schedule pressure is not a reopen reason.
