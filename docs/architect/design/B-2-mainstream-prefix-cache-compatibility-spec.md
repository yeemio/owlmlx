# B-2 Mainstream Prefix-Cache Compatibility Spec

> Status: design-grade spec; B-2.1 classifier and B-2.2 metadata plumbing landed; B-2.3 blocked on B-1c section 2 fast-swap drift triage
> Updated: 2026-06-01
> Campaign: B-2
> Parent goal:
> `files/goals/owlmlx/mainstream-prefix-cache-compatibility-closure-goal-contract.md`

## 1. Purpose

B-2 closes the gap between OwlMLX's current experimental session KV cache and
the behavior mainstream OpenAI / Anthropic compatibility consumers expect from a
runtime-owned prefix-cache lane.

The current explicit session header is useful as a dogfood/control path. It is
not the target contract. OwlCoda, Codex, and other OpenAI-compatible clients
should not need to learn an OwlMLX-private header to benefit from safe
prefix-cache behavior.

This spec freezes the B-2 design before any automatic reuse implementation.
The first code-grade slice must be classifier/diagnostic-only. It may prove
that a request is eligible for future prefix reuse; it must not reuse a cache
object automatically.

## 2. Current Truth

Current verified truth:

- Explicit session KV cache exists.
- It is `experimental`, default-off, native-backend only, and enabled by
  `OWLMLX_SESSION_CACHE_ENABLED=1`.
- The explicit lane requires `X-Owlmlx-Session-Id`.
- Native streaming can reuse an explicit `(session_id, model_id)` prompt cache.
- Non-stream `generate` still uses a fresh single-request cache.
- `/v1/runtime/session-kv-cache` is the diagnostic status surface.
- B-2.2 now maps OpenAI `prompt_tokens_details.cached_tokens` and Anthropic
  `cache_read_input_tokens` only when backend event/result detail carries real
  `session_kv_cache.cached_prompt_tokens` metadata for the current request.
- B-1c section 2 remains aggregate-blocked: a short clean forced-swap canary can
  validate unload / settle / load boundaries, but it is not a 24h/6-swap pass.
- The operator-paused `20260601T074541Z` topoff is not aggregate input: its
  partial ledger reached about 2h18m with zero drops / expirations / rejects,
  but `swap_count=0` and no rollup exists. It cannot unlock B-2.3 because the
  required unload / settle / load boundary was not exercised.
- Correction: when the question is whether the swap boundary itself is clean,
  the right next step is a short forced-swap canary with high-frequency swaps
  such as one swap every 5 minutes, not another passive 4h wait.
- The `20260601T125751Z` 20-minute / 4-swap forced canary exercised a
  5-minute swap cadence and found the real blocker: all four swap boundaries
  were clean and session-cache drops / expirations / rejects stayed zero, but
  the segment failed because `max_drift_bytes=46801784452` and
  `max_unaccounted_session_kv_drift_bytes=45745465112`, with the max-drift
  record on Gemma at sample 61. This is a fast-swap drift triage blocker, not a
  consumer-header problem.

## 3. Design Goal

B-2 defines an OwlMLX-owned mainstream compatibility lane with these end-state
properties:

1. A caller using ordinary OpenAI / Anthropic compatibility payloads can receive
   safe prefix-cache behavior without supplying `X-Owlmlx-Session-Id`.
2. Automatic reuse is considered only when OwlMLX can prove token-prefix
   equivalence for the same model, tokenizer, runtime profile, template
   boundary, and isolation policy.
3. Cache usage is visible through compatibility payloads only when the runtime
   has real cache-hit accounting for that request.
4. The explicit session header remains an experimental control lane, not a
   supported mainstream consumer contract.

## 4. Non-Goals

B-2 does not implement or promise:

- paged KV;
- continuous batching;
- cross-user shared prefix reuse;
- subprocess cache-handle transport;
- non-stream cache reuse before the native path can report real cache metadata;
- default-on cache behavior;
- B-1 promotion to `supported`;
- OwlCoda product integration work.

## 5. Staged Gates

### 5.1 B-2.0 Source-Of-Truth And Contract Freeze

Scope:

- Correct stale source-of-truth rows that deny the existing explicit session
  cache lane.
- Archive the goal contract and design-grade spec.
- Record that mainstream compatibility is OwlMLX-owned.

Pass:

- `native-mlx-backend-capability-matrix.md` distinguishes explicit
  session-scoped reuse (`experimental`) from mainstream implicit prefix reuse
  (not implemented).
- `public-surface.md` distinguishes the experimental diagnostic route from
  compatibility usage fields that remain absent.
- `01-mainline-roadmap.md` introduces B-2 as a near-term Campaign B goal, while
  keeping B-1c section 2 separate.

### 5.2 B-2.1 Prefix-Candidate Classifier

Scope:

- Add a read-only classifier that accepts:
  - `model_id`;
  - tokenized prompt;
  - tokenizer/runtime profile identity;
  - chat-template/profile boundary identity;
  - isolation scope.
- Return `eligible` / `ineligible` plus reason.
- Do not return, clone, mutate, trim, or reuse a cache object.

Required reasons:

| Reason | Meaning |
|---|---|
| `same_model_token_prefix` | Same model/runtime profile and exact token-prefix relation proven. |
| `different_model` | Model identity differs. |
| `different_runtime_profile` | Tokenizer/template/runtime profile differs. |
| `not_token_prefix` | Prompt tokens do not form a prefix relation. |
| `unsafe_isolation_scope` | Reuse would cross the configured isolation boundary. |
| `trim_unavailable_for_edit` | The request needs edited-prefix reuse but trim support is unavailable. |

Pass:

- The classifier can prove same-token-prefix eligibility.
- It rejects different models and runtime profiles.
- It rejects tokenizer/template boundary mismatches.
- It rejects unsafe isolation.
- It emits stable reason codes.
- Tests prove no cache handle is reused and no reuse claim is emitted.

### 5.3 B-2.2 Real Cache Metadata Plumbing

Status: landed on 2026-06-01.

Scope:

- Thread runtime cache decision metadata through existing result/event types.
- Expose cached-token counts to compatibility payloads only when produced by
  the runtime for the current request.

Target OpenAI shape:

```json
{
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 10,
    "total_tokens": 110,
    "prompt_tokens_details": {
      "cached_tokens": 64
    }
  }
}
```

Target Anthropic shape:

```json
{
  "usage": {
    "input_tokens": 100,
    "output_tokens": 10,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 64
  }
}
```

Pass:

- Cached-token fields are absent or zero when the runtime reports no hit.
- Cached-token fields are positive only when the runtime reports a real hit.
- Tests prevent fabricated cache counts.

### 5.4 B-2.3 Automatic Safe Reuse

Scope:

- May start only after B-2.1 and B-2.2 pass and after B-1c section 2 provides
  sufficient aggregate stability for real cache-handle reuse.
- Uses the classifier as an admission gate.
- Reuses a cache only under proven prefix equivalence and configured isolation.

Pass:

- B-1c section 2 aggregate is passed or this stage remains blocked.
- Reuse is opt-in or guarded behind a clearly named runtime flag.
- It does not merge unrelated conversations.
- It emits real cache metadata.

## 6. Safety Contract

Automatic prefix reuse must be rejected unless all of these are true:

1. same `model_id`;
2. same tokenizer identity;
3. same chat-template/runtime profile identity;
4. same cache implementation/version identity;
5. exact token-prefix relation;
6. compatible isolation scope;
7. cache object supports the needed operation:
   - append-only exact-prefix reuse; or
   - safe trim for edited-prefix reuse.

If any check is unknown, the classifier returns `ineligible`. Unknown must not be
treated as eligible.

## 7. Consumer Boundary

`X-Owlmlx-Session-Id` remains:

- allowed for dogfood and diagnosis;
- useful for explicit native session experiments;
- visible in `/v1/runtime/session-kv-cache`.

It is not:

- the target mainstream consumer contract;
- something OwlCoda must hard-code to get normal prefix-cache behavior;
- evidence of OpenAI / Anthropic compatible cache usage by itself.

## 8. Implementation Constraints

- No new `*_contract.py`, `*_harness.py`, `*_evidence.py`, `*_ledger.py`, or
  other banned spec-as-code modules under `owlmlx/`.
- Prefer extending existing runtime modules when a runtime consumer will read
  the fields/functions.
- Classifier-only code may live in the existing cache/runtime area only if
  production runtime code calls it.
- Design and source-of-truth documents must not be imported by runtime code.

## 9. Test Plan

B-2.1 tests:

- same token-prefix candidate accepted;
- different model rejected;
- different runtime profile rejected;
- tokenizer/template boundary mismatch rejected;
- unsafe isolation rejected;
- trim-unavailable edited-prefix request rejected;
- no cache object reused;
- no compatibility usage count emitted.

B-2.2 tests:

- OpenAI non-stream usage remains unchanged when no cache metadata exists;
- OpenAI usage includes `prompt_tokens_details.cached_tokens` when a real hit is
  reported;
- Anthropic usage uses real `cache_read_input_tokens`;
- streaming final usage never fabricates cached-token counts.

B-2.3 tests:

- automatic reuse remains disabled until the configured flag/gate is enabled;
- enabled path reuses only eligible prefix candidates;
- ineligible cases fall back to fresh cache and emit an ineligible reason;
- runtime status counters match compatibility usage counters.

## 10. Evidence Paths

Expected future evidence root:

`files/evidence/owlmlx/bench/prefix-cache-compatibility/`

Expected row families:

- `b2.prefix_candidate_classifier.v1`
- `b2.compat_usage_accounting.v1`
- `b2.automatic_prefix_reuse.v1`

No evidence file in this design round promotes the capability.

## 11. Promotion Ceiling

After B-2.0:

- explicit session KV remains `experimental`;
- mainstream automatic prefix cache remains not implemented;
- compatibility cache usage remains absent.

After B-2.1:

- OwlMLX may claim classifier-level eligibility diagnostics only.

After B-2.2:

- OwlMLX may claim compatibility-visible cache accounting only for runtime paths
  that report real cached-token counts. It must not claim automatic safe prefix
  reuse or infer per-request counts from aggregate status counters.

After B-2.3:

- OwlMLX may claim a narrow automatic prefix-cache lane only if B-1c section 2
  aggregate stability and B-2 evidence both pass.

No stage in this spec independently promotes B-1 to `supported`.

## 12. Next Handoff

The next round is not B-2.3 code-grade yet. B-2.3 is blocked until B-1c
section 2 resolves the fast-swap drift blocker and then provides sufficient
aggregate stability for real cache-handle reuse.

Immediate handoff:

1. Triage the `20260601T125751Z` fast-swap drift failure before any longer
   aggregate run. The boundary was clean; the blocker is the 46.8GB active
   memory drift under 5-minute swap cadence.
2. Determine whether the drift is accounting/baseline error around large-model
   load, real allocator leak, or prompt/session-cache resident accounting gap.
3. Keep the 5-minute forced-swap canary as the boundary-stress shape until the
   drift root cause is closed.
4. Treat forced canaries as boundary diagnostics only, not as 24h/6-swap
   aggregate promotion evidence.
5. Aggregate only completed segments with `measurement_wall_clock_gap_free=true`
   and clean
   cache/drop/swap-boundary audit results.
6. Keep automatic prefix reuse disabled and unimplemented.
7. Do not treat partial measurement-only ledgers as B-1c section 2 aggregate
   input. The segment must reach its planned swap boundary and produce a rollup.
8. Refresh this spec only when B-1c section 2 either passes the aggregate gate
   or produces a new blocker that changes B-2.3 feasibility.

When the prerequisite is met, the first B-2.3 code-grade round may wire
classifier-gated automatic reuse behind an explicit runtime flag. That future
round must prove ineligible requests fall back to fresh cache and that
compatibility usage counters match real per-request runtime metadata.

## 13. Change Log

- 2026-06-01: Initial design-grade spec for B-2 mainstream prefix-cache
  compatibility closure.
- 2026-06-01: B-2.1 read-only prefix-candidate classifier landed with focused
  tests; automatic reuse and cached-token usage fields remain future stages.
- 2026-06-01: B-2.2 real cache metadata plumbing landed. Native stream events
  carry per-request `session_kv_cache.cached_prompt_tokens`, and
  OpenAI/Anthropic compatibility usage maps that field only when present.
- 2026-06-01: Updated next handoff after B-2.1/B-2.2 landed. B-2.3 automatic
  reuse remains blocked on B-1c section 2 aggregate stability, so the dominant
  execution path returns to clean gap-free prompt-reset swap segments.
- 2026-06-01: Recorded operator-paused `20260601T074541Z` topoff as partial
  diagnostic evidence only. It was cache-clean through `8298.33s`, but had
  `swap_count=0` and no segment rollup, so it does not change the B-2.3 blocker.
- 2026-06-01: Corrected the next executable step: for swap-boundary mechanics,
  use a short forced-swap canary with a 5-minute swap cadence instead of
  passively waiting for another 4h segment.
- 2026-06-01: Recorded `20260601T125751Z` 20-minute / 4-swap forced canary.
  It proved swap boundaries can be clean under 5-minute cadence, but failed on
  `max_drift_bytes=46801784452`; B-2.3 is therefore blocked on fast-swap drift
  triage, not on another passive soak duration.
