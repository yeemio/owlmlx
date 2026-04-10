# owlmlx Large-Weight Runtime Path Truth

> Status: authoritative
> Updated: 2026-04-10
> Frozen by: Phase 2 Round 4

## 1. Path Identity

The **large-weight runtime path** is owlmlx's first mature runtime path.

- Path name: `large-weight runtime path`
- Path is NOT named after any single specimen
- First validated specimen: Kimi K2.5-3bit (expert-sharded)
- Additional specimens may join this path when they carry their own evidence

## 2. Path-Level Truths

These facts are validated and owned by owlmlx as path-level truth. They are
not specimen-specific — they apply to any model served through this path.

### 2.1 Serving Posture

- Background-heavy serving is the runtime class
- Foreground interactive serving is not established for this path
- Single-worker queue-based serving is the production pattern
- Engine warmup must complete before accepting requests
- Health and status endpoints must remain responsive during generation

### 2.2 Concurrency Boundary

- Same-process parallel generation is unsafe on MLX/Metal
  (substrate thread-safety limitation, not application bug)
- Generation concurrency boundary = 1
- HTTP connections may arrive concurrently; generation is serialized
- Multi-process isolation technically works but is not cost-effective
  (2× memory for ~1.1× throughput due to Metal GPU contention)

### 2.3 Memory Behavior

- Layer loading scales linearly with layer count (no superlinear accumulation)
- GC cleanup returns Metal active memory to pool floor
- Memory pressure from concurrent engine instances is additive and predictable
- MLX buffer pool allocation is normal runtime behavior, not a leak

### 2.4 Lifecycle

- Lifecycle mode: manual start (no auto-start / auto-restart)
- Graceful shutdown: must drain active generation before exit
- Safe-resume: controlled re-entry after incident, not blind restart

### 2.5 Governance

- Heavy execution protocol is the mandatory entry path for hazardous operations:
  dry-run → single-unit → serial → thresholded → expansion
- This protocol was field-validated through K-Q3a→K-Q4d escalation
- Safe-resume contracts were exercised after a real host incident

## 3. Owned Modules

The following modules are owned by owlmlx for this path:

| Module | Location | Responsibility |
|--------|----------|----------------|
| `GenerationGate` | `owlmlx/serving.py` | Queue-based single-worker generation discipline |
| `build_large_weight_serving_status` | `owlmlx/serving_status.py` | Path-level runtime status shape |
| `merge_specimen_identity` | `owlmlx/serving_status.py` | Specimen detail layered on path-level base |
| `validate_runtime_status` | `owlmlx/runtime_status.py` | Schema validation for runtime status payloads |
| `normalize_large_weight_runtime_status` | `owlmlx/runtime_status.py` | Payload normalization for large-weight path |

## 4. Shell / Runtime Boundary

| Responsibility | Owner |
|----------------|-------|
| Generation serialization discipline | owlmlx (GenerationGate) |
| Runtime status shape and truth | owlmlx (serving_status) |
| Schema validation | owlmlx (runtime_status) |
| HTTP transport (FastAPI, uvicorn) | platform shell |
| Model loading and inference engine | platform shell (kimi-sharded-engine.py) |
| Expert cache management | platform shell (specimen-specific) |
| Product endpoints and routing | platform shell |
| Desktop UI and operator surfaces | platform shell |

## 5. Specimen-Only Facts (Not Path Truth)

The following are specific to the Kimi K2.5 first specimen and must NOT be
generalized as path-level truth without evidence from additional specimens:

- 61-layer structure
- 193 MB per BF16 attention layer
- MoE architecture with 384 experts per layer, 8 active
- Expert-sharded loading pattern
- BF16 attention recovery (quantization remediation)
- ~3-5 s/tok generation speed
- ~11.7 GB full-stack standalone load
- Port 8014
- Specific prefill/decode baselines (4493ms/609ms)

## 6. What This Path Is Not

- Not a general-purpose interactive runtime
- Not a multi-model switching path (one model at a time)
- Not a high-throughput serving solution
- Not a replacement for lightweight model serving
- Not automatically applicable to models outside this weight class
