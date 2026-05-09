# owlmlx Native MLX Backend — Local Candidate Admissibility

> Status: authoritative
> Updated: 2026-05-08
> Scope: per-candidate admissibility judgment for models present on the
> local development host, against the input contract defined in
> `native-mlx-backend-input-contract.md`. This document does **not**
> trigger any upgrade, conversion, or download.

## 1. Why This Document Exists

The capability matrix promotes rows based on real-candidate evidence
(see "Promotion Gate" in `native-mlx-backend-capability-matrix.md`). A
real candidate must be **declared** in this document with a verdict and a
provenance line, or it cannot be used as promotion evidence. Toy-grade
artifacts pulled ad-hoc do not qualify.

## 2. Survey Method

For each model directory under `/Users/yeemio/AI/Agent/models/`:

- list contents to identify weight shards and tokenizer assets
- read `config.json` head (`architectures`, `model_type`, dtype-related
  fields, `quantization` / `quantization_config` if present)
- look up `model_type` in `mlx_lm/models/` (per input contract §4)
- judge admissibility against input contract §3 and §5

No model was loaded; no `mlx_lm.load()` call was executed.

## 3. Local Candidates (2026-05-08)

| Path | Format | `model_type` | Arch module present | Quant | safetensors layout | Admissibility |
|---|---|---|---|---|---|---|
| `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B` | HF release (Transformers/vLLM/SGLang/KTransformers compatible) | `qwen3_5_moe` (top) + `qwen3_5_moe_text` / `qwen3_5_moe` nested | `mlx_lm/models/qwen3_5_moe.py` ✓ | none (bf16) | `model-NNNNN-of-00026.safetensors` + `model.safetensors.index.json` ✓ | **admissible** (B-1, 2026-05-08) |
| `/Users/yeemio/AI/Agent/models/Qwen3.6-27B` | HF release | `qwen3_5` (top, dense) + `text_config` nested | `mlx_lm/models/qwen3_5.py` ✓ | none (bf16) | sharded safetensors ✓ | **likely-admissible-pending-load** |
| `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` | HF release | `gemma4` (top) + `gemma4_text` / `gemma4_vision` nested | `mlx_lm/models/gemma4.py` ✓ + `gemma4_text.py` ✓ | none (bf16) | `model-NNNNN-of-00002.safetensors` + index ✓ | **likely-admissible-pending-load** |

### 3.1 Verdict Vocabulary

| Verdict | Meaning |
|---|---|
| `admissible` | actually loaded successfully via `mlx_lm.load()` and tokenized at least once |
| `likely-admissible-pending-load` | shape passes input-contract §3+§5 inspection but no `load()` has run |
| `inadmissible-needs-conversion` | shape rejected by input contract; needs MLX-format conversion via `mlx_lm.convert` or upstream artifact |
| `inadmissible-no-arch` | `model_type` has no matching module in `mlx_lm/models/` |
| `inadmissible-vendor-format` | weights in PyTorch `.bin` / GGUF / vendor format not accepted by `load()` |

### 3.2 Per-Candidate Notes

**Qwen3.6-35B-A3B** (~67 GB on disk, 26 shards):

- `architectures: ["Qwen3_5MoeForConditionalGeneration"]`,
  `image_token_id: 248056`, `text_config: {...}` — full VLM-style config
- maps to `qwen3_5_moe` arch which has the `text_config` tolerance and
  `vision_tower` / `model.visual` sanitization (input contract §5)
- bf16, no `quantization` block — loads as bf16
- residual unknown (medium confidence) about `Model.sanitize` matching
  the upstream HF tensor naming was the load-time risk distinguishing
  `likely-admissible` from `admissible`. **B-1 (2026-05-08) resolved
  this by executing one `mlx_lm.load()` call against this directory:**
  - `mlx_lm.load()` returned without exception in **14.05 s**
  - returned `model_module = mlx_lm.models.qwen3_5_moe.Model`,
    `tokenizer = mlx_lm.tokenizer_utils.TokenizerWrapper`
  - one minimal `stream_generate(prompt="hello", max_tokens=8)` returned
    8 chunks in 7.93 s; first observed token was the comma `,`
    (token id 11); decode peak memory **69.4 GB**
  - `experts.gate_up_proj` repack inside `Model.sanitize`
    (`qwen3_5_moe.py:36-50`) operated cleanly on the upstream HF release's
    tensor layout — no mismatch surfaced
- **Provenance (per §4.1, "Local HF mirror" first-class form):**
  - upstream repo: `Qwen/Qwen3.6-35B-A3B` (HF), license-linked from
    the local `README.md`
  - upstream commit SHA: `53c43178507d69762986fbfa314f6e8d4d859409`
    (cited from `.cache/huggingface/download/*.metadata` first line,
    consistent across multiple sampled files)
  - mirror download date: 2026-04-23
  - mlx_lm version under which admission was verified: 0.31.2
- upgrade path if a future mlx_lm version regresses sanitize behavior:
  `mlx-community/Qwen3.6-35B-A3B-bf16` (or quantized variants)

**Qwen3.6-27B** (~52 GB on disk):

- `architectures: ["Qwen3_5ForConditionalGeneration"]`,
  `model_type: "qwen3_5"` (dense, not MoE), VLM-style `text_config`
- maps to `qwen3_5` arch (presence verified; sanitize behavior not read in
  detail this round)
- same likely-admissible-pending-load posture as the MoE sibling
- upgrade path if load fails: check `mlx-community/Qwen3.6-27B-*` releases

**gemma-4-31B-it**:

- `architectures: ["Gemma4ForConditionalGeneration"]`, `model_type:
  "gemma4"`, has `gemma4_text` + `gemma4_vision` nested model_types
- maps to `gemma4` (multimodal entry) and `gemma4_text` (text-only entry);
  whether `mlx_lm.load()` routes to the text-only path automatically when
  given the top-level `model_type: "gemma4"` config is **not verified
  this round** — requires reading `gemma4.py` `from_dict` / `sanitize`
- upgrade path if load fails: check `mlx-community/gemma-4-*` releases

## 4. Provenance Policy

Real-candidate evidence used to promote a capability matrix row must
include a provenance line. This document is the **registry of acceptable
provenance forms**:

### 4.1 Acceptable Provenance Forms

| Form | Trust level | Recording requirement |
|---|---|---|
| `mlx-community/<name>` HF release | first-class | record HF revision SHA, model_type, mlx_lm version used |
| Local HF mirror (e.g. `/Users/yeemio/AI/Agent/models/<name>`) of an upstream HF release | first-class **iff** matching upstream HF revision can be cited | record upstream repo + revision the local copy mirrors |
| `unsloth/*-MLX-*` or other reputable third-party MLX-format release | second-class | record HF revision SHA + note the third-party source explicitly |
| Self-converted via `mlx_lm.convert` | second-class | record exact convert command, source HF repo + revision, mlx_lm version, output config.json hash |
| `mlx-vlm`-converted | conditional | admissible only for arch modules with documented VLM-config tolerance (currently `qwen3_5_moe`); record arch + mlx-vlm version |
| Custom `model_file` Python in repo | requires review | record file SHA-256 + reviewer + review date |

### 4.2 Unacceptable Provenance Forms

- ad-hoc curl / wget download with no recorded revision
- "small model from somewhere" with no upstream attribution
- conversions without recorded mlx_lm version (DWQ vs affine confusion
  is invisible without the version)
- any artifact not linked to a row in §3 of this document

## 5. What This Document Does Not Decide

- **whether** to convert any candidate — that is a separate operator
  decision and a separate round
- **when** to run the env-gated real-model smoke
  (`tests/test_mlx_native_backend_real_smoke.py`) — that is gated on
  capability matrix promotion strategy, not on this document
- **whether** the local Qwen3.6-35B-A3B will actually load — moving from
  `likely-admissible-pending-load` to `admissible` requires an actual
  `mlx_lm.load()` call which this round does not perform
- the scope of any future round that turns this table into a machine-
  readable provenance registry

## 6. Maintenance

This table is updated when:

- a new local candidate is added to the host
- a candidate's verdict changes (e.g. a load is attempted and succeeds /
  fails)
- a new HF release is admitted as candidate provenance
- the input contract changes (e.g. mlx_lm upgrade adds / removes a
  quantization mode)

The table is **append-mostly**; verdict downgrades are recorded with a
dated note rather than silent edits.
