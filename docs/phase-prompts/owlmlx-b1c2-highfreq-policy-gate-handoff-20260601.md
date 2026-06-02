# Handoff: no-header auto-prefix lane stability-threshold gate (B-1c §2 high-frequency policy)

> **Type**: design-grade spec handoff — pick up in a FRESH session per the
> fresh-session grade-transition rule. The exploration (this handoff) was done
> in a long context-heavy session; the spec authoring belongs to a clean one.
> **Prepared**: 2026-06-01, from `origin/main` `66440ad5` (synced 0/0).
> **Deliverable for the next session**: ONE design-grade spec deciding the
> stability threshold for the no-header automatic prefix-cache lane. NO code,
> NO bench run, NO capability-label promotion.

---

## 1. The one decision this gate must make

> **Does the no-header automatic prefix-cache lane (B-2.3) use the existing
> B-1c §2 `24h aggregate / 6-swap` threshold, or does it need a distinct
> high-frequency-cadence policy track as its honest stability gate?**

That is the whole gate. It is a **policy / threshold decision**, expressed as a
design spec, not a code change. It produces the criterion that a *later*
bench round measures against; it does not run the bench itself.

## 2. Why this is the next gate (verified state, 2026-06-01)

Three capability lines that all looked like separate work converge on **one**
bottleneck — cross-request KV-cache stability/reuse semantics:

- **B-2.3** (no-header auto prefix reuse) — first opt-in slice landed,
  experimental/default-off. Its own pass criterion (`B-2 spec §5.4`) says
  verbatim: *"B-1c section 2 aggregate / policy evidence is **sufficient for
  the claim being made**; otherwise the stage remains experimental and
  default-off."* → B-2.3 does **not** own a threshold; it defers to B-1c §2.
- **F-3** (Gemma4 resident MTP) — `failed` feasibility (`00fca918`); resident
  process works, MTP acceptance collapses to 0 on request 2+ in a trim regime.
  Same wall: hybrid cache + trim + cross-request reuse.
- **F-2 C2** (n-gram serving) — paused on the same hybrid-trim blocker.

So the live question is no longer "implement B-2.3" or "adapt OwlCoda/Codex" —
it is: **what stability bar makes the no-header auto lane safe to widen past
default-off?** That bar lives in B-1c §2.

## 3. The actual tension to resolve (the heart of the spec)

`B-1c-section-2-spec.md` defines its aggregate as (verified, §2 spec lines
27 / 78 / 81-82 / 173-175):

- aggregate measurement duration **≥ 24h**
- aggregate swap count **≥ 6**
- every segment `measurement_wall_clock_gap_free = true`
- shape origin: *"Original D3 shape was one continuous 24h run with six swaps
  every four hours."*

**But** the same spec's own status line (verified, §2 spec line 5) now says it
is *"blocked on aggregate volume / **policy**"* and that *"future evidence must
keep the **5-minute swap cadence** rather than passively waiting."* And the B-2
spec (§2 current-truth) says *"the right next step is a short forced-swap canary
with **high-frequency** swaps."*

→ The 24h/6-swap bar was shaped for D3's slow-swap continuous run. The
no-header auto-prefix lane is a **different stress profile**: many short
sessions, high-frequency prefix churn, frequent model/profile switches. The
spec must decide, with a stated rationale:

- **Option A** — reuse 24h/6-swap as-is for the no-header lane (one threshold
  for everything). Simple, but may be measuring the wrong stress (slow swaps
  don't exercise high-frequency prefix churn).
- **Option B** — add a distinct **high-frequency cadence track** (e.g. 5-min
  swap cadence, N swaps over a shorter wall-clock window, with the same
  gap-free + drift-budget + reclaim-clean per-segment criteria) as the honest
  gate for the no-header lane specifically, keeping 24h/6-swap for the original
  session-KV soak claim.
- **Option C** — both: 24h/6-swap remains the floor for the *base* session-KV
  capability; the no-header *auto* lane additionally requires the
  high-frequency track. (Two claims, two bars.)

The spec's job is to **pick one and justify it against the calibration rule**:
per the memory note *"observe runtime's own jitter before writing an
invariance/stability spec, else you manufacture a false-fail"* — so the spec
should require a short high-frequency observation to set the drift/cadence
numbers, not invent them.

## 4. Hard constraints (carry into the spec)

- **plan-grade source**: this is a B-1c §2 policy extension (Campaign B-1c),
  consumed by B-2.3 (Campaign B-2). Write the prereq/unlock chain both ways:
  this gate's output is the threshold B-2.3 cites; B-1c §2's existing aggregate
  is its sibling, not its parent.
- **field-name discipline** (README §83): reuse exact existing names —
  `measurement_wall_clock_gap_free`, `aggregate_measurement_duration_s`,
  `aggregate_swap_count`, `soak_plus_swap_stability`,
  `no_swap_soak_stability`, `cache_object_nbytes`. Do NOT coin new names for
  existing concepts. A new high-frequency track needs new names ONLY for the
  genuinely new cadence metric (e.g. `swap_cadence_s`, `high_freq_swap_count`).
- **one gate only** (README §27/§55): this spec decides the *threshold*. It
  does NOT run the canary, does NOT implement B-2.3 widening, does NOT promote
  any label. Those are separate downstream rounds.
- **calibration-before-spec** (memory: equivalence-standard-after-baseline):
  the drift budget / cadence numbers must be grounded in an observed
  high-frequency jitter sample, not asserted. If no such sample exists yet, the
  spec's first slice is "run a short high-frequency observation to set the
  numbers" — stated as a precondition, not faked.
- **no capability-label move**: B-2.3 stays experimental/default-off; this gate
  produces the *criterion* by which a future round could widen it.
- **leave-out set unchanged**: do not touch the standing dirty/untracked files
  (`suffix_decoding/*`, `.claude/`, canvas, competitor matrix, ds4 research,
  owl-lora-pipeline, 软件著作权申请资料/).

## 5. Files the next session must read first (load before writing)

1. `docs/architect/design/B-1c-section-2-spec.md` — the threshold being
   extended; §2 status line, §ll Blocker Taxonomy (2026-06-01), the
   24h/6-swap aggregate definition, the segment gap-free rule.
2. `docs/architect/design/B-2-mainstream-prefix-cache-compatibility-spec.md`
   §5.4 (B-2.3 pass criteria) + §2 current-truth (the high-frequency canary
   hint) — the consumer of this threshold.
3. `docs/architect/design/README.md` — the design-grade discipline (one gate,
   field-name alignment, prereq/unlock, two-signoff) and the spec table (add a
   row for this gate).
4. `docs/source-of-truth/session-kv-cache-experimental.md` — the experimental
   contract whose promotion gate this threshold feeds.
5. `docs/architect/01-mainline-roadmap.md` — Campaign B-1c / B-2 plan-grade
   lineage (so the spec cites the right plan-grade source line).

## 6. Suggested spec shape (the next session adapts)

- name: `docs/architect/design/B-1c-section-2-highfreq-policy-spec.md` (or a
  B-2.3-gating-criteria spec if the next session, after reading, judges the
  threshold belongs under B-2 instead — that judgment is theirs to make from
  the files, not pre-forced here)
- sections per README convention: Purpose · Prerequisites · The threshold
  decision (Option A/B/C + chosen rationale) · Verification contract (the
  pass/fail fields + cadence metric definitions) · Harness changes (which
  existing runner gets the high-freq cadence knob — likely the §2 native runner)
  · Evidence paths · Failure handling · Out-of-scope · Prereq/unlock · Refs ·
  Change log
- the **deliverable is the criterion**, written so a downstream bench round can
  execute it without re-litigating the policy.

## 7. What is already done (do not redo)

- B-2.0 contract freeze ✅ / B-2.1 classifier ✅ / B-2.2 cache-metadata
  plumbing ✅ (maps OpenAI `cached_tokens` / Anthropic `cache_read_input_tokens`
  only when backend detail exists).
- Truth-surface alignment ✅ (`66440ad5`): native-mlx capability matrix,
  public-surface, B-2 spec all now say "B-2.3 first opt-in no-header slice
  landed, still experimental/default-off" — no stale "not implemented" phrasing
  remains (verified 0 hits).
- B-1c §2 raw-RSS-drift false-fail ✅ closed via `cache_object_nbytes` resident
  accounting; §2 now blocked on aggregate volume/policy, not on drift.
- F-3.1 feasibility ✅ recorded as `failed` (`00fca918`); F-3 blocked, on
  upstream-watch (#980). Do not reopen F-3 in this gate.

## 8. Change Log

| Date | Change | By |
|---|---|---|
| 2026-06-01 | Handoff authored. Routes the "no-header auto-prefix lane stability threshold" decision (B-1c §2 high-frequency policy vs B-2.3 gating criteria) to a fresh design-grade session, after verifying the three-line convergence on cross-request KV-cache stability and the B-2.3→B-1c §2 threshold deferral. | architect session (this round) |
