# owlmlx Comparative Evidence Harness Contract

> Status: authoritative
> Updated: 2026-04-28
> Scope: runtime-owned harness contract that produces honest comparative evidence between `owlmlx` and reference runtimes (`oMLX` / `vMLX`)

## 1. Purpose

This document freezes the runtime-owned answer to one narrow question:

**How does `owlmlx` produce repeatable, in-repo comparative evidence against
reference runtimes without inflating it into a parity or replacement claim?**

It directly serves `release-readiness-backlog.md` section 3.5. It does not
replace the descriptive matrix in `reference-runtime-comparison-matrix.md`;
that matrix records relative posture, this contract owns the executable
harness and verdict surface.

## 2. Ownership

The harness is `runtime-owned` per `ownership-boundary.md`.

`owlmlx` owns:

- workload definition
- harness execution path
- raw measurement collection
- frozen verdict statement schema

`owlmlx` does not own:

- comparison rendering for operator consumption (that is `owlops`-owned;
  see `owlops/.../comparison-workspace-contract.md`)
- marketing surfaces, parity statements, replacement claims

## 3. Owned Surfaces

The harness must own the following surfaces. None may be partially exposed
without the others.

### 3.1 Workload Definition

- `workload_class`: enumerated identifier for a comparable workload, for
  example `single_prompt_short`, `single_prompt_long`, `multi_prompt_serial`,
  `multi_prompt_aggregated`
- `workload_inputs`: fully captured inputs (prompt set, decode parameters,
  max-tokens) so any third party can reproduce the run
- `workload_invariants`: fields that must match across the two runtimes for
  the run to be honest (model identity, quantization, host class, budget)

### 3.2 Host Class

- `host_class`: stable host fingerprint covering CPU/GPU class, RAM size,
  power state, OS version
- a run is only valid when both runtimes execute on the same `host_class`
- cross-host comparisons are not allowed; they must be rejected at harness
  level with a frozen reason

### 3.3 Measurement Surface

The harness must capture, per runtime, at minimum:

- `throughput_tokens_per_second`
- `first_token_latency_ms`
- `peak_resident_set_bytes`
- `wall_clock_ms`
- `completed_request_count`
- `failure_count` and per-failure cause class

Additional fields are allowed but must be additive; existing fields may not
be repurposed.

### 3.4 Verdict Schema

Per run, the harness emits a `comparative_evidence_record` with:

- `surface = "owlmlx.comparative_evidence_record"`
- `version = "v1"`
- `host_class`
- `workload_class`
- `workload_invariants`
- `runtimes`: ordered list of `{ runtime_id, version, measurement }`
- `verdict_text`: a frozen, factual sentence — see section 5.1
- `verdict_grade`: one of `measured`, `inconclusive`, `rejected`
- `recorded_at`: ISO timestamp
- `evidence_pointer`: path to raw run artifacts under repo

`verdict_grade` may never be `parity`, `replaces`, `equivalent`, or any
synonym. See section 5.

### 3.5 Evidence Ledger Linkage

Every emitted `comparative_evidence_record` must be appended to a runtime-
owned ledger surface, parallel in discipline to
`phase45-customer-runtime-evidence-ledger.md`. The ledger is append-only.
Records may be superseded but not silently rewritten.

## 4. Repeatability Requirements

A `comparative_evidence_record` is only honest when:

1. the same `workload_class` and `workload_invariants` ran against each
   listed runtime on the same `host_class`
2. at least two repeat runs per runtime exist with consistent verdict_grade
3. the evidence_pointer resolves to artifacts that include raw stdout/stderr,
   resource samples, and a re-run command

Single-shot, non-reproducible measurements must be rejected at ledger entry.

## 5. Hard Rules

### 5.1 Verdict Vocabulary

`verdict_text` must follow the form:

- `"measured: <runtime_a> <metric> <value> vs <runtime_b> <metric> <value> on host_class=<...>, workload_class=<...>"`
- or `"inconclusive: <reason>"`
- or `"rejected: <reason>"`

The following words are banned from `verdict_text`:

- `parity`, `equivalent`, `replaces`, `replacement`, `production-ready`,
  `superior`, `wins`, `beats`, `matches`

This rule is enforced by `release-readiness-backlog.md` section 4.3.

### 5.2 No Cross-Host Promotion

A run on one `host_class` may not be promoted to a verdict for another
`host_class`. Each host requires its own measurement.

### 5.3 No Partial Surface Exposure

The HTTP / file surface that exposes evidence must expose either the full
`comparative_evidence_record` or nothing. Partial exposure (for example
omitting `failure_count` or `verdict_grade`) is rejected.

### 5.4 Harness Failure Is Itself Truth

If the harness cannot run one of the listed runtimes on the host (import
failure, OOM, missing weights), the record is emitted with
`verdict_grade = "rejected"` and a frozen reason. Silent skipping is not
allowed.

### 5.5 Reference Runtime Selection Is Frozen

The harness compares against `oMLX` and `vMLX` as the named reference
runtimes. Adding another reference requires extending this contract, not
adding a new runtime to an existing record schema.

## 6. Out Of Scope

The following are explicitly not owned by this harness:

- model training comparison
- accuracy / quality evaluation (this contract only owns runtime
  performance evidence; quality is a separate evidence line)
- continuous benchmarking (the harness is on-demand; scheduled execution is
  deferred)
- cross-vendor hardware sweeps

## 7. Consumer Boundary

Consumers (notably `owlops`) may:

- read the latest record per `(host_class, workload_class)`
- read the ledger of historical records
- request a new run via an action that flows through the existing operator
  action queue; execution remains runtime-owned

Consumers may not:

- compute their own verdict grade
- reorder, edit, or hide records
- present the record under any vocabulary banned in section 5.1

## 8. Closure Criteria

This contract is considered surface-closed when all of the following are
true:

- a runtime-owned module owns `build_comparative_evidence_record(...)` and
  `comparative_evidence_record_to_dict(...)`
- a runtime-owned operator entry exists at
  `scripts/runtime_comparative_evidence.py` (or equivalent)
- at least one record exists in the ledger for at least one
  `(host_class, workload_class)` pair, with `verdict_grade = "measured"`
- the record is consumable by upper layers via a stable HTTP surface

Until all four are true, this contract is `surface_open`, and
`release-readiness-backlog.md` floor 3.5 remains open.

### 8.1 HTTP Surface Sub-Closure (2026-04-26)

The HTTP surface that exposes the record is now mounted and live-curl
verified through the OwlOps R156 sub-round
(`owlmlx-comparative-evidence-surface-for-owlops-r156`):

- `GET /v1/runtime/comparative-evidence` returns the latest validated
  `comparative_evidence_record` v1, or an explicit `still_blocked`
  payload (HTTP 503) when no record has been appended
- `GET /v1/runtime/comparative-evidence/history` returns the stable
  `comparative_evidence_record_history` v1 envelope, or the same
  `still_blocked` payload when the ledger is empty
- the runtime-owned ledger backing both endpoints is JSONL, append-only
  (`owlmlx.comparative_evidence_ledger.ComparativeEvidenceLedger`)
- `scripts/runtime_comparative_evidence.py` is the operator entry for
  `append-rejected-record` / `latest` / `history`

This sub-closure did **not** close section 8 by itself. At the time, the
third bullet — `verdict_grade = "measured"` — still required a same-host run
with both `owlmlx` and at least one of `omlx` / `vmlx` actually invoked.

### 8.2 Measured Record Closure (2026-04-28)

The measured-record requirement is now closed for one
`(host_class, workload_class)` pair:

- evidence directory:
  `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/`
- ledger:
  `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl`
- `verdict_grade = "measured"`
- `host_class = "Mac17,6-arm64-macOS-26.4.1-128GB"`
- `workload_class = "single_prompt_short"`
- runtime list: `owlmlx`, `omlx`
- both runtimes completed two repeats with `failure_count = 0`
- the `omlx` RSS measurement includes the external live server PID via
  `external_pid_file`
- the `owlmlx` first-token timing uses a `regex:` strategy that matches
  generated output rather than diagnostic preamble
- both HTTP routes served the fresh ledger:
  `/v1/runtime/comparative-evidence` and
  `/v1/runtime/comparative-evidence/history`

This closes section 8 for the required first measured record. It does not
claim parity, replacement, production readiness, or superiority.

## 9. Restart Condition

This contract is reopened only when:

- a new reference runtime is added
- a measurement field is added or retired
- the verdict vocabulary is extended (subject to section 5.1 review)
- the ownership boundary changes

Schedule pressure is not a reopen reason.
