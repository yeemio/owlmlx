# owlmlx Public Developer Preview Readiness

> Status: parked release gate
> Created: 2026-05-10
> Parked: 2026-05-10
> Scope: honest readiness position for public developer preview; anchored to
> measured evidence and closed release floors; does not supersede
> `release-readiness-backlog.md`, `public-surface.md`, or
> `reference-runtime-comparison-matrix.md`
>
> This document is accurate but its goal is deferred. The active goal is
> "Internal Replacement-Grade Runtime Depth." Public release is a parked gate
> with three re-open conditions; see
> `files/execution-prompts/owlmlx/coordinator-checkpoint-internal-replacement-grade-runtime-depth.md`.

## 1. One-Line Position

`owlmlx` is a self-owned Apple Silicon MLX runtime in **developer preview**:
measured Qwen evidence, runtime-owned observability, all seven release floors
closed — not yet a production replacement for `oMLX` or `vMLX`.

## 2. Release-Floor Status

All seven `release-readiness-backlog.md` floors are closed as of 2026-04-28.
This closure is the technical gate that permits the developer-preview label.
It does **not** promote `owlmlx` to release-ready, parity, or production-grade.

| Floor | Status | Closed |
|---|---|---|
| 3.1 Cache scheduler capability | closed (non-stream main path) | 2026-04-25 |
| 3.2 Memory-pressure decision | closed (runtime-owned eviction decision + execution) | 2026-04-26 |
| 3.3 Residency non-resident path | closed (runtime-owned loadability lineage) | 2026-04-25 |
| 3.4 Recovery policy | closed (runtime-owned termination recovery) | 2026-04-27 |
| 3.5 Comparative evidence | closed (same-host measured Qwen and Gemma evidence) | 2026-04-28 |
| 3.6 External customer evidence | closed (OwlOps-boundary external consumer evidence) | 2026-04-28 |
| 3.7 Public surface discipline | closed (frozen `public-surface.md` + contract test) | 2026-04-28 |

Source: `docs/source-of-truth/release-readiness-backlog.md` §5 closure ledger.

## 3. Measured Performance Evidence

All measurements: `max_tokens=64`, `temperature=0`, short-prompt, same host
(`Mac17,6-arm64-macOS-26.4.1-128GB`). Evidence files live in
`files/evidence/owlmlx/`.

| Model | owlmlx TPS | Reference | Reference TPS | Verdict |
|---|---|---|---|---|
| Qwen3.6-27B | 5.45 | oMLX | 2.81 | owlmlx ahead, short-prompt only |
| Qwen3.6-35B-A3B | 3.53 | oMLX | 2.44 | owlmlx ahead, short-prompt only |
| Gemma 4 | 3.75 | vMLX | 3.83 | close, not parity |
| DeepSeek-V4-Flash | n/a | — | — | unsupported loader; clean rejection |

**Critical scope boundary:** these are short-prompt single-turn results on one
host configuration. They do not extend to longer prompts, multi-turn,
concurrent workloads, cache-reuse paths, or other model families.

Source: `docs/source-of-truth/reference-runtime-comparison-matrix.md` §0 and §4.

## 4. Runtime-Owned Observability

`owlmlx` is the only MLX runtime in this comparison that ships a
runtime-owned monitor surface with the following properties:

- `/v1/runtime/monitor/snapshot` — structured health snapshot, source-tagged
- `/v1/runtime/monitor/history` — persistent trend ledger, runtime-owned sampling
- `/v1/runtime/test-runs` — runtime-managed test-run lifecycle with audit ledger
- `/v1/runtime/model-release-candidates/history` — Model RC program with
  measured evidence per model, stored in-repo
- `/metrics` — Prometheus exposition (v0.0.4), `owlmlx_native_*` namespace

These surfaces do not require an external operator tool to consume. They are
part of the public surface freeze (`public-surface.md` §3).

## 5. What Can Be Stated

The following claims are honest for developer-preview external communication:

- `owlmlx` is a self-owned Apple Silicon MLX runtime in developer preview
- The runtime is backed by real serving infrastructure: OpenAI-compatible
  endpoints, Anthropic-compatible endpoints, a generation gate with FIFO
  admission, runtime-owned memory governance, and restart-safe lifecycle
- All seven release floors are closed; the technical-preview surface is frozen
  and documented in `public-surface.md`
- On short-prompt Qwen benchmarks (`max_tokens=64`, same-host,
  `Mac17,6-arm64-macOS-26.4.1-128GB`), `owlmlx` measured faster than `oMLX`
  (Qwen3.6-27B: 5.45 vs 2.81 TPS; Qwen3.6-35B-A3B: 3.53 vs 2.44 TPS)
- On short-prompt Gemma, `owlmlx` measured close to but below `vMLX`
  (3.75 vs 3.83 TPS)
- `owlmlx` returns a clean pre-load rejection for unsupported model families
  (`deepseek_v4`, `deepseek_v3`) without dirtying runtime health
- The runtime ships a runtime-owned monitor surface (`/v1/runtime/monitor/*`)
  not present in reference runtimes as a first-class runtime-truth contract

## 6. What Cannot Be Stated

The following claims are prohibited and must not appear in any external
communication:

- "release-ready" or "production-ready"
- "replaces oMLX" or "replaces vMLX"
- "parity" with any reference runtime
- "production-grade" or "production-quality"
- "superior to", "better than", or "beats" in any unqualified form
- "equivalent" (unqualified)
- Any claim derived from the short-prompt evidence that implies broader workload
  generalization (longer prompts, multi-turn, concurrent, cache-reuse paths)
- DeepSeek support or measured DeepSeek generation
- Heavy-weight repeatability at reference-grade confidence
- Scheduler depth or continuous-batching depth comparable to `vMLX`
- End-user packaging, app distribution, or installation ergonomics

Source: `public-surface.md` §10; `release-readiness-backlog.md` §4.3;
`BANNED_VERDICT_VOCABULARY` in `owlmlx.comparative_evidence_schema`.

## 7. Open Gaps That Remain Below Reference Grade

These are honest gaps as of this freeze. Developer-preview label is compatible
with their existence; they are not hidden:

- **Heavy-weight repeatability** — not yet restored to reference-grade confidence
  across multi-run repeated execution; tracked in
  `phase45-heavy-weight-repeatability-status.md`
- **Host-stable execution confidence** — large model multi-run stability
  improvements in progress; tracked in `phase45-host-stable-execution-status.md`
- **Scheduler / batching depth** — frozen at structural ingress seam;
  continuous-batching and deeper scheduler work remain below `vMLX` depth
- **Broader model-family coverage** — only Qwen3.6-27B, Qwen3.6-35B-A3B, and
  Gemma have measured evidence; DeepSeek and other families are either rejected
  or without measured records
- **Multi-turn / longer prompt / concurrent workload evidence** — no measured
  evidence beyond `max_tokens=64` single-turn

None of these gaps invalidates the developer-preview label. They define the
honest scope of that label.

## 8. Intended External Audience

Developer preview is appropriate for:

- Apple Silicon ML engineers evaluating a runtime with runtime-owned truth and
  governance surfaces
- OwlOps / OwlCoda consumers who depend on the public HTTP surface
- Researchers interested in runtime-owned observability and evidence discipline

Developer preview is **not appropriate for**:

- End users expecting a polished installation story (owlmlx intentionally does
  not own packaging or app distribution)
- Production workloads with multi-turn, concurrent, or heavy-weight requirements
- Deployments requiring DeepSeek or broad model-family coverage

## 9. Relationship to Public Surface Freeze

The developer-preview readiness position is bounded by `public-surface.md`:

- The public surface is frozen at `v1`
- Consumers must use only surfaces listed in `public-surface.md` §3–§6
- Anything not listed there is `internal` and may change without notice
- The banned-vocabulary rules in `public-surface.md` §10 are runtime-enforced
  via schema validation, not only documentation

## 10. Update Rule

This document is updated when:

- a new release floor closes that changes the honest position
- a new measured evidence record changes the performance comparison table in §3
- an open gap in §7 is honestly closed or honestly widened
- the developer-preview label is upgraded or downgraded

This document is not updated to relax open gaps in response to schedule
pressure, nor to promote the label ahead of evidence.
