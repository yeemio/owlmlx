# owlmlx Public Claim Matrix

> Status: authoritative
> Created: 2026-05-10
> Scope: machine-readable table of allowed and prohibited claims for any
> external communication about owlmlx; anchored to evidence, closed floors, and
> the current public release gate in `public-release-standard.md`

## 1. Purpose

This document is the single reference for deciding whether a proposed external
claim about `owlmlx` is honest. It supplements `public-surface.md` §10 and
`release-readiness-backlog.md` §4.3 with a claim-by-claim ruling and an
evidence pointer for each allowed claim.

Rules:
- `allowed` — can appear in external README, release notes, or documentation
- `allowed (scoped)` — allowed only with the stated scope qualification
- `prohibited` — must not appear in any external communication

Scope qualifications are not optional. A claim listed as `allowed (scoped)`
becomes prohibited if the qualification is omitted.

## 2. Identity Claims

| Claim | Ruling | Evidence / source |
|---|---|---|
| "owlmlx is a self-owned Apple Silicon MLX runtime" | allowed | `product-definition.md`, `repository-boundaries.md` |
| "owlmlx is in developer preview" | prohibited for current public release copy | Superseded by `public-release-standard.md`; the old developer-preview threshold is parked until the OwlCoda npm local-learning loop is proven |
| "owlmlx is a technical preview runtime" | allowed (scoped) | Allowed only in engineering docs as "technical-preview surface"; not a public release label |
| "owlmlx is an early formal runtime" | allowed | `release-readiness-backlog.md` §2 |
| "owlmlx is production-ready" | prohibited | `public-surface.md` §10 |
| "owlmlx is production-grade" | prohibited | `public-surface.md` §10 |
| "owlmlx is release-ready" | prohibited | `public-surface.md` §10 |
| "owlmlx replaces oMLX" | prohibited | `public-surface.md` §10 |
| "owlmlx replaces vMLX" | prohibited | `public-surface.md` §10 |

## 3. Performance Claims

| Claim | Ruling | Evidence / source |
|---|---|---|
| "On short-prompt Qwen3.6-27B benchmarks (max_tokens=64, same host), owlmlx measured 5.45 TPS vs oMLX 2.81 TPS" | allowed (scoped) | `files/evidence/owlmlx/comparative-evidence/20260506.../` ; scope: short-prompt, `mac17,6-arm64-macos-26.4.1-128GB` |
| "On short-prompt Qwen3.6-35B-A3B benchmarks (max_tokens=64, same host), owlmlx measured 3.53 TPS vs oMLX 2.44 TPS" | allowed (scoped) | same scope boundary |
| "On short-prompt Gemma 4 benchmarks (max_tokens=64, same host), owlmlx measured 3.75 TPS vs vMLX 3.83 TPS" | allowed (scoped) | same scope boundary; note: close but below vMLX |
| "owlmlx is faster than oMLX" (unqualified) | prohibited | scope required; short-prompt only; does not generalize |
| "owlmlx is faster than vMLX" (unqualified) | prohibited | Gemma is below vMLX; Qwen vs vMLX not measured |
| "owlmlx achieves parity with vMLX" | prohibited | `public-surface.md` §10 |
| "owlmlx achieves parity with oMLX" | prohibited | `public-surface.md` §10 |
| "owlmlx beats oMLX" | prohibited | `BANNED_VERDICT_VOCABULARY`; `public-surface.md` §10 |
| "owlmlx beats vMLX" | prohibited | same |
| "owlmlx wins" | prohibited | same |

## 4. Model Support Claims

| Claim | Ruling | Evidence / source |
|---|---|---|
| "owlmlx has measured evidence for Qwen3.6-27B and Qwen3.6-35B-A3B" | allowed | `files/evidence/owlmlx/model-release-candidates/` |
| "owlmlx has measured evidence for Gemma 4" | allowed | same |
| "owlmlx returns a clean pre-load rejection for DeepSeek-V4 without dirtying runtime health" | allowed | `reference-runtime-comparison-matrix.md` §0 |
| "owlmlx supports DeepSeek" | prohibited | no measured generation; loader not supported |
| "owlmlx supports all MLX model families" | prohibited | coverage is selective |

## 5. Observability Claims

| Claim | Ruling | Evidence / source |
|---|---|---|
| "owlmlx ships a runtime-owned monitor surface (/v1/runtime/monitor/*)" | allowed | `public-surface.md` §3; `runtime-status-schema.md` |
| "owlmlx exposes a Prometheus-compatible /metrics endpoint" | allowed | `public-surface.md` §3 |
| "owlmlx's monitor surface is equivalent to a production observability stack" | prohibited | out of scope; developer preview only |

## 6. Serving Capability Claims

| Claim | Ruling | Evidence / source |
|---|---|---|
| "owlmlx exposes OpenAI-compatible /v1/chat/completions and /v1/completions endpoints" | allowed | `public-surface.md` §3.2 |
| "owlmlx exposes Anthropic-compatible /v1/messages endpoint" | allowed | `public-surface.md` §3.2 |
| "owlmlx uses a FIFO generation gate with ticketed admission" | allowed | `public-surface.md` §4 (`owlmlx.serving`) |
| "owlmlx has runtime-owned memory governance: pressure classification, eviction policy, non-resident admission" | allowed | `public-surface.md` §4; `memory-pressure-contract.md` |
| "owlmlx supports concurrent multi-user production workloads" | prohibited | no measured concurrent evidence; developer preview |
| "owlmlx supports multi-turn workloads at production quality" | prohibited | no measured multi-turn evidence |

## 7. Packaging and Distribution Claims

| Claim | Ruling | Evidence / source |
|---|---|---|
| "owlmlx can be installed via uv from a fresh clone" | allowed (scoped) | scope: developer workflow on Python 3.11.15 with the `runtime` extra |
| "owlmlx public release is gated by the OwlCoda npm package local-model learning loop" | allowed | `public-release-standard.md` |
| "OwlCoda's npm package has completed the owlmlx-backed self-training data and learning loop" | prohibited until proven | Requires the end-to-end proof in `public-release-standard.md` §3-§4 |
| "owlmlx is available as a Homebrew tap" | prohibited | not owned by this repo |
| "owlmlx ships as a macOS app" | prohibited | desktop shell not owned by runtime repo |
| "owlmlx has an end-user installer" | prohibited | packaging intentionally not owned |

## 8. Scope Qualification Templates

When a scoped claim appears in external copy, use one of these exact qualifications:

- Short-prompt performance: "measured on `max_tokens=64`, `temperature=0`, single-turn,
  same host (`Mac17,6-arm64-macOS-26.4.1-128GB`)"
- Developer workflow: "from a fresh clone via `uv sync --extra runtime` on Python 3.11.15"

Never omit the qualification. Never paraphrase it in a way that implies broader
generalization.

## 9. Update Rule

This document is updated when:

- a new measured evidence record changes the performance table in §3
- a new capability is added to `public-surface.md` that warrants a new allowed claim
- a claim category is added or a prohibition is lifted via honest evidence
- the `BANNED_VERDICT_VOCABULARY` changes in `owlmlx.comparative_evidence_schema`

Schedule pressure is not an update reason.
