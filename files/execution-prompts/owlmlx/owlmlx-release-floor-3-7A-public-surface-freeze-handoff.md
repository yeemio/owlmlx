# owlmlx Execution Handoff 3.7A: Public Surface Freeze

> Date: 2026-04-28
> Lane: single ClaudeCode executor (release floor 3.7 sub-round 3.7A)
> Active release floor: `3.7 Public Surface Discipline` — **closeout-recommended**
> Role: public-surface source-of-truth, validation test, and closeout recommendation

## 1. Outcome Label

`owlmlx_release_floor_3_7A_public_surface_closed_recommended`

## 2. Verdict

The public technical-preview boundary is frozen. `release-readiness-backlog.md`
section `3.7` requirements are met: one frozen `public-surface.md` exists,
exactly named modules / contracts / HTTP routes / scripts are listed,
everything not listed is `internal` by default, and the file references
existing source-of-truth documents instead of duplicating them.

This handoff does **not** flip the backlog ledger; coordinator closeout
owns that flip and may also batch it with the parallel `3.6A` external
customer evidence outcome.

## 3. Changed Files

New authoritative source-of-truth doc:

- `docs/source-of-truth/public-surface.md` — 12 sections: status/date,
  purpose, label vocabulary, supported HTTP routes (liveness/status,
  generation + OpenAI/Anthropic compatibility, lifecycle/inventory,
  release-floor contract surfaces), supported runtime modules,
  supported operator scripts, supported source-of-truth contracts,
  consumer rules, internal-only surfaces, explicitly-unsupported
  claims, versioning/change rule, restart condition

New validation test:

- `tests/test_public_surface_contract.py` — 12 cases (existence, label
  vocabulary, internal-default rule, banned-vocabulary cross-reference,
  unsupported-claims section, every referenced doc path resolves,
  every referenced script path resolves, supported HTTP routes listed,
  comparative-evidence script listed, no banned current-claim word in
  positive context outside the unsupported-claims section, no
  positive-assertion sentence claims release-ready / parity /
  replacement / equivalent / production-grade, floor 3.6 caveat
  recorded)

Modified docs:

- `docs/source-of-truth/master-outline.md` — index entry 134 for
  `public-surface.md`; `Updated:` bumped to `2026-04-28`
- `docs/source-of-truth/release-readiness-execution-plan.md` — §6 now
  records the 3.7A outcome (alongside the parallel 3.6A entry), the
  supported-surface scope, the validation test summary, and the
  no-ledger-flip discipline

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-7A-public-surface-freeze-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not**
modified per §6 / §10 of the 3.7A prompt.

## 4. Supported Public Surface Summary

Per `public-surface.md` §3 / §4 / §5 / §6.

Supported HTTP routes:

- liveness/status: `GET /healthz`, `GET /v1/runtime/status`
- generation + compatibility: `POST /v1/generate`,
  `POST /v1/generate/stream`, `POST /v1/chat/completions`,
  `POST /v1/completions`, `POST /v1/messages`,
  `POST /v1/messages/count_tokens`
- lifecycle / inventory: `POST /v1/load`, `POST /v1/unload`,
  `POST /v1/runtime/restart`, `GET /v1/openai/models`,
  `GET /v1/models`, `GET /v1/runtime/model-visibility`
- release-floor contract surfaces: `/v1/runtime/orchestration-status`,
  `/v1/runtime/scheduler-admission-contract`,
  `/v1/runtime/request-context-length-truth`,
  `/v1/runtime/model-residency-policy`,
  `/v1/runtime/memory-pressure-contract`,
  `/v1/runtime/recovery-supervisor-contract`,
  `/v1/runtime/nonresident-loadability-lineage`,
  `/v1/runtime/nonresident-model-admission-policy`,
  `/v1/runtime/memory-pressure-eviction-policy`,
  `POST /v1/runtime/memory-pressure-eviction`,
  `/v1/runtime/reclaim-barrier-event`,
  `/v1/runtime/termination-recovery-policy`,
  `/v1/runtime/comparative-evidence`,
  `/v1/runtime/comparative-evidence/history`

Supported runtime modules: `owlmlx.runtime`, `owlmlx.runtime.server`,
`owlmlx.serving`, `owlmlx.memory_budget`, `owlmlx.context_concurrency`,
`owlmlx.abort_recovery`, `owlmlx.runtime_health`, `owlmlx.model_inventory`,
`owlmlx.model_lineage`, `owlmlx.cache_truth`,
`owlmlx.runtime_model_visibility`, `owlmlx.comparative_evidence_record`,
`owlmlx.comparative_evidence_schema`, `owlmlx.comparative_evidence_ledger`,
`owlmlx.comparative_evidence_runner` (`partial`),
`owlmlx.memory_pressure_eviction_policy`,
`owlmlx.nonresident_model_admission_policy`,
`owlmlx.nonresident_loadability_lineage`,
`owlmlx.recovery_supervisor_contract`,
`owlmlx.termination_recovery_policy`, `owlmlx.reclaim_barrier_event`,
`owlmlx.scheduler_admission_contract`, `owlmlx.orchestration_status`,
`owlmlx.model_residency_policy`, `owlmlx.memory_pressure_contract`,
`owlmlx.runtime_status`.

Supported operator scripts:
`scripts/runtime_comparative_evidence.py`,
`scripts/runtime_mlx_environment_readiness.py`,
`scripts/runtime_mlx_blocker_report.py`,
`scripts/runtime_mlx_host_forensics.py`,
`scripts/runtime_mlx_probe_matrix.py`,
`scripts/runtime_large_weight_specimen_gate.py`,
`scripts/runtime_large_weight_first_smoke.py`,
`scripts/runtime_large_weight_first_smoke_decision.py`.

Supported source-of-truth contracts: `AGENTS.md` plus 25 docs under
`docs/source-of-truth/` (see `public-surface.md` §6 for the exhaustive
list).

## 5. Internal-Only Rule Summary

Anything not listed in `public-surface.md` is `internal` by default. The
explicit internal listing (§8) names: the entire `scripts/runtime_cache_*`
family (~80 phase45 exactness operator entries), the
`scripts/runtime_multi_model_governance_*` family (`partial` observation
status), every `owlmlx.cache_*` module (pre-claim marker / admission
carrier exactness, scheduler/TurboQuant split surfaces,
request-aggregation exactness), every `phase45-*.md` doc except those
linked from §6, every `RuntimeKernel` `_*` private method, and the
comparative-evidence runner's per-attempt artifact internal layout
beyond what `comparative-evidence-harness-contract.md` and the 3.5D
handoff freeze.

`omlx` and `vmlx` are reference runtimes (`not in scope` per §9).

## 6. Tests Run And Results

```text
$ pytest -q tests/test_public_surface_contract.py
............                                                             [100%]
12 passed in 0.01s

$ python3 -m py_compile owlmlx/runtime/server.py
COMPILE_OK

$ git diff --check
DIFF_CHECK_CLEAN
```

The full prompt §7 verification matrix is satisfied. No broader runtime
test was added because the release floor is about public surface truth,
not new runtime code.

## 7. Closeout Recommendation

`closed_recommended`. Coordinator closeout may flip
`release-readiness-backlog.md` row `3.7 public surface` from
`open` to `closed (via runtime-owned public-surface freeze)` with
references to `public-surface.md`,
`tests/test_public_surface_contract.py`, and this 3.7A handoff. If the
parallel `3.6A` outcome
(`owlmlx_release_floor_3_6A_external_customer_evidence_pass_candidate`)
also clears closeout review, the same coordinator round may flip both
rows and bring the section-2 floor count from `5/7` to `7/7`. If
`3.6A` does not clear, `3.7` may still close on its own; the ledger
rows are independent.

## 8. Exact Blocker

None. The deliverables (frozen public-surface doc, validation test,
honest verdict, deferred scope) are all complete; there is no conflict
with the parallel `3.6A` lane. The only remaining action is the
coordinator closeout flip, which by §6 of the 3.7A prompt is owned
outside this lane.

## 9. Confirmation Of Discipline

- **No release / parity / replacement / production-grade / superiority
  / wins / beats / equivalent / matches claim**: confirmed. The
  validation test
  `test_public_surface_does_not_make_banned_current_claims` and
  `test_public_surface_does_not_assert_owlmlx_is_replacement_or_parity`
  enforce both line-level and direct-assertion absence of banned
  current claims; they pass.
- **Floor `3.7` not marked closed in the backlog**: confirmed. This
  handoff explicitly leaves the ledger flip to coordinator closeout.
- **No floor `3.6` work performed in this lane**: confirmed. The
  public-surface doc only references the open status of `3.6` to be
  honest; it does not edit the `3.6` ledger row, the
  customer-runtime-evidence ledger, or any `3.6A` evidence directory.
- **No internal phase45 exactness doc exposed as public**: confirmed.
  §8 lists the entire `scripts/runtime_cache_*` family, every
  `owlmlx.cache_*` module, and every `phase45-*` doc except those
  linked from §6 (and only `phase45-customer-runtime-evidence-ledger`
  is implicitly linked because it backs floor `3.6` evidence — it is
  **not** listed in §6 here as a supported public contract).
- **No external repo edits**: confirmed. `git status` shows only
  owlmlx-internal paths. No `owlops`, `owlcoda`, desktop UI, or
  `/Users/yeemio/AI/Agent` path was touched.
- **Unrelated dirty/staged work preserved**: confirmed. `git diff
  --check` is clean.
