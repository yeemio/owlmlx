# Imported Kimi Crash Safe-Resume Gate

Imported from:
`/Users/yeemio/AI/Agent/files/verification-assets/phase-42/kimi-crash-safe-resume-gate.md`

Import date: 2026-04-09
Purpose: preserve the first concrete safe-resume contract instance inside
`owlmlx` ownership history.

## Key Runtime-Governance Facts

- Full BF16 attention recovery was blocked pending safe-resume gate.
- Forbidden actions included full 61-layer load validation and unguarded heavy
  Python/MLX jobs.
- Minimum allowed resume scope was single-layer, serial, plan-first,
  abort-on-threshold.
- Required guardrails included dry-run support, explicit per-layer targeting,
  memory thresholds, progress logs, and failure as a formal outcome.
- This artifact is a copied historical instance, not the primary living
  governance definition. The authoritative principles now live in:
  - `docs/source-of-truth/runtime-governance.md`
  - `docs/source-of-truth/hazardous-operations.md`
