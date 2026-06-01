# OwlMLX B-2 Code-Grade Prompt: Prefix-Candidate Classifier

> Created: 2026-06-01
> Goal: `owlmlx-mainstream-prefix-cache-compatibility-closure`
> Parent spec:
> `docs/architect/design/B-2-mainstream-prefix-cache-compatibility-spec.md`

## Mission

Implement **B-2.1 only**: a read-only prefix-candidate classifier for future
mainstream prefix-cache compatibility.

The classifier may decide whether a request is eligible for future automatic
prefix reuse. It must not reuse, clone, trim, mutate, or return a cache object.

## Required First Reads

1. `AGENTS.md`
2. `files/goals/owlmlx/mainstream-prefix-cache-compatibility-closure-goal-contract.md`
3. `docs/architect/design/B-2-mainstream-prefix-cache-compatibility-spec.md`
4. `docs/source-of-truth/session-kv-cache-experimental.md`
5. `owlmlx/session_kv_cache.py`
6. `owlmlx/runtime/mlx_native_backend.py`
7. `tests/test_session_kv_cache.py`
8. `tests/test_mlx_native_backend_session_kv_cache.py`

## Hard Rules

1. Do not implement automatic cache-handle reuse.
2. Do not require OwlCoda/Codex to send `X-Owlmlx-Session-Id` as the mainstream
   contract.
3. Do not add cached-token usage fields unless real runtime metadata is
   produced in this same round.
4. Do not create banned spec-as-code modules (`*_contract.py`, `*_harness.py`,
   `*_evidence.py`, `*_ledger.py`, etc.).
5. Leave unrelated dirty files untouched.
6. Keep capability labels honest; no `supported` promotion.

## Required Behavior

The classifier returns:

- `eligible: bool`
- `reason_code: str`
- optional diagnostic details that do not include cache objects

Required reason codes:

- `same_model_token_prefix`
- `different_model`
- `different_runtime_profile`
- `not_token_prefix`
- `unsafe_isolation_scope`
- `trim_unavailable_for_edit`

## Required Tests

Add focused tests proving:

1. same-token-prefix candidate is eligible;
2. different model is rejected;
3. different runtime profile is rejected;
4. tokenizer/template boundary mismatch is rejected;
5. unsafe isolation is rejected;
6. edited-prefix reuse with unavailable trim is rejected;
7. the classifier does not reuse or return a cache handle;
8. no OpenAI/Anthropic cached-token usage field is emitted by this slice.

## Suggested Verification

```bash
uv run pytest tests/test_session_kv_cache.py tests/test_mlx_native_backend_session_kv_cache.py tests/test_runtime_session_kv_cache_route.py -q
```

Add narrower tests as needed for the classifier.

## Expected Outcome

The round should end with a classifier-level diagnostic capability only. The
mainstream automatic prefix-cache lane remains unimplemented until B-2.2/B-2.3
and the B-1c section-2 aggregate gate are satisfied.
