# Coordinator Checkpoint: Internal Replacement-Grade Runtime Depth

**Goal:** `owlmlx-internal-replacement-grade-runtime-depth`
**Opened:** 2026-05-10
**Status:** active

## Strategic Context

Publishing now proves "we can run too." The real value is in:
host-stable repeatability, cache/scheduler depth, multi-model orchestration,
long-context, TTFT default optimization, DeepSeek family breadth, OwlOps
closed loop. None of these form a moat yet. Public release consumes attention
and exposes direction before the depth is there.

Public readiness docs are accurate but parked. This goal supersedes
`owlmlx-public-developer-preview-readiness` as the active main line.

## Active Sub-Campaigns

### 1. Host-Stable Repeatability Campaign

**Target:** three model lines — Qwen3.6-27B, Qwen3.6-35B-A3B, Gemma 4 —
each with N≥20 repeated runs under the Model RC harness.

**Evidence to record per run:** TPS, TTFT, RSS, post-run health, dirty
recovery count, ledger write fidelity.

**Success criterion:** variance across N runs is bounded and the run-to-run
delta does not exceed a frozen acceptable envelope. Single-run data does not
count as repeatability evidence.

**Current state:** Qwen27 and Qwen35 have 2-repeat runs; Gemma has 2-repeat
runs. All show `needs_optimization` verdicts or reference-comparison close-but-
below. Host-stable confidence is below reference grade.

### 2. Cache / Scheduler Depth

**Target:** move `cache_manager` from a single-request gateway into a real
policy layer with at least one observable aggregation dispatch.

**Surfaces to close:**
- cache status surface (what is resident, what is hot, what is evictable)
- release ledger (when and why cache entries are released)
- eviction policy (deterministic ordering given pressure + residency snapshot)
- prefix-cache feasibility probe (not a claim, a feasibility surface)

**Success criterion:** one closed non-exactness scheduler capability on the
active runtime path, visible in `tests/` under repeated load. Not just
marker-exactness assertions.

**Current state:** frozen at structural ingress seam only. `tests/` has
exactness tests; no observable aggregated dispatch under repeated load.

### 3. Qwen35 TTFT Default Optimization

**Target:** decompose the `cold_first_response_dominant` root cause into
measurable sub-phases: load time, template rendering, prefill, first decode,
thinking/profile overhead.

**Success criterion:** at least one sub-phase improvement that is default
serving behavior (not a Model RC warmup experiment). TTFT improvement that
appears in the standard run without special parameters.

**Current state (2026-05-11 — live validated):** Post-load Metal JIT warmup
confirmed via live validation: warmup_ms=123.7ms, first user request
TTFT=1218ms (within 1460–1736ms steady-state range) vs 3458ms cold-start
baseline. Warmup fires `stream_generate("", max_tokens=1)` after every load
call and is default behavior in the serving path. Evidence record appended to
trend-ledger.jsonl. Residual gap: sub-phase decomposition (load/template/
prefill/first-decode) not yet measured; default optimization criterion is met
for the warmup path but deeper sub-phase work remains open.

### 4. DeepSeek Family Bring-Up

**Target:** at least one DeepSeek-V4-Flash variant completes the full
lifecycle: load → generate → unload → clean health, with a measured RC record.

**Success criterion:** a `model_release_candidate_record` for a DeepSeek
variant with `load_result.status = "pass"`, `generation_result.status = "pass"`,
`unload_result.status = "pass"`, and post-run health clean. TPS comparison
with a reference runtime is a bonus, not the gate.

**Current state (2026-05-11 — criterion met):** `DeepSeek-V4-Flash-2bit-DQ`
completed full lifecycle on port 8067 via `.runtime-deepseek-v4-mlx` venv
(Blaizzy fork `pc/add-deepseekv4flash-model`). Measured: load_time_s=14.125,
TTFT=24821ms (cold, 96 GB weights), TPS=32.0, freed_gb=100.0, post-run
health clean. RC record appended to cumulative-ledger.jsonl; bring-up status
doc updated. Lane=flagship_experimental, visibility_status=not_registered.
Blockers resolved: tokenizer_utils.py patched for transformers 5.7.0
CONFIG_MAPPING gap; runner module installed into deepseek venv.

### 5. OwlOps Internal Consumption

**Target:** OwlOps service layer continuously consuming live runtime truth
from the full owned surface: monitor snapshot/history, /metrics,
test-runs, bottleneck classifier, Model RC history.

**Success criterion:** OwlOps can display a live bottleneck classification
and cross-validated metrics snapshot sourced from a running owlmlx instance,
without manual operator intervention to populate the data. Wave 8 UI decisions
are separate.

**Current state (2026-05-11 — pipeline demonstrated):** All 5 surfaces
confirmed live on port 8066 (monitor_snapshot, /metrics, test_runs,
model_rc_history=33 records, bottleneck_contract). Live bottleneck
classification pipeline executed: owlmlx snapshot → BottleneckLayerClassifier
logic → result=`layer=idle, confidence=high`. Evidence record appended to
trend-ledger.jsonl. Service layer (P1-5) is closed. Wave 8 (UI exposure +
stable live consumption across sessions) remains open.

## Public Release Re-Open Conditions

Public release is re-opened only when **all three** of the following are met:

1. At least 3 main-line model families have repeatability evidence (N≥20 each,
   variance bounded within a frozen acceptable envelope).
2. At least one `owlmlx` native-only capability exists that is not just
   wrapping `mlx_lm` — a scheduler policy, a cache management surface, a
   governance primitive that owlmlx owns end-to-end at the execution level.
3. OwlOps stably consumes live runtime truth and forms an internal operational
   closed loop (no manual population, no stale data).

**None of these is sufficient alone.** All three must be met simultaneously.

## Parked Gate

`docs/source-of-truth/public-developer-preview-readiness.md` is accurate and
remains in repository truth. It is not the active goal. Do not drive work
toward public release until the three conditions above are met.

## Durable References

- `docs/source-of-truth/public-developer-preview-readiness.md` (parked)
- `docs/source-of-truth/release-readiness-backlog.md` (7/7 closed — floor
  closure does not imply public release timing)
- `docs/source-of-truth/phase45-host-stable-execution-status.md`
- `docs/source-of-truth/phase45-heavy-weight-repeatability-status.md`
- `docs/source-of-truth/reference-runtime-comparison-matrix.md`
