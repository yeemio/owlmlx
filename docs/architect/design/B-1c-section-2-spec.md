# B-1c Section 2 · Design-Grade Spec

> **Gate**: Campaign B-1c section 2 · Session KV cache soak plus model swap
> **Layer**: design-grade, downstream of `docs/architect/01-mainline-roadmap.md`
> **Status**: design-grade spec + native §2 runner landed; token-boundary cache drops closed and prompt-reset bounded windows produced one aggregate-eligible 4h / 1-swap segment (`20260601T025321Z`). The later 5-minute-cadence forced-swap canaries proved swap boundaries stay clean, but they exposed a raw same-model load-epoch drift gate blocker: Gemma reaches `751370240` bytes raw drift while direct cache-object resident accounting (`cache_object_nbytes`) reports `1054965760` bytes and same-model unaccounted drift `0`. §2 is blocked on drift-gate closure plus aggregate volume, not on another passive wait. See §11 Blocker Taxonomy (2026-06-01)
> **Capability label**: Session KV cache remains `experimental`

## 1. Purpose

B-1c section 2 verifies the second long-stability claim:

```text
With session KV cache enabled, owlmlx can survive repeated model switch cycles
under a mixed short / medium / long session workload without reclaim-barrier
failures, FATAL watermark, hidden cache drops, or active-memory drift.
```

This is separate from B-1c §1. Section 1 proves no-swap session-cache soak
stability. Section 2 adds model unload / load / settle boundaries. A clean §2
result must not be used to hide a missing or failed §1 result.

## 2. Prerequisites

Do not run section 2 until one of these is true:

- current Mac route: B-1c §1 has `interrupted_no_swap_rehearsal = passed` with
  cumulative clean native segments >= 24h
- stronger dedicated-host route: B-1c §1 has `no_swap_soak_stability = passed`

The current Mac / laptop route is expected to be operator-interruptible. Section
2 should follow the same principle: explicit segment boundaries are allowed;
hidden wall-clock gaps inside a segment are not.

## 3. Scope

In scope:

- native backend only
- `OWLMLX_SESSION_CACHE_ENABLED=1`
- mixed short / medium / long session workload at 1:1:1 balance inside each
  segment
- explicit unload / settle / load boundaries between models
- read-only reclaim-barrier stats after each swap
- wall-clock continuity checks inside each segment
- final cleanup unload and settle

Out of scope:

- subprocess cache-handle transport
- paged KV, implicit prefix matching, or continuous batching
- changing the §1 verdict
- public `supported` promotion by §2 alone
- OwlCoda / OwlOps consumer behavior

## 4. Model Rotation

Canonical rotation:

```text
Qwen3.6-27B -> Gemma 4-31B-it -> Qwen3.6-35B-A3B -> Qwen3.6-27B
```

The initial implementation may parameterize paths and labels, but the evidence
must preserve stable labels in the rollup:

```yaml
models:
  - qwen3.6-27b
  - gemma-4-31B-it
  - qwen3.6-35b-a3b
```

If one model is unavailable, the run must be `blocked`, not silently downgraded
to a two-model swap ladder.

## 5. Segment Shape

Original D3 shape was one continuous 24h run with six swaps every four hours.
On the current Mac route, use operator-interruptible segments instead:

- target aggregate duration: >= 24h
- target aggregate swap count: >= 6
- recommended shape: `6 x 4h`, each segment contains one planned swap boundary
- acceptable shape: fewer longer segments, if each segment remains wall-clock
  continuous and records the exact swap boundaries

Each segment starts from a clean process state and writes a separate ledger and
rollup. Segment rollups are then aggregated into the §2 conclusion. Do not
merge ledgers by hand.

## 6. Evidence

Expected output directory:

```text
files/evidence/owlmlx/bench/session-kv-soak/
```

Recommended file naming:

```text
<timestamp>-b1c2-<rotation-label>-soak-swap.jsonl
<timestamp>-b1c2-<rotation-label>-soak-swap-rollup.jsonl
<timestamp>-b1c2-interrupted-soak-swap-rollup.jsonl
```

Per-sample records should use:

```yaml
schema_version: b1c2.v1
gate: B-1c section 2
mode: soak_plus_swap
phase: warmup | measurement | swap
```

Per-swap records must include:

```yaml
swap:
  index: <int>
  from_model: <label>
  to_model: <label>
  unload_ok: true | false
  settle_barrier_state: clean | failed_unload | failed_reclaim | unknown
  load_ok: true | false
  active_memory_before_unload_bytes: <int | null>
  active_memory_after_settle_bytes: <int | null>
  expected_minus_observed_active_bytes: <int | null>
```

Segment rollups must include:

```yaml
soak_plus_swap_stability: passed | failed | blocked
measurement_duration_s: <float>
swap_count: <int>
measurement_wall_clock_gap_free: true | false
ledger_gap_free: true | false
max_drift_bytes: <int | null>
fatal_watermark_count: <int>
failure_measurement_count: <int>
unresolved_reclaim_barrier_events: <int>
session_cache_drops_total: <int>
session_cache_expirations_total: <int>
session_cache_rejects_total: <int>
cleanup_unload_result: <object>
cleanup_settle: <object>
```

Aggregate rollups must keep §1 and §2 separate:

```yaml
interrupted_soak_plus_swap:
  aggregate_measurement_duration_s: <float>
  aggregate_swap_count: <int>
  segment_count: <int>
  all_segments_ok_for_rehearsal: true | false
soak_plus_swap_stability: passed | failed | blocked
graduates:
  soak_plus_swap_stability: true | false
  session_kv_supported: false
```

`session_kv_supported` remains false in this runner. Promotion is a separate
source-of-truth update after B-1a, B-1b, B-1c §1, and B-1c §2 are all reviewed.

## 7. Pass Criteria

`soak_plus_swap_stability = passed` requires all of:

- B-1c §1 prerequisite is already satisfied
- native backend with `measurement_mode = mlx_core_active_memory`
- aggregate measurement duration >= 24h
- aggregate swap count >= 6
- every segment has `measurement_wall_clock_gap_free = true`
- every segment has `ledger_gap_free = true`
- short / medium / long session mix appears in every segment
- `max_drift_bytes <= min(200 MiB, 0.5% host serving budget)`
- every unload succeeds
- every settle barrier reports clean
- every load succeeds
- `fatal_watermark_count = 0`
- `failure_measurement_count = 0`
- `unresolved_reclaim_barrier_events = 0`
- `session_cache_drops_total = 0`
- `session_cache_expirations_total = 0`
- `session_cache_rejects_total = 0`
- final cleanup unload succeeds

If total duration or swap count is short but all samples are clean, the result
is `blocked`, not `passed`.

If any generation, unload, settle, load, watermark, reclaim, cache, or cleanup
condition fails, the result is `failed`.

## 8. Failure Semantics

| Condition | Verdict | Meaning |
|---|---|---|
| §1 prerequisite missing | `blocked` | Do not run or aggregate §2 as promotion evidence |
| Segment shorter than target but clean | `blocked` | Useful segment only |
| Segment has host sleep / power gap | `blocked` | Operational interruption inside segment; not hard runtime failure |
| Aggregate duration < 24h | `blocked` | More clean segments required |
| Aggregate swap count < 6 | `blocked` | More clean swap boundaries required |
| Unload / settle / load failure | `failed` | Swap boundary failed |
| FATAL watermark | `failed` | Memory discipline failed |
| Reclaim-barrier unresolved failure | `failed` | Reclaim discipline failed |
| Session cache drop / expiration / reject during measurement | `failed` | Session cache stability failed |

## 9. Runner Implementation Notes

Preferred implementation path:

```text
scripts/bench/eviction_soak.py
  --gate b1c2-soak-plus-swap
  --gate b1c2-interrupted-soak-plus-swap
```

The first code-grade slice landed as a **fake/backend schema runner**. It
validates the ledger shape, swap phase records, blocked rollup semantics, and
the §1 prerequisite guard. It does not use native allocator truth and does not
make §2 native-run evidence.

The native execution slice now admits `--backend native` only when both of
these are true:

- `--b1c1-prerequisite-satisfied` is explicit
- all three rotation model paths are explicit (`--model-a`, `--model`,
  `--model-b`)

The first native smoke after the current-Mac §1 prerequisite was:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260521T074758Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

It proved native load/generate/unload/settle/load plumbing reaches allocator
truth, but the rollup correctly concluded `failed`:

- `allocator_truth_claimable=true`
- `measurement_mode=mlx_core_active_memory`
- `swap_boundaries_clean=true`
- `session_cache_drops_total=3`
- `max_drift_bytes=343408640` > `drift_budget_bytes=209715200`

The runner was then adjusted so B-1c §2 uses append-only per-session prompts
instead of reusing a byte-identical prompt. The first follow-up smoke:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260521T075608Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

also concluded `failed` with the same Qwen3.6-27B-4bit drop/drift signature
(`session_cache_drops_total=3`, `max_drift_bytes=343408640`). The ledger shows
the prompt did grow inside each session. Direct tokenizer triage then showed the
bench continuation separator was the blocker: Qwen generated token `271`
(`"\n\n"`), while re-tokenizing `"\nUser:"` after that continuation merged into a
different prefix token and forced a trim; Qwen's cache reported no trimmable
tokens for that path. The runner now uses a tokenizer-stable space continuation
for the B-1c §2 bench workload.

The corrected smoke:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260521T080541Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

is clean but intentionally `blocked` because it is only a short smoke:

- `allocator_truth_claimable=true`
- `measurement_mode=mlx_core_active_memory`
- `swap_boundaries_clean=true`
- `session_cache_drops_total=0`
- `max_drift_bytes=0`
- `hard_failure=false`
- `duration_requirement_met=false`
- `swap_requirement_met=false`

This unblocks the first 4h operator-interruptible §2 segment; it still does not
claim `soak_plus_swap_stability=passed` or `session_kv_supported=true`.

The first 4h segment attempt (`20260521T081118Z`) used the old prompt-growth
strategy and ran to completion, but it failed on cache drops at samples `111`,
`321`, and `573`. The deterministic follow-up canary (`20260522T114236Z`) then
failed earlier: after three warmup samples, all three first measurement samples
(`4/5/6`) recorded cache hit + drop before any swap boundary. It was manually
stopped with exit code `143`; the audit file
`20260522T114236Z-b1c2-qwen-gemma-qwen35-deterministic-early-stop-audit.json`
is failure/triage evidence only and does not contain a segment pass claim.

Implementation rule after this finding: B-1c §2 must fail fast and write a
failed rollup as soon as any per-sample session cache drop, expiration, or
reject is observed. The deterministic no-generated-text shape is no longer the
long-run strategy because the native backend's non-trimmable cache path is only
valid when the next prompt is an append-only transcript that includes the prior
generated text. The runner moved through two transcript-compatible variants:
`generated_text_then_stable_suffix`, then
`boundary_safe_generated_text_then_stable_suffix`.

Do not create new `*_harness.py`, `*_ledger.py`, `*_evidence.py`, or
`*_contract.py` modules for this work. Keep the bench runner in `scripts/bench/`
and put durable claims in markdown or JSONL evidence.

The transcript-compatible short canary:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260522T115512Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

is clean but intentionally `blocked`:

- `measurement_duration_s=26.667`
- `swap_count=1`
- `session_cache_drops_total=0`
- `session_cache_expirations_total=0`
- `session_cache_rejects_total=0`
- `max_drift_bytes=0`
- `swap_boundaries_clean=true`
- `hard_failure=false`
- `graduates.session_kv_supported=false`

The follow-up 4h fail-fast segment:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260522T115939Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

failed before the first swap:

- `measurement_duration_s=2133.518`
- prompt mix `36/36/36`
- `measurement_wall_clock_gap_free=true`
- `max_drift_bytes=50331648`
- `session_cache_drops_total=1`
- drop at sample `111`, prompt `long`, Qwen3.6-27B-4bit
- `swap_count=0`
- `soak_plus_swap_stability=failed`
- `graduates.session_kv_supported=false`

This segment is not clean aggregate input. It shows that the first short clean
canary was necessary but not sufficient; the next round should isolate Qwen
long-session token/cache-prefix behavior around the ~900-1000 character prompt
range instead of launching another 4h segment.

The focused no-sleep reproduction:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260522T151921Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

hit the same sample `111` / Qwen long-session drop in `26.528s`, proving the
4h segment failure is reproducible without wall-clock soak. Token-level triage
found the unsafe boundary: the previous prompt ended in `"."`, the generated
text was `"short"`, and re-tokenization merged the next prompt prefix into a
single `".short"` token. That forces an unsafe trim against the stored prompt
cache, which Qwen correctly rejects.
The token comparison is recorded in
`20260522T153000Z-b1c2-qwen-token-boundary-triage.json`.

A blind "always add one leading space before generated text" attempt:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260522T152210Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

failed earlier at sample `4`, because Qwen often generates whitespace
(`"\n\n"`). Prefixing an additional space before an already whitespace-started
continuation changes the stored token boundary and again forces an unsafe trim.

The current runner therefore uses
`boundary_safe_generated_text_then_stable_suffix`: preserve generated text
unchanged when it already starts with whitespace, and insert a single leading
space only when the generated text starts with a non-whitespace token. The
focused canary:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260522T152537Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

is clean but intentionally `blocked`:

- `measurement_duration_s=46.425`
- prompt mix `48/48/48`
- `session_cache_drops_total=0`
- `session_cache_expirations_total=0`
- `session_cache_rejects_total=0`
- `max_drift_bytes=50331648`
- `swap_count=1`
- `swap_boundaries_clean=true`
- `hard_failure=false`
- `graduates.session_kv_supported=false`

This closes the token-boundary canary and reopens the 4h fail-fast §2 segment
route. It still does not claim `soak_plus_swap_stability=passed`; the 24h / six
swap aggregate remains open.

The boundary-safe 4h segment:

```text
files/evidence/owlmlx/bench/session-kv-soak/
  20260522T164506Z-b1c2-qwen3.6-27b-gemma-4-31B-it-qwen3.6-35b-a3b-soak-swap-rollup.jsonl
```

ran to the planned swap boundary and closed the token-boundary blocker, but it
is still failed evidence:

- `measurement_duration_s=14439.346`
- prompt mix `238/238/238`
- `measurement_wall_clock_gap_free=true`
- `session_cache_drops_total=0`
- `session_cache_expirations_total=0`
- `session_cache_rejects_total=0`
- `swap_count=1`
- `swap_boundaries_clean=true`
- `fatal_watermark_count=0`
- `unresolved_reclaim_barrier_events=0`
- cleanup unload OK
- `max_drift_bytes=352321536` > `drift_budget_bytes=209715200`
- `soak_plus_swap_stability=failed`
- `graduates.session_kv_supported=false`

The max drift appears after sample `685` while cache counters remain clean:
`drops=0`, `hits=714`, `misses=3`, `entries_created=3`. This separates the next
blocker from token-boundary reuse: §2 now needs memory-drift triage before any
additional aggregate segment can be treated as clean input.

2026-05-24 Qwen-only no-swap drift probe:

- ledger:
  `files/evidence/owlmlx/bench/session-kv-soak/20260524T113306Z-b1c2-qwen3.6-27b-only-drift-probe-soak-swap.jsonl`
- rollup:
  `files/evidence/owlmlx/bench/session-kv-soak/20260524T113306Z-b1c2-qwen3.6-27b-only-drift-probe-soak-swap-rollup.jsonl`
- `rotation_label=qwen3.6-27b-only-drift-probe`
- `swap_count=0`
- `measurement_duration_s=322.505`
- timestamped samples: 720 (`warmup=3`, `measurement=717`)
- prompt mix: `239/239/239`
- cache drops / expirations / rejects: `0 / 0 / 0`
- `max_drift_bytes=352321536` > `drift_budget_bytes=209715200`
- first over-budget step: sample `486`, long prompt, `drift_bytes=218103808`,
  `prompt_chars_before_generation=3826`
- final repeated 4h-matching step: sample `685`, short prompt,
  `drift_bytes=352321536`, `prompt_chars_before_generation=5481`
- `soak_plus_swap_stability=failed`
- `graduates.session_kv_supported=false`

This reproduces the 352 MB drift without a model swap. The active-memory growth
is a regular 16 MiB allocator staircase correlated with prompt/session growth,
while the session cache remains clean. The next closure round is therefore not
another aggregate segment; it is a runtime/allocator policy decision for growing
session prompts.

2026-05-25 Qwen-only no-swap drift accounting probe:

- ledger:
  `files/evidence/owlmlx/bench/session-kv-soak/20260525T040839Z-b1c2-qwen3.6-27b-only-drift-accounting-v2-probe-soak-swap.jsonl`
- rollup:
  `files/evidence/owlmlx/bench/session-kv-soak/20260525T040839Z-b1c2-qwen3.6-27b-only-drift-accounting-v2-probe-soak-swap-rollup.jsonl`
- `rotation_label=qwen3.6-27b-only-drift-accounting-v2-probe`
- `swap_count=0`
- `measurement_duration_s=178.325`
- timestamped samples: 720 (`warmup=3`, `measurement=717`)
- prompt mix: `239/239/239`
- cache drops / expirations / rejects: `0 / 0 / 0`
- `max_drift_bytes=352321536` > `drift_budget_bytes=209715200`
- diagnostic `session_kv_drift_accounting.mode =
  active_memory_minus_session_kv_positive_delta_upper_bound`
- `max_session_cache_resident_bytes=1233125378`
- `max_unaccounted_session_kv_drift_bytes=0`
- `session_kv_drift_accounting.used_for_promotion_gate=false`
- `soak_plus_swap_stability=failed`
- `graduates.session_kv_supported=false`

This accounting slice proves the 352 MB drift can be covered by a deliberately
conservative positive `active_memory` delta estimate attached to session cache
entries. It does **not** prove the real resident KV working set is 1.23 GB: the
estimate is an upper bound and may double-count allocator high-watermark
stair-steps across generations. Therefore this field is diagnostic only and
must not be used to pass B-1c §2 or promote Session KV cache to `supported`.

2026-05-25 bounded-window policy probes:

- cache-only 1024-token window:
  `20260525T042215Z-b1c2-qwen3.6-27b-only-bounded-window-1024-probe-soak-swap-rollup.jsonl`
  ran 720 samples with cache drops / expirations / rejects all 0 and
  `session_cache_window_bypasses_total=329`, but `max_drift_bytes=293076992`
  still exceeded the 200 MiB budget. Conclusion: persistent-cache bypass alone
  reduces resident cache pressure but repeated long fresh-prefill requests still
  grow MLX active-memory high-watermark.
- prompt freeze 3000-char window after exact-hit empty-suffix runtime fix:
  `20260525T045707Z-b1c2-qwen3.6-27b-only-prompt-freeze-3000-exact-hit-probe-soak-swap-rollup.jsonl`
  kept `max_drift_bytes=150994944` within budget, but failed at sample `371`
  with `session_cache_drops_total=1` on the medium session at
  `prompt_chars_before_generation=3000`. Conclusion: bounded prompt growth can
  satisfy the memory budget, but bounded-context exact / capped prompt reuse
  still has a cache-finalization or trim-mismatch blocker.
- drop-reason probe:
  `20260525T051225Z-b1c2-qwen3.6-27b-only-prompt-freeze-3000-drop-reason-probe-soak-swap-rollup.jsonl`
  reproduced the same sample `371` failure and recorded
  `drop_reason_code=reuse_trim_mismatch`: the stored entry had `955` prompt
  tokens, the requested prompt had `954`, owlmlx requested a trim of `2`, and
  upstream `trim_prompt_cache` returned `0`.
- trim-unavailable safe bypass probe:
  `20260525T051719Z-b1c2-qwen3.6-27b-only-prompt-freeze-3000-trim-bypass-fix-probe-soak-swap-rollup.jsonl`
  ran 720 samples with drops / expirations / rejects all 0 and recorded
  `session_cache_trim_bypasses_total=173`. That closes the unknown drop cause,
  but it fails the memory budget with `max_drift_bytes=293076992` because
  repeated fresh-cache fallback reintroduces allocator high-watermark drift.
- prompt-reset 3000-char window probe:
  `20260525T055831Z-b1c2-qwen3.6-27b-only-prompt-reset-3000-probe-soak-swap-rollup.jsonl`
  ran 720 samples with drops / expirations / rejects all 0,
  `session_cache_trim_bypasses_total=3`, `session_cache_trim_evictions_total=3`,
  and `max_drift_bytes=171704320 <= 209715200`. This is the current
  bounded-window candidate: reset a session back to its base prompt when the
  prompt-growth cap is exceeded instead of repeatedly issuing capped prompts
  that require upstream trims. The rollup correctly remains `blocked` because
  it is Qwen-only focused evidence with `swap_count=0`, not a 24h / 6-swap §2
  segment.
- prompt-reset swap-bearing segment:
  `20260525T061019Z-b1c2-qwen-gemma-qwen35-prompt-reset-3000-4h-soak-swap-rollup.jsonl`
  ran warmup 3 + measurement 714 + swap 1 with drops / expirations / rejects
  all 0, `session_cache_trim_bypasses_total=3`,
  `session_cache_trim_evictions_total=3`,
  `max_drift_bytes=171704320 <= 209715200`,
  `swap_boundaries_clean=true`, FATAL 0, unresolved reclaim barrier 0, cleanup
  unload OK, and cleanup settle active memory 18 bytes. This validates the
  prompt-reset candidate across one real §2 swap boundary, but the rollup
  remains `blocked` and `clean_for_interrupted_aggregate=false` because
  `measurement_wall_clock_gap_free=false` with 6 measurement wall-clock gap
  violations (max `7064.873s`). It must not be counted toward interrupted
  aggregate duration or used for promotion.
- prompt-reset swap-bearing repeat:
  `20260601T025321Z-b1c2-qwen-gemma-qwen35-prompt-reset-3000-4h-soak-swap-rollup.jsonl`
  repeated the same 4h / 1-swap policy with drops / expirations / rejects all
  0, `session_cache_trim_bypasses_total=3`,
  `session_cache_trim_evictions_total=3`,
  `max_drift_bytes=171704320 <= 209715200`,
  `measurement_wall_clock_gap_free=true` (max gap `60.642s`),
  `ledger_gap_free=true`, `swap_boundaries_clean=true`, FATAL 0, unresolved
  reclaim barrier 0, cleanup unload OK, and cleanup settle active memory 18
  bytes. `scripts/bench/session_kv_soak_audit.py` reports
  `clean_for_interrupted_aggregate=true`. The segment rollup still correctly
  remains `blocked` because it is only 4h / 1 swap against the §7 24h / 6-swap
  requirement; it is aggregate input, not a pass.
- fast forced-swap canary:
  `20260601T125751Z-b1c2-qwen-gemma-qwen35-forced-swap-5min-soak-swap-rollup.jsonl`
  ran 20 minutes with 4 swaps at a 5-minute cadence. It completed all swap
  boundaries cleanly (`swap_boundaries_clean=true`), remained
  `measurement_wall_clock_gap_free=true`, and had drops / expirations / rejects
  all 0. The original rollup reported `max_drift_bytes=46801784452`, but this
  is a legacy global-baseline artifact: it compares Gemma active memory against
  the first Qwen27 measurement. Same-model load-epoch re-audit reports
  `max_same_model_load_epoch_drift_bytes=751370240` on Gemma and
  `max_same_model_load_epoch_unaccounted_session_kv_drift_bytes=0`. This canary
  is diagnostic only; it is not aggregate input and it does not promote §2.
- cache-object resident accounting canary:
  `20260601T134131Z-b1c2-qwen-gemma-qwen35-cache-nbytes-5min-soak-swap-rollup.jsonl`
  repeated the 5-minute cadence for 10 minutes / 2 swaps after the runtime began
  recording upstream cache-object bytes when available. It completed both swap
  boundaries cleanly, had drops / expirations / rejects all 0, and every
  measurement row reported `resident_bytes_estimate_mode=cache_object_nbytes`.
  The segment still failed the current raw drift gate
  (`max_same_model_load_epoch_drift_bytes=751370240` on Gemma, budget
  `209715200`), but direct resident-cache accounting reported
  `max_session_cache_resident_bytes=1054965760` and same-model unaccounted drift
  `0`. This is diagnostic only; it proves the drift is explained by a real held
  cache working set, not that §2 has passed.

The landed smoke-only slice covers:

- fake backend schema run
- one swap boundary
- blocked rollup if duration or swap count is short
- no session KV promotion claim

Only after schema tests pass should native execution be attempted.

## 10. Next Step

Do not resume passive aggregate evidence until the fast-swap drift gate is
settled. The next step is not another 4h wait; it is a metric/root-cause closure
for same-model load-epoch drift under high-frequency swaps now that direct
cache-object resident bytes are available.

1. Keep the safe trim-unavailable bypass semantics: pre-generation reuse trim
   refusal may fall back to a fresh request cache and must be counted as
   `trim_bypasses`, not as `drops`; partial trim mismatch remains a hard drop.
2. Use `reset_to_base_prompt_when_max_chars_exceeded` as the current
   prompt-window candidate; it passes the focused Qwen-only 720-sample
   drift/drop criteria and now has one gap-free swap-bearing aggregate input
   segment (`20260601T025321Z`).
3. Keep the 5-minute forced-swap canary as the fast boundary-stress shape while
   triaging whether raw same-model active-memory drift or a stricter resident
   working-set metric is the correct promotion gate.
4. Any new focused or swap-bearing probe must report `session_cache_drops_total=0`,
   `session_cache_expirations_total=0`, `session_cache_rejects_total=0`, and
   either the existing raw drift gate (`max_drift_bytes <= 209715200`) or an
   explicitly reviewed replacement gate based on direct cache-object resident
   bytes before §2 aggregate resumes.
5. Aggregate only gap-free, hard-failure-free segment rollups.
6. Require cumulative duration >= 24h and aggregate swap count >= 6 before
   `soak_plus_swap_stability=passed`.

## 11. Blocker Taxonomy (2026-06-01)

Closeout review after the first gap-free prompt-reset repeat. Maps the current
state to the §7 pass criteria and classifies what blocks
`soak_plus_swap_stability = passed`. The runtime / allocator layer is
functionally clean, and the current segment no longer has a measurement
continuity blocker. The remaining blocker is aggregate volume.

### B1 — Runtime / allocator stability: PASS (functional)

The prompt-reset bounded-window policy
(`reset_to_base_prompt_when_max_chars_exceeded`) closes the drift and trim
blockers. Latest gap-free swap-bearing segment (`20260601T025321Z`, one real
swap):

- `max_drift_bytes = 171704320` ≤ `209715200` (200 MiB) ✓
- `session_cache_drops / expirations / rejects = 0` ✓
- `session_cache_trim_bypasses_total = 3` (was 173) ✓
- `swap_boundaries_clean = true`, every unload OK ✓
- `fatal_watermark_count = 0`, `unresolved_reclaim_barrier_events = 0` ✓
- `measurement_wall_clock_gap_free = true`, `ledger_gap_free = true`,
  session mix balanced (238 / 238 / 238) ✓
- audit reports `clean_for_interrupted_aggregate = true` ✓

§7 criteria #2, #5, #6, #7, #8, #9 satisfied for this segment. No open runtime /
allocator defect.

### B2 — Measurement continuity: CLOSED for latest segment

The earlier `20260525T061019Z` segment failed §7 #5
(`measurement_wall_clock_gap_free`): 6 gaps, max 7064.873 s.
Ledger-timestamp forensics:

- sample 702 @ `10:08:43Z` → sample 703 @ `12:06:28Z` = ~1h58m with no samples,
  then 703 / 704 / 705 emitted within the same second (catch-up burst).

That freeze-then-instant-resume signature is **system sleep** (the process was
frozen; timers fired together on wake), not a swap-induced stall (which would
trickle) and not a runtime hang. `tmux + caffeinate -i` did not prevent it
(lid-close / battery / manual sleep defeats `-i`). Because §3/§5 disqualify
wall-clock gaps *inside* a segment, any sleep event during a segment voids that
segment as aggregate input. **This is environmental — it cannot be fixed in
`session_kv_cache.py`.**

The 2026-06-01 repeat used an explicit `caffeinate -dis` guard and produced
`measurement_wall_clock_gap_free=true`, max measurement gap `60.642s`, and zero
gap violations. That closes the single-segment measurement-continuity proof gap
for the current policy, while preserving the rule that future sleeping segments
must be excluded from aggregate evidence.

### B3 — Raw drift gate under direct cache-object accounting: BLOCKED

The 2026-06-01 cache-object resident canary (`20260601T134131Z`) records direct
cache-object bytes for every measurement row (`cache_object_nbytes`). It proves
the Gemma same-model raw drift (`751370240` bytes) is fully covered by a real
session-cache working set (`1054965760` bytes, unaccounted drift `0`). That is
not a cache drop and not a 46GB leak, but the current §7 pass criterion still
uses raw `max_drift_bytes <= 209715200`. Until the source-of-truth review
decides whether raw drift remains the hard gate or is replaced by a
cache-object-accounted resident working-set gate, §2 remains blocked.

### B4 — Aggregate volume: BLOCKED

§7 #3 (≥24h aggregate) and #4 (≥6 swaps) are unmet (latest aggregate-eligible
input: ~4h, 1 swap). This is now the independent remaining blocker: repeat the
same policy in five more gap-free segments only after B3 is closed, then
aggregate only the clean rollups.

### Route forward

1. **Eliminate sleep for the segment window**: `caffeinate -dis` on AC power,
   lid open; or `sudo pmset` to disable sleep for the window; keep the machine
   unused during a segment. On the current host, `caffeinate -m` is unsupported
   and `-u` exits quickly outside a user-idle assertion context.
2. **Close the drift-gate decision before aggregate resumes**: preserve the
   current raw gate unless a reviewed replacement gate explicitly uses direct
   cache-object resident bytes and keeps unaccounted same-model drift at 0.
3. **Run segments only in confirmed-awake windows**, aggregate via the §2
   interrupted route (each segment internally gap-free; segment *boundaries* are
   allowed). Recommended `6 × 4h`, one swap per segment (§5, §10).
4. **Dedicated always-on host** is the clean long-term route; a shared personal
   Mac is not a reliable 24h-soak measurement environment.
5. Do **not** relax §7 #5 — the gap-free requirement is correct; the fix is
   keeping the machine awake, not tolerating gaps.

### What this does NOT change

Session KV cache stays `experimental`; `session_kv_supported = false`; the bench
never auto-promotes. B1 passing is a functional observation of the §7 functional
criteria — not a promotion, and not a cross-runtime or readiness claim.

### 2026-06-01 fast-swap addendum

The 5-minute-cadence forced canary changed the immediate closure order. It
proved boundary mechanics are not the current fault, but it also showed that the
old global `max_drift_bytes` metric is not valid for multi-model measurement
epochs. Future B-1c §2 rollups must separate:

- legacy/global measurement-start drift, useful only for explaining old ledgers;
- same-model load-epoch active-memory drift, the raw gate candidate;
- same-model resident-cache-accounted drift, diagnostic only until a stricter
  working-set metric exists.

The current actionable blocker is not "run longer". It is deciding and proving
the correct drift gate for high-frequency multi-model cache reuse.

### 2026-06-01 cache-object resident addendum

The cache-object resident canary (`20260601T134131Z`) moves resident accounting
from a positive active-memory delta upper bound to direct upstream cache-object
`nbytes` when available:

- `session_cache_resident_bytes_estimate_modes=["cache_object_nbytes"]`
- `swap_count=2`, `swap_boundaries_clean=true`
- `session_cache_drops_total=0`, `expirations=0`, `rejects=0`
- `max_same_model_load_epoch_drift_bytes=751370240`
- `max_same_model_load_epoch_session_cache_resident_bytes=1054965760`
- `max_same_model_load_epoch_unaccounted_session_kv_drift_bytes=0`

This does not pass §2 because the raw gate remains active. It narrows the
blocker to a policy/gate decision: raw active-memory drift versus direct
cache-object resident working set.
