# Coordinator Checkpoint: owlmlx Public Developer Preview Ready

**Goal:** `owlmlx-public-developer-preview-readiness`
**Closed:** 2026-05-10
**Operator:** owlcoda

## What Was Done

1. **`docs/source-of-truth/public-developer-preview-readiness.md`** (new) —
   Anchors the developer-preview position: all 7 release floors closed,
   measured Qwen/Gemma performance evidence, honest open gaps, can/cannot claim
   lists, intended external audience. Single canonical entry point for the
   developer-preview label.

2. **`README.md`** (updated) —
   First screen now communicates developer-preview label in the opening
   paragraph. Current State section replaced with accurate description of real
   runtime capabilities. Performance evidence table added. Obsolete
   "source-of-truth repository, not yet code-heavy" language removed. Document
   Map reorganized into functional groups with developer-preview entry points
   first. Immediate Priority updated to reflect post-floor-closure state.

3. **`docs/source-of-truth/public-claim-matrix.md`** (new) —
   Machine-readable table of allowed, allowed (scoped), and prohibited claims
   across identity, performance, model support, observability, serving
   capability, and packaging dimensions. Each entry has a ruling and an
   evidence pointer. Scope qualification templates provided.

4. **`docs/source-of-truth/public-export-allowlist.md`** (new) —
   Defines what is safe to export to a public repository as-is, what requires
   sanitization, and what must not be exported. Covers evidence JSONL
   `artifact_path` fields, internal docs, phase45 artifacts, and the
   comparison matrix private paths. Includes a pre-export checklist.

5. **`docs/source-of-truth/reference-runtime-comparison-matrix.md`** (updated)
   — Sanitized §2 private absolute paths to `<runtime-probes repo>/...`
   placeholders. All factual content (TPS numbers, verdicts) preserved.

## Honest Position Stated

`owlmlx` is a self-owned Apple Silicon MLX runtime in developer preview.
Measured short-prompt Qwen evidence: 5.45 TPS vs oMLX 2.81 (Qwen27B); 3.53 vs
2.44 (Qwen35B-A3B). Gemma close to but below vMLX (3.75 vs 3.83). All seven
release floors closed 2026-04-28. Public surface frozen at v1.

Not production-ready. Not parity. Not a replacement. Open gaps (heavy-weight
repeatability, scheduler depth, multi-turn evidence) are stated, not hidden.

## What Was Not Done

- Evidence JSONL `artifact_path` fields still contain local model paths. A
  pre-export sanitization pass is required before pushing to a public remote.
  See `public-export-allowlist.md` §3.2 and the scan command there.
- Docs outside `public-surface.md` §6 that contain incidental private paths
  are not sanitized. They are internal and can be excluded from public export.
- No code changes were made. This goal was documentation-only.

## Durable References

- `docs/source-of-truth/public-developer-preview-readiness.md`
- `docs/source-of-truth/public-claim-matrix.md`
- `docs/source-of-truth/public-export-allowlist.md`
- `docs/source-of-truth/public-surface.md` (pre-existing)
- `docs/source-of-truth/release-readiness-backlog.md` (pre-existing, 7/7 closed)
