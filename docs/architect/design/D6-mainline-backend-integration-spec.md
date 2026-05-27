# D6 · Design-Grade Spec · Mainline Backend Integration

> **Gate**: Campaign D6 · DSV4-Flash 2bit-DQ mainline backend integration through `MlxLmSubprocessBackend`
> **Plan-grade source**: [`../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md)
> **Phase-prompt source**: [`../../phase-prompts/owlmlx-d6-mainline-backend-integration-designgrade-20260527.md`](../../phase-prompts/owlmlx-d6-mainline-backend-integration-designgrade-20260527.md)
> **Status**: design-grade draft · 2026-05-27 · fresh-session landed
> **Prerequisite**: D1 / D2 / D3 / D4 all passed 2026-05-17 in `.runtime-deepseek-v4-mlx/` isolated lane (see [`../../source-of-truth/deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §1)
> **Non-goal**: this spec does not claim D6 promotes DSV4-Flash 2bit-DQ to `partial`; D6 alone keeps `experimental_only`. `partial` requires D5 + D6 + D7 jointly, and visibility is bounded at `technical_preview` per plan-grade §1 / §6.

---

## 1. Purpose

D6 moves DSV4-Flash 2bit-DQ from "isolated harness lane runs" to "mainline `MlxLmSubprocessBackend` consumes it through the documented backend protocol":

```text
isolated D1-D4 lane (passed 2026-05-17)
  -> scripts/bench/deepseek_v4_d1_repeatability.py talks to .runtime-deepseek-v4-mlx/ directly via persistent-child protocol
  -> evidence under d1-/d2-/d3-/d4-...

D6 target
  -> pyproject.toml declares `deepseek-experimental` optional dependency group
  -> a venv populated from that extras group is reachable as `python_executable` for `MlxLmSubprocessBackend`
  -> the existing in-process probe in mlx_lm_subprocess_backend.py:178 (`_read_model_type_from_config`)
     + mlx_lm_subprocess_backend.py:953 (`_probe_model_type_support` -> `importlib.util.find_spec("mlx_lm.models.deepseek_v4")`)
     resolves to supported=True against the Blaizzy fork installed in that venv
  -> `MlxLmSubprocessBackend.load -> stream_generate_messages -> unload` lifecycle succeeds end-to-end
  -> backend.status() reports clean child_health after unload
  -> evidence under d6-mainline-backend-integration/ with explicit `backend_class=MlxLmSubprocessBackend` field
```

D6 does **not** modify the backend's surface area — `MlxLmSubprocessBackend` already detects `model_type=deepseek_v4` via [`owlmlx/runtime/mlx_lm_subprocess_backend.py:178`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:178) and probes child-runtime support via [`owlmlx/runtime/mlx_lm_subprocess_backend.py:953`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:953). D6 is therefore an **environment + reproducibility + evidence** spec, not a backend-refactor spec. The D6 design-grade question is: under what packaging declaration and what harness shape does the existing backend become honest about DSV4 lifecycle, with measured cross-validation against the D2 baseline?

D6 preserves [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) row "DeepSeek V4 Flash 2bit-DQ adapter optimization" at `experimental` until D5 + D7 join it. D6 alone is **necessary but insufficient** for `partial`.

---

## 2. Scope

### 2.1 In

| Item | Requirement |
|---|---|
| Runtime environment | A new venv populated from `deepseek-experimental` extras group (canonical name: `.runtime-deepseek-experimental/`); **separate from** `.venv` / `.runtime1-mlx` / `.runtime-deepseek-v4-mlx` |
| pyproject change | One new `[project.optional-dependencies]` entry: `deepseek-experimental = [...]` per §3 |
| Backend class | `MlxLmSubprocessBackend` (NOT `MlxNativeBackend`; isolation is mandatory for the experimental adapter) |
| mlx-lm source pin | Blaizzy fork commit `5c10538136b9038b9626c134612b08afc18d697a` (same commit as D1-D4 baseline; locks the variable so D6 measures path change, not code change) |
| Model artifact | `DeepSeek-V4-Flash-2bit-DQ` at `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ` |
| Prompt surface | `messages` / chat-template rendering (D1 adopted surface) |
| Generation surface | `stream_generate_messages` (D2 adopted surface) |
| Lifecycle phases | preflight -> load -> 6-prompt cross-validation matrix -> unload -> clean health |
| Cross-validation baseline | [`files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl`](../../../files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl) (6 rows: p1/p2/p4 × 128/512) |
| Drift thresholds | TTFT: ≤20% relative; decode_tps_after_first_token: ≤15% relative; child_rss_gb: ≤1.0 GB absolute |
| Test extension | New env-gated case added to [`tests/test_mlx_native_backend_real_smoke.py`](../../../tests/test_mlx_native_backend_real_smoke.py); module name retained for backward-compat with existing test references in [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §5 |
| Evidence path | `files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/` |
| Capability label | `experimental_only` (D6 does not promote) |
| Visibility surface | unchanged (`visibility_status=not_registered`; D7 handles registration) |

### 2.2 Out

- `MlxNativeBackend` (in-process) integration for DSV4 — D6 deliberately picks subprocess isolation because (a) D1-D4 baselines were collected through subprocess-equivalent isolated harness, (b) the 96 GB peak unified memory makes in-process kernel impact on owlmlx parent unacceptable
- DSV4-Pro / 4bit / 8bit / FP16 variants (plan §1 hard rules)
- N≥20 sustained-load repeatability (D5)
- `/v1/runtime/model-visibility` registration or any visibility surface change (D7)
- MTP speculative path on DSV4 (D8 far term; blocked by D3 `mtp_weights_absent_or_stripped` verdict)
- Any update to [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope (D7 unblocks the visibility clause; D6 leaves §4 unchanged)
- Measured TPS comparison against oMLX / vMLX (banned per [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §3)
- New module under `owlmlx/` to carry DSV4-specific spec/validator (per [[project-owlmlx-agents-module-as-spec-rule]]; the only allowed `owlmlx/` change is data, not code: future D7 may edit [`owlmlx/model_release_candidate_record.py:39-47`](../../../owlmlx/model_release_candidate_record.py:39) — D6 does NOT touch that data block)
- Modification of mlx-lm upstream or transformers upstream
- Promotion of [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) DSV4 row to `partial`

---

## 3. pyproject Extras Group Definition

### 3.1 TOML insertion

Add the following block under `[project.optional-dependencies]` in [`pyproject.toml`](../../../pyproject.toml), strictly after the existing `dev` group:

```toml
[project.optional-dependencies]
runtime = [
    "mlx>=0.22.0",
    "mlx-lm>=0.22.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
]
dev = [
    "pytest>=8.0",
]
deepseek-experimental = [
    "mlx-lm @ git+https://github.com/Blaizzy/mlx-lm@5c10538136b9038b9626c134612b08afc18d697a",
]

[tool.hatch.metadata]
allow-direct-references = true
```

**Isolation invariants** (every one of these is a code-grade review checkbox):

1. The string `deepseek-experimental` MUST NOT appear inside the `runtime` extras list.
2. The `mlx-lm @ git+...` URL MUST NOT appear inside the `runtime`, `dev`, or any unrelated extras list.
3. No other `[project.optional-dependencies]` entry is modified by D6.
4. `[project] dependencies = []` remains empty — default install MUST NOT pull DSV4 deps.
5. `[tool.hatch.build.targets.wheel] packages = ["owlmlx"]` remains unchanged — no new package surface ships with the wheel.
6. `[tool.hatch.metadata].allow-direct-references = true` is required because hatch rejects git direct references in optional dependencies without this explicit metadata setting.

### 3.2 Installation command

The canonical install command for D6:

```bash
uv venv .runtime-deepseek-experimental --python 3.13
uv pip install --python .runtime-deepseek-experimental/bin/python \
  'mlx-lm @ git+https://github.com/Blaizzy/mlx-lm@5c10538136b9038b9626c134612b08afc18d697a'
```

Do **not** use `uv sync --extra deepseek-experimental --python
.runtime-deepseek-experimental/bin/python` for this task. In uv project mode,
that command selects the interpreter for the project `.venv`; it does not
populate the target venv in place, and can rebuild the normal project `.venv`.
D6's isolation requirement is that the fork lands only in
`.runtime-deepseek-experimental/`.

After install, the venv MUST satisfy:

```bash
.runtime-deepseek-experimental/bin/python -c 'import importlib.util; print(importlib.util.find_spec("mlx_lm.models.deepseek_v4") is not None)'
# expected stdout: True
```

If that command prints `False` or raises, D6 preflight fails with `extras_install_blocked` (see §8 row 1).

### 3.3 transformers dependency posture

The Blaizzy fork's own dependency declarations pull `transformers` transitively. D6 does NOT pin `transformers` in the extras group. Rationale:

- The fork patches `tokenizer_utils.py` so `deepseek_v4` falls back through `PreTrainedTokenizerFast` regardless of whether `transformers 5.x` registers `deepseek_v4` in `CONFIG_MAPPING` (per [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §2).
- Pinning transformers here would shadow the fork's own constraint and risk a future fork-update / pin-conflict.
- If a future transformers release breaks the fallback path, the failure surfaces during preflight as `tokenizer_fallback_path_broken` (see §8 row 6), not as a silent corruption.

### 3.4 Isolation from `.runtime-deepseek-v4-mlx/`

The existing isolated lane venv `.runtime-deepseek-v4-mlx/` (used by D1-D4 isolated harness) is **left untouched** by D6. The two venvs coexist:

| venv | populated by | consumed by | scope |
|---|---|---|---|
| `.runtime-deepseek-v4-mlx/` | ad-hoc / editable install at `/tmp/mlx-lm-dsv4` | `scripts/bench/deepseek_v4_d1_repeatability.py real/metrics` subcommands | D1-D4 isolated lane (frozen) |
| `.runtime-deepseek-experimental/` | `uv pip install --python <venv>/bin/python <pinned fork>` | `MlxLmSubprocessBackend(python_executable=...)` | D6 mainline-backend lane (new) |

Keeping both makes D2 ↔ D6 cross-validation honest: the mlx-lm commit hash matches (`5c10538136b9038b9626c134612b08afc18d697a`), so the only deliberate variable is **path through which the kernel reaches the runner module**, not the runner module's underlying code.

---

## 4. Backend Integration Surface

### 4.1 The backend already supports the model_type

`MlxLmSubprocessBackend.load()` resolves DSV4 in three existing steps. None require code change for D6:

| Step | Location | Behavior |
|---|---|---|
| Read `model_type` from local `config.json` | [`owlmlx/runtime/mlx_lm_subprocess_backend.py:178`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:178) `_read_model_type_from_config(model_path)` | Returns `"deepseek_v4"` for the local artifact |
| Probe child-runtime support via `find_spec` | [`owlmlx/runtime/mlx_lm_subprocess_backend.py:953`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:953) `_probe_model_type_support(runner_model_id, model_type)` | Spawns one short python subprocess with `python_executable` from `__init__`, runs `importlib.util.find_spec("mlx_lm.models.deepseek_v4")`. With the D6 venv configured, this returns `supported=True` |
| Start persistent child + send `load` action | [`owlmlx/runtime/mlx_lm_subprocess_backend.py:1226`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:1226) `load(model_id, memory_gb=...)` | Spawns the runner module `owlmlx.runtime.mlx_lm_runner` via the same `python_executable`, sends `{"action": "load", "model_id": <runner_model_id>}`; child performs `mlx_lm.load(<path>)` against the Blaizzy fork's `deepseek_v4.py` |

The pre-D6 state (where `_probe_model_type_support` returns `supported=False`) produces the clean reject in [`owlmlx/runtime/mlx_lm_subprocess_backend.py:1244`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:1244) (`error_code=RuntimeErrorCode.unsupported_model_family`, `does_not_start_child=True`, `does_not_dirty_backend_health=True`). That clean reject is the D4-equivalent fallback; D6's success path supersedes it only when the configured `python_executable` has the extras installed.

### 4.2 Configuration shape for D6 consumers

D6 callers (the new harness subcommand + the new test case) construct the backend with explicit `python_executable`:

```python
from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend

backend = MlxLmSubprocessBackend(
    python_executable=".runtime-deepseek-experimental/bin/python",
    # `model_path_resolver` left as None — model_id IS the absolute artifact path for D6
    # `timeout_s` raised to 900 to absorb cold load (D2 measured 30226 ms TTFT once)
    timeout_s=900.0,
    # `health_probe_timeout_s` left default (2.0) — probe is cheap python subprocess
    auto_restart_dead_session=False,  # D6 fails loudly on restart, never silently recovers
    max_restart_attempts=0,
)
```

Rationale for the non-default arguments:

- `auto_restart_dead_session=False` + `max_restart_attempts=0`: D6 evidence MUST distinguish "lifecycle ran clean" from "restart masked a child crash". The post-unload backend.status() check (§5.4) would still pass after a silent restart, defeating the gate. D5 may later relax this for sustained-load coverage; D6 keeps the strictest.
- `timeout_s=900.0`: 2026-05-11 measured cold TTFT 24821 ms + load 14125 ms ≈ 39 s for the first prompt. 900 s is a ~20x buffer to absorb cold-Metal warmups and prompt-prefill variance without ever timing out under healthy conditions.

### 4.3 No new interface

D6 does NOT add new methods, new fields, or new error codes to `MlxLmSubprocessBackend` / `RuntimeBackend` Protocol / `RuntimeErrorCode`. Any code-grade PR introducing new backend interface is out of scope and MUST be rejected as scope creep.

The only owlmlx-package change permissible during D6 code-grade is **the new harness subcommand call site** (§9), which lives under `scripts/`, not `owlmlx/`. Per [[project-owlmlx-agents-module-as-spec-rule]].

---

## 5. Lifecycle Run Shape

### 5.1 Preflight

```yaml
preflight:
  mainline_runtime_path: .runtime-deepseek-experimental
  deepseek_experimental_extras_installed: true | false
  mlx_lm_source:
    origin: <module path resolved via `find_spec` in the venv>
    package_version: <importlib.metadata.version("mlx-lm")>
    git_commit: <expected = 5c10538136b9038b9626c134612b08afc18d697a or null>
  backend_class: MlxLmSubprocessBackend
  python_executable: <absolute path to .runtime-deepseek-experimental/bin/python>
  model_artifact_path: /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ
  model_type_in_config: deepseek_v4
  model_type_support_probe:
    module_name: mlx_lm.models.deepseek_v4
    supported: true | false
    returncode: 0 | <non-zero>
  stock_runtime_untouched: true
  default_model_surface_unchanged: true
  d2_baseline_evidence_path: files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl
  d2_baseline_rows_present: 6
```

Preflight fails (`blocked`) when any of:

- `deepseek_experimental_extras_installed=false`
- `model_type_support_probe.supported=false`
- `mlx_lm_source.git_commit != 5c10538136b9038b9626c134612b08afc18d697a` (mismatch is a soft warning, not a hard fail — code-grade may relax to `expected_or_logged`)
- `d2_baseline_rows_present < 6`
- `model_artifact_path` missing or unreadable

### 5.2 Lifecycle yaml

```yaml
lifecycle:
  load:
    timeout_s: 900
    max_load_time_s_expected: 60     # D1 measured 14.125 s; 60 s is a 4x cold-Metal buffer
    record_fields:
      - load_time_s
      - pid
      - runner_model_id
      - returncode
  generate_matrix:
    prompt_surface: messages
    generation_surface: stream_generate_messages
    prompt_ids: [p1_short_cn, p2_short_en, p4_long_context]
    max_tokens_levels: [128, 512]
    total_rows: 6                     # 3 prompts × 2 token levels
    record_fields_per_row:
      - prompt_id
      - max_tokens
      - load_time_s_carried             # constant per session; carried for joinability with D2
      - ttft_ms
      - stream_wall_ms
      - prompt_tokens
      - completion_tokens
      - decode_tps_after_first_token
      - wall_tps
      - child_rss_gb
      - rss_sample_scope: child_process
      - rss_sample_source: ps_rss_kb
      - rss_sample_timing: after_generation_before_unload
      - restart_observed: false
      - repetition_flag: false
      - stop_reason: stop | length | <other>
  unload:
    timeout_s: 60
    expected_freed_gb_lower_bound: 80   # 2026-05-11 measured 100 GB freed; ≥80 GB tolerates KV variance
    record_fields:
      - unload_time_s
      - freed_gb
      - returncode
  health:
    sample_points:
      - before_load
      - after_load
      - after_each_generate_row
      - after_unload
    snapshot_fields:
      - backend.status().healthy
      - backend.status().loaded_models  # tuple; after_unload must equal ()
      - backend.status().detail["backend_kind"]
      - child_restart_count             # MUST remain 0 throughout D6
```

### 5.3 Single load session

D6 runs the entire 6-row generate matrix in **one** loaded session (one child process from one `backend.load`). The first row carries the cold TTFT; subsequent rows are warm. This matches D2's lifecycle and makes the cross-validation honest.

A child restart at any point during the 6 rows fails D6 (per `auto_restart_dead_session=False` in §4.2).

### 5.4 Post-unload clean-health check

After `backend.unload(model_id)`:

```python
status = backend.status()
assert status.healthy is True
assert status.loaded_models == ()
assert status.backend_name == "mlx-lm-subprocess"
```

These three assertions are the "clean health" gate. They are evaluated **once**, immediately after unload returns. They MUST hold; otherwise D6 records `health.clean_health_after_unload=false` and `verdict=failed`.

---

## 6. Evidence Schema

### 6.1 Per-row record

Each generate row produces one JSONL line. Schema:

```yaml
schema_version: d6.mainline-backend.v1
record_type: mainline_backend_lifecycle_row
gate: D6
run_id: <ts>-d6-<descriptor>
created_at_utc: <ISO-8601 Z>
model_id: DeepSeek-V4-Flash-2bit-DQ
backend_class: MlxLmSubprocessBackend          # explicit; distinguishes from D2 isolated-harness lane
backend_path:
  python_executable: <absolute>
  runner_module: owlmlx.runtime.mlx_lm_runner
  deepseek_experimental_extras_active: true
  mlx_lm_source:
    git_commit: 5c10538136b9038b9626c134612b08afc18d697a
    package_version: <version>
prompt_surface: messages
generation_surface: stream_generate_messages
prompt_id: <p1_short_cn | p2_short_en | p4_long_context>
max_tokens: <128 | 512>
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
  rss_sample_timing: after_generation_before_unload
backend_health_snapshot:
  before_load:
    healthy: <bool>
    loaded_model_count: <int>
  after_load:
    healthy: <bool>
    loaded_model_count: <int>
    child_restart_count: 0
  after_this_row:
    healthy: <bool>
    loaded_model_count: 1
    child_restart_count: 0
  after_unload:                                 # populated only on the final row's record
    healthy: <bool | null>
    loaded_model_count: <int | null>
    child_restart_count: <int | null>
cross_validation:
  d2_baseline_row_pointer: <jsonl line offset or row index into the d2 baseline file>
  ttft_ms_diff_rel: <float>                     # (d6 - d2) / d2
  decode_tps_diff_rel: <float>
  child_rss_gb_diff_abs: <float>
  drift_within_threshold: <bool>
host_state:
  unified_memory_gb_capacity: 128
  watermark_observed: GREEN | YELLOW | RED | FATAL | UNKNOWN
  watermark_action_observed: <enum>
verdict: passed | blocked | failed
verdict_reason: <string, optional; populated on non-passed>
```

### 6.2 Run-level summary

Alongside the JSONL, the harness writes `<run_id>.summary.json` matching D2's `d2.metrics.run.v2` shape:

```yaml
schema_version: d6.mainline-backend.run.v1
run_id: <ts>-d6-<descriptor>
rows_written: 6
passed_rows: 6
drift_within_threshold_rows: 6
preflight: passed | blocked | failed
backend_class: MlxLmSubprocessBackend
mlx_lm_git_commit: 5c10538136b9038b9626c134612b08afc18d697a
metric_summary:
  ttft_ms: {count: 6, min: <>, p50: <>, max: <>}
  decode_tps_after_first_token: {count: 6, min: <>, p50: <>, max: <>}
  child_rss_gb: {count: 6, min: <>, p50: <>, max: <>}
cross_validation_summary:
  ttft_ms_diff_rel_max: <float, must be ≤ 0.20>
  decode_tps_diff_rel_max: <float, must be ≤ 0.15>
  child_rss_gb_diff_abs_max: <float, must be ≤ 1.0>
backend_health_summary:
  child_restart_observed: false
  clean_health_after_unload: true
  unload_freed_gb: <float, must be ≥ 80>
overall_conclusion: passed | blocked | failed
```

### 6.3 Evidence directory layout

```text
files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/
  <ts>-d6-mainline-backend-lifecycle.jsonl
  <ts>-d6-mainline-backend-lifecycle.summary.json
  <ts>-d6-cross-validation-vs-d2.jsonl         # optional sidecar with per-row diff detail
```

The plan-grade [§10 Evidence Paths](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md#10-evidence-paths) names two candidate files (`<ts>-d6-mainline-backend-lifecycle.jsonl` and `<ts>-d6-mainline-backend-metrics.jsonl`). D6 design-spec collapses both into the single `lifecycle.jsonl` ledger above because the lifecycle row already embeds metrics per the D2 precedent; the optional `cross-validation` sidecar replaces the `metrics.jsonl` second file. Plan-grade §10 thus reads as "two-file capacity ceiling", not "two mandatory files".

### 6.4 Banned ledger row

D6 evidence MUST NOT contain a `comparative_ledger` row, a `reference_runtime_comparison_*` populated block, or any field of the form `oMLX_*` / `vMLX_*`. Cross-validation in §6.2 is **D2-versus-D6 self-comparison only**; it does not compare against external reference runtimes. Banned per [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §3.

---

## 7. Acceptance / Pass Criteria

D6 verdict aggregation:

```yaml
D6_mainline_backend_integration:
  preflight: passed
  pyproject_extras_group_present_and_isolated: true
  deepseek_experimental_extras_installed: true
  model_type_support_probe.supported: true
  mlx_lm_git_commit_matches_baseline: true
  lifecycle:
    load: passed
    six_row_generate_matrix: passed
    unload: passed
    unload_freed_gb_ge_80: true
    clean_health_after_unload: true
    child_restart_observed: false
  cross_validation_vs_d2:
    ttft_ms_diff_rel_max: <= 0.20
    decode_tps_diff_rel_max: <= 0.15
    child_rss_gb_diff_abs_max: <= 1.0
    rows_within_threshold: 6 / 6
  test_extension:
    tests/test_mlx_native_backend_real_smoke.py.OWLMLX_DSV4_SUBPROCESS_SMOKE: passed (when env-gated)
  evidence:
    lifecycle_jsonl_present: true
    summary_json_present: true
    no_comparative_ledger_row: true
    no_visibility_registration_in_ledger: true
  capability_label:
    runtime_capability_matrix_unchanged: true   # DSV4 row stays at `experimental`
    model_release_candidate_record_unchanged: true  # owlmlx/model_release_candidate_record.py:39-47 untouched
  overall_conclusion: passed | blocked | failed
```

### 7.1 Hard pass requirements

Every one of these is necessary:

1. pyproject `deepseek-experimental` extras group present, syntactically valid, and **not contaminating** `runtime`/`dev` extras (§3.1 invariants 1-6).
2. The new venv (`.runtime-deepseek-experimental/`) is reproducibly installable from a clean checkout via the §3.2 commands, on the same 128 GB host.
3. `MlxLmSubprocessBackend.load(<DSV4 path>)` returns `ok=True` within `timeout_s=900` (typically ≤ 60 s per §5.2 expected upper bound).
4. All 6 generate matrix rows return `ok=True` with `restart_observed=false` and `repetition_flag=false`.
5. `backend.unload(...)` returns `ok=True` and reports `freed_gb >= 80`.
6. Post-unload `backend.status()` reports `loaded_models == ()` and `healthy is True`.
7. Per-row cross-validation against the D2 baseline (same prompt_id × max_tokens cell) satisfies all three thresholds.
8. `tests/test_mlx_native_backend_real_smoke.py` env-gated DSV4 case passes when `OWLMLX_DSV4_SUBPROCESS_SMOKE_PYTHON` and `OWLMLX_DSV4_SUBPROCESS_SMOKE_MODEL_PATH` env vars are set.
9. Evidence files land at `files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/` with both `.jsonl` and `.summary.json` artifacts.
10. No code change to `owlmlx/` package other than data in `owlmlx/model_release_candidate_record.py` (D6 leaves even that data untouched — that update is D7's job).

### 7.2 Capability-label invariants after D6 passes

D6 passing does **NOT** change:

- [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) — the "DeepSeek V4 Flash 2bit-DQ adapter optimization" row stays at `experimental`.
- [`owlmlx/model_release_candidate_record.py:39-47`](../../../owlmlx/model_release_candidate_record.py:39) `DEFAULT_MODEL_RELEASE_CANDIDATES` — DSV4 entry stays at `lane=flagship_experimental`, `visibility_status=not_registered`, `verdict=experimental_only`.
- [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope — visibility registration on `GET /v1/openai/models` remains prohibited.
- [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) — no claim change.

D6 produces a [`model_release_candidate_record`](../../../owlmlx/model_release_candidate_record.py) JSONL entry (under `files/evidence/owlmlx/model-release-candidates/`) marking `deepseek_v4_flash_2bit_dq_mainline_backend_integration=passed` per [plan §6](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md#6-acceptance-wording), but the matrix-level `partial` promotion waits for D5 + D7.

### 7.3 2026-05-27 execution result

Code-grade execution on 2026-05-27 produced a complete D6 lifecycle evidence
run, but **did not pass D6**:

- `20260527T071857Z-d6-mainline-backend-lifecycle.summary.json`: preflight
  passed, but load failed with a Metal GPU timeout before any generation row.
- `20260527T072206Z-d6-mainline-backend-lifecycle.jsonl` and `.summary.json`:
  preflight passed; model load, 6/6 generation rows, unload, and clean
  post-unload health completed; `mlx_lm_git_commit` matched
  `5c10538136b9038b9626c134612b08afc18d697a`; `unload_freed_gb=100.0`.
- Verdict remained `failed` because D2 cross-validation did not satisfy the
  frozen thresholds: every row exceeded `child_rss_gb_diff_abs <= 1.0`, and
  some rows also exceeded TTFT / decode TPS drift budgets.

This is usable D6 triage evidence, not a D6 pass. D5/D7 promotion paths remain
blocked until D6 is either re-run under a valid comparable baseline or the
design-spec is explicitly amended with a new, evidence-backed cross-validation
criterion.

---

## 8. Failure Semantics

| # | Failure | Classification | Where surfaced | Next action |
|---|---|---|---|---|
| 1 | `.runtime-deepseek-experimental` population fails (Blaizzy fork URL unreachable, build error, transformers conflict) | `blocked` | preflight | trigger plan-grade §9.3 upstream watch ledger; consider candidate-fork switch to `#1195` / `#1189` / `#1201` per plan §11 |
| 2 | `_probe_model_type_support` returns `supported=False` in the new venv | `blocked` | preflight | extras likely installed against wrong python; verify `.runtime-deepseek-experimental/bin/python` activated for `uv sync` |
| 3 | `MlxLmSubprocessBackend.load` returns `ok=False` with `error_code=backend_error` (child crashed during `mlx_lm.load`) | `failed` | lifecycle.load | capture stderr (last 2000 chars per backend's `detail.stderr`); inspect for `[metal] insufficient memory` (would classify `metal_oom`, host-OOM) or `broken_pipe_child_lost` |
| 4 | `restart_observed=true` at any generate row | `failed` | lifecycle.generate | record row; do NOT promote; investigate whether D5 sustained-load can reproduce or this is transient |
| 5 | Cross-validation drift exceeds any threshold on any row | `failed` | cross_validation | record per-row diffs; the gap itself becomes the next dominant gap; reassess whether subprocess JSON-protocol overhead is the culprit (would suggest D6 design-spec amendment, not abandon) |
| 6 | Tokenizer fallback path broken (`PreTrainedTokenizerFast` cannot load DSV4 tokenizer config) | `failed` | lifecycle.load | record exact exception; check transformers version pulled transitively; this is the §3.3 risk materializing |
| 7 | Post-unload `backend.status()` reports `loaded_models != ()` OR `healthy=False` | `failed` | health.after_unload | backend health pollution; D4 reject path is the documented fallback but D6 does not auto-fall-back — record and fail |
| 8 | `unload.freed_gb < 80` | `failed` | lifecycle.unload | unload did not actually release weights; investigate Metal allocator behavior; do not promote |
| 9 | Host memory watermark observed at `RED` or `FATAL` during the 6-row matrix | `blocked` (not `failed`) | host_state | this is D5 territory (sustained-load tests pressure); D6 single-cycle should never hit RED. If it does, host has other contention; reschedule rather than fail |
| 10 | Stdout transport corruption (non-JSON line from child not classified as `benign_child_stdout_noise`) | `failed` | lifecycle.generate | record `corrupt_json_transport_record` per [`owlmlx/runtime/mlx_lm_subprocess_backend.py:239`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:239); this is a backend health issue, not a DSV4 issue, but D6 records it as DSV4-context blocked |

`blocked` ≠ `failed`:
- `blocked` means D6 cannot run as designed; the spec itself or external dependencies need attention. Re-run on next attempt is reasonable.
- `failed` means D6 ran as designed and did not meet the bar. Re-run with the same inputs will produce the same `failed`. Promotion is denied.

Both verdicts surface in the `verdict` field of the run-level summary (§6.2). Neither permits writing `verdict=passed` to the `model_release_candidate_record` JSONL.

---

## 9. Harness Requirements

### 9.1 Harness extension, not rewrite

D6 extends the existing [`scripts/bench/deepseek_v4_d1_repeatability.py`](../../../scripts/bench/deepseek_v4_d1_repeatability.py) (D1/D2/D3/D4 shared harness; 2705 lines). The extension adds one new top-level subcommand:

```text
uv run python scripts/bench/deepseek_v4_d1_repeatability.py mainline \
    --run-id <ts>-d6-<descriptor> \
    --backend-python .runtime-deepseek-experimental/bin/python \
    --model-path /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ \
    --d2-baseline files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl \
    --prompt-ids p1_short_cn,p2_short_en,p4_long_context \
    --max-tokens-levels 128,512 \
    --timeout-s 900 \
    --evidence-dir files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration
```

The `mainline` subcommand sits **alongside** the existing `preflight` / `dry-run` / `real` / `metrics` / `compare` subcommands. None of those are modified by D6.

### 9.2 What the `mainline` subcommand does (code-grade contract)

The design-spec freezes the subcommand's behavior:

1. Run preflight (§5.1) against `--backend-python` and the model path. On any preflight failure, emit a single `blocked` row and exit non-zero.
2. Construct `MlxLmSubprocessBackend(python_executable=<--backend-python>, timeout_s=<--timeout-s>, auto_restart_dead_session=False, max_restart_attempts=0)`.
3. Snapshot `backend.status()` -> `health.before_load`.
4. Call `backend.load(<--model-path>, memory_gb=100.0)`. Snapshot -> `health.after_load`.
5. For each `(prompt_id, max_tokens)` in the cartesian of `--prompt-ids × --max-tokens-levels`:
   - Resolve `messages` via the harness's existing `_messages_for_prompt` helper ([`scripts/bench/deepseek_v4_d1_repeatability.py:737`](../../../scripts/bench/deepseek_v4_d1_repeatability.py:737)).
   - Call `backend.stream_generate_messages(model_id, messages, max_tokens=...)`.
   - Compute `ttft_ms` (time from request to first `event=token`), `stream_wall_ms` (total wall), `completion_tokens` (final `done` event's `completion_tokens`), `decode_tps_after_first_token` and `wall_tps` per D2-spec formulas.
   - Sample child RSS via the existing `_process_rss_gb(pid)` helper ([`scripts/bench/deepseek_v4_d1_repeatability.py:807`](../../../scripts/bench/deepseek_v4_d1_repeatability.py:807)) after generation, before next request.
   - Compute cross-validation diffs against the matching `(prompt_id, max_tokens)` row in `--d2-baseline`.
   - Write one JSONL row per §6.1.
   - Snapshot `backend.status()` -> `health.after_this_row`.
6. Call `backend.unload(<--model-path>)`. Snapshot -> `health.after_unload`.
7. Write the run-level summary per §6.2.
8. Exit 0 iff `overall_conclusion=passed`; otherwise exit non-zero with a final diagnostic line on stdout.

### 9.3 Forbidden harness changes

The `mainline` subcommand MUST NOT:

- Modify any function used by `real` / `metrics` / `compare` / `preflight` / `dry-run` subcommands (sharing helpers like `_messages_for_prompt`, `_prompt_by_id`, `_process_rss_gb`, `_append_jsonl` is allowed and required; mutating their signatures or behavior is forbidden).
- Write to `.runtime-deepseek-v4-mlx/` (the D1-D4 isolated lane).
- Spawn any subprocess except those owned by `MlxLmSubprocessBackend`.
- Touch `owlmlx/` package source (read-only imports are fine).
- Write to `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl` (that ledger gets a separate per-stage row from the model_release_candidate tooling, not from this harness directly).

### 9.4 Test extension

Add the following env-gated test functions to [`tests/test_mlx_native_backend_real_smoke.py`](../../../tests/test_mlx_native_backend_real_smoke.py). The file name retains `mlx_native` for backward compatibility with [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §5 references; a docstring update at module top SHOULD note that the module now also covers subprocess-backend smokes.

```text
env vars (all opt-in; absent -> skip):
  OWLMLX_DSV4_SUBPROCESS_SMOKE_PYTHON       -> path to .runtime-deepseek-experimental/bin/python
  OWLMLX_DSV4_SUBPROCESS_SMOKE_MODEL_PATH   -> path to DSV4-Flash 2bit-DQ artifact
  OWLMLX_DSV4_SUBPROCESS_SMOKE_MAX_TOKENS   -> int, default 32 (lighter than D6 harness 128/512 — this test is a smoke, not the full matrix)

test_dsv4_subprocess_backend_lifecycle_load_stream_unload:
  - construct MlxLmSubprocessBackend with the env-supplied python_executable
  - load(model_path)
  - stream_generate_messages(...) once with the test prompt "Say one short sentence."
  - assert at least one token event, then done
  - assert finish_reason is not None, completion_tokens > 0
  - unload(model_path) -> ok=True
  - assert status().loaded_models == () after unload

test_dsv4_subprocess_backend_rejects_when_extras_missing:
  - construct MlxLmSubprocessBackend with python_executable pointing at the project's default `.venv` (NOT the deepseek-experimental venv)
  - load(model_path) -> ok=False with error_code=unsupported_model_family
  - assert detail["does_not_start_child"] is True
  - assert detail["does_not_dirty_backend_health"] is True
  - skip when OWLMLX_DSV4_SUBPROCESS_SMOKE_FALLBACK_PYTHON is unset
```

The second test pins the D4-equivalent fallback: when the `deepseek-experimental` extras are NOT installed in the configured venv, the backend MUST refuse cleanly and NOT pollute health. This invariant is the safety net under which D6 is allowed to exist at all.

### 9.5 No new modules

Per [[project-owlmlx-agents-module-as-spec-rule]], D6 code-grade MUST NOT create:

- New files under `owlmlx/`
- `*_contract.py`, `*_evidence.py`, `*_harness.py`, `*_ledger.py` modules anywhere
- New `tests/test_*` files (extend `test_mlx_native_backend_real_smoke.py` only)
- New `scripts/bench/*` files (extend `deepseek_v4_d1_repeatability.py` only)

If the code-grade implementation discovers a need that genuinely cannot fit these constraints, it MUST stop and request a design-spec amendment, not work around the rule.

---

## 10. Review Checklist

Code-grade review MUST verify each box explicitly:

- [ ] [`pyproject.toml`](../../../pyproject.toml) `[project.optional-dependencies]` gains exactly one new entry named `deepseek-experimental`; the entry contains exactly one element `"mlx-lm @ git+https://github.com/Blaizzy/mlx-lm@5c10538136b9038b9626c134612b08afc18d697a"`; no other dependency block is modified; `[tool.hatch.metadata].allow-direct-references = true` is present.
- [ ] `uv venv .runtime-deepseek-experimental --python 3.13 && uv pip install --python .runtime-deepseek-experimental/bin/python 'mlx-lm @ git+https://github.com/Blaizzy/mlx-lm@5c10538136b9038b9626c134612b08afc18d697a'` succeeds on a clean checkout on the 128 GB host; the venv contains importable `mlx_lm.models.deepseek_v4`.
- [ ] `MlxLmSubprocessBackend(python_executable=".runtime-deepseek-experimental/bin/python", auto_restart_dead_session=False, max_restart_attempts=0)` constructs without error; no new keyword arguments are introduced to `MlxLmSubprocessBackend.__init__`.
- [ ] `_probe_model_type_support` at [`owlmlx/runtime/mlx_lm_subprocess_backend.py:953`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py:953) returns `supported=True` against the new venv. No code change to that method.
- [ ] The `mainline` subcommand in [`scripts/bench/deepseek_v4_d1_repeatability.py`](../../../scripts/bench/deepseek_v4_d1_repeatability.py) runs the 6-row matrix end-to-end in one loaded session with `restart_observed=false` on every row.
- [ ] Each generate row's `cross_validation.drift_within_threshold=true`; specifically `ttft_ms_diff_rel ≤ 0.20`, `decode_tps_diff_rel ≤ 0.15`, `child_rss_gb_diff_abs ≤ 1.0`.
- [ ] Post-unload `backend.status().loaded_models == ()`, `healthy is True`, `child_restart_count == 0`.
- [ ] `unload.freed_gb ≥ 80`.
- [ ] Evidence JSONL row matches `schema_version=d6.mainline-backend.v1` schema (§6.1); summary matches `schema_version=d6.mainline-backend.run.v1` (§6.2).
- [ ] No row contains any `comparative_ledger`, `reference_runtime_comparison_*` populated block, or `oMLX_*`/`vMLX_*` field; no row uses any [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §3 banned vocabulary in any string value.
- [ ] No file is added or modified under `owlmlx/` package (read-only imports are fine; the `owlmlx/model_release_candidate_record.py` DSV4 data block at lines 39-47 stays byte-identical).
- [ ] No new test file is created in `tests/`; the two new test functions are appended to `tests/test_mlx_native_backend_real_smoke.py` and are skip-by-default.
- [ ] [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) DSV4 row remains at `experimental`; no edit during D6 code-grade.
- [ ] [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope remains unchanged; visibility-registration prohibition stays in force.
- [ ] The `mainline` subcommand's argparse help string does NOT promise "parity with X", "replaces Y", "matches Z" — uses only the banned-vocabulary-safe phrasings from [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §8.

---

## 11. Next Round

After D6 design-spec landed (this document):

1. **D6 code-grade in a fresh session.** Feed this spec to a fresh CLI session per [[feedback-fresh-session-grade-transitions]]. The code-grade session's deliverables:
   - pyproject.toml edit (§3.1)
   - new `.runtime-deepseek-experimental/` venv populated (§3.2)
   - new `mainline` subcommand in `scripts/bench/deepseek_v4_d1_repeatability.py` (§9.1-9.3)
   - two new test functions in `tests/test_mlx_native_backend_real_smoke.py` (§9.4)
   - one passing 6-row lifecycle evidence run (§6) on the 128 GB host
   - one `model_release_candidate_record` JSONL row marking `deepseek_v4_flash_2bit_dq_mainline_backend_integration=passed` (per plan §6 wording, schema per [`owlmlx/model_release_candidate_schema.py`](../../../owlmlx/model_release_candidate_schema.py))

2. **D5 design-grade fresh session.** D5 (sustained-load N≥20) reuses the D6 backend path. The D5 design-spec MUST:
   - Reference the `MlxLmSubprocessBackend` + `.runtime-deepseek-experimental` configuration locked here.
   - Lift `auto_restart_dead_session=False` only if D5 explicitly handles restart attribution (D5 may instead choose to retain the strict setting and treat restart-during-N-rounds as a fail).
   - Use the same 6-row matrix prompt set or a single fixed prompt across N=20 — D5 design-grade decides.
   - Honor the same `experimental_only` capability label.

3. **D5 code-grade fresh session.** After D5 design-spec landed.

4. **D7 design-grade fresh session.** D7 handles `technical_preview` visibility registration. D7's preconditions: D5 passed + D6 passed. D7's deliverables include the [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope amendment AND the [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) row promotion from `experimental` to `partial`. D7 owns the surface-level capability label change; D6 does not.

5. **Sweep follow-up** (independent round, not D6's scope): per plan-grade §13, update the five stale-language locations after D5+D6+D7 land. D6 does not touch them.

This D6 design-spec is **self-contained**: a fresh code-grade session reading only this file and the linked source-of-truth + code files should be able to produce the D6 code-grade artifacts without additional clarification. If a fresh code-grade session reports ambiguity, the gap is a design-spec defect to be amended here, not papered over in code.

---

## 12. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Code-grade amendment: canonical venv population changed from `uv sync --extra ... --python <target>` to `uv pip install --python <target> ...` after execution showed uv project sync can rebuild the normal `.venv`. Added required hatch `allow-direct-references` metadata, tightened review wording, and recorded the first D6 execution result: lifecycle completed on the second attempt but D6 remained `failed` because D2 cross-validation drift budgets were not met. | Codex code-grade loop |
| 2026-05-27 | Initial D6 design-grade spec. Trigger: plan-grade [`09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md) landed same day; handoff [`owlmlx-d6-mainline-backend-integration-designgrade-20260527.md`](../../phase-prompts/owlmlx-d6-mainline-backend-integration-designgrade-20260527.md) routed work to a fresh design-grade session. Scope: pyproject extras group + `MlxLmSubprocessBackend` configuration discipline + 6-row D2-cross-validated lifecycle evidence + test extension; no backend interface change; no capability-label promotion. | Codex architect loop (with user direction) |
