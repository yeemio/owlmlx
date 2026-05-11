# Stage 1 Archive Manifest (v3 — final, verified)

Branch: `refactor/stage-1-archive-spec-layer`

**Status**: complete. All 5 archive commits landed, full test suite green.

## Methodology (v3)

Three iterations were needed before the analysis was correct.
This is recorded honestly because it shaped the actual commit shape:

- **v1** (initial): regex-based closure missed `from ..X import`
  relative imports inside `runtime/`. Reported 157 dead modules.
  Would have wrongly archived 149 modules that ARE reachable.
- **v2**: closure corrected. Reported 8 dead modules. Undercount —
  treated `runtime/__init__.py` re-exports as "real consumption".
- **v3** (this): distinguished re-export plumbing from actual field
  reads. Scrubbed BOTH `__init__.py` files, then archived modules whose
  fields are not read by any real runtime code. Reported 152 candidates.
  Caught one further misclassification at execution (`context_concurrency`
  has module-level functions consumed by live code, not just a dataclass)
  → final result: **151 modules archived, 1 kept**.

## Final result

| Asset | Before | After Stage 1 | Archived |
|---|---:|---:|---:|
| `owlmlx/*.py` top-level modules | 193 | 42 | **151** |
| `owlmlx/__init__.py` lines | 1,251 | 88 | -1,163 |
| `owlmlx/runtime/__init__.py` lines | 602 | 71 | -531 |
| Test files | 222 | ~67 | ~155 |
| pytest collection | 1501 cases + warnings | **925 cases, 0 errors** | — |
| pytest run | (not previously reported) | **922 passed / 3 skipped / 0 failed** | — |

**Total LOC moved to `archive/spec-layer-v0/`**: ~73K (modules + tests + scripts).

## Commit shape

| # | Commit | What |
|---|---|---|
| c1 | `d639f67` | scrub `owlmlx/__init__.py` 1251→88 lines |
| c2 | `1cb0631a` | scrub `owlmlx/runtime/__init__.py` 602→71 lines |
| c3 | `b7d5f6fa` | archive cache_stream_* (84 mod + 85 tests + 44 scripts) |
| c4 | `a2bc5dd5` | archive cache_pre_claim_/pre_gate_/cohort/child/request/counter/closure/batching/runtime/repeatability/structural/admission_hook (48 mod + 49 tests + 25 scripts) |
| c5 | (this batch) | archive multi_model_/cache_scheduler_/cache_turboquant_/ad-hoc (19 mod + 21 tests + 0 scripts) |
| c6 | (this commit) | AGENTS.md anti-regression rule + MANIFEST_v3 |

## What stays — the 11 truly-consumed spec contracts

These are the actual functional spine, with `.field_name` read sites in
`runtime/server.py` and/or `runtime/kernel.py`:

```
abort_recovery                          field_reads = 18
host_pressure                           field_reads = 15
memory_pressure_contract                field_reads = 3
memory_pressure_eviction_policy         field_reads = 16
cache_scheduler_status                  field_reads = 16
model_residency_policy                  field_reads = 32
nonresident_loadability_lineage         field_reads = 29
nonresident_model_admission_policy      field_reads = 54
reclaim_barrier_event                   field_reads = 2
recovery_supervisor_contract            field_reads = 2
request_context_length_truth            field_reads = 2
```

This cluster is the watermark / admission / eviction / recovery contracts
that align with PR #649. They become the headline architecture in Stage 2
(vocabulary rename).

## What was archived but is reversible

Everything moved to `archive/spec-layer-v0/` retains full git history.
If any module turns out to have a hidden consumer, `git mv` it back.
The single misclassification caught at execution (`context_concurrency`)
proves the kept-vs-archived line is conservative — when in doubt the
manifest erred toward keeping.
