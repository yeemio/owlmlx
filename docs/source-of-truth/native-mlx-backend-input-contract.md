# owlmlx Native MLX Backend — Input Contract

> Status: authoritative
> Updated: 2026-05-08
> Scope: what `mlx_lm.load()` accepts as input, as observed in the
> `mlx_lm 0.31.2` source installed at
> `.venv/lib/python3.11/site-packages/mlx_lm/`. This document is the
> **input-side counterpart** of the capability matrix: the matrix says what
> entry points the native adapter can reach; this doc says what artifacts can
> flow in on the load side.

## 1. Why This Document Exists

owlmlx's native MLX backend (`owlmlx/runtime/mlx_native_backend.py`) defers
to `mlx_lm.load(...)` for model loading. Without a written input contract,
"can we load this model?" is decided ad-hoc per round, and every round risks
either a silent green check on a toy artifact or a silent red on a real
candidate. This document fixes the contract by reading the upstream source.

The contract is **not** owlmlx's invention — it is `mlx_lm`'s. owlmlx's job
is to record and reason about it, not to fork it.

## 2. Resolution Path: HF Repo Id vs Local Path

`mlx_lm.utils.load(path_or_hf_repo, ...)` (`utils.py:453-502`):

1. Existence check is `Path(path_or_hf_repo).exists()` — there is no scheme
   parsing. A string that happens to exist as a local directory is treated
   as local; otherwise it is forwarded to `huggingface_hub.snapshot_download`.
   See `_download` (`utils.py:236-249`).
2. The Hub download is filtered by `allow_patterns`:

   ```
   ["*.json", "model*.safetensors", "*.py", "tokenizer.model",
    "*.tiktoken", "tiktoken.model", "*.txt", "*.jsonl", "*.jinja"]
   ```

   (`utils.py:237-247`). PyTorch `.bin`, GGUF, `consolidated.*` are **not
   pulled**.
3. Local paths bypass `_download` but are subject to the same downstream
   validation in `load_model` and `load_tokenizer`.

**Implication for owlmlx**: a local model directory is admissible if and
only if it would survive the same validation a Hub-downloaded directory
gets. This means the on-disk shape — not the source — determines
admissibility.

## 3. Mandatory On-Disk Shape

For `mlx_lm.load()` to succeed:

| File / pattern | Required? | Source ref |
|---|---|---|
| `config.json` | yes | `load_config` opens `model_path / "config.json"` (`utils.py:264`) |
| `model*.safetensors` | yes (≥1) | `glob.glob(str(model_path / "model*.safetensors"))` (`utils.py:316`); on `strict=True` empty match → `FileNotFoundError` (`utils.py:319`) |
| `model.safetensors.index.json` | only if multi-shard | sharded models with index file are the standard HF layout |
| Tokenizer files | yes (one form) | `tokenizer_utils.load` accepts `tokenizer.json`, `tokenizer_config.json`, `tokenizer.model`, `*.tiktoken`, `tiktoken.model`, `*.jinja` (`utils.py:495 → 429`) |
| `generation_config.json` | optional | only `eos_token_id` is merged (`utils.py:267-277`) |
| Custom `*.py` arch file | optional | activated by `model_file` key in `config.json` (`utils.py:325`) |

**Not read by `load()`** even if present:

- `pytorch_model*.bin`
- `*.gguf` (handled by a separate loader in `mlx_lm/gguf.py`, not
  reachable through `load()`)
- `consolidated.*`
- vendor-specific files

`config.json` is parsed for two pieces of dispatch information:

- `model_type` — drives `_get_classes(config)` →
  `importlib.import_module(f"mlx_lm.models.{model_type}")`
  (`utils.py:175, 188`); after a `MODEL_REMAPPING` rewrite
  (`utils.py:45-55`)
- `quantization` (or HF-style `quantization_config`) — drives the
  optional quantize-on-load branch (`utils.py:365-390`)

## 4. Architecture Module Registry

`mlx_lm` resolves the architecture by filesystem dispatch into
`mlx_lm/models/`. A model can only be loaded if there is a matching `.py`
file (or a `MODEL_REMAPPING` redirect). Reading
`.venv/lib/python3.11/site-packages/mlx_lm/models/` reveals the present
modules; for owlmlx's current local-candidate scope (Qwen3.6 family +
Gemma 4 family), the relevant modules are:

| `model_type` | Module |
|---|---|
| `qwen3_5_moe` | `mlx_lm/models/qwen3_5_moe.py` |
| `qwen3_5` | `mlx_lm/models/qwen3_5.py` |
| `qwen3_moe` | `mlx_lm/models/qwen3_moe.py` |
| `qwen3` | `mlx_lm/models/qwen3.py` |
| `gemma4` | `mlx_lm/models/gemma4.py` |
| `gemma4_text` | `mlx_lm/models/gemma4_text.py` |

Anything not on this list — e.g. a hypothetical `qwen5_xyz` — is rejected
at `importlib.import_module`. Adding an arch is upstream work, not owlmlx
work.

## 5. VLM Configs and Vision-Tower Sanitization

A subtle but important property: `mlx_lm.load()` can ingest some
**VLM-converted artifacts** for text-only inference, but only when the
matching arch module has explicit support. The `qwen3_5_moe` module
demonstrates the pattern:

- `ModelArgs.from_dict` accepts both flat configs and `text_config`-nested
  configs (`mlx_lm/models/qwen3_5_moe.py:14-18`):

  ```python
  if "text_config" not in params:
      return cls(model_type=..., text_config=params)
  ```

- `Model.sanitize` strips weights whose names start with `vision_tower` /
  `model.visual` and re-prefixes the rest under `language_model.`
  (`mlx_lm/models/qwen3_5_moe.py:23-34`).

This means an mlx-vlm-converted artifact whose `config.json` contains
`vision_config` and whose safetensors contain `vision_tower.*` weights is
**load-path-compatible as a text-only LM** through `mlx_lm.load()`,
provided the arch module supports the dual-config + sanitize pattern.
Actual admission still requires a per-artifact load attempt.

This is **architecture-specific**, not a general property. `qwen2_5_vl`,
for instance, is reachable only via `MODEL_REMAPPING["qwen2_5_vl"] =
"qwen2_vl"` (`utils.py:52`). owlmlx must not generalize: each VLM-config
candidate requires per-architecture verification before admission.

## 6. Quantization Variant First-Class Status

The authoritative path is `load_model` lines 348–390 plus `quantize_model`
lines 798–806 in `utils.py`. Status of each variant relevant to
mlx-community's Qwen3.6 family:

| Variant | First-class at load? | Notes |
|---|---|---|
| `4bit` (affine) | yes | `mode="affine"` (default), `bits=4`, `group_size=64` (`utils.py:800` `defaults_for_mode["affine"]`) |
| `6bit` (affine) | yes | same path as 4bit, `bits=6`; not special-cased |
| `8bit` (affine) | yes | same path, `bits=8` |
| `bf16` | yes | not a quantization — weights load as stored. The `_quantize` branch is skipped when `config.json` has no `quantization` / `quantization_config` key (`utils.py:365` guard) |
| `mxfp4` | yes | `defaults_for_mode["mxfp4"] = (32, 4)` (`utils.py:802`); two ingest paths: native (`config["quantization"]["mode"] = "mxfp4"`) and HF-legacy (`quantization_config["quant_method"] == "mxfp4"` rewritten on `utils.py:375-379` to `{group_size: 32, bits: 4, mode: "mxfp4"}`) |
| `nvfp4` | yes (with caveat) | `defaults_for_mode["nvfp4"] = (16, 4)` (`utils.py:803`); only the **native** `mode` channel is auto-recognized — there is no HF-legacy `quant_method: "nvfp4"` rewrite branch. Also wraps `nn.QuantizedLinear` into `nn.QQLinear` when `config.get("quantize_activations", False)` (`utils.py:392-406`) |
| `4bit-DWQ` | **load-time identical to affine 4bit** | DWQ is an offline conversion technique implemented in `mlx_lm/quant/dwq.py` (`compute_dwq_targets:29`, `dwq_quantize:69`, CLI entry `main:242`). Its output is ordinary `mode="affine"` 4bit safetensors with `quantization = {"group_size": 64, "bits": 4, "mode": "affine"}`. **`mlx_lm.load` cannot distinguish it from a non-DWQ 4bit affine artifact** at runtime; there is no DWQ-aware decode path |

Other branches present in `load_model` (`utils.py:371-390`) but outside
owlmlx's current candidate scope: bitnet, compressed-tensors, AWQ, GPTQ.
Each has a distinct legacy rewrite branch.

**Implication for capability matrix**: 4bit and 4bit-DWQ should not be
treated as two separate evidence points for promotion. DWQ improves
conversion quality, not runtime capability.

## 7. Custom-Architecture Escape Hatch

A repo can ship a `model_file` key in `config.json` (`utils.py:325`)
that points to a Python file inside the repo. `mlx_lm.load()` will load
that file dynamically as the architecture module. This is how some
mlx-community releases ship pre-release / out-of-tree archs.

owlmlx admissibility policy on `model_file`: requires per-candidate
review. An untrusted custom `*.py` is code, not data — admitting it under
"declared provenance" requires recording the file hash and reviewing the
code in the admissibility table.

## 8. What `mlx_lm.load()` Does Not Do

- does not coerce dtype (no fp16/bf16/fp32 conversion at load)
- does not validate vocabulary size between `config.json` and tokenizer
- does not run a forward pass (so weight-shape vs arch mismatches surface
  on first generate, not on load)
- does not check disk-space sufficiency or RAM headroom
- does not enforce a license file or any provenance check

## 9. Confidence

- **High** for §2–§4, §6 (read directly from `utils.py`)
- **High** for §5 specifically for `qwen3_5_moe` — direct read of
  `mlx_lm/models/qwen3_5_moe.py:14-50`
- **Medium** for whether every weight shape produced by a third-party
  mlx-vlm 0.4.4 conversion matches the `Qwen3_5Model` parameter tree
  exactly — `sanitize` repacks `experts.gate_up_proj` (`qwen3_5_moe.py:36-50`)
  but a load was not executed
- **Medium** that no nvfp4-specific HF-legacy `quant_method` branch
  exists in mlx_lm 0.31.2 — verified by full read of `load_model`, but
  newer mlx_lm versions may add one
