# owlmlx Phase 45 Round 7: Cache Closure Rung

## Goal

Advance `cache_scheduler_depth` from separate truth/evidence surfaces to one
runtime-owned closure rung that is still honest relative to `oMLX` / `vMLX`.

## Dominant Gap

`cache_scheduler_depth`

## Why This Round

`owlmlx` now has:

- `owlmlx.cache_scheduler_status`
- `owlmlx.cache_residency_evidence`
- `owlmlx.cache_repeatability_evidence`
- `owlmlx.turboquant_readiness`

It still lacks one stronger closure-level answer for:

- how far the runtime has actually progressed inside this gap
- what exact counter-level blocker still prevents a deeper claim

## Required Work

1. Add one runtime-owned cache closure surface that combines:
   - scheduler depth
   - cache profile visibility
   - residency/reuse evidence
   - repeatability evidence
   - TurboQuant readiness
2. Keep closure labels conservative:
   - `truth_only`
   - `evidence_visible`
   - `repeatability_visible`
   - `turboquant_safety_ready`
   - `partial_closure`
3. Freeze the exact blocker if direct runtime-owned reuse/eviction counters are
   still absent.
4. Add a focused test file, one operator script, and source-of-truth updates.

## Verification

- targeted pytest for the new closure surface plus adjacent cache tests
- one script smoke for the new closure surface
- updated goal/gap truth reflecting the next remaining blocker

## Hard Rules

- work only inside `owlmlx`
- do not overclaim cache parity
- do not fabricate runtime cache counters
- keep the result runtime-only and machine-readable
