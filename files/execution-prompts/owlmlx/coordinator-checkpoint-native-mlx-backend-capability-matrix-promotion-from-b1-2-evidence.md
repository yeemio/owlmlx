# owlmlx Coordinator Checkpoint — Native MLX Backend Capability Matrix Promotion from B-1.2 Evidence (B-1.3)

## Verdict

- `native_mlx_backend_capability_matrix_first_supported_labels_4_promoted_2_declined`

Four native rows advance from `partial` to `supported` under §1a Promotion
Gate. Two rows stay `partial` with explicit decline reasons. Seven other
rows (without B-1.2 evidence) are not touched. **This is the first round
in owlmlx's native MLX backend capability matrix to produce `supported`
labels.**

## What This Checkpoint Is

The redirected main line's seventh round and the second §1a Promotion
Gate round (after B-1.1). It is doc-only: zero runtime / test /
environment / model changes. Its product is row-state advancement
backed by B-1.2's declared-provenance real-candidate adapter-routed
evidence, with a complete §1a + legend-predicate walkthrough recorded
in §3d.

## What Is Now Frozen Exact

### Capability matrix changes

`docs/source-of-truth/native-mlx-backend-capability-matrix.md` §3:

| Row | Native column |
|---|---|
| In-process model handle | `partial` → **`supported`** |
| In-process tokenizer handle | `partial` → **`supported`** |
| Token-level `decode_step` iterator | `partial` → **`supported`** |
| Per-step finish-reason inspection | `partial` → **`supported`** |
| KV cache handle (`make_prompt_cache`) | unchanged (`partial`); decline recorded |
| Scheduler admission hook | unchanged (`partial`); decline recorded |

Each promoted row's Notes column was rewritten to remove the
"until B-1.3 walks the gate" stale framing and replaced with the
B-1.3 §3d justification + legend predicate evidence.

The two declined rows' Notes columns were updated to record the §3d
decline reason (version-drift caveat for KV cache handle; legend
structural ceiling for scheduler admission hook).

### New §3d section

A new "Promotion-Gate-Compliant Promotions (B-1.3 Round)" section was
inserted between §3c and §4. It records:

- provenance line cited from B-1.2 checkpoint (HF revision SHA, mlx_lm
  version, evidence test file)
- per-row §1a four-gate walkthrough (gates 1–4) for all six B-1.2
  candidates
- per-row legend-predicate verification ("upstream stable public API +
  no patching") for the four promoted rows
- per-row legend-predicate analysis for the two declined rows
- explicit list of rows outside B-1.3's scope (7 rows with no B-1.2
  evidence)

### Staleness sweep performed

Per `feedback-stale-language-sweep.md` discipline, the matrix was swept
for stale framing left from prior rounds. Refreshed:

- §1 third paragraph: removed "every native row below is still scaffold-
  grade. A `supported` label would require..." wording — replaced with
  status reflecting that B-1.3 produced four `supported` labels and a
  legend-clarification paragraph distinguishing entry-point reachability
  from product-feature completeness
- §2 fourth bullet: "scaffold-grade entry-point assumptions until
  lifecycle smoke testing runs" → updated to reference B-1 / B-1.2 /
  B-1.3 evidence chain
- §3a closing paragraph: added §3d cross-references for
  admission/cancellation/KV-cache rows, removed "B-1.3 §1a walkthrough
  pending" framing
- §3b decline table: added §3d cross-references for KV cache handle and
  Scheduler admission hook entries
- §5 last bullet: refreshed to reflect §3d outcome
- §6 Feasibility Verdict: added B-1.3 §3d outcome line
- §7 Recommended Next Round: rewrote entirely. Previously said
  "B-1.3 — Capability Matrix Promotion from B-1.2 Evidence" (which is
  this round). Now points at C-1 / C-2 / C-3 / C-4 (the rounds that
  move the seven-line architectural assessment, not just the matrix)

### Files modified

- `docs/source-of-truth/native-mlx-backend-capability-matrix.md` —
  §3 row state changes (4 promote, 2 decline), §3d new section, §1 /
  §2 / §3a / §3b / §5 / §6 / §7 staleness sweep edits

### Files added (round-scope)

- `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-capability-matrix-promotion-from-b1-2-evidence.md`
  (this round's prompt)
- `files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-capability-matrix-promotion-from-b1-2-evidence.md`
  (this checkpoint)

## Provenance Cited (per §1a gate 2)

- candidate row: `Qwen3.6-35B-A3B` in
  `native-mlx-backend-local-candidate-admissibility.md` §3 (verdict
  `admissible`, B-1, 2026-05-08)
- upstream HF repo: `Qwen/Qwen3.6-35B-A3B`
- upstream commit SHA: `53c43178507d69762986fbfa314f6e8d4d859409`
- mlx_lm version: 0.31.2
- evidence checkpoint:
  `coordinator-checkpoint-native-mlx-backend-real-smoke-on-admitted-candidate.md`
- evidence test file: `tests/test_mlx_native_backend_real_smoke.py`
  (env-gated; activated by
  `OWLMLX_NATIVE_SMOKE_MODEL_PATH=/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`)

## §1a Gate Walkthrough Summary

For all four promoted rows, the four §1a gate conditions plus the
legend `supported` predicate are satisfied:

1. **gate 1** (admissibility row cited): same Qwen3.6-35B-A3B row,
   `admissible`
2. **gate 2** (provenance recorded): HF commit SHA cited
3. **gate 3** (Notes column updated): each row's Notes refreshed with
   B-1.2 lifecycle evidence + B-1.3 §3d cross-reference
4. **gate 4** (no quantization-subclass dependency): bf16 candidate, no
   quantization block — no DWQ vs affine 4bit risk
5. **legend predicate** ("upstream stable public API + no patching"):
   - Model handle → `mlx_lm.load` is top-level, stable across mlx-lm ≥ 0.22
   - Tokenizer handle → returned by `mlx_lm.load`; `TokenizerWrapper` public type
   - decode_step iterator → `mlx_lm.stream_generate` yields `GenerationResponse`
     (public dataclass)
   - finish_reason → `GenerationResponse` field, documented contract

For the two declined rows, gates 1–4 are satisfied but the legend
predicate fails:

- **KV cache handle**: submodule path (`mlx_lm.models.cache.*`),
  defensive attribute walk, version-pinned to 0.31.2 — matches the
  legend's `partial` "version drift / behavioral gaps" definition
- **Scheduler admission hook**: structurally cannot satisfy "upstream
  stable public API" because no upstream multi-request scheduler
  exists. owlmlx invented `_TicketedAdmission`. The legend has no
  vocabulary for "owlmlx-owned, no upstream needed"; row stays
  `partial` until either the legend is extended or upstream changes

## What This Checkpoint Closes

- the B-1 → B-1.1 → B-1.2 → B-1.3 evidence-and-promotion chain on the
  native MLX backend capability matrix
- the doc-grade gap between "real adapter lifecycle proven" and
  "matrix reflects the proof"
- the audit-trail expectation that promotions be walkable row-by-row
  against §1a + legend predicate (the §3d section is now the canonical
  template; B-1.1's §3b was a precursor, B-1.3's §3d adds legend-
  predicate verification on top)

## What This Checkpoint Does Not Claim

- no row reaches `supported` for the seven rows outside the B-1.2
  evidence set (cancellation / sampler / drafter / logits / prefill-
  decode / pinning / structured / multi-stream / KV reuse / KV cache
  handle / Scheduler admission hook). They each require their own
  declared-provenance evidence
- no claim that owlmlx itself supports the four promoted capabilities
  as **product features**. `supported` per legend means entry-point
  reachable through stable upstream public API without patching;
  product-feature support is a different, higher claim governed by
  other documents
- no native adapter binding was tested in this round
- no model was loaded / streamed / unloaded in this round
- no environment file changed
- no admissibility / input-contract / conversion-ownership / promotion-
  gate clause edited
- no `pyproject.toml` / `uv.lock` / `.python-version` / `conftest.py`
  modification

## Test Counts (No Change)

This round did not modify any code under test and did not add tests.
Last known counts persist (per B-1.2 checkpoint when env-gate active):

- `tests/test_mlx_native_backend.py`: 13 passed + 1 skipped
- `tests/test_mlx_native_backend_post_claim_invariants.py`: 6 passed
- `tests/test_mlx_native_backend_real_upstream_binding.py`: 4 passed
- `tests/test_mlx_native_backend_real_smoke.py`: 2 passed (env-gate
  activated) / 2 skipped (default CI)

## Current Frozen Active Seam (No Change)

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

## Notable Implementation Choices

1. **Two decline reasons are about legend, not evidence.** Both KV
   cache handle and Scheduler admission hook had complete B-1.2
   evidence. Neither was promoted because the legend predicate either
   doesn't bind (no upstream entry point) or shows version-drift
   warning signs. Honoring the legend strictly is the anti-pollution
   discipline in action — promoting either of these would require
   loosening `supported`'s definition, and that is a governance change,
   not a row promotion
2. **§3d sits between §3c and §4.** §3a was scaffold-round verified
   rows; §3b was B-1.1 promotion walkthrough; §3c was B-1.2 evidence;
   §3d is B-1.3 promotion walkthrough. The order encodes the project's
   evidence → promotion alternation, which is the mechanism that
   prevents "tests passed = row promoted" pollution
3. **§7 rewritten entirely.** Previously pointed at B-1.3 (this round).
   Now points at C-1 / C-2 / C-3 / C-4. Rationale: per the seven-line
   architectural assessment, doc-only B-x rounds beyond this round
   only polish the native-MLX matrix; the high-leverage gaps (cache /
   repeatability / memory governance / serving) live in other matrices
   and require code-grade work, not just doc rounds
4. **B-1.3 produced no `supported` for owlmlx-owned capabilities.**
   This is honest: the matrix is upstream-API-centric. owlmlx's own
   inventions (ticketed admission, single-request KV cache binding)
   are valuable but the legend gives them no `supported` slot. A
   future round could extend the legend; that is not B-1.3's call

## Side Effects

- four parallel research subagents were spawned during B-1.3
  foreground work. They produced read-only research markdown for
  C-1 / C-2 / C-3 / C-4 (cache manager, repeatability harness, memory
  actuator, serving surface hardening). Their outputs are landscape
  maps; **none** of them wrote files in the repo. Their content will
  be consumed by future C-x rounds when authored

## Next Authorized Round

Per refreshed §7 and the seven-line architectural assessment:

### High-leverage (recommended)

- **C-1 cache_manager scaffold** — moves Line 5 (`behind`). Subagent A
  produced the landscape map: `mlx_lm 0.31.2` already has `LRUPromptCache`
  + `PromptTrie` (a near-complete reuse engine); `cache_truth.py` is
  legacy SSD-cache schema, zero overlap; cache_manager.py is brand-new
  ownership domain
- **C-2 repeatability harness** — moves Line 6 (`behind`). Subagent B
  produced the landscape map: `phase45-heavy-weight-repeatability-status.md`
  has 5-rung enum at `supported_host_repeatability_visible` (repeat_runs=2);
  `comparative_evidence_runner.py` already exists. Gap is multi-axis
  randomized load with N≥20 runs + statistical degradation discriminator
- **C-3 memory_actuator** — moves Line 3 (`partial`). Subagent C-3
  produced the landscape map: `mx.clear_cache` / `set_cache_limit` /
  `set_wired_limit` / `get_active_memory` exposed by mlx; native
  `unload` today only drops Python references with no `mx.clear_cache`
  call. Five surface points identified
- **C-4 serving_hardening** — moves Line 4 (`partial`). Subagent C-4
  produced the landscape map: server.py has 0 middleware, no
  `x-request-id` propagation, no graceful shutdown, no `/metrics`,
  unbounded `Condition.wait()` in GenerationGate. Six concrete
  hardenings identified, none requiring batching

### Independent / deferrable

- **B-2** sibling candidate admissibility (Qwen3.6-27B / gemma-4-31B-it)
- **B-4** cooperative cancellation real-stream evidence

I recommend the **next round be C-1 or C-2 (operator's choice)**. Both
move different lines of the seven-line assessment. Both have research
landscape maps already produced. Doc-only B-x rounds beyond this point
add audit polish but no broader replacement-verdict movement.
