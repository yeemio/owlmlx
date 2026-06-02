# F-3 · Design-Grade Spec

> **Gate**: Campaign F · F-3 — Gemma 4 resident MTP A/B (assistant-drafter speculative decoding promoted from `deferred_cli_per_request` to a resident, parent-supervised runner with pure-decode A/B evidence)
> **Layer**: design-grade, downstream of [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Part V · Campaign F · F-3, upstream of code-grade (resident MTP runner + A/B harness)
> **Plan-grade source**: [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) line 335 ("F3 Gemma 4 resident MTP A/B（待 drafter / trim blocker 解除后恢复）") + [`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md)
> **Status**: design-grade — **F-3.1 local prerequisite failed** (the upstream `mlx-lm #980` issue is closed, but the 2026-06-01 local `mlx-lm` / `mlx-vlm` pin failed the §2.2 resident-MTP feasibility probe; see §2.4 and §9). A 2026-06-02 local inventory also found no full-attention MTP target/drafter candidate to bypass the hybrid-cache blocker (§2.5). Code-grade does **not** start until a later local prerequisite probe reaches `resident_viable_*`.
> **Non-goal**: this spec does not promote `assistant_drafter` to `supported`. It defines the resident-runner A/B that produces the evidence a later §1a Promotion Gate round would consume. It also does not touch the `mlx-lm` text line, DS4, or continuous batching.

## 1. Purpose

F-1 landed the runtime-owned `speculative_execution_status` surface and proved the kernel can *observe* an MTP runner — but the only MTP path that exists today is `deferred_cli_per_request`: every request shells out to a fresh `python -m mlx_vlm generate` subprocess that reloads the target + drafter from scratch. The 2026-05-06 Gemma4 probe ([`gemma4-mtp-drafter-probe-20260506.md`](../../source-of-truth/gemma4-mtp-drafter-probe-20260506.md)) measured MTP at `0.8793×` non-MTP elapsed, but that number **includes process startup + model load cost** and therefore cannot be read as decode speedup.

F-3 closes exactly one gap: **make the Gemma4 MTP runner resident (load once, serve many) under parent-side supervision, then measure pure-decode A/B so the speculative speedup claim is honest.**

The deliverable is **evidence**, not a promotion: an A/B ledger that separates load cost from decode speed for resident MTP vs resident non-MTP on the same target, same prompt, same `max_tokens`, with post-run health + RSS accounting. Whether that evidence later promotes `assistant_drafter` from `experimental` → `partial` is a **separate §1a Promotion Gate round** that consumes this ledger; F-3 itself promotes nothing.

This gate fills the holes F-1 explicitly pre-cut for it:

- F-1 `runner_status=loaded` (vs `deferred_cli_per_request`) — F-3 is the first gate that can legitimately report `loaded`
- F-1 `cache_sharing.scope=in_process_resident` future row — F-3 decides whether resident Gemma4 MTP reaches it or stays `deferred_cli_per_request`
- F-1.3 §6.2 integration-reality note: *"F-1.3 does NOT introduce a parent-side `MlxVlmMtpSubprocessBackend` … that work is a precursor of a future Gemma 4 resident MTP gate (F-3)."* — **F-3 is that gate.**

## 2. Prerequisites

### 2.1 Hard prerequisite gate — hybrid-cache resident viability (BLOCKING)

F-3 code-grade **MUST NOT start** until one of the following holds:

1. **Upstream fix reaches the local runtime**: [`mlx-lm #980`](https://github.com/ml-explore/mlx-lm/issues/980) (RotatingKVCache / SSM caches not trimmable) is closed/merged **and** the installed `mlx-lm` / `mlx-vlm` pin is locally proven to pick up the relevant behavior for this Gemma4 resident-MTP lane, **OR**
2. **Owlmlx non-trimmable resident path proven viable**: a feasibility probe (§2.2) proves a resident Gemma4 MTP runner can hold the target+drafter resident across requests in **append-only / non-trimmable** mode (no `trim_prompt_cache` dependency on the hybrid Gemma4 cache), reusing the same defensive pattern `MlxNativeBackend._trim_prompt_cache_with_reason` already encodes for #980.

**Why this blocks**: Gemma4 is a hybrid (multimodal, `gemma4_text` + `gemma4_vision`) architecture. Resident serving means holding a KV cache across requests; trimming that cache is exactly what #980 says is unsupported for RotatingKVCache / SSM-class caches. A resident runner that silently recomputes the full prompt every request would defeat the purpose (and would measure *slower*, not faster). Route 2 is the owlmlx-owned escape: prove resident reuse works in append-only mode without needing trim, matching the session-KV-cache append-only precedent already shipped.

This prerequisite is **honestly recorded as the gate's blocker**, mirroring how B-1c §2 records `measurement_wall_clock_gap_free=false`. The spec is complete; only the start signal waits.

### 2.2 Recommended de-risk: non-trimmable resident feasibility probe (precedes code-grade)

Before full F-3 code-grade, a minimal feasibility probe SHOULD answer one question with a real local run:

> Can a single persistent `mlx-vlm` child process hold `gemma-4-31B-it` + the `gemma-4-31B-it-assistant-bf16` drafter resident, serve ≥2 sequential generate requests **without reloading the model**, and report a non-trivial `speculative_summary` on the 2nd request — using append-only cache semantics (no `trim_prompt_cache` call on the Gemma4 cache)?

A `passed` probe satisfies §2.1 route 2 and unblocks F-3. A `failed`/`blocked` probe keeps F-3 blocked and feeds the upstream-watch ledger (§9). This probe is plan-grade feasibility-probe discipline applied to the gate's single riskiest assumption.

### 2.4 2026-06-01 F-3.1 local probe result (FAILED)

The first local F-3.1 probe ran after the B-1c memory-sensitive soak released
the host:

```text
files/evidence/owlmlx/bench/f3-resident-mtp/20260601T124448Z-f3-1-resident-feasibility.jsonl
```

Result:

- `schema_version=f3.resident_feasibility.v1`
- `verdict=failed`
- `failure_reasons=["non_trivial_speculative_summary_missing_after_first_request"]`
- `capability_label=experimental`
- `used_for_promotion_gate=false`
- versions: `mlx-vlm 0.5.0`, `mlx-lm 0.31.3`, `mlx 0.31.2`
- target + drafter loaded once: `target_load_count=1`, `draft_load_count=1`
- resident process served 3 requests: `requests_served=3`, `reloads_observed=0`
- speculative summaries: request 0 `mean_accepted_tokens=1.0`, requests 1-2
  `mean_accepted_tokens=0.0`, `rounds=0`
- `trim_attempted=true`, with 180 observed `KVCache` / `RotatingKVCache`
  `trim` calls

Interpretation: the local runtime can load target + drafter once and keep a
resident process alive across requests, but it did **not** satisfy the F-3.1
resident-viable gate because request 2+ did not produce non-trivial speculative
acceptance and the run entered a trim regime. This does not prove Gemma4 MTP is
impossible in principle; it proves this local pin + prompt/cache path does not
clear the prerequisite. F-3.2/F-3.3 remain blocked.

### 2.5 2026-06-02 local MTP candidate inventory

After the negative Gemma4 F-3.1 verdict, the next low-risk MTP action was to
look for a local **full-attention** MTP target/drafter candidate that could avoid
the hybrid-cache / trim blocker instead of forcing Gemma4 forward.

Evidence:

```text
files/evidence/owlmlx/bench/f3-resident-mtp/20260602T093630Z-f3-mtp-candidate-inventory.jsonl
```

Result:

- `schema_version=f3.mtp_candidate_inventory.v1`
- `model_count=14`
- `mtp_candidate_count=11`
- `assistant_drafter_artifact_count=2`
- `native_mtp_hybrid_or_unknown_candidate_count=9`
- `native_mtp_full_attention_candidate_count=0`
- `full_attention_resident_mtp_next_target_available=false`
- `capability_label=experimental`
- `used_for_promotion_gate=false`

Interpretation: the local disk has MTP-like signals, but not the bypass target
F-3 needs next. The Gemma4 assistant artifacts are already covered by the failed
F-3.1 route. The Qwen3.5/Qwen3.6 and DeepSeek V4 configs expose native-MTP-ish
signals (`mtp_num_hidden_layers` / `num_nextn_predict_layers`), but their config
surfaces are hybrid or trim-sensitive (`linear_attention` / `sliding_window`).
That means they are **not** the "full-attention resident MTP candidate" needed
to bypass the current blocker. Do not start F-3.2/F-3.3 from this inventory.

### 2.6 Soft prerequisites (must hold, not blocking by themselves)

- F-1 design + code-grade landed and green (the `speculative_execution_status` surface F-3 will drive into the `loaded` shape) — **met** (F-1.2/F-1.3 landed, evidence `20260525T142617Z`)
- this F-3 design-grade spec reviewed + signed off (architect + user, per [`README.md`](README.md) two-gate rule)
- the `GEMMA4_MTP_CAPABILITY_LABEL` constant in [`owlmlx/gemma4_mtp_drafter.py`](../../../owlmlx/gemma4_mtp_drafter.py) line 23 remains the honest source of truth for the `assistant_drafter` label and stays `"experimental"` throughout F-3 (F-3 produces promotion *evidence*; it does not flip the label)
- Track 1 (B-1c §2) still owns the cache/memory/allocator editing surface; F-3 lands in non-overlapping files (§6.3 forbidden-edit list)

## 3. Scope

### In scope (F-3.1 feasibility probe → F-3.2 resident runner → F-3.3 A/B evidence)

- **F-3.1**: the §2.2 non-trimmable resident feasibility probe — a read-mostly script proving resident multi-request serving without model reload and without trim, emitting a probe verdict ledger
- **F-3.2**: a parent-side resident MTP backend (`MlxVlmMtpResidentBackend` or equivalent) that holds one persistent `mlx-vlm` child, speaks the existing JSONL child protocol, and exposes `load` / `generate` / `stream_generate` / `unload` / `status` per the `RuntimeBackend` Protocol ([`owlmlx/runtime/backends.py:23`](../../../owlmlx/runtime/backends.py)), so the kernel can drive `observe_speculative_runner_load` into the F-1 `runner_status=loaded` shape
- **F-3.3**: a resident A/B harness producing the §5 verification ledger — resident MTP vs resident non-MTP, pure-decode timing isolated from load cost
- wiring the resident runner's emitted records through the **existing** F-1 `observe_speculative_runner_*` kernel APIs (no new surface; F-1's v1 contract absorbs `runner_status=loaded` additively)
- evidence ledger under `files/evidence/owlmlx/bench/f3-resident-mtp/`

### Out of scope (explicitly **not** F-3)

- promotion of `assistant_drafter` (or any method) to `partial` / `supported` — that is a separate §1a round consuming F-3.3 evidence
- the `mlx-lm` text-line MTP path (Qwen / gpt-oss). F-3 is **Gemma4 / `mlx-vlm` line only**. A text-line MTP gate is separate and currently has no probe (roadmap leaves it for later F-series work)
- DS4 native MTP weights / path (roadmap F-7, far term)
- continuous batching / cross-request parallelism — **permanently excluded** (MLX/Metal same-process parallel-generation-unsafe substrate limit; capability-matrix `boundary = 1`). Resident ≠ parallel: F-3's resident runner serves **serially** through the existing `GenerationGate`
- chunked prefill ([`B-prefill-chunking-spec.md`](B-prefill-chunking-spec.md)) — a separate single-worker decode gate; F-3 must not absorb it
- any change to the F-1 `speculative_execution_status` **schema** (F-3 only drives existing fields into the `loaded` shape; new fields would be an F-1 v-bump, out of F-3)
- editing the `mlx-vlm` upstream package or vendoring a fork
- structured-output / tool-calling invariance under spec (Campaign F-4)
- a stable external clear-session / drafter-swap API

## 4. What "resident" means here (and what it does not)

| Property | `deferred_cli_per_request` (today) | `resident` (F-3 target) |
|---|---|---|
| target + drafter load | every request | once, on `load` |
| process lifetime | one subprocess per request | one persistent child across requests |
| F-1 `runner_status` | `deferred_cli_per_request` | `loaded` |
| timing isolates decode? | no (load cost mixed in) | **yes** (load excluded from per-request timing) |
| concurrency | n/a (serial by spawn) | **serial** via `GenerationGate` (NOT parallel) |
| cache across requests | none | append-only reuse if §2.1 route 2 holds; else fresh-per-request inside the resident process (still saves load cost, but no decode-cache benefit) |

**Honesty boundary**: "resident" is a *process-lifetime* claim, not a *parallelism* claim and not a *cache-depth* claim. If §2.1 resolves only via route 2 (append-only, no trim), F-3 must report that the resident win is **load-amortization + append-only reuse**, not full prefix-trim reuse — and the A/B ledger must label which regime produced the numbers.

## 5. Verification Contract

F-3 produces **bench evidence** (unlike F-1's contract-shape conformance). Independent conclusions are named so a later §1a round can cite them precisely.

### 5.1 `f3_1_resident_feasibility` (F-3.1 probe pass criteria)

- one persistent `mlx-vlm` child loads `gemma-4-31B-it` + `gemma-4-31B-it-assistant-bf16` drafter **once**
- serves ≥3 sequential generate requests with **zero intervening model reloads** (proven by a load-count counter in the child, not by timing inference)
- the 2nd+ requests report a non-null `speculative_summary` with `mean_accepted_tokens > 0`
- no `trim_prompt_cache` call is made on the Gemma4 cache (append-only regime), OR if trim is attempted it is caught by the `_trim_prompt_cache_with_reason` defensive layer with a recorded reason code (never a crash)
- post-run 8066 `/healthz` clean idle (`active_model_id=null`, `model_count=0`, `backend_error=null`), no residual `mlx_vlm` processes
- verdict ∈ { `resident_viable_append_only`, `resident_viable_with_trim`, `blocked_on_local_runtime`, `blocked_on_980`, `failed` }

`resident_viable_*` unblocks F-3.2/F-3.3. `blocked_on_local_runtime` /
`blocked_on_980` / `failed` keeps the gate blocked and writes the
upstream-watch row (§9).

### 5.2 `f3_3_pure_decode_ab` (F-3.3 A/B pass criteria)

The A/B MUST isolate decode from load:

- both arms (MTP-on, MTP-off) run against the **same resident process** lifecycle: load once per arm, then time only the generate calls (load timestamp excluded from the reported per-request latency)
- identical target, prompt set, `max_tokens`, `temperature=0`, and post-run health/RSS accounting on both arms
- run in **both orders** (MTP-then-baseline and baseline-then-MTP) to control for warm-up, mirroring the 2026-05-06 probe's two-order discipline
- output text **byte-identical** between MTP and non-MTP arms for each prompt (speculative decoding must not change output; a mismatch is an automatic `failed` — this is the spec-path-safety invariant, the same honesty axis as F-4)
- report per-arm decode TPS (tokens/sec **excluding** load), `mean_accepted_tokens`, `rounds`, peak RSS, and the MTP/non-MTP **decode-time** ratio
- the headline claim is the **pure-decode ratio**, explicitly distinguished from the 2026-05-06 `0.8793×` whole-process ratio

Independent conclusions emitted:

| Conclusion field | Meaning |
|---|---|
| `resident_load_amortized` | bool — resident held across all A/B requests with zero reloads |
| `pure_decode_ratio` | float — MTP decode-time / non-MTP decode-time (excluding load); `<1.0` means MTP faster |
| `output_byte_identical` | bool — MTP vs non-MTP output identical for every prompt |
| `mean_accepted_tokens` | float — averaged over MTP-arm requests |
| `cache_regime` | string — `append_only` \| `trim` \| `fresh_per_request` (which regime §2.1 resolved to) |
| `health_clean_pre_post` | bool — 8066 clean before and after both arms |
| `used_for_promotion_gate` | **`false`** — F-3 evidence is diagnostic until a separate §1a round consumes it |

### 5.3 What F-3 does NOT claim from this evidence

- not `supported`, not `partial` — the label stays `experimental` (§2.5); promotion is a separate round
- not parity with oMLX cross-family native MTP — F-3 is Gemma4-only
- not a text-line (Qwen/gpt-oss) MTP claim
- a favorable `pure_decode_ratio` is **necessary but not sufficient** for promotion; the §1a gate additionally requires N≥20 repeatability + clean reclaim, per the live promotion framework

## 6. Harness Changes

### 6.1 F-3.1 (feasibility probe)

- new probe script (operator-run, not in the import path): `scripts/runtime_gemma4_mtp_resident_probe.py`, modelled on the existing `scripts/runtime_gemma4_mtp_drafter.py`
- the probe drives a persistent child via the existing `mlx-vlm` probe venv (`OWLMLX_RUNTIME_PYTHON` → the isolated `runtime-probes/mlx-vlm-mtp-probe/.venv`), NOT the main `.venv`
- emits `files/evidence/owlmlx/bench/f3-resident-mtp/<ts>-f3-1-resident-feasibility.jsonl`

### 6.2 F-3.2 (resident backend) + F-3.3 (A/B)

- new module: `owlmlx/runtime/mlx_vlm_mtp_resident_backend.py` — a parent-side wrapper analogous to [`MlxLmSubprocessBackend`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py) but holding **one** persistent `mlx-vlm` MTP child; implements the `RuntimeBackend` Protocol so the kernel treats it like any other backend
  - it reuses the existing JSONL child protocol that [`mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py) already speaks; the **runner internals are not edited** (same one-directional-observation discipline F-1 established)
- kernel wiring: the resident backend's `load` / `generate` / `unload` returns are fed through the **existing** `observe_speculative_runner_load` / `observe_speculative_runner_generate` / `observe_speculative_runner_unload` APIs (landed in F-1.3) so `speculative_execution_status` flips to the §4.11.2-style `runner_status=loaded` shape — **no new surface, no F-1 schema change**
- new A/B harness: `scripts/bench/f3_resident_mtp_ab.py`, emitting the §5.2 ledger
- new tests: `tests/test_mlx_vlm_mtp_resident_backend.py` (Protocol conformance + serial-gate invariant + no-reload-across-requests assertion against a fake child)

### 6.3 Forbidden edits (Track 1 / Stage 1 / F-1 boundary)

F-3 PRs MUST NOT touch:

- [`owlmlx/session_kv_cache.py`](../../../owlmlx/session_kv_cache.py), [`owlmlx/cache_manager.py`](../../../owlmlx/cache_manager.py), [`owlmlx/scheduler_admission.py`](../../../owlmlx/scheduler_admission.py), [`owlmlx/memory_pressure_eviction_policy.py`](../../../owlmlx/memory_pressure_eviction_policy.py), [`owlmlx/memory_watermark.py`](../../../owlmlx/memory_watermark.py) (Track 1)
- the `speculative_execution_status` **schema** in [`owlmlx/runtime/speculative_execution_status.py`](../../../owlmlx/runtime/speculative_execution_status.py) (F-1 owns it; F-3 only drives existing fields)
- [`owlmlx/runtime/mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py) internal logic (observe-only)
- the `GEMMA4_MTP_CAPABILITY_LABEL` constant value (stays `"experimental"`)
- `MlxNativeBackend` cache trim internals beyond reusing `_trim_prompt_cache_with_reason` read-only as the reason-code reference

## 7. Evidence

```text
files/evidence/owlmlx/bench/f3-resident-mtp/
  <YYYYMMDDTHHMMSSZ>-f3-1-resident-feasibility.jsonl
  <YYYYMMDDTHHMMSSZ>-f3-3-pure-decode-ab.jsonl
  <YYYYMMDDTHHMMSSZ>-f3-3-pure-decode-ab-rollup.jsonl
```

Feasibility row:

```yaml
schema_version: f3.resident_feasibility.v1
record_type: resident_mtp_feasibility_probe
gate: F-3
target: gemma-4-31B-it
drafter: gemma-4-31B-it-assistant-bf16
reloads_observed: <int>          # MUST be 0 across the ≥3 requests for a pass
requests_served: <int>
mean_accepted_tokens: <float>
trim_attempted: true | false
trim_reason_code: <code | null>
cache_regime: append_only | trim | fresh_per_request
health_clean_pre_post: true | false
verdict: resident_viable_append_only | resident_viable_with_trim | blocked_on_local_runtime | blocked_on_980 | failed
```

A/B rollup row:

```yaml
schema_version: f3.pure_decode_ab_rollup.v1
gate: F-3
slice: F3.3
orders_run: [mtp_then_baseline, baseline_then_mtp]
resident_load_amortized: true | false
pure_decode_ratio: <float>       # MTP decode-time / non-MTP decode-time, load excluded
whole_process_ratio_ref: 0.8793  # 2026-05-06 probe, for explicit contrast
output_byte_identical: true | false
mean_accepted_tokens: <float>
cache_regime: append_only | trim | fresh_per_request
peak_rss_bytes_mtp: <int>
peak_rss_bytes_baseline: <int>
health_clean_pre_post: true | false
used_for_promotion_gate: false
```

`used_for_promotion_gate: false` is fixed at F-3 close — the evidence exists, but flipping `assistant_drafter` to `partial` is a separate §1a round that reads this ledger.

## 8. Failure Handling

| Condition | Handling |
|---|---|
| §2.1 prerequisite unmet at start | gate stays `blocked`; do not start F-3.2/F-3.3; write/refresh upstream-watch row (§9) |
| F-3.1 probe `blocked_on_980` | F-3 stays blocked; the append-only route is not viable; escalate to upstream-watch + reconsider whether a non-Gemma4 (full-attention) MTP target should precede this gate |
| resident child crashes mid-A/B | abort that arm, mark `resident_load_amortized=false`, do not fabricate decode numbers from a partial run; re-run cleanly |
| MTP vs non-MTP output **not** byte-identical | **automatic `failed`** — this is a spec-path-safety violation, not a perf result; record the divergence and stop (do not report a speedup from a run that changed output) |
| `pure_decode_ratio >= 1.0` (MTP not faster resident) | honest negative result — record it; F-3 evidence can legitimately conclude "resident MTP is not faster on this target" and that blocks promotion rather than being hidden |
| post-run health dirty / residual processes | `health_clean_pre_post=false`; run is invalid for promotion regardless of timing |

**Honesty rules**:
- a favorable whole-process number must never be reported as a decode speedup; only `pure_decode_ratio` (load excluded) is the headline
- if §2.1 resolves to `fresh_per_request` (resident process but no cross-request cache reuse because trim is blocked and append-only didn't apply to the prompt shape), the ledger MUST say so in `cache_regime` — the resident win is then load-amortization only, and the spec must not imply cache-depth parity

## 9. Upstream Watch Linkage

F-3's blocker is now a **local prerequisite verification** problem, not merely an
open-issue watch. Per the competitor-matrix upstream-watch discipline
([`competitor-capability-matrix-20260527.md` §4.3](../../source-of-truth/competitor-capability-matrix-20260527.md)):

- F-3 remains keyed to [`mlx-lm #980`](https://github.com/ml-explore/mlx-lm/issues/980), but the live issue state must be checked before each F-3.1/F-3.2 attempt
- as of 2026-06-01, the GitHub issue is **closed**; that does not by itself unblock F-3 because route 1 additionally requires the local installed `mlx-lm` / `mlx-vlm` pin to demonstrate the needed behavior on this Gemma4 resident-MTP lane
- if local pin verification passes, re-evaluate §2.1 route 1 (trim-based resident becomes viable)
- the §2.2 feasibility probe is the owlmlx-owned way to unblock **without** waiting for upstream (route 2)
- shared blocker with F-2 C2 (n-gram serving) and prefix-cache reuse — a single #980 resolution unblocks all three; the watch row should note the shared dependency

## 10. Out-of-scope reminders

- F-3 does not promote any method; the label stays `experimental` and `used_for_promotion_gate=false`
- F-3 does not touch the `mlx-lm` text line, DS4, continuous batching, chunked prefill, or structured-output invariance
- F-3 does not change the F-1 `speculative_execution_status` schema; it only drives existing fields into the `loaded` shape
- F-3 does not vendor or edit `mlx-vlm`; it wraps the existing runner via a parent-side resident backend
- a resident runner is **serial** through `GenerationGate` — "resident" never implies parallel generation (substrate boundary = 1)

## 11. References

### Plan-grade lineage
- [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Part V · Campaign F · F-3 (line 335) + §G4 Speculative Path Landing
- [`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md) (speculative direction)

### Upstream gate
- [`F-1-spec.md`](F-1-spec.md) §6.2 integration-reality note (names F-3 as the spawn-site gate) + §4.7 `runner_status=loaded` + §4.9 `in_process_resident` rows (the holes F-3 fills)

### Code surfaces F-3 reads / wraps
- Probe precedent + capability constant: [`owlmlx/gemma4_mtp_drafter.py`](../../../owlmlx/gemma4_mtp_drafter.py), [`scripts/runtime_gemma4_mtp_drafter.py`](../../../scripts/runtime_gemma4_mtp_drafter.py)
- Existing MTP child protocol (wrapped, not edited): [`owlmlx/runtime/mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py)
- Parent-side resident backend template: [`owlmlx/runtime/mlx_lm_subprocess_backend.py`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py)
- Backend Protocol the resident backend implements: [`owlmlx/runtime/backends.py:23`](../../../owlmlx/runtime/backends.py)
- F-1 observe APIs (driven, not changed): [`owlmlx/runtime/kernel.py`](../../../owlmlx/runtime/kernel.py) `observe_speculative_runner_*`
- #980 defensive layer reference: [`owlmlx/runtime/mlx_native_backend.py`](../../../owlmlx/runtime/mlx_native_backend.py) `_trim_prompt_cache_with_reason`

### Blocker
- [`mlx-lm #980`](https://github.com/ml-explore/mlx-lm/issues/980) — RotatingKVCache / SSM caches not trimmable; **closed on GitHub as of 2026-06-01 live check**, but F-3 remains blocked until the local `mlx-lm` / `mlx-vlm` pin or the §2.2 append-only probe proves resident viability for this lane
- 2026-06-01 local F-3.1 probe:
  [`20260601T124448Z-f3-1-resident-feasibility.jsonl`](../../../files/evidence/owlmlx/bench/f3-resident-mtp/20260601T124448Z-f3-1-resident-feasibility.jsonl)
  records `verdict=failed`; resident load was proven (`reloads_observed=0`,
  `requests_served=3`), but request 2+ had `mean_accepted_tokens=0.0` and the
  run observed 180 trim calls
- 2026-06-02 local MTP candidate inventory:
  [`20260602T093630Z-f3-mtp-candidate-inventory.jsonl`](../../../files/evidence/owlmlx/bench/f3-resident-mtp/20260602T093630Z-f3-mtp-candidate-inventory.jsonl)
  records `native_mtp_full_attention_candidate_count=0` across 14 local model
  dirs; Qwen / DeepSeek MTP signals remain hybrid or trim-sensitive rather than
  a bypass path for F-3.2
- 2026-05-06 whole-process A/B reference (the number F-3 must NOT conflate with decode speedup): [`gemma4-mtp-drafter-probe-20260506.md`](../../source-of-truth/gemma4-mtp-drafter-probe-20260506.md) §"A/B Timing Return"

## 12. Change Log

| Date | Change | By |
|---|---|---|
| 2026-06-01 | design-grade draft (fresh-context derivation from plan-grade roadmap F-3); landed BLOCKED on `mlx-lm #980` prerequisite gate with owlmlx-owned non-trimmable feasibility route as the unblock path | architect session (this round) |
| 2026-06-01 | live upstream re-check: `mlx-lm #980` is closed, so the gate wording was narrowed from "open issue blocker" to "local prerequisite verification blocker"; F-3.1 remains required before code-grade starts | goal loop F-3.1 |
| 2026-06-01 | added `blocked_on_local_runtime` as a first-class F-3.1 verdict because an unusable isolated probe venv is a different blocker from an upstream #980 defect | goal loop F-3.1 |
| 2026-06-01 | recorded first F-3.1 local resident probe result: `verdict=failed`; target/drafter loaded once and served 3 requests, but request 2+ reported no non-trivial speculative acceptance and the run observed 180 trim calls; F-3.2 remains blocked | goal loop F-3.1 |
| 2026-06-02 | recorded local MTP candidate inventory: 14 model dirs, 11 with MTP/assistant signals, but 0 full-attention native-MTP candidates; F-3 remains blocked rather than switching to an unproven hybrid target | MTP follow-up |
