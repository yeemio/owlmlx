# Hypura Overflow Path Reference

> Status: external reference
> Updated: 2026-04-11
> Scope: research input for future `owlmlx` overflow / NVMe-tier execution path

## 1. Purpose

This document records `Hypura` as an external research reference for future
`owlmlx` overflow execution work.

Hypura is not adopted as an owlmlx runtime path. It is recorded because its
technical direction is adjacent to owlmlx's large-weight and memory-governance
work:

- Apple Silicon local inference
- model weights larger than practical resident memory
- GPU / RAM / NVMe tier-aware execution
- MoE expert streaming and cache behavior

The purpose of this document is to keep the reference available for future
research without confusing it with current supported capability.

## 2. External Project Identity

| Field | Value |
|---|---|
| Project | Hypura |
| Repository | `https://github.com/t8/hypura` |
| Current interpretation | Storage-tier-aware LLM inference scheduler for Apple Silicon |
| Primary implementation | Rust + llama.cpp FFI + Metal + GGUF |
| Relevant model class | Models that exceed comfortable resident-memory limits |
| Current owlmlx label | External reference, not supported path |

## 3. What Hypura Appears To Optimize

Hypura's relevant idea is not generic model serving. It is:

**When the whole model cannot or should not stay resident, place tensors across
GPU / RAM / NVMe and stream the cold tier during inference.**

From the public project and research notes, the important mechanisms are:

- tensor placement across storage tiers
- NVMe-backed tensor loading
- Metal execution through llama.cpp integration
- expert streaming for MoE models
- neuron / expert cache behavior
- I/O and compute overlap experiments

This is closest to an `overflow execution strategy`, not a foreground
interactive serving strategy.

## 4. Difference From owlmlx Kimi Large-Weight Path

Hypura and the owlmlx Kimi line are adjacent but not the same route.

| Dimension | owlmlx Kimi large-weight path | Hypura |
|---|---|---|
| Primary specimen | Kimi K2.5, 1T total / 32B active MoE | General GGUF models |
| Runtime base | Python + MLX / Metal + custom Kimi sharded engine | Rust + llama.cpp FFI + Metal |
| Weight format | Kimi-specific expert-sharded assets | GGUF tensor files |
| Core work | BF16 attention recovery, expert sharding, queue-based serving boundary | GPU/RAM/NVMe placement and streaming |
| Serving posture | Background-heavy, single-worker queue-based | Overflow / streaming inference research |
| Concurrency truth | Generation concurrency = 1 for large-weight path | Not the primary question |
| Current maturity in our stack | Validated specimen and owlmlx path truth | External reference only |

The key difference:

- Kimi work proves a specimen-specific 1T MoE can be made stable as a
  background-heavy MLX path.
- Hypura explores a more general storage-tier scheduler for models that cannot
  remain comfortably resident.

## 5. Relationship To Existing owlmlx Truth

Hypura is relevant to these existing owlmlx truths:

| owlmlx truth | Relationship |
|---|---|
| `memory_budget.py` | Today owlmlx answers "will it fit?"; Hypura suggests future work for "if not, can it stream?" |
| `large-weight-path-truth.md` | Kimi is queue-based and background-heavy; Hypura is another possible background-heavy execution style |
| `runtime-governance.md` | NVMe-tier execution is hazardous enough to require staged validation |
| `hazardous-operations.md` | Any Hypura-style probe should follow dry-run → single-model → thresholded expansion |
| `capability-absorption-inventory.md` | Future candidate area, not part of first substrate-boundary absorption group |

## 6. Current Non-Adoption Decision

Hypura must not be treated as an adopted path yet.

Reasons:

1. It is centered on GGUF / llama.cpp, while the current owlmlx path is MLX /
   oMLX oriented.
2. It has not been tested on our M5-class local platform with our model fleet.
3. It has not been tested against Kimi K2.5 expert-sharded assets.
4. Its public performance claims are model- and hardware-specific.
5. Its best role for us is research input for an overflow path, not replacement
   of the current large-weight path.

Therefore:

- Do not rename an owlmlx path after Hypura.
- Do not treat Hypura as a supported backend.
- Do not make Hypura a dependency of the current platform.
- Do not use Hypura to reopen Kimi's frozen serving boundary.

## 7. Future Research Gate

Hypura becomes actionable only if a future round explicitly opens an
`overflow execution path` investigation.

Minimum gate for such a round:

1. Choose a non-critical GGUF model small enough to probe safely.
2. Verify Hypura build and local hardware compatibility.
3. Measure load time, prefill, decode, memory pressure, and NVMe pressure.
4. Compare against the same model under existing platform runtimes where
   practical.
5. Record whether the result is:
   - useful as an external backend
   - useful only as a scheduling reference
   - not useful for this hardware generation

Kimi K2.5 must not be the first Hypura probe target. It is too large and too
specialized for an initial backend feasibility test.

## 8. Current Label

`Hypura` label inside owlmlx:

**external-reference / future-overflow-path-candidate**

It is relevant enough to track, but not mature enough in our stack to promote
to `experimental` owlmlx capability.
