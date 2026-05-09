# owlmlx Phase 45: Current-Host Heavy Boundary Budget Blocker

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only exact blocker for the current-host selected heavy boundary

## 1. Purpose

This document freezes one narrow truth:

**Why did the first real heavy boundary check on the current host fail, even
though host-stable execution and selected specimen completeness were both
green?**

The purpose is to keep this blocker from being diluted into:

- stale download residue
- vague “heavy-weight still blocked”
- generic host instability
- another excuse to reopen cache/governance work

## 2. Exact Current Result

On the current host:

- `host_stable_execution` is green
- the selected supported candidate baseline exists
- the selected heavy specimen path is complete:
  - `/Users/yeemio/AI/Agent/models/Kimi-K2.5-3bit`
- the first heavy boundary check is **not** green

The exact blocker is:

- `memory_budget_exceeded`

Exact current expression:

- `122.0G requested > 116.0G limit`

Runtime-owned reason:

- `loading 122.0G would exceed serving budget: 0.0G loaded + 122.0G requested = 122.0G > 116.0G limit`

## 3. What This Blocker Is

This blocker is:

- runtime-owned
- exact
- preconditions-grade
- specific to the selected heavy boundary on the current host

It means:

- the current host can validate runtime baseline truth
- but the currently selected Kimi heavy boundary does not fit inside the
  present serving budget

## 4. What This Blocker Is Not

This blocker is **not**:

- a stale `.aria2` root-directory issue
- a specimen completeness issue
- a default-registry readiness issue
- a host-stable execution failure
- proof that the current host is useless
- proof that heavy-weight repeatability is restored

The root models directory may still contain unrelated `.aria2` residue, but
that is no longer the active truth for this round.

## 5. Current Truth Implications

Because this blocker is exact:

- `heavy_weight_runtime_repeatability` remains
  `local_preconditions_incomplete`
- `customer_runtime_evidence` remains `early_formal_runtime`
- `dominant_next_gap` remains `host_stable_execution`

What does **not** become honest:

- `host_ready_not_repeated`
- `supported_host_repeatability_visible`
- replacement-grade closure

## 6. Allowed Next Moves

From this blocker, only two honest next moves exist:

1. **Retarget the heavy boundary to something that fits the current host budget**
   - keep the current host as supported candidate baseline
   - keep cache/governance frozen
   - do not pretend the current Kimi boundary already entered

2. **Freeze here**
   - accept `boundary_check_still_preconditions_blocked`
   - wait for another host/budget/target condition

## 7. Forbidden Misreads

Do not rewrite this blocker as:

- “the host is blocked again”
- “the selected specimen is incomplete”
- “cache must reopen”
- “governance must reopen”
- “heavy-weight repeatability almost works”

## 8. Honest Summary

The current host has progressed far enough to support stronger runtime
validation.

The selected Kimi heavy boundary has **not** progressed far enough to enter
that heavier path on this host, because its required serving budget exceeds the
current limit exactly.
