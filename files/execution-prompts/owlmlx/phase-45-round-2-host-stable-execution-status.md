# owlmlx Phase 45 Round 2: Host-Stable Execution Status

> Status: archived execution prompt
> Updated: 2026-04-13

## Goal

Execute the next round of
`owlmlx-replacement-grade-stability-alignment`.

## Dominant Gap

`host_stable_execution`

`owlmlx` already has:

- MLX environment readiness
- blocker report
- host forensics
- first-smoke locality decision

But those assets still answer narrower questions. The repo still lacks one
host-level contract that says whether a machine is even a valid candidate for
replacement-grade runtime validation.

## Required Outcome

Create one runtime-owned host-stability contract that:

1. is not specimen-specific
2. summarizes default-Metal and force-CPU readiness
3. incorporates host crash forensics
4. outputs one honest status for the current host
5. recommends the next execution class:
   - local runtime validation
   - local forensics
   - move-host handoff

## Hard Rules

1. Stay inside `owlmlx`.
2. Do not add shell/UI/control-plane work.
3. Do not reopen MiniMax as the top-level goal.
4. Keep the contract host-level, not specimen-level.
5. Do not claim stable execution exists if no verified-safe baseline exists.

## Verification

At minimum:

- new runtime tests for the host-stability contract
- existing readiness/forensics tests still pass
- one operator-facing script emits the new host status contract

## Honest End State

Good:

- `owlmlx` can now answer whether a host is a candidate for replacement-grade
  validation

Bad:

- still requiring the reader to combine readiness + forensics + specimen
  scripts manually

