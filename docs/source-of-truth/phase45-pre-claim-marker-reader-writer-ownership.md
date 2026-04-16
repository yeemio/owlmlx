# owlmlx Phase 45: Pre-Claim Marker Reader/Writer Ownership

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only pre-claim marker reader/writer ownership

## 1. Purpose

Freeze the exact reader/writer ownership boundary for inert pre-claim markers
once marker trigger inputs are already exact.

## 2. Owned Contract

`owlmlx/cache_pre_claim_marker_reader_writer_ownership.py` now owns:

- `build_cache_pre_claim_marker_reader_writer_ownership(...)`
- `cache_pre_claim_marker_reader_writer_ownership_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_marker_reader_writer_ownership.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_marker_reader_writer_ownership"`
- `version = "phase45"`

Stable sections:

- `summary`
- `reader_writer_boundary`
- `forbidden_writer_expansions`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = reader_writer_ownership_exact`

The reader/writer boundary is:

- `writer_ownership_status = writer_paths_limited_to_explicit_pre_claim_drop_cancel_and_gate_claim_expiry`
- `reader_ownership_status = reader_paths_limited_to_writer_paths_plus_pre_claim_discard_observation`
- `allowed_writer_paths = ["explicit_pre_claim_drop_cancel_writer", "gate_claim_expiry_writer"]`
- `allowed_reader_only_paths = ["pre_claim_discard_observer"]`

The forbidden writer expansions are:

- `no_scheduler_writer_before_claim`
- `no_child_backend_writer_before_claim`
- `no_stream_writer_before_claim`
- `no_execution_priority_writer_before_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- trigger inputs were exact
- marker visibility was exact

Now it can say something narrower:

- marker writer ownership is exact
- marker reader-only paths are exact
- the remaining question is now marker state-carrier exactness, not generic
  reader/writer ownership

## 5. What This Does Not Claim

It does not claim:

- scheduler may author a marker
- child/backend or stream paths may author a marker
- writer ownership may create hidden queue ownership

It only freezes the reader/writer boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze marker state-carrier exactness:

- what inert state carrier holds a marker before gate claim
- which carrier semantics remain absent
- what still must remain unavailable until whole-request gate claim
