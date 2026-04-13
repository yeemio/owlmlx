# owlmlx Phase 45 Round 9: Heavy-Weight Repeatability Status

## Goal

Advance `heavy_weight_runtime_repeatability` from a staging/specimen narrative
gap into a runtime-owned repeatability status with an exact host-aware blocker.

## Dominant Gap

`heavy_weight_runtime_repeatability`

## Why This Round

`owlmlx` now has:

- specimen completeness gate
- first-smoke locality decision
- host-stable execution status

It still lacks one runtime-owned answer for:

- whether heavy-weight repeatability is locally blocked, host-ready, or actually repeated
- whether the exact blocker is current-host baseline, missing supported host, or missing repeated proof

## Required Work

1. Add one runtime-owned heavy-weight repeatability surface that combines:
   - host stability
   - specimen gate / first-smoke decision
   - repeatability rung
2. Keep host truth strict; do not fake local success on the current blocked host.
3. Add one host-aware harness contract that can honestly return:
   - `local_blocked`
   - `host_ready_not_repeated`
   - `supported_host_repeatability_visible`
4. Freeze the exact external blocker if no supported host is available.

## Verification

- focused pytest for the new surface plus adjacent host/specimen tests
- one script smoke for the new repeatability surface
- source-of-truth update reflecting the next remaining blocker

## Hard Rules

- work only inside `owlmlx`
- do not overclaim heavy-weight serving proof on the current blocked host
- keep the result runtime-only and machine-readable
