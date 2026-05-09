# owlmlx Coordinator Checkpoint — Native MLX Backend Capability Matrix Promotion from B-1 Evidence (B-1.1)

## Verdict

- `native_mlx_backend_capability_matrix_promoted_4_rows_experimental_to_partial`

Four native rows advance from `experimental` to `partial` under the
Promotion Gate (§1a). Nine other rows are explicitly reviewed and
declined promotion in this round, with stated reason for each. No row
reaches `supported`.

## What This Checkpoint Is

The redirected main line's fifth round and the **first round to advance
capability matrix row state** under the §1a Promotion Gate. This round
is doc-only: zero runtime change, zero new tests, zero environment
change, zero model operation. Its product is row-state advancement
backed by B-1's declared-provenance real-candidate evidence.

## What Is Now Frozen Exact

### Capability matrix changes

`docs/source-of-truth/native-mlx-backend-capability-matrix.md` §3:

| Row | Native column | Subprocess column |
|---|---|---|
| In-process model handle | `experimental` → **`partial`** | unchanged (`not_in_scope`) |
| In-process tokenizer handle | `experimental` → **`partial`** | unchanged (`not_in_scope`) |
| Token-level `decode_step` iterator | `experimental` → **`partial`** | unchanged (`not_in_scope`) |
| Per-step finish-reason inspection | `experimental` → **`partial`** | unchanged (`partial`) |

Each row's Notes column was minimally extended with the B-1 evidence
reference and the B-1.2 cap statement. No row's pre-existing description
was deleted.

A new §3b "Promotion-Gate-Compliant Promotions (B-1.1 Round)" was added
between §3a and §4, recording the §1a four-gate walkthrough for each of
the four promoted rows and listing nine other rows that were reviewed
and **declined** promotion this round, with reason per row.

### Files modified

- `docs/source-of-truth/native-mlx-backend-capability-matrix.md` —
  §3 four-row update + §3b new section

### Files added (round-scope only)

- `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-capability-matrix-promotion-from-b1-evidence.md`
  (this round's prompt)
- `files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-capability-matrix-promotion-from-b1-evidence.md`
  (this checkpoint)

## Provenance Cited (per §1a gate 2)

- candidate row: `Qwen3.6-35B-A3B` in
  `native-mlx-backend-local-candidate-admissibility.md` §3 (verdict
  `admissible`, B-1, 2026-05-08)
- upstream HF repo: `Qwen/Qwen3.6-35B-A3B`
- upstream commit SHA: `53c43178507d69762986fbfa314f6e8d4d859409`
- mlx_lm version of admission: 0.31.2
- evidence checkpoint:
  `coordinator-checkpoint-native-mlx-backend-local-candidate-real-load-admissible.md`

## §1a Gate Walkthrough Summary

For all four promoted rows, the four gate conditions are satisfied:

1. **gate 1** (admissibility row cited): satisfied — same Qwen3.6-35B-A3B
   row, `admissible`
2. **gate 2** (provenance recorded in checkpoint): satisfied — HF commit
   SHA cited above
3. **gate 3** (Notes column updated with load+lifecycle evidence):
   satisfied — each row's Notes column extended with the specific B-1
   observation that supports it (model class, tokenizer wrapper, 8-chunk
   stream, finish_reason field presence)
4. **gate 4** (no runtime-indistinguishable quantization subclass):
   satisfied — candidate is bf16, no quantization block; no DWQ vs
   affine 4bit confusion possible

## Rows Reviewed and Declined Promotion in B-1.1

Recorded in §3b for audit. Summary:

- **KV cache handle**: stays `partial`. Promotion to `supported` requires
  adapter-side `_make_fresh_prompt_cache` to fire under real load —
  the B-1 smoke bypassed the adapter (ran directly against `mlx_lm`).
  This is the B-1.2 cap
- **Sampler injection / Speculative drafter / Logits hook / Prefill-decode
  separation / Cooperative cancellation / Scheduler admission**: each
  has stated reason (no new evidence in B-1)
- **In-process model residency / pinning**: model living in session is
  incidental, not a standalone capability claim
- **Structured output / multi-stream / KV reuse**: stay `not_in_scope`,
  no relevant evidence

## What This Checkpoint Closes

- the first official capability matrix promotion round under the §1a
  Promotion Gate
- the gap between "we have admissibility evidence" (B-1) and "the matrix
  reflects it" (B-1.1)
- the audit-trail expectation that promotions be walkable row-by-row
  against §1a (the §3b section is now the template for future
  promotions)

## What This Checkpoint Does Not Claim

- no row reaches `supported`. The B-1.2 cap is real — adapter-routed
  evidence has not been produced
- no native adapter binding was tested in this round
- no model was loaded / streamed / unloaded
- no environment file changed
- no `pyproject.toml` / `uv.lock` / `.python-version` / `conftest.py`
  modification
- no Promotion Gate clause itself was modified
- no admissibility doc edit (B-1's writes already cover the candidate)
- the four declined promotion rows are not declared "broken" — only
  "without evidence in this round"

## Test Counts (No Change)

This round did not modify any code under test and did not add tests.
Last known counts persist (94 passed + 3 skipped on the focused MLX
native adapter set, per the B-1 checkpoint).

## Current Frozen Active Seam (No Change)

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

## Notable Implementation Choices

1. **Notes columns extended, not rewritten.** Each promoted row's prior
   description (subprocess vs native asymmetry, fake-test reference)
   stays. The B-1 evidence is appended as a discrete sentence — the
   row's history is preserved in-place, not deleted
2. **§3b added between §3a and §4, not at the end.** §3a is the
   per-test-evidence section (fake `mlx_lm` rounds); §3b is the
   per-promotion-gate-walkthrough section. Putting them adjacent makes
   the evidence-then-promotion ordering visible in the document
3. **Decline list explicit, not implicit.** Future readers can see that
   nine other rows were reviewed and consciously not promoted, rather
   than assume "the rest were ignored." This is what the promotion gate
   audit trail looks like in practice
4. **§4 "Native-Only Delta" untouched.** Its narrative (3.) about KV
   cache partial binding is correct under the new state and would be
   misleading to edit per-row — promotion is row-state, not narrative-
   reframing

## Next Authorized Round

Three candidates, ranked:

### Path B-1.2 (recommended): Native Adapter Real Lifecycle on Admitted Candidate

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-real-smoke-on-admitted-candidate.md`
  (to be authored)
- run `tests/test_mlx_native_backend_real_smoke.py` with
  `OWLMLX_NATIVE_SMOKE_MODEL_PATH=/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`
  on the now-admitted candidate; this is the round that exercises
  `MlxNativeBackend.load → stream_generate → unload` end-to-end on a
  real model
- requires the same RAM headroom gate as B-1 (≥70 GB free / reclaimable;
  `omlx.cli serve` must not be running, or be killable as in B-1)
- on success: produces declared-provenance evidence sufficient to lift
  the B-1.2 cap on four B-1.1-promoted rows (model handle, tokenizer
  handle, decode_step iterator, per-step finish_reason) and to consider
  KV cache handle, scheduler admission, cooperative cancellation for
  promotion in a follow-up B-1.3 round
- explicitly does **not** itself promote any row — promotion stays a
  separate doc round under the gate

### Path B-2 (alternative, parallel-safe): Sibling Candidate Admissibility

- B-1-shaped admissibility for `Qwen3.6-27B` (`qwen3_5`) and
  `gemma-4-31B-it` (`gemma4`); each its own round
- adds breadth (multiple admitted candidates) but does not unblock
  matrix promotion further

### Path B-3 (deferrable): Sampler Injection Binding

- mirror the KV-cache-handle round shape on `mlx_lm.sample_utils.make_sampler`
- can run any time; not gated on B-1.2 / B-2

I recommend **B-1.2 first**: it is the only round that lifts the cap
this round just stated, and it cashes in B-1's admitted candidate while
the operator memory is fresh.
