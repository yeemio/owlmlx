# owlmlx Coordinator Checkpoint — Native MLX Backend Input Contract & Local-Candidate Admissibility: frozen

## Verdict

- `native_mlx_backend_input_contract_and_local_candidate_admissibility_frozen`

This is a **documentation-only** round. Four source-of-truth documents
land; one capability-matrix-level anti-pollution clause lands; four
README document-map lines land. Zero runtime code change. Zero model
download. Zero conversion execution. Zero capability matrix row-state
change.

## What This Checkpoint Is

The redirected main line's third round. After the second round
(`native-mlx-backend-lifecycle-smoke-and-kv-cache-handle-owned-partial-promoted`)
landed real-installed `mlx_lm 0.31.2` upstream binding for KV cache
handle, the natural next move was a real-model smoke. The project owner
explicitly redirected it: **"我不想拿所谓的冒烟漂亮数据来污染环境"**.

The professional move under that constraint is not to find a bigger
smoke; it is to write down, before any smoke runs, what a smoke must
*be* in order to count as evidence for matrix promotion. This round
is that contract.

## What Is Now Frozen Exact

### New documents (4)

- `docs/source-of-truth/native-mlx-backend-input-contract.md`
  — what `mlx_lm.load()` accepts, sourced from
  `.venv/lib/python3.11/site-packages/mlx_lm/utils.py` 0.31.2 with file
  paths and line numbers; covers resolution path, mandatory on-disk
  shape, architecture module registry, VLM-config tolerance pattern,
  quantization variant first-class status (4/6/8bit affine, bf16,
  mxfp4, nvfp4, 4bit-DWQ-as-affine), custom-architecture escape hatch,
  what `mlx_lm.load()` does not do, and confidence levels
- `docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`
  — per-candidate admissibility verdicts for the three local model
  directories under `/Users/yeemio/AI/Agent/models/`: Qwen3.6-35B-A3B,
  Qwen3.6-27B, gemma-4-31B-it. All three are
  `likely-admissible-pending-load`: their on-disk shape passes the
  input contract §3+§5 check (model_type maps to a present
  `mlx_lm/models/<arch>.py`, sharded `model*.safetensors` + index
  present, bf16) but no `mlx_lm.load()` was actually invoked this
  round. Provenance acceptance policy (§4.1) records six provenance
  forms in decreasing trust level
- `docs/source-of-truth/native-mlx-backend-conversion-path-ownership.md`
  — layered ownership statement: execution layer borrowed from
  `mlx_lm.convert` / `mlx-vlm` / mlx-community releases; path semantics
  layer owned by owlmlx. Four acceptable conversion routes; what
  owlmlx does not authorize (no fork of `mlx_lm.convert`, no
  owlmlx-internal arch additions, no automation that erases provenance,
  no quality-variant-as-capability mapping)

### Capability matrix change (clause-only, no row state changes)

- `docs/source-of-truth/native-mlx-backend-capability-matrix.md`
  gains §1a "Promotion Gate (Anti-Pollution Contract)". Native rows can
  only be promoted from `partial` to `supported` on **declared-provenance
  real-candidate evidence**. Ad-hoc toy smoke is explicitly disqualified
  even when all assertions pass. Promotions must cite the candidate row
  in `native-mlx-backend-local-candidate-admissibility.md`, record
  provenance in the promoting round's checkpoint, and update the
  promoted row's `Notes` column with load+lifecycle evidence
- header `Updated:` advanced from 2026-05-07 to 2026-05-08
- **no §3 row state field changed**; **no §3a row added**; **no §6
  feasibility verdict changed**; **no §7 next-round recommendation
  changed**

### README change (one-line per-doc additions)

- `README.md` Document Map gains four new lines under the existing
  capability-matrix line, pointing to the four new source-of-truth
  documents. No narrative text added. No other section modified.

## Key Findings From The Source Read

These are recorded because they are non-obvious and influence future
rounds:

1. **mlx-vlm-converted artifacts are load-path-compatible with
   `mlx_lm.load()` for text-only inference** when the arch module supports the
   `text_config` tolerance + `vision_tower` sanitize pattern. Verified
   directly for `qwen3_5_moe` at
   `mlx_lm/models/qwen3_5_moe.py:14-50`. This dissolves the worry that
   the `mlx-community/Qwen3.6-35B-A3B-*` releases (converted with
   mlx-vlm 0.4.4 per their model cards) are unusable as text-only
   candidates at the input-contract layer; actual admission still
   requires a per-artifact load
2. **4bit-DWQ is indistinguishable from 4bit affine at `mlx_lm.load`
   time**. DWQ is implemented in `mlx_lm/quant/dwq.py` as an offline
   conversion CLI; its output is ordinary `mode="affine", bits=4,
   group_size=64` safetensors. Therefore the matrix must not treat
   "4bit" and "4bit-DWQ" as separate capability evidence points —
   recorded explicitly in §1a Promotion Gate
3. **The local Qwen3.6-35B-A3B Transformers full-precision release has
   `model_type: "qwen3_5_moe"` matching exactly to
   `mlx_lm/models/qwen3_5_moe.py`**. The plausible outcome of the
   eventual `load()` call is success, but the residual unknown is whether
   the original HF release's tensor naming matches what `Model.sanitize`
   expects (sanitize was authored against mlx-vlm-converted layouts;
   the HF release may differ). This residual unknown is what
   distinguishes `likely-admissible-pending-load` from `admissible` in
   the candidate table
4. **mlx_lm.load only reads `model*.safetensors`** — no `pytorch_model
   *.bin`, `*.gguf`, or `consolidated.*` are pulled. The local Qwen3.6
   directories happen to be safetensors-format (the HF release ships
   safetensors-only), so this constraint does not block them; but it is
   a hard constraint to record for any future candidate

## Test Counts (No Change)

This round added no tests and changed no code paths under test. The last
known counts from the prior round persist:

- `tests/test_mlx_native_backend.py`: 13 passed + 1 skipped
- `tests/test_mlx_native_backend_post_claim_invariants.py`: 6 passed
- `tests/test_mlx_native_backend_real_upstream_binding.py`: 4 passed
- `tests/test_mlx_native_backend_real_smoke.py`: 2 skipped (env-gated)
- combined: 94 passed + 3 skipped

No pytest run was executed in this round. The above is a non-changing
reference, not a fresh measurement.

## Current Frozen Active Seam (No Change)

- `summary.seam_rung = aggregation_active_seam_exact`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- `preserved_secondary_runtime_branch = turboquant_preconditions`
- `preserved_secondary_runtime_branch.status = preconditions_exact`
- top-level customer-runtime-evidence label remains `early_formal_runtime`

This checkpoint does not move the active phase45 seam. The native
adapter remains parallel and is not invoked by any published serving
path.

## What This Checkpoint Closes

The "Native MLX Backend Input Contract & Local-Candidate Admissibility"
documentation round is **frozen**:

- input contract is recorded against installed mlx_lm 0.31.2 source
- local candidates are surveyed and posture-scored
- promotion gate is in force at the matrix-document level
- conversion path ownership is layered and recorded

The matrix anti-pollution anchor exists. From this point forward, any
round that promotes a native row must satisfy the gate or be rejected.

## What This Checkpoint Does Not Claim

- continuous batching, prefix cache reuse, KV cache reuse, cache parity,
  stream interleaving, speculative decoding, structured output — all
  remain unclaimed
- any local candidate has been actually loaded by `mlx_lm.load()`
- any capability matrix row has been promoted
- any environment file (`pyproject.toml`, `uv.lock`, `.python-version`,
  `conftest.py`) has been changed
- any model has been downloaded or converted
- the native adapter is wired into any serving path
- the subprocess sentinel chain has been resumed

## Notable Implementation Choices

1. **No machine-readable provenance registry yet.** The candidate table
   in `native-mlx-backend-local-candidate-admissibility.md` is markdown,
   not YAML. A YAML registry was considered and deferred — premature
   schema would lock in vocabulary before enough candidates exist to
   validate the schema. Three candidates is too few. This becomes a
   round of its own when ≥6 candidates accumulate
2. **gemma4 routing not verified this round.** The local
   gemma-4-31B-it has `model_type: "gemma4"` and both `gemma4.py` and
   `gemma4_text.py` exist; whether `mlx_lm.load()` routes correctly to
   text-only when given the multimodal top-level config was not read in
   detail. Recorded as a per-candidate residual unknown rather than
   investigated, because this round is shape-survey-only
3. **mlx-community provenance form does not require revision SHA today.**
   §4.1 records SHA recording as a requirement, but no SHA is recorded
   for any current candidate because no real-candidate is admitted yet.
   The first round that promotes a row is the first round that has to
   record an SHA

## Next Authorized Round

Three candidates, ranked:

### Path B-1 (recommended): Native MLX Backend — Local-Candidate Real Load

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-local-candidate-real-load.md`
  (to be authored)
- target candidate: `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`
  (already on disk, no download)
- minimal scope: invoke `mlx_lm.load(<local_path>)` once, capture
  whether it succeeds or raises; if it succeeds, perform a single
  short `stream_generate` (`max_tokens=8`) and then `unload`
- on success: advance the candidate's verdict from
  `likely-admissible-pending-load` to `admissible` with provenance line
  citing the local mirror, propose matrix promotion in a separate
  follow-up round
- on failure: record exact exception, classify (sanitize-shape-mismatch
  / arch-import-error / config-key-missing / other), update the
  candidate row, decide whether to fall back to an mlx-community
  artifact in a separate round
- explicitly does **not** introduce new tests beyond the existing env-
  gated `test_mlx_native_backend_real_smoke.py`
- explicitly does **not** download anything

### Path B-2 (alternative): mlx-community Artifact Real Load

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-mlx-community-real-load.md`
  (to be authored)
- only chosen if B-1 fails or if the operator decides the local
  Transformers release is too risky (67 GB bf16 RAM headroom, etc.)
- target candidate: `mlx-community/Qwen3.6-35B-A3B-bf16` or
  `mlx-community/Qwen3.6-35B-A3B-4bit` per operator choice
- requires a download (this is the conditional download moment, not the
  current moment)

### Path B-3 (parallel, deferrable): Sampler Injection Binding

- file: `files/execution-prompts/owlmlx/owlmlx-native-mlx-backend-sampler-injection-binding.md`
  (to be authored)
- mirror the KV-cache-handle round shape: bind
  `mlx_lm.sample_utils.make_sampler` per request, record on
  `_NativeSession.last_sampler`, single-request semantics, real-upstream
  binding test
- expands the native adapter's owned entry-point surface without
  promoting any existing row
- can be picked up at any time; not gated on B-1 / B-2

I recommend **Path B-1 first**. It cashes in the contract that this
round just locked, on a candidate that is already on disk, with no
download, no conversion, and a binary-shaped outcome (loads or doesn't).
B-2 only becomes the right move if B-1 fails. B-3 is independent and
can run any time the operator wants entry-point surface expansion
without promotion stakes.
