# owlmlx Phase 45 Round 8: Multi-Model Governance Status

## Goal

Advance `multi_model_lifecycle_governance` from a narrative replacement-grade
gap into a runtime-owned contract with runnable verification.

## Dominant Gap

`multi_model_lifecycle_governance`

## Why This Round

`owlmlx` now has:

- inventory truth
- budget truth
- load/unload/restart semantics
- restartability truth

It still lacks one runtime-owned answer for:

- resident model count
- active/default model semantics
- unload/restart safety as a governance surface
- whether pinning/TTL/eviction history genuinely exist

## Required Work

1. Add one runtime-owned governance status surface that combines:
   - inventory truth
   - budget truth
   - load/unload/restart semantics
   - active/default model semantics
2. Expose honest fields for:
   - resident model count
   - active/default behavior
   - restart/unload safety
   - pinning support
   - TTL support
   - eviction history visibility
3. Add one repeated multi-model harness:
   - load A
   - load B
   - switch/generate
   - unload
   - restart
   - verify governance truth remains honest
4. Freeze the closure level conservatively.

## Verification

- focused pytest for the new governance surface plus adjacent runtime tests
- one script smoke for the governance surface
- source-of-truth update reflecting the next remaining blocker

## Hard Rules

- work only inside `owlmlx`
- do not invent pinning or TTL if they are not implemented
- keep the result runtime-only and machine-readable
