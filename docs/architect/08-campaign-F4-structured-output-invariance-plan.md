# Campaign F · F-4 — Structured-Output Invariance Plan

> **Grade**: plan-grade · architecture intent
> **承载位置**: `docs/architect/08-campaign-F4-structured-output-invariance-plan.md`
> **下游 design-grade**: [`design/F-4-structured-output-invariance-spec.md`](design/F-4-structured-output-invariance-spec.md)
> **Plan-grade 来源**: [`01-mainline-roadmap.md`](01-mainline-roadmap.md) Part II #10 + Part V Campaign F + G3
> **Status**: selected as next replacement-grade gap after B prefill chunking closeout
> **语言纪律**: this plan does not claim structured-output reliability is supported; it defines how to measure it

---

## 1. Goal Contract

| Field | Value |
|---|---|
| `goal_id` | `campaign-f4-structured-output-invariance` |
| `title` | Structured-output invariance as owlmlx's next replacement-grade reliability gap |
| `success_definition` | owlmlx has a reproducible workload + validator + JSONL evidence path that measures JSON / tool-call / nested-object / enum / thinking-tag breakage across the three primary models and runtime knobs; at promotion time F-4 can report a hard break rate target of `<0.1%` only if evidence reaches the matrix threshold |
| `blocked_definition` | F-4 is blocked only if the runtime cannot produce structured-output samples through an existing serving path, or if validation cannot be made deterministic without model-specific hand inspection |
| `hard_rules` | no cache / trim / speculative serving edits in plan/design; no supported claim from plan-grade; no external benchmark substituted for repo-local evidence; no source-of-truth promotion without §1a evidence |
| `out_of_scope` | raw TPS optimization, prompt-cache reuse, n-gram serving integration, grammar-constrained decoding implementation, OwlCoda client integration |
| `current_truth` | F-1 status surface landed; F-2 C0/C1 passed but C2 serving integration is blocked by mlx-lm hybrid trim; B prefill chunking configuration/progress surfaces are supported but acceleration is not promised; roadmap #10 Structured-Output Invariance remains missing |
| `remaining_gaps` | no structured-output workload, no validator, no breakage-rate ledger, no cross-knob invariance matrix, no evidence to compare model/chunk/temperature fragility |
| `dominant_next_gap` | create the F-4 measurement contract and first code-grade round for deterministic validation + a small smoke matrix |

---

## 2. Why F-4 Now

The previous performance lane has reached a short-term ceiling on the three primary local models:

- raw decode throughput is already close enough to the local MLX ceiling that additional speed work is low-leverage
- F-2 n-gram serving integration and A prompt-cache reuse are both paused behind mlx-lm hybrid trim limitations
- B prefill chunking now gives callers a supported configuration/progress surface, but not a wall-clock acceleration story

That leaves the most valuable replacement-grade gap in the roadmap: **structured-output invariance**.

F-4 aligns with owlmlx's declared identity: **Reliability + Provenance + Governance**, not raw throughput. A runtime that can say "this configuration preserves JSON/tool-call shape under controlled knobs" has a more defensible enterprise story than a runtime that only reports tokens per second.

---

## 3. Replacement-Grade Question

F-4 asks:

```text
When model, prompt class, temperature, prefill chunk size, and future speculative
methods vary, does owlmlx preserve structured-output contracts?
```

The first phase does **not** require a live speculative method. It establishes the baseline matrix before spec is re-enabled:

- JSON parse validity
- required-field completeness
- enum integrity
- nested object structure
- tool/function-call argument parseability
- thinking-tag closure
- forbidden prose outside the structured envelope

Once F-2/F-3/F-7 unpause, the same matrix becomes the guardrail for speculative-path promotion.

---

## 4. Scope

### In scope

- A fixed structured-output workload with five families:
  - `json_schema_flat`
  - `function_call_arguments`
  - `nested_object`
  - `enum_constrained`
  - `thinking_tag_closed`
- A deterministic validator that classifies failures without model-specific hand judging
- A benchmark runner that can vary:
  - model: Qwen 27B 4bit / Qwen 35B-A3B 4bit / Gemma 31B 4bit
  - chunk: 512 / 2048 / 8192 where the path supports `prefill_chunk_tokens`
  - temperature: 0 / 0.3
  - output contract family
- JSONL evidence with per-sample failure taxonomy and rollup break rates
- Honest capability wording for F-4 result states

### Out of scope

- Implementing grammar-constrained decoding or JSON repair
- Adding a new OpenAI/Anthropic tool-call API surface
- Treating OwlCoda live sessions as the first test harness
- Claiming cross-runtime or cross-host reliability before local evidence exists
- Reviving n-gram serving integration while mlx-lm hybrid trim remains blocked
- Editing `session_kv_cache.py`, `cache_manager.py`, `memory_*`, or Track 1 files

---

## 5. Matrix Shape

The naive Cartesian matrix is too large if interpreted as:

```text
50 prompts × 5 families × 3 models × 3 chunks × 2 temps × 20 repeats
```

That is 90,000 generations before retries. It is useful as a **long-run aspiration**, not the first executable gate.

F-4 therefore uses staged evidence:

| Stage | Purpose | Minimum output count | Expected wall time |
|---|---|---:|---:|
| F-4.0 | validator-only fixture tests | 0 model generations | minutes |
| F-4.1 | smoke matrix, prove runner and taxonomy | 30-60 generations | < 1 hour |
| F-4.2 | stratified reliability matrix | ≥1000 generations | several hours / resumable |
| F-4.3 | candidate promotion repeat | ≥1000 fresh generations | separate run |

The F-4.2 matrix is stratified, not exhaustive:

```text
3 models × 3 chunks × 2 temperatures × 5 families × sampled cases
```

The sampler must preserve a stable seed and write the sampled case ids into the ledger so a future run can replay the exact matrix.

---

## 6. Breakage Taxonomy

F-4 separates hard failures from diagnostic drift.

| Category | Meaning | Counts against hard break rate |
|---|---|---|
| `json_parse_failed` | output cannot be parsed as JSON after extracting the expected envelope | yes |
| `schema_required_missing` | required key absent | yes |
| `schema_type_mismatch` | key exists but type is wrong | yes |
| `enum_value_invalid` | enum field outside allowed vocabulary | yes |
| `tool_arguments_invalid` | function/tool-call arguments are missing or not parseable | yes |
| `thinking_tag_unclosed` | requested thinking-style tag is not closed | yes |
| `extra_prose_outside_envelope` | response contains prose before/after a strict JSON-only request | yes |
| `semantic_value_mismatch` | parse/schema ok but deterministic expected value is wrong | yes, only for cases with exact expected values |
| `format_variant` | valid structure but harmless whitespace/key-order/string escaping differs | no |
| `refusal_or_safety_text` | model refuses instead of following a benign structured request | yes unless prompt is explicitly adversarial |

Rollups must report both:

- `hard_break_rate`
- `diagnostic_variant_rate`

---

## 7. Capability Wording

F-4 produces evidence about a reliability property. It does not automatically promote a runtime method.

| Result | Wording |
|---|---|
| F-4.0 validator passed | `structured_output_validator=scaffold_only` |
| F-4.1 smoke passed | `structured_output_invariance=experimental` |
| F-4.2 ≥1000 matrix with 0 hard breaks | `structured_output_invariance=partial_candidate` |
| F-4.3 fresh repeat with 0 hard breaks | eligible for source-of-truth promotion review |
| Any hard break | no promotion; failure taxonomy becomes the next dominant gap |

`supported` is not available from plan/design alone.

---

## 8. Relationship To Campaign F

F-4 sits after F-1 and beside F-2/F-3:

- **F-1** gives runtime-owned speculative status; F-4 does not change it
- **F-2/F-3** are speculative method lanes; currently blocked/paused for serving integration
- **F-4** establishes the structured-output guardrail those methods must pass before serving promotion
- **F-5** can later become a draft constraint checker if F-4 finds recurrent tool/JSON breakage

This is why F-4 can proceed while F-2/F-3 are paused: it measures current serving behavior first, then becomes the guardrail for future speculative behavior.

---

## 9. Integration Boundary

F-4 should start at the runtime harness layer, not OwlCoda live integration.

The first harness should use existing runtime paths and fixed prompts. OwlCoda can consume the evidence later, but the initial matrix must not depend on a live OwlCoda session state. This preserves the roadmap boundary: OwlCoda is downstream consumption; owlmlx owns runtime reliability evidence.

---

## 10. Evidence Paths

Design-grade should use:

```text
files/evidence/owlmlx/bench/structured-output-invariance/
  <ts>-f4-validator-fixtures.jsonl
  <ts>-f4-validator-fixtures-rollup.jsonl
  <ts>-f4-smoke-matrix.jsonl
  <ts>-f4-smoke-matrix-rollup.jsonl
  <ts>-f4-stratified-matrix.jsonl
  <ts>-f4-stratified-matrix-rollup.jsonl
```

No evidence should be promoted into `docs/source-of-truth/` until the relevant code-grade round has run and §1a review is explicit.

---

## 11. Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Model-specific prompt brittleness | A bad prompt can measure prompt quality instead of runtime reliability | Use simple deterministic schemas, store fixture cases, keep failures inspectable |
| Too-large matrix | A 90k generation matrix stalls the campaign | Stage F-4.0 / F-4.1 / F-4.2; make F-4.2 resumable |
| False confidence from temperature 0 only | structured reliability often breaks at mild sampling | Include temp=0.3 in F-4.1+ |
| Overclaim from local-only evidence | one host/model run is not production truth | Label as local structured-output evidence until repeated |
| Conflating diagnostic variants with hard breaks | key order/whitespace differences are not contract failures | Separate hard break rate from diagnostic variant rate |

---

## 12. Status / Next Step

Decision: F-4 is accepted as the next replacement-grade mainline after B prefill chunking closeout.

Next execution round:

1. Land design-grade [`design/F-4-structured-output-invariance-spec.md`](design/F-4-structured-output-invariance-spec.md)
2. Review the F-4.0/F-4.1 thresholds
3. Start code-grade only after review: validator fixtures + smoke harness, not the full ≥1000 matrix

---

## 13. References

- [`01-mainline-roadmap.md`](01-mainline-roadmap.md) #10 Structured-Output Invariance, Campaign F, and G3
- [`06-campaign-F1-plan.md`](06-campaign-F1-plan.md)
- [`design/F-1-spec.md`](design/F-1-spec.md)
- [`design/F-2-ngram-suffix-spec.md`](design/F-2-ngram-suffix-spec.md)
- [`design/B-prefill-chunking-spec.md`](design/B-prefill-chunking-spec.md)

---

## 14. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Initial F-4 plan-grade selection after performance lane closeout; defines structured-output invariance as the next Reliability / Provenance / Governance gap | Codex architect loop |
