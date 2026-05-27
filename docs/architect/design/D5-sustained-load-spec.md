# D5 · Design-Grade Spec · 128G Sustained Load N≥20 Repeatability

> **Gate**: Campaign D5 · DSV4-Flash 2bit-DQ sustained-load N≥20 repeatability through the mainline backend path established by D6
> **Plan-grade source**: [`../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md)
> **Prerequisite**: D6 passed 2026-05-27 under amended §7.1 item 7 (intra-run RSS stability gate); see [`D6-mainline-backend-integration-spec.md`](D6-mainline-backend-integration-spec.md) §7.3
> **Companion**: Campaign A N≥20 evidence schema (`scripts/runtime_repeatability_campaign.py` + `owlmlx.repeatability_statistics`) — D5 reuses Campaign A's `campaign_label=repeatability_evidence` semantics
> **Status**: design-grade · 2026-05-27
> **Non-goal**: this spec does not claim D5 promotes DSV4-Flash 2bit-DQ to `partial`; D5 keeps `experimental_only`. `partial` requires D5 + D6 + D7 jointly per plan-grade §6.

---

## 1. Purpose

D5 produces the missing **N≥20 same-prompt repeatability** evidence for DSV4-Flash 2bit-DQ on the 128 GB host through the **same mainline backend path** D6 established:

```text
D1 (2026-05-17): 5 prompts × 3 token ladder × 1 generation each = 15 generations (passed)
D2 (2026-05-17): 6 metric rows (passed)
D6 (2026-05-27): 6-row matrix on mainline backend path (passed under amended §7.1 item 7)

D5 missing evidence shape (this spec):
  preflight (D6 path verified)
  -> backend.load (one session)
  -> 20 rounds of same prompt × same max_tokens, all in one loaded session
  -> backend.unload
  -> clean post-unload health
  -> evidence: per-round JSONL + run-level rollup with Campaign A statistics
```

D5 answers plan-grade §3 question (a): "sustained load N≥20 rounds 下保持内存稳定（无漂移）" and (d) "sustained load 后 backend health 与 settle barrier 保持 clean".

### 1.1 Why D5 uses the D6 mainline backend path (not the D1 isolated harness)

Plan-grade §5 stage table reads "在 isolated lane（不动 backend path）", but plan-grade §3.2 and §13 sequencing both require D5 to depend on D6's backend path being live. D5 design-spec resolves the inconsistency in favor of the §3.2/§13 reading because:

1. D6 is now passed (2026-05-27), so the mainline backend path exists and is reachable.
2. N≥20 evidence is meaningful only if the path under test is the **path that production consumers (D7 visibility tier) will actually use**. The D1 isolated harness is not that path.
3. Running D5 on the D6 path also implicitly retests D6 lifecycle correctness over 20 cycles — strictly more rigorous than the 6-row D6 acceptance.
4. The plan-grade §5 "isolated lane" wording was drafted before D6 design-spec resolved the path question; this D5 design-spec supersedes it.

The plan-grade text is left as-is (no edits) since the §3.2/§13 reading is internally consistent and authoritative.

---

## 2. Scope

### 2.1 In

| Item | Requirement |
|---|---|
| Runtime environment | `.runtime-deepseek-experimental/` populated per D6 spec §3.2 (already established 2026-05-27) |
| Backend class | `MlxLmSubprocessBackend` (same as D6); reused via the `mainline` subcommand's backend factory or extended by a new `sustained` subcommand (§8) |
| mlx-lm source pin | Blaizzy fork commit `5c10538136b9038b9626c134612b08afc18d697a` (locked by D6) |
| Model artifact | `DeepSeek-V4-Flash-2bit-DQ` at `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ` |
| Prompt | Single fixed prompt: `p2_short_en` ("Answer in two concise English sentences about runtime isolation.") |
| `max_tokens` | 512 (D2 baseline row exists at `p2_short_en × 512` for advisory cross-validation) |
| Round count `N` | 20 (default; configurable upward via CLI but ≥20 is the gate) |
| Lifecycle phases | preflight (D6 verified) → load → 20 rounds → unload → clean health |
| Statistics schema | Campaign A schema via `owlmlx.repeatability_statistics.compute_repeatability_statistics` |
| Evidence path | `files/evidence/owlmlx/deepseek-v4/d5-sustained-load/` |
| Capability label | `experimental_only` (D5 alone does not promote) |
| Visibility surface | unchanged (`visibility_status=not_registered`; D7 handles registration) |

### 2.2 Out

- Multi-prompt N≥20 matrices (D5 is single-prompt sustained-load; multi-prompt versions are future scope, not part of D5 or the plan-grade campaign D upgrade)
- DSV4-Pro / 4bit / 8bit / FP16 variants
- Visibility registration on any surface (D7)
- MTP speculative path on DSV4 (D8 far term)
- Any update to [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope (D7 owns that change)
- Measured TPS comparison against oMLX / vMLX (banned per [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §3)
- New module under `owlmlx/` (per [[project-owlmlx-agents-module-as-spec-rule]])
- Modification of mlx-lm upstream or transformers upstream
- Promotion of [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) DSV4 row
- Re-running D6 (D5 is layered on top; if D6 evidence is invalidated, D5 must be rerun from scratch in a separate round)

---

## 3. Configuration Reuse From D6

D5 inherits **every** D6 configuration choice without modification. The following are passed through verbatim:

| Knob | Value | Source |
|---|---|---|
| `python_executable` | `.runtime-deepseek-experimental/bin/python` | D6 spec §4.2 |
| `timeout_s` | 900.0 (per-request, applied per round) | D6 spec §4.2 |
| `auto_restart_dead_session` | `False` (D5 fails loudly on restart, never silently recovers across the 20 rounds) | D6 spec §4.2 |
| `max_restart_attempts` | 0 | D6 spec §4.2 |
| `model_path_resolver` | `None` (model_id is the absolute artifact path) | D6 spec §4.2 |
| Backend probe pre-load | `_probe_model_type_support` resolves `mlx_lm.models.deepseek_v4` against the D6 venv | D6 spec §4.1 |

D5 does NOT modify:

- `pyproject.toml` (D6 already added the `deepseek-experimental` extras group)
- `MlxLmSubprocessBackend.__init__` signature
- `_probe_model_type_support` / `_read_model_type_from_config` in [`owlmlx/runtime/mlx_lm_subprocess_backend.py`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py)
- The `.runtime-deepseek-experimental/` venv contents
- Any existing harness subcommand (`preflight`, `dry-run`, `run`, `compare`, `metrics`, `mainline`, `checkpoint-inspect`, `mtp-preload-reject`)

D5's only code surface is a **new** harness subcommand `sustained` (§8) plus its CLI argparse registration. No `owlmlx/` package change. No new test files (extend `tests/test_deepseek_v4_d1_repeatability.py` and `tests/test_mlx_native_backend_real_smoke.py` per §8.4).

---

## 4. Lifecycle Run Shape

### 4.1 Preflight (lighter than D6's; reuses D6 attestation)

```yaml
preflight:
  d6_prerequisite_passed: true                # gates D5; verified by D6.1 reclassification attestation
  d6_evidence_path: files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/
  d6_accepted_run_id: 20260527T072206Z-d6-mainline-backend-lifecycle
  d6_acceptance_source:
    evidence_summary: files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/20260527T072206Z-d6-mainline-backend-lifecycle.summary.json
    reclassification_spec: docs/architect/design/D6-mainline-backend-integration-spec.md §7.3 / §12
    model_release_candidate_ledger: files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl
    quality_caveat: deepseek_v4_flash_2bit_dq_mainline_backend_integration=passed
  mainline_runtime_path: .runtime-deepseek-experimental
  python_executable: .runtime-deepseek-experimental/bin/python
  model_type_support_probe.supported: true   # same probe as D6
  mlx_lm_source.git_commit: 5c10538136b9038b9626c134612b08afc18d697a
  backend_class: MlxLmSubprocessBackend
  model_artifact_path: /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ
  prompt_id: p2_short_en
  max_tokens: 512
  round_count_N: 20
  d2_baseline_pointer:
    file: files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl
    row_selector: {prompt_id: p2_short_en, max_tokens: 512}
    advisory_only: true                      # per D6 §6.5 lesson; not a gate
  d6_baseline_pointer:
    file: files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/20260527T072206Z-d6-mainline-backend-lifecycle.jsonl
    row_selector: {prompt_id: p2_short_en, max_tokens: 512}
    advisory_only: true                      # diagnostic only; D5 vs D6 single-run divergence is not a gate
  stock_runtime_untouched: true
  default_model_surface_unchanged: true
```

Preflight fails (`blocked`) when any of:

- `d6_prerequisite_passed=false` (no D6.1 acceptance attestation for `20260527T072206Z-d6-mainline-backend-lifecycle` in the D6 spec / model-release-candidate ledger)
- `model_type_support_probe.supported=false`
- `mlx_lm_source.git_commit != 5c10538136b9038b9626c134612b08afc18d697a` (soft warning, logged but does not fail)
- `model_artifact_path` missing or unreadable
- `round_count_N < 20`

### 4.2 Lifecycle yaml

```yaml
lifecycle:
  load:
    timeout_s: 900
    max_load_time_s_expected: 60      # consistent with D6
    record_fields:
      - load_time_s
      - pid
      - runner_model_id
      - returncode
  rounds:
    count_N: 20
    prompt_id: p2_short_en
    max_tokens: 512
    prompt_surface: messages
    generation_surface: stream_generate_messages
    fixed_messages_sha256: <stable across all 20 rounds; pin in evidence>
    per_round_record_fields:
      - round_index            # 0..19
      - ttft_ms
      - stream_wall_ms
      - prompt_tokens
      - completion_tokens
      - decode_tps_after_first_token
      - wall_tps
      - child_rss_gb
      - rss_sample_scope: child_process
      - rss_sample_source: ps_rss_kb
      - rss_sample_timing: after_generation_before_next_round
      - restart_observed: false       # MUST be false for every round
      - repetition_flag: false        # MUST be false for every round
      - stop_reason: stop | length | <other>
      - backend_status_healthy: <bool after this round>
  unload:
    timeout_s: 60
    expected_freed_gb_lower_bound: 80
    record_fields:
      - unload_time_s
      - freed_gb
      - returncode
  health:
    sample_points:
      - before_load
      - after_load
      - after_each_round
      - after_unload
    snapshot_fields:
      - backend.status().healthy
      - backend.status().loaded_models
      - backend.status().backend_name
      - child_restart_count             # MUST remain 0 throughout D5
```

### 4.3 Single load session, fixed prompt

D5 runs all 20 rounds in **one** loaded session (single `backend.load`). The prompt is the same byte sequence for every round; the `fixed_messages_sha256` field in the evidence pins this. The first round carries the cold TTFT; rounds 2-20 are warm. This is the canonical Campaign A sustained-load shape.

A child restart at any point during the 20 rounds fails D5 (per `auto_restart_dead_session=False`).

### 4.4 Post-unload clean-health check (identical to D6 §5.4)

After `backend.unload(model_id)`:

```python
status = backend.status()
assert status.healthy is True
assert status.loaded_models == ()
assert status.backend_name == "mlx-lm-subprocess"
```

---

## 5. Evidence Schema

### 5.1 Per-round JSONL record

```yaml
schema_version: d5.sustained-load.v1
record_type: sustained_load_round
gate: D5
run_id: <ts>-d5-<descriptor>
created_at_utc: <ISO-8601 Z>
model_id: DeepSeek-V4-Flash-2bit-DQ
backend_class: MlxLmSubprocessBackend       # explicit; D5 runs through the D6 mainline path
backend_path:
  python_executable: <absolute>
  runner_module: owlmlx.runtime.mlx_lm_runner
  deepseek_experimental_extras_active: true
  mlx_lm_source:
    git_commit: 5c10538136b9038b9626c134612b08afc18d697a
    package_version: <version>
campaign_label: repeatability_evidence       # Campaign A semantics: requires N ≥ 20
prompt_surface: messages
generation_surface: stream_generate_messages
prompt_id: p2_short_en
max_tokens: 512
fixed_messages_sha256: <stable across all 20 rounds in a single run>
round_index: <int, 0..19>
metrics:
  load_time_s: <float, carried per row from single load>
  ttft_ms: <float>
  stream_wall_ms: <float>
  prompt_tokens: <int | null>
  completion_tokens: <int>
  decode_tps_after_first_token: <float>
  wall_tps: <float>
  child_rss_gb: <float>
  rss_sample_scope: child_process
  rss_sample_source: ps_rss_kb
  rss_sample_timing: after_generation_before_next_round
backend_health_snapshot_after_this_round:
  healthy: <bool>
  loaded_model_count: 1
  child_restart_count: 0
host_state:
  unified_memory_gb_capacity: 128
  watermark_observed: GREEN | YELLOW | RED | FATAL | UNKNOWN   # see §5.3
verdict: passed | failed
verdict_reason: <string, optional; populated on non-passed>
```

### 5.2 Run-level rollup record (`<run_id>.summary.json`)

```yaml
schema_version: d5.sustained-load.run.v1
run_id: <ts>-d5-<descriptor>
created_at: <ISO-8601 Z>
gate: D5
campaign_label: repeatability_evidence       # only true when rows_written ≥ 20
preflight: passed | blocked | failed
preflight_detail: <§4.1 yaml>
rounds_attempted: 20
rounds_passed: 20
rounds_failed: 0
backend_class: MlxLmSubprocessBackend
mlx_lm_git_commit: 5c10538136b9038b9626c134612b08afc18d697a

repeatability_statistics:                    # Campaign A schema; see §5.3
  ttft_ms:
    all_rounds: {count: 20, mean: <>, stddev: <>, cv: <>, min: <>, p50: <>, max: <>}
    warm_rounds_2_to_20: {count: 19, mean: <>, stddev: <>, cv: <>, min: <>, p50: <>, max: <>}
  decode_tps_after_first_token:
    all_rounds: {count: 20, mean: <>, stddev: <>, cv: <>, min: <>, p50: <>, max: <>}
  wall_tps:
    all_rounds: {count: 20, mean: <>, stddev: <>, cv: <>, min: <>, p50: <>, max: <>}
  child_rss_gb:
    all_rounds: {count: 20, min: <>, max: <>, range: <>, p50: <>}

intra_run_stability:                         # gate per §6
  child_rss_gb_range_gb: <float>             # max - min across 20 rounds; must be ≤ 1.0
  child_rss_gb_max_gb: <float>               # observed max; sanity ≤ 30 GB
  decode_tps_cv_all_rounds: <float>          # must be ≤ 0.20 (Campaign A bar)
  ttft_ms_cv_warm_rounds: <float>            # rounds 2-20; must be ≤ 0.30
  monotonic_rss_growth_detected: <bool>      # diagnostic: is RSS strictly non-decreasing?
  within_threshold: <bool>

cross_validation:                            # ADVISORY per §6.5 of D6 spec (inherited rule)
  vs_d2_baseline:
    decode_tps_diff_rel: <float>
    ttft_ms_warm_diff_rel: <float>
    child_rss_gb_diff_abs: <float>
  vs_d6_baseline:
    decode_tps_diff_rel: <float>
    ttft_ms_warm_diff_rel: <float>
    child_rss_gb_diff_abs: <float>

backend_health_summary:
  child_restart_observed: false
  clean_health_after_unload: true
  unload_freed_gb: <float, must be ≥ 80>
  unload_time_s: <float>

host_state_summary:
  worst_watermark_observed: GREEN | YELLOW | RED | FATAL | UNKNOWN
  watermark_red_or_fatal_observed: false      # MUST be false

overall_conclusion: passed | blocked | failed
verdict: passed | blocked | failed
lifecycle_path: <jsonl path>
summary_path: <this file's path>
```

### 5.3 Statistics computation

D5 reuses [`owlmlx.repeatability_statistics`](../../../owlmlx/repeatability_statistics.py) to compute mean / stddev / CV / min / p50 / max from the per-round metric arrays. The statistics are computed in two slices:

1. **`all_rounds`** (N=20) — used for `decode_tps_after_first_token`, `wall_tps`, `child_rss_gb`.
2. **`warm_rounds_2_to_20`** (N=19, excludes round 0) — used for `ttft_ms` only, because round 0 is cold and has a structurally different TTFT (D2 baseline shows cold TTFT of ~45 s vs warm ~250 ms for the same prompt).

`CV` (coefficient of variation) is `stddev / mean`. It is a dimensionless stability index; lower is more stable.

### 5.4 Host watermark sampling

D5 samples host unified memory pressure per round via `vm_stat` (macOS) or equivalent. The sample is classified into the existing owlmlx `MemoryWatermark` enum (`GREEN < YELLOW < RED < FATAL`, see [`owlmlx/memory_watermark.py`](../../../owlmlx/memory_watermark.py)) using the same thresholds (65% / 80% / 90%). The harness reads pressure via subprocess `vm_stat`; it does NOT depend on an owlmlx runtime server being live.

If `vm_stat` is unavailable or fails to parse, the watermark is recorded as `UNKNOWN` and that round does not fail on host_state grounds alone.

### 5.5 Evidence directory layout

```text
files/evidence/owlmlx/deepseek-v4/d5-sustained-load/
  <ts>-d5-sustained-load.jsonl                 # 20 rows, one per round
  <ts>-d5-sustained-load.summary.json
```

Per plan-grade §10, the two-file scheme `<ts>-d5-128g-sustained-load-n20.jsonl` + `<ts>-d5-128g-sustained-load-rollup.jsonl` is a capacity ceiling; D5 design-spec collapses to one jsonl + one summary json (same shape as D6 §6.3).

### 5.6 Banned ledger row

D5 evidence MUST NOT contain `comparative_ledger`, `reference_runtime_comparison_*` populated blocks, or any `oMLX_*`/`vMLX_*` field. Cross-validation in §5.2 is **D5-versus-D2/D6 self-comparison only** (advisory) and never against external reference runtimes. Banned per [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §3.

---

## 6. Acceptance / Pass Criteria

D5 hard gates (every one is necessary):

1. **Preflight passed** (§4.1): D6 prerequisite verified, model_type probe supported, model artifact present, N≥20.
2. **20/20 rounds completed** with `restart_observed=false` and `repetition_flag=false` on every round. A `done` event must be present for every round.
3. **Backend health clean after unload**: `backend.status().healthy is True`, `loaded_models == ()`.
4. **Unload freed_gb ≥ 80**.
5. **Intra-run `child_rss_gb` stability**: `max - min across 20 rounds ≤ 1.0 GB`, AND observed max ≤ 30 GB ceiling. (Looser than D6's 0.5 GB intra-run gate because 20 rounds vs 6 rounds gives more room for legitimate small accumulation, but still tight enough to catch any GB-scale leak.)
6. **`decode_tps_after_first_token` CV ≤ 0.20 across all 20 rounds** (Campaign A's TPS CV bar; follows [`01-mainline-roadmap.md` line 224](../01-mainline-roadmap.md#L224)).
7. **`ttft_ms` CV ≤ 0.30 across warm rounds 2-20** (relaxed from Campaign A's 0.10 to account for DSV4 first-token-prefill variance; round 0 cold TTFT is excluded from this gate but recorded in the per-round JSONL).
8. **No `RED` or `FATAL` watermark observed** during any of the 20 rounds (`UNKNOWN` is allowed when `vm_stat` cannot run).
9. **Cross-validation against D2 and D6 baselines is recorded but advisory only** per D6 spec §6.5 lesson — any drift is diagnostic, not gating.
10. **No `owlmlx/` package change** during D5 code-grade; harness extension + test extension only (per [[project-owlmlx-agents-module-as-spec-rule]]).

### 6.1 Capability-label invariants after D5 passes

D5 passing does **NOT** change:

- [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) — DSV4 row stays at `experimental`.
- [`owlmlx/model_release_candidate_record.py:39-47`](../../../owlmlx/model_release_candidate_record.py:39) — DSV4 entry stays at `lane=flagship_experimental`, `visibility_status=not_registered`, `verdict=experimental_only`.
- [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope — unchanged.
- [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) — no claim change.

D5 produces a `model_release_candidate_record` JSONL row under `files/evidence/owlmlx/model-release-candidates/` marking `deepseek_v4_flash_2bit_dq_128g_sustained_load=passed` per [plan §6](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md#6-acceptance-wording). The `partial` matrix-level promotion still waits for D5 + D6 + D7 joint; D5 alone does NOT promote.

### 6.2 What happens if D5 fails

A D5 failure does NOT invalidate D6. D6 evidence stands. D5 simply remains the dominant gap until either:

- The failure is a transient host-condition (e.g., RED watermark during a noisy host run) → reschedule and retry.
- The failure is a real RSS leak (range > 1.0 GB) → triage the runner-level memory behavior; this becomes a `failed` D5 round and may need a fresh round (D5.1) to investigate.
- The failure is a CV-budget overflow → triage stream protocol or sampler variance; reassess gate thresholds if the budget itself was overconfident (the D6.1 calibration lesson applies symmetrically — but only after measurement, not in advance).

---

## 7. Failure Semantics

| # | Failure | Classification | Where surfaced | Next action |
|---|---|---|---|---|
| 1 | D6 prerequisite not found (no D6.1 acceptance attestation for `20260527T072206Z-d6-mainline-backend-lifecycle` in the D6 spec / model-release-candidate ledger) | `blocked` | preflight | run or reclassify D6 first; do not proceed to D5 |
| 2 | `_probe_model_type_support` returns `supported=False` (extras missing) | `blocked` | preflight | re-populate `.runtime-deepseek-experimental/` per D6 spec §3.2 |
| 3 | `MlxLmSubprocessBackend.load` returns `ok=False` | `failed` | lifecycle.load | capture stderr; classify Metal OOM vs broken_pipe_child_lost per D6 spec §8 row 3 |
| 4 | Any round's `restart_observed=true` | `failed` | lifecycle.rounds | record the round_index; this is a major sustained-load failure mode |
| 5 | Any round's `repetition_flag=true` | `failed` | lifecycle.rounds | record; classify per [`D1-spec.md`](D1-spec.md) repetition diagnostics |
| 6 | `child_rss_gb` intra-run range > 1.0 GB OR observed max > 30 GB | `failed` | intra_run_stability | record per-round RSS array; this is the primary memory-leak detector |
| 7 | `decode_tps_after_first_token` CV > 0.20 (all rounds) | `failed` | intra_run_stability | record CV; investigate whether KV cache growth or thermal throttling caused the spread |
| 8 | `ttft_ms` CV > 0.30 (warm rounds 2-20) | `failed` | intra_run_stability | record CV; investigate prefill stability |
| 9 | Any round observes `RED` or `FATAL` watermark | `blocked` | host_state | this is host-noise, not a runtime defect; reschedule when host is idle |
| 10 | Post-unload `backend.status()` reports `loaded_models != ()` OR `healthy=False` | `failed` | health.after_unload | backend health pollution after 20 cycles; investigate child shutdown sequence |
| 11 | `unload.freed_gb < 80` | `failed` | lifecycle.unload | unload did not actually release weights; investigate Metal allocator |
| 12 | Stdout transport corruption during any round | `failed` | lifecycle.rounds | record per D6 spec §8 row 10; D6 path-level issue but surfaces in D5 context |

`blocked` ≠ `failed`:
- `blocked` means D5 cannot run as designed; resolve external/environmental issue and retry.
- `failed` means D5 ran as designed and did not meet the bar; capability-label remains unchanged.

---

## 8. Harness Requirements

### 8.1 New `sustained` subcommand in the D1 repeatability harness

D5 adds **one** new subcommand to [`scripts/bench/deepseek_v4_d1_repeatability.py`](../../../scripts/bench/deepseek_v4_d1_repeatability.py) alongside the existing 8 subcommands. No existing subcommand is modified.

```text
uv run python scripts/bench/deepseek_v4_d1_repeatability.py sustained \
    --run-id <ts>-d5-sustained-load \
    --backend-python .runtime-deepseek-experimental/bin/python \
    --model-path /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ \
    --prompt-id p2_short_en \
    --max-tokens 512 \
    --round-count 20 \
    --d6-passed-evidence files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/20260527T072206Z-d6-mainline-backend-lifecycle.summary.json \
    --d2-baseline files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl \
    --evidence-dir files/evidence/owlmlx/deepseek-v4/d5-sustained-load \
    --timeout-s 900
```

### 8.2 `run_sustained` function contract (code-grade scope)

The new `run_sustained(...)` function in the harness MUST:

1. **Preflight**: read the D6.1 acceptance attestation rather than trusting the original D6 summary verdict alone. The 2026-05-27 D6 evidence summary was produced before D6.1 amended the gate, so code-grade MUST accept either (a) a future D6 summary with `overall_conclusion=passed` and `intra_run_stability.within_threshold=true`, or (b) the committed D6.1 attestation chain: D6 spec §7.3/§12 plus a model-release-candidate ledger row whose `quality_caveats` include `deepseek_v4_flash_2bit_dq_mainline_backend_integration=passed` and whose pointer references `20260527T072206Z-d6-mainline-backend-lifecycle.summary.json`. On miss, emit `blocked` summary and exit non-zero.
2. **Probes**: reuse `_d6_probe_model_type_support` and `_d6_runtime_provenance` from the D6 code path (no new probe code).
3. **Backend construction**: identical to D6 `run_mainline` (python_executable, timeout_s=900, auto_restart_dead_session=False, max_restart_attempts=0). Backend factory MUST be injectable for tests.
4. **Snapshot `backend.status()` -> `health.before_load`.**
5. **`backend.load(<model_path>, memory_gb=100.0)`** with the same load-timing instrumentation as `run_mainline`.
6. **20 rounds in one session**:
   - Resolve `messages` via the existing harness helper `_messages_for_prompt(_prompt_by_id(args.prompt_id))`.
   - Compute `fixed_messages_sha256` once (must match every round's payload bytes).
   - For each round 0..19:
     - Call `backend.stream_generate_messages(model_id, messages, max_tokens=...)`.
     - Compute per-round TTFT, stream_wall_ms, decode_tps, wall_tps via the same formulas as `run_mainline`.
     - Sample `child_rss_gb` via `_process_rss_gb(pid)`.
     - Sample host watermark via `_d5_sample_host_watermark()` (new helper).
     - Snapshot `backend.status()` after the round.
     - Append per-round JSONL row.
7. **`backend.unload(<model_path>)`** with same unload-timing instrumentation.
8. **Compute repeatability statistics** via `owlmlx.repeatability_statistics.compute_repeatability_statistics`.
9. **Compute cross-validation** against D2 and (optional) D6 baseline rows for `(p2_short_en, 512)`.
10. **Write `<run_id>.summary.json`** per §5.2.
11. **Exit 0** iff `overall_conclusion=passed`, else 1.

### 8.3 Forbidden harness changes

The `sustained` subcommand MUST NOT:

- Modify any function used by `preflight`, `dry-run`, `run`, `compare`, `metrics`, `mainline`, `checkpoint-inspect`, or `mtp-preload-reject`.
- Touch `.runtime-deepseek-v4-mlx/` (D1-D4 isolated lane).
- Spawn any subprocess except those owned by `MlxLmSubprocessBackend` plus the `vm_stat` subprocess for watermark sampling.
- Touch `owlmlx/` package source (read-only imports are fine).
- Write `model_release_candidate_record` rows directly; the post-run amendment to `cumulative-ledger.jsonl` is a separate user-side action, following the D6 staged-publication pattern.

### 8.4 Test extension

#### 8.4.1 Unit tests in `tests/test_deepseek_v4_d1_repeatability.py`

Three new unit tests (extend, do not create new file):

1. `test_sustained_writes_d5_evidence_on_happy_path` — fake backend, 20 rounds, all pass, intra-run RSS stability gate satisfied, statistics computed.
2. `test_sustained_flags_intra_run_rss_drift_as_failed` — fake backend with stepping RSS samples crossing 1.0 GB range across 20 rounds.
3. `test_sustained_emits_blocked_when_d6_prerequisite_missing` — preflight without a passed D6 evidence summary.

Tests use the same `_DSV4FakeBackend` + `_mock_d6_probes` helpers introduced for D6 unit tests. The fake backend gains a `round_capacity` parameter so it can simulate 20 calls without test runtime exceeding ~1 second (per-call sleep stays at ~10ms).

#### 8.4.2 Env-gated real smoke in `tests/test_mlx_native_backend_real_smoke.py`

One new env-gated test (extend, do not create new file):

`test_dsv4_subprocess_backend_sustained_load_n20` — gated by `OWLMLX_DSV4_SUSTAINED_SMOKE_PYTHON` / `OWLMLX_DSV4_SUSTAINED_SMOKE_MODEL_PATH` (separate from D6 env vars so users can opt into sustained load specifically). Runs 20 rounds of `p2_short_en × 512` through `MlxLmSubprocessBackend`; asserts all 20 complete, intra-run RSS range ≤ 1.0 GB, no restart, clean post-unload health.

### 8.5 No new modules

Per [[project-owlmlx-agents-module-as-spec-rule]], D5 code-grade MUST NOT create:

- New files under `owlmlx/`
- `*_contract.py`, `*_evidence.py`, `*_harness.py`, `*_ledger.py` modules anywhere
- New `tests/test_*` files (extend the two existing files only)
- New `scripts/bench/*` files (extend `deepseek_v4_d1_repeatability.py` only)

---

## 9. Inter-Path Divergence Awareness (Inherited From D6 §6.5)

D5's cross-validation block (§5.2) compares against D2 baseline AND the D6 passed run. Both comparisons are **advisory diagnostic only** per the D6.1 lesson:

- The D2 isolated-harness path and the D6/D5 mainline-backend path have a known structural 14 GB `child_rss_gb` offset (D6 spec §6.5.1). D5 absolute `child_rss_gb` values will be in the same ~21 GB band as D6, not the ~7 GB band of D2.
- D5 vs D6 comparison (same path, different round count) is a single-run comparison; one-sample diff is not a stability claim. D5's own 20-round CV statistics are the stability claim.
- TTFT cold round 0 will likely differ from D2's cold TTFT (D6 measured ~3x faster cold TTFT than D2); this is a documented path characteristic, not a regression.

D5 spec therefore does NOT introduce any new cross-path equivalence gate. The only stability gates D5 uses are **intra-D5-run** (§6 items 5, 6, 7).

---

## 10. Review Checklist

Code-grade review MUST verify each box explicitly:

- [ ] D5 spec references the D6.1-accepted evidence run by exact filename in preflight; preflight verifies either a future `overall_conclusion=passed` D6 summary or the committed D6.1 attestation chain (D6 spec §7.3/§12 + model-release-candidate ledger `quality_caveats` entry).
- [ ] The new `sustained` subcommand in [`scripts/bench/deepseek_v4_d1_repeatability.py`](../../../scripts/bench/deepseek_v4_d1_repeatability.py) is registered alongside (not replacing) the existing 8 subcommands.
- [ ] The new `run_sustained` function reuses `_d6_probe_model_type_support` and `_d6_runtime_provenance` without modification.
- [ ] `MlxLmSubprocessBackend` is constructed with the same kwargs as D6 `run_mainline` (python_executable, timeout_s=900, auto_restart_dead_session=False, max_restart_attempts=0). No new kwargs are added to `MlxLmSubprocessBackend.__init__`.
- [ ] 20 rounds run in one loaded session; `fixed_messages_sha256` is identical across all 20 rounds; restart_observed is false on every round.
- [ ] Statistics are computed via [`owlmlx.repeatability_statistics`](../../../owlmlx/repeatability_statistics.py) (not reimplemented in the harness).
- [ ] `intra_run_stability` block in the summary contains `child_rss_gb_range_gb`, `child_rss_gb_max_gb`, `decode_tps_cv_all_rounds`, `ttft_ms_cv_warm_rounds`, `within_threshold`.
- [ ] `child_rss_gb_range_gb ≤ 1.0` AND `child_rss_gb_max_gb ≤ 30` (gate per §6 item 5).
- [ ] `decode_tps_cv_all_rounds ≤ 0.20` (gate per §6 item 6).
- [ ] `ttft_ms_cv_warm_rounds ≤ 0.30` (gate per §6 item 7); the round 0 TTFT is recorded but excluded from this CV.
- [ ] Watermark sampling uses `vm_stat` (or equivalent) subprocess; missing/parse-fail yields `UNKNOWN`, not failure.
- [ ] `cross_validation` block is populated against both D2 and D6 baselines but `overall_conclusion` does NOT depend on it (advisory only, per D6 §6.5 lesson).
- [ ] No `comparative_ledger` / `reference_runtime_comparison_*` / `oMLX_*` / `vMLX_*` field anywhere in evidence; no banned vocabulary in any string value (per [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §3).
- [ ] No file added or modified under `owlmlx/`. The `owlmlx/model_release_candidate_record.py:39-47` DSV4 data block stays byte-identical (D7 is the only round permitted to edit it).
- [ ] No new test file; the unit tests live in `tests/test_deepseek_v4_d1_repeatability.py` (3 new functions) and the env-gated test lives in `tests/test_mlx_native_backend_real_smoke.py` (1 new function).
- [ ] [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) DSV4 row remains at `experimental` (D5 alone does not promote).
- [ ] [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope remains unchanged.

---

## 11. Next Round

After D5 design-spec landed (this document):

1. **D5 code-grade in a fresh session** (or current session if user directs `直接干`). Deliverables:
   - new `sustained` subcommand in `scripts/bench/deepseek_v4_d1_repeatability.py` (~250 LOC)
   - new `_d5_sample_host_watermark` helper
   - 3 new unit tests in `tests/test_deepseek_v4_d1_repeatability.py`
   - 1 new env-gated test in `tests/test_mlx_native_backend_real_smoke.py`
   - one real-evidence run on the 128 GB host (≈ 5-10 minutes wall clock)
   - one `model_release_candidate_record` JSONL row marking `deepseek_v4_flash_2bit_dq_128g_sustained_load=passed`

2. **D7 design-grade fresh session** (after D5 passed). D7 owns:
   - `runtime-capability-matrix.md` DSV4 row promotion from `experimental` to `partial` (D5 + D6 + D7 joint requirement)
   - `deepseek-v4-bring-up-status.md` §4 Blocked Scope amendment (visibility on `technical_preview` allowed)
   - `model_release_candidate_record.py:39-47` data update (`lane=technical_preview`, `visibility_status=technical_preview_registered`, `verdict=partial`)
   - `/v1/runtime/model-visibility` diagnostic surface registration

3. **D7 code-grade fresh session** (after D7 design-grade).

4. **Sweep follow-up** (independent round, not D5's scope): per plan-grade §13, update the five stale-language locations after D5 + D6 + D7 all land.

This D5 design-spec is **self-contained**: a fresh code-grade session reading only this file, the D6 spec, and the linked source-of-truth + code files should be able to produce the D5 code-grade artifacts without additional clarification.

---

## 12. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Initial D5 design-grade spec, written same day as D6 passed. Trigger: D6 verdict reclassified to `passed` under amended §7.1 item 7 (commit `a7387d1a`); D5/D7 unblocked on the D6 prerequisite; user direction `直接干` permitted in-session design-grade transition (overriding [[feedback-fresh-session-grade-transitions]] for this work). Scope: N≥20 sustained-load through the D6 mainline backend path, single fixed prompt `p2_short_en × 512`, intra-run RSS stability + Campaign A CV gates, cross-validation against D2 and D6 as advisory diagnostic only (D6.1 lesson inherited). | Codex architect loop (with user direction) |
