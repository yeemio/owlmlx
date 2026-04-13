# owlmlx Phase 45 Round 24: Continuous-Batching Feasibility

## Goal

Advance the selected scheduler branch after `owlmlx.cache_scheduler_branch_selection`
has frozen `continuous_batching` as the next locally reducible scheduler path.

## Current frozen truth

- `owlmlx.cache_scheduler_branch_selection` is exact
- selected branch:
  - `continuous_batching`
  - `status = locally_reducible_on_current_path`
- secondary branch:
  - `multi_worker_scheduler_depth`
  - `status = safety_revalidation_required`
- the active queue policy is already explicit:
  - serial
  - ticketed FIFO
- heavy-weight repeatability remains externally blocked on this host

## This round must do

1. freeze whether continuous batching is only absent or whether there is an
   exact feasibility blocker on the current path
2. keep multi-worker depth secondary unless concurrency safety really changes
3. avoid inflating scheduler parity from queue-policy truth alone

## Minimum deliverables

- one narrow runtime-owned continuous-batching feasibility surface or equivalent exact freeze
- focused tests
- one live script run showing the selected branch truth
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim continuous batching exists unless runtime-owned proof actually moves
- do not reopen multi-worker depth unless concurrency safety is revalidated honestly
- do not drift back to specimen-first or shell-layer work
