# owlmlx

**Developer preview** — self-owned Apple Silicon MLX runtime with measured
Qwen evidence and runtime-owned observability. Not yet a production replacement
for `oMLX` or `vMLX`. See `docs/source-of-truth/public-developer-preview-readiness.md`.

---

`owlmlx` is our own runtime.

It exists to become the runtime source of truth we actually need on Apple
Silicon, rather than a long-lived patch layer on top of someone else's
runtime. `oMLX` and `vMLX` matter to this project as reference points and
sources of proven ideas, not as identity anchors.

## Project Definition

`owlmlx` is a self-owned MLX runtime project with four frozen statements:

1. `owlmlx` is our own runtime.
2. Its direction is to replace `oMLX`, while absorbing useful experience from
   `oMLX`, `vMLX`, and other MLX runtimes as `owlmlx`'s own architecture.
3. The `large-weight runtime path` is the first mature path inside `owlmlx`;
   `Kimi` is the first validated specimen on that path, not the path's name.
4. The current desktop product shell repository, historically referred to as
   `local-llm-platform`, sits on top of `owlmlx` and is not a peer runtime
   source of truth.

## Why This Repository Exists

We are no longer solving a "patch upstream and hope it sticks" problem.

Our runtime direction already includes requirements that deserve their own
source of truth:

- Memory governance during multi-model switching
- Switch safety and restart-safe runtime behavior
- Runtime truth exposure to higher layers
- Background-heavy serving for workloads that do not fit interactive latency

Those goals are larger than a few upstream patches. They define a runtime
program.

## Developer Preview Status

`owlmlx` is in **developer preview** as of 2026-05-10. All seven
`release-readiness-backlog.md` floors are closed. The public surface is frozen
and documented in `public-surface.md`.

Measured short-prompt performance on `Mac17,6-arm64-macOS-26.4.1-128GB`
(`max_tokens=64`, `temperature=0`):

| Model | owlmlx TPS | Reference TPS | Runtime |
|---|---|---|---|
| Qwen3.6-27B | 5.45 | 2.81 | oMLX |
| Qwen3.6-35B-A3B | 3.53 | 2.44 | oMLX |
| Gemma 4 | 3.75 | 3.83 | vMLX |

These are short-prompt results. They do not imply broader parity or
replacement. See `docs/source-of-truth/public-developer-preview-readiness.md`
for the full claim matrix and honest open gaps.

Runtime-owned observability ships as first-class HTTP surfaces:

- `GET /v1/runtime/monitor/snapshot` — structured health snapshot
- `GET /v1/runtime/monitor/history` — persistent trend ledger
- `GET /metrics` — Prometheus exposition (`owlmlx_native_*` namespace)
- `GET /v1/runtime/model-release-candidates/history` — per-model RC evidence

## Current State

- Real runtime kernel: OpenAI-compatible, Anthropic-compatible, and
  native generation endpoints; FIFO admission gate; restart-safe lifecycle
- Runtime-owned memory governance: pressure classification, eviction policy,
  non-resident admission, recovery policy
- Technical-preview serving path: `scripts/runtime_technical_preview_server.py`
  launches a real `mlx_lm` subprocess backend without stopping legacy services
- Evidence program: Model RC ledger and comparative-evidence harness with
  measured same-host records
- Not owned: desktop shell, packaging, app distribution, operator UI —
  those belong to `owlops` and product layers above this runtime

## What `owlmlx` Is Not

- Not a renamed `oMLX` fork
- Not a thin wrapper around `vMLX`
- Not a copy of the current desktop product shell repository
- Not a GUI or dashboard project
- Not a claim that generalized foreground runtime is already solved

## Document Map

**Developer preview entry points:**
- `docs/source-of-truth/public-developer-preview-readiness.md` — readiness
  position, claim matrix, performance evidence, open gaps
- `docs/source-of-truth/public-surface.md` — frozen public surface boundary:
  supported HTTP routes, Python modules, operator scripts
- `docs/source-of-truth/release-readiness-backlog.md` — 7/7 floors closed;
  closure ledger with evidence references

**Runtime architecture:**
- `docs/source-of-truth/master-outline.md`
- `docs/source-of-truth/product-definition.md`
- `docs/source-of-truth/system-architecture.md`
- `docs/source-of-truth/single-host-orchestration-architecture.md`
- `docs/source-of-truth/repository-boundaries.md`
- `docs/source-of-truth/runtime-capability-matrix.md`
- `docs/source-of-truth/native-mlx-backend-capability-matrix.md`
- `docs/source-of-truth/runtime-contracts.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/runtime-governance.md`
- `docs/source-of-truth/hazardous-operations.md`

**Evidence program:**
- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/model-release-candidate-program.md`
- `docs/source-of-truth/reference-runtime-comparison-matrix.md`

**Governance truth:**
- `docs/source-of-truth/model-residency-policy.md`
- `docs/source-of-truth/memory-pressure-contract.md`
- `docs/source-of-truth/memory-pressure-eviction-policy.md`
- `docs/source-of-truth/nonresident-model-admission-policy.md`
- `docs/source-of-truth/termination-recovery-policy.md`
- `docs/source-of-truth/reclaim-barrier-event.md`

**Developer workflow:**
- `docs/source-of-truth/python-environment.md`
- `docs/source-of-truth/python-environment-research.md`
- `docs/source-of-truth/autonomous-loop-discipline.md`
- `docs/source-of-truth/roadmap.md`

## Immediate Priority

The runtime source-of-truth layer is stable. The current job is advancing
measured evidence coverage (heavier workloads, multi-turn, additional model
families) and closing the open gaps listed in
`docs/source-of-truth/public-developer-preview-readiness.md` §7.

## Development Environment

Project Python is **3.11.15** (pinned via `.python-version`); toolchain is
**uv**. From a fresh clone:

```bash
uv sync --extra runtime
uv run pytest
```

`pytest` will emit a loud `UserWarning` if invoked outside `.venv/` so the
default shell `python3` (often a different version) cannot be silently
used. See `docs/source-of-truth/python-environment.md` for full developer
workflow and `docs/source-of-truth/python-environment-research.md` for
the rationale behind the pin.
