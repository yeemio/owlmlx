# B-1c Section 2 · High-Frequency Swap Policy · Design-Grade Spec

> **Gate**: Campaign B-1c §2 high-frequency swap-cadence stability policy — the
> honest threshold the no-header automatic prefix-cache lane (B-2.3) defers to.
> **Layer**: design-grade, downstream of `../01-mainline-roadmap.md`
> (Campaign B-1c), consumed by Campaign B-2
> (`B-2-mainstream-prefix-cache-compatibility-spec.md` §5.4).
> **Status**: superseded 2026-06-02 by the base §7 count-based reset in
> `B-1c-section-2-spec.md`. This file is retained as the decision-history record
> for why 5-minute switch cadence matters, but its earlier Option C split
> (base 24h/6-swap unchanged; separate high-frequency sibling gate) is no longer
> current policy.
> **Capability label**: unchanged. Session KV cache stays `experimental`; the
> B-2.3 no-header auto-prefix lane stays `experimental` and default-off. This
> spec promotes nothing; it defines the criterion a *later* bench round measures.

## 1. Purpose

This historical spec was written when `B-1c-section-2-spec.md` §7 still defined
the §2 pass bar as **≥24h aggregate duration / ≥6 swaps, every segment
wall-clock-gap-free**. That shape was inherited from D3: *"one continuous 24h
run with six swaps every four hours"* — a slow-swap endurance soak.

The current base spec has since absorbed the high-frequency insight and replaced
the duration-first bar entirely with four count-based axes:
`load_stability`, `throughput_stability`, `switch_stability`, and
`concurrency_stability`. Duration is now a reported byproduct, not a pass gate.

B-2.3 (no-header automatic prefix reuse) does **not** own a stability threshold.
Its pass criterion (`B-2-...-spec.md` §5.4) defers verbatim: *"B-1c section 2
aggregate / policy evidence is sufficient for the claim being made; otherwise
the stage remains experimental and default-off."*

This spec supplied the deferred policy before the base reset. It answered one
question:

> **Does the no-header automatic prefix-cache lane use the existing 24h/6-swap
> aggregate as its stability gate, or does it need a distinct high-frequency
> swap-cadence track?**

It does **not** run the canary, implement lane widening, or move any label.

## 2. Current truth this policy is written from (2026-06-02)

The runtime/allocator layer is already functionally clean for one swap-bearing
segment (`B-1c-section-2-spec.md` §11 B1, segment `20260601T025321Z`). The live
blockers are measurement gaps in the four-axis base gate: throughput decay and
concurrency breadth. Three lines converge on cross-request KV-cache
stability/reuse semantics:

- **B-2.3** no-header lane: first opt-in slice landed (`experimental`,
  default-off, `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`). It now produces a
  real no-header hit via prompt-only refresh (`20260602T011000Z`,
  `usable_hit_count=1`) and the three-model compat-route metadata path passed
  (`20260602T015245Z` / `20260602T015559Z`). The lane's mechanics work; only its
  stability threshold is open.
- **F-3** resident MTP: `failed` feasibility (`00fca918`) on the same hybrid
  cache + trim + cross-request reuse wall. Out of scope here; do not reopen.
- **F-2 C2** n-gram serving: paused on the same hybrid-trim blocker.

The decisive observation: the 5-minute forced-swap cadence is not a convenience
— it is the stressor that **found a real defect**. The 2h/24-swap run
(`20260601T141659Z`) kept boundaries/drops/expirations/rejects clean yet drove
Gemma resident cache to `2768240640` bytes, over the reviewed `2147483648`
working-set budget. Slow 4h-swap soaking would have hidden that capacity
problem. The follow-up LRU cap (`OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES`) and
the 40m/8-swap validation (`20260601T162203Z`, `2144829440 <= 2147483648`, 4
evictions, clean) closed it functionally. Both `B-1c-section-2-spec.md` §10 and
§11 B4 already direct future evidence to *retain the 5-minute cadence so duration
and swap count grow together*, rather than resume passive single-swap waits.

## 3. The threshold decision

### 3.1 Options considered

- **Option A** — reuse 24h/6-swap as-is for the no-header lane. Rejected: a
  slow-swap endurance soak does not exercise the no-header lane's actual risk
  (high-frequency prefix churn + frequent unload/settle/load). It would gate the
  lane on a measurement of the *wrong* stress. "Hardest bar" is not the same as
  "honest bar"; §2's own evidence shows the slow shape hides the real failure.
- **Option B** — replace 24h/6-swap with a high-frequency track for the
  no-header lane, and keep 24h/6-swap only for the base session-KV soak claim.
  Rejected as the *sole* gate: the no-header lane is built on the session KV
  cache, so it inherits the base capability's long-run endurance risk. Letting
  the lane shed the base endurance claim entirely would under-gate a default-on
  / `supported` widening.
- **Option C (graduated)** — **chosen.** Two claims, two bars, applied to the
  claim grade.

### 3.2 Historical decision — Option C, graduated by claim

| Claim being made | Honest stability gate |
|---|---|
| Base Session KV cache → `supported` (the §1a Promotion Gate) | **Superseded.** This used to say base §7 stayed at ≥24h aggregate / ≥6 swaps. The current base §7 is four-axis count-based. |
| No-header auto-prefix lane (B-2.3) → widen experimental confidence past the current opt-in/default-off floor | **New high-frequency swap-cadence track** (§4). This is the evidence "sufficient for the claim being made" under B-2.3 §5.4 for the narrow, flag-gated, experimental claim. |
| No-header auto-prefix lane → default-on / `supported` | **Both bars above**, plus wider B-2 compatibility coverage (`B-2-...-spec.md` §11). The high-frequency track alone never makes the lane default-on. |

Rationale: the high-frequency track measures the property the no-header lane
actually claims (reuse-under-churn safety + bounded resident pressure across
rapid swaps), which the slow 24h/6-swap shape did not. The current base gate now
requires the wider four-axis proof for any bigger default-on / `supported` step,
so nothing is relaxed for the promotion that warrants broad endurance and
isolation evidence. This keeps a working lane from being permanently blocked
behind an environmentally-stuck 24h soak (Mac sleep voids segments — §11 B2) for
its *narrow* claim, while refusing to let it go default-on on sub-axis evidence.

## 4. The high-frequency track — verification contract

A **high-frequency segment** is one B-1c §2 soak-plus-swap segment run at a
forced short swap cadence under the resident cap. New rollup fields (only two new
names; everything else reuses existing field names per `README.md` §83):

```yaml
swap_cadence_s: <float>        # NEW. Forced wall-clock seconds between swaps.
high_freq_swap_count: <int>    # NEW. Swaps completed at swap_cadence_s in segment.
```

### 4.1 Per-segment pass conditions

A high-frequency segment is **clean aggregate input** only when all hold:

- `swap_cadence_s <= 300` (the observed boundary stressor; 5-minute cadence)
- `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES` is set to the reviewed working-set
  budget (`2147483648`) and `max_session_cache_resident_bytes <=
  OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES`
- drift gate `drift_gate.mode = cache_object_resident_accounted` with estimate
  kind `cache_object_nbytes`, and
  `max_same_model_load_epoch_unaccounted_session_kv_drift_bytes <=
  drift_budget_bytes` (`209715200`)
- `session_cache_drops_total = 0`, `session_cache_expirations_total = 0`,
  `session_cache_rejects_total = 0`
- LRU pressure relief is recorded as `session_cache_trim_evictions_total` /
  `evictions`, **never** counted as drops
- `swap_boundaries_clean = true`; every unload, settle barrier, and load OK
- `fatal_watermark_count = 0`, `unresolved_reclaim_barrier_events = 0`
- `measurement_wall_clock_gap_free = true`, `ledger_gap_free = true`
- short / medium / long session mix present in the segment
- audit reports `clean_for_interrupted_aggregate = true`

### 4.2 Aggregate pass condition (the threshold)

`high_freq_swap_stability = passed` requires, across clean high-frequency
segments only:

- `aggregate(high_freq_swap_count) >= 24`
- `aggregate_measurement_duration_s >= 7200` (2h) at `swap_cadence_s <= 300`
- every aggregated segment satisfies §4.1
- the base B-1c §1 prerequisite is already satisfied (carried unchanged)

**Why these numbers, and what they do / do not prove (calibration honesty):**
the `>= 24` swap floor and `>= 2h` duration reproduce the
`20260601T141659Z` stress shape — the exact shape that *surfaced* the resident
pressure blocker — now required to run **clean under the cap**. They are grounded
in observation, not invented. 24 clean swaps bounds the per-swap boundary-defect
rate to roughly `p <= 12%` at ~95% confidence (rule of three, `3/24`); this is a
4× step up from §7's 6-swap floor but is **not** a low-defect-rate proof. The
number is a floor with a stated rationale, not a sacred constant: raise it by
aggregating more clean high-frequency segments when a tighter bound is wanted.
The first clean reproduction confirms the floor is achievable; if it is not, the
blocker it exposes — not a relaxed number — is the next gate.

### 4.3 Calibration status

The cadence (`<= 300s`) and resident budget (`2147483648`) are already observed
and reviewed (`20260601T141659Z` / `162203Z`; `B-1c-section-2-spec.md` §11 B3a).
What does **not** yet exist is a single high-frequency segment that is both
≥2h/≥24-swap **and** clean under the cap (the 2h/24-swap run predated the cap and
failed; the post-cap validation is only 40m/8-swap). Per the
calibration-before-spec rule (`memory: equivalence-standard-after-baseline`),
this spec sets cadence/budget from observation and defines the volume floor from
the observed blocker shape; it does not assert a drift/cadence number that has
never been measured.

## 5. Harness changes (minimal — no new modules)

Single existing runner: `scripts/bench/eviction_soak.py` (the §2 native runner).

- Today `_next_swap_due()` derives the interval as
  `swap_interval_s = duration_s / max(swap_count, 1)` (line ~2819) — cadence is a
  side effect of duration ÷ swap count. The 5-minute canaries achieved cadence by
  hand-tuning short duration + swap count.
- Change: add an explicit `--swap-cadence-s` knob that, when set, overrides the
  derived interval (`swap_interval_s = swap_cadence_s`) and decouples swap count
  from duration, so a segment can run long while swapping every 5 minutes.
- Emit `swap_cadence_s` and `high_freq_swap_count` in the segment rollup.
- Require `OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES` to be set for high-frequency
  segments; surface `session_cache_trim_evictions_total` separately from drops.

No `*_harness.py` / `*_ledger.py` / `*_evidence.py` / `*_contract.py` modules
(`README.md` §26 Stage-1 ban; `B-2-...-spec.md` §8). The cadence knob and rollup
fields are code-grade work for a **separate** round; this spec only specifies it.

## 6. Evidence paths

Existing root: `files/evidence/owlmlx/bench/session-kv-soak/`.
Row family stays `b1c2.v1`, extended with the two high-frequency fields.
Recommended naming:

```text
<timestamp>-b1c2-<rotation-label>-highfreq-<cadence>-soak-swap.jsonl
<timestamp>-b1c2-<rotation-label>-highfreq-<cadence>-soak-swap-rollup.jsonl
```

No evidence file produced under this policy promotes the capability.

## 7. Failure handling

| Condition | Verdict | Meaning |
|---|---|---|
| Segment shorter than §4.2 floor but clean | `blocked` | Useful high-frequency aggregate input only |
| Host sleep / power gap inside a segment | `blocked` | Environmental; voids that segment as aggregate input (§11 B2) |
| `max_session_cache_resident_bytes` over the cap | `failed` | Resident-pressure discipline failed (the `20260601T141659Z` class) |
| Drop / expiration / reject during measurement | `failed` | Cross-request reuse stability failed |
| Unload / settle / load failure at a swap boundary | `failed` | Boundary mechanics failed under churn |
| FATAL watermark / unresolved reclaim barrier | `failed` | Memory discipline failed |

Evictions under the LRU cap are **not** failures; they are bounded-pressure
relief and are counted separately.

## 8. Supersession Boundary

Current policy lives in `B-1c-section-2-spec.md` §7. This historical file should
not be used to argue that base §7 still has a duration-first 24h/6-swap bar. The
parts that remain useful are:

- 5-minute cadence is the right switch stressor because it found a real resident
  pressure defect;
- resident cap / direct cache-object accounting remain required for the load
  axis;
- a clean high-frequency segment is not enough if throughput and concurrency
  axes remain under-measured.

No capability label is promoted by this file.
- The standing dirty / untracked leave-out set (`suffix_decoding/*`, `.claude/`,
  `04-architecture-canvas.html`, competitor matrix, `ds4-*` research,
  `owl-lora-pipeline`, `软件著作权申请资料/`).

## 9. Prerequisites and unlock chain

**Prerequisite to satisfy this gate** (not to author this spec):

- B-1c §1 prerequisite already satisfied (`current_mac_section_1_prerequisite_met=true`).
- B-1c §2 runtime/allocator layer functionally clean (`B-1c-section-2-spec.md`
  §11 B1) and the resident cap landed (§11 B3a). Both already true.

**What passing `high_freq_swap_stability` unlocks:**

- It is the evidence B-2.3 §5.4 defers to for the **narrow** experimental claim:
  it can raise confidence in widening the no-header lane past the current opt-in
  floor. It does **not** by itself make the lane default-on or `supported`, and
  it does **not** unlock base Session KV `supported` (that remains the §1a Gate
  with B-1c §2's four-axis count-based gate).

**Sibling, not parent:** the base four-axis B-1c §2 gate is this track's sibling
under Campaign B-1c §2, not its parent. The base soak claim and the no-header
lane claim are measured by different bars (§3.2).

## 10. References

- `B-1c-section-2-spec.md` §5 / §7 / §10 / §11 (B1–B4, route forward) — the base
  threshold this extends and the evidence it is grounded in.
- `B-2-mainstream-prefix-cache-compatibility-spec.md` §2 / §5.4 / §11 / §12 —
  the consumer; the deferral; the promotion ceiling.
- `../../source-of-truth/session-kv-cache-experimental.md` §5 / §7 — the
  experimental contract and superseded flat promotion gate.
- `../01-mainline-roadmap.md` — Campaign B-1c / B-2 plan-grade lineage.
- Evidence: `20260601T141659Z` (blocker-surfacing 2h/24-swap),
  `20260601T162203Z` (40m/8-swap cap validation), `20260602T011000Z` (no-header
  real hit), `20260602T002448Z` (auto-prefix 20m/4-swap safety, clean).

## 11. Change log

| Date | Change | By |
|---|---|---|
| 2026-06-02 | Spec authored from the `owlmlx-b1c2-highfreq-policy-gate-handoff-20260601` handoff. It originally decided **Option C (graduated)**: base Session KV `supported` kept the old §7 24h/6-swap bar, while the no-header auto-prefix lane's narrow experimental widening used a new high-frequency swap-cadence track (`swap_cadence_s <= 300`, `high_freq_swap_count >= 24`, ≥2h, under the resident cap, with the reviewed `cache_object_resident_accounted` drift gate). Numbers grounded in the `20260601T141659Z` blocker shape, floor flagged not-sacred. Design-grade only; no code, no bench, no label move. Pending sign-off. | fresh design session |
| 2026-06-02 | Superseded by user decision to re-found base §7 itself on four count-based axes. Duration is demoted to reported byproduct; high-frequency switch count is folded into `switch_stability`; throughput and concurrency are explicit blocked axes until measured. | count-based reset |
