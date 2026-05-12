# owlmlx Next Stage Runtime Discipline Handoff — 2026-05-12

## Purpose

This handoff closes the current window and gives the next Codex window a
reopen-safe entry point for the new stage.

The next stage is still `owlmlx` runtime work. It is **not** an OwlCoda
implementation stage. OwlCoda remains a downstream consumer and future public
release acceptance gate.

## Current Verified Truth

- Current repo: `/Users/yeemio/AI/gitrep/owlmlx`
- Current branch: `main`
- `main` is aligned with `origin/main`
- Current HEAD: `d76fb539 Add resumed Track B cache eviction prompt`
- All local refactor branches are merged into local `main`
- Only known dirty file: `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`
  - This is runtime-generated local evidence.
  - Do not stage it unless explicitly asked.
- Public release standard is frozen in:
  - `docs/source-of-truth/public-release-standard.md`
- Coordinator correction is frozen in:
  - `docs/source-of-truth/owlcoda-learning-loop-coordination.md`
- Track B resume prompt exists at:
  - `files/execution-prompts/owlmlx/stage-3.3-track-b-resume-cache-residency-eviction.md`
- Eviction soak script is currently a placeholder:
  - `scripts/bench/eviction_soak.py`
  - It exits `2` by design and has no implementation yet.

## What Not To Reopen

- Do not reopen Stage 3.2 independence cleanup. It is complete.
- Do not treat Agent-side oMLX patch tooling as an owlmlx migration target.
- Do not switch the current mainline to OwlCoda.
- Do not claim public release, developer-preview release, production-ready, or
  OwlCoda learning-loop complete.
- Do not treat Track B completion as public release closure.
- Do not add new spec-as-code modules. AGENTS.md Stage 1 anti-regression rules
  still apply.
- Do not stage `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`.

## Current Runtime / Deployment

No live runtime was restarted or changed during this handoff.

Known prior convention:

- `8066` is the local owlmlx runtime port when running.
- Before relying on it, verify live state with:

```bash
curl -fsS http://127.0.0.1:8066/healthz
curl -fsS http://127.0.0.1:8066/v1/runtime/monitor/snapshot | python3 -m json.tool | head -80
```

## Important Files

- `AGENTS.md` — read first; includes anti-regression rule.
- `docs/source-of-truth/runtime-spine-architecture-blueprint.zh.md` — Chinese architecture blueprint.
- `docs/source-of-truth/owlcoda-learning-loop-coordination.md` — corrected coordinator decision.
- `docs/source-of-truth/public-release-standard.md` — future public release gate.
- `files/execution-prompts/owlmlx/stage-3.3-track-b-resume-cache-residency-eviction.md` — old Track B resume prompt.
- `scripts/bench/eviction_soak.py` — Stage 4 placeholder, now likely needs to move ahead of Track B runtime changes.
- `owlmlx/cache_manager.py`
- `owlmlx/cache_residency_tracker.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/model_residency_policy.py`
- `owlmlx/runtime/kernel.py`

## Known Gaps

The latest external-architect review found three main issues:

1. Docs have begun to expand again after Stage 1 reduced spec-as-code. Do not
   answer every uncertainty with a new long narrative document.
2. The public release gate is good, but the v0 learning artifact shape is not
   frozen. It must be a short decision, not a new blueprint.
3. `owlmlx`'s main differentiator is memory discipline, but
   `scripts/bench/eviction_soak.py` is still a placeholder. There is no first
   50-round model-switch soak report proving zero memory accumulation.

## Next Dominant Gap

`memory_discipline_baseline_missing`

Do not start by expanding Track B architecture. First establish baseline
evidence for the memory-discipline claim.

Recommended next order:

1. Freeze v0 learning artifact shape in a tiny decision doc, maximum 50 lines.
   This should answer only:
   - data shape: tool-use trace / preference pair / conversation trace / other
   - learning shape: LoRA / DPO / continual pretrain / no-op adapter verdict
   - runtime registration shape: model lineage adapter chain or other existing surface
2. Implement and run `scripts/bench/eviction_soak.py` for owlmlx first.
   - Start with N=2 or N=3 smoke.
   - Then N=50 only after the smoke proves ledger shape and cleanup.
3. Only after the soak baseline, resume Track B cache/residency/eviction runtime changes.

## Suggested First Commands

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
git status --short --branch
git log --oneline --decorate -5
sed -n '1,220p' docs/source-of-truth/owlcoda-learning-loop-coordination.md
sed -n '1,220p' docs/source-of-truth/public-release-standard.md
sed -n '1,220p' scripts/bench/eviction_soak.py
```

If creating a branch for the next stage:

```bash
git switch main
git pull --ff-only
git switch -c refactor/stage-3.3-memory-discipline-baseline
```

## Starter Prompt For New Window

```text
We are in /Users/yeemio/AI/gitrep/owlmlx. Read AGENTS.md and
docs/handoff/owlmlx-next-stage-runtime-discipline-handoff-20260512.md first.

Current main is synced to origin/main at d76fb539. Only expected dirty file is
files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl; do not stage it.

The current mainline is still owlmlx runtime capability, not OwlCoda. OwlCoda is
the downstream public release acceptance gate, but do not start OwlCoda work.

Next dominant gap: memory_discipline_baseline_missing.

First, create a very short v0 learning artifact decision doc (<=50 lines) so
Track B knows whether future learning means LoRA / DPO / continual pretrain /
another shape. Then implement the first owlmlx-only eviction_soak baseline in
scripts/bench/eviction_soak.py. Start with N=2 or N=3 smoke, produce JSONL
evidence, and only then consider the N=50 run. Do not claim public release,
prefix cache, continuous batching, or cache parity.
```
