# owlmlx Native MLX Backend — Conversion Path Ownership

> Status: authoritative
> Updated: 2026-05-08
> Scope: layered ownership of weight conversion (Transformers / vendor
> formats → MLX-loadable safetensors). Records what owlmlx implements
> versus what owlmlx borrows, and what owlmlx **owns** at the path-semantics
> level.

## 1. Why This Document Exists

owlmlx is a self-owned MLX runtime (identity contract recorded in
`AGENTS.md:39` and `docs/source-of-truth/master-outline.md:225`). Its
identity contract is explicit:

> what `owlmlx` owns is identity, principles, governance, truth contracts,
> and path semantics — not necessarily every line of execution code

Weight conversion is a high-effort, well-solved upstream problem. Forking
its execution kernel would violate the identity contract from the other
side ("Not a thin wrapper around vMLX" implies symmetrically: not a shadow
reimplementation of mlx-lm either). At the same time, owlmlx cannot
disclaim conversion entirely — without a path-level ownership statement,
the capability matrix has no anti-pollution anchor (any artifact found in
the wild can be smuggled in as evidence).

This document fixes that boundary.

## 2. Layered Ownership

| Layer | What it does | owlmlx role |
|---|---|---|
| Execution layer | Performs dtype conversion, quantization, repacking, safetensors writing | **borrow** — `mlx_lm.convert`, `mlx-vlm`, mlx-community pre-converted artifacts |
| Path semantics layer | Decides what artifact is admissible as input, where it lives, how its provenance is recorded, when matrix promotion may cite it | **own** — codified in this document and in `native-mlx-backend-local-candidate-admissibility.md` |

owlmlx does **not** plan to reimplement `mlx_lm.convert` or any subset of
its kernel. owlmlx **does** own the rules under which a conversion's output
is allowed to advance the capability matrix.

## 3. Acceptable Conversion Routes

In decreasing order of trust:

### 3.1 Pre-converted upstream artifact (preferred)

- `mlx-community/<name>` HF releases
- conversion is performed by the mlx community using `mlx_lm.convert` or
  `mlx-vlm` and published with model cards
- owlmlx accepts these as first-class candidates without performing the
  conversion locally
- provenance recording requirement: HF revision SHA, model_type, mlx_lm
  version stated on the model card (where present), local mirror path if
  any

### 3.2 Reputable third-party MLX-format release

- `unsloth/*-MLX-*` and similar third-party converters with a maintained
  reputation
- accepted as second-class candidates: same shape as mlx-community but
  recorded with explicit third-party note
- provenance recording requirement: same as 3.1 plus a note identifying
  the third-party publisher

### 3.3 Local conversion via `mlx_lm.convert`

- only invoked when no acceptable upstream artifact exists for the target
  arch + quantization combination
- the conversion command is logged verbatim, including all flags
- the source HF repo + revision is logged
- the output config.json is hashed and the hash is recorded
- mlx_lm version is recorded (because identical commands at different
  mlx_lm versions can produce subtly different outputs; DWQ vs non-DWQ
  affine 4bit is invisible at load time per input contract §6)
- the conversion is performed in a dedicated round, not as a side-effect
  of any other round

### 3.4 Local conversion via `mlx-vlm`

- accepted only for architectures that have been proven VLM-config
  tolerant in the input contract (currently only `qwen3_5_moe`); see
  `native-mlx-backend-input-contract.md` §5
- per-architecture review required — not a blanket admission
- provenance recording requirement: mlx-vlm version + arch module that
  consumes the result + verification that the arch's `sanitize` step
  handles the produced weight tensor naming

## 4. What This Document Does Not Authorize

owlmlx does **not** authorize:

- forking `mlx_lm.convert` or maintaining an owlmlx-internal copy
- adding new arch modules to `mlx_lm/models/` from owlmlx — that is
  upstream work; if a candidate model has no matching arch, the correct
  response is to wait for upstream support, not to ship it inside owlmlx
- "convenience" automation that hides which conversion route was used
  (e.g. a wrapper that silently falls back from upstream artifact to
  local conversion would erase provenance)
- treating `mlx_lm.convert` quality variants (DWQ on/off, calibration
  data choice, group_size variation) as separate runtime capabilities;
  per input contract §6 they are indistinguishable at load time

## 5. Storage and Layout

- pre-converted upstream artifacts live in
  `~/.cache/huggingface/hub/` under HF-default management; owlmlx does
  not maintain a parallel cache directory
- self-converted artifacts live in a path the operator explicitly chooses
  per round (no global default — forces per-round provenance discussion)
- local Transformers / vendor releases mirrored on the development host
  (e.g. `/Users/yeemio/AI/Agent/models/`) are catalogued in
  `native-mlx-backend-local-candidate-admissibility.md` but are not
  themselves a conversion route — they are pre-conversion source material

## 6. Capability Matrix Promotion Coupling

Per `native-mlx-backend-capability-matrix.md` §1a "Promotion Gate", any
matrix promotion that cites a converted artifact must record the
conversion route used (3.1 / 3.2 / 3.3 / 3.4) along with the route-
specific provenance fields above. A promotion whose conversion route
cannot be cleanly classified into one of these four routes is **not
admissible** as promotion evidence.

## 7. What This Document Does Not Decide

- whether to convert any specific candidate now, ever, or in the next
  round — that is operator-driven and decided per round
- whether owlmlx should publish its own MLX artifacts to HF — out of
  scope; current direction is to consume, not publish
- whether owlmlx should contribute upstream to `mlx_lm.convert` — also
  out of scope; possible but not committed
