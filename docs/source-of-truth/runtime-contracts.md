# owlmlx Runtime Contracts

> Status: authoritative
> Updated: 2026-05-06

## 1. Purpose

This document defines runtime-owned contracts that should live in `owlmlx`
rather than only inside platform-layer protocol documents.

The platform shell may proxy, aggregate, or present these contracts, but the
semantic ownership belongs here.

## 2. Contract Families

`owlmlx` currently recognizes five first-class contract families:

1. `core runtime status`
2. `large-weight runtime path status`
3. `training substrate`
4. `artifact layout`
5. `training-to-serving`

These are runtime contracts, not dashboard-only response shapes.

## 3. Contract Rules

### 3.1 Runtime Truth Is Authoritative

Runtime contracts must describe runtime truth as the runtime itself understands
it. Platform layers may add product context, but they must not rewrite the
meaning of runtime state.

### 3.2 Capability Labels Must Be Honest

A contract must not imply a capability that the runtime does not honestly
support.

### 3.3 Path-Level Contracts Must Not Be Generalized Improperly

Specimen-specific or path-specific fields must remain path-scoped. A
large-weight runtime path contract must not be mistaken for generalized
foreground runtime support.

## 4. Core Runtime Status Contract

The core runtime status contract exists to expose authoritative runtime facts
such as:

- runtime identity
- load state
- memory state
- switching and readiness state
- cache or lifecycle truth where owned by the runtime

This contract may initially be fulfilled through external runtime surfaces, but
the contract itself belongs to `owlmlx`.

### 4.1 Stream Timing Diagnostic Contract

Raw stream generation may include diagnostic timing detail on `done` events:

- `detail.timing.surface = owlmlx.child_stream_timing`
- `prompt_render_ms`
- `stream_call_start_ms`
- `first_response_ms`
- `first_visible_token_ms`
- `stream_wall_ms`

This is runtime-owned diagnostic evidence, not a stable product UI contract.
It exists to separate template/render overhead, parent exchange overhead, and
child `mlx_lm.stream_generate` pre-first-response latency during Model RC and
reference-runtime closure rounds.

Model RC records may aggregate this diagnostic timing into optional
observability fields:

- `runtime_stream_wall_ms`
- `runtime_first_response_ms`
- `runtime_first_visible_token_ms`
- `runtime_prompt_render_ms`
- `runtime_timing_repeat_count`
- `runtime_timing_gate_status`
- `experimental_prefill_warmup_status`
- `experimental_prefill_warmup_mode`
- `experimental_prefill_warmup_ms`
- `experimental_prefill_warmup_included_in_metrics`

Valid timing-gate statuses are `supported`, `partial`, `unsupported`, and
`not_in_scope`. These are evidence availability labels, not performance
success labels.

Experimental prefill warmup fields are Model RC-only observability. They
describe an explicitly requested post-load, pre-measured stream generation and
must not be interpreted as a default runtime serving behavior. Warmup
generations are excluded from primary TTFT, TPS, lifecycle repeat counts, and
pass/fail verdict metrics unless the warmup operation itself fails.

## 5. Large-Weight Runtime Path Contract

The large-weight runtime path contract exists to expose runtime facts specific
to the first mature path, including:

- runtime variant identity
- memory and cache state
- lifecycle mode
- path-specific serving posture
- honest interactive-status labels

`Kimi` currently validates this path, but the contract is path-owned rather than
specimen-owned.

The formal path truth (serving posture, concurrency boundary, memory behavior,
lifecycle, governance) is frozen in `large-weight-path-truth.md`.

### 5.1 Owned Serving Modules

The following owlmlx modules implement runtime contracts for this path:

- `owlmlx/serving.py` — `GenerationGate` enforces the queue-based single-worker
  generation discipline (concurrency boundary = 1)
- `owlmlx/serving_status.py` — `build_large_weight_serving_status()` produces
  the owlmlx-owned status shape; `merge_specimen_identity()` layers specimen
  detail on top
- `owlmlx/runtime_status.py` — schema validation for both core and large-weight
  status payloads

### 5.2 Validated Runtime Boundaries (From First Specimen)

The following runtime boundaries were established through the Kimi K2.5
experiment line (Phase 42, gates K-Q3a through K-Q4d) and have been absorbed
into large-weight path truth:

**Serving concurrency:**

- Same-process parallel generation is unsafe on MLX/Metal (substrate-level
  thread-safety limitation, not specimen-specific)
- Serialized queue-based serving (generation lock) is the safe production
  pattern; validated to 4 queued connections
- Multi-process isolation bypasses the thread-safety crash but is not
  cost-effective (2× memory for ~1.1× throughput due to Metal GPU contention)

**Memory behavior:**

- BF16 attention layer loading scales linearly with layer count (no
  superlinear accumulation observed across 1→61 layer escalation)
- GC cleanup returns Metal active memory to pool floor; no persistent
  accumulation detected
- Memory pressure from concurrent engine instances is additive and predictable

**Serving architecture:**

- Single-worker, queue-based serving is the recommended production pattern
  for large-weight path models
- Engine warmup (prefill + initial generation) should happen before accepting
  requests
- Health and status endpoints must remain responsive even under generation load

**Governance validation:**

- The heavy execution protocol (dry-run → single-unit → serial → thresholded
  → expansion) was field-validated through the full K-Q3/K-Q4 escalation
- Safe-resume contracts were exercised after a real host incident
- These governance rules are now runtime truth, not just documentation

These boundaries are path-level truth. Specimen-specific details (layer count,
per-layer memory size, generation speed) remain specimen-scoped and should not
be generalized without evidence from additional specimens.

## 6. Training Substrate Contract

The training substrate contract exists to define how model training relates to
the owlmlx runtime. It covers:

- training environment (hardware, venv, managed environment rules)
- training stack selection (primary MLX native, fallback PyTorch + PEFT)
- substrate boundary (owlmlx-owned vs shell-owned vs external tooling)
- model architecture verification rules

This contract is the authority for training environment truth. It is NOT a
training orchestration system. Data engineering, evaluation criteria, and
training job scheduling remain outside this contract.

The full contract is in `training-substrate-contract.md`.

## 7. Artifact Layout Contract

The artifact layout contract defines where trained model artifacts live, how
they are named, versioned, and registered for runtime consumption. It covers:

- base model path rules (read-only after download)
- tuned artifact layout (`$MODELS_ROOT/{model-id}/tuned/{run-id}/`)
- naming convention (`{task}-{method}-{date}-{seq}`)
- metadata.json as the artifact registration record
- checkpoint and evaluation subtree structure

The full contract is in `artifact-layout-contract.md`.

## 8. Training-To-Serving Contract

The training-to-serving contract defines how trained artifacts re-enter the
owlmlx runtime for inference. It covers:

- load path for LoRA adapters and full fine-tune artifacts
- serving feasibility checklist (registration, file integrity, load
  verification, inference delta, memory budget, path compliance)
- runtime status extension for tuned artifact identity
- model switching safety integration with GenerationGate
- responsibility boundary between runtime (HOW to switch) and product (WHEN)

The full contract is in `training-to-serving-contract.md`.

## 9. Relationship To Platform Protocols

The current desktop product shell repository may continue to define:

- proxy routes
- snapshot composition
- UI-specific aggregation
- shell-level error handling

But those should reference runtime-owned contracts from `owlmlx`, not serve as
the only truth source for runtime semantics.

The same rule applies to governance contracts such as hazardous-operation
classification and safe-resume state.
