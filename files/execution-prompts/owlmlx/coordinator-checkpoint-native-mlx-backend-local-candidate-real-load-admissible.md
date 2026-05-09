# owlmlx Coordinator Checkpoint — Native MLX Backend Local-Candidate Real Load (B-1): admissible

## Verdict

- `native_mlx_backend_local_candidate_real_load_qwen3_5_moe_35b_a3b_admissible`

The local mirror at `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B` was
loaded by `mlx_lm.load()` without exception, and one minimal
`stream_generate` call returned 8 token chunks. The candidate's verdict
in `native-mlx-backend-local-candidate-admissibility.md` §3 advances
from `likely-admissible-pending-load` to `admissible`. Provenance
satisfies §4.1 "Local HF mirror" first-class form (upstream repo +
commit SHA + mirror date cited).

## What This Checkpoint Is

The redirected main line's fourth round and the first round to use the
Promotion Gate (§1a) framework. This round does **not** itself promote
any capability matrix row; it produces the declared-provenance evidence
that a follow-up round may cite when proposing promotions.

## Resource Pre-Check (Step 1)

Before any load attempt:

- physical RAM: 128 GB (≥ 96 GB tier)
- initial reading: free 6.3 GB, inactive 55.6 GB → reclaimable total
  ~64 GB → **below the prompt's `free ≥ 70 GB` gate**
- root cause located: PID 12141 was a 2-day-10-hour-old `omlx.cli serve`
  process holding 52 GB RSS, listening on `127.0.0.1:8001` with no active
  client connections (LISTEN-only socket per `lsof -nP -iTCP:8001`)
- operator-authorized SIGTERM (no SIGKILL escalation needed; process
  exited cleanly within ~13 seconds)
- post-kill reading: free 60.8 GB, inactive 26.9 GB, speculative 2.0 GB
  → reclaimable total **89.6 GB** (134% of the model's 67 GB on-disk
  footprint)
- gate satisfied; proceeded to Step 2

This is recorded because the resource gate was explicitly designed to
prevent swap-thrash loads, and the pre-check did its job: it blocked the
load until the operator-authorized cleanup of an unrelated long-running
process.

## Step 2 Result

Single blocking `mlx_lm.load("/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B")`
invocation via temporary script `/tmp/owlmlx_local_candidate_load_attempt.py`
(deleted after the round; not committed to repo).

```json
{
  "mlx_lm_version": "0.31.2",
  "verdict": "load_returned_without_exception",
  "elapsed_s": 14.05,
  "model_type_repr": "Model",
  "model_module": "mlx_lm.models.qwen3_5_moe",
  "tokenizer_type_repr": "TokenizerWrapper",
  "tokenizer_module": "mlx_lm.tokenizer_utils"
}
```

`Model.sanitize` (`qwen3_5_moe.py:23-50`) operated cleanly on the
upstream HF release's tensor naming, including the `experts.gate_up_proj`
repack. The medium-confidence residual unknown recorded in the
admissibility document §3.2 is now resolved.

## Step 4 Result (Minimal Smoke)

`stream_generate(model, tokenizer, "hello", max_tokens=8)` over the
loaded session:

```json
{
  "verdict": "stream_returned",
  "elapsed_s": 7.93,
  "chunks_observed": 8,
  "first_chunk_repr": "GenerationResponse(text=',', token=11, ..., prompt_tps=0.13, generation_tps=13667.55, peak_memory=69.40, finish_reason=None)",
  "last_chunk_repr": "GenerationResponse(text=' simple', token=4145, ..., generation_tps=76.06, peak_memory=69.40, finish_reason='..."
}
```

Quantitative observations (not capability claims):

- decode throughput stabilized to ~76 tok/s after the first-token warm-up
- peak memory while serving: **69.40 GB** (consistent with the 67 GB
  on-disk bf16 footprint plus framework overhead)
- prompt_tps reading 0.13 is a single-token-prompt division artifact, not
  a serving metric

The smoke confirms `load → stream_generate → unload`-shaped lifecycle is
exercisable on this candidate via the existing native adapter dependencies
(`mlx_lm.load`, `mlx_lm.stream_generate`). The smoke was executed
**outside** the native adapter (directly against `mlx_lm`), because this
round is an admissibility round, not an adapter-binding round.

## Provenance (per §4.1 "Local HF mirror")

- upstream repo: `Qwen/Qwen3.6-35B-A3B` on HuggingFace
  (anchor: `README.md` `license_link` →
  `https://huggingface.co/Qwen/Qwen3.6-35B-A3B/blob/main/LICENSE`)
- upstream commit SHA:
  **`53c43178507d69762986fbfa314f6e8d4d859409`**
  (extracted from `.cache/huggingface/download/config.json.metadata` and
  `.cache/huggingface/download/model.safetensors.index.json.metadata`,
  both files agree on the same first-line value)
- mirror download timestamps: 2026-04-23 (per the second column of the
  metadata files; multiple shards downloaded across that day)
- mlx_lm version of admission: 0.31.2

This is sufficient to qualify the mirror as a §4.1 first-class candidate
and to back any future capability matrix promotion that cites this row.

## What This Checkpoint Closes

- the `B-1: Native MLX Backend — Local-Candidate Real Load` round, with
  verdict `admissible`
- the residual unknown in
  `native-mlx-backend-local-candidate-admissibility.md` §3.2 about
  whether `Model.sanitize` matches the upstream HF release's tensor
  naming for `qwen3_5_moe`
- the prerequisite-evidence gap blocking any promotion-gate-compliant
  proposal that cites this candidate

## What This Checkpoint Does Not Claim

- **no capability matrix row was promoted in this round.** Promotion
  must run as a separate round under Promotion Gate §1a, with explicit
  row-by-row reasoning and provenance line cited from this checkpoint
- **no native adapter binding was added or modified.** The smoke ran
  directly against `mlx_lm`, not through `MlxNativeBackend`. Wiring the
  same flow through the native adapter is a separate round
- the admissibility result for `Qwen3.6-27B` (`qwen3_5` arch) and
  `gemma-4-31B-it` (`gemma4` arch) remains
  `likely-admissible-pending-load`. Each requires its own B-1-shaped
  round
- no claim of multi-request scheduling, KV cache reuse across requests,
  speculative decoding, or any unrelated runtime capability is added
  by this round
- no `pyproject.toml`, `uv.lock`, `.python-version`, or `conftest.py`
  change

## Side Effects

- one third-party process killed (`omlx.cli serve`, PID 12141), with
  operator authorization, after verifying no active client connections
- one temporary script written to `/tmp/owlmlx_local_candidate_load_attempt.py`
  and deleted at round end; one output file `/tmp/owlmlx_local_candidate_load_attempt.out`
  retained outside the repo as informal log
- nothing downloaded, nothing converted, no model touched on disk
  beyond memory-mapping during load

## Test Counts (No Change)

This round did not modify any code under test and did not add tests.
Last known counts persist (94 passed + 3 skipped on the focused MLX
native adapter set, per the prior round's checkpoint).

## Current Frozen Active Seam (No Change)

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

## Notable Implementation Choices

1. **Smoke ran outside the native adapter, not through it.** The point
   of this round was admissibility of the *artifact*, not coverage of
   the adapter. Running through `MlxNativeBackend` would have
   confounded two questions: "does the artifact load" and "does the
   adapter route correctly". Each gets its own round
2. **Temporary script not committed.** The load attempt is a one-shot
   admissibility experiment, not a reproducible artifact. The
   reproduction recipe is in this checkpoint plus the admissibility
   document; the script itself was a vehicle, not a deliverable
3. **Operator-authorized SIGTERM of `omlx.cli serve` is recorded as a
   side effect, not as a permanent decision.** owlmlx is in scope to
   replace oMLX, but this round did not freeze any "oMLX is shut down"
   state — the operator may bring it back up at any time, and that does
   not invalidate this round's verdict

## Next Authorized Round

Three candidates, ranked:

### Path B-1.1 (recommended): Capability Matrix Promotion Proposal

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-capability-matrix-promotion-from-b1-evidence.md`
  (to be authored)
- scope: walk every native-column row whose evidence kind would advance
  given B-1's result. Candidates:
  - "In-process model handle" `experimental` → propose `partial` with
    real-load evidence (model object actually returned)
  - "In-process tokenizer handle" `experimental` → propose `partial`
    with real-load evidence (tokenizer wrapper actually returned)
  - "Token-level decode_step iterator" `experimental` → propose `partial`
    with real-stream evidence (8 chunks observed)
  - "Per-step finish-reason inspection" `experimental` → propose
    `partial` (last chunk carried `finish_reason` field, even if
    truncated in display)
  - **explicitly does not** promote KV cache handle from `partial` to
    `supported`, because the smoke did not use the adapter's
    `_make_fresh_prompt_cache` binding
- the proposal walks Promotion Gate §1a explicitly and either justifies
  each row with the provenance + evidence above, or declines that row
- still doc-only; no runtime change

### Path B-1.2 (parallel, optional): Native Adapter Real Lifecycle Test

- run the same `load → stream_generate → unload` flow **through**
  `MlxNativeBackend` (not directly against `mlx_lm`) on the now-admitted
  candidate; this is what
  `tests/test_mlx_native_backend_real_smoke.py` is wired to do under
  `OWLMLX_NATIVE_SMOKE_MODEL_PATH`
- on success: produces evidence that the native adapter's KV cache
  binding actually fires under real load; this is what would unlock a
  Promotion Gate-compliant promotion of the KV cache row
- requires ~70 GB RAM headroom again (same gate as this round)
- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-real-smoke-on-admitted-candidate.md`
  (to be authored)

### Path B-2 (deferred): Sibling Candidate Admissibility

- run B-1-shaped admissibility for `Qwen3.6-27B` (`qwen3_5`) and
  `gemma-4-31B-it` (`gemma4`); same procedure, separate rounds
- not recommended next because the matrix value of admitting siblings
  before promoting from the first admission is small

I recommend **B-1.1 first**: cash in this round's evidence into matrix
state via the Promotion Gate, while the load happened recently enough
that the operator memory is fresh. **B-1.2 second** if the operator
wants real-lifecycle proof through the adapter (the first round to
actually bind native adapter behavior to a real model). **B-2 third**.
