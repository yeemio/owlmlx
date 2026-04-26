# owlmlx - Orchestration Status Composition Refresh

## 你是谁

你是 `owlmlx` 主线执行者。

这轮不是 `owlops` 消费侧工作，也不是继续新开一个单点 policy contract。

这轮是统筹后的组合刷新：

- `scheduler_admission_contract`
- `model_residency_policy`
- `memory_pressure_contract`

都已经有 runtime-owned surface。

现在要把既有 `owlmlx.orchestration_status` 从早期直接读
`/v1/runtime/status` 的粗聚合，升级成真正消费这些子 contract 的总姿态面。

## 工作目录

`/Users/yeemio/AI/gitrep/owlmlx`

## 本轮唯一目标

刷新 `owlmlx.orchestration_status`，让它成为 single-host orchestration
immediate program 的组合入口。

它应该总结：

- admission 当前怎么判断
- model residency 当前怎么判断
- memory pressure 当前怎么判断
- 哪些 recovery / stream / scheduler-depth 信号仍然不足

但它不能宣称：

- full local scheduler 已完成
- continuous batching 已完成
- pressure-ranked eviction 已完成
- recovery supervisor 已完成

## 最终 verdict 只能二选一

- `owlmlx_orchestration_status_composition_refreshed`
- `owlmlx_orchestration_status_composition_still_blocked`

如果 still blocked，必须说明：

- 哪个子 surface 不能被稳定消费
- 为什么不能诚实刷新总面
- 下一轮要先修哪个 blocker

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/single-host-orchestration-architecture.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/orchestration-status-surface.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/scheduler-admission-contract.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/model-residency-policy.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/memory-pressure-contract.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/orchestration_status.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/scheduler_admission_contract.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/model_residency_policy.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/memory_pressure_contract.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_orchestration_status.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_scheduler_admission_contract.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_model_residency_policy.py`
16. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_memory_pressure_contract.py`
17. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

读完后先输出不超过 12 行执行计划，再动手。

## 第一性原则

- `composed runtime truth > duplicated ad-hoc inference`
- `child contract verdicts > raw status guessing`
- `partial remains partial`
- `unknown remains explicit`
- `one stable upstream surface > several disconnected facts`

## 当前已接受事实

当前 program 已经有这些 runtime-owned surfaces：

- `owlmlx.scheduler_admission_contract`
  - transport: `GET /v1/runtime/scheduler-admission-contract`
  - decisions: `accepted / deferred / rejected / unknown`
- `owlmlx.model_residency_policy`
  - transport: `GET /v1/runtime/model-residency-policy`
  - states: `resident / default_active / pinned / ttl_managed / evictable / unknown`
- `owlmlx.memory_pressure_contract`
  - transport: `GET /v1/runtime/memory-pressure-contract`
  - states: `within_budget / near_budget / over_budget / unknown`

`owlmlx.orchestration_status` already exists:

- transport: `GET /v1/runtime/orchestration-status`

But it must now be refreshed to compose the newer child surfaces instead of
remaining a stale early aggregation.

## Required Composition Behavior

The refreshed `orchestration_status` must:

1. include child surface references under stable sections
2. derive summary posture from child surface outputs where honest
3. preserve layer-by-layer assessment
4. expose missing signals from child surfaces without flattening them away
5. keep recovery and stream limitations explicit
6. remain JSON-serializable and transport-safe

At minimum, stable output should make clear:

- authoritative child surfaces consumed
- selected / dominant bottleneck layer if one is honestly visible
- layer assessment for:
  - admission
  - generation_gate
  - stream_hold
  - model_residency
  - memory_pressure
  - recovery
  - unknown
- child missing signals
- preserved invariants

## Decision Priority

When multiple child surfaces suggest pressure, use conservative priority:

1. `recovery` if current runtime exposes exhausted restart / explicit recovery failure
2. `memory_pressure` if pressure contract is `over_budget`
3. `admission` if scheduler admission is currently `deferred` by pre-gate backlog
4. `generation_gate` if scheduler admission is `deferred` by post-claim gate waiters
5. `model_residency` if residency policy shows multiple resident controls competing but no harder blocker is visible
6. `unknown` if child surfaces do not support a dominant layer

If this priority conflicts with existing code truth, stop and justify the
narrower honest rule. Do not force the priority mechanically.

## Not In Scope

Do not implement:

- recovery supervisor
- pressure-ranked eviction
- reclaim engine
- continuous batching
- multi-worker scheduler
- OwlOps UI/service consumption

Do not change:

- post-claim `max_concurrent=1`
- `ticketed_fifo` safety boundary
- child/backend execution semantics

## Expected Files

Likely touched files:

- `owlmlx/orchestration_status.py`
- `docs/source-of-truth/orchestration-status-surface.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/runtime-capability-matrix.md`
- `tests/test_orchestration_status.py`
- `tests/test_runtime_server.py`

Only touch additional files if the actual implementation requires it.

## Verification

Run at least:

- `pytest -q tests/test_orchestration_status.py`
- `pytest -q tests/test_scheduler_admission_contract.py tests/test_model_residency_policy.py tests/test_memory_pressure_contract.py`
- `pytest -q tests/test_runtime_server.py -k "orchestration_status or scheduler_admission_contract or model_residency_policy or memory_pressure_contract"`

If broader tests are already known green and cheap, run them too.

## Delivery Format

Report in this order:

1. 一句最终结论：`refreshed` 或 `still_blocked`
2. exact verdict
3. authoritative surface
4. child surfaces consumed
5. dominant layer selection rule
6. layers still partial / unknown
7. files changed
8. commands run and key results
9. remaining blocker, if any
