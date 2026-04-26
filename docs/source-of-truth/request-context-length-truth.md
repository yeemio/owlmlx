# owlmlx Request Context-Length Truth

> Status: authoritative
> Updated: 2026-04-25
> Scope: runtime-only admission support for request context-length classification

## 1. Purpose

This document freezes a narrow runtime-owned answer for admission:

**Given a request's runtime-visible context token signal, is the request known
high-context, known non-high-context, or still unknown for admission purposes?**

This is not tokenizer parity.
It is not generation enforcement.
It exists so high-context-only recovery probing can affect only requests that
are actually known to be high-context.

## 2. Owned Contract

`owlmlx/request_context_length_truth.py` owns:

- `build_request_context_length_truth(...)`
- `request_context_length_truth_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/request-context-length-truth`

Contract:

- `surface = "owlmlx.request_context_length_truth"`
- `version = "v1"`

Stable sections:

- `summary`
- `classification`
- `thresholds`
- `source`
- `policy_boundaries`
- `missing_signals`

## 3. Current Inputs

The contract consumes only explicit runtime-visible request context signals:

- `context_tokens`
  - an explicitly supplied non-negative token count
- `request_context_class`
  - retained as source metadata only
  - not enough by itself to claim exact token accounting

It also consumes the already-owned serving-path concurrency truth from
`owlmlx/context_concurrency.py`:

- `HIGH_CONTEXT_THRESHOLD_TOKENS`
- `is_high_context(...)`
- `gate_entry_for_context(...)`
- `concurrency_gate_snapshot()`

It does not call a tokenizer.
It does not load a model.
It does not estimate tokens from characters or payload shape.

## 4. Classification Vocabulary

Current classification vocabulary:

- `high_context`
  - only when explicit `context_tokens` is greater than
    `HIGH_CONTEXT_THRESHOLD_TOKENS`
- `non_high_context`
  - only when explicit `context_tokens` is at or below
    `HIGH_CONTEXT_THRESHOLD_TOKENS`
- `unknown`
  - when trustworthy token-count truth is absent

Unknown context length must remain `unknown`.
It must not be narrated as short, safe, exact, or replacement-ready.

## 5. Admission Semantics

`scheduler_admission_contract` consumes this surface as an admission support
signal.

When `recovery_supervisor_contract` reports `probing`:

- known `high_context` requests defer with
  `recovery_probing_high_context_deferred`
- known `non_high_context` requests are not rejected or deferred solely because
  probing exists
- `unknown` context requests keep probing visible but non-global

Hard recovery barriers still reject before ordinary admission checks regardless
of context length.

## 6. What This Does Not Claim

It does not claim:

- full tokenizer parity
- prompt-shape or character-count token estimation
- generation-path enforcement
- failed unload/reclaim barrier events
- stream-hold counters or duration tracking
- continuous batching or multi-worker scheduling

It only claims:

- admission now owns a narrow context-length truth input
- recovery probing no longer needs to be a global non-decisive warning
- unknown context remains explicitly unknown
