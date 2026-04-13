# owlmlx Phase 45 Round 13: Governance Runtime Observations

## Goal

Advance `multi_model_lifecycle_governance` from harness-fed transition evidence
to narrower runtime-owned observations.

## Dominant Gap

`multi_model_lifecycle_governance`

## Why This Round

`owlmlx` now has:

- governance status
- governance controls
- governance transition ledger

But the strongest governance signals still come from harness-fed evidence.

The next reduction step is not to invent policy; it is to make a small slice of
transition observations runtime-owned on the active kernel path.

## Required Work

1. add narrow runtime-owned governance observations where `owlmlx` already owns
   lifecycle transitions
2. keep observations lightweight:
   - transition count
   - active-model reassignment visibility
   - restart-restore visibility
3. do not invent TTL, pinning, or eviction policy

## Verification

- focused pytest for the observation surface plus adjacent governance/kernel tests
- one script smoke for the runtime-owned observations
- source-of-truth update reflecting what is now observed directly versus still
  harness-only

## Hard Rules

- work only inside `owlmlx`
- do not inflate customer readiness
- do not rename observations into lifecycle policy
