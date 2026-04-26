# owlmlx Phase 45: Cache Pre-Gate Admission-Window Seam

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only post-structural cache exactness on the active path

## 1. Purpose

Freeze the next exact cache blocker after:

- `owlmlx.cache_structural_ingress_seam` is already live on the runtime path
- `cache_scheduler_depth` has been reauthorized as the dominant gap
- request aggregation remains the active cache subchain

## 2. Owned Contract

`owlmlx/cache_pre_gate_admission_window_seam.py` now owns:

- `build_cache_pre_gate_admission_window_seam(...)`
- `cache_pre_gate_admission_window_seam_to_dict(...)`

Operator entry:

- `scripts/runtime_customer_runtime_evidence.py`

Contract:

- `surface = "owlmlx.cache_pre_gate_admission_window_seam"`
- `version = "phase45"`

Stable sections:

- `summary`
- `selected_seam`
- `preserved_secondary_dependencies`
- `preserved_secondary_runtime_branch`

## 3. Current Honest Result

The current preserved checkpoint remains:

- `summary.seam_rung = "pre_gate_admission_window_seam_exact"`
- `selected_seam.seam = "bounded_pre_gate_admission_hook"`
- `selected_seam.status = "bounded_hook_present_but_no_request_aggregation_window"`

Preserved secondary truth remains:

- `single_request_per_child_exchange_blocks_aggregated_dispatch`
- `stream_session_holds_gate_until_completion`
- `turboquant_preconditions = preconditions_exact`

## 4. What This Changes

Before this round, active cache truth could stop at:

- `owlmlx.cache_structural_ingress_seam`
- `closure_level = structural_ingress_seam_introduced`

That checkpoint remains true, but it is no longer the active cache blocker.

It now serves as the preserved ingress checkpoint that enabled the next
authorized widening.

Current live truth has already moved beyond it:

- a bounded pre-gate admission window now forms cohorts before whole-request
  gate claim
- the active cache surface has advanced to
  `owlmlx.cache_request_aggregation_active_seam`
- the next blocker is now downstream of this seam

## 5. What This Does Not Claim

It does not claim:

- request aggregation support
- continuous batching support
- aggregated child dispatch
- stream-path rewrite
- cache parity

It only preserves the exact seam that existed immediately before the window
widening round.

## 6. Next Closure Step

The next step is no longer authorization for ingress-window work.

That authorization has already been consumed.

The next coordinator choice now lives downstream of this preserved checkpoint.
