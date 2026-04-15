# owlmlx Phase 45 Round 26: Request Aggregation Window Exactness

## Goal

Advance `cache_scheduler_depth` after the batching mechanism subgap is already
frozen exact.

## Current frozen truth

- `owlmlx.cache_batching_mechanism_subgap` is exact
- selected mechanism:
  - `request_aggregation_window`
- dependent mechanisms remain secondary:
  - `shared_prefill_batch_step`
  - `interleaved_decode_scheduler`

## This round must do

1. freeze whether `request_aggregation_window` is runtime-owned and locally
   implementable on the active path
2. distinguish:
   - exact missing ingress mechanism
   - exact child/session dependency that still blocks it
3. keep shared prefill and interleaved decode secondary unless runtime truth
   actually changes

## Minimum deliverables

- one narrow runtime-owned request-aggregation surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact request-aggregation result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim batching exists unless runtime-owned proof actually moves
- do not reopen multi-worker depth unless concurrency truth changes honestly
- do not drift back to shell/product work
